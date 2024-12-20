#include "globalParam_router.h"

int GlobalParam_router::gLayerNum = 3;
double GlobalParam_router::gEpsilon = 0.00000000000001;
bool GlobalParam_router::g90DegreeMode = true;
// BoardGrid
double GlobalParam_router::gDiagonalCost = 1.41421356237;  //Cost for path searching
double GlobalParam_router::gWirelengthCost = 1.0;          //Cost for path searching
double GlobalParam_router::gLayerChangeCost = 10.0;        //Cost for path searching
// Obstacle cost
double GlobalParam_router::gViaInsertionCost = 100.0;  //Cost added to the via grid
double GlobalParam_router::gTraceBasicCost = 50.0;     //10?     //Cost added to the base grid by traces
double GlobalParam_router::gPinObstacleCost = 1000.0;  //2000?   //Cost for obstacle pins added to the via (or/and) base grid
// Increment of obstacle cost
double GlobalParam_router::gStepViaObsCost = 0.0;  //10.0;  //Cost added to the via grid
double GlobalParam_router::gStepTraObsCost = 0.0;  //2.5;
// Other cost
double GlobalParam_router::gViaTouchBoundaryCost = 1000.0;
double GlobalParam_router::gTraceTouchBoundaryCost = 100000.0;
double GlobalParam_router::gViaForbiddenCost = 2000.0;
double GlobalParam_router::gObstacleCurveParam = 10000.0;
// Grid Setup
unsigned int GlobalParam_router::inputScale = 10; //from 10 -> 1(for pseudo routing) no!!!
unsigned int GlobalParam_router::enlargeBoundary = 0;  //from 10 -> 50
float GlobalParam_router::gridFactor = 0.1;            // 1/inputScale
// Routing Options
bool GlobalParam_router::gViaUnderPad = false;
bool GlobalParam_router::gUseMircoVia = true;
bool GlobalParam_router::gAllowViaForRouting = true;
bool GlobalParam_router::gCurvingObstacleCost = true;
unsigned int GlobalParam_router::gNumRipUpReRouteIteration = 5;//5
// Outputfile
int GlobalParam_router::gOutputPrecision = 5;
string GlobalParam_router::gOutputFolder = "output";
bool GlobalParam_router::gOutputDebuggingKiCadFile = false;
bool GlobalParam_router::gOutputDebuggingGridValuesPyFile = false;
bool GlobalParam_router::gOutputStackedMicroVias = false;
// logfile
string GlobalParam_router::gLogFolder = "log";
VerboseLevel GlobalParam_router::gVerboseLevel = VerboseLevel::NOTSET;
//VerboseLevel GlobalParam_router::gVerboseLevel = VerboseLevel::DEBUG;

int GlobalParam_router::gSeed = 1470295829;  //time(NULL);
const double GlobalParam_router::gSqrt2 = sqrt(2);
const double GlobalParam_router::gTan22_5 = tan(22.5 * PI / 180.0);

util_router::TimeUsage GlobalParam_router::runTime = util_router::TimeUsage();

void GlobalParam_router::setFolders() {
    if (!util_router::createDirectory(gOutputFolder)) {
        gOutputFolder = "";
    }
    if (!util_router::createDirectory(gLogFolder)) {
        gLogFolder = "";
    }
}

void GlobalParam_router::showCurrentUsage(const string comment) {
    runTime.showUsage(comment, util_router::TimeUsage::PARTIAL);
}

void GlobalParam_router::showFinalUsage(const string comment) {
    runTime.showUsage(comment, util_router::TimeUsage::FULL);
}

void GlobalParam_router::setUsageStart() {
    runTime.start(util_router::TimeUsage::PARTIAL);
}
