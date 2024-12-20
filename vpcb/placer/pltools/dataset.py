#dataset constructor
import math
from pltools.kicad_parser.kicad_pcb import Board
from pltools.kicad_parser.items import fpitems
from pltools.modeling import Module, Net, Pad

class Dataset:

    def __init__(self):
        self.modules = []
        self.Nets = []
        self.board = None

    def load(self, data_path):
        self.board = Board.from_file(data_path)

    #caculate placable boundary
        gr_x = []
        gr_y = []
        gr_boundary_range = 0.06
        for gr_line in self.board.graphicItems:
            gr_x.append(gr_line.end.X)
            gr_y.append(gr_line.end.Y)
            gr_x.append(gr_line.start.X)
            gr_y.append(gr_line.start.Y)
        self.boundary = [max(gr_x)-gr_boundary_range, min(gr_x)+gr_boundary_range, max(gr_y)-gr_boundary_range, min(gr_y)+gr_boundary_range]

    #build nets
        for itnet in self.board.nets:
            net = Net(itnet.name)
            self.Nets.append(net)

    #build modules and pads
        for footprint in self.board.footprints:
            x = footprint.position.X
            y = footprint.position.Y
            id = len(self.modules)
            angle = footprint.position.angle
            if angle == None:
                angle = 0
            if angle == -90:
                angle = 270
            lock = footprint.locked
            #layer = footprint.layer
            all_x = []
            all_y = []
            for items in footprint.graphicItems:
                # if items.layer == "F.CrtYd":
                #     pass
                if type(items) == fpitems.FpPoly:
                    for point in items.coordinates:
                        all_x.append(point.X)
                        all_y.append(point.Y)
                    wid = items.stroke.width
                if type(items) == fpitems.FpText:
                    if items.type == 'reference':
                        name = items.text
            width = max(all_x) - min(all_x) + wid + 0.2
            height = max(all_y) - min(all_y) + wid + 0.2
            if angle == -90 or angle == 90 or angle == 270:
                width_current = height
                height_current = width
            else:
                width_current = width
                height_current = height
            module = Module(name, x, y, width_current, height_current, id, angle, lock)
            self.modules.append(module)

            for itpad in footprint.pads:
                x_offset = itpad.position.X
                y_offset = itpad.position.Y
                pad = Pad(x_offset, y_offset, id)
                if itpad.net:
                    net_num = itpad.net.number
                    module.setNetlist(net_num)
                    self.Nets[net_num].addpad(pad)
                    self.Nets[net_num].link_module(module.id)

    def Get_boundary(self):
        return self.boundary
    
    def Get_Modules(self, part_id=0):
        part_modules = []
        for module in self.modules:
            if module.part_id == part_id:
                part_modules.append(module)
        return part_modules
    
    def Get_Nets(self, part_id=0):
        part_nets = []
        for net in self.Nets:
            if net.part_id == part_id:
                part_nets.append(net)
        return part_nets
    
    def Get_Board(self):
        return self.board
    
    def partition(self, boundary, config):
        '''partition the board
        TODO: implement the partition algorithm
        '''
        self.partition_list = []


        for module in self.modules:
            module.setPartitionid(config.id)

        for net in self.Nets:
            net.setPartitionid(config.id)

        return self.partition_list
    
    def update_modules(self, modules, part_id=0):
        index = 0
        for module in self.modules:
            if module.part_id == part_id:
                module.x_center = modules[index].x_center
                module.y_center = modules[index].y_center
                module.angle = modules[index].angle
                index += 1

    def update_board(self):
        '''update the modules to the board'''
        index = 0
        for footprint in self.board.footprints:
            footprint.position.X = self.modules[index].x_center
            footprint.position.Y = self.modules[index].y_center
            footprint.position.angle = self.modules[index].angle
            index += 1
    
    def wirte_back(self, path):
        import os
        current_directory = os.getcwd()
        parent_directory = os.path.dirname(current_directory)
        print(parent_directory)
        
        self.board.to_file(path)