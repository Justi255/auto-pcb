import os 
import sys 
import torch 
from torch.autograd import Function

sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)))
import draw_place_cpp
import PlaceDrawer
sys.path.pop() 

class DrawPlaceFunction(Function):
    @staticmethod
    def forward(
            pos,
            metric_info, 
            node_size_x, node_size_y, 
            pin_offset_x, pin_offset_y, 
            pin2node_map,
            netpin_start,
            flat_netpin, 
            xl, yl, xh, yh, 
            site_width, row_height, 
            bin_size_x, bin_size_y, 
            num_movable_nodes, num_filler_nodes,
            valid_num_nets, 
            filename
            ):
        ret = draw_place_cpp.forward(
                pos,
                metric_info, 
                node_size_x, node_size_y, 
                pin_offset_x, pin_offset_y, 
                pin2node_map, 
                netpin_start,
                flat_netpin, 
                xl, yl, xh, yh, 
                site_width, row_height, 
                bin_size_x, bin_size_y, 
                num_movable_nodes, num_filler_nodes, 
                valid_num_nets,
                filename
                )
        # if C/C++ API failed, try with python implementation 
        if not filename.endswith(".gds") and not ret:
            ret = PlaceDrawer.PlaceDrawer.forward(
                    pos,
                    metric_info, 
                    node_size_x, node_size_y, 
                    pin_offset_x, pin_offset_y, 
                    pin2node_map, 
                    xl, yl, xh, yh, 
                    site_width, row_height, 
                    bin_size_x, bin_size_y, 
                    num_movable_nodes, num_filler_nodes, 
                    filename
                    )
        return ret 

class DrawPlace(object):
    """ 
    @brief Draw placement
    """
    def __init__(self, node_size_x, node_size_y, pin_offset_x, pin_offset_y, pin2node_map, netpin_start, flat_netpin , xl, yl, xh, yh, \
                 site_width, row_height, bin_size_x, bin_size_y, num_movable_nodes, num_filler_nodes, valid_num_nets):
        """
        @brief initialization 
        """
        self.node_size_x = torch.from_numpy(node_size_x)
        self.node_size_y = torch.from_numpy(node_size_y)
        self.pin_offset_x = torch.from_numpy(pin_offset_x)
        self.pin_offset_y = torch.from_numpy(pin_offset_y)
        self.pin2node_map = torch.from_numpy(pin2node_map)
        self.netpin_start = torch.from_numpy(netpin_start)
        self.flat_netpin  = torch.from_numpy(flat_netpin)
        self.xl = xl 
        self.yl = yl 
        self.xh = xh 
        self.yh = yh 
        self.site_width = site_width
        self.row_height = row_height 
        self.bin_size_x = bin_size_x 
        self.bin_size_y = bin_size_y
        self.num_movable_nodes = num_movable_nodes
        self.num_filler_nodes = num_filler_nodes
        self.valid_num_nets = valid_num_nets

    def forward(self, pos, metric_info, filename): 
        """ 
        @param pos cell locations, array of x locations and then y locations
        @param metric_info, info about current solution 
        @param filename suffix specifies the format 
        """
        return DrawPlaceFunction.forward(
                pos,
                metric_info,
                self.node_size_x, 
                self.node_size_y, 
                self.pin_offset_x, 
                self.pin_offset_y, 
                self.pin2node_map, 
                self.netpin_start,
                self.flat_netpin,
                self.xl, 
                self.yl, 
                self.xh, 
                self.yh, 
                self.site_width, 
                self.row_height, 
                self.bin_size_x, 
                self.bin_size_y, 
                self.num_movable_nodes, 
                self.num_filler_nodes, 
                self.valid_num_nets,
                filename
                )

    def __call__(self, pos, metric_info, filename):
        """
        @brief top API 
        @param pos cell locations, array of x locations and then y locations 
        @param metric_info, info about current solution
        @param filename suffix specifies the format 
        """
        return self.forward(pos, metric_info, filename)
