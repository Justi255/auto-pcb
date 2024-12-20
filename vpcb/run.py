import os
import json
import copy
import shutil
from placer.AutoDMPPCB.DREAMPlacePCB.Placer import PlacementEngine
from placer.pltools import main as pltools

def main():
    filename = "config.json"
    filename = os.path.join(os.path.dirname(__file__), filename)
    with open(filename, 'r') as f:
        config_info = json.load(f)
        io_path = dict([(key, config_info[key]) for key in ["pcb_input", "result_dir"]])
        
        # Loading placer model
        io_path_placer = copy.deepcopy(io_path)
        io_path_placer["result_dir"]["value"] = io_path["result_dir"]["value"] + "placer_results/"
        if config_info["placer"]["value"] == "DREAMPlacePCB":
            engine = PlacementEngine()
            new_params = {
                "pcb_input":io_path_placer["pcb_input"]["value"],
                "result_dir":io_path_placer["result_dir"]["value"]
            }
            engine.update_params(new_params)
            ppa = engine()
        elif config_info["placer"]["value"] == "ADSAPlace":
            # TODO
            print("Unrecognized placer.")
        elif config_info["placer"]["value"] == "pltools":
            pltools.main(io_path_placer["pcb_input"]["value"], io_path_placer["result_dir"]["value"])
        else:
            print("Unrecognized placer.")
        
        # Prepare router input
        file_name = os.path.basename(io_path["pcb_input"]["value"])
        design_name = file_name.split('.')[0]
        placer_result_path = os.path.join(io_path_placer["result_dir"]["value"], design_name)
        placer_result_file = os.path.join(placer_result_path, file_name)
        if not os.path.isfile(placer_result_file):
            print("Failed to place.")
            return

        # Loading router model
        io_path_router = copy.deepcopy(io_path)
        io_path_router["pcb_input"]["value"] = placer_result_file
        io_path_router["result_dir"]["value"] = io_path["result_dir"]["value"] + "router_results/"

        if config_info["router"]["value"] == "autorouting_fr":
            # Prepare router input for autorouting_fr 把pcb文件和pro文件复制到router_result/bm*/目录下，然后调用Kicad2Dan.py转化为FR的输入dsn文件
            router_result_path = os.path.join(io_path_router["result_dir"]["value"], design_name)
            if not os.path.isdir(router_result_path):
                os.makedirs(router_result_path)
    
            shutil.copy(placer_result_file, router_result_path)
    
            find_in_dir = os.path.dirname(io_path["pcb_input"]["value"])
            root, ext = os.path.splitext(file_name)
            target_file = root + ".kicad_pro"
            is_find = False
            pro_file_path = None
            for root_dir, dirs, files in os.walk(find_in_dir):
                if target_file in files:
                    pro_file_path = os.path.join(root_dir, target_file)
                    is_find = True
                    break
            if is_find:
                shutil.copy(pro_file_path, router_result_path)
            
            kicad_file = os.path.join(router_result_path, file_name)
            os.system("/bin/python3 parser/Kicad2Dsn.py %s %s" % (kicad_file, router_result_path))
            dsn_file = os.path.join(router_result_path, root + ".dsn")

            # set input file path for router
            io_path_router["pcb_input"]["value"] = dsn_file

            fr_dir = "router/autorouting_fr/"
            jar_path = fr_dir + "build/libs/autorouting_fr-1.0-SNAPSHOT.jar"
            
            # build if necessary 
            if not os.path.isfile(jar_path):
                os.chdir(fr_dir)
                os.system("gradle build")
                os.chdir("../..")
            
            # run jar by parameters
            os.system("java -jar "+ jar_path + " " + io_path_router["pcb_input"]["value"] + " " + io_path_router["result_dir"]["value"])

            # router result processing # TODO
            # ses_file = os.path.join(router_result_path, design_name + ".ses")
            # os.system("/bin/python3 Ses2Kicad.py %s %s %s" % (kicad_file, ses_file, router_result_path))

        else:
            print("Unrecognized router.")

if __name__ == "__main__":
    main()