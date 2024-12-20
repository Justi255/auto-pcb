import os
import sys
import numpy as np
import pdb
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))
from   dataset import Dataset
import matplotlib
import joblib
from modeling import Node,Net,Pad
from optimizer import MILP_placer
from typing import List
matplotlib.use('Agg')
sys.path.pop()

def center_placement(Nodes:List[Node], minX, minY, maxX, maxY):
    for node in Nodes:
        if node.lock:
            continue
        node.setPos((minX + maxX)/2 - node.width.value/2, (minY + maxY)/2 - node.height.value/2)
        node.setRotation(0)

rawdb = Dataset(input_file_path="../../../../../examples/test_data/bm9/bm9.unrouted.kicad_pcb")
rawdb.load()

# write back path
path = "./output/bm9"
img_path = os.path.join(path,"plot")
os.makedirs(path, exist_ok=True)
os.makedirs(img_path, exist_ok=True)

center_placement(rawdb.Nodes, rawdb.layout[0], rawdb.layout[1], rawdb.layout[2], rawdb.layout[3])
gp_out_file = os.path.join(
    path,
    "%s.unrouted.%s" % ("bm9", "kicad_pcb"))
rawdb.wirte_back(gp_out_file)

rawdb = Dataset(input_file_path="./output/bm9/bm9.unrouted.kicad_pcb")
rawdb.load()

# write back path
path = "./result/bm9"
img_path = os.path.join(path,"plot")
os.makedirs(path, exist_ok=True)
os.makedirs(img_path, exist_ok=True)

netss = [net for net in rawdb.Nets if len(net.pads)>= 2]
num_nets = len(netss)
nets_order = np.zeros((num_nets, num_nets, 4))
for net1id, net1 in enumerate(netss):
    for net2id, net2 in enumerate(netss):
        if net1id == net2id:
            continue
        for net1_pad in net1.padlist:
            for net2_pad in net2.padlist:
                pad1 = rawdb.Pads[net1_pad]
                pad2 = rawdb.Pads[net2_pad]
                if pad1.node_index == pad2.node_index:
                    order = -1
                    if abs(pad1.x_offset - pad2.x_offset) < abs(pad1.y_offset - pad2.y_offset):
                        if pad1.y_offset > pad2.y_offset:
                            order = 0
                            print(f"{net1.name} is relatively upper than {net2.name}")
                        if pad1.y_offset < pad2.y_offset:
                            order = 1
                            print(f"{net1.name} is relatively lower than {net2.name}")
                    elif abs(pad1.x_offset - pad2.x_offset) > abs(pad1.y_offset - pad2.y_offset):
                        if pad1.x_offset > pad2.x_offset:
                            order = 2
                            print(f"{net1.name} is relatively rightter than {net2.name}")
                        if pad1.x_offset < pad2.x_offset:
                            order = 3
                            print(f"{net1.name} is relatively lefter than {net2.name}")
                    
                    if order != -1:
                        nets_order[net1id][net2id][order] += 1

nets_pos = np.zeros((num_nets,2))
for netid, net in enumerate(netss):
    pos_x = []
    pos_y = []
    for padid in net.padlist:
        pad  = rawdb.Pads[padid]
        node = rawdb.Nodes[pad.node_index]
        pos_x.append(pad.x_offset + node.x_left)
        pos_y.append(pad.y_offset + node.y_bottom)
    nets_pos[netid][0] = sum(pos_x)/len(pos_x)
    nets_pos[netid][1] = sum(pos_y)/len(pos_y)

correct = 0
wrong   = 0
for net1id, net1 in enumerate(netss):
    for net2id, net2 in enumerate(netss):
        if net1id == net2id:
            continue
        up    = nets_order[net1id][net2id][0]
        down  = nets_order[net1id][net2id][1]
        right = nets_order[net1id][net2id][2]
        left  = nets_order[net1id][net2id][3]
        if up    > down:
            if nets_pos[net1id][1] > nets_pos[net2id][1]:
                correct += 1
                print(f"predict correct, {net1.name} is up to {net2.name}")
            else:
                wrong   += 1
                print(f"predict wrong, {net1.name} is down to {net2.name}")
        if up    < down:
            if nets_pos[net1id][1] < nets_pos[net2id][1]:
                correct += 1
                print(f"predict correct, {net1.name} is down to {net2.name}")
            else:
                wrong   += 1
                print(f"predict wrong, {net1.name} is up to {net2.name}")
        if right > left:
            if nets_pos[net1id][0] > nets_pos[net2id][0]:
                correct += 1
                print(f"predict correct, {net1.name} is right to {net2.name}")
            else:
                wrong   += 1
                print(f"predict wrong, {net1.name} is left to {net2.name}")
        if right < left:
            if nets_pos[net1id][0] < nets_pos[net2id][0]:
                correct += 1
                print(f"predict correct, {net1.name} is left to {net2.name}")
            else:
                wrong   += 1
                print(f"predict wrong, {net1.name} is right to {net2.name}")
print(f"accuracy : {correct/(correct + wrong)}")

# order constraints
vo = []
ho = []
norelpairs = []
xl, yl, xh, yh = rawdb.layout
threhold = 0.4*max(xh-xl, yh-yl)

for i1, node1 in enumerate(rawdb.Nodes):
    for i2, node2 in enumerate(rawdb.Nodes):
        #continue
        if i2 <= i1:
            continue
        # one of the two is a fixed node
        if (node1.lock or node2.lock):
            continue
        if ((max(abs(node1.x_left - node2.x_left), abs(node1.y_bottom - node2.y_bottom)) > threhold)):
            if abs(node1.x_left - node2.x_left) < abs(node1.y_bottom - node2.y_bottom):
                if node1.y_bottom < node2.y_bottom:
                    vo.append([i1, i2])
                else:
                    vo.append([i2,i1])
            else:
                if node1.x_left < node2.x_left:
                    ho.append([i1, i2])
                else:
                    ho.append([i2,i1]) 
        else:
            norelpairs.append([i1,i2])

horiz_order = [[rawdb.Nodes[i] for i in h] for h in ho]
vert_order = [[rawdb.Nodes[i] for i in v] for v in vo]
print('num horizontal & vertical constraints:',len(horiz_order),len(vert_order))

# milp_placer = MILP_placer(rawdb.Nodes, rawdb.Nets, rawdb.Pads, 
#                           norelpairs, horiz_order, vert_order,
#                           rawdb.layout[0], rawdb.layout[1], rawdb.layout[2], rawdb.layout[3], 
#                           max_seconds=3800, num_cores= joblib.cpu_count())
# nodes = milp_placer.layout()
    
# # update raw database
# rawdb.update_nodes(nodes)
        
# write placement solution
gp_out_file = os.path.join(
    path,
    "%s.unrouted.%s" % ("bm9", "kicad_pcb"))
rawdb.wirte_back(gp_out_file)
                        
                        
                    
                
