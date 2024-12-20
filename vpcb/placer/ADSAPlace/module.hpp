#include <string>
#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <ctype.h>
#include <map>
#include <vector>


#include <boost/regex.hpp>
#include <boost/algorithm/string/split.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/trim_all.hpp>
#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/polygon.hpp>
#include <boost/tuple/tuple.hpp>

#include "element.hpp"
#include "pin.hpp"

using namespace std;
using namespace boost::geometry;
namespace trans = boost::geometry::strategy::transform;
namespace bg = boost::geometry;
typedef boost::geometry::model::d2::point_xy<double> Point;

/**
Module
Base module class for hierarchy
*/
class Module {
  public:
    string name;
    int level;

    int idx;
    model::polygon<model::d2::point_xy<double> > poly;
    boost::geometry::model::box< model::d2::point_xy<double> > envelope;
    double width;
    double height;
    double sigma;
    double xCoordinate;
    double yCoordinate;
    double xBy2;
    double yBy2;
    double initialX;
    double initialY;
    int orientation = 0;

    int terminal = 0;

    double x_offset = 0.0;
    double y_offset = 0.0; // virtual pin offsets

    vector < int > Netlist; // vector of netlist ids this module is associated with [for online wl comp.]
    vector < int > cells;

    vector < Module *> children;
    Module *parent = nullptr;
    bool leaf = false;
    bool root = false;
    bool macroModule = false;
    int fixed = 0;

    void setNetList(int NetId);
    void setParameterNodes(double width, double height);
    void setParameterPl(double xCoordinate, double yCoordinate);
    void setPos(double x, double y);
    void updateCoordinates();
    void printExterior() const;
    void printParameter();
    void init_module(int id, int lev, bool r);
    void add_child(Module* m);
    void insert_cell(int i);
    bool isleaf();
};