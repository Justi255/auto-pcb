//GridBasedRouter.cpp
#include "GridBasedRouter.h"

double GridBasedRouter::get_routed_wirelength() {
    return this->get_routed_wirelength(this->bestSolution);
}

double GridBasedRouter::get_routed_wirelength(std::vector<MultipinRoute> &mpr) {
    double overallRoutedWL = 0.0;
    for (const auto &mpn : mpr) {
        overallRoutedWL += mpn.getRoutedWirelength();
    }
    return overallRoutedWL;
}

int GridBasedRouter::get_routed_num_vias() {
    return this->get_routed_num_vias(this->bestSolution);
}

int GridBasedRouter::get_routed_num_vias(std::vector<MultipinRoute> &mpr) {
    int overallNumVias = 0;
    for (const auto &mpn : mpr) {
        overallNumVias += mpn.getRoutedNumVias();
    }
    return overallNumVias;
}

int GridBasedRouter::get_routed_num_bends() {
    return this->get_routed_num_bends(this->bestSolution);
}

int GridBasedRouter::get_routed_num_bends(std::vector<MultipinRoute> &mpr) {
    int overallNumBends = 0;
    for (const auto &mpn : mpr) {
        overallNumBends += mpn.getRoutedNumBends();
    }
    return overallNumBends;
}

// deprecated
bool GridBasedRouter::writeNetsFromGridPaths(std::vector<MultipinRoute> &multipinNets, std::ofstream &ofs) {
    if (!ofs)
        return false;

    // Set output precision
    ofs << std::fixed << std::setprecision(GlobalParam_router::gOutputPrecision);
    // Estimated total routed wirelength
    double totalEstWL = 0.0;
    double totalEstGridWL = 0.0;
    int totalNumVia = 0;

    //std::cout << "================= Start of " << __FUNCTION__ << "() =================" << std::endl;

    // Multipin net
    for (auto &mpNet : multipinNets) {
        if (!mDb.isNetId(mpNet.netId)) {
            std::cerr << __FUNCTION__ << "() Invalid net id: " << mpNet.netId << std::endl;
            continue;
        }

        auto &net = mDb.getNet(mpNet.netId);
        if (!mDb.isNetclassId(net.getNetclassId())) {
            std::cerr << __FUNCTION__ << "() Invalid netclass id: " << net.getNetclassId() << std::endl;
            continue;
        }

        // Convert from features to grid paths
        // if (mpNet.features.empty()) {
        //     continue;
        // }
        // mpNet.featuresToGridPaths();

        auto &netclass = mDb.getNetclass(net.getNetclassId());
        double netEstWL = 0.0;
        double netEstGridWL = 0.0;
        int netNumVia = 0;

        for (auto &gridPath : mpNet.mGridPaths) {
            Location prevLocation = gridPath.getSegments().front();

            for (auto &location : gridPath.getSegments()) {
                if (prevLocation == location) {
                    continue;
                }
                // Sanity Check
                if (location.m_z != prevLocation.m_z &&
                    location.m_y != prevLocation.m_y &&
                    location.m_x != prevLocation.m_x) {
                    std::cerr << __FUNCTION__ << "() Invalid path between location: " << location << ", and prevLocation: " << prevLocation << std::endl;
                    continue;
                }
                // Print Through Hole Via
                if (location.m_z != prevLocation.m_z) {
                    ++totalNumVia;
                    ++netNumVia;

                    ofs << "(via";
                    ofs << " (at " << GlobalParam_router::gridFactor * (prevLocation.m_x + mMinX * GlobalParam_router::inputScale - GlobalParam_router::enlargeBoundary / 2) << " " << GlobalParam_router::gridFactor * (prevLocation.m_y + mMinY * GlobalParam_router::inputScale - GlobalParam_router::enlargeBoundary / 2) << ")";
                    ofs << " (size " << netclass.getViaDia() << ")";
                    ofs << " (drill " << netclass.getViaDrill() << ")";
                    ofs << " (layers Top Bottom)";
                    ofs << " (net " << mpNet.netId << ")";
                    ofs << ")" << std::endl;
                }

                // Print Segment/Track/Wire
                if (location.m_x != prevLocation.m_x || location.m_y != prevLocation.m_y) {
                    point_2d start{GlobalParam_router::gridFactor * (prevLocation.m_x + mMinX * GlobalParam_router::inputScale - GlobalParam_router::enlargeBoundary / 2), GlobalParam_router::gridFactor * (prevLocation.m_y + mMinY * GlobalParam_router::inputScale - GlobalParam_router::enlargeBoundary / 2)};
                    point_2d end{GlobalParam_router::gridFactor * (location.m_x + mMinX * GlobalParam_router::inputScale - GlobalParam_router::enlargeBoundary / 2), GlobalParam_router::gridFactor * (location.m_y + mMinY * GlobalParam_router::inputScale - GlobalParam_router::enlargeBoundary / 2)};
                    totalEstWL += point_2d::getDistance(start, end);
                    totalEstGridWL += Location::getDistance2D(prevLocation, location);
                    netEstWL += point_2d::getDistance(start, end);
                    netEstGridWL += Location::getDistance2D(prevLocation, location);

                    ofs << "(segment";
                    ofs << " (start " << start.m_x << " " << start.m_y << ")";
                    ofs << " (end " << end.m_x << " " << end.m_y << ")";
                    ofs << " (width " << netclass.getTraceWidth() << ")";
                    ofs << " (layer " << mGridLayerToName.at(location.m_z) << ")";
                    ofs << " (net " << mpNet.netId << ")";
                    ofs << ")" << std::endl;
                }
                prevLocation = location;
            }
        }
        // std::cout << "\tNet " << net.getName() << "(" << net.getId() << "), netDegree: " << net.getPins().size()
        //           << ", Total WL: " << netEstWL << ", Total Grid WL: " << netEstGridWL << ", #Vias: " << netNumVia << ", currentRouteCost: " << mpNet.currentRouteCost << std::endl;
    }

    //std::cout << "\tEstimated Total WL: " << totalEstWL << ", Total Grid WL: " << totalEstGridWL << ", Total # Vias: " << totalNumVia << std::endl;
    //std::cout << "================= End of " << __FUNCTION__ << "() =================" << std::endl;
    return true;
}

void GridBasedRouter::writeSolutionBackToDbAndSaveOutput(const std::string fileNameTag, std::vector<MultipinRoute> &multipinNets) {
    // Estimated total routed wirelength
    double totalEstWL = 0.0;
    double totalEstGridWL = 0.0;
    int totalNumVia = 0;

    //std::cout << "================= Start of " << __FUNCTION__ << "() =================" << std::endl;

    // Multipin net
    for (auto &mpNet : multipinNets) {
        if (!mDb.isNetId(mpNet.netId)) {
            //std:cout << __FUNCTION__ << "() Invalid net id: " << mpNet.netId << std::endl;
            continue;
        }

        auto &net = mDb.getNet(mpNet.netId);
        if (!mDb.isNetclassId(net.getNetclassId())) {
            //std:cout << __FUNCTION__ << "() Invalid netclass id: " << net.getNetclassId() << std::endl;
            continue;
        }

        // Convert from features to grid paths
        // if (mpNet.features.empty()) {
        //     continue;
        // }
        // mpNet.featuresToGridPaths();

        // Clear current net's segments and vias
        net.clearSegments();
        net.clearVias();

        auto &netclass = mDb.getNetclass(net.getNetclassId());
        double netEstWL = 0.0;
        double netEstGridWL = 0.0;
        int netNumVia = 0;

        for (auto &gridPath : mpNet.mGridPaths) {
            Location prevLocation = gridPath.getSegments().front();

            for (auto &location : gridPath.getSegments()) {
                if (prevLocation == location) {
                    continue;
                }
                // Sanity Check
                if (location.m_z != prevLocation.m_z &&
                    location.m_y != prevLocation.m_y &&
                    location.m_x != prevLocation.m_x) {
                    std::cerr << __FUNCTION__ << "() Invalid path between location: " << location << ", and prevLocation: " << prevLocation << std::endl;
                    continue;
                }
                // Print Through Hole Via
                if (location.m_z != prevLocation.m_z) {
                    ++totalNumVia;
                    ++netNumVia;

                    if (GlobalParam_router::gUseMircoVia) {
                        if (GlobalParam_router::gOutputStackedMicroVias) {
                            int startGridLayerId = std::min(location.m_z, prevLocation.m_z);
                            int endGridLayerId = std::max(location.m_z, prevLocation.m_z);
                            for (int layerId = startGridLayerId; layerId + 1 <= endGridLayerId; ++layerId) {
                                Via via{net.getViaCount(), net.getId(), netclass.getMicroViaDia(), ViaType::MICRO};
                                point_2d dbPoint;
                                this->gridPointToDbPoint(point_2d{(double)location.x(), (double)location.y()}, dbPoint);
                                via.setPosition(dbPoint);
                                via.setDrillSize(netclass.getMicroViaDrill());
                                via.setLayer(std::vector<std::string>{this->mGridLayerToName.at(layerId), this->mGridLayerToName.at(layerId + 1)});

                                if (layerId == 0 || layerId + 1 == mDb.getNumCopperLayers() - 1) {
                                    // Micro via must have outter layer to inner layer
                                    via.setType(ViaType::MICRO);
                                } else {
                                    // Blind/Buried vias are between two inner layers
                                    via.setType(ViaType::BLIND_BURIED);
                                }
                                net.addVia(via);
                            }
                        } else {
                            Via via{net.getViaCount(), net.getId(), netclass.getMicroViaDia(), ViaType::MICRO};
                            point_2d dbPoint;
                            this->gridPointToDbPoint(point_2d{(double)location.x(), (double)location.y()}, dbPoint);
                            via.setPosition(dbPoint);

                            int startGridLayerId = std::min(location.m_z, prevLocation.m_z);
                            int endGridLayerId = std::max(location.m_z, prevLocation.m_z);
                            via.setLayer(std::vector<std::string>{this->mGridLayerToName.at(startGridLayerId), this->mGridLayerToName.at(endGridLayerId)});
                            net.addVia(via);
                        }
                    } else {
                        Via via{net.getViaCount(), net.getId(), netclass.getViaDia(), ViaType::THROUGH};
                        point_2d dbPoint;
                        this->gridPointToDbPoint(point_2d{(double)location.x(), (double)location.y()}, dbPoint);
                        via.setPosition(dbPoint);
                        via.setLayer(std::vector<std::string>{this->mGridLayerToName.front(), this->mGridLayerToName.back()});
                        net.addVia(via);
                    }
                }
                // Print Segment/Track/Wire
                if (location.m_x != prevLocation.m_x || location.m_y != prevLocation.m_y) {
                    point_2d start, end;
                    this->gridPointToDbPoint(point_2d{(double)prevLocation.x(), (double)prevLocation.y()}, start);
                    this->gridPointToDbPoint(point_2d{(double)location.x(), (double)location.y()}, end);
                    totalEstWL += point_2d::getDistance(start, end);
                    totalEstGridWL += Location::getDistance2D(prevLocation, location);
                    netEstWL += point_2d::getDistance(start, end);
                    netEstGridWL += Location::getDistance2D(prevLocation, location);

                    Segment segment{net.getSegmentCount(), net.getId(), netclass.getTraceWidth(), mGridLayerToName.at(location.m_z)};
                    points_2d pts;
                    pts.push_back(start);
                    pts.push_back(end);
                    segment.setPosition(pts);
                    net.addSegment(segment);
                }
                prevLocation = location;
            }
        }
        //std:cout << "\tNet " << net.getName() << "(" << net.getId() << "), netDegree: " << net.getPins().size()
                  //<< ", Total WL: " << netEstWL << ", Total Grid WL: " << netEstGridWL << ", #Vias: " << netNumVia << ", currentRouteCost: " << mpNet.currentRouteCost << std::endl;
    }

    //std:cout << "\tEstimated Total WL: " << totalEstWL << ", Total Grid WL: " << totalEstGridWL << ", Total # Vias: " << totalNumVia << std::endl;
    //std:cout << "================= End of " << __FUNCTION__ << "() =================" << std::endl;

    // Output the .kicad_pcb file
    std::string nameTag = fileNameTag;
    //std::string nameTag = "printKiCad";
    //nameTag = nameTag + "_s_" + std::to_string(GlobalParam_router::inputScale) + "_i_" + std::to_string(GlobalParam_router::gNumRipUpReRouteIteration) + "_b_" + std::to_string(GlobalParam_router::enlargeBoundary);
    mDb.printKiCad(GlobalParam_router::gOutputFolder, nameTag);
}

