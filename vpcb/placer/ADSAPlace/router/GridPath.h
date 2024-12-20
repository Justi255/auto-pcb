#ifndef PCBROUTER_GRID_PATH_H
#define PCBROUTER_GRID_PATH_H

#include <algorithm>
#include <list>
#include <vector>

#include "globalParam_router.h"
#include "point.h"

class GridPath {
   public:
    //ctor
    GridPath() {}
    //dtor
    ~GridPath() {}

    void addLocation(const Location &l) { mLocations.emplace_back(l); }
    std::list<Location> &setLocations() { return mLocations; }
    std::list<Location> &setSegments() { return mSegments; }

    const std::list<Location> &getSegments() const { return mSegments; }
    const std::list<Location> &getLocations() const { return mLocations; }

    void removeRedundantPoints();
    void copyLocationsToSegments() { mSegments = mLocations; }
    void transformSegmentsToLocations();
    void printLocations() const;
    void printSegments() const;

    double getRoutedWirelength() const;
    int getRoutedNumVias() const;
    int getRoutedNumBends() const;

    friend class BoardGrid;
    friend class MultipinRoute;

   private:
    std::list<Location> mLocations;
    std::list<Location> mSegments;
};

#endif