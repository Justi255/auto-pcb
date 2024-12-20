"""
Parser for Netlist Protocol Buffer format from google
    docs:https://github.com/google-research/circuit_training/blob/main/docs/NETLIST_FORMAT.md

"""

import argparse

class PlcObject:
    def __init__(self, id):
        self.name = None
        self.node_id = id
        self.height = 0
        self.width = 0
        self.weight = 0
        self.x = -1
        self.x_offset = 0
        self.y = -1
        self.y_offset = 0
        self.m_name = None  # for macro name
        self.pb_type = None
        self.side = None
        self.orientation = None

    def IsHardMacro(self):
        if (self.pb_type == '"MACRO"'):
            return True
        else:
            return False

    def IsSoftMacro(self):
        if (self.pb_type == '"macro"'):
            return True
        else:
            return False

    def IsPort(self):
        if (self.pb_type == '"PORT"'):
            return True
        else:
            return False

    def GetLocation(self):
        return self.x - self.width / 2.0 , self.y - self.height / 2.0

    def GetWidth(self):
        return self.width

    def GetHeight(self):
        return self.height


class PBparser():
    def __init__(self) -> None:
        self.plc_object_list = []
        self.canvas_width = None
        self.canvas_height = None
        self.n_cols = None
        self.n_rows = None


    def from_file(self, netlist_file, plc_file):
        # read protocol buffer netlist
        with open(netlist_file) as f:
            netlist_content = f.read().splitlines()
        f.close()

        object_id = 0
        key = ""
        float_values = ['"height"', '"weight"', '"width"', '"x"', '"x_offset"', '"y"', '"y_offset"']
        placeholders = ['"macro_name"', '"orientation"', '"side"', '"type"']
        for line in netlist_content:
            words = line.split()
            if words[0] == 'node':
                if len(self.plc_object_list) > 0 and self.plc_object_list[-1].name == '"__metadata__"':
                    self.plc_object_list.pop(-1)
                self.plc_object_list.append(PlcObject(object_id)) # add object
                object_id += 1
            elif words[0] == 'name:':
                self.plc_object_list[-1].name = words[1]
            elif words[0] == 'key:' :
                key = words[1]  # the attribute name
            elif words[0] == 'placeholder:' :
                if key == placeholders[0]:
                    self.plc_object_list[-1].m_name = words[1]
                elif key == placeholders[1]:
                    self.plc_object_list[-1].orientation = words[1]
                elif key == placeholders[2]:
                    self.plc_object_list[-1].side = words[1]
                elif key == placeholders[3]:
                    self.plc_object_list[-1].pb_type = words[1]
            elif words[0] == 'f:' :
                if key == float_values[0]:
                    self.plc_object_list[-1].height = round(float(words[1]), 6)
                elif key == float_values[1]:
                    self.plc_object_list[-1].weight = round(float(words[1]), 6)
                elif key == float_values[2]:
                    self.plc_object_list[-1].width = round(float(words[1]), 6)
                elif key == float_values[3]:
                    self.plc_object_list[-1].x = round(float(words[1]),6)
                elif key == float_values[4]:
                    self.plc_object_list[-1].x_offset = round(float(words[1]), 6)
                elif key == float_values[5]:
                    self.plc_object_list[-1].y = round(float(words[1]),6)
                elif key == float_values[6]:
                    self.plc_object_list[-1].y_offset = round(float(words[1]), 6)

        # read plc file for all the plc objects
        with open(plc_file) as f:
            plc_content = f.read().splitlines()
        f.close()

        for line in plc_content:
            items = line.split()
            if (len(items) > 2 and items[0] == "#" and items[1] == "Columns"):
                self.n_cols = int(items[3])
                self.n_rows = int(items[6])
            elif (len(items) > 2 and items[0] == "#" and items[1] == "Width"):
                self.canvas_width = float(items[3])
                self.canvas_height = float(items[6])           

    def get_Obj_ist(self):
        return self.plc_object_list
        
    def get_canvas_width(self):
        return self.canvas_width
    
    def get_canvas_height(self):
        return self.canvas_height
    
    
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--netlist", help="protocol buffer netlist", type = str, default = "./src/vlsi_parser/test/ariane.pb.txt")
    arg_parser.add_argument("--plc", help="plc_file", type = str, default = "./src/vlsi_parser/test/ariane.plc")
    args = arg_parser.parse_args()

    PB_parser = PBparser()
    PB_parser.from_file(args.netlist, args.plc)
    obj_list = PB_parser.get_Obj_ist()
    
    ## visualization example with PB files
    import pltools.visualizer as vis
    
    vis_obj = []
    macro_color = None 
    for obj in obj_list:
        x, y = obj.GetLocation()
        if obj.IsHardMacro():
            macro_color = "purple"
        elif obj.IsSoftMacro():
            macro_color = "green"
        vis_obj.append(vis.VisualObject(x, y, size1=obj.GetWidth(), size2=obj.GetHeight(), color=macro_color))
    
    visualizer = vis.Visualizer(PB_parser.get_canvas_width(),PB_parser.get_canvas_height())    
    visualizer.add_object(vis_obj)

    visualizer.visualize_layout()
