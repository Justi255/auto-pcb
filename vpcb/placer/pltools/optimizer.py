# Desc: global optimizer
import time
import numpy as np
from pltools.placer import Placer
from pltools.checker import Checker
from shapely.geometry import Polygon
import math
import copy
import pltools.visualizer as vis

class Optimizer:
    def __init__(self):
        pass

    def configure_optimizer(self):
        pass

    def run(self):
        pass
class SAplacer:
    def __init__(self, Modules, Nets, boundary, outer_iter, inner_iter, seed = 19937):
        '''
        input:
            Modules: list of modules
            Nets: list of nets
            boundary: [x_max, x_min, y_max, y_min]
            outer_iter: number of outer iterations
            inner_iter: number of inner iterations
        '''
        self.modules = Modules
        self.num_modules = len(self.modules)
        self.nets = Nets

        self.boundary = boundary
        self.width = boundary[0] - boundary[1]
        self.height = boundary[2] - boundary[3]

        self.outer_iter = outer_iter
        self.inner_iter = inner_iter

        self.initial_iter = 1000
        self.seed = seed
        self.temperature = 0.5


        self.norma_wl = 0.0
        self.norma_rd = 0.0
        self.norma_al = 0.0
        self.norma_oa = 0.0
        #for best solution
        self.best_cost = float('inf')
        self.best_oa = float('inf')
        self.best_sol = Modules
        #0:hpwl 1:rudy 2:alignment 3:overlap
        self.weight = [0.5, 0.1, 0.1, 0.3]
        # self.cost = [0.0, 0.0, 0.0, 0.0]
        # self.hpwl = 0.0
        # self.rudy = 0.0
        # self.aligment = 0.0
        # self.overlap = 0.0
        # self.current_cost = float('inf')
        # self.cost_normalized = 0.0
        # self.overlap = 0.0

        self.best_wl = 0.0
        self.best_rd = 0.0
        self.best_al = 0.0
        self.best_i = 0

        #set random seed
        self.rng = np.random.default_rng(self.seed)
        self.prob_swap = 0.25
        self.prob_rotate = 0.15
        self.prob_shift = 0.6

    def run(self, ini_mode):
        #initialize parameters
        self.ini_param()

        #initial placement
        placer = Placer()
        placer.initial_placement(self.modules, self.boundary[0], self.boundary[1], self.boundary[2], self.boundary[3], ini_mode)
        self.set_radius()
        #cost = self.count_allcost()
        t1 = time.time()
        visualizer = vis.Visualizer(self.width, self.height)
        frames = []        
        for i in range(self.outer_iter):
            t2 = time.time()
            visualizer.current_frame = []
            visualizer.objects = []
            visualizer.add_object(self.visualize())
            visualizer.frame_objects()
            frames.append(visualizer.current_frame)
            if i>1:
                print("=====", i, "=====")
                print("Iteration: ", i, "  time: ", t2 - t1, "s","  time per iteration: ", (t2 - t1)/i, "s", "  time left: ", (t2 - t1)/i * (self.outer_iter - i))
                print("Temperatrue:  ", self.temperature, "  Overlap_weight: ", self.weight[3], "  Overlap: ", self.best_oa)
                print(" HPWL: ", cost[1], " rudy: ", cost[2], " alignment: ", cost[3], " overlap: ", cost[4])
                print(" best_cost: ", self.best_cost, " best_oa: ", self.best_oa)
            if i % 5 == 0:
                cost = self.count_allcost()
            for j in range(self.inner_iter * self.num_modules):
                cost = self.random_move(cost)

            self.update_temperature()

        print(" best_wl: ", self.best_wl, " best_rd: ", self.best_rd, " best_al: ", self.best_al, " best_cost: ", self.best_cost, " best_oa: ", self.best_oa)
        visualizer.visualize_layout(framing_on=True, frames=frames, save_gif=True)

        # self.modules = self.best_sol

        #oa_move = 100 * self.num_modules
        # while oa_move > 0:
        #     self.overlap_sol()
        #     cost = self.count_allcost()
        #     oa_move -= 1

        # self.modules = self.best_sol

        # for module in self.modules:
        #     module.radius = 4.0
        #
        # adjust_num = self.inner_iter * self.num_modules

        # while adjust_num > 0 or self.best_oa > 0:
        # while adjust_num > 0:
        #     self.random_move()
        #     if adjust_num % 5 == 0:
        #         self.count_allcost()
        #     adjust_num -= 1
            # if adjust_num < 0:
            #     self.weight[3] *= 1.02
            # if adjust_num<-999:
            #     self.weight[3] = 99999.999
            # if adjust_num<-1999:
            #     break

        # self.modules = self.best_sol


    def ini_param(self):
        sum_wl, sum_rd, sum_al, sum_oa = 0.0, 0.0, 0.0, 0.0
        for i in range(self.initial_iter):
            placer = Placer()
            check = Checker()
            placer.random_placement(self.modules, self.boundary[0], self.boundary[1], self.boundary[2], self.boundary[3])
            for net in self.nets:
                if len(net.pads)==0:
                    continue
                net.UpdateCost(self.modules)
                sum_wl += net.GetCost()[0]
                sum_rd += net.GetCost()[1]
                sum_al += net.GetCost()[2]
            sum_oa += check.Overlap(self.modules)

        self.norma_wl = sum_wl / self.initial_iter
        self.norma_rd = sum_rd / self.initial_iter
        self.norma_al = sum_al / self.initial_iter
        self.norma_oa = max(sum_oa / self.initial_iter, 1.0)

        # a = 0

    def count_allcost(self):
        hpwl = 0.0
        rudy = 0.0
        aligment = 0.0
        cost_normalized = 0.0
        check = Checker()
        for net in self.nets:
            if len(net.pads) == 0:
                continue
            net.UpdateCost(self.modules)
            hpwl += net.GetCost()[0]
            rudy += net.GetCost()[1]
            aligment += net.GetCost()[2]
        cost_normalized = self.weight[0] * hpwl/self.norma_wl + \
                          self.weight[1] * rudy/self.norma_rd + \
                          self.weight[2] * aligment/self.norma_al
        overlap = check.Overlap(self.modules)
        # self.overlap = overlap
        current_cost = self.weight[0]*hpwl/self.norma_wl +\
                       self.weight[1]*rudy/self.norma_rd +\
                       self.weight[2]*aligment/self.norma_al +\
                       self.weight[3]*overlap/self.norma_oa

        cost_vec = []
        cost_vec.append(current_cost)
        cost_vec.append(hpwl)
        cost_vec.append(rudy)
        cost_vec.append(aligment)
        cost_vec.append(overlap)

        if overlap <= self.best_oa and cost_normalized < self.best_cost:
            self.best_oa = overlap
            self.best_cost = cost_normalized
            self.best_sol = copy.deepcopy(self.modules)
            self.best_wl = hpwl
            self.best_rd = rudy
            self.best_al = aligment
        # else:
        #     pass

        elif overlap < self.best_oa:
            self.best_oa = overlap
            self.best_cost = cost_normalized
            self.best_sol = copy.deepcopy(self.modules)
            self.best_wl = hpwl
            self.best_rd = rudy
            self.best_al = aligment

        return cost_vec

        # a = 0


    def random_move(self, current_cost_vec):
        current_wl = current_cost_vec[1]
        current_rd = current_cost_vec[2]
        current_al = current_cost_vec[3]
        current_oa = current_cost_vec[4]
        current_cost = current_cost_vec[0]
        prev_cost = [0.0, 0.0, 0.0]
        trans_cost = [0.0, 0.0, 0.0]
        prev_oa = 0.0
        trans_oa = 0.0
        state = -1
        check = Checker()

        opr_module1 = self.random_choice()
        while opr_module1.lock:
            opr_module1 = self.random_choice()

        moving_module = [opr_module1]
        type_prob = self.rng.uniform(0, 1)
        orig_x1 = opr_module1.x_coordinate
        orig_y1 = opr_module1.y_coordinate

        if type_prob < self.prob_swap:
            state = 0
            opr_module2 = self.random_choice()
            while opr_module2.lock or (opr_module2.id == opr_module1.id):
                opr_module2 = self.random_choice()
            orig_x2 = opr_module2.x_coordinate
            orig_y2 = opr_module2.y_coordinate

            moving_module.append(opr_module2)

            net_hascount = []
            for module in moving_module:
                for net_id in module.netlist:
                    if net_id not in net_hascount:
                        self.nets[net_id].UpdateCost(self.modules)
                        prev_cost[0] += self.nets[net_id].GetCost()[0]
                        prev_cost[1] += self.nets[net_id].GetCost()[1]
                        prev_cost[2] += self.nets[net_id].GetCost()[2]
                        net_hascount.append(net_id)
            prev_oa = check.Overlap_particial(moving_module, self.modules)
            opr1_x = min(max(self.boundary[1], opr_module2.x_coordinate), self.boundary[0] - opr_module1.width)
            opr1_y = min(max(self.boundary[3], opr_module2.y_coordinate), self.boundary[2] - opr_module1.height)

            opr2_x = min(max(self.boundary[1], opr_module1.x_coordinate), self.boundary[0] - opr_module2.width)
            opr2_y = min(max(self.boundary[3], opr_module1.y_coordinate), self.boundary[2] - opr_module2.height)

            opr_module1.setPos(opr1_x, opr1_y)
            opr_module2.setPos(opr2_x, opr2_y)

        elif type_prob > self.prob_swap and type_prob < (self.prob_swap + self.prob_shift):
            state = 1
            for net_id in opr_module1.netlist:
                self.nets[net_id].UpdateCost(self.modules)
                prev_cost[0] += self.nets[net_id].GetCost()[0]
                prev_cost[1] += self.nets[net_id].GetCost()[1]
                prev_cost[2] += self.nets[net_id].GetCost()[2]
            prev_oa = check.Overlap_particial(moving_module, self.modules)
            left_x = min(opr_module1.radius, opr_module1.x_coordinate - self.boundary[1])
            right_x = min(opr_module1.radius, self.boundary[0] - opr_module1.x_coordinate - opr_module1.width)
            down_y = min(opr_module1.radius, opr_module1.y_coordinate - self.boundary[3])
            up_y = min(opr_module1.radius, self.boundary[2] - opr_module1.y_coordinate - opr_module1.height)

            dx = self.rng.uniform(-left_x, right_x) + orig_x1
            dy = self.rng.uniform(-down_y, up_y) + orig_y1
            opr_module1.setPos(dx, dy)

        elif type_prob > (self.prob_swap + self.prob_shift) and type_prob < (self.prob_swap + self.prob_shift + self.prob_rotate):
            state = 2
            for net_id in opr_module1.netlist:
                self.nets[net_id].UpdateCost(self.modules)
                prev_cost[0] += self.nets[net_id].GetCost()[0]
                prev_cost[1] += self.nets[net_id].GetCost()[1]
                prev_cost[2] += self.nets[net_id].GetCost()[2]
            prev_oa = check.Overlap_particial(moving_module, self.modules)
            r = self.rng.integers(0,4)
            opr_module1.setRotation(r)

            opr1_x = min(max(self.boundary[1], opr_module1.x_coordinate), self.boundary[0] - opr_module1.width)
            opr1_y = min(max(self.boundary[3], opr_module1.y_coordinate), self.boundary[2] - opr_module1.height)
            opr_module1.setPos(opr1_x, opr1_y)

        #layer_change
        else:
            state = 3

        net_count = []
        for module in moving_module:
            for net_id in module.netlist:
                if net_id not in net_count:
                    self.nets[net_id].UpdateCost(self.modules)
                    trans_cost[0] += self.nets[net_id].GetCost()[0]
                    trans_cost[1] += self.nets[net_id].GetCost()[1]
                    trans_cost[2] += self.nets[net_id].GetCost()[2]
                    net_count.append(net_id)
        trans_oa = check.Overlap_particial(moving_module, self.modules)

        update_wl = current_wl - prev_cost[0] + trans_cost[0]
        update_rd = current_rd - prev_cost[1] + trans_cost[1]
        update_al = current_al - prev_cost[2] + trans_cost[2]
        update_oa = current_oa - prev_oa + trans_oa

        update_cost = self.weight[0]*update_wl/self.norma_wl +\
                      self.weight[1]*update_rd/self.norma_rd +\
                      self.weight[2]*update_al/self.norma_al +\
                      self.weight[3]*update_oa/self.norma_oa

        update_cost_vec = []
        update_cost_vec.append(update_cost)
        update_cost_vec.append(update_wl)
        update_cost_vec.append(update_rd)
        update_cost_vec.append(update_al)
        update_cost_vec.append(update_oa)

        # current_cost = self.weight[0]*current_wl/self.norma_wl +\
        #                self.weight[1]*current_rd/self.norma_rd +\
        #                self.weight[2]*current_al/self.norma_al +\
        #                self.weight[3]*current_oa/self.norma_oa

        accept = self.Sa_check(current_cost, update_cost)
        if accept:
            return  update_cost_vec

        else:
            #return back
            if state == 0:
                opr_module1.setPos(orig_x1, orig_y1)
                opr_module2.setPos(orig_x2, orig_y2)
            elif state == 1:
                opr_module1.setPos(orig_x1, orig_y1)
            elif state == 2:
                opr_module1.setRotation(4 - r)
                opr_module1.setPos(orig_x1, orig_y1)
            else:
                pass
            return current_cost_vec

        # a = 0

    def random_choice(self):
        randint = self.rng.integers(0, len(self.modules))
        # print(randint)
        random_module = self.modules[randint]
        return random_module

    def set_radius(self):
        Poly_area = []
        for module in self.modules:
            poly = Polygon(module.poly)
            Poly_area.append(poly.area)
        Poly_area.sort()
        Q = Poly_area[math.floor(self.num_modules * 2/3)]
        for module in self.modules:
            poly = Polygon(module.poly)
            if poly.area <= Q:
                module.radius = 25 * Q / (poly.area)
            else:
                module.radius = 100

    def Sa_check(self, current_cost, update_cost):
        # del_cost = 0.0
        p = self.rng.uniform(0, 1)
        del_cost = update_cost - current_cost

        accept_p = np.exp(-del_cost/self.temperature)

        if (del_cost <= 0) or  (p <= accept_p):
            return True
        else:
            return False

    def update_temperature(self):
        self.weight[3] *= 1.02
        if self.temperature > 50e-3:
            self.temperature = self.temperature * 0.985
            for module in self.modules:
                module.radius  = max(0.985 * module.radius, 3 / 4 * module.radius)
        elif self.temperature > 10e-3:
            self.temperature = self.temperature * 0.9992
            for module in self.modules:
                module.radius = max(0.9992 * module.radius, 2 / 4 * module.radius)
        elif self.temperature > 5e-3:
            self.temperature = self.temperature * 0.9955
            for module in self.modules:
                module.radius = max(0.9955 * module.radius, 1 / 4 * module.radius)
        elif self.temperature > 1e-3:
            self.temperature = self.temperature * 0.9965
            for module in self.modules:
                module.radius = max(0.9965 * module.radius, 2.0)
        else:
            if self.temperature > 1e-7:
                self.temperature = 0.885 * self.temperature
            else:
                self.temperature = 1e-10
            for module in self.modules:
                module.radius = max(0.885 * module.radius, 4.0)

    def overlap_sol(self):
        for module in self.modules:
            pass

    def visualize(self):
        axis_x, axis_y, grid_width, grid_height = self.boundary[1], self.boundary[3], self.width, self.height
        obj_list = []
        for module in self.modules:
            offset_x = module.x_coordinate - axis_x
            offset_y = module.y_coordinate - axis_y
            obj_list.append(
                vis.VisualObject(
                    x=offset_x, y=offset_y,
                    shape='rectangle', size1=module.width, size2=module.height,
                    color='purple'))
        return obj_list

        # visualizer = vis.Visualizer(grid_width, grid_height)
        # visualizer.add_object(obj_list)
        # visualizer.frame_objects()


