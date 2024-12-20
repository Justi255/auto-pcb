#include "database/kicadPcbDataBase.h"
#include "getopt.h"
#include "placer.hpp"
#include "router/GridBasedRouter.h"
#include "util.h"



int main(int argc, char *argv[]){

    GlobalParam::setFolders();
    GlobalParam::setUsageStart();
    using namespace std::chrono;

    std::string designName = argv[1];
    std::cout << "Parsing design: " << designName << std::endl;
    kicadPcbDataBase db(designName);
    // db.printLayer();
    // db.printComp();
    // db.printInst();
    // db.printNetclass();
    // db.printNet();
    // db.printFile();
    // db.printPcbRouterInfo();
    // db.printDesignStatistics();
    // db.printRoutedSegmentsWLAndNumVias();

    // Remove all the routed nets
    // db.removeRoutedSegmentsAndVias();


    std::cout << "Starting placer..." << std::endl;
    placer aplacer(db);

    if(argc >= 3){
        aplacer.set_num_iterations(atoi(argv[2]));
    }
    if(argc >= 4){
        aplacer.set_iterations_moves(atoi(argv[3]));
    }
    if(argc >= 5){
        aplacer.set_ini_placemode(atoi(argv[4]));
    }
    if(argc == 6){

        aplacer.placer_flow();
        db.printKiCad();
        GridBasedRouter arouter(db);
        arouter.initialization();
        arouter.route_all();

        
        db.printKiCad();
        GlobalParam::showCurrentUsage("Placer");
        GlobalParam::showFinalUsage("End of Program");
        return 0;
    }

    if(argc >= 7){
        aplacer.test_flow();
        db.printKiCad();
        GlobalParam::showCurrentUsage("Placer");
        GlobalParam::showFinalUsage("End of Program");
        return 0;
    }

    
    aplacer.placer_flow();
    db.printKiCad();
    // std::cout << "outer_iter: " << aplacer.get_num_iterations()
    //           << ", inner_iter: " << aplacer.get_iterations_moves()
    //           << std::endl;

    GlobalParam::showCurrentUsage("Placer");
    GlobalParam::showFinalUsage("End of Program");

    return 0;
}