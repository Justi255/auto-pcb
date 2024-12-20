from pltools.kicad_parser import kicad_pcb
from pltools.kicad_parser.items import gritems
from pltools.kicad_parser.items import fpitems

import pltools.visualizer as vis

def get_bbox_Gr(obj):
    """Get bounding box of a board."""
    lX = []
    lY = []
    ax = []
    ay = []
    for item in obj.graphicItems:
        # if type(item) != gritems.GrText and type(item) != gritems.GrTextBox and type(item) != fpitems.FpText and type(item) != fpitems.FpTextBox:
        if type(item) == gritems.GrLine:   
            ax.append(item.start.X)
            ax.append(item.end.X)
            ay.append(item.start.Y)
            ay.append(item.end.Y)
            lenth_X = item.end.X - item.start.X
            lenth_Y = item.end.Y - item.start.Y
            lX.append(lenth_X)
            lY.append(lenth_Y)
    x = min(ax)
    y = min(ay)
    width = max(lX)
    height = max(lY)

    return x, y, width, height            

def get_bbox_Fp(obj):
    """Get bounding box of a footprint."""
    lX = []
    lY = []
    ax = []
    ay = []
    for item in obj.graphicItems:
        # if type(item) != gritems.GrText and type(item) != gritems.GrTextBox and type(item) != fpitems.FpText and type(item) != fpitems.FpTextBox:
        if type(item) == fpitems.FpLine:
            ax.append(item.start.X)
            ax.append(item.end.X)
            ay.append(item.start.Y)
            ay.append(item.end.Y)
            lenth_X = item.end.X - item.start.X
            lenth_Y = item.end.Y - item.start.Y
            lX.append(lenth_X)
            lY.append(lenth_Y)  
        if type(item) == fpitems.FpCircle:
            ax.append(item.center.X)
            ay.append(item.center.Y)
            lX.append(abs(item.end.X - item.center.X))
            lY.append(abs(item.end.Y - item.center.Y))
    x = min(ax)
    y = min(ay)
    width = max(lX)
    height = max(lY)

    return x + obj.position.X, y + obj.position.Y, width, height



# Load the board
import os
print(os.getcwd())
board = kicad_pcb.Board().from_file('src/pltools/examples/testdata/test7.kicad_pcb')

axis_x, axis_y, grid_width, grid_height = get_bbox_Gr(board)

obj_list = []
for obj in board.footprints:
    x, y, width, height = get_bbox_Fp(obj)
    offset_x = x - axis_x
    offset_y = y - axis_y
    obj_list.append(
        vis.VisualObject(
            x=offset_x, y=offset_y, 
            shape='rectangle', size1=width, size2=height,  
            color='purple'))

visualizer = vis.Visualizer(grid_width,grid_height)
visualizer.add_object(obj_list)
visualizer.visualize_layout()