void GridBasedRouter::setupLayerMapping() {
    // Setup layer mappings
    for (auto &layerIte : mDb.getCopperLayers()) {
        //std:cout << "Grid layer Id: " << mGridLayerToName.size() << ", mapped to DB: " << layerIte.second << std::endl;
        mLayerNameToGridLayer[layerIte.second] = mGridLayerToName.size();
        mDbLayerIdToGridLayer[layerIte.first] = mGridLayerToName.size();
        mGridLayerToName.push_back(layerIte.second);
    }
}

void GridBasedRouter::setupGridDiffPairNetclass(const int netclassId1, const int netclassId2, int &gridDiffPairNetclassId) {
    const int ncId1 = min(netclassId1, netclassId2);
    const int ncId2 = max(netclassId1, netclassId2);


    const auto &gnc1 = mBg.getGridNetclass(ncId1);
    const auto &gnc2 = mBg.getGridNetclass(ncId2);

    auto it = mGridNetclassIdsToDiffPairOne.find(make_pair(ncId1, ncId2));
    if (it != mGridNetclassIdsToDiffPairOne.end()) {
        gridDiffPairNetclassId = it->second;
        return;
    }

    /*
    // Store in mBg.mGridDiffPairNetclass
    int id = mGridNetclassIdsToDiffPairOne.size();
    gridDiffPairNetclassId = id;
    this->mGridNetclassIdsToDiffPairOne.emplace(make_pair(ncId1, ncId2), id);
    */
    // Store in mBg.mGridNetclass
    int id = mBg.getGridNetclasses().size();
    gridDiffPairNetclassId = id;
    this->mGridNetclassIdsToDiffPairOne.emplace(make_pair(ncId1, ncId2), id);

    int clearance = max(gnc1.getClearance(), gnc2.getClearance());
    int traceWidth = gnc1.getTraceWidth() + clearance + gnc2.getTraceWidth();
    int viaDia = gnc1.getViaDia() + clearance + gnc2.getViaDia();
    int viaDrill = gnc1.getViaDrill() + clearance + gnc2.getViaDrill();
    int microViaDia = gnc1.getMicroViaDia() + clearance + gnc2.getMicroViaDia();
    int microViaDrill = gnc1.getMicroViaDrill() + clearance + gnc2.getMicroViaDrill();

    GridDiffPairNetclass gridDiffPairNetclass{id, clearance, traceWidth, viaDia, viaDrill, microViaDia, microViaDrill, ncId1, ncId2};

    // Setup derived values
    gridDiffPairNetclass.setHalfTraceWidth((int)floor((double)traceWidth / 2.0));
    gridDiffPairNetclass.setHalfViaDia((int)floor((double)viaDia / 2.0));
    gridDiffPairNetclass.setHalfMicroViaDia((int)floor((double)microViaDia / 2.0));
    // Diagnoal cases // Watch out the conservative values over here if need more spaces for routing
    int diagonalTraceWidth = (int)ceil(traceWidth / sqrt(2));
    gridDiffPairNetclass.setDiagonalTraceWidth(diagonalTraceWidth);
    gridDiffPairNetclass.setHalfDiagonalTraceWidth((int)floor((double)diagonalTraceWidth / 2.0));
    int diagonalClearance = (int)ceil(clearance / sqrt(2));
    gridDiffPairNetclass.setDiagonalClearance(diagonalClearance);

    gridDiffPairNetclass.setViaExpansion(gridDiffPairNetclass.getHalfViaDia());
    gridDiffPairNetclass.setTraceExpansion(gridDiffPairNetclass.getHalfTraceWidth());
    gridDiffPairNetclass.setDiagonalTraceExpansion(gridDiffPairNetclass.getHalfDiagonalTraceWidth());
    GridNetclass::setObstacleExpansion(0);
    if (GlobalParam_router::gUseMircoVia) {
        gridDiffPairNetclass.setViaExpansion(gridDiffPairNetclass.getHalfMicroViaDia());
    }

    // Update Trace-end shape grids and Calculate the trace-end shape grids
    int halfTraceWidth = gridDiffPairNetclass.getHalfTraceWidth();
    std::vector<Point_2D<int>> traceEndGrids;
    getRasterizedCircle(halfTraceWidth, (double)halfTraceWidth, traceEndGrids);
    gridDiffPairNetclass.setTraceEndShapeGrids(traceEndGrids);

    // Update trace searching grids and Calculate the trace searching grid
    int traceSearchRadius = gridDiffPairNetclass.getHalfTraceWidth() + gridDiffPairNetclass.getClearance();
    std::vector<Point_2D<int>> traceSearchingGrids;
    getRasterizedCircle(traceSearchRadius, (double)traceSearchRadius, traceSearchingGrids);
    gridDiffPairNetclass.setTraceSearchingSpaceToGrids(traceSearchingGrids);

    // Update Via shape grids
    int halfViaDia = (int)floor((double)viaDia / 2.0);
    if (GlobalParam_router::gUseMircoVia) {
        halfViaDia = (int)floor((double)microViaDia / 2.0);
    }
    std::vector<Point_2D<int>> viaGrids;
    getRasterizedCircle(halfViaDia, (double)halfViaDia, viaGrids);
    gridDiffPairNetclass.setViaShapeGrids(viaGrids);

    // Update via searching grids
    int viaSearchRadius = gridDiffPairNetclass.getHalfViaDia() + gridDiffPairNetclass.getClearance();
    if (GlobalParam_router::gUseMircoVia) {
        viaSearchRadius = gridDiffPairNetclass.getHalfMicroViaDia() + gridDiffPairNetclass.getClearance();
    }
    std::vector<Point_2D<int>> viaSearchingGrids;
    // Watch out the case of via size < trace size
    if (viaSearchRadius < traceSearchRadius) {
        // Use trace searching grids instead
        gridDiffPairNetclass.setViaSearchingSpaceToGrids(traceSearchingGrids);
    } else {
        // Calculate the via searching grid
        getRasterizedCircle(viaSearchRadius, (double)viaSearchRadius, viaSearchingGrids);
        gridDiffPairNetclass.setViaSearchingSpaceToGrids(viaSearchingGrids);
    }

    // Setup incremental searching grids
    gridDiffPairNetclass.setupTraceIncrementalSearchGrids();
    gridDiffPairNetclass.setupViaIncrementalSearchGrids();

    if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG) {
        //std:cout << __FUNCTION__ << "(): Create new diff pair netclass..." << std::endl;
        //std:cout << "==============Base netclass 1: id: " << gnc1.getId() << "==============" << std::endl;
        //std:cout << "clearance: " << gnc1.getClearance() << ", traceWidth: " << gnc1.getTraceWidth() << std::endl;
        //std:cout << "viaDia: " << gnc1.getViaDia() << ", viaDrill: " << gnc1.getViaDrill() << std::endl;
        //std:cout << "microViaDia: " << gnc1.getMicroViaDia() << ", microViaDrill: " << gnc1.getMicroViaDrill() << std::endl;
        //std:cout << "==============Base netclass 2: id: " << gnc2.getId() << "==============" << std::endl;
        //std:cout << "clearance: " << gnc2.getClearance() << ", traceWidth: " << gnc2.getTraceWidth() << std::endl;
        //std:cout << "viaDia: " << gnc2.getViaDia() << ", viaDrill: " << gnc2.getViaDrill() << std::endl;
        //std:cout << "microViaDia: " << gnc2.getMicroViaDia() << ", microViaDrill: " << gnc2.getMicroViaDrill() << std::endl;
        //std:cout << "==============Grid netclass: id: " << id << "==============" << std::endl;
        //std:cout << "clearance: " << gridDiffPairNetclass.getClearance() << ", diagonal clearance: " << gridDiffPairNetclass.getDiagonalClearance() << std::endl;
        //std:cout << "traceWidth: " << gridDiffPairNetclass.getTraceWidth() << ", half traceWidth: " << gridDiffPairNetclass.getHalfTraceWidth() << std::endl;
        //std:cout << "diagonal traceWidth: " << gridDiffPairNetclass.getDiagonalTraceWidth() << ", half diagonal traceWidth: " << gridDiffPairNetclass.getHalfDiagonalTraceWidth() << std::endl;
        //std:cout << "viaDia: " << gridDiffPairNetclass.getViaDia() << ", halfViaDia: " << gridDiffPairNetclass.getHalfViaDia() << ", viaDrill: " << gridDiffPairNetclass.getViaDrill() << std::endl;
        //std:cout << "microViaDia: " << gridDiffPairNetclass.getMicroViaDia() << ", microViaDrill: " << gridDiffPairNetclass.getMicroViaDrill() << std::endl;
        //std:cout << "==============Grid netclass: id: " << id << ", Expansions==============" << std::endl;
        //std:cout << "viaExpansion: " << gridDiffPairNetclass.getViaExpansion() << std::endl;
        //std:cout << "traceExpansion: " << gridDiffPairNetclass.getTraceExpansion() << std::endl;
        //std:cout << "DiagonalTraceExpansion: " << gridDiffPairNetclass.getDiagonalTraceExpansion() << std::endl;
        //std:cout << "(static)obstacleExpansion: " << GridNetclass::getObstacleExpansion() << std::endl;
    }

    // Put the netclass into class vectors
    mBg.addGridNetclass(static_cast<GridNetclass>(gridDiffPairNetclass));
    // mBg.addGridDiffPairNetclass(gridDiffPairNetclass);
}

