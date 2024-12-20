from pltools.dataset import Dataset


def main(input_file_path, output_file_path):

    ## load the board to be placed
    db = Dataset()
    db.load(input_file_path)


    ## caculate HPWL
    nets = db.Get_Nets()
    modules = db.Get_Modules()
    hpwl = 0
    acc = 0
    for net in nets:
        net.UpdateCost(modules)
        hpwl_tmp= net.GetCost()[0]
        hpwl += hpwl_tmp
        # print("Net:{} {},HPWL:{}".format(acc, net.name, hpwl_tmp))
        acc += 1
    
    print("Total HPWL: ", hpwl)



if __name__ == '__main__':
    # main('src/pltools/examples/testdata/tmp/PCBBenchmarks/{0}/{0}.unrouted.kicad_pcb'.format("bm7"), 'logs/bm7.kicad_pcb')
    # main('src/pltools/examples/testdata/tmp/bm3.unrouted.kicad_pcb', 'logs/bm7.kicad_pcb')
    print('testfile ={0}'.format("bm3.unrouted.kicad_pcb")) 
    main('C:/Users/Administrator/Desktop/{0}'.format("bm3.unrouted.kicad_pcb"), 'logs/')

    print('testfile ={0}'.format("bm3.unrouted.gp22.kicad_pcb"))
    main('C:/Users/Administrator/Desktop/{0}'.format("bm3.unrouted.gp22.kicad_pcb"), 'logs/')


