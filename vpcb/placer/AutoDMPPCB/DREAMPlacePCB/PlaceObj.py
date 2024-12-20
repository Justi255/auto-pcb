import os
import sys
import time
import numpy as np
import itertools
import logging
import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F
import pdb
import gzip
from BasicPlace import BasicPlace, PlaceDataCollection
from EvalMetrics import EvalMetrics
from Params  import Params
import matplotlib.pyplot as plt

num_obj = 0

class Precondition:
    """Preconditioning engine is critical for convergence.
    Need to be carefully designed.
    """
    def __init__(self, data_collections:PlaceDataCollection, pws):
        self.data_collections = data_collections
        self.pws = pws
        self.iteration = 0
        self.alpha = 1.0
        self.best_overflow = None
        self.overflows = []

    def set_overflow(self, overflow):
        self.overflows.append(overflow)
        if self.best_overflow is None:
            self.best_overflow = overflow
        elif self.best_overflow.mean() > overflow.mean():
            self.best_overflow = overflow

    def __call__(self, grad, density_weight, update_mask=None):
        """Introduce alpha parameter to avoid divergence.
        It is tricky for this parameter to increase.
        """
        with torch.no_grad():
            # The preconditioning step in python is time-consuming, as in each gradient
            # pass, the total net weight should be re-calculated.
            sum_pin_weights_in_nodes = self.pws(self.data_collections.net_weights)
            precond = (sum_pin_weights_in_nodes + self.alpha * density_weight * self.data_collections.node_areas)

            precond.clamp_(min=1.0)
            grad[0 : self.data_collections.num_nodes].div_(precond)
            grad[self.data_collections.num_nodes : self.data_collections.num_nodes * 2].div_(precond)
            # grad[torch.abs(grad) < 1e-2] = 0
            # grad[torch.abs(grad) > 1e2]  = 1e2

            ### stop gradients for terminated electric field
            if update_mask is not None:
                pass
            self.iteration += 1

        return grad