void GridBasedRouter::setupGridNetclass() {
    for (auto &netclassIte : mDb.getNetclasses()) {
        int id = netclassIte.getId();
        int clearance = dbLengthToGridLengthCeil(netclassIte.getClearance());
        int traceWidth = dbLengthToGridLengthCeil(netclassIte.getTraceWidth());
        int viaDia = dbLengthToGridLengthCeil(netclassIte.getViaDia());
        int viaDrill = dbLengthToGridLengthCeil(netclassIte.getViaDrill());
        int microViaDia = dbLengthToGridLengthCeil(netclassIte.getMicroViaDia());
        int microViaDrill = dbLengthToGridLengthCeil(netclassIte.getMicroViaDrill());

        GridNetclass gridNetclass{id, clearance, traceWidth, viaDia, viaDrill, microViaDia, microViaDrill};

        // Setup derived values
        gridNetclass.setHalfTraceWidth((int)floor((double)traceWidth / 2.0));
        gridNetclass.setHalfViaDia((int)floor((double)viaDia / 2.0));
        gridNetclass.setHalfMicroViaDia((int)floor((double)microViaDia / 2.0));

        // Diagnoal cases
        int diagonalTraceWidth = (int)ceil(dbLengthToGridLength(netclassIte.getTraceWidth()) / sqrt(2));
        gridNetclass.setDiagonalTraceWidth(diagonalTraceWidth);
        gridNetclass.setHalfDiagonalTraceWidth((int)floor((double)diagonalTraceWidth / 2.0));
        int diagonalClearance = (int)ceil(dbLengthToGridLength(netclassIte.getClearance()) / sqrt(2));
        gridNetclass.setDiagonalClearance(diagonalClearance);

        // !!! Move below expanding functions to a new function, to handle multiple netclasses

        // Setup expansion values (for obstacles on the grids)
        gridNetclass.setViaExpansion(gridNetclass.getHalfViaDia());
        gridNetclass.setTraceExpansion(gridNetclass.getHalfTraceWidth());
        gridNetclass.setDiagonalTraceExpansion(gridNetclass.getHalfDiagonalTraceWidth());
        GridNetclass::setObstacleExpansion(0);
        // Expanded cases
        // gridNetclass.setViaExpansion(gridNetclass.getHalfViaDia() + gridNetclass.getClearance());
        // gridNetclass.setTraceExpansion(gridNetclass.getHalfTraceWidth() + gridNetclass.getClearance());
        // gridNetclass.setDiagonalTraceExpansion(gridNetclass.getHalfDiagonalTraceWidth() + gridNetclass.getDiagonalClearance());
        // GridNetclass::setObstacleExpansion(gridNetclass.getClearance());
        if (GlobalParam_router::gUseMircoVia) {
            gridNetclass.setViaExpansion(gridNetclass.getHalfMicroViaDia());
        }

        // Update Trace-end shape grids
        double traceWidthFloating = dbLengthToGridLength(netclassIte.getTraceWidth());
        int halfTraceWidth = gridNetclass.getHalfTraceWidth();
        double halfTraceWidthFloating = traceWidthFloating / 2.0;
        // WARNING!! Expanded cases // Not updated yet!!
        // double viaDiaFloating = dbLengthToGridLength(netclassIte.getViaDia());
        // int halfViaDia = gridNetclass.getViaExpansion();
        // double halfViaDiaFloating = viaDiaFloating / 2.0 + dbLengthToGridLength(netclassIte.getClearance());

        // Calculate the trace-end shape grids
        std::vector<Point_2D<int>> traceEndGrids;
        getRasterizedCircle(halfTraceWidth, halfTraceWidthFloating, traceEndGrids);
        gridNetclass.setTraceEndShapeGrids(traceEndGrids);

        // Update trace searching grids
        std::vector<Point_2D<int>> traceSearchingGrids;
        int traceSearchRadius = gridNetclass.getHalfTraceWidth() + gridNetclass.getClearance();
        double traceSearchRadiusFloating = dbLengthToGridLength(netclassIte.getTraceWidth()) / 2.0 + dbLengthToGridLength(netclassIte.getClearance());
        //std:cout << "traceSearchRadius: " << traceSearchRadius << ", traceSearchRadiusFloating: " << traceSearchRadiusFloating << std::endl;
        // Expanded cases
        // int traceSearchRadius = gridNetclass.getHalfTraceWidth();
        // double traceSearchRadiusFloating = dbLengthToGridLength(netclassIte.getTraceWidth()) / 2.0;

        // Calculate the trace searching grid
        getRasterizedCircle(traceSearchRadius, traceSearchRadiusFloating, traceSearchingGrids);
        gridNetclass.setTraceSearchingSpaceToGrids(traceSearchingGrids);
        // Debugging
        //std:cout << "Relative trace searching grids points: " << std::endl;
        for (auto &pt : gridNetclass.getTraceSearchingSpaceToGrids()) {
            //std:cout << pt << std::endl;
        }

        // Update Via shape grids
        double viaDiaFloating = dbLengthToGridLength(netclassIte.getViaDia());
        int halfViaDia = (int)floor((double)viaDia / 2.0);
        double halfViaDiaFloating = viaDiaFloating / 2.0;
        // Expanded cases
        // double viaDiaFloating = dbLengthToGridLength(netclassIte.getViaDia());
        // int halfViaDia = gridNetclass.getViaExpansion();
        // double halfViaDiaFloating = viaDiaFloating / 2.0 + dbLengthToGridLength(netclassIte.getClearance());
        if (GlobalParam_router::gUseMircoVia) {
            viaDiaFloating = dbLengthToGridLength(netclassIte.getMicroViaDia());
            halfViaDia = (int)floor((double)microViaDia / 2.0);
            halfViaDiaFloating = viaDiaFloating / 2.0;
        }

        std::vector<Point_2D<int>> viaGrids;
        getRasterizedCircle(halfViaDia, halfViaDiaFloating, viaGrids);
        gridNetclass.setViaShapeGrids(viaGrids);

        // Update via searching grids
        std::vector<Point_2D<int>> viaSearchingGrids;
        int viaSearchRadius = gridNetclass.getHalfViaDia() + gridNetclass.getClearance();
        double viaSearchRadiusFloating = halfViaDiaFloating + dbLengthToGridLength(netclassIte.getClearance());
        // Expanded cases
        // int viaSearchRadius = gridNetclass.getHalfViaDia();
        // double viaSearchRadiusFloating = halfViaDiaFloating;
        if (GlobalParam_router::gUseMircoVia) {
            viaSearchRadius = gridNetclass.getHalfMicroViaDia() + gridNetclass.getClearance();
            viaSearchRadiusFloating = halfViaDiaFloating + dbLengthToGridLength(netclassIte.getClearance());
        }

        // Watch out the case of via size < trace size
        // //std:cout << "viaSearchRadius: " << viaSearchRadius << ", viaSearchRadiusFloating: " << viaSearchRadiusFloating << std::endl;
        // //std:cout << "traceSearchRadius: " << traceSearchRadius << ", traceSearchRadiusFloating: " << traceSearchRadiusFloating << std::endl;
        if (viaSearchRadiusFloating < traceSearchRadiusFloating) {
            // Use trace searching grids instead
            gridNetclass.setViaSearchingSpaceToGrids(traceSearchingGrids);
        } else {
            // Calculate the via searching grid
            getRasterizedCircle(viaSearchRadius, viaSearchRadiusFloating, viaSearchingGrids);
            gridNetclass.setViaSearchingSpaceToGrids(viaSearchingGrids);

            // Debugging
            //std:cout << "viaSearchRadius: " << viaSearchRadius << ", viaSearchRadiusFloating: " << viaSearchRadiusFloating << std::endl;
            //std:cout << "Relative via searching grids points: " << std::endl;
            for (auto &pt : gridNetclass.getViaSearchingSpaceToGrids()) {
                //std:cout << pt << std::endl;
            }
        }

        // Setup incremental searching grids
        gridNetclass.setupTraceIncrementalSearchGrids();
        gridNetclass.setupViaIncrementalSearchGrids();
        // Put the netclass into class vectors
        mBg.addGridNetclass(gridNetclass);

        //std:cout << "==============DB netclass: id: " << netclassIte.getId() << "==============" << std::endl;
        //std:cout << "clearance: " << netclassIte.getClearance() << ", traceWidth: " << netclassIte.getTraceWidth() << std::endl;
        //std:cout << "viaDia: " << netclassIte.getViaDia() << ", viaDrill: " << netclassIte.getViaDrill() << std::endl;
        //std:cout << "microViaDia: " << netclassIte.getMicroViaDia() << ", microViaDrill: " << netclassIte.getMicroViaDrill() << std::endl;
        //std:cout << "==============Grid netclass: id: " << id << "==============" << std::endl;
        //std:cout << "clearance: " << gridNetclass.getClearance() << ", diagonal clearance: " << gridNetclass.getDiagonalClearance() << std::endl;
        //std:cout << "traceWidth: " << gridNetclass.getTraceWidth() << ", half traceWidth: " << gridNetclass.getHalfTraceWidth() << std::endl;
        //std:cout << "diagonal traceWidth: " << gridNetclass.getDiagonalTraceWidth() << ", half diagonal traceWidth: " << gridNetclass.getHalfDiagonalTraceWidth() << std::endl;
        //std:cout << "viaDia: " << gridNetclass.getViaDia() << ", halfViaDia: " << gridNetclass.getHalfViaDia() << ", viaDrill: " << gridNetclass.getViaDrill() << std::endl;
        //std:cout << "microViaDia: " << gridNetclass.getMicroViaDia() << ", microViaDrill: " << gridNetclass.getMicroViaDrill() << std::endl;
        //std:cout << "==============Grid netclass: id: " << id << ", Expansions==============" << std::endl;
        //std:cout << "viaExpansion: " << gridNetclass.getViaExpansion() << std::endl;
        //std:cout << "traceExpansion: " << gridNetclass.getTraceExpansion() << std::endl;
        //std:cout << "DiagonalTraceExpansion: " << gridNetclass.getDiagonalTraceExpansion() << std::endl;
        //std:cout << "(static)obstacleExpansion: " << GridNetclass::getObstacleExpansion() << std::endl;
    }
}

void GridBasedRouter::setupBoardGrid() {
    //std:cout << "\n\n######Start of " << __FUNCTION__ << "()" << std::endl;
    // Get board dimension
    //mDb.getBoardBoundaryByPinLocation(this->mMinX, this->mMaxX, this->mMinY, this->mMaxY);
    mDb.getBoardBoundaryByEdgeCuts(this->mMinX, this->mMaxX, this->mMinY, this->mMaxY);
    //std:cout << "Routing Outline: (" << this->mMinX << ", " << this->mMinY << "), (" << this->mMaxX << ", " << this->mMaxY << ")" << std::endl;
    //std:cout << "GlobalParam_router::inputScale: " << GlobalParam_router::inputScale << ", GlobalParam_router::enlargeBoundary: " << GlobalParam_router::enlargeBoundary << ", GlobalParam_router::gridFactor: " << GlobalParam_router::gridFactor << std::endl;

    // Get grid dimension
    const unsigned int h = int(std::abs(mMaxY * GlobalParam_router::inputScale - mMinY * GlobalParam_router::inputScale)) + GlobalParam_router::enlargeBoundary;
    const unsigned int w = int(std::abs(mMaxX * GlobalParam_router::inputScale - mMinX * GlobalParam_router::inputScale)) + GlobalParam_router::enlargeBoundary;
    const unsigned int l = mDb.getNumCopperLayers();
    //std:cout << "BoardGrid Size: w:" << w << ", h:" << h << ", l:" << l << std::endl;

    // Initialize board grid
    mBg.initilization(w, h, l);

    //std:cout << "######End of " << __FUNCTION__ << "()\n\n";
}

