from dataclasses import make_dataclass, fields, asdict
from operator import itemgetter
import os
import sys
import copy
import json
from pathlib import Path
import logging
import ConfigSpace as CS
import ConfigSpace.hyperparameters as CSH
from ConfigSpace.read_and_write import json as CS_JSON

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))
from hpbandster.core.worker import Worker
from DREAMPlacePCB.Placer import PlacementEngine
from tuner_configs import (
    AUTODMP_BASE_CONFIG,
    AUTODMP_BASE_PPA,
    AUTODMP_BAD_RATIO,
    AUTODMP_BEST_CFG,
)
sys.path.pop()

opj = os.path.join

# Wrap AutoDMP config in dataclass
def update_cfg(self, cfg):
    my_fields = [f.name for f in fields(self)]
    for p, v in cfg.items():
        if p in my_fields:
            setattr(self, p, type(getattr(self, p))(v))
        elif "GP_" in p:
            p = p.replace("GP_", "")
            gp = self.global_place_stages[0]
            if p in gp:
                gp[p] = type(gp[p])(v)


AutoDMPConfig = make_dataclass(
    "AutoDMPConfig", AUTODMP_BASE_CONFIG, namespace={"update_cfg": update_cfg}
)


class AutoDMPWorker(Worker):
    def __init__(
        self,
        log_dir,
        *args,
        default_config,
        route_utilization_ratio,
        overflow_ratio,
        multiobj=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.log_dir = log_dir
        self.route_utilization_ratio = route_utilization_ratio
        self.overflow_ratio = overflow_ratio
        self.multiobj = multiobj

        # update default with best parameters
        path_reuse = Path(default_config["reuse_params"])
        if path_reuse.suffix == ".json" and path_reuse.is_file():
            with path_reuse.open() as f:
                best_params = json.load(f)
        else:
            best_params = AUTODMP_BEST_CFG.get(default_config["reuse_params"], {})
            # best params will be ""
        print("Reusing best parameters:", best_params)
        self.default_config = {**best_params, **default_config}

        # setup PPA reference
        path_ppa = Path(default_config["base_ppa"]).resolve()
        if path_ppa.suffix == ".json" and path_ppa.is_file():
            with path_ppa.open() as f:
                self.base_ppa = json.load(f)
        else:
            self.base_ppa = AUTODMP_BASE_PPA[default_config["base_ppa"]]
        print("PPA reference:", self.base_ppa)
        self.bad_run = {
            k: float(v * AUTODMP_BAD_RATIO) for k, v in self.base_ppa.items()
        }

        self.PlaceEngine = PlacementEngine()

    def _create_params(self, config):
        params = AutoDMPConfig(**AUTODMP_BASE_CONFIG)
        params.update_cfg(self.default_config)
        params.update_cfg(config)
        return asdict(params)
    
    def _update_logger(self, working_directory, suffix=""):
        # change logger
        log = logging.getLogger()
        filehandler = logging.FileHandler(
            opj(working_directory, f"AutoDMPPCB{suffix}.log"), "w"
        )
        formatter = logging.Formatter("[%(levelname)-7s] %(name)s - %(message)s")
        filehandler.setFormatter(formatter)
        log = logging.getLogger()
        for hdlr in log.handlers[:]:  # remove existing file handler
            if isinstance(hdlr, logging.FileHandler):
                log.removeHandler(hdlr)
        log.addHandler(filehandler)
        log.setLevel(logging.DEBUG)

    def compute(self, config_id, config, budget, working_directory, **kwargs):
        config_identifier = "run-" + "_".join([str(x) for x in config_id])

        working_directory = opj(self.log_dir, config_identifier)
        os.makedirs(working_directory, exist_ok=True)

        self._update_logger(working_directory)

        config["result_dir"] = working_directory
        params = self._create_params(config)
        self.PlaceEngine.update_params(params)

        config_filename = opj(working_directory, "parameters.json")
        self.PlaceEngine.params.dump(config_filename)

        result = self.PlaceEngine()

        if float("inf") in result.values():
            ppa = self.bad_run
        else:
            ppa = result

        hpwl_norm = ppa["hpwl"] / self.base_ppa["hpwl"]
        overflow_norm = ppa["overflow"] / self.base_ppa["overflow"]
        route_utilization_norm = ppa["route_utilization"] / self.base_ppa["route_utilization"]

        if self.multiobj:
            return {
                "loss": (hpwl_norm, overflow_norm, route_utilization_norm),
                "info": result,
            }
        else:
            cost = (
                hpwl_norm
                + self.overflow_ratio * overflow_norm
                + self.route_utilization_ratio * route_utilization_norm
            )
            result.update({"cost": float(cost)})
            return {
                "loss": float(cost),
                "info": result,
            }

    @staticmethod
    def get_configspace(config_file: str, seed=None):
        # read JSON config if provided
        if os.path.isfile(config_file):
            with open(config_file, "r") as f:
                cs = CS_JSON.read(f.read())
                cs.seed(seed)
            return cs