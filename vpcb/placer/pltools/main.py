import os
import sys
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))
from pltools.dataset import Dataset
from pltools.optimizer import SAplacer

from pltools.floorplan import Floorplaner
sys.path.pop()

def main(input_file_path, output_file_path):
    
    # output dir process
    design_name = os.path.basename(input_file_path).replace(".unrouted.kicad_pcb", "")
    path = "./%s/%s/" % (output_file_path, design_name)
    if not os.path.exists(path):
        os.makedirs("mkdir -p %s" % (path))
    path = os.path.join(
        "../",
        path.replace("../", ""))
    gp_out_file = os.path.join(
        path,
        "%s.unrouted.%s" % (design_name, "kicad_pcb"))
    # sys.exit()
    
    ## load the board to be placed
    db = Dataset()
    db.load(input_file_path)

    ## run the simulated annealing algorithm
    outer_iter, inner_iter = 50, 25
    sa = SAplacer(db.Get_Modules(), db.Get_Nets(), db.Get_boundary(), outer_iter, inner_iter)
    sa.run(ini_mode=1)

    ## write the best solution to a file
    db.update_modules(modules=sa.best_sol)
    db.update_board()

    db.wirte_back(path=gp_out_file)

    ## visualize the best solution
    sa.visualize()

def main_partition(input_file_path, output_file_path):
    ## load the board to be placed
    db = Dataset()
    db.load(input_file_path)

    ## partition the board
    partition_list = db.partition(config)

    ## run the simulated annealing algorithm
    outer_iter, inner_iter = 50, 25
    for part in partition_list: 
        sa = SAplacer(db.Get_Modules(part.id), db.Get_Nets(part.id), part.boundary, outer_iter, inner_iter)
        db.update_modules(sa.best_sol, part.id)

    db.update_board()

    ## write the best solution to a file
    db.wirte_back(path=output_file_path)

    ## visualize the best solution
    sa.visualize()

if __name__ == '__main__':
    main('src/pltools/examples/testdata/bm7.kicad_pcb', 'logs/bm7.kicad_pcb')
    # main('src/pltools/examples/testdata/tmp/bm3.unrouted.kicad_pcb', 'logs/bm7.kicad_pcb')