void GridBasedRouter::getRasterizedCircle(const int radius, const double radiusFloating, std::vector<Point_2D<int>> &grids) {
    // Center grid
    grids.push_back(Point_2D<int>{0, 0});
    if (radius == 0) {
        return;
    }
    // The rests
    for (int x = -radius; x <= radius; ++x) {
        for (int y = -radius; y <= radius; ++y) {
            if (x == 0 && y == 0) continue;

            // Check if any corner of grid is within the halfViaDiaFloating
            Point_2D<double> LL{(double)x - 0.5, (double)y - 0.5};
            Point_2D<double> LR{(double)x + 0.5, (double)y - 0.5};
            Point_2D<double> UL{(double)x - 0.5, (double)y + 0.5};
            Point_2D<double> UR{(double)x + 0.5, (double)y + 0.5};
            Point_2D<double> L{(double)x - 0.5, (double)y};
            Point_2D<double> R{(double)x + 0.5, (double)y};
            Point_2D<double> T{(double)x, (double)y + 0.5};
            Point_2D<double> B{(double)x, (double)y - 0.5};
            Point_2D<double> center{0.0, 0.0};

            if (Point_2D<double>::getDistance(LL, center) < radiusFloating ||
                Point_2D<double>::getDistance(LR, center) < radiusFloating ||
                Point_2D<double>::getDistance(UL, center) < radiusFloating ||
                Point_2D<double>::getDistance(UR, center) < radiusFloating ||
                Point_2D<double>::getDistance(L, center) < radiusFloating ||
                Point_2D<double>::getDistance(R, center) < radiusFloating ||
                Point_2D<double>::getDistance(T, center) < radiusFloating ||
                Point_2D<double>::getDistance(B, center) < radiusFloating) {
                grids.push_back(Point_2D<int>{x, y});
            }
        }
    }
}

void GridBasedRouter::setupGridNetsAndGridPins() {
    if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG) {
        //std:cout << "Starting " << __FUNCTION__ << "()..." << std::endl;
    }

    // Iterate nets
    for (auto &net : mDb.getNets()) {
        if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG) {
            //std:cout << "\nNet: " << net.getName() << ", netId: " << net.getId() << ", netDegree: " << net.getPins().size() << "..." << std::endl;
        }

        mGridNets.push_back(MultipinRoute{net.getId(), net.getNetclassId(), mDb.getCopperLayers().size()});
        auto &gridRoute = mGridNets.back();
        auto &pins = net.getPins();
        double polygonExpansion = 0.0;
        int boxContraction = 0;
        int pseudoPinExpansion = 0;
        if (mDb.isNetclassId(net.getNetclassId())) {
            auto &dbNetclass = mDb.getNetclass(net.getNetclassId());
            // polygonExpansion = dbNetclass.getClearance() + dbNetclass.getTraceWidth() / 2.0;
            // boxContraction = dbLengthToGridLengthCeil(dbNetclass.getTraceWidth() / 2.0);
            boxContraction = 1 + (int)floor((double)dbLengthToGridLengthCeil(dbNetclass.getTraceWidth()) / 2.0);  //Notes the +1 here is needed
            polygonExpansion = dbNetclass.getClearance();
            // pseudoPinExpansion = dbLengthToGridLengthCeil(dbNetclass.getClearance());
            pseudoPinExpansion = dbLengthToGridLengthCeil(dbNetclass.getClearance() + dbNetclass.getTraceWidth() / 2.0);
            pseudoPinExpansion = min(pseudoPinExpansion, dbLengthToGridLengthCeil(dbNetclass.getClearance()) + (int)floor((double)dbLengthToGridLengthCeil(dbNetclass.getTraceWidth()) / 2.0));
            // boxContraction = 0;
        }

        for (auto &pin : pins) {
            // TODO: Id Range Checking?
            // DB elements
            auto &comp = mDb.getComponent(pin.getCompId());
            auto &inst = mDb.getInstance(pin.getInstId());
            auto &pad = comp.getPadstack(pin.getPadstackId());
            // Router grid element
            auto &gridPin = gridRoute.getNewGridPin();
            // Setup the GridPin
            this->setupGridPin(pad, inst, gridPin);
            // this->setupGridPinPseudoPins(pad, inst, pseudoPinExpansion, gridPin);
            this->setupGridPinPolygonAndExpandedPolygon(pad, inst, polygonExpansion, gridPin);
            this->setupGridPinContractedBox(pad, inst, boxContraction, gridPin);
        }

        gridRoute.setupGridPinsRoutingOrder();
    }

    // Iterate instances
    auto &instances = mDb.getInstances();
    for (auto &inst : instances) {
        if (!mDb.isComponentId(inst.getComponentId())) {
            std::cerr << __FUNCTION__ << "(): Illegal component Id: " << inst.getComponentId() << ", from Instance: " << inst.getName() << std::endl;
            continue;
        }

        auto &comp = mDb.getComponent(inst.getComponentId());
        for (auto &pad : comp.getPadstacks()) {
            // Router grid element
            mGridPins.push_back(GridPin{});
            auto &gridPin = mGridPins.back();
            // Setup the GridPin
            this->setupGridPin(pad, inst, gridPin);
        }
    }

    //std:cout << "End of " << __FUNCTION__ << "()..." << std::endl;
}

void GridBasedRouter::setupGridPin(const padstack &pad, const instance &inst, GridPin &gridPin) {
    setupGridPin(pad, inst, GridNetclass::getObstacleExpansion(), gridPin);
}

void GridBasedRouter::setupGridPinPolygonAndExpandedPolygon(const padstack &pad, const instance &inst, const double polygonExpansion, GridPin &gridPin) {
    // Handle GridPin's pinPolygon, which should be expanded by clearance
    Point_2D<double> polyPadSize = pad.getSize();
    Point_2D<double> expandedPolyPadSize = pad.getSize();
    expandedPolyPadSize.m_x += 2.0 * polygonExpansion;
    expandedPolyPadSize.m_y += 2.0 * polygonExpansion;
    Point_2D<double> pinDbLocation;
    mDb.getPinPosition(pad, inst, &pinDbLocation);

    // //std:cout << "pinDbLocation: " << pinDbLocation << ", padSize: " << polyPadSize << std::endl;

    // Get a exact locations expanded polygon in db's coordinates
    std::vector<Point_2D<double>> exactDbLocExpandedPadPoly;
    std::vector<Point_2D<double>> exactDbLocPadPoly;
    if (pad.getPadShape() == padShape::CIRCLE || pad.getPadShape() == padShape::OVAL) {
        // WARNING!! shape_to_coords's pos can be origin only!!! Otherwise the rotate function will be wrong
        exactDbLocExpandedPadPoly = shape_to_coords(expandedPolyPadSize, point_2d{0, 0}, padShape::CIRCLE, inst.getAngle(), pad.getAngle(), pad.getRoundRectRatio(), 32);
        exactDbLocPadPoly = shape_to_coords(polyPadSize, point_2d{0, 0}, padShape::CIRCLE, inst.getAngle(), pad.getAngle(), pad.getRoundRectRatio(), 32);
    } else {
        exactDbLocExpandedPadPoly = shape_to_coords(expandedPolyPadSize, point_2d{0, 0}, padShape::RECT, inst.getAngle(), pad.getAngle(), pad.getRoundRectRatio(), 32);
        exactDbLocPadPoly = shape_to_coords(polyPadSize, point_2d{0, 0}, padShape::RECT, inst.getAngle(), pad.getAngle(), pad.getRoundRectRatio(), 32);
    }

    // Shift to exact location
    for (auto &&pt : exactDbLocExpandedPadPoly) {
        pt.m_x += pinDbLocation.m_x;
        pt.m_y += pinDbLocation.m_y;
    }
    for (auto &&pt : exactDbLocPadPoly) {
        pt.m_x += pinDbLocation.m_x;
        pt.m_y += pinDbLocation.m_y;
    }

    // Transform this into Boost's polygon in router's grid coordinates
    polygon_double_t exactLocGridPadShapePoly;
    for (const auto &pt : exactDbLocPadPoly) {
        Point_2D<double> pinGridPt;
        dbPointToGridPoint(pt, pinGridPt);
        // //std:cout << " db's pt: " << pt << ", grid's pt: " << pinGridPt << std::endl;
        bg::append(exactLocGridPadShapePoly.outer(), point_double_t(pinGridPt.x(), pinGridPt.y()));
    }
    bg::correct(exactLocGridPadShapePoly);
    gridPin.setPinPolygon(exactLocGridPadShapePoly);

    polygon_double_t exactLocGridPadExpandedShapePoly;
    for (const auto &pt : exactDbLocExpandedPadPoly) {
        Point_2D<double> pinGridPt;
        dbPointToGridPoint(pt, pinGridPt);
        // //std:cout << " db's pt: " << pt << ", grid's pt: " << pinGridPt << std::endl;
        bg::append(exactLocGridPadExpandedShapePoly.outer(), point_double_t(pinGridPt.x(), pinGridPt.y()));
    }
    bg::correct(exactLocGridPadExpandedShapePoly);
    gridPin.setExpandedPinPolygon(exactLocGridPadExpandedShapePoly);

    // get the bounding box
    box_double_t box;
    bg::envelope(exactLocGridPadExpandedShapePoly, box);
    gridPin.setExpandedPinLL(Point_2D<int>(round(bg::get<bg::min_corner, 0>(box)), round(bg::get<bg::min_corner, 1>(box))));
    gridPin.setExpandedPinUR(Point_2D<int>(round(bg::get<bg::max_corner, 0>(box)), round(bg::get<bg::max_corner, 1>(box))));
}

void GridBasedRouter::setupGridPinContractedBox(const padstack &pad, const instance &inst, const int gridContraction, GridPin &gridPin) {
    // Setup GridPin's location with layers
    Point_2D<double> pinDbLocation;
    mDb.getPinPosition(pad, inst, &pinDbLocation);
    Point_2D<int> pinGridLocation;
    dbPointToGridPointRound(pinDbLocation, pinGridLocation);

    // Setup GridPin's LL,UR boundary
    double width = 0, height = 0;
    mDb.getPadstackRotatedWidthAndHeight(inst, pad, width, height);
    Point_2D<double> pinDbUR{pinDbLocation.m_x + width / 2.0, pinDbLocation.m_y + height / 2.0};
    Point_2D<double> pinDbLL{pinDbLocation.m_x - width / 2.0, pinDbLocation.m_y - height / 2.0};
    Point_2D<int> pinGridLL, pinGridUR;
    dbPointToGridPointRound(pinDbUR, pinGridUR);
    dbPointToGridPointRound(pinDbLL, pinGridLL);
    pinGridUR.m_x -= gridContraction;
    pinGridUR.m_y -= gridContraction;
    pinGridLL.m_x += gridContraction;
    pinGridLL.m_y += gridContraction;
    gridPin.setContractedPinLL(pinGridLL);
    gridPin.setContractedPinUR(pinGridUR);
}

