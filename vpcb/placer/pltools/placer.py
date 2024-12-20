# Desc: pre-placement
import numpy as np
class Placer:
    def __init__(self, seed = 19937):
        self.seed = seed
        self.rng = np.random.default_rng(self.seed)

    def initial_placement(self, Modules, maxx, minx, maxy, miny, ini_mode):
        #center placement
        if ini_mode == 1:
            for module in Modules:
                if module.lock:
                    continue
                module.setPos(1/2*minx + 1/2*maxx - 1/2*module.width, 1/2*maxy + 1/2*miny - 1/2*module.height)
                # module.setRotation(0)

        #greedy placement
        elif ini_mode == 2:
            x_end, y_end = minx, miny
            for module in Modules:
                if module.lock:
                    continue
                if ( x_end + module.width > maxx ) or ( y_end + module.height > maxy ):
                    x_end, y_end = minx, miny
                module.setPos(x_end, y_end)
                x_end += module.width
                y_end += module.height
        #spiral placement
        elif ini_mode == 3:
            num_components = len(Modules)

            # 0 up, 1 right, 2 down, 3 left
            move_type = 0

            #count gird number
            x_grid, y_grid = 0, 0
            while (x_grid * y_grid) < num_components:
                if x_grid <= y_grid:
                    x_grid += 1
                else:
                    y_grid += 1

            x_width = (maxx - minx)/x_grid
            y_width = (maxy - miny)/y_grid
            #check boundary
            x, y = 0, 0
            x_max = x_grid
            x_min = 1
            y_max = y_grid
            y_min = 0
            for module in Modules:
                if module.lock:
                    continue
                #up
                if move_type == 0:
                    if y < y_max:
                        if (miny + y * y_width + module.height) < maxy:
                            module.setPos(minx + x * x_width, miny + y * y_width)
                        else:
                            module.setPos(minx + x * x_width, maxy - module.height)
                        y += 1
                    else:
                        move_type = 1
                        y_max -= 1
                        if (miny + y * y_width + module.height) < maxy:
                            module.setPos(minx + x * x_width, miny + y * y_width)
                        else:
                            module.setPos(minx + x * x_width, maxy - module.height)
                #right
                elif move_type == 1:
                    if x < x_max:
                        if (minx + x * x_width + module.width) < maxx and (miny + y * y_width + module.height) < maxy:
                            module.setPos(minx + x * x_width, miny + y * y_width)
                        else:
                            module.setPos(maxx - module.width, maxy - module.height)
                        x += 1
                    else:
                        move_type = 2
                        x_max -= 1
                        if (minx + x * x_width + module.width) < maxx and (miny + y * y_width + module.height) < maxy:
                            module.setPos(minx + x * x_width, miny + y * y_width)
                        else:
                            module.setPos(maxx - module.width, maxy - module.height)
                #down
                elif move_type == 2:
                    if y > y_min:
                        if (minx + x * x_width + module.width) < maxx and (miny + y * y_width + module.height) < maxy:
                            module.setPos(minx + x * x_width, miny + y * y_width)
                        else:
                            module.setPos(maxx - module.width, maxy - module.height)
                        y -= 1
                    else:
                        move_type = 3
                        y_min += 1
                        if (minx + x * x_width + module.width) < maxx and (miny + y * y_width + module.height) < maxy:
                            module.setPos(minx + x * x_width, miny + y * y_width)
                        else:
                            module.setPos(maxx - module.width, maxy - module.height)
                #left
                elif move_type == 3:
                    if x > x_min:
                        if (minx + x * x_width + module.width) < maxx:
                            module.setPos(minx + x * x_width, miny + y * y_width)
                        else:
                            module.setPos(maxx - module.width, miny + y * y_width)
                        x -= 1
                    else:
                        move_type = 0
                        x_min += 1
                        if (minx + x * x_width + module.width) < maxx:
                            module.setPos(minx + x * x_width, miny + y * y_width)
                        else:
                            module.setPos(maxx - module.width, miny + y * y_width)

        #classification placement
        elif ini_mode == 4:
            for module in Modules:
                if (module.name == 'U'):
                    #place in center
                    module.setPos(1/2*minx + 1/2*maxx - 1/2*module.width, 1/2*maxy + 1/2*miny - 1/2*module.height)
                elif (module.name == 'R') or (module.name == 'C'):
                    pass

    def random_placement(self, Modules, maxx, minx, maxy, miny):
        for module in Modules:
            if module.lock:
                continue
            # rng = np.random.default_rng()
            dx = self.rng.uniform(minx, maxx - module.width)
            dy = self.rng.uniform(miny, maxy - module.height)
            module.setPos(dx, dy)

            r = self.rng.integers(0, 4)
            module.setRotation(r)
            opr1_x = min(max(minx, module.x_coordinate), maxx - module.width)
            opr1_y = min(max(miny, module.y_coordinate), maxy - module.height)
            module.setPos(opr1_x, opr1_y)


    def validate_move(self, Module, layout_w, layout_h):

        pass