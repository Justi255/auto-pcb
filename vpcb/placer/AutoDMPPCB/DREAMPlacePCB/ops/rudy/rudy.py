import os
import sys
import math
import torch
from torch import nn
from torch.autograd import Function
import matplotlib.pyplot as plt
import pdb

sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)))
import rudy_cpp
import rudy_cuda
sys.path.pop()


class Rudy(nn.Module):
    def __init__(self,
                 netpin_start,
                 flat_netpin,
                 net_weights,
                 xl,
                 xh,
                 yl,
                 yh,
                 num_bins_x,
                 num_bins_y,
                 deterministic_flag, 
                 initial_utilization_map=None):
        super(Rudy, self).__init__()
        self.netpin_start = netpin_start
        self.flat_netpin = flat_netpin
        self.net_weights = net_weights
        self.xl = xl
        self.yl = yl
        self.xh = xh
        self.yh = yh
        self.num_bins_x = num_bins_x
        self.num_bins_y = num_bins_y
        self.bin_size_x = (xh - xl) / num_bins_x
        self.bin_size_y = (yh - yl) / num_bins_y

        self.deterministic_flag = deterministic_flag

        self.initial_utilization_map = initial_utilization_map

        #plt.imsave("rudy_initial.png", (self.initial_horizontal_utilization_map + self.initial_vertical_utilization_map).data.cpu().numpy().T, origin='lower')

    def forward(self, pin_pos):
        utilization_map = torch.zeros(
            (self.num_bins_x, self.num_bins_y),
            dtype=pin_pos.dtype,
            device=pin_pos.device)
        if pin_pos.is_cuda:
            func = rudy_cuda.forward
        else:
            func = rudy_cpp.forward
        func(pin_pos, self.netpin_start, self.flat_netpin, self.net_weights,
             self.bin_size_x, self.bin_size_y, self.xl, self.yl, self.xh,
             self.yh, self.num_bins_x, self.num_bins_y, self.deterministic_flag, 
             utilization_map)

        # convert demand to utilization in each bin
        bin_area = self.bin_size_x * self.bin_size_y
        utilization_map.mul_(1 / (bin_area))

        if self.initial_utilization_map is not None:
            utilization_map.add_(
                self.initial_utilization_map)

        return utilization_map