void GridBasedRouter::setupGridPinPseudoPins(const padstack &pad, const instance &inst, const int gridExpansion, GridPin &gridPin) {
    if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
        //std:cout << __FUNCTION__ << "(): Starting..." << std::endl;

    if (gridPin.getPinShape() == GridPin::PinShape::CIRCLE) {
        return;
    }

    // Setup GridPin's location with layers
    Point_2D<double> pinDbLocation;
    mDb.getPinPosition(pad, inst, &pinDbLocation);
    Point_2D<int> pinGridLocation;
    dbPointToGridPointRound(pinDbLocation, pinGridLocation);
    std::vector<int> layers;
    this->getGridLayers(pad, inst, layers);

    // Setup GridPin's LL,UR boundary
    double width = 0, height = 0;
    mDb.getPadstackRotatedWidthAndHeight(inst, pad, width, height);
    Point_2D<double> pinDbUR{pinDbLocation.m_x + width / 2.0, pinDbLocation.m_y + height / 2.0};
    Point_2D<double> pinDbLL{pinDbLocation.m_x - width / 2.0, pinDbLocation.m_y - height / 2.0};
    Point_2D<int> pinGridLL, pinGridUR;
    dbPointToGridPointRound(pinDbUR, pinGridUR);
    dbPointToGridPointRound(pinDbLL, pinGridLL);

    if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
        //std:cout << "PinGridLL: " << pinGridLL << ", PinGridUR: " << pinGridUR << std::endl;

    // Handle Pseudo Pins
    gridPin.pinWithLayers.clear();
    vector<Point_2D<int>> pseudoPins;
    pseudoPins.emplace_back(pinGridLL.x() - gridExpansion, pinGridLocation.y());            //L
    pseudoPins.emplace_back(pinGridUR.x() + gridExpansion, pinGridLocation.y());            //R
    pseudoPins.emplace_back(pinGridLocation.x(), pinGridUR.y() + gridExpansion);            //U
    pseudoPins.emplace_back(pinGridLocation.x(), pinGridLL.y() - gridExpansion);            //Lower
    pseudoPins.emplace_back(pinGridLL.x() - gridExpansion, pinGridLL.y() - gridExpansion);  //LL
    pseudoPins.emplace_back(pinGridUR.x() + gridExpansion, pinGridLL.y() - gridExpansion);  //LR
    pseudoPins.emplace_back(pinGridUR.x() + gridExpansion, pinGridUR.y() + gridExpansion);  //UR
    pseudoPins.emplace_back(pinGridLL.x() - gridExpansion, pinGridUR.y() + gridExpansion);  //UL

    if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
        //std:cout << " location in grid: " << pinGridLocation << ", original db abs. loc. : " << pinDbLocation.m_x << " " << pinDbLocation.m_y << ", layers:";

    for (const auto &pt : pseudoPins) {
        for (auto layer : layers) {
            gridPin.pinWithLayers.push_back(Location(pt.m_x, pt.m_y, layer));

            //if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
                //std:cout << " " << layer;
        }
    }

    //if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
        //std:cout << ", #layers:" << gridPin.pinWithLayers.size() << " " << layers.size() << std::endl;
}

void GridBasedRouter::setupGridPin(const padstack &pad, const instance &inst, const int gridExpansion, GridPin &gridPin) {
    // set grid pin shape
    if (pad.getPadShape() == padShape::RECT) {
        gridPin.setPinShape(GridPin::PinShape::RECT);
    } else if (pad.getPadShape() == padShape::ROUNDRECT) {
        gridPin.setPinShape(GridPin::PinShape::RECT);
    } else if (pad.getPadShape() == padShape::OVAL) {
        gridPin.setPinShape(GridPin::PinShape::CIRCLE);
    } else if (pad.getPadShape() == padShape::CIRCLE) {
        gridPin.setPinShape(GridPin::PinShape::CIRCLE);
    } else if (pad.getPadShape() == padShape::TRAPEZOID) {
        gridPin.setPinShape(GridPin::PinShape::RECT);
    }

    // Setup GridPin's location with layers
    Point_2D<double> pinDbLocation;
    mDb.getPinPosition(pad, inst, &pinDbLocation);
    Point_2D<int> pinGridLocation;
    dbPointToGridPointRound(pinDbLocation, pinGridLocation);
    std::vector<int> layers;
    this->getGridLayers(pad, inst, layers);

    //if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
        //std:cout << " location in grid: " << pinGridLocation << ", original db abs. loc. : " << pinDbLocation.m_x << " " << pinDbLocation.m_y << ", layers:";

    gridPin.setPinCenter(pinGridLocation);
    gridPin.setPinLayers(layers);
    for (auto layer : layers) {
        gridPin.pinWithLayers.push_back(Location(pinGridLocation.m_x, pinGridLocation.m_y, layer));

        //if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
            //std:cout << " " << layer;
    }

    //if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
        //std:cout << ", #layers:" << gridPin.pinWithLayers.size() << " " << layers.size() << std::endl;

    // Setup GridPin's LL,UR boundary
    double width = 0, height = 0;
    mDb.getPadstackRotatedWidthAndHeight(inst, pad, width, height);
    Point_2D<double> pinDbUR{pinDbLocation.m_x + width / 2.0, pinDbLocation.m_y + height / 2.0};
    Point_2D<double> pinDbLL{pinDbLocation.m_x - width / 2.0, pinDbLocation.m_y - height / 2.0};
    Point_2D<int> pinGridLL, pinGridUR;
    dbPointToGridPointRound(pinDbUR, pinGridUR);
    dbPointToGridPointRound(pinDbLL, pinGridLL);
    pinGridUR.m_x += gridExpansion;
    pinGridUR.m_y += gridExpansion;
    pinGridLL.m_x -= gridExpansion;
    pinGridLL.m_y -= gridExpansion;
    gridPin.setPinLL(pinGridLL);
    gridPin.setPinUR(pinGridUR);

    //if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG)
        //std:cout << "PinGridLL: " << pinGridLL << ", PinGridUR: " << pinGridUR << std::endl;

    // Handle pad shape polygon to derive pinShapeToGrids
    double dbExpansion = gridLengthToDbLength((double)gridExpansion);
    Point_2D<double> expandedPadSize = pad.getSize();
    expandedPadSize.m_x += (2.0 * dbExpansion);
    expandedPadSize.m_y += (2.0 * dbExpansion);
    // WARNING!! shape_to_coords's pos can be origin only!!! Otherwise the rotate function will be wrong
    std::vector<Point_2D<double>> expandedPadPoly = shape_to_coords(expandedPadSize, point_2d{0, 0}, pad.getPadShape(), inst.getAngle(), pad.getAngle(), pad.getRoundRectRatio(), 32);

    // Calculate pinShapeToGrids
    // 1. Make Boost polygon of pad shape
    polygon_t padShapePoly;
    for (const auto &pt : expandedPadPoly) {
        bg::append(padShapePoly.outer(), point(pt.x() + pinDbLocation.x(), pt.y() + pinDbLocation.y()));
    }
    // printPolygon(padShapePoly);

    for (int x = pinGridLL.m_x; x <= pinGridUR.m_x; ++x) {
        for (int y = pinGridLL.m_y; y <= pinGridUR.m_y; ++y) {
            // 2. Make fake grid box as Boost polygon
            point_2d gridDbLL, gridDbUR;
            polygon_t gridDbPoly;
            this->gridPointToDbPoint(point_2d{(double)x - 0.5, (double)y - 0.5}, gridDbLL);
            this->gridPointToDbPoint(point_2d{(double)x + 0.5, (double)y + 0.5}, gridDbUR);
            ////std:cout << "gridDbLL: " << gridDbLL << ", gridDbUR" << gridDbUR << std::endl;
            bg::append(gridDbPoly.outer(), point(gridDbLL.x(), gridDbLL.y()));
            bg::append(gridDbPoly.outer(), point(gridDbLL.x(), gridDbUR.y()));
            bg::append(gridDbPoly.outer(), point(gridDbUR.x(), gridDbUR.y()));
            bg::append(gridDbPoly.outer(), point(gridDbUR.x(), gridDbLL.y()));
            bg::append(gridDbPoly.outer(), point(gridDbLL.x(), gridDbLL.y()));  // Closed loop
            // printPolygon(gridDbPoly);

            // Compare if the grid box polygon has overlaps with padstack polygon
            if (bg::overlaps(gridDbPoly, padShapePoly) || bg::within(gridDbPoly, padShapePoly)) {
                gridPin.addPinShapeGridPoint(Point_2D<int>{x, y});
            }
        }
    }
}

void GridBasedRouter::set_net_layer_pref_weight(const int _netId, const std::string &_layerName, const int _weight) {
    if (_weight < 0) {
        //std:cout << __FUNCTION__ << ": Invalid weight: " << _weight << std::endl;
        return;
    }
    if (_netId > this->mGridNets.size()) {
        //std:cout << __FUNCTION__ << ": Invalid net Id: " << _netId << std::endl;
        return;
    }
    if (mLayerNameToGridLayer.end() == mLayerNameToGridLayer.find(_layerName)) {
        //std:cout << __FUNCTION__ << ": Invalid layer name: " << _layerName << std::endl;
        return;
    }
    int gridLayerId = mLayerNameToGridLayer.find(_layerName)->second;
    auto &gridNet = this->mGridNets.at(_netId);
    if (gridLayerId >= gridNet.getLayerCosts().size()) {
        //std:cout << __FUNCTION__ << ": Invalid layer Id: " << gridLayerId << " to add weights" << std::endl;
        return;
    }

    gridNet.setLayerCost(gridLayerId, _weight);
    return;
}

void GridBasedRouter::set_net_all_layers_pref_weights(const int _netId, const int _weight) {
    if (_weight < 0) {
        //std:cout << __FUNCTION__ << ": Invalid weight: " << _weight << std::endl;
        return;
    }
    if (_netId > this->mGridNets.size()) {
        //std:cout << __FUNCTION__ << ": Invalid net Id: " << _netId << std::endl;
        return;
    }
    auto &gridNet = this->mGridNets.at(_netId);
    gridNet.setAllLayersCosts(_weight);
    return;
}

void GridBasedRouter::set_diff_pair_net_id(const int _netId1, const int _netId2) {
    if (_netId1 >= mGridNets.size()) {
        //std:cout << __FUNCTION__ << ": Invalid netId: " << _netId1 << std::endl;
        return;
    }
    if (_netId2 >= mGridNets.size()) {
        //std:cout << __FUNCTION__ << ": Invalid netId: " << _netId2 << std::endl;
        return;
    }

    auto &gn1 = this->mGridNets.at(_netId1);
    gn1.setPairNetId(_netId2);
    auto &gn2 = this->mGridNets.at(_netId2);
    gn2.setPairNetId(_netId1);

    if (GlobalParam_router::gVerboseLevel <= VerboseLevel::WARNING) {
        if (gn1.getGridNetclassId() != gn2.getGridNetclassId()) {
            //std:cout << __FUNCTION__ << "(): Different netclass between differential pair nets"
                      //<< ", net1's netclass: " << gn1.getGridNetclassId()
                      //<< ", net2's netclass: " << gn2.getGridNetclassId() << std::endl;
        }
    }

    // Create or get a corresponding diff pair netclass
    int gridDiffPairNetclassId = -1;
    setupGridDiffPairNetclass(gn1.getGridNetclassId(), gn2.getGridNetclassId(), gridDiffPairNetclassId);

    // Create a diff pair net instance
    this->mGridDiffPairNets.emplace_back(this->mGridDiffPairNets.size(),
                                         gridDiffPairNetclassId, mDb.getCopperLayers().size(), gn1, gn2);

    GridDiffPairNet &gDpNet = this->mGridDiffPairNets.back();
    gDpNet.setupDiffPairGridPins(0, this->mGridLayerToName.size() - 1);

    if (GlobalParam_router::gVerboseLevel <= VerboseLevel::DEBUG) {
        //std:cout << std::endl
                  //<< __FUNCTION__ << "(): Create a new diff pair..." << std::endl;
        //std:cout << "NetId1: " << gn1.getNetId() << ", NetId2: " << gn2.getNetId() << std::endl;
        //std:cout << "GridDiffPairNetId: " << gDpNet.getNetId() << ", GridDiffPairNetclassId: " << gDpNet.getGridNetclassId() << std::endl;
    }
}

