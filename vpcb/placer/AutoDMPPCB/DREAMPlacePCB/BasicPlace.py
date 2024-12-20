import imageio
import os
import time
import logging
from typing   import List
from Modeling import Node
from Dataset  import Dataset 
from PlaceDB  import PlaceDB
from Params  import Params
import EvalMetrics
import numpy as np
import torch
import torch.nn as nn

# import ops
from ops.pin_pos.pin_pos                                         import PinPos
from ops.logsumexp_wirelength.logsumexp_wirelength               import LogSumExpWirelength
from ops.weighted_average_wirelength.weighted_average_wirelength import WeightedAverageWirelength
from ops.electric_potential.electric_overflow                    import ElectricOverflow
from ops.electric_potential.electric_potential                   import ElectricPotential
from ops.hpwl.hpwl                                               import HPWL
from ops.move_boundary.move_boundary                             import MoveBoundary
from ops.pin_weight_sum.pin_weight_sum                           import PinWeightSum
from ops.legality_check.legality_check                           import LegalityCheck
from ops.draw_place.draw_place                                   import DrawPlace
from ops.macro_legalize.macro_legalize                           import MacroLegalize
from ops.rudy.rudy                                               import Rudy
from ops.pin_utilization.pin_utilization                         import PinUtilization
from ops.adjust_node_area.adjust_node_area                       import AdjustNodeArea

class PlaceDataCollection(object):
    """
    @brief A wraper for all data tensors on device for building ops
    """
    def __init__(self, pos, params:Params, placedb:PlaceDB, device):
        """
        @brief initialization
        @param pos locations of cells
        @param params parameters
        @param placedb placement database
        @param device cpu or cuda
        """

        self.pos                              = pos
        self.xl                               = placedb.xl
        self.yl                               = placedb.yl
        self.xh                               = placedb.xh
        self.yh                               = placedb.yh

        self.row_height                       = placedb.row_height
        self.site_width                       = placedb.site_width

        self.shift_factor                     = placedb.shift_factor
        self.scale_factor                     = placedb.scale_factor

        self.num_pins                         = placedb.num_pins
        self.num_nets                         = placedb.num_nets
        self.num_nodes                        = placedb.num_nodes
        self.num_physical_nodes               = placedb.num_physical_nodes
        self.num_filler_nodes                 = placedb.num_filler_nodes
        self.num_movable_nodes                = placedb.num_movable_nodes
        self.num_fixed_nodes                  = placedb.num_fixed_nodes

        self.area                             = placedb.area
        self.total_space_area                 = placedb.total_space_area
        self.total_filler_node_area           = placedb.total_filler_node_area
        self.total_movable_node_area          = placedb.total_movable_node_area
        self.total_fixed_node_area            = placedb.total_fixed_node_area

        #可布线性相关
        if params.routability_opt_flag:
            self.routing_grid_xl          = placedb.routing_grid_xl
            self.routing_grid_yl          = placedb.routing_grid_yl
            self.routing_grid_xh          = placedb.routing_grid_xh
            self.routing_grid_yh          = placedb.routing_grid_yh
            self.num_routing_grids_x      = placedb.num_routing_grids_x
            self.num_routing_grids_y      = placedb.num_routing_grids_y
            self.unit_horizontal_capacity = placedb.unit_horizontal_capacity
            self.unit_vertical_capacity   = placedb.unit_vertical_capacity

        with torch.no_grad():
            self.regions                      = torch.from_numpy(placedb.regions).to(device)
            self.flat_region_boxes            = torch.from_numpy(placedb.flat_region_boxes).to(device) 
            self.flat_region_boxes_start      = torch.from_numpy(placedb.flat_region_boxes_start).to(device) 
            self.node2fence_region_map        = torch.from_numpy(placedb.node2fence_region_map).to(device) 

            self.node_areas                   = torch.from_numpy(placedb.node_areas).to(device)
            self.node_pos                     = torch.from_numpy(placedb.node_pos).to(device)
            self.node_size                    = torch.from_numpy(placedb.node_size).to(device)
            self.node_size_x                  = torch.from_numpy(placedb.node_size_x).to(device)
            self.node_size_y                  = torch.from_numpy(placedb.node_size_y).to(device)
            self.num_pins_in_nodes            = torch.from_numpy(placedb.num_pins_in_nodes).to(device)
            self.pin_weights                  = torch.from_numpy(placedb.pin_weights).to(device)
            if placedb.movable_macro_mask is not None:
                self.movable_macro_mask           = torch.from_numpy(placedb.movable_macro_mask).to(device)
            else:
                self.movable_macro_mask           = None
            self.flat_node2pin_map            = torch.from_numpy(placedb.flat_node2pin_map).to(device)
            self.flat_node2pin_start_map      = torch.from_numpy(placedb.flat_node2pin_start_map).to(device)
            self.sorted_node_map              = torch.from_numpy(placedb.sorted_node_map).to(device)

            self.pin_mask_ignore_fixed_macros = torch.from_numpy(placedb.pin_mask_ignore_fixed_macros).to(device)
            self.pin_offset_x                 = torch.from_numpy(placedb.pin_offset_x).to(device)
            self.pin_offset_y                 = torch.from_numpy(placedb.pin_offset_y).to(device)
            self.pin2node_map                 = torch.from_numpy(placedb.pin2node_map).to(device)
            self.pin2net_map                  = torch.from_numpy(placedb.pin2net_map).to(device)

            self.net_mask_all                  = torch.from_numpy(placedb.net_mask_all).to(device)
            self.valid_num_nets                = torch.from_numpy(placedb.valid_num_nets).to(device)
            self.net_mask_ignore_large_degrees = torch.from_numpy(placedb.net_mask_ignore_large_degrees).to(device)
            self.net_weights                   = torch.from_numpy(placedb.net_weights).to(device)
            self.flat_net2pin_map              = torch.from_numpy(placedb.flat_net2pin_map).to(device)
            self.flat_net2pin_start_map        = torch.from_numpy(placedb.flat_net2pin_start_map).to(device)

            #可布线性相关
            if params.routability_opt_flag:
                self.original_node_size_x     = self.node_size_x.clone()
                self.original_node_size_y     = self.node_size_y.clone()
                self.original_pin_offset_x    = self.pin_offset_x.clone()
                self.original_pin_offset_y    = self.pin_offset_y.clone()
                self.unit_pin_capacity        = torch.from_numpy(placedb.unit_pin_capacity).to(device)
                if placedb.initial_horizontal_utilization_map is not None:
                    self.initial_horizontal_utilization_map = torch.from_numpy(placedb.initial_horizontal_utilization_map).to(device)
                else:
                    self.initial_horizontal_utilization_map = None
                if placedb.initial_vertical_utilization_map is not None:
                    self.initial_vertical_utilization_map   = torch.from_numpy(placedb.initial_vertical_utilization_map).to(device)
                else:
                    self.initial_vertical_utilization_map = None

