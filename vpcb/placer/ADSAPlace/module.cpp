#include "module.hpp"
#include <boost/geometry/geometries/adapted/c_array.hpp>
#include <boost/geometry/geometries/adapted/boost_tuple.hpp>

BOOST_GEOMETRY_REGISTER_BOOST_TUPLE_CS(cs::cartesian)
BOOST_GEOMETRY_REGISTER_C_ARRAY_CS(cs::cartesian)

void Module::setNetList(int NetId) {
  // Sets parameters given an entry in Nets file
  Netlist.push_back(NetId);
}
void Module::setParameterNodes(double width, double height) {
  // Sets parameters given an entry in Nodes file
  this -> xCoordinate = 0.0;
  this -> yCoordinate = 0.0;
  this -> width = width;
  this -> height = height;
  double points[][2] = {{0.0, 0.0}, {width, 0.0}, {width, height}, {0.0, height}};
  model::polygon< model::d2::point_xy<double> > tmp;
  append(tmp, points);
  boost::geometry::correct(tmp);
  this -> poly = tmp;
  boost::geometry::envelope(poly, envelope);
}

void Module::setParameterPl(double xCoordinate, double yCoordinate) {
  // Sets parameters given an entry in Pl file
  this -> setPos(xCoordinate, yCoordinate);
  initialX = xCoordinate;
  initialY = yCoordinate;
  this -> sigma = 50.0;
}

void Module::setPos(double x, double y) {
  // Sets position of a node object (lower-left corner)
  trans::translate_transformer<double, 2, 2> translate(x - this->xCoordinate, y - this->yCoordinate);
  model::polygon<model::d2::point_xy<double> > tmp;
  boost::geometry::transform(this->poly, tmp, translate);
  this->poly = tmp;
  updateCoordinates();
}

/**
upateCoordinates
Updates parameters of Node class from a geometry object
*/
void Module::updateCoordinates() {
  boost::geometry::model::d2::point_xy<double> centroid;
  boost::geometry::centroid(this->poly, centroid);
  this -> xBy2 = centroid.get<0>();
  this -> yBy2 = centroid.get<1>();

  boost::geometry::model::box< model::d2::point_xy<double> > envtmp;
  boost::geometry::envelope(this->poly, envtmp);
  this->envelope = envtmp;
  Point minCorner = this->envelope.min_corner();
  Point maxCorner = this->envelope.max_corner();
  this->width  = maxCorner.get<0>() - minCorner.get<0>();
  this->height = maxCorner.get<1>() - minCorner.get<1>();
  this->xCoordinate = bg::get<bg::min_corner, 0>(this->envelope);
  this->yCoordinate = bg::get<bg::min_corner, 1>(this->envelope);
}

/**
printExterior
print polygon vertices
*/
void Module::printExterior() const{
  for(auto it = boost::begin(boost::geometry::exterior_ring(this->poly)); it != boost::end(boost::geometry::exterior_ring(this->poly)); ++it) {
      double x = bg::get<0>(*it);
      double y = bg::get<1>(*it);
      cout << x << " " << y << endl;
  }
}

/**
printParameter
print node params
*/
void Module::printParameter() {
  cout << "name      " << this -> name << endl;
  cout << "Width         " << this -> width << endl;
  cout << "Height        " << this -> height << endl;
  cout << "X_Co-ordinate " << this -> xCoordinate << endl;
  cout << "Y_Co-ordinate " << this -> yCoordinate << endl;
  cout << "X/2           " << xBy2 << endl;
  cout << "Y/2           " << yBy2 << endl;
  cout << "NetList       ";
  vector < int > ::iterator it2;
  for (it2 = Netlist.begin(); it2 != Netlist.end(); ++it2) {
    cout << * it2 << " ";
  }
  this -> printExterior();
  cout << "\n" << endl;
}

void Module::init_module(int id, int lev, bool r) {
  root = r;
  idx = id;
  level = lev;
}
void Module::add_child(Module* m) {
  children.push_back(m);
}
void Module::insert_cell(int i) {
  cells.push_back(i);
}
bool Module::isleaf() {
  return leaf;
}