class PlaceObj(BasicPlace):
    """
    @brief Define placement objective:
        wirelength + density_weight * density penalty
    It includes various ops related to global placement as well.
    """
    def __init__(self, params, placedb, density_weight, global_place_params):
        """
        @brief initialize ops for placement
        @param params parameters
        @param placedb placement database
        @param density_weight density weight in the objective
        @param global_place_params global placement parameters for current global placement stage
        """
        super(PlaceObj, self).__init__(params, placedb)
        self.global_place_params = global_place_params

        ### quadratic penalty
        self.density_quad_coeff = 2000
        self.quad_penalty_coeff = None
        self.init_density = None
        ### increase density penalty if slow convergence
        self.density_factor = 1

        if(len(self.data_collections.regions) > 0):
            ### fence region will enable quadratic penalty by default
            self.quad_penalty = True
            
        else:
            ### non fence region will use first-order density penalty by default
            self.quad_penalty = False
        
        ### fence region
        ### update mask controls whether stop gradient/updating, 1 represents allow grad/update
        self.update_mask = None
        if len(self.data_collections.regions) > 0:
            ### for subregion rough legalization, once stop updating, perform immediate greddy legalization once
            ### this is to avoid repeated legalization
            ### 1 represents already legal
            self.legal_mask = torch.zeros(len(self.data_collections.regions) + 1)

        if len(self.data_collections.regions) > 0:
            pass
        else:
            self.density_weight = torch.tensor(
                [density_weight],
                dtype=self.torch_dtype,
                device=self.device)
        ### Note: even for multi-electric fields, they use the same gamma
        num_bins_x = global_place_params["num_bins_x"] if "num_bins_x" in global_place_params and global_place_params["num_bins_x"] > 1 else self.params.num_bins_x
        num_bins_y = global_place_params["num_bins_y"] if "num_bins_y" in global_place_params and global_place_params["num_bins_y"] > 1 else self.params.num_bins_y
        name = "Global placement: %dx%d bins by default" % (num_bins_x, num_bins_y)
        logging.info(name)
        self.num_bins_x = num_bins_x
        self.num_bins_y = num_bins_y
        self.bin_size_x = (self.data_collections.xh - self.data_collections.xl) / num_bins_x
        self.bin_size_y = (self.data_collections.yh - self.data_collections.yl) / num_bins_y
        self.gamma = torch.tensor(10 * self.base_gamma,
                                  dtype=self.torch_dtype,
                                  device=self.device)
        if global_place_params["wirelength"] == "weighted_average":
            self.wirelength = self.build_wa_wirelength(self.data_collections, self.gamma)
        elif global_place_params["wirelength"] == "logsumexp":
            self.wirelength = self.build_lg_wirelength(self.data_collections, self.gamma)
        else:
            assert 0, "unknown wirelength model %s" % (
                global_place_params["wirelength"])
        self.precondition = Precondition(self.data_collections, self.pws)


        self.Lgamma_iteration = global_place_params["iteration"]
        if 'Llambda_density_weight_iteration' in global_place_params:
            self.Llambda_density_weight_iteration = global_place_params[
                'Llambda_density_weight_iteration']
        else:
            self.Llambda_density_weight_iteration = 1
        if 'Lsub_iteration' in global_place_params:
            self.Lsub_iteration = global_place_params['Lsub_iteration']
        else:
            self.Lsub_iteration = 1
        if 'routability_Lsub_iteration' in global_place_params:
            self.routability_Lsub_iteration = global_place_params[
                'routability_Lsub_iteration']
        else:
            self.routability_Lsub_iteration = self.Lsub_iteration
        self.start_fence_region_density = False


    def obj_fn(self, pos):
        """
        @brief Compute objective.
            wirelength + density_weight * density penalty
        @param pos locations of cells
        @return objective value
        """
        wirelength = self.wirelength(pos)
        if self.params.use_rudy_map:
            rudy_map   = self.route_utilization_map(pos)
            # rudy_map   -= self.params.rudy_net_threhold
            # rudy_map.clamp_(min=0)
            global num_obj
            if self.params.plot_flag:
                path = "./%s/%s" % (self.params.result_dir, self.params.design_name())
                figname = "%s/plot/route%d.png" % (path, num_obj)
                num_obj += 1
                os.system("mkdir -p %s" % (os.path.dirname(figname)))
                plt.imsave(
                    figname, rudy_map.data.cpu().numpy().T, origin="upper"
                )
            density    = self.electric_potential(pos, rudy_map)
            logging.info(" use rudy map")            
        else:
            density    = self.electric_potential(pos)
            

        if self.init_density is None:
            ### record initial density
            self.init_density = density.data.clone()
            ### density weight subgradient preconditioner
            density_weight_grad_precond = self.init_density.masked_scatter(self.init_density > 0, 1 /self.init_density[self.init_density > 0])
            self.quad_penalty_coeff = self.density_quad_coeff / 2 * density_weight_grad_precond
        if self.quad_penalty:
            ### quadratic density penalty
            density = density * (1 + self.quad_penalty_coeff * density)
        if len(self.data_collections.regions) > 0:
            pass
        else:
            result = torch.add(wirelength, density, alpha=(self.density_factor * self.density_weight).item())

        return result

    def obj_and_grad_fn(self, pos):
        """
        @brief compute objective and gradient.
            wirelength + density_weight * density penalty
        @param pos locations of cells
        @return objective value
        """
        # self.check_gradient(pos)
        if pos.grad is not None:
            pos.grad.zero_()
        obj = self.obj_fn(pos)
        obj.backward()

        self.precondition(pos.grad, self.density_weight, self.update_mask)

        return obj, pos.grad

    def forward(self):
        """
        @brief Compute objective with current locations of cells.
        """
        return self.obj_fn(self.data_collections.pos[0])

    def check_gradient(self, pos):
        """
        @brief check gradient for debug
        @param pos locations of cells
        """
        wirelength = self.wirelength(pos)

        if pos.grad is not None:
            pos.grad.zero_()
        wirelength.backward()
        wirelength_grad = pos.grad.clone()

        pos.grad.zero_()
        if self.params.use_rudy_map:
            rudy_map   = self.route_utilization_map(pos)
            # rudy_map   -= self.params.rudy_net_threhold
            # rudy_map.clamp_(min=0)
            global num_obj
            if self.params.plot_flag:
                path = "./%s/%s" % (self.params.result_dir, self.params.design_name())
                figname = "%s/plot/route%d.png" % (path, num_obj)
                num_obj += 1
                os.system("mkdir -p %s" % (os.path.dirname(figname)))
                plt.imsave(
                    figname, rudy_map.data.cpu().numpy().T, origin="upper"
                )
            density    = self.density_weight * self.electric_potential(pos, rudy_map)
            logging.info(" use rudy map")
        else:
            density    = self.density_weight * self.electric_potential(pos)
            
        density.backward()
        density_grad = pos.grad.clone()

        wirelength_grad_norm = wirelength_grad.norm(p=1)
        density_grad_norm = density_grad.norm(p=1)

        if torch.isinf(wirelength_grad_norm) or torch.isnan(wirelength_grad_norm):
            logging.info("wirelength_grad norm = %.6E" % (wirelength_grad_norm))
            print("wirelength_grad:" ,wirelength_grad.cpu())
        if torch.isinf(density_grad_norm) or torch.isnan(density_grad_norm):  
            logging.info("density_grad norm    = %.6E" % (density_grad_norm))
            print("density_grad: " ,density_grad.cpu())
            
        pos.grad.zero_()

    def estimate_initial_learning_rate(self, x_k, lr):
        """
        @brief Estimate initial learning rate by moving a small step.
        Computed as | x_k - x_k_1 |_2 / | g_k - g_k_1 |_2.
        @param x_k current solution
        @param lr small step
        """
        obj_k, g_k = self.obj_and_grad_fn(x_k)
        x_k_1 = torch.autograd.Variable(x_k - lr * g_k, requires_grad=True)
        obj_k_1, g_k_1 = self.obj_and_grad_fn(x_k_1)

        return (x_k - x_k_1).norm(p=2) / (g_k - g_k_1).norm(p=2)

    def initialize_density_weight(self, params, placedb):
        """
        @brief compute initial density weight
        @param params parameters
        @param placedb placement database
        """
        wirelength = self.wirelength(self.data_collections.pos[0])
        if self.data_collections.pos[0].grad is not None:
            self.data_collections.pos[0].grad.zero_()
        wirelength.backward()
        wirelength_grad_norm = self.data_collections.pos[0].grad.norm(p=1)

        self.data_collections.pos[0].grad.zero_()
        if self.params.use_rudy_map:
            rudy_map   = self.route_utilization_map(self.data_collections.pos[0])
            # rudy_map   -= self.params.rudy_net_threhold
            # rudy_map.clamp_(min=0)
            global num_obj
            if self.params.plot_flag:
                path = "./%s/%s" % (self.params.result_dir, self.params.design_name())
                figname = "%s/plot/route%d.png" % (path, num_obj)
                num_obj += 1
                os.system("mkdir -p %s" % (os.path.dirname(figname)))
                plt.imsave(
                    figname, rudy_map.data.cpu().numpy().T, origin="upper"
                )
            density    = self.electric_potential(self.data_collections.pos[0], rudy_map)
            logging.info(" use rudy map")                       
        else:
            density    = self.electric_potential(self.data_collections.pos[0])
            
        ### record initial density
        self.init_density = density.data.clone()
        density.backward()
        density_grad_norm = self.data_collections.pos[0].grad.norm(p=1)

        grad_norm_ratio = wirelength_grad_norm / density_grad_norm
        self.density_weight = torch.tensor(
            [self.params.density_weight * grad_norm_ratio],
            dtype=self.torch_dtype,
            device=self.device)

        return self.density_weight

    def update_density_weight(self, cur_metric:EvalMetrics, prev_metric:EvalMetrics, iteration):
        """
        @brief update density weight
        """
        if not self.params.update_density_weight:
            return self.density_weight
        
        ### params for hpwl mode from RePlAce
        ref_hpwl   = self.params.RePlAce_ref_hpwl
        LOWER_PCOF = self.params.RePlAce_LOWER_PCOF
        UPPER_PCOF = self.params.RePlAce_UPPER_PCOF

        ### based on hpwl
        with torch.no_grad():
            delta_hpwl = cur_metric.hpwl - prev_metric.hpwl
            if delta_hpwl < 0:
                # delta_hpwl < 0, result will be better, more than 200 iter mu will be same
                # mu will >= 1.03 and <= 1.05, when iter increase, mu will decrease
                mu = UPPER_PCOF * np.maximum(
                    np.power(0.9999, float(iteration)), 0.98)
            else:
                # delta_hpwl >= 0, result will be worse, 1.4*ref_hpwl or more worse mu will be same
                # ref_hpwl tell us how much we can suffer hpwl worse, when delta_hpwl >= ref_hpwl, mu will <= 1.0
                # mu will >= 0.9975 and <= 1.05, when delta_hpwl increase, mu will decrease
                mu = UPPER_PCOF * torch.pow(
                    UPPER_PCOF, -delta_hpwl / ref_hpwl).clamp(
                        min=LOWER_PCOF, max=UPPER_PCOF)
            self.density_weight *= mu
    
    @property
    def base_gamma(self):
        """
        @brief compute base gamma
        """
        return self.params.gamma * (self.bin_size_x + self.bin_size_y)

    def update_gamma(self, iteration, overflow):
        """
        @brief update gamma in wirelength model
        @param iteration optimization step
        @param overflow evaluated in current step
        """
        ### overflow can have multiple values for fence regions, use their weighted average based on movable node number
        if overflow.numel() == 1:
            overflow_avg = overflow
        else:
            overflow_avg = overflow
        coef = torch.pow(10, (overflow_avg - 0.1) * 20 / 9 - 1)
        self.gamma = torch.tensor((self.base_gamma * coef).item() , dtype = torch.float32, device = self.device)
        if self.global_place_params["wirelength"] == "weighted_average":
            self.wirelength = self.build_wa_wirelength(self.data_collections, self.gamma)
        elif self.global_place_params["wirelength"] == "logsumexp":
            self.wirelength = self.build_lg_wirelength(self.data_collections, self.gamma)
