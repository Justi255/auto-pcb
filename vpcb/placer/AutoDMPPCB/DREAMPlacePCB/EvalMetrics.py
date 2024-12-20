import time
import torch
import pdb
from PlaceDB    import PlaceDB

class EvalMetrics (object):
    """
    @brief evaluation metrics at one step
    """
    def __init__(self, iteration=None, detailed_step=None):
        """
        @brief initialization
        @param iteration optimization step
        """
        self.iteration = iteration
        self.detailed_step = detailed_step
        self.objective = None
        self.wirelength = None
        self.density = None
        self.density_weight = None
        self.hpwl = None
        self.rmst_wl = None
        self.overflow = None
        self.goverflow = None
        self.route_utilization = None
        self.pin_utilization = None
        self.max_density = None
        self.gmax_density = None
        self.gamma = None
        self.tns = None
        self.wns = None
        self.eval_time = None

    def __str__(self):
        """
        @brief convert to string
        """
        content = ""
        metric_num = 0
        if self.iteration is not None:
            content = "iteration %4d" % (self.iteration)
            metric_num  += 1
        if self.wirelength is not None:
            content += ", WL %.4E" % (self.wirelength)
            metric_num  += 1
            if not metric_num%2:
                content += "\n"
        if self.density is not None:
            if self.density.numel() == 1:
                content += ", Density %.4E" % (self.density)
            else:
                content += ", Density [%s]" % ", ".join(["%.4E" % i for i in self.density])
            metric_num  += 1
            if not metric_num%2:
                content += "\n"
        if self.density_weight is not None:
            if self.density_weight.numel() == 1:
                content += ", DensityWeight %.4E" % (self.density_weight)
            else:
                content += ", DensityWeight [%s]" % ", ".join(["%.4E" % i for i in self.density_weight])
            metric_num  += 1
            if not metric_num%2:
                content += "\n"
        if self.hpwl is not None:
            content += ", wHPWL %.4E" % (self.hpwl)
            metric_num  += 1
            if not metric_num%2:
                content += "\n"
        if self.overflow is not None:
            if self.overflow.numel() == 1:
                content += ", Overflow %.4E" % (self.overflow)
            else:
                content += ", Overflow [%s]" % ", ".join(["%.4E" % i for i in self.overflow])
            metric_num  += 1
            if not metric_num%2:
                content += "\n"
        if self.route_utilization is not None:
            content += ", RouteOverflow %.4E" % (self.route_utilization)
            metric_num  += 1
            if not metric_num%2:
                content += "\n"
        if self.pin_utilization is not None:
            content += ", PinOverflow %.4E" % (self.pin_utilization)
            metric_num  += 1
            if not metric_num%2:
                content += "\n"
        if self.gamma is not None:
            content += ", gamma %.4E" % (self.gamma)
            metric_num  += 1
            if not metric_num%2:
                content += "\n"
        if self.eval_time is not None:
            content += ", time %.4fms" % (self.eval_time*1000)
            metric_num  += 1
            if not metric_num%2:
                content += "\n"

        return content

    def __repr__(self):
        """
        @brief print
        """
        return self.__str__()

    def evaluate(self, placedb:PlaceDB, ops, var):
        """
        @brief evaluate metrics
        @param placedb placement database
        @param ops a list of ops
        @param var variables
        """
        tt = time.time()
        with torch.no_grad():
            if "objective" in ops:
                self.objective = ops["objective"](var).data
            if "wirelength" in ops:
                self.wirelength = ops["wirelength"](var).data
            if "density" in ops:
                self.density = ops["density"](var).data
            if "hpwl" in ops:
                self.hpwl = ops["hpwl"](var).data
            if "overflow" in ops:
                overflow, max_density = ops["overflow"](var)
                if overflow.numel() == 1:
                    self.overflow = overflow.data / placedb.total_movable_node_area
                    self.max_density = max_density.data
                else:
                    pass
            if "goverflow" in ops:
                overflow, max_density = ops["goverflow"](var)
                self.goverflow = overflow.data / placedb.total_movable_node_area
                self.gmax_density = max_density.data
            if "route_utilization" in ops:
                route_utilization_map = ops["route_utilization"](var)
                route_utilization_map_sum = route_utilization_map.sum()
                self.route_utilization = route_utilization_map.sub_(1).clamp_(min=0).sum() / route_utilization_map_sum
            if "pin_utilization" in ops:
                pin_utilization_map = ops["pin_utilization"](var)
                pin_utilization_map_sum = pin_utilization_map.sum()
                self.pin_utilization = pin_utilization_map.sub_(1).clamp_(min=0).sum() / pin_utilization_map_sum
        self.eval_time = time.time() - tt
