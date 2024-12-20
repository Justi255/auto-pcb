#include <string>

using namespace std;

class pPin {
  public:
  string name;
  double x_offset;
  double y_offset;
  int id;
  double depth;

  void set_params(string nn, double xoffset, double yoffset, int id) {
    this -> name = nn;
    this -> x_offset = xoffset;
    this -> y_offset = yoffset;
    this -> id = id;
  }
};
