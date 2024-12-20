
#include <iostream>
#include <vector>
#include <fstream>
#include <string>
#include <regex>
#include <map>

#include <boost/algorithm/string/split.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/polygon.hpp>
#include <boost/geometry/geometries/adapted/boost_tuple.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/adapted/c_array.hpp>
#include "database/kicadPcbDataBase.h"

//#include "Node.hpp"
//#include "Pin.hpp"
#include "module.hpp"
//#include "Hierarchy.hpp"
//#include "readScl.hpp"

class element;
class pPin;
class Module;

extern map < string, int > name2id;
extern vector < element > element_Id;
extern vector < Module * > moduleId;
//extern Hierarchy H;

int readNodesFile(string fname);
int readShapesFile(string fname);
int readWtsFile(string fname);
int readPlFile(string fname);
int readClstFile(string fname);
map<int, vector<pPin> > readNetsFile(string fname);
map<int, vector<pPin> > readConstraintsFile(string fname, map<int, vector<pPin> > & netToCell, kicadPcbDataBase& db);
int writePlFile(string fname);
int writeRadFile(string fname);
int writeNodesFile(string fname);
int writeFlippedFile(string fname);
