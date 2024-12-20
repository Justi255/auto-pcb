import re
from typing import List
import cvxpy as cp
from modeling import Node,Net,Pad
from cvxpy import Constant, Minimize, Problem
from z3 import *
import numpy as np


class MILP_placer(object):

    def __init__(self, nodes:List[Node], nets:List[Net], pads:List[Pad], norelpairs, 
                 horizontal_orderings, vertical_orderings, 
                 minX , minY , maxX, maxY, margin=0.2, 
                 max_seconds=100, num_cores=1, name=""):
        self.name   = name
        self.margin = margin

        self.norelpairs = norelpairs
        self.horizontal_orderings = horizontal_orderings
        self.vertical_orderings = vertical_orderings
        
        # nodes是元器件的列表
        self.nodes:List[Node] = nodes
        # nets是net的列表
        self.nets:List[Net] = nets
        self.pads:List[Pad] = pads
        self.num_nets = len(nets)
        self.num_nodes = len(nodes)

        self.minX = Constant(minX)
        self.minY = Constant(minY)
        self.maxX = Constant(maxX)
        self.maxY = Constant(maxY)
        self.board_width = Constant(maxX - minX)
        self.board_height = Constant(maxY - minY)
        
        # 模块间的相对位置系数
        self.p = cp.Variable(shape=(self.num_nodes,self.num_nodes), boolean=True)
        self.q = cp.Variable(shape=(self.num_nodes,self.num_nodes), boolean=True)

        # 线网间的相对位置系数
        num_nets = len(nets)
        self.n_p = cp.Variable(shape=(num_nets,num_nets), boolean=True)
        self.n_q = cp.Variable(shape=(num_nets,num_nets), boolean=True)
        # net间的重叠
        self.n_oa = cp.Variable(shape=(num_nets,num_nets),nonneg = True)

        self.max_seconds = max(max_seconds,1)
        print(" num_cores: ",num_cores)
        self.num_cores = max(num_cores,1)

    # Return constraints for the ordering.
    @staticmethod
    def _order(nodes:List[Node], horizontal):
        if len(nodes) == 0: return
        constraints = []
        curr = nodes[0]
        for node in nodes[1:]:
            if horizontal:
                constraints.append(curr.right <= node.left)
            else:
                constraints.append(curr.top <= node.bottom)
            curr = node
        return constraints
    
    def layout(self):
        constraints = []
        # VDD的名称格式
        pattern = r'\dV\d'

        # 限制模块在可布局区域内部
        constraints += [self.minX + self.margin  <= node.left   for node in self.nodes if not node.lock]
        constraints += [self.minY + self.margin  <= node.bottom for node in self.nodes if not node.lock]
        constraints += [self.maxX - self.margin  >= node.right  for node in self.nodes if not node.lock]
        constraints += [self.maxY - self.margin  >= node.top    for node in self.nodes if not node.lock]
        
        # routability
        for n_i, net in enumerate(self.nets):
            mx = []
            my = []
            for pi, padid in enumerate(net.padlist):
                pad  = self.pads[padid]
                node = self.nodes[pad.node_index]
                # node的中心点坐标
                nodex = node.x_center
                nodey = node.y_center
                poff = [pad.x_offset, pad.y_offset]
                # 分别为0°、90°、180°、270°
                nmnr = (not node.m) and (not node.r) 
                nmr  = (not node.m) and (node.r)
                mnr  = (node.m)     and (not node.r)
                mr   = (node.m)     and (node.r)

                pinposx = nodex + nmnr*(poff[0]) + \
                                nmr*(poff[1]) + \
                                mnr*(-1*poff[0]) + \
                                mr*(-1*poff[1])
                
                
                pinposy = nodey + nmnr*(poff[1]) + \
                                nmr*(-1*poff[0]) + \
                                mnr*(-1*poff[1]) + \
                                mr*(poff[0])
                # 这里mx,my是pin的绝对坐标
                mx.append(pinposx)
                my.append(pinposy)

            # net的矩形包络限制条件
            constraints += [net.L_x <= x for x in mx]
            constraints += [net.U_x >= x for x in mx]
            constraints += [net.L_y <= y for y in my]
            constraints += [net.U_y >= y for y in my]

            if len(net.pads) <= 1: 
                # constraints += [ 0 <= self.n_oa[n_i, n_j] for n_j in range(len(self.nets))]
                print("ignore 1 pin net overlap, net name:",net.name)
                continue

            if re.match(pattern, net.name) or net.name=="GND" or net.name=="VDD":
                # constraints += [ 0 <= self.n_oa[n_i, n_j] for n_j in range(len(self.nets))]
                print("ignore power net overlap, net name:",net.name)
                continue
        
            for n_j in range(n_i+1,len(self.nets)):
                net_i = net
                net_j = self.nets[n_j]
                if len(net_j.pads) <= 1:
                    # constraints += [ 0 <= self.n_oa[n_i, n_j]]
                    print("ignore 1 pin net overlap, net name:",net_j.name)
                    continue
                if re.match(pattern, net_j.name) or net_j.name=="GND" or net_j.name=="VDD":
                    # constraints += [ 0 <= self.n_oa[n_i, n_j]]
                    print("ignore power net overlap, net name:",net_j.name)
                    continue
                # 线网之间不重叠
                constraints += [
                    net_i.U_x <= net_j.L_x + self.board_width*(self.n_p[n_i,n_j] + self.n_q[n_i,n_j]) + self.n_oa[n_i, n_j],
                    net_i.U_y <= net_j.L_y + self.board_height*(1 + self.n_p[n_i,n_j] - self.n_q[n_i,n_j]) + self.n_oa[n_i, n_j],
                    net_i.L_x >= net_j.U_x - self.board_width*(1 - self.n_p[n_i,n_j] + self.n_q[n_i,n_j]) - self.n_oa[n_i, n_j],
                    net_i.L_y >= net_j.U_y - self.board_height*(2 - self.n_p[n_i,n_j] - self.n_q[n_i,n_j]) - self.n_oa[n_i, n_j],
                ]
        
        # nonoverlap constraints
        for i in range(len(self.nodes)):
            for j in range(i+1,len(self.nodes)):
                if self.norelpairs is not None:
                    if [i,j] not in self.norelpairs:
                        continue
                node_i = self.nodes[i]
                node_j = self.nodes[j]
                
                # 若都不可以移动
                if (node_i.lock) and (node_j.lock):
                    continue
                                
                constraints += [
                    node_i.right  + self.margin  <= node_j.left   + self.board_width*(self.p[i,j] + self.q[i,j]),
                    node_i.top    + self.margin  <= node_j.bottom + self.board_height*(1 + self.p[i,j] - self.q[i,j]),
                    node_i.left   - self.margin  >= node_j.right  - self.board_width*(1 - self.p[i,j] + self.q[i,j]),
                    node_i.bottom - self.margin  >= node_j.top    - self.board_height*(2 - self.p[i,j] - self.q[i,j]),
                ]

        # Enforce the relative ordering of the boxes.
        for ordering in self.horizontal_orderings:
            constraints += self._order(ordering, True)
        for ordering in self.vertical_orderings:
            constraints += self._order(ordering, False)
        
        hpwl = [(net.U_x - net.L_x) + (net.U_y - net.L_y) for net in self.nets if len(net.pads) > 2]
        hpwls = cp.sum(hpwl)
        net_overlap =  cp.sum(self.n_oa)
        obj = Minimize(hpwls + net_overlap)
        # obj = Minimize(0)
        p = Problem(obj, constraints)
        
        assert p.is_dcp() or p.is_dgp() or p.is_dqcp()

        p.solve(solver=cp.CBC, qcp=True, warm_start=True, verbose=True, 
                maximumSeconds=self.max_seconds, numberThreads=self.num_cores, allowableGap=0.1)
        verify_constraints = np.array([c.violation() for c in constraints])
        for i , item in enumerate(verify_constraints):
            if item == True:
                print(constraints[i])
        return self.nodes