from typing import List
from cvxpy import Variable, Constant
import numpy as np


class Node:
    def __init__(self, name, x_center, y_center, x_left, y_bottom, width, height, node_index, angle, lock):
        self.name = name
        self.node_index = node_index
        self.width =  Constant(width)
        self.height = Constant(height)
        self.lock = lock
        self.x_left   = x_left
        self.y_bottom = y_bottom
        self.angle = angle
        self.x_left2center   = x_center - x_left
        self.y_bottom2center = y_center - y_bottom
        
        # 允许0°、90°、180°、270°的逆时针旋转操作
        # 上述操作可以等价于是否进行逆时针的90°旋转操作，用变量r表示
        # 与是否旋转180°的线性组合，用变量m表示
        if not lock:
            self.r = Variable(boolean=True)
            self.m = Variable(boolean=True)
            self.r.value = (angle/90)%2
            self.m.value = (angle/90)//2
        else:
            self.r=Constant((angle/90)%2)
            self.m=Constant((angle/90)//2)
            
        # x,y is the poly center of node
        if not lock:
            self.x = Variable()
            self.y = Variable()
            self.x.value = x_left + 0.5*(self.r.value*self.height.value + (1-self.r.value)*self.width.value)
            self.y.value = y_bottom + 0.5*(self.r.value*self.width.value + (1-self.r.value)*self.height.value)
        else:
            self.x = Constant(x_left + 0.5*(self.r.value*self.height.value + (1-self.r.value)*self.width.value))
            self.y = Constant(y_bottom + 0.5*(self.r.value*self.width.value + (1-self.r.value)*self.height.value))

    # 表明这是一个属性方法，不需要显式调用
    @property
    def size(self):
        return self.width.value * self.height.value
    
    @property
    def x_center(self):
        return self.x_left + self.x_left2center

    @property
    def y_center(self):
        return self.y_bottom + self.y_bottom2center
    
    @property
    def left(self):
        return self.x - 0.5*(self.r*self.height + (1-self.r)*self.width)
    
    @property
    def left_value(self):
        return self.x.value - 0.5*(self.r.value*self.height.value + (1-self.r.value)*self.width.value)

    @property
    def right(self):
        return self.x + 0.5*(self.r*self.height + (1-self.r)*self.width)

    @property
    def right_value(self):
        return self.x.value + 0.5*(self.r.value*self.height.value + (1-self.r.value)*self.width.value)
    
    @property
    def bottom(self):
        return self.y - 0.5*(self.r*self.width + (1-self.r)*self.height)

    @property
    def bottom_value(self):
        return self.y.value - 0.5*(self.r.value*self.width.value + (1-self.r.value)*self.height.value)
    
    @property
    def top(self):
        return self.y + 0.5*(self.r*self.width + (1-self.r)*self.height)
    
    @property
    def top_value(self):
        return self.y.value + 0.5*(self.r.value*self.width.value + (1-self.r.value)*self.height.value)
    
    @property
    def angle_value(self):
        return (self.m.value * 2 + self.r.value)*90

    def set_index(self , node_index):
        self.node_index = node_index
    
    def set_pads(self, pads):
        self.pads:List[Pad] = pads
    
    def update_padlist(self):
        self.padlist = []
        for pad in self.pads:
            self.padlist.append(pad.pad_index)

    def setPos(self, x_left, y_bottom):
        self.x_left   = x_left
        self.y_bottom = y_bottom

    def setRotation(self, angle):
        self.angle = angle

class Pad:
    def __init__(self, x_offset, y_offset, pad_index, node_index):
        self.x_offset     = x_offset
        self.y_offset     = y_offset
        self.pad_index    = pad_index
        self.node_index   = node_index
        self.net_index    = -1

    def set_index(self, pad_index, node_index):
        self.pad_index    = pad_index
        self.node_index   = node_index

    def set_offset(self, x_offset, y_offset):
        self.x_offset    = x_offset
        self.y_offset    = y_offset

    def set_netindex(self, net_index):
        self.net_index    = net_index
        
class Net:
    def __init__(self, name):
        self.name           = name
        self.unlock_len     = 0
        self.pads:List[Pad] = []
        self.U_x        = Variable()
        self.L_x        = Variable()
        self.U_y        = Variable()
        self.L_y        = Variable()

    def add_pad(self, pad:Pad):
        self.pads.append(pad)
    
    def update_padlist(self):
        self.padlist = []
        for pad in self.pads:
            self.padlist.append(pad.pad_index)

    def net_hpwl(self, nodes:List[Node]):
        if (len(self.pads) <= 1):
            return 0
        else:
            pad_x = []
            pad_y = []
            for pad in self.pads:
                pad_x.append(nodes[pad.node_index].x_left + pad.x_offset)
                pad_y.append(nodes[pad.node_index].y_bottom + pad.y_offset)
            return (max(pad_x) - min(pad_x) + max(pad_y) - min(pad_y))

