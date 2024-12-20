import sys
import os
import re
import math
import time
import numpy as np
import torch
import logging
from Params import Params
from Dataset import Dataset
from Modeling import Node, Net, Pad
from typing import List
import pdb

datatypes = {
        'float32' : np.float32,
        'float64' : np.float64
        }

class PlaceDB (object):
    """
    @brief placement database
    """
    def __init__(self, params:Params, rawdb:Dataset):
        """
        initialization
        To avoid the usage of list, I flatten everything.
        """
        self.rawdb = rawdb # raw placement database, a C++ object
        self.device = None # determine the placement model run on cpu or gpu

        self.num_physical_nodes = None # number of real nodes, including movable nodes, and fixed nodes
        self.num_fixed_nodes = None # number of  fixed nodes
        self.node_name2id_map = {} # node name to id map, cell name
        self.node_names = None # 1D array, cell name
        self.node_pos    = None # 1D array, cell position  , x first then y
        self.node_pos_x  = None # 1D array, cell position x, movable first then fixed, finally filler
        self.node_pos_y  = None # 1D array, cell position y, movable first then fixed, finally filler
        self.node_orient = None # 1D array, cell orientation
        self.node_size   = None # 1D array, cell size , width first then height
        self.node_size_x = None # 1D array, cell width, movable first then fixed
        self.node_size_y = None # 1D array, cell height, movable first then fixed
        self.movable_macro_mask = None # 1D array, a mask determine which cell is macro
        self.num_pins_in_nodes = None # 1D array, pins a node have, movable first then fixed  

        self.pin_offset_x = None # 1D array, pin offset x to its node
        self.pin_offset_y = None # 1D array, pin offset y to its node
        self.pin_pos_x  = None   # 1D array, pin position x, movable first then fixed 
        self.pin_pos_y  = None   # 1D array, pin position y, movable first then fixed

        self.net_name2id_map = {} # net name to id map
        self.net_names = None # net name
        self.net_weights = None # weights for each net

        self.net2pin_map = None # array of 1D array, each row stores pin id
        self.flat_net2pin_map = None # flatten version of net2pin_map
        self.flat_net2pin_start_map = None # starting index of each net in flat_net2pin_map
        self.net_mask_all = None # 1D array, a mask includes all nets whose net_degree greater or equal 2
        self.net_mask_ignore_large_degrees = None # 1D array, a mask excludes the net in net_mask_all whose net_degree too large 

        self.node2pin_map = None # array of 1D array, contains pin id of each node
        self.flat_node2pin_map = None # flatten version of node2pin_map
        self.flat_node2pin_start_map = None # starting index of each node in flat_node2pin_map
        self.sorted_node_map = None # array of 1D array,sort nodes by size, return their sorted indices, designed for memory coalesce in electrical force

        self.pin2node_map = None # 1D array, contain parent node id of each pin
        self.pin2net_map = None # 1D array, contain parent net id of each pin
        self.pin_mask_ignore_fixed_macros  = None # 1D array, a mask ignore the pins belong to a fixed node

        self.regions = None # array of 1D array, placement regions like FENCE and GUIDE
        self.flat_region_boxes = None # flat version of regions
        self.flat_region_boxes_start = None # start indices of regions, length of num regions + 1
        self.node2fence_region_map = None # map cell to a region, maximum integer if no fence region

        self.xl = None
        self.yl = None
        self.xh = None
        self.yh = None

        self.shift_factor = None
        self.scale_factor = None

        self.row_height = None
        self.site_width = None

        self.bin_size_x = None
        self.bin_size_y = None
        self.num_bins_x = None
        self.num_bins_y = None

        self.num_movable_pins = None

        self.node_areas = None # array of 1D array, area a node takes, w*h
        self.total_movable_node_area = None # total movable cell area
        self.total_fixed_node_area = None # total fixed cell area
        self.total_space_area = None # total placeable space area excluding fixed cells

        # enable filler cells
        # the Idea from e-place and RePlace
        self.total_filler_node_area = None
        self.num_filler_nodes = None

        self.routing_grid_xl = None
        self.routing_grid_yl = None
        self.routing_grid_xh = None
        self.routing_grid_yh = None
        self.num_routing_grids_x = None
        self.num_routing_grids_y = None
        self.num_routing_layers = None
        self.unit_horizontal_capacity = None # per unit distance, projected to one layer
        self.unit_vertical_capacity = None # per unit distance, projected to one layer
        self.unit_horizontal_capacities = None # per unit distance, layer by layer
        self.unit_vertical_capacities = None # per unit distance, layer by layer
        self.initial_horizontal_demand_map = None # routing demand map from fixed cells, indexed by (grid x, grid y), projected to one layer
        self.initial_vertical_demand_map = None # routing demand map from fixed cells, indexed by (grid x, grid y), projected to one layer
        self.unit_pin_capacity = None # pin capacity each unit 
        self.initial_horizontal_utilization_map = None # routing utilization map from fixed cells, demand map div routing_grid_size * unit_capacity
        self.initial_vertical_utilization_map = None # routing utilization map from fixed cells, demand map div routing_grid_size * unit_capacity

        self.max_net_weight = None # maximum net weight in timing opt
        self.dtype = datatypes[params.dtype]

    def scale_pl(self, shift_factor, scale_factor):
        """
        @brief scale placement solution only
        @param shift_factor shift factor to make the origin of the layout to (0, 0)
        @param scale_factor scale factor
        """
        self.node_pos_x -= shift_factor[0]
        self.node_pos_x *= scale_factor
        self.node_pos_y -= shift_factor[1]
        self.node_pos_y *= scale_factor
        self.node_pos    = np.concatenate((self.node_pos_x, self.node_pos_y))

    def unscale_pl(self, shift_factor, scale_factor): 
        """
        @brief unscale placement solution only
        @param shift_factor shift factor to make the origin of the layout to (0, 0)
        @param scale_factor scale factor
        """
        unscale_factor = 1.0 / scale_factor
        if not(shift_factor[0] == 0 and shift_factor[1] == 0 and unscale_factor == 1.0):
            self.node_pos_x = self.node_pos_x * unscale_factor + shift_factor[0]
            self.node_pos_y = self.node_pos_y * unscale_factor + shift_factor[1]
            self.node_pos    = np.concatenate((self.node_pos_x, self.node_pos_y))

    def scale(self, routability_opt_flag, shift_factor, scale_factor):
        """
        @brief shift and scale coordinates
        @param routability_opt_flag if optimize routability
        @param shift_factor shift factor to make the origin of the layout to (0, 0)
        @param scale_factor scale factor
        """
        logging.info("shift coordinate system by (%g, %g), scale coordinate system by %g" 
                % (shift_factor[0], shift_factor[1], scale_factor))
        self.scale_pl(shift_factor, scale_factor)
        self.node_size_x *= scale_factor
        self.node_size_y *= scale_factor
        self.pin_offset_x *= scale_factor
        self.pin_offset_y *= scale_factor
        self.xl -= shift_factor[0]
        self.xl *= scale_factor
        self.yl -= shift_factor[1]
        self.yl *= scale_factor
        self.xh -= shift_factor[0]
        self.xh *= scale_factor
        self.yh -= shift_factor[1]
        self.yh *= scale_factor
        if routability_opt_flag:
            self.routing_grid_xl -= shift_factor[0]
            self.routing_grid_xl *= scale_factor
            self.routing_grid_yl -= shift_factor[1]
            self.routing_grid_yl *= scale_factor
            self.routing_grid_xh -= shift_factor[0]
            self.routing_grid_xh *= scale_factor
            self.routing_grid_yh -= shift_factor[1]
            self.routing_grid_yh *= scale_factor
        self.row_height *= scale_factor
        self.site_width *= scale_factor

        # shift factor for rectangle 
        box_shift_factor = np.array([shift_factor, shift_factor]).reshape(1, -1)
        self.total_space_area *= scale_factor * scale_factor # this is area
        self.total_movable_node_area *= scale_factor * scale_factor
        self.total_fixed_node_area *= scale_factor * scale_factor

        if len(self.flat_region_boxes): 
            self.flat_region_boxes -= box_shift_factor
            self.flat_region_boxes *= scale_factor

        for i in range(len(self.regions)):
            pass

    def sort(self):
        """
        @brief Sort net by degree.
        Sort pin array such that pins belonging to the same net is abutting each other
        """
        logging.info("sort nets by degree and pins by net")

        # sort nets by degree
        net_degrees = np.array([len(pins) for pins in self.net2pin_map])
        net_order = net_degrees.argsort() # indexed by new net_id, content is old net_id
        self.net_names = self.net_names[net_order]
        self.net2pin_map = self.net2pin_map[net_order]
        for net_id, net_name in enumerate(self.net_names):
            self.net_name2id_map[net_name] = net_id
        for new_net_id in range(len(net_order)):
            for pin_id in self.net2pin_map[new_net_id]:
                self.pin2net_map[pin_id] = new_net_id
        ## check
        #for net_id in range(len(self.net2pin_map)):
        #    for j in range(len(self.net2pin_map[net_id])):
        #        assert self.pin2net_map[self.net2pin_map[net_id][j]] == net_id

        # sort pins such that pins belonging to the same net is abutting each other
        pin_order = self.pin2net_map.argsort() # indexed new pin_id, content is old pin_id
        self.pin2net_map = self.pin2net_map[pin_order]
        self.pin2node_map = self.pin2node_map[pin_order]
        self.pin_offset_x = self.pin_offset_x[pin_order]
        self.pin_offset_y = self.pin_offset_y[pin_order]
        old2new_pin_id_map = np.zeros(len(pin_order), dtype=np.int32)
        for new_pin_id in range(len(pin_order)):
            old2new_pin_id_map[pin_order[new_pin_id]] = new_pin_id
        for i in range(len(self.net2pin_map)):
            for j in range(len(self.net2pin_map[i])):
                self.net2pin_map[i][j] = old2new_pin_id_map[self.net2pin_map[i][j]]
        for i in range(len(self.node2pin_map)):
            for j in range(len(self.node2pin_map[i])):
                self.node2pin_map[i][j] = old2new_pin_id_map[self.node2pin_map[i][j]]
        ## check
        #for net_id in range(len(self.net2pin_map)):
        #    for j in range(len(self.net2pin_map[net_id])):
        #        assert self.pin2net_map[self.net2pin_map[net_id][j]] == net_id
        #for node_id in range(len(self.node2pin_map)):
        #    for j in range(len(self.node2pin_map[node_id])):
        #        assert self.pin2node_map[self.node2pin_map[node_id][j]] == node_id

    @property
    def num_movable_nodes(self):
        """
        @return number of movable nodes
        """
        return self.num_physical_nodes - self.num_fixed_nodes

    @property
    def num_nodes(self):
        """
        @return number of movable nodes, and fillers
        """
        return self.num_physical_nodes + self.num_filler_nodes

    @property
    def num_nets(self):
        """
        @return number of nets
        """
        return len(self.net2pin_map)

    @property
    def num_pins(self):
        """
        @return number of pins
        """
        return len(self.pin2net_map)

    @property
    def width(self):
        """
        @return width of layout
        """
        return self.xh-self.xl

    @property
    def height(self):
        """
        @return height of layout
        """
        return self.yh-self.yl

    @property
    def area(self):
        """
        @return area of layout
        """
        return self.width*self.height

    def bin_xl(self, id_x):
        """
        @param id_x horizontal index
        @return bin xl
        """
        return self.xl+id_x*self.bin_size_x

    def bin_xh(self, id_x):
        """
        @param id_x horizontal index
        @return bin xh
        """
        return min(self.bin_xl(id_x)+self.bin_size_x, self.xh)

    def bin_yl(self, id_y):
        """
        @param id_y vertical index
        @return bin yl
        """
        return self.yl+id_y*self.bin_size_y

    def bin_yh(self, id_y):
        """
        @param id_y vertical index
        @return bin yh
        """
        return min(self.bin_yl(id_y)+self.bin_size_y, self.yh)

    def num_bins(self, l, h, bin_size):
        """
        @brief compute number of bins
        @param l lower bound
        @param h upper bound
        @param bin_size bin size
        @return number of bins
        """
        return int(np.ceil((h-l)/bin_size))

    def bin_centers(self, l, h, bin_size):
        """
        @brief compute bin centers
        @param l lower bound
        @param h upper bound
        @param bin_size bin size
        @return array of bin centers
        """
        num_bins = self.num_bins(l, h, bin_size)
        centers = np.zeros(num_bins, dtype=self.dtype)
        for id_x in range(num_bins):
            bin_l = l+id_x*bin_size
            bin_h = min(bin_l+bin_size, h)
            centers[id_x] = (bin_l+bin_h)/2
        return centers

    @property
    def routing_grid_size_x(self):
        return (self.routing_grid_xh - self.routing_grid_xl) / self.num_routing_grids_x

    @property
    def routing_grid_size_y(self):
        return (self.routing_grid_yh - self.routing_grid_yl) / self.num_routing_grids_y

    def all_hpwl(self, x, y, flat_net2pin_map, flat_net2pin_start_map, net_weights, net_mask):
        """
        return hpwl of all nets
        """
        if len(flat_net2pin_start_map) == 0:
            return 0
        hpwl = 0
        max_float32               = np.finfo(np.float32).max
        min_float32               = np.finfo(np.float32).min

        for net_id in range(len(flat_net2pin_start_map) -1 ):
            x_max_tmp                 = min_float32
            x_min_tmp                 = max_float32
            y_max_tmp                 = min_float32
            y_min_tmp                 = max_float32
            for j in  range(flat_net2pin_start_map[net_id], flat_net2pin_start_map[net_id+1]):
                x_max_tmp                 = max(x_max_tmp, x[flat_net2pin_map[j]])
                x_min_tmp                 = min(x_min_tmp, x[flat_net2pin_map[j]])
                y_max_tmp                 = max(y_max_tmp, y[flat_net2pin_map[j]])
                y_min_tmp                 = min(y_min_tmp, y[flat_net2pin_map[j]])
            hpwl_tmp = (x_max_tmp - x_min_tmp + y_max_tmp - y_min_tmp)*net_weights[net_id] if net_mask[net_id] else 0.0
            hpwl += hpwl_tmp
            logging.info("Net:{},HPWL:{}".format(net_id, hpwl_tmp))
        logging.info("Total HPWL = %g ", hpwl)
        return hpwl

    def overlap(self, xl1, yl1, xh1, yh1, xl2, yl2, xh2, yh2):
        """
        @brief compute overlap between two boxes
        @return overlap area between two rectangles
        """
        return max(min(xh1, xh2)-max(xl1, xl2), 0.0) * max(min(yh1, yh2)-max(yl1, yl2), 0.0)

    def density_map(self, x, y):
        """
        @brief this density map evaluates the overlap between cell and bins
        @param x horizontal cell locations
        @param y vertical cell locations
        @return density map
        """
        bin_index_xl = np.maximum(np.floor(x/self.bin_size_x).astype(np.int32), 0)
        bin_index_xh = np.minimum(np.ceil((x+self.node_size_x)/self.bin_size_x).astype(np.int32), self.num_bins_x-1)
        bin_index_yl = np.maximum(np.floor(y/self.bin_size_y).astype(np.int32), 0)
        bin_index_yh = np.minimum(np.ceil((y+self.node_size_y)/self.bin_size_y).astype(np.int32), self.num_bins_y-1)

        density_map = np.zeros([self.num_bins_x, self.num_bins_y])

        for node_id in range(self.num_physical_nodes):
            for ix in range(bin_index_xl[node_id], bin_index_xh[node_id]+1):
                for iy in range(bin_index_yl[node_id], bin_index_yh[node_id]+1):
                    density_map[ix, iy] += self.overlap(
                            self.bin_xl(ix), self.bin_yl(iy), self.bin_xh(ix), self.bin_yh(iy),
                            x[node_id], y[node_id], x[node_id]+self.node_size_x[node_id], y[node_id]+self.node_size_y[node_id]
                            )

        for ix in range(self.num_bins_x):
            for iy in range(self.num_bins_y):
                density_map[ix, iy] /= (self.bin_xh(ix)-self.bin_xl(ix))*(self.bin_yh(iy)-self.bin_yl(iy))

        return density_map

    def density_overflow(self, x, y, target_density):
        """
        @brief if density of a bin is larger than target_density, consider as overflow bin
        @param x horizontal cell locations
        @param y vertical cell locations
        @param target_density target density
        @return density overflow cost
        """
        density_map = self.density_map(x, y)
        return np.sum(np.square(np.maximum(density_map-target_density, 0.0)))

    def print_node(self, node_id):
        """
        @brief print node information
        @param node_id cell index
        """
        logging.debug("node %s(%d), size (%g, %g), pos (%g, %g)" % (self.node_names[node_id], node_id, self.node_size_x[node_id], self.node_size_y[node_id], self.node_x[node_id], self.node_y[node_id]))
        pins = "pins "
        for pin_id in self.node2pin_map[node_id]:
            pins += "%s(%s, %d) " % (self.node_names[self.pin2node_map[pin_id]], self.net_names[self.pin2net_map[pin_id]], pin_id)
        logging.debug(pins)

    def print_net(self, net_id):
        """
        @brief print net information
        @param net_id net index
        """
        logging.debug("net %s(%d)" % (self.net_names[net_id], net_id))
        pins = "pins "
        for pin_id in self.net2pin_map[net_id]:
            pins += "%s(%s, %d) " % (self.node_names[self.pin2node_map[pin_id]], self.net_names[self.pin2net_map[pin_id]], pin_id)
        logging.debug(pins)

    #def flatten_nested_map(self, net2pin_map):
    #    """
    #    @brief flatten an array of array to two arrays like CSV format
    #    @param net2pin_map array of array
    #    @return a pair of (elements, cumulative column indices of the beginning element of each row)
    #    """
    #    # flat netpin map, length of #pins
    #    flat_net2pin_map = np.zeros(len(pin2net_map), dtype=np.int32)
    #    # starting index in netpin map for each net, length of #nets+1, the last entry is #pins
    #    flat_net2pin_start_map = np.zeros(len(net2pin_map)+1, dtype=np.int32)
    #    count = 0
    #    for i in range(len(net2pin_map)):
    #        flat_net2pin_map[count:count+len(net2pin_map[i])] = net2pin_map[i]
    #        flat_net2pin_start_map[i] = count
    #        count += len(net2pin_map[i])
    #    assert flat_net2pin_map[-1] != 0
    #    flat_net2pin_start_map[len(net2pin_map)] = len(pin2net_map)

    #    return flat_net2pin_map, flat_net2pin_start_map

    def initialize_from_gendb(self, params:Params, nodes:List[Node], nets:List[Net], pins:List[Pad]):
        """
        @brief initialize data members from raw database
        @param params parameters
        """
        xl, yl, xh, yh         = self.rawdb.layout
        num_pins               = len(pins)
        num_nets               = len(nets)
        num_physical_nodes     = len(nodes)
        
        # regions相关数据结构
        regions                 = []
        flat_region_boxes       = []
        flat_region_boxes_start = [0]
        node2fence_region_map   = []

        # node相关数据结构
        num_movable_nodes         = 0
        num_fixed_nodes           = 0
        total_space_area          = 0
        total_movable_node_area   = 0
        total_fixed_node_area     = 0

        node_pos_fixed_x          = []
        node_pos_fixed_y          = []
        node_pos_movable_x        = []
        node_pos_movable_y        = []

        node_size_fixed_x         = []
        node_size_fixed_y         = []
        node_size_movable_x       = []
        node_size_movable_y       = []

        node2pin_map_fixed        = []
        num_pins_in_nodes_fixed   = []
        node2pin_map_movable      = []
        num_pins_in_nodes_movable = []

        for node in nodes:
            if node.lock:
                num_fixed_nodes         += 1
                total_fixed_node_area   += node.width*node.height
                node_pos_fixed_x.append(node.x_left)
                node_pos_fixed_y.append(node.y_bottom)
                node_size_fixed_x.append(node.width)
                node_size_fixed_y.append(node.height)
                node2pin_map_fixed.append(node.padlist)
                num_pins_in_nodes_fixed.append(len(node.padlist))
            else:
                num_movable_nodes       += 1
                total_movable_node_area += node.width*node.height
                node_pos_movable_x.append(node.x_left)
                node_pos_movable_y.append(node.y_bottom)
                node_size_movable_x.append(node.width)
                node_size_movable_y.append(node.height)
                node2pin_map_movable.append(node.padlist)
                num_pins_in_nodes_movable.append(len(node.padlist))

        if params.random_center_init_flag:
            logging.info("move cells to the center of layout")
            node_pos_movable_x = (np.array([(xl * 1.0 + xh * 1.0) / 2]*num_movable_nodes) - np.array(node_size_movable_x)/2).tolist()
            node_pos_movable_y = (np.array([(yl * 1.0 + yh * 1.0) / 2]*num_movable_nodes) - np.array(node_size_movable_y)/2).tolist()
            
        total_area       = (xh - xl)*(yh - yl)
        total_space_area = total_area - total_fixed_node_area
        node_pos         = node_pos_movable_x + node_pos_fixed_x + node_pos_movable_y + node_pos_fixed_y
        node_pos_x       = node_pos_movable_x + node_pos_fixed_x
        node_pos_y       = node_pos_movable_y + node_pos_fixed_y
        node_size_x      = node_size_movable_x + node_size_fixed_x
        node_size_y      = node_size_movable_y + node_size_fixed_y
        node_areas       = (np.array(node_size_x) * np.array(node_size_y)).tolist()
        node_size        = node_size_x + node_size_y

        if params.target_density < 1:
            movable_macro_mask = [1]*num_movable_nodes
        else:  # no movable macros
            movable_macro_mask = None

        node2pin_map            = node2pin_map_movable + node2pin_map_fixed
        flat_node2pin_map       = np.zeros(num_pins, dtype=np.int32)
        flat_node2pin_start_map = np.zeros(num_physical_nodes+1, dtype=np.int32)
        num_pins_in_nodes       = num_pins_in_nodes_movable + num_pins_in_nodes_fixed

        count = 0
        for i in range(len(node2pin_map)):
            flat_node2pin_map[count:count+len(node2pin_map[i])] = node2pin_map[i]
            flat_node2pin_start_map[i] = count 
            count += len(node2pin_map[i])
        flat_node2pin_start_map[len(node2pin_map)] = count
        sorted_node_map = np.argsort(node_size_movable_x).tolist()

        # pin相关数据结构
        pin_offset_x = []
        pin_offset_y = []
        # for debug
        pin_pos_x    = []
        pin_pos_y    = []
        pin2node_map = []
        pin2net_map  = []
        for pin in pins:
            pin_offset_x.append(pin.x_offset)
            pin_offset_y.append(pin.y_offset)
            # for debug
            pin_pos_x.append(nodes[pin.node_index].x_left + pin.x_offset)
            pin_pos_y.append(nodes[pin.node_index].y_bottom + pin.y_offset)
            pin2node_map.append(pin.node_index)
            pin2net_map.append(pin.net_index)
        pin_mask_ignore_fixed_macros = (np.array(pin2node_map) >= num_movable_nodes).tolist()

        # net相关数据结构
        net2pin_map = []
        for net in nets:
            net2pin_map.append(net.padlist)
        flat_net2pin_map       = np.zeros(num_pins, dtype=np.int32)
        flat_net2pin_start_map = np.zeros(num_nets+1, dtype=np.int32)
        # 构建展平的相关数据结构
        count = 0
        for i in range(len(net2pin_map)):
            flat_net2pin_map[count:count+len(net2pin_map[i])] = net2pin_map[i]
            flat_net2pin_start_map[i] = count 
            count += len(net2pin_map[i])
        flat_net2pin_start_map[len(net2pin_map)] = count
        net_degrees                   = np.array([len(net2pin) for net2pin in net2pin_map])
        net_mask_all                  = (2 <= net_degrees).tolist()
        valid_num_nets                = sum(net_mask_all)
        net_mask_ignore_large_degrees = np.logical_and(net_mask_all, net_degrees < params.ignore_net_degree).tolist()
        net_weights                   = np.ones(num_nets, dtype=self.dtype).tolist()

        # 可布线性相关
        if params.routability_opt_flag:
            routing_grid_xl               = xl
            routing_grid_yl               = yl
            routing_grid_xh               = xh
            routing_grid_yh               = yh
            num_routing_grids_x           = params.route_num_bins_x
            num_routing_grids_y           = params.route_num_bins_y
            routing_grid_size_x           = (routing_grid_xh - routing_grid_xl) / num_routing_grids_x
            routing_grid_size_y           = (routing_grid_yh - routing_grid_yl) / num_routing_grids_y
            unit_horizontal_capacity      = params.unit_horizontal_capacity
            unit_vertical_capacity        = params.unit_vertical_capacity
            
            initial_horizontal_demand_map = np.zeros((params.route_num_bins_x, params.route_num_bins_y))
            initial_vertical_demand_map   = np.zeros((params.route_num_bins_x, params.route_num_bins_y))

            unit_pin_capacity = np.array(num_pins_in_nodes[:num_movable_nodes]) / np.array(node_areas[:num_movable_nodes])
            avg_pin_capacity  = np.mean(np.array(unit_pin_capacity)) * params.target_density
            unit_pin_capacity = np.clip(avg_pin_capacity, None, params.unit_pin_capacity)
            logging.info("unit_pin_capacity = %g" %(unit_pin_capacity))

            initial_horizontal_utilization_map = initial_horizontal_demand_map/(
                    routing_grid_size_y *
                    unit_horizontal_capacity)
            initial_vertical_utilization_map = initial_vertical_demand_map/(
                    routing_grid_size_x *
                    unit_vertical_capacity)

        self.device                        = torch.device("cuda" if params.gpu else "cpu")

        self.row_height                    = params.row_height
        self.site_width                    = params.site_width

        self.shift_factor                  = params.shift_factor
        self.scale_factor                  = params.scale_factor

        self.num_physical_nodes            = num_physical_nodes
        self.num_fixed_nodes               = num_fixed_nodes
        self.node_names                    = np.array([node.name for node in nodes], dtype=np.string_)

        self.node_areas                    = np.array(node_areas, dtype=self.dtype)
        self.total_fixed_node_area         = total_fixed_node_area
        self.total_movable_node_area       = total_movable_node_area
        self.total_space_area              = total_space_area

        self.xl                            = xl
        self.yl                            = yl
        self.xh                            = xh
        self.yh                            = yh

        self.regions                       = np.array(regions, dtype=self.dtype)
        self.flat_region_boxes             = np.array(flat_region_boxes, dtype=self.dtype)
        self.flat_region_boxes_start       = np.array(flat_region_boxes_start, dtype=np.int32)
        self.node2fence_region_map         = np.array(node2fence_region_map, dtype=np.int32)

        self.node_pos                      = np.array(node_pos, dtype=self.dtype)
        self.node_pos_x                    = np.array(node_pos_x, dtype=self.dtype)
        self.node_pos_y                    = np.array(node_pos_y, dtype=self.dtype)
        self.node_size                     = np.array(node_size, dtype=self.dtype)
        self.node_size_x                   = np.array(node_size_x, dtype=self.dtype)
        self.node_size_y                   = np.array(node_size_y, dtype=self.dtype)
        if movable_macro_mask is not None:
            self.movable_macro_mask            = np.array(movable_macro_mask,  dtype=np.uint8)
        self.num_pins_in_nodes             = np.array(num_pins_in_nodes, dtype=np.int32)
        self.pin_weights                   = np.array(num_pins_in_nodes, dtype=self.dtype)
        self.node2pin_map                  = np.array(node2pin_map, dtype=object)
        self.flat_node2pin_map             = np.array(flat_node2pin_map, dtype=np.int32)
        self.flat_node2pin_start_map       = np.array(flat_node2pin_start_map, dtype=np.int32)
        self.sorted_node_map               = np.array(sorted_node_map, dtype=np.int32)

        self.pin_offset_x                  = np.array(pin_offset_x, dtype=self.dtype)
        self.pin_offset_y                  = np.array(pin_offset_y, dtype=self.dtype)
        # for debug
        self.pin_pos_x                     = np.array(pin_pos_x, dtype=self.dtype)
        self.pin_pos_y                     = np.array(pin_pos_y, dtype=self.dtype)
        self.pin2node_map                  = np.array(pin2node_map, dtype=np.int32)
        self.pin2net_map                   = np.array(pin2net_map, dtype=np.int32)
        self.pin_mask_ignore_fixed_macros  = np.array(pin_mask_ignore_fixed_macros, dtype=np.uint8)
        
        self.net_names                     = np.array([net.name for net in nets], dtype=np.string_)
        self.net2pin_map                   = np.array(net2pin_map, dtype=object)
        self.flat_net2pin_map              = np.array(flat_net2pin_map, dtype=np.int32)
        self.flat_net2pin_start_map        = np.array(flat_net2pin_start_map, dtype=np.int32)
        self.net_mask_all                  = np.array(net_mask_all, dtype=np.uint8)
        self.valid_num_nets                = np.array(valid_num_nets, dtype=np.int32)
        self.net_mask_ignore_large_degrees = np.array(net_mask_ignore_large_degrees, dtype=np.uint8)
        self.net_weights                   = np.array(net_weights, dtype=self.dtype)

        # 可布线性相关
        if params.routability_opt_flag:
            self.routing_grid_xl                     = routing_grid_xl
            self.routing_grid_yl                     = routing_grid_yl
            self.routing_grid_xh                     = routing_grid_xh
            self.routing_grid_yh                     = routing_grid_yh
            self.num_routing_grids_x                 = num_routing_grids_x
            self.num_routing_grids_y                 = num_routing_grids_y
            self.unit_horizontal_capacity            = np.array(unit_horizontal_capacity, dtype=self.dtype)
            self.unit_vertical_capacity              = np.array(unit_vertical_capacity, dtype=self.dtype)
            self.initial_horizontal_demand_map       = np.array(initial_horizontal_demand_map, dtype=self.dtype)
            self.initial_vertical_demand_map         = np.array(initial_vertical_demand_map, dtype=self.dtype) 
            self.unit_pin_capacity                   = np.array(unit_pin_capacity, dtype=self.dtype)
            self.initial_horizontal_utilization_map  = np.array(initial_horizontal_utilization_map, dtype=self.dtype)
            self.initial_vertical_utilization_map    = np.array(initial_vertical_utilization_map, dtype=self.dtype)
        
        if params.test_hpwl_flag:
           _ = self.all_hpwl(pin_pos_x, pin_pos_y, flat_net2pin_map, flat_net2pin_start_map, net_weights, net_mask_all)


    def initialize_num_bins(self, params:Params):
        """
        @brief initialize number of bins with a heuristic method, which many not be optimal.
        The heuristic is adapted form RePlAce, 2x2 to 4096x4096. 
        """
        # derive bin dimensions by keeping the aspect ratio 
        # this bin setting is not for global placement, only for other steps 
        # global placement has its bin settings defined in global_place_stages
        if params.num_bins_x <= 1 or params.num_bins_y <= 1: 
            total_bin_area = self.area
            avg_movable_area = self.total_movable_node_area / self.num_movable_nodes
            ideal_bin_area = avg_movable_area / params.target_density
            ideal_num_bins = total_bin_area / ideal_bin_area
            if (ideal_num_bins < 4): # smallest number of bins 
                ideal_num_bins = 4
            aspect_ratio = (self.yh - self.yl) / (self.xh - self.xl)
            y_over_x = True 
            if aspect_ratio < 1: 
                aspect_ratio = 1.0 / aspect_ratio
                y_over_x = False 
            aspect_ratio = int(math.pow(2, round(math.log2(aspect_ratio))))
            num_bins_1d = 2 # min(num_bins_x, num_bins_y)
            while num_bins_1d <= 4096:
                found_num_bins = num_bins_1d * num_bins_1d * aspect_ratio
                if (found_num_bins > ideal_num_bins / 4 and found_num_bins <= ideal_num_bins): 
                    break 
                num_bins_1d *= 2
            if y_over_x:
                self.num_bins_x = num_bins_1d
                self.num_bins_y = num_bins_1d * aspect_ratio
            else:
                self.num_bins_x = num_bins_1d * aspect_ratio
                self.num_bins_y = num_bins_1d
            params.num_bins_x = self.num_bins_x
            params.num_bins_y = self.num_bins_y
        else:
            self.num_bins_x = params.num_bins_x
            self.num_bins_y = params.num_bins_y

    def __call__(self, params:Params, nodes:List[Node], nets:List[Net], pins:List[Pad]):
        """
        @brief top API to read placement files
        @param params parameters
        """
        tt = time.time()

        self.initialize_from_gendb(params, nodes, nets, pins)
        self.initialize(params)

        logging.info("reading benchmark takes %g seconds" % (time.time()-tt))

    def initialize(self, params:Params):
        """
        @brief initialize data members after reading
        @param params parameters
        """
        # shift and scale
        # adjust shift_factor and scale_factor if not set
        params.shift_factor[0] = self.xl
        params.shift_factor[1] = self.yl
        logging.info("set shift_factor = (%g, %g), as original row bbox = (%g, %g, %g, %g)" 
                % (params.shift_factor[0], params.shift_factor[1], self.xl, self.yl, self.xh, self.yh))

        logging.info("set scale_factor = %g" % (params.scale_factor))
        self.scale(params.routability_opt_flag, params.shift_factor, params.scale_factor)

        content = """
        ================================= Benchmark Statistics =================================
        #physical nodes = %d, #movable = %d, #nets = %d
        die area = (%g, %g, %g, %g) %g, #pins = %d\n
        """ % (
                self.num_physical_nodes, self.num_movable_nodes, self.num_nets,
                self.xl, self.yl, self.xh, self.yh, self.area, self.num_pins)
        content += "total_movable_node_area = %g, total_fixed_node_area = %g, total_space_area = %g\n" \
            % (self.total_movable_node_area, self.total_fixed_node_area, self.total_space_area)
        
        target_density = min(self.total_movable_node_area / self.total_space_area, 1.0)
        if target_density > params.target_density:
            logging.warning("target_density %g is smaller than utilization %g, ignored" % (params.target_density, target_density))
            params.target_density = target_density
        content += "\tutilization = %g, target_density = %g\n" % (self.total_movable_node_area / self.total_space_area, params.target_density)

        # insert filler nodes
        if len(self.regions) > 0:
            pass

        if params.enable_fillers:
            # the way to compute this is still tricky; we need to consider place_io together on how to
            # summarize the area of fixed cells, which may overlap with each other.
            if len(self.regions) > 0:
                pass
            else:
                node_size_order = np.argsort(self.node_size_x[: self.num_movable_nodes])
                range_lb = int(self.num_movable_nodes*0.05)
                range_ub = int(self.num_movable_nodes*0.95)
                if range_lb >= range_ub: # when there are too few cells, i.e., <= 1
                    filler_size_x = 0
                else:
                    filler_size_x = np.mean(self.node_size_x[node_size_order[range_lb:range_ub]])
                filler_size_y = self.row_height
                placeable_area = max(self.area - self.total_fixed_node_area, self.total_space_area)
                content += "\tuse placeable_area = %g to compute fillers\n" % (placeable_area)
                self.total_filler_node_area = max(
                    placeable_area * params.target_density - self.total_movable_node_area, 0.0
                )
                filler_area = filler_size_x * filler_size_y
                if filler_area == 0: 
                    self.num_filler_nodes = 0
                else:
                    self.num_filler_nodes = int(round(self.total_filler_node_area / filler_area))
                    node_size_x = np.concatenate(
                        [
                            self.node_size_x,
                            np.full(self.num_filler_nodes, fill_value=filler_size_x, dtype=self.node_size_x.dtype),
                        ]
                    )
                    node_size_y = np.concatenate(
                        [
                            self.node_size_y,
                            np.full(self.num_filler_nodes, fill_value=filler_size_y, dtype=self.node_size_y.dtype),
                        ]
                    )
                    node_size = np.concatenate(
                        [
                            node_size_x,
                            node_size_y,
                        ]
                    )

                    node_pos_x = np.concatenate(
                        [
                            self.node_pos_x,
                            np.random.uniform(
                                low=self.xl,
                                high=self.xh - node_size_x[-self.num_filler_nodes],
                                size=self.num_filler_nodes,
                            ),
                        ]
                    )
                    node_pos_y = np.concatenate(
                        [
                            self.node_pos_y,
                            np.random.uniform(
                                low=self.yl,
                                high=self.yh - node_size_y[-self.num_filler_nodes],
                                size=self.num_filler_nodes,
                            ),
                        ]
                    )
                    node_pos = np.concatenate(
                        [
                            node_pos_x,
                            node_pos_y,
                        ]
                    )
                    node_areas                         = (np.array(node_size_x) * np.array(node_size_y)).tolist()
                    self.node_areas                    = np.array(node_areas, dtype=self.dtype)
                    self.node_pos                      = np.array(node_pos, dtype=self.dtype)
                    self.node_pos_x                    = np.array(node_pos_x, dtype=self.dtype)
                    self.node_pos_y                    = np.array(node_pos_y, dtype=self.dtype)
                    self.node_size                     = np.array(node_size, dtype=self.dtype)
                    self.node_size_x                   = np.array(node_size_x, dtype=self.dtype)
                    self.node_size_y                   = np.array(node_size_y, dtype=self.dtype)

                content += "\ttotal_filler_node_area = %g, #fillers = %d, filler sizes = %gx%g\n" % (
                    self.total_filler_node_area,
                    self.num_filler_nodes,
                    filler_size_x,
                    filler_size_y,
                )
        else:
            self.total_filler_node_area = 0
            self.num_filler_nodes = 0
            filler_size_x, filler_size_y = 0, 0
            if len(self.regions) > 0:
                pass

            content += "\ttotal_filler_node_area = %g, #fillers = %d, filler sizes = %gx%g\n" % (
                self.total_filler_node_area,
                self.num_filler_nodes,
                filler_size_x,
                filler_size_y,
            )

        # set number of bins 
        # derive bin dimensions by keeping the aspect ratio 
        self.initialize_num_bins(params)
        # set bin size 
        self.bin_size_x = (self.xh - self.xl) / self.num_bins_x
        self.bin_size_y = (self.yh - self.yl) / self.num_bins_y

        content += "\tnum_bins = %dx%d, bin sizes = %gx%g\n" % (self.num_bins_x, self.num_bins_y, self.bin_size_x, self.bin_size_y)

        if params.routability_opt_flag:
            content += "\t================================== routing information =================================\n"
            content += "\trouting grids (%d, %d)\n" % (self.num_routing_grids_x, self.num_routing_grids_y)
            content += "\trouting grid sizes (%g, %g)\n" % (self.routing_grid_size_x, self.routing_grid_size_y)
            content += "\trouting capacity H/V (%g, %g) per tile\n" % (self.unit_horizontal_capacity * self.routing_grid_size_y, self.unit_vertical_capacity * self.routing_grid_size_x)
        content += "\t========================================================================================"

        logging.info(content)

    def write(self, filename):
        """
        @brief write placement solution
        @param filename output file name
        """
        tt = time.time()
        logging.info("writing to %s" % (filename))

        # write solution
        self.rawdb.wirte_back(filename)
        logging.info("write placement solution takes %.3f seconds" % (time.time()-tt))
    
    def apply(self, params:Params, node_pos_x, node_pos_y):
        """
        @brief apply placement solution and update database
        """
        # assign solution
        self.node_pos_x[:self.num_movable_nodes] = node_pos_x[:self.num_movable_nodes]
        self.node_pos_y[:self.num_movable_nodes] = node_pos_y[:self.num_movable_nodes]

        # unscale locations
        self.unscale_pl(params.shift_factor, params.scale_factor)
        pos_movable_x     = self.node_pos_x[:self.num_movable_nodes]
        pos_movable_y     = self.node_pos_y[:self.num_movable_nodes]

        # update raw database
        self.rawdb.update_nodes(pos_movable_x, pos_movable_y)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("One input parameters in json format in required")

    params = Params()
    params.load(sys.argv[sys.argv[1]])
    logging.info("parameters = %s" % (params))

    db = PlaceDB()
    db(params)

    db.print_node(1)
    db.print_net(1)
