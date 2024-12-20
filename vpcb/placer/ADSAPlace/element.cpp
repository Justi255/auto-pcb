#include "element.hpp"

using namespace std;
using namespace boost::geometry;
namespace trans = boost::geometry::strategy::transform;
namespace bg = boost::geometry;
typedef boost::geometry::model::d2::point_xy<double> Point;//2D point in Cartesian coordinate system(笛卡尔坐标系)

/**
 * 设定几何属性，并绘制包含所有元件的最小矩形
*/
void element::setParameter(string _name, double _width, double _height, bool _terminal, int _id, int _mirror=0, bool throughhole=false){
    name = _name;
    xC = 0.0;
    yC = 0.0;
    orientation = 0;
    width = _width;
    height = _height;
    S = width * height;
    terminal = _terminal;
    mirror = _mirror;

    //for boost error
    //sigma = 50* max(200/(width*height),1.0);
    //sigma = 600/(width*height);
    //sigma =  max(max(width,height),1.0);
    //sigma = 50;
    //sigma = 100;
    //sigma = sqrt(pow(width,2) + pow(height,2));

    if (_mirror == -1){
        layer = -1;
    }
    orient_str = "N";
    id = _id;
    through_hole=throughhole;

    if (!terminal) {
    std::vector<Point> points;
    points.push_back(Point(0.0,0.0));
    points.push_back(Point(0.0,_height));
    points.push_back(Point(_width,_height));
    points.push_back(Point(_width,0.0));
    // points.push_back(Point(0.0,0.0));

    model::polygon< model::d2::point_xy<double> > _poly;
    assign_points(_poly, points);//Assign a range of points to the polygon
    boost::geometry::correct(_poly);//correct geometry

    poly = _poly;
    boost::geometry::envelope(_poly, envelope);
    boost::geometry::envelope(_poly, envelope_d);//Calculates the envelope (with strategy) of a geometry.assign below
    }
}

/**
直接读取shape信息
*/
void element::setParameterShapes(string wkt){
  model::polygon< model::d2::point_xy<double> > _poly;
  boost::geometry::read_wkt(wkt, _poly);
  boost::geometry::correct(_poly);
  poly = _poly;
}

/**
 * 读取weight
*/
void element::setParameterWts(int _weight){
  weight = _weight;
}

/**
 * 读取pl（？）文件
*/
void element::setParameterPl(double xC, double yC, string _orient_str, bool _fixed){
    setPos(xC, yC);
    initial_x = xC;
    initial_y = yC;
    orient_str = _orient_str;
    init_orient = str2orient(_orient_str);
    setRotation(str2orient(_orient_str));
    fixed = _fixed;

    //sigma = 50.0 * max(10/(double)(width * height), 1.0);
}

/**
 * 读取netlist文件,确定net序号
*/
void element::setNetList(int NetId){
    Netlist.push_back(NetId);
}

/**
 * 元件的顶点（poly)与中心绝对坐标（xC,yC)移动相同距离
*/
void element::setPos(double x, double y){
    if(!terminal) {
      trans::translate_transformer<double, 2, 2> translate(x - xC, y - yC);
      model::polygon<model::d2::point_xy<double> > tmp;
      boost::geometry::transform(poly, tmp, translate);
      poly = tmp;
      updateCoordinates();
  } else {
      xC = x;
      yC = y;
    }
}

void element::layerChange(){
    layer = -1 * layer;
    flipped = -1 * flipped;
    setRotation(4);
}

int element::wrap_orientation(int kX){
    return kX % 8;
}

/**
 * 先移到全局的原点旋转，再移回原位
*/
void element::setRotation(int r){
    int rot_deg = 45*r;
    double tmpx = xC;
    double tmpy = yC;

    setPos(-width/2,-height/2);//移到原点
    model::polygon<model::d2::point_xy<double> > tmp;
    trans::rotate_transformer<boost::geometry::degree, double, 2, 2> rotate(rot_deg);
    boost::geometry::transform(poly, tmp, rotate);
    poly = tmp;
    double otmp = wrap_orientation(orientation + r);
    orientation = otmp;
    setPos(tmpx, tmpy);
}

void element::updateCoordinates(){
    if(terminal) {
        center_x = xC;
        center_y = yC;
    } else {
        boost::geometry::model::d2::point_xy<double> centroid;
        boost::geometry::centroid(poly, centroid); //计算几何中心
        center_x = centroid.get<0>();
        center_y = centroid.get<1>();

        boost::geometry::model::box< model::d2::point_xy<double> > envtmp;
        boost::geometry::model::box< model::d2::point_xy<int> > envtmp2;
        boost::geometry::envelope(poly, envtmp);//envtmp为两点坐标
        envelope_d=envtmp;

        Point minCorner = envelope_d.min_corner();
        Point maxCorner = envelope_d.max_corner();
        width  = maxCorner.get<0>() - minCorner.get<0>();
        height = maxCorner.get<1>() - minCorner.get<1>();
        xC = bg::get<bg::min_corner, 0>(envelope_d);//左下角
        yC = bg::get<bg::min_corner, 1>(envelope_d);

        envtmp2.max_corner().set<0>(ceil(maxCorner.x()));
        envtmp2.max_corner().set<1>(ceil(maxCorner.y()));
        envtmp2.min_corner().set<0>(floor(minCorner.x()));
        envtmp2.min_corner().set<1>(floor(minCorner.y()));
        //boost::geometry::convert(envtmp, envtmp2);
        envelope = envtmp2;
  }
}

int element::str2orient(string o) const{
  if(o == "N") {
    return 0;
  } else if(o == "NE") {
    return 1;
  } else if(o == "E") {
    return 2;
  } else if(o == "SE") {
    return 3;
  } else if (o == "S") {
    return 4;
  } else if (o == "SW") {
    return 5;
  } else if (o == "W") {
    return 6;
  } else if (o == "NW") {
    return 7;
  }
  return -1;
}

string element::orient2str(int o) const{
    if(o == 0 || o == 8) {
    return "N";
  } else if(o == 1) {
    return "NE";
  } else if(o == 2) {
    return "E";
  } else if(o == 3) {
    return "SE";
  } else if(o == 4) {
    return "S";
  } else if(o == 5) {
    return "SW";
  } else if(o == 6) {
    return "W";
  } else if(o == 7) {
    return "NW";
  }
  return "";
}

/**
 * 输出元件顶点
*/
void element::printExterior() const{
    for(auto it = boost::begin(boost::geometry::exterior_ring(poly)); it != boost::end(boost::geometry::exterior_ring(poly)); ++it) {
        double x = bg::get<0>(*it);
        double y = bg::get<1>(*it);
        cout << x << " " << y << endl;
  }
}

void element::printParameter(){
    cout << "name          " << name << endl;
    cout << "id           " << id << endl;
    cout << "Width         " << width << endl;
    cout << "Height        " << height << endl;
    cout << "Weight        " << weight << endl;
    cout << "X_Co-ordinate " << xC << endl;
    cout << "Y_Co-ordinate " << yC << endl;
    cout << "X_center      " << center_x << endl;
    cout << "Y_center      " << center_y << endl;
    cout << "Orientation   " << orientation << endl;
    cout << "terminal      " << terminal << endl;
    cout << "fixed         " << fixed << endl;
    cout << "layer         " << layer << endl;
    cout << "through_hole   " << through_hole << endl;
    cout << "NetList       ";
    vector < int > ::iterator it2;
    for (it2 = Netlist.begin(); it2 != Netlist.end(); ++it2) {
        cout << *it2 << " ";
    }
    cout << "\n" << endl;
}