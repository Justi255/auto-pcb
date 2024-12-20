// GridBasedRouter.h
#ifndef PCBROUTER_GRID_BASED_ROUTER_H
#define PCBROUTER_GRID_BASED_ROUTER_H

#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "BoardGrid.h"
#include "GridDiffPairNet.h"
#include "PcbRouterBoost.h"
#include "globalParam_router.h"
#include "kicadPcbDataBase.h"
#include "util_router.h"

class GridBasedRouter {
   public:
    // ctor
    GridBasedRouter(kicadPcbDataBase &db) : mDb(db) {}
    // dtor
    ~GridBasedRouter() {}

    void route();
    void route_all();
    void route_diff_pairs();
    void initialization();

    // Setter
    void set_grid_scale(const int _iS) {
        GlobalParam_router::inputScale = abs(_iS);
        GlobalParam_router::gridFactor = 1.0 / (float)GlobalParam_router::inputScale;
    }
    void set_num_iterations(const int _numRRI) { GlobalParam_router::gNumRipUpReRouteIteration = abs(_numRRI); }
    void set_enlarge_boundary(const int _eB) { GlobalParam_router::enlargeBoundary = abs(_eB); }

    void set_wirelength_weight(const double _ww) { GlobalParam_router::gWirelengthCost = abs(_ww); }
    void set_diagonal_wirelength_weight(const double _dww) { GlobalParam_router::gDiagonalCost = abs(_dww); }
    void set_layer_change_weight(const double _lCC) { GlobalParam_router::gLayerChangeCost = abs(_lCC); }

    void set_track_obstacle_weight(const double _toc) { GlobalParam_router::gTraceBasicCost = _toc; }
    void set_via_obstacle_weight(const double _voc) { GlobalParam_router::gViaInsertionCost = _voc; }
    void set_pad_obstacle_weight(const double _poc) { GlobalParam_router::gPinObstacleCost = _poc; }

    void set_track_obstacle_step_size(const double _tocss) { GlobalParam_router::gStepTraObsCost = _tocss; }
    void set_via_obstacle_step_size(const double _vocss) { GlobalParam_router::gStepViaObsCost = _vocss; }

    void set_net_layer_pref_weight(const int _netId, const std::string &_layerName, const int _weight);
    void set_net_all_layers_pref_weights(const int _netId, const int _weight);

    void set_diff_pair_net_id(const int _netId1, const int _netId2);

    // Getter
    unsigned int get_grid_scale() { return GlobalParam_router::inputScale; }
    unsigned int get_num_iterations() { return GlobalParam_router::gNumRipUpReRouteIteration; }
    unsigned int get_enlarge_boundary() { return GlobalParam_router::enlargeBoundary; }

    double get_wirelength_weight() { return GlobalParam_router::gWirelengthCost; }
    double get_diagonal_wirelength_weight() { return GlobalParam_router::gDiagonalCost; }
    double get_layer_change_weight() { return GlobalParam_router::gLayerChangeCost; }

    double get_track_obstacle_weight() { return GlobalParam_router::gTraceBasicCost; }
    double get_via_obstacle_weight() { return GlobalParam_router::gViaInsertionCost; }
    double get_pad_obstacle_weight() { return GlobalParam_router::gPinObstacleCost; }
    double get_track_obstacle_step_size() { return GlobalParam_router::gStepTraObsCost; }
    double get_via_obstacle_step_size() { return GlobalParam_router::gStepViaObsCost; }

    double get_total_cost() { return bestTotalRouteCost; }
    double get_routed_wirelength();
    double get_routed_wirelength(std::vector<MultipinRoute> &mpr);
    int get_routed_num_vias();
    int get_routed_num_vias(std::vector<MultipinRoute> &mpr);
    int get_routed_num_bends();
    int get_routed_num_bends(std::vector<MultipinRoute> &mpr);

   private:
    void testRouterWithPinShape();
    void routeSingleIteration(const bool ripupRoutedNet = false);
    void routeDiffPairs(const bool ripupRoutedNet = false);
    void routeSignalNets(const bool ripupRoutedNet = false);

    bool writeNetsFromGridPaths(std::vector<MultipinRoute> &multipinNets, std::ofstream &ofs);  //deprectaed
    //void
    void writeSolutionBackToDbAndSaveOutput(const std::string fileNameTag, std::vector<MultipinRoute> &multipinNets);

