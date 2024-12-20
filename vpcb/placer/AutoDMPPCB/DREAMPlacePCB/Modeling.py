from typing import List

class Node:
    def __init__(self, name, x_center, y_center, x_left, y_bottom, width, height, node_index, angle, lock):
        self.name = name
        self.node_index = node_index
        self.width =  width
        self.height = height
        self.lock = lock
        self.x_left   = x_left
        self.y_bottom = y_bottom
        self.angle = angle
        self.x_left2center   = x_center - x_left
        self.y_bottom2center = y_center - y_bottom

    @property
    def size(self):
        return self.width * self.height
    
    @property
    def x_center(self):
        return self.x_left + self.x_left2center

    @property
    def y_center(self):
        return self.y_bottom + self.y_bottom2center
    
    @property
    def left(self):
        return self.x_left
    
    @property
    def right(self):
        return self.x_left + self.width

    @property
    def bottom(self):
        return self.y_bottom 
    
    @property
    def top(self):
        return self.y_bottom + self.height
    
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


