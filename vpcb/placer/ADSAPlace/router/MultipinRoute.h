#ifndef PCBROUTER_MULTI_PIN_ROUTE_H
#define PCBROUTER_MULTI_PIN_ROUTE_H

#include <vector>

#include "GridPath.h"
#include "GridPin.h"
#include "PostProcessing.h"
#include "globalParam_router.h"
#include "point.h"

class MultipinRoute {
   public:
    MultipinRoute() {
    }
    MultipinRoute(const int netId) {
        this->netId = netId;
    }
    MultipinRoute(const int netId, const int gridNetclassId) {
        this->netId = netId;
        this->gridNetclassId = gridNetclassId;
    }
    MultipinRoute(const int netId, const int gridNetclassId, const size_t numGridLayer) {
        this->netId = netId;
        this->gridNetclassId = gridNetclassId;
        this->mLayerCosts.resize(numGridLayer, 0);
    }

    void featuresToGridPaths();
    void gridPathLocationsToSegments();
    void gridPathSegmentsToLocations();
    void removeFirstGridPathRedudantLocations();
    void removeAcuteAngleBetweenGridPinsAndPaths(const double gridWireWidth);
    void setupGridPinsRoutingOrder();
    double getGridPinsDistance(const GridPin &gp1, const GridPin &gp2);

    int getGridNetclassId() const { return gridNetclassId; }
    int getNetId() const { return netId; }

    const std::vector<pr::prIntCost> &getLayerCosts() const { return mLayerCosts; }
    const std::vector<GridPath> &getGridPaths() const { return mGridPaths; }
    const std::vector<GridPin> &getGridPins() const { return mGridPins; }
    void clearGridPaths() { mGridPaths.clear(); }

    GridPath &getNewGridPath() {
        mGridPaths.push_back(GridPath{});
        return mGridPaths.back();
    }
    GridPin &getNewGridPin() {
        mGridPins.push_back(GridPin{});
        return mGridPins.back();
    }

    double getRoutedWirelength() const;
    int getRoutedNumVias() const;
    int getRoutedNumBends() const;
    double getCurTrackObstacleCost() const { return curTrackObstacleCost; }
    double getCurViaObstacleCost() const { return curViaObstacleCost; }
    double getCurNegTrackObstacleCost() const { return -curTrackObstacleCost; }
    double getCurNegViaObstacleCost() const { return -curViaObstacleCost; }

    int getPairNetId() const { return mPairNetId; }
    bool isDiffPair() const { return mPairNetId != -1; }

    void setPairNetId(const int _netId) { mPairNetId = _netId; }
    void setCurTrackObstacleCost(const double &toc) { curTrackObstacleCost = toc; }
    void setCurViaObstacleCost(const double &voc) { curViaObstacleCost = voc; }
    void addCurTrackObstacleCost(const double &stoc) { curTrackObstacleCost += stoc; }
    void addCurViaObstacleCost(const double &svoc) { curViaObstacleCost += svoc; }

    void setLayerCost(const int layerId, const pr::prIntCost cost) { mLayerCosts.at(layerId) = cost; }
    void setAllLayersCosts(const pr::prIntCost cost) { mLayerCosts.assign(mLayerCosts.size(), cost); }

    friend class BoardGrid;
    friend class MultipinRoute;
    friend class GridBasedRouter;

   private:
    int netId = -1;
    int gridNetclassId = -1;
    int mPairNetId = -1;
    int mGridDiffPairNetclassId = -1;
    float currentRouteCost = 0.0;
    std::vector<GridPin> mGridPins;
    std::vector<GridPath> mGridPaths;
    std::vector<pr::prIntCost> mLayerCosts;  //Layer preferences for this net, align with board grid layer
    std::vector<int> mGridPinsRoutingOrder;
    // std::vector<Location> vias; //TODO

    // deprecated, will clean up later
    /*[[deprecated]]*/ std::vector<Location> features;  // Make this obsolete, please

    // Cost along with this net
    double curTrackObstacleCost = 0.0;
    double curViaObstacleCost = 0.0;
};

#endif