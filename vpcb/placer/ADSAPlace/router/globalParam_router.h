#ifndef PCBROUTER_GLOBALPARAM_ROUTER_H
#define PCBROUTER_GLOBALPARAM_ROUTER_H

#include <math.h>
#include <stdlib.h>
#include <time.h>

#include <string>

#include "util_router.h"

using namespace std;

#define PI 3.14159265358979323846264338

#define BOUND_CHECKS

namespace pr {

using prIntCost = int;
using prFltCost = double;

}  // namespace pr

enum VerboseLevel {
    CRITICAL = 50,
    FATAL = CRITICAL,
    ERROR = 40,
    WARNING = 30,
    WARN = WARNING,
    INFO = 20,
    DEBUG = 10,
    NOTSET = 0,
    DEFAULT = WARN
};

class GlobalParam_router {
   public:
    static int gLayerNum;
    static double gEpsilon;
    static bool g90DegreeMode;

    //BoardGrid
    static double gDiagonalCost;
    static double gWirelengthCost;
    static double gLayerChangeCost;

    //Obstacle cost
    static double gViaInsertionCost;
    static double gTraceBasicCost;
    static double gPinObstacleCost;

    //Step size of obstacle cost
    static double gStepViaObsCost;
    static double gStepTraObsCost;

    //Other costs
    static double gViaTouchBoundaryCost;
    static double gTraceTouchBoundaryCost;
    static double gViaForbiddenCost;
    static double gObstacleCurveParam;

    //Grid Setup
    static unsigned int inputScale;
    static unsigned int enlargeBoundary;
    static float gridFactor;  // For outputing

    //Routing Options
    static bool gViaUnderPad;
    static bool gUseMircoVia;
    static bool gAllowViaForRouting;
    static bool gCurvingObstacleCost;
    static unsigned int gNumRipUpReRouteIteration;

    //Outputfile
    static int gOutputPrecision;
    static string gOutputFolder;
    static bool gOutputDebuggingKiCadFile;
    static bool gOutputDebuggingGridValuesPyFile;
    static bool gOutputStackedMicroVias;

    //Log
    static string gLogFolder;
    static VerboseLevel gVerboseLevel;

    const static double gSqrt2;
    const static double gTan22_5;

    static int gSeed;

    static util_router::TimeUsage runTime;

    static void setFolders();
    static void setLayerNum(int l) { gLayerNum = l; }

    static void showCurrentUsage(const string comment);
    static void showFinalUsage(const string comment);
    static void setUsageStart();
};

#endif