    // Helpers
    void setupBoardGrid();
    void setupLayerMapping();
    void setupGridNetclass();
    void setupGridDiffPairNetclass(const int netclassId1, const int netclassId2, int &gridDiffPairNetclassId);
    void setupGridNetsAndGridPins();
    void setupGridPin(const padstack &pad, const instance &inst, GridPin &gridPin);
    void setupGridPin(const padstack &pad, const instance &inst, const int gridExpansion, GridPin &gridPin);
    void setupGridPinPseudoPins(const padstack &pad, const instance &inst, const int gridExpansion, GridPin &gridPin);
    void setupGridPinPolygonAndExpandedPolygon(const padstack &pad, const instance &inst, const double polygonExpansion, GridPin &gridPin);
    void setupGridPinContractedBox(const padstack &pad, const instance &inst, const int gridContraction, GridPin &gridPin);
    float getOverallRouteCost(const std::vector<MultipinRoute> &gridNets);

    // Obastcle costs
    void addAllPinCostToGrid(const int);
    // void addAllPinInflationCostToGrid(const int);
    void addPinAvoidingCostToGrid(const Pin &, const float, const bool, const bool, const bool, const int inflate = 0);
    void addPinAvoidingCostToGrid(const padstack &, const instance &, const float, const bool, const bool, const bool, const int inflate = 0);
    void addPinAvoidingCostToGrid(const GridPin &gridPin, const float value, const bool toViaCost, const bool toViaForbidden, const bool toBaseCost, const int inflate = 0);
    // PadShape version
    // void addPinShapeAvoidingCostToGrid(const GridPin &gridPin, const float value, const bool toViaCost, const bool toViaForbidden, const bool toBaseCost);

    // Rasterize circle
    void getRasterizedCircle(const int radius, const double radiusFloating, std::vector<Point_2D<int> > &grids);

    // Pin Layers on Grid
    bool getGridLayers(const Pin &, std::vector<int> &layers);
    bool getGridLayers(const padstack &, const instance &, std::vector<int> &layers);

    int getNextRipUpNetId();
    std::string getParamsNameTag();

    // Utilities
    int dbLengthToGridLengthCeil(const double dbLength) {
        return (int)ceil(dbLength * GlobalParam_router::inputScale);
    }
    int dbLengthToGridLengthFloor(const double dbLength) {
        return (int)floor(dbLength * GlobalParam_router::inputScale);
    }
    double dbLengthToGridLength(const double dbLength) {
        return dbLength * GlobalParam_router::inputScale;
    }
    double gridLengthToDbLength(const double gridLength) {
        return gridLength / GlobalParam_router::inputScale;
    }

    bool dbPointToGridPoint(const point_2d &dbPt, point_2d &gridPt);
    bool dbPointToGridPointCeil(const Point_2D<double> &dbPt, Point_2D<int> &gridPt);
    bool dbPointToGridPointFloor(const Point_2D<double> &dbPt, Point_2D<int> &gridPt);
    bool dbPointToGridPointRound(const Point_2D<double> &dbPt, Point_2D<int> &gridPt);
    bool gridPointToDbPoint(const point_2d &gridPt, point_2d &dbPt);

   private:
    BoardGrid mBg;
    kicadPcbDataBase &mDb;

    // Layer mapping between DB and BoardGrid
    std::vector<std::string> mGridLayerToName;
    std::unordered_map<std::string, int> mLayerNameToGridLayer;
    std::unordered_map<int, int> mDbLayerIdToGridLayer;

    // GridNetclasses mapping to GridDiffPairNetclass
    std::map<std::pair<int, int>, int> mGridNetclassIdsToDiffPairOne;  // unordered_map doesn't support std::pair as a key

    // Global GridPins including the pins aren't connected by nets
    std::vector<GridPin> mGridPins;

    // Routing results from iterations
    std::vector<MultipinRoute> mGridNets;                       //Current routing structures to the board grid
    std::vector<MultipinRoute> bestSolution;                    //Keep the best routing solutions
    std::vector<std::vector<MultipinRoute> > routingSolutions;  //Keep the routing solutions of each iteration
    double bestTotalRouteCost = std::numeric_limits<double>::max();

    // Diff pairs
    std::vector<GridDiffPairNet> mGridDiffPairNets;

    // Board Boundary
    double mMinX = std::numeric_limits<double>::max();
    double mMaxX = std::numeric_limits<double>::min();
    double mMinY = std::numeric_limits<double>::max();
    double mMaxY = std::numeric_limits<double>::min();
};

#endif
