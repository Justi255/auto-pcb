
#include "DesignRuleChecker.h"
#include "GridBasedRouter.h"
#include "frTime.h"
#include "kicadPcbDataBase.h"
#include "util_router.h"

//#define DRV_CHECKER

int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cout << "Please provide input testcase filename." << std::endl;
        return 0;
    }

    util_router::showSysInfoComdLine(argc, argv);
    GlobalParam_router::setFolders();
    GlobalParam_router::setUsageStart();
    fr::frTime timeObj;

    std::string designName = argv[1];
    std::cout << "Parsing design: " << designName << std::endl;
    kicadPcbDataBase db(designName);

    db.printLayer();
    db.printComp();
    db.printInst();
    db.printNetclass();
    db.printNet();
    // db.printFile();
    db.printPcbRouterInfo();
    db.printDesignStatistics();

    // Report current WL & # vias
    db.printRoutedSegmentsWLAndNumVias();

    GlobalParam_router::showCurrentUsage("Parser");
    GlobalParam_router::setUsageStart();

#ifdef DRV_CHECKER

    std::cout << "Starting design rule checker..." << std::endl;
    DesignRuleChecker checker(db);

    if (argc >= 3) {
        checker.setInputPrecision(atoi(argv[2]));
    }
    if (argc >= 4) {
        checker.setAcuteAngleTol(atof(argv[3]));
    }

    checker.checkAcuteAngleViolationBetweenTracesAndPads();
    // checker.checkTJunctionViolation();

#else
    // Remove all the routed nets
    db.removeRoutedSegmentsAndVias();

    std::cout << "Starting router..." << std::endl;
    srand(GlobalParam_router::gSeed);
    GridBasedRouter router(db);

    if (argc >= 3) {
        router.set_grid_scale(atoi(argv[2]));
    }
    if (argc >= 4) {
        router.set_num_iterations(atoi(argv[3]));
    }
    if (argc >= 5) {
        router.set_enlarge_boundary(atoi(argv[4]));
    }
    if (argc >= 6) {
        router.set_layer_change_weight(atof(argv[5]));
    }
    if (argc >= 7) {
        router.set_track_obstacle_weight(atof(argv[6]));
    }
    if (argc >= 8) {
        router.set_track_obstacle_step_size(atof(argv[7]));
    }
    if (argc >= 9) {
        router.set_via_obstacle_step_size(atof(argv[8]));
    }
    if (argc >= 10) {
        router.set_pad_obstacle_weight(atof(argv[9]));
    }
    // router.testRouterWithPinShape();
    router.initialization();

    // GND (20) to route on Bottom Layer
    // router.set_net_all_layers_pref_weights(20, 1);
    // router.set_net_layer_pref_weight(20, "Bottom", 0);

    // // Differential pairs for BBBC
    // // PDDR_CLKN(228), PDDR_CLK(230)
    // router.set_diff_pair_net_id(228, 230);
    // // DDR_CLKN(376), DDR_CLK(274)
    // router.set_diff_pair_net_id(274, 376);

    // bm2.unrouted.diffpair
    // router.set_diff_pair_net_id(20, 21);
    // router.set_diff_pair_net_id(11, 12);
    // router.set_diff_pair_net_id(14, 16);

    // router.route_diff_pairs();
    // router.route();
    router.route_all();

    // db.printRoutedSegmentsWLAndNumVias();

    std::cout << "routed WL: " << router.get_routed_wirelength()
              << ", routed # vias: " << router.get_routed_num_vias()
              << ", routed # bends: " << router.get_routed_num_bends() << std::endl;

    GlobalParam_router::showCurrentUsage("GridBasedRouter");
    GlobalParam_router::showFinalUsage("End of Program");

    timeObj.print();

#endif

    return 0;
}
