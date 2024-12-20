#dataset constructor
import os
import copy
from typing import List
from kicad_parser.kicad_pcb import Board
from kicad_parser.items.gritems import GrLine, GrArc
from kicad_parser.items.fpitems import FpLine, FpCircle, FpPoly, FpArc, FpText
from modeling import Node, Net, Pad
import numpy as np
import logging
import pdb

class Dataset:

    def __init__(self, input_file_path):
        self.input_file_path         = input_file_path
        self.layout           = []
        self.Nodes:List[Node] = []
        self.Nets:List[Net]   = []
        self.Pads:List[Pad]   = []
        self.board            = None
        self.sorted_node      = []
        self.node_mask        = None
    
    def load(self):
        self.board = Board.from_file(self.input_file_path)

        #count layout
        board_gr_x_line = []
        board_gr_y_line = []
        board_gr_x_arc  = []
        board_gr_y_arc  = []
        for items in self.board.graphicItems:
            if type(items) == GrLine:
                board_gr_x_line.append(items.start.X + items.width/2)
                board_gr_x_line.append(items.start.X - items.width/2)
                board_gr_y_line.append(items.start.Y + items.width/2)
                board_gr_y_line.append(items.start.Y - items.width/2)
                board_gr_x_line.append(items.end.X + items.width/2)
                board_gr_x_line.append(items.end.X - items.width/2)
                board_gr_y_line.append(items.end.Y + items.width/2)
                board_gr_y_line.append(items.end.Y - items.width/2)
            elif type(items) == GrArc:
                board_gr_x_arc.append(items.mid.X + items.width/2)
                board_gr_x_arc.append(items.mid.X - items.width/2)
                board_gr_y_arc.append(items.mid.Y + items.width/2)
                board_gr_y_arc.append(items.mid.Y - items.width/2)
        

        if len(board_gr_x_arc) == 0 and len(board_gr_y_arc) == 0 :
            xl, yl, xh, yh = min(board_gr_x_line), min(board_gr_y_line), max(board_gr_x_line), max(board_gr_y_line) 
        else:
            xl, yl, xh, yh = min(board_gr_x_arc), min(board_gr_y_arc), max(board_gr_x_arc), max(board_gr_y_arc)
        
        # some dirty code
        if "bm1" in self.input_file_path:
            xh -= 5.0

        self.layout:List[float] = [xl, yl, xh, yh]

        #build nets
        for itnet in self.board.nets:
            net = Net(itnet.name)
            self.Nets.append(net)
        self.Nets_empty = copy.deepcopy(self.Nets)

        #build nodes and pads
        node_movable:List[Node] = []
        node_lock:List[Node] = []
        pad_movable:List[Pad] = []
        pad_lock:List[Pad] = []

        for footprint in self.board.footprints:
            fp_x_center = footprint.position.X
            fp_y_center = footprint.position.Y
            fp_angle    = footprint.position.angle
            if fp_angle == None:
                fp_angle = 0
            elif fp_angle == -90:
                fp_angle = 270
            assert (fp_angle == 0) or (fp_angle == 90) or (fp_angle == 180) or (fp_angle == 270)
            lock = footprint.locked
            if lock:
                node_index = len(node_lock)
            else:
                node_index = len(node_movable)
            #layer = footprint.layer
            fp_gr_x = []
            fp_gr_y = []
            # need to consider fp_angle
            for items in footprint.graphicItems:
                if type(items) == FpText:
                    if items.type == 'reference':
                        fp_name = items.text
                        logging.info("node name = %s" % (fp_name))
                elif type(items) == FpLine:
                    start = copy.deepcopy(items.start)
                    end   = copy.deepcopy(items.end)
                    if   (fp_angle == 0):
                        start.X, start.Y     =  start.X, start.Y
                        end.X  , end.Y       =  end.X, end.Y
                    elif (fp_angle == 90):
                        start.X, start.Y     =  start.Y,  -start.X
                        end.X  , end.Y       =  end.Y  ,  -end.X
                    elif (fp_angle == 180):
                        start.X, start.Y     =  -start.X, -start.Y
                        end.X  , end.Y       =  -end.X  , -end.Y
                    elif (fp_angle == 270):    
                        start.X, start.Y     =  -start.Y,  start.X
                        end.X  , end.Y       =  -end.Y  ,  end.X
                    width = items.stroke.width
                    if width == None:
                        width = 0
                    fp_gr_x.append(fp_x_center + start.X - width/2)
                    fp_gr_x.append(fp_x_center + start.X + width/2)
                    fp_gr_x.append(fp_x_center + end.X - width/2)
                    fp_gr_x.append(fp_x_center + end.X + width/2)

                    fp_gr_y.append(fp_y_center + start.Y - width/2)
                    fp_gr_y.append(fp_y_center + start.Y + width/2)
                    fp_gr_y.append(fp_y_center + end.Y - width/2)
                    fp_gr_y.append(fp_y_center + end.Y + width/2)
                    logging.info("add a FpLine item, X start and end = (%g, %g), Y start and end = (%g, %g), width = %g" 
                % (fp_x_center + start.X, fp_x_center + end.X, fp_y_center + start.Y, fp_y_center + end.Y, width))
                elif type(items) == FpCircle:
                    center    = copy.deepcopy(items.center)
                    end       = items.end
                    width     = items.stroke.width
                    raius     = end.X - center.X
                    # set the correct center
                    if   (fp_angle == 0):
                        center.X, center.Y     =  center.X, center.Y
                    elif (fp_angle == 90):
                        center.X, center.Y     =  center.Y,  -center.X
                    elif (fp_angle == 180):
                        center.X, center.Y     =  -center.X, -center.Y
                    elif (fp_angle == 270):    
                        center.X, center.Y     =  -center.Y,  center.X
                    rx_center = fp_x_center + center.X
                    ry_center = fp_y_center + center.Y
                    if width == None:
                        width = 0
                    fp_gr_x.append(rx_center - raius - width/2)
                    fp_gr_x.append(rx_center + raius + width/2)
                    fp_gr_y.append(ry_center - raius - width/2)
                    fp_gr_y.append(ry_center + raius + width/2)
                    logging.info("add a FpCircle item, center = (%g, %g), raius = %g, width = %g" 
                % (rx_center, ry_center, raius, width))
                elif type(items) == FpPoly:
                    width = items.stroke.width
                    if width == None:
                        width = 0
                    for point in items.coordinates:
                        point = copy.deepcopy(point)
                        if   (fp_angle == 0):
                            point.X, point.Y     =  point.X, point.Y
                        elif (fp_angle == 90):
                            point.X, point.Y     =  point.Y,  -point.X
                        elif (fp_angle == 180):
                            point.X, point.Y     =  -point.X, -point.Y
                        elif (fp_angle == 270):    
                            point.X, point.Y     =  -point.Y,  point.X
                        fp_gr_x.append(fp_x_center + point.X - width/2)
                        fp_gr_x.append(fp_x_center + point.X + width/2)
                        fp_gr_y.append(fp_y_center + point.Y - width/2)
                        fp_gr_y.append(fp_y_center + point.Y + width/2)
                        logging.info("add a FpPoly point, X = %g, Y = %g, width = %g" 
                        % (fp_x_center + point.X, fp_y_center + point.Y, width))
                elif type(items) == FpArc:
                    start = copy.deepcopy(items.start)
                    # 粗糙建模暂未使用mid信息
                    mid   = copy.deepcopy(items.mid)
                    end   = copy.deepcopy(items.end)
                    if   (fp_angle == 0):
                        start.X, start.Y     =  start.X, start.Y
                        end.X  , end.Y       =  end.X, end.Y
                    elif (fp_angle == 90):
                        start.X, start.Y     =  start.Y,  -start.X
                        end.X  , end.Y       =  end.Y  ,  -end.X
                    elif (fp_angle == 180):
                        start.X, start.Y     =  -start.X, -start.Y
                        end.X  , end.Y       =  -end.X  , -end.Y
                    elif (fp_angle == 270):    
                        start.X, start.Y     =  -start.Y,  start.X
                        end.X  , end.Y       =  -end.Y  ,  end.X
                    width = items.stroke.width
                    if width == None:
                        width = 0
                    fp_gr_x.append(fp_x_center + start.X - width/2)
                    fp_gr_x.append(fp_x_center + start.X + width/2)
                    fp_gr_x.append(fp_x_center + end.X - width/2)
                    fp_gr_x.append(fp_x_center + end.X + width/2)

                    fp_gr_y.append(fp_y_center + start.Y - width/2)
                    fp_gr_y.append(fp_y_center + start.Y + width/2)
                    fp_gr_y.append(fp_y_center + end.Y - width/2)
                    fp_gr_y.append(fp_y_center + end.Y + width/2)
                    logging.info("add a FpArc item, X start and end = (%g, %g), Y start and end = (%g, %g), width = %g" 
                        % (fp_x_center + start.X, fp_x_center + end.X, fp_y_center + start.Y, fp_y_center + end.Y, width))

            pads    = []
            fp_pad_x   = []
            fp_pad_y   = []
            for itpad in footprint.pads:
                pad_x_offset  = copy.deepcopy(itpad.position.X)
                pad_y_offset  = copy.deepcopy(itpad.position.Y)
                pad_angle     = itpad.position.angle
                pad_num       = itpad.number

                if pad_angle == None:
                    pad_angle = 0
                elif pad_angle == -90:
                    pad_angle = 270
                
                try:
                    assert (pad_angle == 0) or (pad_angle == 90) or (pad_angle == 180) or (pad_angle == 270)
                except AssertionError as e:
                    logging.info("pad_angle error! node name:%s, pad number:%s, node_center = (%g, %g), offset = (%g, %g), pad_size = (%g, %g), pad_angle = %d" 
                    % (fp_name, pad_num, fp_x_center, fp_y_center, pad_x_offset, pad_y_offset, pad_size_x, pad_size_y, pad_angle))
                

                # set the correct offset
                if   (fp_angle == 0):
                    pad_x_offset, pad_y_offset     =  pad_x_offset, pad_y_offset
                elif (fp_angle == 90):
                    pad_x_offset, pad_y_offset     =  pad_y_offset,  -pad_x_offset
                elif (fp_angle == 180):
                    pad_x_offset, pad_y_offset     = -pad_x_offset, -pad_y_offset
                elif (fp_angle == 270):    
                    pad_x_offset, pad_y_offset     =  -pad_y_offset,  pad_x_offset
                
                # set the correct size
                pad_size_x, pad_size_y = copy.deepcopy(itpad.size.X), copy.deepcopy(itpad.size.Y)
                if pad_angle%180:
                    pad_size_x, pad_size_y = pad_size_y, pad_size_x

                pad_x_center = fp_x_center  + pad_x_offset
                pad_y_center = fp_y_center  + pad_y_offset
                logging.info("node name:%s, pad number:%s, node_center = (%g, %g), offset = (%g, %g), pad_size = (%g, %g)" 
                % (fp_name, pad_num, fp_x_center, fp_y_center, pad_x_offset, pad_y_offset, pad_size_x, pad_size_y))
                fp_pad_x.append(pad_x_center - pad_size_x/2.0)
                fp_pad_x.append(pad_x_center + pad_size_x/2.0)
                fp_pad_y.append(pad_y_center - pad_size_y/2.0)
                fp_pad_y.append(pad_y_center + pad_size_y/2.0)
                
                if lock:
                    pad_index =len(pad_lock)
                    pad = Pad(pad_x_offset, pad_y_offset, pad_index, node_index)
                    pad_lock.append(pad)
                else:
                    pad_index =len(pad_movable)
                    pad = Pad(pad_x_offset, pad_y_offset, pad_index, node_index)
                    pad_movable.append(pad)

                pads.append(pad)
                if itpad.net:
                    net_num = itpad.net.number
                    pad.set_netindex(net_num)
                    if (not lock):
                        self.Nets[net_num].add_pad(pad)
                        
            # some dirty code
            if "bm2" in self.input_file_path and fp_name == "B1":
                fp_x        = fp_gr_x
                fp_y        = fp_gr_y
            else:
                fp_x        = fp_gr_x + fp_pad_x
                fp_y        = fp_gr_y + fp_pad_y

            fp_x_left   = min(fp_x) if len(fp_x) > 0 else 0
            fp_y_bottom = min(fp_y) if len(fp_y) > 0 else 0
            fp_width    = max(fp_x) - fp_x_left   if len(fp_x) > 0 else 0
            fp_height   = max(fp_y) - fp_y_bottom if len(fp_y) > 0 else 0

            logging.info("node name:%s, width, height = (%g, %g), fp_x_left = %g, fp_y_bottom = %g" 
            % (fp_name, fp_width, fp_height, fp_x_left, fp_y_bottom))

            if lock:
                node = Node(fp_name, fp_x_center, fp_y_center, fp_x_left, fp_y_bottom, fp_width, fp_height, node_index, fp_angle, lock)
                node_lock.append(node)
            else:
                node = Node(fp_name, fp_x_center, fp_y_center, fp_x_left, fp_y_bottom, fp_width, fp_height, node_index, fp_angle, lock)
                node_movable.append(node)
            node.set_pads(pads)
            if not lock:
                node.update_padlist()

        for net in self.Nets:
            net.unlock_len = len(net.pads)
            
        for pad in pad_lock:
            pad.set_index(pad.pad_index + len(pad_movable), pad.node_index + len(node_movable))
            if pad.net_index != -1:
                self.Nets[pad.net_index].add_pad(pad)

        for node in node_lock:
            node.set_index(node.node_index + len(node_movable))
            node.update_padlist()
        
        self.num_movable_nodes = len(node_movable)
        self.Nodes = node_movable + node_lock
        self.Pads  = pad_movable  + pad_lock

        for pad in self.Pads:
            # offset is relate to center, now set it relate to left/bottom
            pad.set_offset(pad.x_offset + self.Nodes[pad.node_index].x_left2center, \
                           pad.y_offset + self.Nodes[pad.node_index].y_bottom2center)
        
        for net in self.Nets:
            net.update_padlist()
              
        def sort_node_by_area(node:Node):
            return node.size
        self.sorted_node = sorted(node_movable, key=sort_node_by_area, reverse=True)        
    
    def gen_rawdb(self, index):
        if index == 0:
            self.node_mask = [1] + [0]*(len(self.sorted_node) - 1)
        else:
            self.node_mask = [0] + self.node_mask[:-1] 
        
        node_lock:List[Node]    = []
        node_movable:List[Node] = []
        # 疑惑在于self.Nodes中的信息变更， self.sorted_node中的信息是否会变更呢
        for mask, node in zip(self.node_mask, self.sorted_node):
            if mask != 1:
                node_tmp = copy.deepcopy(node)
                node_tmp.lock = True
                node_lock.append(node_tmp)
            else:
                node_tmp = copy.deepcopy(node)
                node_movable.append(node_tmp)
                break
        
        num_pads = 0
        node_lock_raw    = copy.deepcopy(self.Nodes[self.num_movable_nodes:])
        nodes:List[Node] = node_movable + node_lock + node_lock_raw
        pads             = []
        nets             = copy.deepcopy(self.Nets_empty)
        for node_index, node in enumerate(nodes):
            node.set_index(node_index)
            for pad_index, pad in enumerate(node.pads):
                pad.set_index(pad_index + num_pads, node_index)
                nets[pad.net_index].add_pad(pad)
            node.update_padlist()
            pads += node.pads
            num_pads += len(node.pads)
        
        for net in nets:
            net.update_padlist()
        return nodes, pads, nets             

    def update_nodes(self, nodes:List[Node]):
        for node_pair in zip(nodes,self.Nodes):
            if node_pair[0].lock:
                continue
            else:
                node_pair[1].x_left   = node_pair[0].left_value
                node_pair[1].y_bottom = node_pair[0].bottom_value 
                node_pair[1].angle    = node_pair[0].angle_value       

    def wirte_back(self, output_file_path):
        index = -1
        for footprint in self.board.footprints:
            if footprint.locked:
                continue
            index += 1
            fp_angle = footprint.position.angle
            if fp_angle == None:
                fp_angle = 0
            angle    = self.Nodes[index].angle
            assert (angle == 0) or (angle == 90) or (angle == 180) or (angle == 270)

            for itpad in footprint.pads:
                if itpad.position.angle == None:
                    pad_angle = 0
                else:
                    pad_angle = itpad.position.angle
                itpad.position.angle  = (int(pad_angle) + int(angle) - fp_angle)%360

            footprint.position.X     = self.Nodes[index].x_center
            footprint.position.Y     = self.Nodes[index].y_center
            footprint.position.angle = int(angle)

        self.board.to_file(output_file_path)


if __name__ == "__main__":
    """
    @brief test dataset parser.
    """
    rawdb = Dataset("../../../../examples/test_data/bm7/bm7.unrouted.kicad_pcb")
    rawdb.load()

    hpwl = 0
    acc = 0
    for net in rawdb.Nets:
        hpwl_tmp= net.net_hpwl(rawdb.Nodes)
        hpwl += hpwl_tmp
        print("Net:{} {},HPWL:{}".format(acc, net.name, hpwl_tmp))
        acc += 1
    
    print("Total HPWL: ", hpwl)
    
    for db_index in range(rawdb.num_movable_nodes):
        nodes, pads, nets = rawdb.gen_rawdb(db_index)
