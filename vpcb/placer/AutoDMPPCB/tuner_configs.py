# AutoDMP base config
AUTODMP_BASE_CONFIG = {
    "pcb_input" :"../../../examples/test_data/bm1/bm1.unrouted.kicad_pcb",
    "result_dir" :"output",
    "global_place_stages": [
        {
            "num_bins_x" : 1024, 
            "num_bins_y" : 1024, 
            "iteration" : 1000, 
            "learning_rate" : 0.01, 
            "learning_rate_decay" : 1.0, 
            "wirelength" : "logsumexp", 
            "optimizer" : "nesterov", 
            "Llambda_density_weight_iteration" : 1, 
            "Lsub_iteration" : 1, 
            "routability_Lsub_iteration" : 1
        }
    ],
    "density_weight": 8e-05,
    "stop_overflow": 0.0,
    "RePlAce_ref_hpwl": 1500,
    "RePlAce_LOWER_PCOF": 0.95,
    "RePlAce_UPPER_PCOF": 1.05,
    "gamma": 4.0,
}


# Cost ratio for unfinished AutoDMP runs
AUTODMP_BAD_RATIO = 10


# Base PPA
AUTODMP_BASE_PPA = {
}


# Best found parameters
AUTODMP_BEST_CFG = {
}
