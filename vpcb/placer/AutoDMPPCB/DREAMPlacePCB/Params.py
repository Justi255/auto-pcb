import logging
import os
import sys
import json 
import math 
from collections import OrderedDict
import pdb

class Params:
    """
    @brief Parameter class
    """
    def __init__(self, iopath:dict):
        """
        @brief initialization
        """
        self.pcb_input  = iopath["pcb_input"]["value"] # the pcb design file input
        self.result_dir = iopath["result_dir"]["value"] # result directory for output
        self.gpu = None # enable gpu or not
        self.use_rl = None # whether use RL to optimize placement
        self.num_bins_x = None # number of bins in horizontal direction; computed by internal heuristic if not specified
        self.num_bins_y = None # number of bins in vertical direction; computed by internal heuristic if not specified
        self.global_place_stages = None # global placement configurations of each stage, a dictionary of {\"num_bins_x\", \"num_bins_y\", \"iteration\", \"learning_rate\", \"learning_rate_decay\", \"wirelength\", \"optimizer\", \"Llambda_density_weight_iteration\", \"Lsub_iteration\"}
        self.use_bb = None # whether use bb step
        self.target_density = None # target density
        self.density_weight = None # initial weight of density cost
        self.update_density_weight = None # whether update_density_weight
        self.use_rudy_map = None # whether use_rudy_map to compute eletric force
        self.rudy_net_threhold = None # if net congestion greater than rudy_net_threhold density will consider net congestion
        self.random_seed = None # random seed
        self.scale_factor = None # scale factor to avoid numerical overflow; 0.0 means not set
        self.shift_factor = None # shift factor to avoid numerical issues when the lower-left origin of rows is not (0, 0)
        self.ignore_net_degree = None # ignore net degree larger than some value
        self.enable_fillers = None # enable filler cells
        self.global_place_flag = None # whether use global placement
        self.legalize_flag = None # whether use internal legalization
        self.detailed_place_flag = None # whether use internal detailed placement
        self.stop_overflow = None # stopping criteria, consider stop when the overflow reaches to a ratio
        self.dtype = None # data type, float32 | float64
        self.plot_flag = None # whether plot solution or not
        self.gif_flag  = None # whether generate a gif or not
        self.metric_plot_flag  = None # whether plot metric
        self.plot_map_flag = None # whether plot map in electric force map 
        self.RePlAce_ref_hpwl = None # reference HPWL used in RePlAce for updating density weight
        self.RePlAce_LOWER_PCOF = None # lower bound ratio used in RePlAce for updating density weight
        self.RePlAce_UPPER_PCOF = None # upper bound ratio used in RePlAce for updating density weight
        self.gamma = None # base coefficient for log-sum-exp and weighted-average wirelength, a relative value to bin size
        self.RePlAce_skip_energy_flag = None # whether skip density energy computation for fast mode, may not work with some solvers
        self.random_center_init_flag = None # whether perform random initialization around the center for global placement
        self.sort_nets_by_degree = None # whether sort nets by degree or not
        self.num_threads = None # number of CPU threads
        self.routability_opt_flag = None # whether enable routability optimization
        self.route_num_bins_x = None # number of routing grids/tiles
        self.route_num_bins_y = None # number of routing grids/tiles
        self.node_area_adjust_overflow = None # the overflow where to adjust node area
        self.max_num_area_adjust = None # maximum times to adjust node area
        self.adjust_rudy_area_flag = None # whether use RUDY/RISA map to guide area adjustment
        self.adjust_pin_area_flag = None # whether use pin utilization map to guide area adjustment
        self.area_adjust_stop_ratio = None # area_adjust_stop_ratio
        self.route_area_adjust_stop_ratio = None # route_area_adjust_stop_ratio
        self.pin_area_adjust_stop_ratio = None # pin_area_adjust_stop_ratio
        self.unit_horizontal_capacity = None # number of horizontal routing tracks per unit distance
        self.unit_vertical_capacity = None # number of vertical routing tracks per unit distance
        self.unit_pin_capacity = None # number of pins per unit area
        self.max_route_opt_adjust_rate = None # max_route_opt_adjust_rate
        self.route_opt_adjust_exponent = None # exponent to adjust the routing utilization map
        self.pin_stretch_ratio = None # pin_stretch_ratio
        self.max_pin_opt_adjust_rate = None # max_pin_opt_adjust_rate
        self.deterministic_flag = None # whether require run-to-run determinism, may have efficiency overhead
        self.row_height = None # a row's height
        self.site_width = None # a site's width
        self.test_hpwl_flag = None # test hpwl if compute correct
        self.write_back_flag = None # whether write back to pcb


    def printWelcome(self):
        """
        @brief print welcome message
        """
        content = """\
========================================================
                       DREAMPlacePCB
========================================================"""
        logging.info(content)

    def printHelp(self):
        """
        @brief print help message for JSON parameters
        """
        content = self.toMarkdownTable()
        print(content)

    def toMarkdownTable(self):
        """
        @brief convert to markdown table 
        """
        key_length = len('JSON Parameter')
        key_length_map = []
        value_length = len('value')
        value_length_map = []
        description_length = len('Description')
        description_length_map = []

        def getvalueColumn(key, value):
            if sys.version_info.major < 3: # python 2
                flag = isinstance(value['value'], unicode)
            else: #python 3
                flag = isinstance(value['value'], str)
            if flag and not value['value'] and 'required' in value: 
                return value['required']
            else:
                return value['value']

        for key, value in self.params_dict.items():
            key_length_map.append(len(key))
            value_length_map.append(len(str(getvalueColumn(key, value))))
            description_length_map.append(len(value['description']))
            key_length = max(key_length, key_length_map[-1])
            value_length = max(value_length, value_length_map[-1])
            description_length = max(description_length, description_length_map[-1])

        content = "| %s %s| %s %s| %s %s|\n" % (
                'JSON Parameter', 
                " " * (key_length - len('JSON Parameter') + 1), 
                'value', 
                " " * (value_length - len('value') + 1), 
                'Description', 
                " " * (description_length - len('Description') + 1)
                )
        content += "| %s | %s | %s |\n" % (
                "-" * (key_length + 1), 
                "-" * (value_length + 1), 
                "-" * (description_length + 1)
                )
        count = 0
        for key, value in self.params_dict.items():
            content += "| %s %s| %s %s| %s %s|\n" % (
                    key, 
                    " " * (key_length - key_length_map[count] + 1), 
                    str(getvalueColumn(key, value)), 
                    " " * (value_length - value_length_map[count] + 1), 
                    value['description'], 
                    " " * (description_length - description_length_map[count] + 1)
                    )
            count += 1
        return content 

    def toJson(self):
        """
        @brief convert to json
        """
        data = {}
        for key, value in self.__dict__.items():
            if key != 'params_dict': 
                data[key] = value
        return data

    def fromDict(self, params_dict):
        """
        @brief load form dict
        """
        for key, value in params_dict.items():
            self.__dict__[key] = value
                
    def fromJson(self, params_dict):
        """
        @brief load form json
        """
        for key, dict in params_dict.items():
            if 'value' in dict: 
                self.__dict__[key] = dict['value']
            else:
                self.__dict__[key] = None

    def dump(self, filename):
        """
        @brief dump to json file
        """
        with open(filename, 'w') as f:
            json.dump(self.toJson(), f)

    def load(self, filename):
        """
        @brief load from json file
        """
        filename = os.path.join(os.path.dirname(__file__), filename)
        with open(filename, 'r') as f:
            self.fromJson(json.load(f))

    def __str__(self):
        """
        @brief string
        """
        return str(self.toJson())

    def __repr__(self):
        """
        @brief print
        """
        return self.__str__()
    
    def design_name(self):
        """
        @brief speculate the design name for dumping out intermediate solutions, 
        for example input benchmarks/bm3.unrouted.kicad_pcb
        output bm3 
        """
        if self.pcb_input: 
            design_name = os.path.basename(self.pcb_input).replace(".unrouted.kicad_pcb", "")
        return design_name 
    
    def update(self, params):
        """
        @brief update parameters
        """
        if isinstance(params, dict):
            self.fromDict(params)
        else:
            assert 0
    
    
