#include <string>
#include <iostream>

#include <boost/regex.hpp>
#include <boost/algorithm/string/split.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/trim_all.hpp>
#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/polygon.hpp>
#include <boost/tuple/tuple.hpp>

using namespace std;
using namespace boost::geometry;
namespace trans = boost::geometry::strategy::transform;
namespace bg = boost::geometry;
typedef boost::geometry::model::d2::point_xy<double> Point;


class element{
    public:
    string name;
    model::polygon<model::d2::point_xy<double> > poly; //元件外端点
    boost::geometry::model::box< model::d2::point_xy<double> > envelope_d; //double型envelope
    boost::geometry::model::box< model::d2::point_xy<int> > envelope; //the envelope (with strategy) of a geometry(two points)

    int id;
    double width;
    double height;
    double S;//面积
    int weight;
    bool terminal;
    bool fixed;
    bool overlap;
    double sigma;//移动半径
    double xC; //左下角x坐标
    double yC; //左下角y坐标
    double initial_x; 
    double initial_y;
    double center_x; //几何中心坐标
    double center_y; //几何中心坐标
    string orient_str;
    int init_orient;
    int orientation; //数字化旋转角度 1：45°，2：90°， 3：135°...
    int layer = 1;//1 or -1;
    bool through_hole;
    int mirror;
    int flipped = -1;
    vector <int> Netlist;

    void setParameter(string _name, double _width, double _height, bool _terminal, int _id, int _mirror=0, bool throughhole=false);

    void setParameterShapes(string wkt);
    void setParameterWts(int _weight);
    void setParameterPl(double xCoordinate, double yCoordinate, string _orient_str, bool _fixed);
    void setNetList(int NetId);
    void setPos(double x, double y);
    void layerChange();
    //static void local_flip(Point &p);
    int wrap_orientation(int kX);
    void setRotation(int r);
    void updateCoordinates();
    int str2orient(string o) const;
    string orient2str(int o) const;
    void printExterior() const;
    void printParameter();
};