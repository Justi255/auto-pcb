import matplotlib
matplotlib.use('Agg')
import os
import sys
import json
import time
import numpy as np
import logging
# for consistency between python2 and python3
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)
sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)))
import configure
from Params         import Params
from PlaceDB        import PlaceDB
from Dataset        import Dataset
from NonLinearPlace import NonLinearPlace
from EvalMetrics    import EvalMetrics
import pdb
sys.path.pop()

class PlacementEngine:
    
    def __init__(self):
        filename = "io.json"
        filename = os.path.join(os.path.dirname(__file__), filename)
        with open(filename, 'r') as f:
            io_path_placer = json.load(f)
        
        logging.root.name = "DREAMPlacePCB"
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)-7s] %(name)s - %(message)s",
        )
        self.params = Params(io_path_placer)
        self.params.load("params.json")
        self.params.printWelcome()

        logging.info("parameters = %s" % (self.params))
        # control numpy multithreading
        os.environ["OMP_NUM_THREADS"] = "%d" % (self.params.num_threads)
        
        assert (not self.params.gpu) or configure.compile_configurations["CUDA_FOUND"] == 'TRUE', \
        "CANNOT enable GPU without CUDA compiled"
    
    def __call__(self):
        """
        @brief Top API to run the entire placement flow.
        @param params parameters
        """
        tt = time.time()
        # read raw database
        rawdb = Dataset(self.params.pcb_input)
        rawdb.load()
        
        self.placedb = PlaceDB(self.params, rawdb)
        if self.params.use_rl:
            for gendb_id in range(rawdb.num_movable_nodes):
                nodes, pads, nets = rawdb.gen_rawdb(gendb_id)
                self.placedb(self.params, nodes, nets, pads)
                logging.info("db id : %d, reading database takes %.2f seconds" % (gendb_id, (time.time() - tt)))
            
                # solve placement
                tt = time.time()
                placer = NonLinearPlace(gendb_id)
                logging.info("non-linear placement initialization takes %.2f seconds" %
                            (time.time() - tt))
                final_metrics:EvalMetrics = placer(self.params, self.placedb)
                logging.info("step:%d, non-linear placement takes %.2f seconds" %
                            (gendb_id, (time.time() - tt)))
        else:
            self.placedb(self.params, rawdb.Nodes, rawdb.Nets, rawdb.Pads)
            logging.info("reading database takes %.2f seconds" % (time.time() - tt))
            # solve placement
            tt = time.time()
            placer = NonLinearPlace(gendb_id=0)
            logging.info("non-linear placement initialization takes %.2f seconds" %
                        (time.time() - tt))
            final_metrics:EvalMetrics = placer(self.params, self.placedb)
            logging.info("non-linear placement takes %.2f seconds" % (time.time() - tt))            

        if self.params.write_back_flag: 
            # write placement solution
            path = "./%s/%s/" % (self.params.result_dir, self.params.design_name())
            if not os.path.exists(path):
                os.system("mkdir -p %s" % (path))
            gp_out_file = os.path.join(
                path,
                "%s.unrouted.%s" % (self.params.design_name(), "kicad_pcb"))
            self.placedb.write(gp_out_file)
            
        final_ppa = {
            "hpwl": final_metrics.hpwl.clone().cpu().tolist(),
            "overflow": final_metrics.overflow.clone().cpu().tolist()[0]
        }
        if self.params.routability_opt_flag:
            other_metrics = {
                "route_utilization": final_metrics.route_utilization.clone().cpu().tolist()
            }
            final_ppa.update(other_metrics)
            
        return final_ppa
    
    def update_params(self, new_params):
        self.params.update(new_params)
        logging.info("parameters = %s" % (self.params))


if __name__ == "__main__":
    """
    @brief regreesion test.
    """
    engine = PlacementEngine()
    for i in range(1, 12):
        new_params = {"pcb_input":f"../../../../examples/test_data/bm{i}/bm{i}.unrouted.kicad_pcb"}
        engine.update_params(new_params)
        ppa = engine()
    # ppa = engine()