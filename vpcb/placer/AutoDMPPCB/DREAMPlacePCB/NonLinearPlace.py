import os
import sys
import time
import pickle
import numpy as np
import logging
import torch
import gzip
import copy
import matplotlib.pyplot as plt
import inspect

if sys.version_info[0] < 3:
    import cPickle as pickle
else:
    import _pickle as pickle
from typing                                 import List
from Params                                 import Params
from PlaceDB                                import PlaceDB
from BasicPlace                             import BasicPlace
from PlaceObj                               import PlaceObj
from NesterovAcceleratedGradientOptimizer   import NesterovAcceleratedGradientOptimizer
from EvalMetrics                            import EvalMetrics
from torch.optim.lr_scheduler               import ExponentialLR
import pdb


class NonLinearPlace(object):
    """
    @brief Nonlinear placement engine.
    It takes parameters and placement database and runs placement flow.
    """

    def __init__(self, gendb_id):
        """
        @brief initialization.
        """
        self.gendb_id = gendb_id

    def __call__(self, params:Params, placedb:PlaceDB):
        """
        @brief Top API to solve placement.
        @param params parameters
        @param placedb placement database
        """
        iteration = 0
        all_metrics = []
        lrs = []
        scheduler = None

        # global placement
        if params.global_place_flag:
            # global placement may run in multiple stages according to user specification
            for global_place_params in params.global_place_stages:

                # we formulate each stage as a 3-nested optimization problem
                # f_gamma(g_density(h(x) ; density weight) ; gamma)
                # Lgamma      Llambda        Lsub
                # When optimizing an inner problem, the outer parameters are fixed.
                # This is a generalization to the eplace/RePlAce approach

                # As global placement may easily diverge, we record the position of best overflow and its metric
                best_metric:List[EvalMetrics] = [None]
                best_pos = [None]

                if params.gpu:
                    torch.cuda.synchronize()
                tt = time.time()
                # construct model and optimizer
                density_weight = 0.0
                # construct placement model
                model = PlaceObj(
                    params,
                    placedb,
                    density_weight,
                    global_place_params,
                ).to(placedb.device)
                optimizer_name = global_place_params["optimizer"]

                # determine optimizer
                if optimizer_name.lower() == "adam":
                    optimizer = torch.optim.Adam(model.parameters(), lr=0)
                elif optimizer_name.lower() == "sgd":
                    optimizer = torch.optim.SGD(model.parameters(), lr=0)
                elif optimizer_name.lower() == "sgd_momentum":
                    optimizer = torch.optim.SGD(model.parameters(), lr=0, momentum=0.9, nesterov=False)
                elif optimizer_name.lower() == "sgd_nesterov":
                    optimizer = torch.optim.SGD(model.parameters(), lr=0, momentum=0.9, nesterov=True)
                elif optimizer_name.lower() == "nesterov":
                    optimizer = NesterovAcceleratedGradientOptimizer(
                        model.parameters(),
                        lr=0,
                        obj_and_grad_fn=model.obj_and_grad_fn,
                        constraint_fn=model.move_boundary,
                        use_bb = params.use_bb
                    )
                else:
                    assert 0, "unknown optimizer %s" % (optimizer_name)

                logging.info("use %s optimizer" % (optimizer_name))
                model.train()
                # defining evaluation ops
                eval_ops = {
                    "hpwl": model.hpwl,
                    "overflow": model.electric_overflow,
                }
                if params.routability_opt_flag:
                    eval_ops.update(
                        {
                            "route_utilization": model.route_utilization_map,
                            "pin_utilization": model.pin_utilization_map,
                        }
                    )

                # a function to initialize learning rate
                def initialize_learning_rate(pos):
                    learning_rate = model.estimate_initial_learning_rate(
                        pos, global_place_params["learning_rate"]
                    )
                    # update learning rate
                    for param_group in optimizer.param_groups:
                        param_group["lr"] = learning_rate.data
                    lrs.append(optimizer.param_groups[0]["lr"].data.clone().cpu().numpy())

                if iteration == 0:
                    initialize_learning_rate(model.data_collections.pos[0])
                    if (
                        optimizer_name.lower() in ["sgd", "adam", "sgd_momentum", "sgd_nesterov"]
                        and "learning_rate_decay" in global_place_params
                    ):
                        scheduler = ExponentialLR(
                            optimizer,
                            gamma=global_place_params["learning_rate_decay"],
                        )
                # the state must be saved after setting learning rate
                initial_state = copy.deepcopy(optimizer.state_dict())

                if params.gpu:
                    torch.cuda.synchronize()
                logging.info("%s initialization takes %g seconds" % (optimizer_name, (time.time() - tt)))

                # stopping criteria
                def Lgamma_stop_criterion(Lgamma_step, metrics:List[List[List[EvalMetrics]]], stop_mask=None):
                    """
                    @brief if overflow is adequacy small ,stop
                    """
                    with torch.no_grad():
                        if len(metrics) > 1:
                            cur_metric = metrics[-1][-1][-1]
                            prev_metric = metrics[-2][-1][-1]

                            if Lgamma_step > 100 and (
                                (
                                    cur_metric.overflow[-1] < params.stop_overflow
                                    and cur_metric.hpwl > prev_metric.hpwl
                                )
                                or cur_metric.max_density[-1] < params.target_density
                            ):
                                logging.debug(
                                    "Lgamma stopping criteria: %d > 100 and (( %g < 0.1 and %g > %g ) or %g < 1.0)"
                                    % (
                                        Lgamma_step,
                                        cur_metric.overflow[-1],
                                        cur_metric.hpwl,
                                        prev_metric.hpwl,
                                        cur_metric.max_density[-1],
                                    )
                                )
                                return True
                        # a heuristic to detect divergence and stop early
                        if len(metrics) > 50:
                            cur_metric = metrics[-1][-1][-1]
                            prev_metric = metrics[-50][-1][-1]
                            if best_metric[0] is None:
                                return False
                            # record HPWL and overflow increase, and check divergence
                            elif (
                                cur_metric.overflow[-1] > prev_metric.overflow[-1]
                                and cur_metric.hpwl > best_metric[0].hpwl * 2
                            ):
                                return True
                        return False

                def Llambda_stop_criterion(Lgamma_step, Llambda_density_weight_step, metrics:List[List[EvalMetrics]]):
                    """
                    @brief if overflow decrease suffer from hpwl increase it will stop
                    """
                    with torch.no_grad():
                        if len(metrics) > 1:
                            cur_metric = metrics[-1][-1]
                            prev_metric = metrics[-2][-1]
                            if (
                                cur_metric.overflow[-1] < params.stop_overflow
                                and cur_metric.hpwl > prev_metric.hpwl
                            ) or cur_metric.max_density[-1] < 1.0:
                                logging.debug(
                                    "Llambda stopping criteria: %d and (( %g < 0.1 and %g > %g ) or %g < 1.0)"
                                    % (
                                        Llambda_density_weight_step,
                                        cur_metric.overflow[-1],
                                        cur_metric.hpwl,
                                        prev_metric.hpwl,
                                        cur_metric.max_density[-1],
                                    )
                                )
                                return True
                    return False

                # use a moving average window for stopping criteria, for an example window of 3
                # 0, 1, 2, 3, 4, 5, 6
                #    window2
                #             window1
                moving_avg_window = max(min(model.Lsub_iteration // 2, 3), 1)

                def Lsub_stop_criterion(Lgamma_step, Llambda_density_weight_step, Lsub_step, metrics:List[EvalMetrics]):
                    """
                    @brief if obj not decrease too much, it will stop
                    moving_avg_window=1
                    compare prev obj avg in window with cur obj avg in window
                    """
                    with torch.no_grad():
                        if len(metrics) >= moving_avg_window * 2:
                            cur_avg_obj = 0
                            prev_avg_obj = 0
                            for i in range(moving_avg_window):
                                cur_avg_obj += metrics[-1 - i].objective
                                prev_avg_obj += metrics[-1 - moving_avg_window - i].objective
                            cur_avg_obj /= moving_avg_window
                            prev_avg_obj /= moving_avg_window
                            threshold = 0.999
                            if cur_avg_obj >= prev_avg_obj * threshold:
                                logging.debug(
                                    "Lsub stopping criteria: %d and %g > %g * %g"
                                    % (Lsub_step, cur_avg_obj, prev_avg_obj, threshold)
                                )
                                return True
                    return False

                def one_descent_step(
                    Lgamma_step, Llambda_density_weight_step, Lsub_step, iteration, metrics:List, stop_mask=None
                ):
                    """
                    @brief optimize one step
                    optimize the placement solution one step 
                    move boundary to ensure the solution is legal
                    record the metrics about current solution
                    record the best overflow solution and its metrics
                    """
                    t0  = time.time()
                    pos = model.pos[0]
                    
                    # plot init placement
                    if iteration == 0:
                        # metric for init iteration
                        init_metric = EvalMetrics(
                            iteration, (Lgamma_step, Llambda_density_weight_step, Lsub_step)
                        )
                        init_metric.gamma = model.gamma.data.clone()
                        init_metric.density_weight = model.density_weight.data.clone()
                        init_metric.evaluate(placedb, eval_ops, model.pos[0].data.clone())
                        init_metric.objective, _ = model.obj_and_grad_fn(pos)
                        metrics.append(init_metric)
                        logging.info(init_metric)
                        if params.plot_flag:
                            model.plot(self.gendb_id, "global_placement", init_metric.iteration, model.pos[0].data.clone().cpu().numpy(), str(init_metric))
                        
                    # handle multiple density weights for multi-electric field
                    if torch.eq(model.density_weight.mean(), 0.0):
                        model.initialize_density_weight(params, placedb)
                        logging.info("density_weight = %.6E" % (model.density_weight.data))

                    optimizer.zero_grad()
                    model.obj_and_grad_fn(pos)
                    t3 = time.time()
                    optimizer.step()
                    logging.info("optimizer step %.3f ms" % ((time.time() - t3) * 1000))
                    # move any out-of-bound cell back to placement region
                    model.move_boundary(pos)
                    
                    # metric for this iteration
                    cur_metric = EvalMetrics(
                        iteration + 1, (Lgamma_step, Llambda_density_weight_step, Lsub_step)
                    )
                    cur_metric.gamma = model.gamma.data.clone()
                    cur_metric.density_weight = model.density_weight.data.clone()
                    cur_metric.evaluate(placedb, eval_ops, model.pos[0].data.clone())
                    cur_metric.objective, _ = model.obj_and_grad_fn(pos)
                    metrics.append(cur_metric)
                    lrs.append(optimizer.param_groups[0]["lr"].data.clone().cpu().numpy())
                    logging.info(cur_metric)
                    if params.plot_flag:
                        model.plot(self.gendb_id, "global_placement", cur_metric.iteration, model.pos[0].data.clone().cpu().numpy(), str(cur_metric))
                    
                    # record the best outer cell overflow
                    if best_metric[0] is None or best_metric[0].overflow[-1] > cur_metric.overflow[-1]:
                        best_metric[0] = cur_metric
                        if best_pos[0] is None:
                            best_pos[0] = model.pos[0].data.clone()
                        else:
                            best_pos[0].data.copy_(model.pos[0].data)
                
                    logging.info("full step %.3f ms\n" % ((time.time() - t0) * 1000))

                def check_plateau(x, window=10, threshold=0.001):
                    """
                    @brief check if overflow is converge but still too large
                    case 2 in check_divergence
                    @param x overflow list
                    @param window window=15
                    @param threshold threshold=0.001
                    """
                    if len(x) < window:
                        return False
                    x = x[-window:]
                    return (np.max(x) - np.min(x)) / np.mean(x) < threshold

                def check_divergence(x, window=50, threshold=0.05):
                    """
                    @brief check if divergence through x
                    there are 3 cases will return true 
                    1.overflow is too large than best_overflow
                    2.overflow is converge but still too large
                    3.overflow changes too frequently
                    @param x divergence list, each element is a list have 2 items:hpwl and overflow
                    @param window we will check if divergence through window length items in x
                    @param threshold threshold=0.1 * overflow_list[-1]
                    """
                    if len(x) < window or best_metric[0] is None:
                        return False
                    x = np.array(x[-window:])
                    overflow_mean = np.mean(x[:, 1])
                    overflow_diff = np.maximum(0, np.sign(x[1:, 1] - x[:-1, 1])).astype(np.float32)
                    overflow_diff = np.sum(overflow_diff) / overflow_diff.shape[0]
                    overflow_range = np.max(x[:, 1]) - np.min(x[:, 1])
                    wl_mean = np.mean(x[:, 0])
                    wl_ratio, overflow_ratio = (wl_mean - best_metric[0].hpwl.item()) / best_metric[0].hpwl.item(), \
                    (overflow_mean - max(params.stop_overflow, best_metric[0].overflow.item())) / best_metric[0].overflow.item()
                    if wl_ratio > threshold * 1.2:
                        # this condition is not suitable for routability-driven opt with cell inflation
                        if (not params.routability_opt_flag) and overflow_ratio > threshold:
                            logging.warning(
                                f"Divergence detected: overflow increases too much than best overflow ({overflow_ratio:.4f} > {threshold:.4f})"
                            )
                            return True
                        elif (overflow_ratio > 0.1) and (overflow_range < threshold):
                            logging.warning(
                                f"Divergence detected: overflow plateau ({overflow_range:.4f} < {threshold:.4f})"
                            )
                            return True
                        elif overflow_diff > 0.6:
                            logging.warning(
                                f"Divergence detected: overflow fluctuate too frequently ({overflow_diff:.2f} > 0.6)"
                            )
                            return True
                        else:
                            return False
                    else:
                        return False

                Lgamma_metrics = all_metrics

                if params.routability_opt_flag:
                    adjust_area_flag = True
                    adjust_route_area_flag = params.adjust_rudy_area_flag
                    adjust_pin_area_flag = params.adjust_pin_area_flag
                    num_area_adjust = 0

                Llambda_flat_iteration = 0

                ### preparation for self-adaptive divergence check
                overflow_list = [1]
                divergence_list = []
                min_perturb_interval = 50
                stop_placement = 0
                last_perturb_iter = -min_perturb_interval
                perturb_counter = 0

                for Lgamma_step in range(model.Lgamma_iteration):
                    Lgamma_metrics.append([])
                    Llambda_metrics:List[List[EvalMetrics]] = Lgamma_metrics[-1]
                    for Llambda_density_weight_step in range(model.Llambda_density_weight_iteration):
                        Llambda_metrics.append([])
                        Lsub_metrics = Llambda_metrics[-1]
                        for Lsub_step in range(model.Lsub_iteration):
                            ## divergence threshold should decrease as overflow decreases
                            ## only detect divergence when overflow is relatively low but not too low
                            div_flag = check_divergence(
                                # sometimes maybe too aggressive...
                                divergence_list, window=3, threshold=0.1 * overflow_list[-1])
                            if (
                                len(placedb.regions) == 0
                                and params.stop_overflow * 1.1 < overflow_list[-1] < params.stop_overflow * 4
                                and div_flag
                            ):
                                model.pos[0].data.copy_(best_pos[0].data)
                                stop_placement = 1

                                logging.error(
                                    "possible DIVERGENCE detected, roll back to the best position recorded"
                                )

                            one_descent_step(
                                Lgamma_step, Llambda_density_weight_step, Lsub_step, iteration, Lsub_metrics
                            )

                            if len(placedb.regions) == 0:
                                overflow_list.append(Llambda_metrics[-1][-1].overflow.data.item())
                                divergence_list.append(
                                    [
                                        Llambda_metrics[-1][-1].hpwl.data.item(),
                                        Llambda_metrics[-1][-1].overflow.data.item(),
                                    ]
                                )

                            ## quadratic penalty and entropy injection
                            if (
                                len(placedb.regions) == 0
                                and iteration - last_perturb_iter > min_perturb_interval
                                and check_plateau(overflow_list, window=15, threshold=0.001)
                            ):
                                if overflow_list[-1] > 0.9:  # stuck at high overflow
                                    model.quad_penalty = True
                                    model.density_factor *= 2
                                    logging.info(
                                        f"Stuck at early stage. Turn on quadratic penalty with double density factor to accelerate convergence"
                                    )
                                    last_perturb_iter = iteration
                                    perturb_counter += 1

                            iteration += 1
                            # stopping criteria
                            if Lsub_stop_criterion(
                                Lgamma_step, Llambda_density_weight_step, Lsub_step, Lsub_metrics
                            ):
                                break
                        Llambda_flat_iteration += 1
                        # update density weight
                        if Llambda_flat_iteration > 1:
                            model.update_density_weight(
                                Llambda_metrics[-1][-1],
                                Llambda_metrics[-2][-1]
                                if len(Llambda_metrics) > 1
                                else Lgamma_metrics[-2][-1][-1],
                                Llambda_flat_iteration,
                            )
                        # logging.debug("update density weight %.3f ms" % ((time.time()-t2)*1000))
                        if Llambda_stop_criterion(Lgamma_step, Llambda_density_weight_step, Llambda_metrics):
                            break

                        # for routability optimization
                        if (
                            params.routability_opt_flag
                            and num_area_adjust < params.max_num_area_adjust
                            and Llambda_metrics[-1][-1].overflow < params.node_area_adjust_overflow
                        ):
                            content = (
                                "routability optimization round %d: adjust area flags = (%d, %d, %d)"
                                % (
                                    num_area_adjust,
                                    adjust_area_flag,
                                    adjust_route_area_flag,
                                    adjust_pin_area_flag,
                                )
                            )
                            pos = model.data_collections.pos[0]

                            route_utilization_map = None
                            pin_utilization_map = None
                            if adjust_route_area_flag:
                                route_utilization_map = model.route_utilization_map(pos)
                                if params.plot_flag:
                                    path = "./%s/%s" % (params.result_dir, params.design_name())
                                    figname = "%s/plot/route%d.png" % (path, num_area_adjust)
                                    os.system("mkdir -p %s" % (os.path.dirname(figname)))
                                    plt.imsave(
                                        figname, route_utilization_map.data.cpu().numpy().T, origin="upper"
                                    )
                            if adjust_pin_area_flag:
                                pin_utilization_map = model.pin_utilization_map(pos)
                                if params.plot_flag:
                                    path = "./%s/%s" % (params.result_dir, params.design_name())
                                    figname = "%s/plot/pin%d.png" % (path, num_area_adjust)
                                    os.system("mkdir -p %s" % (os.path.dirname(figname)))
                                    plt.imsave(
                                        figname, pin_utilization_map.data.cpu().numpy().T, origin="upper"
                                    )
                            (
                                adjust_area_flag,
                                adjust_route_area_flag,
                                adjust_pin_area_flag,
                            ) = model.adjust_node_area(
                                pos, route_utilization_map, pin_utilization_map
                            )
                            content += " -> (%d, %d, %d)" % (
                                adjust_area_flag,
                                adjust_route_area_flag,
                                adjust_pin_area_flag,
                            )
                            logging.info(content)
                            if adjust_area_flag:
                                num_area_adjust += 1
                                # restart Llambda
                                model.electric_potential.reset()
                                model.electric_overflow.reset()
                                model.pin_utilization_map.reset()
                                model.initialize_density_weight(params, placedb)
                                model.density_weight.mul_(0.1 / params.density_weight)
                                logging.info("density_weight = %.6E" % (model.density_weight.data))
                                # load state to restart the optimizer
                                optimizer.load_state_dict(initial_state)
                                # must after loading the state
                                initialize_learning_rate(pos)
                                # increase iterations of the sub problem to slow down the search
                                model.Lsub_iteration = model.routability_Lsub_iteration

                                # reset best metric
                                best_metric[0] = None
                                best_pos[0] = None

                                break

                    # gradually reduce gamma to tradeoff smoothness and accuracy
                    model.update_gamma(Lgamma_step, Llambda_metrics[-1][-1].overflow)
                    model.precondition.set_overflow(Llambda_metrics[-1][-1].overflow)
                    if Lgamma_stop_criterion(Lgamma_step, Lgamma_metrics) or stop_placement == 1:
                        break

                    # update learning rate
                    if optimizer_name.lower() in ["sgd", "adam", "sgd_momentum", "sgd_nesterov"]:
                        if "learning_rate_decay" in global_place_params:
                            scheduler.step()

                logging.info("optimizer %s takes %.3f seconds" % (optimizer_name, time.time() - tt))

            # recover node size and pin offset for legalization, since node size is adjusted in global placement
            if params.routability_opt_flag:
                with torch.no_grad():
                    # convert lower left to centers
                    model.pos[0][: placedb.num_movable_nodes].add_(
                        model.data_collections.node_size_x[: placedb.num_movable_nodes] / 2
                    )
                    model.pos[0][placedb.num_nodes : placedb.num_nodes + placedb.num_movable_nodes].add_(
                        model.data_collections.node_size_y[: placedb.num_movable_nodes] / 2
                    )
                    model.data_collections.node_size_x.copy_(model.data_collections.original_node_size_x)
                    model.data_collections.node_size_y.copy_(model.data_collections.original_node_size_y)
                    # use fixed centers as the anchor
                    model.pos[0][: placedb.num_movable_nodes].sub_(
                        model.data_collections.node_size_x[: placedb.num_movable_nodes] / 2
                    )
                    model.pos[0][placedb.num_nodes : placedb.num_nodes + placedb.num_movable_nodes].sub_(
                        model.data_collections.node_size_y[: placedb.num_movable_nodes] / 2
                    )
                    model.data_collections.pin_offset_x.copy_(model.data_collections.original_pin_offset_x)
                    model.data_collections.pin_offset_y.copy_(model.data_collections.original_pin_offset_y)
        else:
            density_weight = 0.0
            place_params = {
                "iteration":0,
                "wirelength":"weighted_average"
            }
            model = PlaceObj(
                params,
                placedb,
                density_weight,
                place_params,
            ).to(placedb.device)
            model.train()
            eval_ops = {
                    "hpwl": model.hpwl,
                    "overflow": model.electric_overflow,
                }
            if params.routability_opt_flag:
                eval_ops.update(
                    {
                        "route_utilization": model.route_utilization_map,
                        "pin_utilization": model.pin_utilization_map,
                    }
                )
            cur_metric = EvalMetrics(iteration)
            cur_metric.evaluate(placedb, eval_ops, model.pos[0].data.clone())
            cur_metric.objective, _ = model.obj_and_grad_fn(model.pos[0].detach().clone().requires_grad_(True))
            all_metrics.append(cur_metric)
            logging.info(cur_metric)
            if params.plot_flag:
                model.plot(self.gendb_id, "expert_placement", cur_metric.iteration, model.pos[0].data.clone().cpu().numpy(), str(cur_metric))

        # legalization
        if params.legalize_flag:
            tt = time.time()
            model.pos[0].data.copy_(model.legalization(model.pos[0]))
            logging.info("legalization takes %.3f seconds" % (time.time() - tt))
            cur_metric = EvalMetrics(iteration + 1)
            cur_metric.gamma = model.gamma.data.clone()
            cur_metric.density_weight = model.density_weight.data.clone()
            cur_metric.evaluate(placedb, eval_ops, model.pos[0].data.clone())
            cur_metric.objective, _ = model.obj_and_grad_fn(model.pos[0].detach().clone().requires_grad_(True))
            all_metrics.append(cur_metric)
            lrs.append(optimizer.param_groups[0]["lr"].data.clone().cpu().numpy())
            logging.info(cur_metric)
            if params.plot_flag:
                model.plot(self.gendb_id, "legalization", cur_metric.iteration, model.pos[0].data.clone().cpu().numpy(), str(cur_metric))
            iteration += 1            

        # flatten metrics
        flatten = lambda l: sum(map(flatten, l), []) if isinstance(l, list) else [l]
        all_metrics = flatten(all_metrics)
            
        # plot metric
        if params.metric_plot_flag:  
            
            density_weights = [metric.density_weight.data.item() for metric in all_metrics]
            gammas = [metric.gamma.data.item() for metric in all_metrics]
            
            objectives = [metric.objective.data.item() for metric in all_metrics]
            hpwls = [metric.hpwl.data.item() for metric in all_metrics]
            overflows = [metric.overflow.data.item() for metric in all_metrics]
            max_densitys = [metric.max_density.data.item() for metric in all_metrics]
            if params.routability_opt_flag:
                route_utilizations = [metric.route_utilization.data.item() for metric in all_metrics]
                pin_utilizations = [metric.pin_utilization.data.item() for metric in all_metrics]
            
            epochs = np.arange(len(objectives))
            path = "%s/%s/plot" % (params.result_dir, params.design_name())
            os.makedirs(path, exist_ok=True)
            
            plt.figure()
            plt.plot(epochs, np.log10(density_weights), color="r", label='density_weights')
            plt.legend()
            plt.xlabel('epochs')
            plt.ylabel('density_weights/log10')
            figname = os.path.join(path, "density_weights.png")
            plt.savefig(figname)
            
            plt.figure()
            plt.plot(epochs, np.log10(gammas), color="g", label='gammas')
            plt.legend()
            plt.xlabel('epochs')
            plt.ylabel('gammas/log10')
            figname = os.path.join(path, "gammas.png")
            plt.savefig(figname)
            
            plt.figure()
            plt.plot(epochs, np.log10(lrs[0 : len(epochs)]), color="b", label='learning rate')
            plt.legend()
            plt.xlabel('epochs')
            plt.ylabel('learning rate/log10')
            figname = os.path.join(path, "lr.png")
            plt.savefig(figname)

            if params.routability_opt_flag:
                fig, axis = plt.subplots(2, 3, figsize=(5 * 6, 5 * 3))
                axis[0, 0].plot(epochs, np.log10(objectives), color="red")
                axis[0, 0].set_title("objectives/log10")
                axis[0, 1].plot(epochs, np.log10(hpwls), color="blue")
                axis[0, 1].set_title("hpwls/log10")
                axis[0, 2].plot(epochs, overflows, color="green")
                axis[0, 2].set_title("overflows")
                axis[1, 0].plot(epochs, max_densitys, color="yellow")
                axis[1, 0].set_title("max_densitys")
                axis[1, 1].plot(epochs, route_utilizations, color="orange")
                axis[1, 1].set_title("route_utilizations")
                axis[1, 2].plot(epochs, pin_utilizations, color="black")
                axis[1, 2].set_title("pin_utilizations")
            else:
                fig, axis = plt.subplots(2, 2, figsize=(5 * 4, 5 * 3))
                axis[0, 0].plot(epochs, np.log10(objectives), color="red")
                axis[0, 0].set_title("objectives/log10")
                axis[0, 1].plot(epochs, np.log10(hpwls), color="blue")
                axis[0, 1].set_title("hpwls/log10")
                axis[1, 0].plot(epochs, overflows, color="green")
                axis[1, 0].set_title("overflows")
                axis[1, 1].plot(epochs, max_densitys, color="yellow")
                axis[1, 1].set_title("max_densitys")
                
            fig.tight_layout(pad=2.0)
            figname = os.path.join(path, "obj.png")
            plt.savefig(figname)

        if params.gif_flag:
            path = "./%s/%s/plot/" % (params.result_dir, params.design_name())
            model.images2gif(path + "global_placement"   , path + "gp.gif")
            
        if params.write_back_flag: 
            # save results
            cur_pos = model.pos[0].data.clone().cpu().numpy()
            # apply solution
            placedb.apply(
                params,
                cur_pos[0 : placedb.num_movable_nodes],
                cur_pos[placedb.num_nodes : placedb.num_nodes + placedb.num_movable_nodes],
            )

        return all_metrics[-1]