void GridBasedRouter::initialization() {
    // Initilization
    this->setupLayerMapping();
    this->setupGridNetclass();
    this->setupBoardGrid();
    this->setupGridNetsAndGridPins();
}

void GridBasedRouter::route_diff_pairs() {
    //std:cout << std::fixed << std::setprecision(5);
    //std:cout << std::endl
              //<< "=================" << __FUNCTION__ << "==================" << std::endl;

    // Add all instances' pins to a cost in grid (without inflation for spacing)
    mBg.addPinShapeObstacleCostToGrid(this->mGridPins, GlobalParam_router::gPinObstacleCost, true, true, true);

    std::string initialMapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + ".initial" + this->getParamsNameTag();
    mBg.printMatPlot(initialMapNameTag);

    // Add all nets to grid routes
    double totalCurrentRouteCost = 0.0;
    bestTotalRouteCost = 0.0;
    auto &nets = mDb.getNets();

    for (auto &gridDPNet : this->mGridDiffPairNets) {
        MultipinRoute &gn1 = gridDPNet.getGridNet1();
        MultipinRoute &gn2 = gridDPNet.getGridNet2();

        //std:cout << "\n\nRouting differential pair nets: " << nets.at(gn1.getNetId()).getName()
                  //<< "(" << gn1.getNetId() << ") and " << nets.at(gn2.getNetId()).getName()
                  //<< "(" << gn2.getNetId() << "), dpNetId: " << gridDPNet.getNetId()
                  //<< ", dpNetclassId: " << gridDPNet.getGridDiffPairNetclassId() << std::endl;

        gridDPNet.setCurTrackObstacleCost(GlobalParam_router::gTraceBasicCost);
        gridDPNet.setCurViaObstacleCost(GlobalParam_router::gViaInsertionCost);
        gn1.setCurTrackObstacleCost(GlobalParam_router::gTraceBasicCost);
        gn1.setCurViaObstacleCost(GlobalParam_router::gViaInsertionCost);
        gn2.setCurTrackObstacleCost(GlobalParam_router::gTraceBasicCost);
        gn2.setCurViaObstacleCost(GlobalParam_router::gViaInsertionCost);

        // Route the net
        mBg.routeGridDiffPairNet(gridDPNet);

        // totalCurrentRouteCost += gridNet.currentRouteCost;
        // //std:cout << "=====> currentRouteCost: " << gridNet.currentRouteCost << ", totalCost: " << totalCurrentRouteCost << std::endl;

        // Debugging purpose, put the GridDiffPairNet routing result into DB
        // for (const auto &gp : gridDPNet.mGridPaths) {
        //     auto &ngp = gn1.getNewGridPath();
        //     ngp = gp;
        // }
    }

    // Set up the base solution
    std::vector<double> iterativeCost;
    iterativeCost.push_back(totalCurrentRouteCost);
    bestTotalRouteCost = totalCurrentRouteCost;
    this->bestSolution = this->mGridNets;
    routingSolutions.push_back(this->mGridNets);

    //std:cout << "i=0, totalCurrentRouteCost: " << totalCurrentRouteCost << ", bestTotalRouteCost: " << bestTotalRouteCost << std::endl;

    //std:cout << "\n\n======= Finished Routing all nets. =======\n\n"
              //<< std::endl;

    // Routing has done. Print the final base cost
    std::string mapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + this->getParamsNameTag();
    mBg.printMatPlot(mapNameTag);

    // Output final result to KiCad file
    std::string nameTag = "bestSolutionWithMerging";
    nameTag = nameTag + "." + this->getParamsNameTag();
    writeSolutionBackToDbAndSaveOutput(nameTag, this->bestSolution);
}

void GridBasedRouter::route_all() {
    std::cout << std::fixed << std::setprecision(5);
    std::cout << std::endl
              << "=================" << __FUNCTION__ << "==================" << std::endl;

    // Add all instances' pins to a cost in grid (without inflation for spacing)
    mBg.addPinShapeObstacleCostToGrid(this->mGridPins, GlobalParam_router::gPinObstacleCost, true, true, true);

    std::string initialMapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + ".initial" + this->getParamsNameTag();
    mBg.printMatPlot(initialMapNameTag);

    // Route all nets!
    this->routeSingleIteration();

    // Set up the base solution
    std::vector<double> iterativeCost;
    double totalCurrentRouteCost = this->getOverallRouteCost(this->mGridNets);
    iterativeCost.push_back(totalCurrentRouteCost);
    routingSolutions.push_back(this->mGridNets);
    this->bestTotalRouteCost = totalCurrentRouteCost;
    this->bestSolution = this->mGridNets;

    if (GlobalParam_router::gOutputDebuggingKiCadFile) {
        std::string nameTag = "fristTimeRouteAll";
        nameTag = nameTag + "." + this->getParamsNameTag();
        writeSolutionBackToDbAndSaveOutput(nameTag, this->mGridNets);
    }
    if (GlobalParam_router::gOutputDebuggingGridValuesPyFile) {
        std::string mapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + ".i_" + std::to_string(0) + this->getParamsNameTag();
        mBg.printMatPlot(mapNameTag);
    }

    std::cout << "\n\n======= Start Fixed-Order Rip-Up and Re-Route all nets. =======\n\n";

    for (int i = 0; i < static_cast<int>(GlobalParam_router::gNumRipUpReRouteIteration); ++i) {
        // Route all nets!
        this->routeSingleIteration(true);

    //     // Debugging output files
        if (GlobalParam_router::gOutputDebuggingKiCadFile) {
            std::string nameTag = "i_" + std::to_string(i + 1);
            nameTag = nameTag + "." + this->getParamsNameTag();
            writeSolutionBackToDbAndSaveOutput(nameTag, this->mGridNets);
        }
        if (GlobalParam_router::gOutputDebuggingGridValuesPyFile) {
            std::string mapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + ".i_" + std::to_string(i + 1) + this->getParamsNameTag();
            mBg.printMatPlot(mapNameTag);
        }

    //     // See if is a better routing solution
        totalCurrentRouteCost = this->getOverallRouteCost(this->mGridNets);
        if (totalCurrentRouteCost < bestTotalRouteCost) {
            bestTotalRouteCost = totalCurrentRouteCost;
            this->bestSolution = this->mGridNets;
        }
        routingSolutions.push_back(this->mGridNets);
        iterativeCost.push_back(totalCurrentRouteCost);
    }

    std::cout << "\n\n======= Rip-up and Re-route cost breakdown =======" << std::endl;
    for (std::size_t i = 0; i < iterativeCost.size(); ++i) {
        cout << "i=" << i << ", cost: " << iterativeCost.at(i)
             << ", WL: " << this->get_routed_wirelength(routingSolutions.at(i))
             << ", #Vias: " << this->get_routed_num_vias(routingSolutions.at(i))
             << ", #Bends: " << this->get_routed_num_bends(routingSolutions.at(i));

        if (fabs(bestTotalRouteCost - iterativeCost.at(i)) < GlobalParam_router::gEpsilon) {
            cout << " <- best result" << std::endl;
        } else {
            cout << std::endl;
        }
    }

    // Output final result to KiCad file
    std::string nameTag = "bestSolutionWithMerging";
    nameTag = nameTag + "." + this->getParamsNameTag();
    writeSolutionBackToDbAndSaveOutput(nameTag, this->bestSolution);

    std::cout << "\n\n======= Post Processing of the best solution =======" << std::endl;
    for (auto &&gridNet : this->bestSolution) {
        if (mDb.isNetId(gridNet.getNetId())) {
            cout << "\n\nNet: " << mDb.getNet(gridNet.getNetId()).getName() << ", netId: " << gridNet.getNetId() << std::endl;
        }
        double wireWidth = 0.0;
        if (mDb.isNetclassId(gridNet.getGridNetclassId())) {
            auto &dbNetclass = mDb.getNetclass(gridNet.getGridNetclassId());
            wireWidth = dbLengthToGridLength(dbNetclass.getTraceWidth());
        }
        gridNet.removeAcuteAngleBetweenGridPinsAndPaths(wireWidth);
    }

    std::cout << "\n\n======= Finished Routing all nets. =======\n\n"
              << std::endl;

    // Output final result to KiCad file
    nameTag = "afterPostProcessing." + this->getParamsNameTag();
    writeSolutionBackToDbAndSaveOutput(nameTag, this->bestSolution);
}

float GridBasedRouter::getOverallRouteCost(const std::vector<MultipinRoute> &gridNets) {
    float overallRouteCost = 0;
    for (const auto &gn : gridNets) {
        overallRouteCost += gn.currentRouteCost;
    }
    return overallRouteCost;
}

void GridBasedRouter::routeSingleIteration(const bool ripupRoutedNet) {
    routeDiffPairs(ripupRoutedNet);
    routeSignalNets(ripupRoutedNet);
}

void GridBasedRouter::routeDiffPairs(const bool ripupRoutedNet) {
    auto &nets = mDb.getNets();

    for (auto &gridDPNet : this->mGridDiffPairNets) {
        MultipinRoute &gn1 = gridDPNet.getGridNet1();
        MultipinRoute &gn2 = gridDPNet.getGridNet2();

        //std:cout << "\n\nRouting differential pair nets: " << nets.at(gn1.getNetId()).getName()
                  //<< "(" << gn1.getNetId() << ") and " << nets.at(gn2.getNetId()).getName()
                  //<< "(" << gn2.getNetId() << "), dpNetId: " << gridDPNet.getNetId()
                  //<< ", dpNetclassId: " << gridDPNet.getGridDiffPairNetclassId() << std::endl;

        if (!ripupRoutedNet) {
            // First Iteration
            gridDPNet.setCurTrackObstacleCost(GlobalParam_router::gTraceBasicCost);
            gridDPNet.setCurViaObstacleCost(GlobalParam_router::gViaInsertionCost);
            gn1.setCurTrackObstacleCost(GlobalParam_router::gTraceBasicCost);
            gn1.setCurViaObstacleCost(GlobalParam_router::gViaInsertionCost);
            gn2.setCurTrackObstacleCost(GlobalParam_router::gTraceBasicCost);
            gn2.setCurViaObstacleCost(GlobalParam_router::gViaInsertionCost);
        } else {
            // Rip-up routed net
            gridDPNet.clearGridPaths();
            mBg.ripup_route(gn1);
            mBg.ripup_route(gn2);

            // Reroute with updated obstacle costs
            gridDPNet.addCurTrackObstacleCost(GlobalParam_router::gStepTraObsCost);
            gridDPNet.addCurViaObstacleCost(GlobalParam_router::gStepViaObsCost);
            gn1.addCurTrackObstacleCost(GlobalParam_router::gStepTraObsCost);
            gn1.addCurViaObstacleCost(GlobalParam_router::gStepViaObsCost);
            gn2.addCurTrackObstacleCost(GlobalParam_router::gStepTraObsCost);
            gn2.addCurViaObstacleCost(GlobalParam_router::gStepViaObsCost);
        }

        // Route the net
        mBg.routeGridDiffPairNet(gridDPNet);
    }
}

