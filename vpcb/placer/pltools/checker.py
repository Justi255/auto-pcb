# Desc: layout cheker and scoring
from shapely.geometry import Polygon #used for overlap checking
class Checker:
    def __init__(self):
        #self.modules = Modules
        pass

    def Overlap(self, Modules):
        oa = 0.0
        for module1 in Modules:
            for module2 in Modules:
                if(module2.id == module1.id):
                    continue
                if module1.lock and module2.lock:
                    continue
                poly_a = Polygon(module1.poly)
                poly_b = Polygon(module2.poly)
                if not poly_a.intersects(poly_b):
                    continue
                overlap_area = poly_a.intersection(poly_b).area
                if overlap_area == 0:
                    continue
                oa += pow(overlap_area, 2) + overlap_area
                # oa += pow(overlap_area, 2)
        oa = oa/2
        return oa

    def Overlap_particial(self, Modules_p, Modules):
        oa = 0.0
        module_count = []
        for module1 in Modules_p:
            module_count.append(module1.id)
            for module2 in Modules:
                if(module2.id == module1.id):
                    continue
                if module2.id in module_count:
                    continue
                # overlap_area = 0.0
                poly_a = Polygon(module1.poly)
                poly_b = Polygon(module2.poly)
                if not poly_a.intersects(poly_b):
                    continue
                overlap_area = poly_a.intersection(poly_b).area

                if overlap_area == 0:
                    continue

                oa += pow(overlap_area, 2) + overlap_area
                # oa += pow(overlap_area, 2)
        return oa



    def check_move(self, module, maxx, minx, maxy, miny):

        pass

    def scoring(self):
        pass
