# Desc: approximate modeling
from typing import List
import math
from shapely import affinity, LineString


class Module:
    def __init__(self, name, x, y, width, height, id, angle, lock, layer=1):
        self.name = name
        self.width = width
        self.height = height
        # self.terminal = terminal
        self.id = id
        self.angle = angle
        self.angle_num = angle/90

        # Move radius, limite the move range of modules in one step for SA
        self.radius = 100

        self.lock = lock
        self.layer = layer
        self.x_center = x
        self.y_center = y
        self.x_coordinate = x - 1 / 2 * width
        self.y_coordinate = y - 1 / 2 * height

        self.netlist = []
        self.poly = [(self.x_coordinate, self.y_coordinate), (self.x_coordinate + width, self.y_coordinate),
        (self.x_coordinate + width, self.y_coordinate + height), (self.x_coordinate, self.y_coordinate + height)]

        self.part_id = 0 ## default partition id is 0

    def setPos(self, x, y):
        # left down coordinate
        self.x_coordinate = x
        self.y_coordinate = y

        # center coordinate
        self.x_center = 1 / 2 * self.width + x
        self.y_center = 1 / 2 * self.height + y
        self.poly = [(x, y), (x + self.width, y), (x + self.width, y + self.height), (x, y + self.height)]

    def setNetlist(self, net_id):
        if net_id in self.netlist:
            pass
        else:
            self.netlist.append(net_id)

    def setRotation(self, r_angle_num):
        r_angle = r_angle_num * 90
        self.angle_num = (self.angle_num + r_angle_num) % 4
        self.angle = self.angle_num * 90
        poly1 = LineString(self.poly)
        rotated1 = affinity.rotate(poly1, r_angle, origin=(self.x_center, self.y_center))
        width1 = rotated1.bounds[2] - rotated1.bounds[0]
        height1 = rotated1.bounds[3] - rotated1.bounds[1]
        # width1 = round(rotated1.bounds[2] - rotated1.bounds[0], 4)
        # height1 = round(rotated1.bounds[3] - rotated1.bounds[1], 4)
        self.width = width1
        self.height = height1
        self.x_coordinate = self.x_center - 1 / 2 * width1
        self.y_coordinate = self.y_center - 1 / 2 * height1

        # opr1_x = min(max(self.minx, self.x_coordinate), self.maxx - self.width)
        # opr1_y = min(max(self.miny, self.y_coordinate), self.maxy - self.height)
        # self.setPos(opr1_x, opr1_y)

        # self.poly = [(self.x_coordinate, self.y_coordinate), (self.x_coordinate + width1, self.y_coordinate),
        #              (self.x_coordinate + width1, self.y_coordinate + height1),
        #              (self.x_coordinate, self.y_coordinate + height1)]
    
    def setPartitionid(self, part_id):
        self.part_id = part_id


    def print_para(self):
        print("===== Module:", self.id, "=====")
        print("Module name:", self.name)
        print("Assigned to partition:", self.part_id)
        print(self.x_center,self.y_center)
        print(self.angle)
        print("locked:", self.lock)
        print("     Netlist     ")
        for net in self.netlist:
            print("Net ", net)
    def build_model(self):
        # build model
        pass

class Net:
    def __init__(self, name, weight=1.0):
        self.pads = []
        self.module_id = []
        self.name = name
        self.weight = weight

        # 0 for hpwl, 1 for rudy, 2 for placement
        self.Cost = [0.0, 0.0, 0.0]

        self.part_id = 0  ## default partition id is 0

    def addpad(self,pad):
        self.pads.append(pad)

    def link_module(self,module_id):
        if module_id not in self.module_id:
            self.module_id.append(module_id)

    def reset(self):
        self.Cost = [0.0, 0.0, 0.0]

    def GetCost(self):
        return self.Cost

    def UpdateCost(self, Modules):
        if (len(self.pads) <= 1):
            self.Cost = [0.0, 0.0, 0.0]
        else:
            x_locs = []
            y_locs = []
            for pad in self.pads:
                if (Modules[pad.id].angle == 0):
                    x_locs.append(Modules[pad.id].x_center + pad.x_offset)
                    y_locs.append(Modules[pad.id].y_center + pad.y_offset)
                elif (Modules[pad.id].angle == 90):
                    x_locs.append(Modules[pad.id].x_center + pad.y_offset)
                    y_locs.append(Modules[pad.id].y_center - pad.x_offset)
                elif (Modules[pad.id].angle == 180):
                    x_locs.append(Modules[pad.id].x_center - pad.x_offset)
                    y_locs.append(Modules[pad.id].y_center - pad.y_offset)
                elif (Modules[pad.id].angle == 270) or (Modules[pad.id].angle == -90):
                    x_locs.append(Modules[pad.id].x_center - pad.y_offset)
                    y_locs.append(Modules[pad.id].y_center + pad.x_offset)
                else:
                    rad = float(Modules[pad.id].angle) * math.pi / 180.0
                    x_locs.append(
                        Modules[pad.id].x_center + pad.x_offset * math.cos(rad) + pad.y_offset * math.sin(rad))
                    y_locs.append(
                        Modules[pad.id].y_center + pad.y_offset * math.cos(rad) - pad.x_offset * math.sin(rad))
            max_x = max(x_locs)
            min_x = min(x_locs)
            max_y = max(y_locs)
            min_y = min(y_locs)
            self.Cost[0] = self.weight * (max(x_locs) - min(x_locs) + max(y_locs) - min(y_locs))
            self.Cost[1] = self.weight * self.Cost[0] / max((max(x_locs) - min(x_locs)) * (max(y_locs) - min(y_locs)), 1.0)

            self.Cost[2] = 0.0
            for i in range(len(x_locs) - 1):
                if x_locs[i] == x_locs[i+1] or y_locs[i] == y_locs[i+1]:
                    continue
                self.Cost[2] += self.weight * min(abs((x_locs[i] - x_locs[i+1]) / (y_locs[i] - y_locs[i+1])),
                                                      abs((y_locs[i] - y_locs[i+1]) / (x_locs[i] - x_locs[i+1])))

                # self.Cost[2] += abs(x_locs[0] - x_locs[i]) * abs(y_locs[0] - y_locs[i])

    def setPartitionid(self, part_id):
        self.part_id = part_id


    def print(self):
        id = 0
        print("Net name:", self.name)
        print("Assigned to partition:", self.part_id)
        print("There are ", len(self.pads), "pads in this net")
        for pad in self.pads:
            print("id: ",id, "  Net name:", self.name)
            id += 1
            print("x_offset: ", pad.x_offset, " y_offset: ", pad.y_offset)


class Pad:
    def __init__(self, x_offset, y_offset, id):
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.id = id