void GridBasedRouter::routeSignalNets(const bool ripupRoutedNet) {
    auto &nets = mDb.getNets();
    for (auto &net : nets) {
        //Diff Pair
        // if (net.getId() != 228 && net.getId() != 230 && net.getId() != 274 && net.getId() != 376)
        //     continue;

        //Acute Angle
        // if (net.getId() != 31 && net.getId() != 34 && net.getId() != 18 /*&& net.getId() != 28*/)
        //     continue;

        //std:cout << "\n\nRouting net: " << net.getName() << ", netId: " << net.getId() << ", netDegree: " << net.getPins().size() << "..." << std::endl;
        if (net.getPins().size() < 2)
            continue;

        auto &gridRoute = this->mGridNets.at(net.getId());
        if (net.getId() != gridRoute.netId) {
            //std:cout << "!!!!!!! inconsistent net.getId(): " << net.getId() << ", gridRoute.netId: " << gridRoute.netId << std::endl;
        }
        if (gridRoute.isDiffPair()) {
            continue;
        }

        // Temporary reomve the pin cost on the cost grid
        mBg.addPinShapeObstacleCostToGrid(gridRoute.mGridPins, -GlobalParam_router::gPinObstacleCost, true, false, true);

        // if (GlobalParam_router::gOutputDebuggingGridValuesPyFile) {
        //     std::string mapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + ".Net_" + std::to_string(net.getId()) + ".removeSTPad." + this->getParamsNameTag();
        //     mBg.printMatPlot(mapNameTag);
        // }

        // Setup design rules in board grid
        if (!mDb.isNetclassId(net.getNetclassId())) {
            std::cerr << __FUNCTION__ << "() Invalid netclass id: " << net.getNetclassId() << std::endl;
            continue;
        }

        if (!ripupRoutedNet) {
            // First Iteration
            gridRoute.setCurTrackObstacleCost(GlobalParam_router::gTraceBasicCost);
            gridRoute.setCurViaObstacleCost(GlobalParam_router::gViaInsertionCost);
        } else {
            // Rip-up routed net
            mBg.ripup_route(gridRoute);
            // Reroute with updated obstacle costs
            gridRoute.addCurTrackObstacleCost(GlobalParam_router::gStepTraObsCost);
            gridRoute.addCurViaObstacleCost(GlobalParam_router::gStepViaObsCost);
        }

        // Route the net
        mBg.routeGridNetFromScratch(gridRoute);

        // Put back the pin cost on base cost grid
        mBg.addPinShapeObstacleCostToGrid(gridRoute.mGridPins, GlobalParam_router::gPinObstacleCost, true, false, true);
    }
}

void GridBasedRouter::route() {
    //std:cout << std::fixed << std::setprecision(5);
    //std:cout << std::endl
              //<< "=================" << __FUNCTION__ << "==================" << std::endl;

    // Add all instances' pins to a cost in grid (without inflation for spacing)
    mBg.addPinShapeObstacleCostToGrid(this->mGridPins, GlobalParam_router::gPinObstacleCost, true, true, true);

    std::string initialMapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + ".initial" + this->getParamsNameTag();
    mBg.printMatPlot(initialMapNameTag);

    // Add all nets to grid routes
    double totalCurrentRouteCost = 0.0;
    bestTotalRouteCost = 0.0;
    auto &nets = mDb.getNets();
    for (auto &net : nets) {
        //Diff Pair
        // if (net.getId() != 228 && net.getId() != 230 && net.getId() != 274 && net.getId() != 376)
        //     continue;

        //std:cout << "\n\nRouting net: " << net.getName() << ", netId: " << net.getId() << ", netDegree: " << net.getPins().size() << "..." << std::endl;
        if (net.getPins().size() < 2)
            continue;

        auto &gridRoute = this->mGridNets.at(net.getId());
        if (net.getId() != gridRoute.netId)
            //std:cout << "!!!!!!! inconsistent net.getId(): " << net.getId() << ", gridRoute.netId: " << gridRoute.netId << std::endl;

        // Temporary reomve the pin cost on the cost grid
        mBg.addPinShapeObstacleCostToGrid(gridRoute.mGridPins, -GlobalParam_router::gPinObstacleCost, true, false, true);

        // if (GlobalParam_router::gOutputDebuggingGridValuesPyFile) {
        //     std::string mapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + ".Net_" + std::to_string(net.getId()) + ".removeSTPad." + this->getParamsNameTag();
        //     mBg.printMatPlot(mapNameTag);
        // }

        // Setup design rules in board grid
        if (!mDb.isNetclassId(net.getNetclassId())) {
            std::cerr << __FUNCTION__ << "() Invalid netclass id: " << net.getNetclassId() << std::endl;
            continue;
        }
        gridRoute.setCurTrackObstacleCost(GlobalParam_router::gTraceBasicCost);
        gridRoute.setCurViaObstacleCost(GlobalParam_router::gViaInsertionCost);

        // Route the net
        mBg.routeGridNetFromScratch(gridRoute);
        totalCurrentRouteCost += gridRoute.currentRouteCost;
        //std:cout << "=====> currentRouteCost: " << gridRoute.currentRouteCost << ", totalCost: " << totalCurrentRouteCost << std::endl;

        // Put back the pin cost on base cost grid
        mBg.addPinShapeObstacleCostToGrid(gridRoute.mGridPins, GlobalParam_router::gPinObstacleCost, true, false, true);
    }

    // Set up the base solution
    std::vector<double> iterativeCost;
    iterativeCost.push_back(totalCurrentRouteCost);
    bestTotalRouteCost = totalCurrentRouteCost;
    this->bestSolution = this->mGridNets;
    routingSolutions.push_back(this->mGridNets);

    if (GlobalParam_router::gOutputDebuggingKiCadFile) {
        std::string nameTag = "fristTimeRouteAll";
        nameTag = nameTag + "." + this->getParamsNameTag();
        writeSolutionBackToDbAndSaveOutput(nameTag, this->mGridNets);
    }
    //std:cout << "i=0, totalCurrentRouteCost: " << totalCurrentRouteCost << ", bestTotalRouteCost: " << bestTotalRouteCost << std::endl;

    //std:cout << "\n\n======= Start Fixed-Order Rip-Up and Re-Route all nets. =======\n\n";

    // Rip-up and Re-route all the nets one-by-one ten times
    for (int i = 0; i < static_cast<int>(GlobalParam_router::gNumRipUpReRouteIteration); ++i) {
        for (auto &net : nets) {
            //continue;
            if (net.getPins().size() < 2)
                continue;

            auto &gridRoute = mGridNets.at(net.getId());
            if (net.getId() != gridRoute.netId)
                //std:cout << "!!!!!!! inconsistent net.getId(): " << net.getId() << ", gridRoute.netId: " << gridRoute.netId << std::endl;

            //std:cout << "\n\ni=" << i + 1 << ", Routing net: " << net.getName() << ", netId: " << net.getId() << ", netDegree: " << net.getPins().size() << "..." << std::endl;

            // Temporary reomve the pin cost on the cost grid
            mBg.addPinShapeObstacleCostToGrid(gridRoute.mGridPins, -GlobalParam_router::gPinObstacleCost, true, false, true);

            if (!mDb.isNetclassId(net.getNetclassId())) {
                std::cerr << __FUNCTION__ << "() Invalid netclass id: " << net.getNetclassId() << std::endl;
                continue;
            }

            // Rip-up and re-route
            mBg.ripup_route(gridRoute);
            totalCurrentRouteCost -= gridRoute.currentRouteCost;

            gridRoute.addCurTrackObstacleCost(GlobalParam_router::gStepTraObsCost);
            gridRoute.addCurViaObstacleCost(GlobalParam_router::gStepViaObsCost);
            mBg.routeGridNetFromScratch(gridRoute);
            totalCurrentRouteCost += gridRoute.currentRouteCost;

            // Put back the pin cost on base cost grid
            mBg.addPinShapeObstacleCostToGrid(gridRoute.mGridPins, GlobalParam_router::gPinObstacleCost, true, false, true);
        }
        if (GlobalParam_router::gOutputDebuggingKiCadFile) {
            std::string nameTag = "i_" + std::to_string(i + 1);
            nameTag = nameTag + "." + this->getParamsNameTag();
            writeSolutionBackToDbAndSaveOutput(nameTag, this->mGridNets);
        }
        if (GlobalParam_router::gOutputDebuggingGridValuesPyFile) {
            std::string mapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + ".i_" + std::to_string(i + 1) + this->getParamsNameTag();
            mBg.printMatPlot(mapNameTag);
        }
        if (totalCurrentRouteCost < bestTotalRouteCost) {
            //std:cout << "!!!!>!!!!> Found new bestTotalRouteCost: " << totalCurrentRouteCost << ", from: " << bestTotalRouteCost << std::endl;
            bestTotalRouteCost = totalCurrentRouteCost;
            this->bestSolution = this->mGridNets;
        }
        routingSolutions.push_back(this->mGridNets);
        iterativeCost.push_back(totalCurrentRouteCost);
        //std:cout << "i=" << i + 1 << ", totalCurrentRouteCost: " << totalCurrentRouteCost << ", bestTotalRouteCost: " << bestTotalRouteCost << std::endl;
    }
    //std:cout << "\n\n======= Rip-up and Re-route cost breakdown =======" << std::endl;
    for (std::size_t i = 0; i < iterativeCost.size(); ++i) {
        cout << "i=" << i << ", cost: " << iterativeCost.at(i)
             << ", WL: " << this->get_routed_wirelength(routingSolutions.at(i))
             << ", #Vias: " << this->get_routed_num_vias(routingSolutions.at(i))
             << ", #Bends: " << this->get_routed_num_bends(routingSolutions.at(i));

        if (fabs(bestTotalRouteCost - iterativeCost.at(i)) < GlobalParam_router::gEpsilon) {
            cout << " <- best result" << std::endl;
        } else {
            cout << std::endl;
        }
    }

    //std:cout << "\n\n======= Finished Routing all nets. =======\n\n"
              //<< std::endl;

    // Routing has done. Print the final base cost
    std::string mapNameTag = util_router::getFileNameWoExtension(mDb.getFileName()) + this->getParamsNameTag();
    mBg.printMatPlot(mapNameTag);

    // Output final result to KiCad file
    std::string nameTag = "bestSolutionWithMerging";
    nameTag = nameTag + "." + this->getParamsNameTag();
    writeSolutionBackToDbAndSaveOutput(nameTag, this->bestSolution);

    // mBg.showViaCachePerformance();
}