class BasicPlace(nn.Module):
    """
    @brief Base placement class.
    All placement engines should be derived from this class.
    """
    def __init__(self, params:Params, placedb:PlaceDB):
        """
        @brief initialization.
        @param params parameters
        @param placedb placement database
        """
        super(BasicPlace, self).__init__()
        tt = time.time()
        self.device  = placedb.device
        self.dtype   = placedb.dtype
        self.params  = params
        self.pos = nn.ParameterList([nn.Parameter(torch.from_numpy(placedb.node_pos).to(self.device))])
        self.torch_dtype = self.pos[0].dtype
        self.data_collections = PlaceDataCollection(self.pos, params, placedb, self.device)
        logging.debug("build data takes %.2f seconds" % (time.time() - tt))

        # 构建op
        self.pin_pos                = self.build_pin_pos(self.data_collections)

        self.electric_potential     = self.build_electric_potential(self.data_collections)
        self.hpwl                   = self.build_hpwl(self.data_collections)
        self.electric_overflow      = self.build_electric_overflow(self.data_collections)

        self.move_boundary          = self.build_move_boundary(self.data_collections)

        self.pws                    = self.build_pws(self.data_collections)

        self.legality_check         = self.build_legality_check(self.data_collections)
        self.legalization           = self.build_legalization(self.data_collections)
        self.draw_placement         = self.build_draw_placement(self.data_collections)
        
        if params.routability_opt_flag:
            # compute congestion map, RISA/RUDY congestion map
            self.route_utilization_map = self.build_route_utilization_map(self.data_collections)
            self.pin_utilization_map = self.build_pin_utilization_map(self.data_collections)
            # adjust instance area with congestion map
            self.adjust_node_area = self.build_adjust_node_area(self.data_collections)

    def build_pin_pos(self, data_collections:PlaceDataCollection):
        """
        @brief sum up the pins for each cell
        @param data_collections a collection of all data and variables required for constructing the ops
        """
        
        return PinPos(
            pin_offset_x            = data_collections.pin_offset_x,
            pin_offset_y            = data_collections.pin_offset_y,
            pin2node_map            = data_collections.pin2node_map,
            flat_node2pin_map       = data_collections.flat_node2pin_map,
            flat_node2pin_start_map = data_collections.flat_node2pin_start_map,
            num_physical_nodes      = data_collections.num_physical_nodes,
            algorithm               = "node-by-node")

    def build_lg_wirelength(self, data_collections:PlaceDataCollection, gamma):
        """
        @brief build the op to compute log-sum-exp wirelength
        @param data_collections a collection of data and variables required for constructing ops
        """

        wirelength_for_pin_op = LogSumExpWirelength(
            flat_netpin=data_collections.flat_net2pin_map,
            netpin_start=data_collections.flat_net2pin_start_map,
            pin2net_map=data_collections.pin2net_map,
            net_weights=data_collections.net_weights,
            net_mask=data_collections.net_mask_all,
            pin_mask=data_collections.pin_mask_ignore_fixed_macros,
            gamma =gamma,
            algorithm='merged')

        # wirelength for position
        def lg_wirelength(pos):
            return wirelength_for_pin_op(self.pin_pos(pos))

        return lg_wirelength
    
    def build_wa_wirelength(self, data_collections:PlaceDataCollection, gamma):
        """
        @brief build the op to compute weighted average wirelength
        @param data_collections a collection of data and variables required for constructing ops
        """

        # use WeightedAverageWirelength atomic
        wirelength_for_pin_op = WeightedAverageWirelength(
            flat_netpin  =data_collections.flat_net2pin_map,
            netpin_start =data_collections.flat_net2pin_start_map,
            pin2net_map  =data_collections.pin2net_map,
            net_weights  =data_collections.net_weights,
            net_mask     =data_collections.net_mask_all,
            pin_mask     =data_collections.pin_mask_ignore_fixed_macros,
            gamma        =gamma,
            algorithm='merged')

        # wirelength for position
        def wa_wirelength(pos):
            return wirelength_for_pin_op(self.pin_pos(pos))

        return wa_wirelength 
    
    def build_electric_potential(self, data_collections:PlaceDataCollection):
        """
        @brief e-place electrostatic potential
        @param data_collections a collection of data and variables required for constructing ops
        """
        bin_size_x             = (self.data_collections.xh - self.data_collections.xl)/self.params.num_bins_x
        bin_size_y             = (self.data_collections.yh - self.data_collections.yl)/self.params.num_bins_y
        bin_center_x           = torch.from_numpy(self.bin_centers(self.data_collections.xl,self.data_collections.xh,bin_size_x)).to(self.device)
        bin_center_y           = torch.from_numpy(self.bin_centers(self.data_collections.yl,self.data_collections.yh,bin_size_y)).to(self.device)

        return ElectricPotential(
            node_size_x=data_collections.node_size_x,
            node_size_y=data_collections.node_size_y,
            bin_center_x=bin_center_x,
            bin_center_y=bin_center_y,
            target_density=self.params.target_density,
            xl=data_collections.xl,
            yl=data_collections.yl,
            xh=data_collections.xh,
            yh=data_collections.yh,
            bin_size_x=bin_size_x,
            bin_size_y=bin_size_y,
            num_movable_nodes=data_collections.num_movable_nodes,
            num_terminals=data_collections.num_fixed_nodes,
            num_filler_nodes=data_collections.num_filler_nodes,
            padding=0,
            deterministic_flag=self.params.deterministic_flag,
            sorted_node_map=data_collections.sorted_node_map,
            movable_macro_mask=data_collections.movable_macro_mask,
            fast_mode=self.params.RePlAce_skip_energy_flag,
            region_id=None,
            fence_regions=None,
            node2fence_region_map=None,
            placedb=None,
            plot_map_flag=self.params.plot_map_flag,
            img_dir="./%s/%s/summary/" % (self.params.result_dir, self.params.design_name()),
            )

    def build_hpwl(self, data_collections:PlaceDataCollection):
        """
        @brief compute half-perimeter wirelength
        @param data_collections a collection of all data and variables required for constructing the ops
        """

        wirelength_for_pin = HPWL(
            flat_netpin=data_collections.flat_net2pin_map,
            netpin_start=data_collections.flat_net2pin_start_map,
            pin2net_map=data_collections.pin2net_map,
            net_weights=data_collections.net_weights,
            net_mask=data_collections.net_mask_all,
            algorithm='net-by-net')

        # wirelength for position
        def hpwl(pos):
            return wirelength_for_pin(self.pin_pos(pos))

        return hpwl
    
    def build_electric_overflow(self, data_collections:PlaceDataCollection):
        """
        @brief compute electric density overflow
        @param data_collections a collection of all data and variables required for constructing the ops
        """
        bin_size_x             = (self.data_collections.xh - self.data_collections.xl)/self.params.num_bins_x
        bin_size_y             = (self.data_collections.yh - self.data_collections.yl)/self.params.num_bins_y
        bin_center_x           = torch.from_numpy(self.bin_centers(self.data_collections.xl,self.data_collections.xh,bin_size_x)).to(self.device)
        bin_center_y           = torch.from_numpy(self.bin_centers(self.data_collections.yl,self.data_collections.yh,bin_size_y)).to(self.device)
        
        return ElectricOverflow(
            node_size_x=data_collections.node_size_x,
            node_size_y=data_collections.node_size_y,
            bin_center_x=bin_center_x,
            bin_center_y=bin_center_y,
            target_density=self.params.target_density,
            xl=data_collections.xl,
            yl=data_collections.yl,
            xh=data_collections.xh,
            yh=data_collections.yh,
            bin_size_x=bin_size_x,
            bin_size_y=bin_size_y,
            num_movable_nodes=data_collections.num_movable_nodes,
            num_terminals=data_collections.num_fixed_nodes,
            num_filler_nodes=0,
            padding=0,
            deterministic_flag=self.params.deterministic_flag,
            sorted_node_map=data_collections.sorted_node_map,
            movable_macro_mask=data_collections.movable_macro_mask)

    def build_move_boundary(self, data_collections:PlaceDataCollection):
        """
        @brief bound nodes into layout region
        @param params parameters
        @param placedb placement database
        @param data_collections a collection of all data and variables required for constructing the ops
        @param device cpu or cuda
        """
        return MoveBoundary(
            node_size_x=data_collections.node_size_x,
            node_size_y=data_collections.node_size_y,
            xl=data_collections.xl,
            yl=data_collections.yl,
            xh=data_collections.xh,
            yh=data_collections.yh,
            num_movable_nodes=data_collections.num_movable_nodes,
            num_filler_nodes=data_collections.num_filler_nodes,)

    def build_pws(self, data_collections:PlaceDataCollection):
        """
        @brief accumulate pin weights of a node
        @param data_collections a collection of all data and variables required for constructing the ops
        """
        # CPU version by default...
        pws = PinWeightSum(
            flat_nodepin=data_collections.flat_node2pin_map,
            nodepin_start=data_collections.flat_node2pin_start_map,
            pin2net_map=data_collections.pin2net_map,
            num_nodes=data_collections.num_nodes,
            algorithm='node-by-node')

        return pws

    def build_legality_check(self, data_collections:PlaceDataCollection):
        """
        @brief legality check
        @param data_collections a collection of all data and variables required for constructing the ops
        """
        return LegalityCheck(
            node_size_x=data_collections.node_size_x,
            node_size_y=data_collections.node_size_y,
            flat_region_boxes=data_collections.flat_region_boxes,
            flat_region_boxes_start=data_collections.flat_region_boxes_start,
            node2fence_region_map=data_collections.node2fence_region_map,
            xl=data_collections.xl,
            yl=data_collections.yl,
            xh=data_collections.xh,
            yh=data_collections.yh,
            site_width=data_collections.site_width,
            row_height=data_collections.row_height,
            scale_factor=data_collections.scale_factor,
            num_terminals=data_collections.num_fixed_nodes,
            num_movable_nodes=data_collections.num_movable_nodes,)

    def build_legalization(self, data_collections:PlaceDataCollection):
        """
        @brief legalization
        @param data_collections a collection of all data and variables required for constructing the ops
        """

        ml = MacroLegalize(
            node_size_x=data_collections.node_size_x,
            node_size_y=data_collections.node_size_y,
            node_weights=data_collections.num_pins_in_nodes.to(torch.float32),
            flat_region_boxes=data_collections.flat_region_boxes,
            flat_region_boxes_start=data_collections.flat_region_boxes_start,
            node2fence_region_map=data_collections.node2fence_region_map,
            xl=data_collections.xl,
            yl=data_collections.yl,
            xh=data_collections.xh,
            yh=data_collections.yh,
            # all nodes include
            site_width=data_collections.site_width,
            row_height=data_collections.row_height,
            num_bins_x=self.params.num_bins_x,
            num_bins_y=self.params.num_bins_y,
            num_movable_nodes=data_collections.num_movable_nodes,
            num_terminal_NIs=0,
            num_filler_nodes=data_collections.num_filler_nodes,)

        def legalization(pos):
            logging.info("Start legalization")
            pos1 = ml(pos, pos)
            legal = self.legality_check(pos1)
            if not legal:
                logging.error("legality check failed, " \
                    "return illegal results.")
            return pos1

        return legalization
    
    def build_draw_placement(self, data_collections:PlaceDataCollection):
        """
        @brief plot placement
        """
        bin_size_x             = (self.data_collections.xh - self.data_collections.xl)/self.params.num_bins_x
        bin_size_y             = (self.data_collections.yh - self.data_collections.yl)/self.params.num_bins_y
        return DrawPlace(
            node_size_x=data_collections.node_size_x.data.clone().cpu().numpy(),
            node_size_y=data_collections.node_size_y.data.clone().cpu().numpy(),
            pin_offset_x=data_collections.pin_offset_x.data.clone().cpu().numpy(),
            pin_offset_y=data_collections.pin_offset_y.data.clone().cpu().numpy(),
            pin2node_map=data_collections.pin2node_map.data.clone().cpu().numpy(),
            netpin_start=data_collections.flat_net2pin_start_map.clone().cpu().numpy(),
            flat_netpin=data_collections.flat_net2pin_map.clone().cpu().numpy(),
            xl=data_collections.xl,
            yl=data_collections.yl,
            xh=data_collections.xh,
            yh=data_collections.yh,
            site_width= data_collections.site_width,
            row_height= data_collections.row_height, 
            bin_size_x=bin_size_x,
            bin_size_y=bin_size_y,
            num_movable_nodes=data_collections.num_movable_nodes,
            num_filler_nodes=data_collections.num_filler_nodes,
            valid_num_nets=data_collections.valid_num_nets,)

    def build_route_utilization_map(self, data_collections:PlaceDataCollection):
        """
        @brief routing congestion map based on current cell locations
        @param data_collections a collection of all data and variables required for constructing the ops
        """
        congestion_op = Rudy(
            netpin_start=data_collections.flat_net2pin_start_map,
            flat_netpin=data_collections.flat_net2pin_map,
            net_weights=data_collections.net_weights,
            xl=data_collections.routing_grid_xl,
            yl=data_collections.routing_grid_yl,
            xh=data_collections.routing_grid_xh,
            yh=data_collections.routing_grid_yh,
            num_bins_x=data_collections.num_routing_grids_x,
            num_bins_y=data_collections.num_routing_grids_y,
            deterministic_flag=self.params.deterministic_flag)

        def route_utilization_map_op(pos):
            pin_pos = self.pin_pos(pos)
            return congestion_op(pin_pos)

        return route_utilization_map_op

        return route_utilization_map_op

    def build_pin_utilization_map(self, data_collections:PlaceDataCollection):
        """
        @brief pin density map based on current cell locations
        @param data_collections a collection of all data and variables required for constructing the ops
        """
        return PinUtilization(
            pin_weights=data_collections.pin_weights,
            flat_node2pin_start_map=data_collections.flat_node2pin_start_map,
            node_size_x=data_collections.node_size_x,
            node_size_y=data_collections.node_size_y,
            xl=data_collections.routing_grid_xl,
            yl=data_collections.routing_grid_yl,
            xh=data_collections.routing_grid_xh,
            yh=data_collections.routing_grid_yh,
            num_movable_nodes=data_collections.num_movable_nodes,
            num_filler_nodes=data_collections.num_filler_nodes,
            num_bins_x=data_collections.num_routing_grids_x,
            num_bins_y=data_collections.num_routing_grids_y,
            unit_pin_capacity=data_collections.unit_pin_capacity,
            pin_stretch_ratio=self.params.pin_stretch_ratio,
            deterministic_flag=self.params.deterministic_flag)

    def build_adjust_node_area(self, data_collections:PlaceDataCollection):
        """
        @brief adjust cell area according to routing congestion and pin utilization map
        """
        target_density = torch.tensor(self.params.target_density, dtype=self.torch_dtype, device=self.device)
        total_movable_area = data_collections.total_movable_node_area
        total_filler_area = data_collections.total_filler_node_area
        total_place_area = data_collections.total_space_area
        adjust_node_area_op = AdjustNodeArea(
            flat_node2pin_map=data_collections.flat_node2pin_map,
            flat_node2pin_start_map=data_collections.flat_node2pin_start_map,
            pin_weights=data_collections.pin_weights,
            xl=data_collections.routing_grid_xl,
            yl=data_collections.routing_grid_yl,
            xh=data_collections.routing_grid_xh,
            yh=data_collections.routing_grid_yh,
            num_movable_nodes=data_collections.num_movable_nodes,
            num_filler_nodes=data_collections.num_filler_nodes if data_collections.num_filler_nodes != 0 else -2*data_collections.num_physical_nodes,
            route_num_bins_x=data_collections.num_routing_grids_x,
            route_num_bins_y=data_collections.num_routing_grids_y,
            pin_num_bins_x=data_collections.num_routing_grids_x,
            pin_num_bins_y=data_collections.num_routing_grids_y,
            total_place_area=total_place_area,
            total_whitespace_area=total_place_area - total_movable_area,
            max_route_opt_adjust_rate=self.params.max_route_opt_adjust_rate,
            route_opt_adjust_exponent=self.params.route_opt_adjust_exponent,
            max_pin_opt_adjust_rate=self.params.max_pin_opt_adjust_rate,
            area_adjust_stop_ratio=self.params.area_adjust_stop_ratio,
            route_area_adjust_stop_ratio=self.params.route_area_adjust_stop_ratio,
            pin_area_adjust_stop_ratio=self.params.pin_area_adjust_stop_ratio,
            unit_pin_capacity=data_collections.unit_pin_capacity)

        def adjust_node_area(pos, route_utilization_map,
                                      pin_utilization_map):
            return adjust_node_area_op(
                pos, data_collections.node_size_x,
                data_collections.node_size_y, data_collections.pin_offset_x,
                data_collections.pin_offset_y, target_density,
                route_utilization_map, pin_utilization_map)

        return adjust_node_area
    
    def bin_centers(self, l, h, bin_size):
        """
        @brief compute bin centers
        @param l lower bound
        @param h upper bound
        @param bin_size bin size
        @return array of bin centers
        """
        num_bins = int(np.ceil((h-l)/bin_size))
        centers = np.zeros(num_bins, dtype=np.float32)
        for id_x in range(num_bins):
            bin_l = l+id_x*bin_size
            bin_h = min(bin_l+bin_size, h)
            centers[id_x] = (bin_l+bin_h)/2
        return centers
    
    def plot(self, gendb_id, stage_name, iteration, pos, metric_info):
        """
        @brief plot layout
        @param stage_name automation stage
        @param iteration optimization step
        @param pos locations of nodes
        @param metric_info, info about current solution
        """
        tt = time.time()
        path = "%s/%s" % (self.params.result_dir, self.params.design_name())
        figname = "./%s/plot/%s/iter_%s_%s.png" % (path, stage_name, '{:04}'.format(gendb_id), '{:04}'.format(iteration))
        os.system("mkdir -p %s" % (os.path.dirname(figname)))
        if isinstance(pos, np.ndarray):
            pos = torch.from_numpy(pos)
        self.draw_placement(pos, metric_info, figname)
        logging.info("plotting to %s takes %.3f seconds" %
                     (figname, time.time() - tt))
        
    def images2gif(self, img_dir, gif_dir):
        """
        @brief convert img to gif
        @param img_dir image dir
        @param gif_dir gif dir
        """               
        files_list = sorted(os.listdir(img_dir))

        # 将图片序列保存为GIF
        if len(files_list) > 1:
            with imageio.get_writer(gif_dir, mode='I', fps=50) as writer:
                for filename in files_list:
                    image_path = os.path.join(img_dir, filename)
                    image = imageio.imread(image_path)
                    writer.append_data(image)