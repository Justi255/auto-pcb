import os
import sys
import math
import torch
from torch import nn
from torch.autograd import Function

sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)))
import move_boundary_cpp
import move_boundary_cuda
sys.path.pop()


class MoveBoundaryFunction(Function):
    """ 
    @brief Bound cells into layout boundary, perform in-place update 
    """
    @staticmethod
    def forward(pos, node_size_x, node_size_y, xl, yl, xh, yh,
                num_movable_nodes, num_filler_nodes):
        if pos.is_cuda:
            func = move_boundary_cuda.forward
        else:
            func = move_boundary_cpp.forward
        output = func(pos.view(pos.numel()), node_size_x, node_size_y, xl, yl,
                      xh, yh, num_movable_nodes, num_filler_nodes)
        return output


class MoveBoundary(object):
    """ 
    @brief Bound cells into layout boundary, perform in-place update 
    """
    def __init__(self, node_size_x, node_size_y, xl, yl, xh, yh,
                 num_movable_nodes, num_filler_nodes):
        super(MoveBoundary, self).__init__()
        self.node_size_x = node_size_x
        self.node_size_y = node_size_y
        self.xl = xl
        self.yl = yl
        self.xh = xh
        self.yh = yh
        self.num_movable_nodes = num_movable_nodes
        self.num_filler_nodes = num_filler_nodes

    def forward(self, pos):
        return MoveBoundaryFunction.forward(
            pos,
            node_size_x=self.node_size_x,
            node_size_y=self.node_size_y,
            xl=self.xl,
            yl=self.yl,
            xh=self.xh,
            yh=self.yh,
            num_movable_nodes=self.num_movable_nodes,
            num_filler_nodes=self.num_filler_nodes)

    def __call__(self, pos):
        return self.forward(pos)