void GridBasedRouter::testRouterWithPinShape() {
    //std:cout << std::fixed << std::setprecision(5);
    //std:cout << std::endl
              //<< "=================" << __FUNCTION__ << "==================" << std::endl;

    // Initilization
    this->setupLayerMapping();
    this->setupGridNetclass();
    this->setupBoardGrid();
    this->setupGridNetsAndGridPins();

    // Add all instances' pins to a cost in grid (without inflation for spacing)
    //this->addAllPinCostToGrid(0);
    mBg.addPinShapeObstacleCostToGrid(this->mGridPins, GlobalParam_router::gPinObstacleCost, true, true, true);

    // Routing has done
    // Print the final base cost
    // mBg.printGnuPlot();
    mBg.printMatPlot();

    // Output final result to KiCad file
    // writeSolutionBackToDbAndSaveOutput(this->bestSolution);
}

void GridBasedRouter::addAllPinCostToGrid(const int inflate) {
    for (auto &gridPin : mGridPins) {
        addPinAvoidingCostToGrid(gridPin, GlobalParam_router::gPinObstacleCost, true, true, true, inflate);
    }
}

void GridBasedRouter::addPinAvoidingCostToGrid(const Pin &p, const float value, const bool toViaCost, const bool toViaForbidden, const bool toBaseCost, const int inflate) {
    // TODO: Id Range Checking?
    auto &comp = mDb.getComponent(p.getCompId());
    auto &inst = mDb.getInstance(p.getInstId());
    auto &pad = comp.getPadstack(p.getPadstackId());

    addPinAvoidingCostToGrid(pad, inst, value, toViaCost, toViaForbidden, toBaseCost, inflate);
}

void GridBasedRouter::addPinAvoidingCostToGrid(const padstack &pad, const instance &inst, const float value, const bool toViaCost, const bool toViaForbidden, const bool toBaseCost, const int inflate) {
    Point_2D<double> pinDbLocation;
    mDb.getPinPosition(pad, inst, &pinDbLocation);
    double width = 0, height = 0;
    mDb.getPadstackRotatedWidthAndHeight(inst, pad, width, height);
    Point_2D<double> pinDbUR{pinDbLocation.m_x + width / 2.0, pinDbLocation.m_y + height / 2.0};
    Point_2D<double> pinDbLL{pinDbLocation.m_x - width / 2.0, pinDbLocation.m_y - height / 2.0};
    Point_2D<int> pinGridLL, pinGridUR;
    dbPointToGridPointRound(pinDbUR, pinGridUR);
    dbPointToGridPointRound(pinDbLL, pinGridLL);
    if (inflate > 0) {
        pinGridUR.m_x += inflate;
        pinGridUR.m_y += inflate;
        pinGridLL.m_x -= inflate;
        pinGridLL.m_y -= inflate;
    }
    //std:cout << __FUNCTION__ << "()"
              //<< " toViaCostGrid:" << toViaCost << ", toViaForbidden:" << toViaForbidden << ", toBaseCostGrid:" << toBaseCost;
    //std::cout << ", cost:" << value << ", inst:" << inst.getName() << "(" << inst.getId() << "), pad:"
              //<< pad.getName() << ", at(" << pinDbLocation.m_x << ", " << pinDbLocation.m_y
              //<< "), w:" << width << ", h:" << height << ", LLatgrid:" << pinGridLL << ", URatgrid:" << pinGridUR
              //<< ", inflate: " << inflate << ", layers:";

    // TODO: Unify Rectangle to set costs
    // Get layer from Padstack's type and instance's layers
    std::vector<int> layers;
    this->getGridLayers(pad, inst, layers);

    for (auto &layer : layers) {
        //std:cout << " " << layer;
    }
    //std:cout << std::endl;

    for (auto &layer : layers) {
        for (int x = pinGridLL.m_x; x <= pinGridUR.m_x; ++x) {
            for (int y = pinGridLL.m_y; y <= pinGridUR.m_y; ++y) {
                Location gridPt{x, y, layer};
                if (!mBg.validate_location(gridPt)) {
                    //std::cout << "\tWarning: Out of bound, pin cost at " << gridPt << std::endl;
                    continue;
                }
                //std::cout << "\tAdd pin cost at " << gridPt << std::endl;
                if (toBaseCost) {
                    mBg.base_cost_add(value, gridPt);
                }
                if (toViaCost) {
                    mBg.via_cost_add(value, gridPt);
                }
                //TODO:: How to controll clear/set
                if (toViaForbidden) {
                    mBg.setViaForbidden(gridPt);
                }
            }
        }
    }
}

void GridBasedRouter::addPinAvoidingCostToGrid(const GridPin &gridPin, const float value, const bool toViaCost, const bool toViaForbidden, const bool toBaseCost, const int inflate) {
    Point_2D<int> pinGridLL = gridPin.getPinLL();
    Point_2D<int> pinGridUR = gridPin.getPinUR();
    if (inflate > 0) {
        pinGridUR.m_x += inflate;
        pinGridUR.m_y += inflate;
        pinGridLL.m_x -= inflate;
        pinGridLL.m_y -= inflate;
    }
    //std::cout << __FUNCTION__ << "()"
              //<< " toViaCostGrid:" << toViaCost << ", toViaForbidden:" << toViaForbidden << ", toBaseCostGrid:" << toBaseCost;
    //std::cout << ", cost:" << value << ", LLatgrid:" << pinGridLL << ", URatgrid:" << pinGridUR
              //<< ", inflate: " << inflate << std::endl;

    for (int layerId : gridPin.getPinLayers()) {
        for (int x = pinGridLL.m_x; x <= pinGridUR.m_x; ++x) {
            for (int y = pinGridLL.m_y; y <= pinGridUR.m_y; ++y) {
                Location gridPt{x, y, layerId};
                if (!mBg.validate_location(gridPt)) {
                    //std::cout << "\tWarning: Out of bound, pin cost at " << gridPt << std::endl;
                    continue;
                }
                //std::cout << "\tAdd pin cost at " << gridPt << std::endl;
                if (toBaseCost) {
                    mBg.base_cost_add(value, gridPt);
                }
                if (toViaCost) {
                    mBg.via_cost_add(value, gridPt);
                }
                //TODO:: How to controll clear/set
                if (toViaForbidden) {
                    mBg.setViaForbidden(gridPt);
                }
            }
        }
    }
}

bool GridBasedRouter::getGridLayers(const Pin &pin, std::vector<int> &layers) {
    // TODO: Id Range Checking?
    auto &comp = mDb.getComponent(pin.getCompId());
    auto &inst = mDb.getInstance(pin.getInstId());
    auto &pad = comp.getPadstack(pin.getPadstackId());

    return getGridLayers(pad, inst, layers);
}

bool GridBasedRouter::getGridLayers(const padstack &pad, const instance &inst, std::vector<int> &layers) {
    if (pad.getType() == padType::SMD) {
        auto layerIte = mDbLayerIdToGridLayer.find(inst.getLayer());
        if (layerIte != mDbLayerIdToGridLayer.end()) {
            layers.push_back(layerIte->second);
        }
    } else {
        //Put all the layers
        for (int layer = 0; layer < mGridLayerToName.size(); ++layer) {
            layers.push_back(layer);
        }
    }
    return true;
}

int GridBasedRouter::getNextRipUpNetId() {
    return rand() % mGridNets.size();
}

std::string GridBasedRouter::getParamsNameTag() {
    // std::ostringstream out;
    // out.precision();

    std::string ret = "s_" + std::to_string(this->get_grid_scale());
    ret += "_i_" + std::to_string(get_num_iterations());
    ret += "_b_" + std::to_string(get_enlarge_boundary());
    ret += "_lc_" + std::to_string((int)get_layer_change_weight());
    ret += "_to_" + std::to_string((int)get_track_obstacle_weight());
    ret += "_vo_" + std::to_string((int)get_via_obstacle_weight());
    ret += "_po_" + std::to_string((int)get_pad_obstacle_weight());
    ret += "_tss_" + std::to_string((int)get_track_obstacle_step_size());
    ret += "_vss_" + std::to_string((int)get_via_obstacle_step_size());
    return ret;
}

bool GridBasedRouter::dbPointToGridPoint(const point_2d &dbPt, point_2d &gridPt) {
    //TODO: boundary checking
    gridPt.m_x = dbPt.m_x * GlobalParam_router::inputScale - mMinX * GlobalParam_router::inputScale + GlobalParam_router::enlargeBoundary / 2;
    gridPt.m_y = dbPt.m_y * GlobalParam_router::inputScale - mMinY * GlobalParam_router::inputScale + GlobalParam_router::enlargeBoundary / 2;
    return true;
}

bool GridBasedRouter::dbPointToGridPointCeil(const Point_2D<double> &dbPt, Point_2D<int> &gridPt) {
    //TODO: boundary checking
    gridPt.m_x = ceil(dbPt.m_x * GlobalParam_router::inputScale - mMinX * GlobalParam_router::inputScale + (double)GlobalParam_router::enlargeBoundary / 2);
    gridPt.m_y = ceil(dbPt.m_y * GlobalParam_router::inputScale - mMinY * GlobalParam_router::inputScale + (double)GlobalParam_router::enlargeBoundary / 2);
    return true;
}

bool GridBasedRouter::dbPointToGridPointFloor(const Point_2D<double> &dbPt, Point_2D<int> &gridPt) {
    //TODO: boundary checking
    gridPt.m_x = floor(dbPt.m_x * GlobalParam_router::inputScale - mMinX * GlobalParam_router::inputScale + (double)GlobalParam_router::enlargeBoundary / 2);
    gridPt.m_y = floor(dbPt.m_y * GlobalParam_router::inputScale - mMinY * GlobalParam_router::inputScale + (double)GlobalParam_router::enlargeBoundary / 2);
    return true;
}

bool GridBasedRouter::dbPointToGridPointRound(const Point_2D<double> &dbPt, Point_2D<int> &gridPt) {
    //TODO: boundary checking
    gridPt.m_x = round(dbPt.m_x * GlobalParam_router::inputScale - mMinX * GlobalParam_router::inputScale + (double)GlobalParam_router::enlargeBoundary / 2);
    gridPt.m_y = round(dbPt.m_y * GlobalParam_router::inputScale - mMinY * GlobalParam_router::inputScale + (double)GlobalParam_router::enlargeBoundary / 2);
    return true;
}

bool GridBasedRouter::gridPointToDbPoint(const point_2d &gridPt, point_2d &dbPt) {
    //TODO: boundary checking
    //TODO: consider integer ceiling or flooring???
    dbPt.m_x = GlobalParam_router::gridFactor * (gridPt.m_x + mMinX * GlobalParam_router::inputScale - (double)GlobalParam_router::enlargeBoundary / 2);
    dbPt.m_y = GlobalParam_router::gridFactor * (gridPt.m_y + mMinY * GlobalParam_router::inputScale - (double)GlobalParam_router::enlargeBoundary / 2);
    return true;
}