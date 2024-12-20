#define BOOST_NO_AUTO_PTR

#include <cstdio>
#include "globalParam.h"
#include "util.h"
#include "linreg.h"

#include <functional>
#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <ctype.h>
#include <map>
#include <vector>
#include <unordered_set>
#include <algorithm>
#include <string>
#include <numeric>
#include <cmath>
#include <unistd.h>
#include <ctime>
#include <ratio>
#include <chrono>
#include <errno.h>

// boost version 1.69.0
#include <boost/algorithm/string/split.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/geometry.hpp>
#include <boost/assign.hpp>
#include <boost/geometry.hpp>
#include <boost/geometry/io/io.hpp>
#include <boost/geometry/algorithms/area.hpp>
#include <boost/geometry/geometries/point.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/polygon.hpp>
#include <boost/random.hpp>
#include <boost/random/normal_distribution.hpp>
#include <boost/random/uniform_real.hpp>
#include <boost/random/uniform_01.hpp>
#include <boost/foreach.hpp>
#include <boost/geometry/index/rtree.hpp>

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

#include "readFiles.hpp"
#include "time.h"
typedef boost::geometry::model::d2::point_xy<double> Point;

class placer{
    public:
    int iii = 0; //iterator counter
    placer(kicadPcbDataBase &db) : mDb(db) {}
    ~placer(){}

    void placer_flow();
    void test_flow();
    kicadPcbDataBase &getDb() { return mDb; }
    kicadPcbDataBase &mDb;

    void set_wirelength_weight(double _cst){l1 = _cst;}
    void set_num_iterations(int iter) {outer_loop_iter = iter;}
    //modified
    void set_iterations_moves(int iter) {inner_loop_iter = iter;}
    void set_initial_temperature(double tmp) {t_0 = tmp;}
    void set_ini_placemode(int mode) {ini_placemode = mode;}
    void set_movemode(int movemode) {move_mode = movemode;}

    int get_num_iterations() {return outer_loop_iter;}
    int get_iterations_moves() {return inner_loop_iter;}

    //for routing algorithm
    void write_back();
    bool routing_move();
    void out_check(bool pseudo_result);
    void rwrite_back();
    double solve_oa(double oa_cost);
    void pseudo_flow();
    //copy to routing algorithm
    //map<int, vector<pPin> > routingcell;
    vector <element> temp_sol;

    private:
    void random_initial_placement();
    void random_placement(int xmin, int xmax, int ymin, int ymax, element &e);

    //modified
    void initial_placement();
    void my_iniplacement(double xmin, double xmax, double ymin, double ymax, element &e);
    //void placement(int xmin, int xmax, int ymin, int ymax, element &e);
    void center_placement(int xmin, int xmax, int ymin, int ymax, element &e);
    void spiral_placement(int grid_x, int grid_y, double xmove, double ymove, element &e);
    void greedy_placement(int xmin, int xmax, int ymin, int ymax, element &e);
    void classification_placement(double xmin, double xmax, double ymin, double ymax, element &e);
    std::vector< double > cost_data;
    std::vector< double > cost_data1;

    //void set_boundaries();
    void initialize_params(map<int, vector<pPin> > &netToCell);
    void validate_move(element &et, double rx, double ry);

    vector<double> cost(map<int, vector<pPin> > &netToCell, int temp_debug = 0);
    //double cost_partial(vector < element *> &nodes, map<int, vector<pPin> > &netToCell);
    double cell_overlap();
    double Hpwl(map<int, vector<pPin> > &netToCell);
    double cell_overlap_partial(vector < element* > &elements);
    double wirelength_partial(vector < element* > &elements, map<int, vector<pPin> > &netToCell);
    double order(map<int, vector<pPin> > &netToCell);
    double order_partial(vector < element* > &elements, map<int, vector<pPin> > &netToCell);
    //avoid entraped
    double stun(map<int, vector<pPin> > &netToCell);
    bool check_entrapment();

    float annealer(map<int, vector<pPin> > &netToCell, string initial_pl);
    double initialize_temperature(map<int, vector<pPin> > &netToCell);
    void update_temperature();
    void modified_lam_update(int i);
    vector<double> initiate_move(vector<double> current_cost, map<int, vector<pPin> > &netToCell);
    bool check_move(double prevCost, double newCost);
    //void project_soln();
    void overlap_soln();
    vector < element > ::iterator random_element();

    private:
    vector < double > l_hist;
    vector < double > density_hist;
    vector < double > var_hist;
    vector < double > temp_hist;

    double micro_overlap_x;
    double micro_overlap_x2;
    double micro_cdist;
    double overlap_x;
    double overlap_x2;
    double  cdist;

    std::pair <double,double> density_normalization;
    double densityAlpha = 0.0001;
    int densityFlag = 0;

    bool entraped = false;
    double entrapment_threshold = 0.75;

    // best-so-far solution variables
    vector < element > bestSol;

    bool hierachical = false;

    double best_wl = 0.0;
    double best_rd = 0.0;
    double best_od = 0.0;
    double best_overlap = std::numeric_limits<double>::max();
    double best_cost = std::numeric_limits<double>::max();
    //double best_count = std::numeric_limits<double>::max();


    std::vector<std::string> mGridLayerToName;
    std::unordered_map<std::string, int> mLayerNameToGrid;

    // cost histories
    vector < double > cost_hist;
    vector < double > wl_hist;
    vector < double > oa_hist;

    // cost normalization terms
    int initial_loop_iter = 100;
    std::pair <double,double> cost_normalization;
    std::pair <double,double> wl_normalization;
    std::pair <double,double> area_normalization;
    std::pair <double,double> routability_normalization;
    std::pair <double,double> order_normalization;
    double sigma_update = 0.985;
    
    map<int, vector<pPin> > *netToCell = nullptr;
    vector < vector < pPin > > *netToCellVec = nullptr;
    vector< int > accept_history;

    int num_nets;
    vector< double > net_weights;

    //modified
    int ini_placemode = 0; // 0 for pure; 1 for center placement ; 2 for spiral placement; 3 for greedy packer;
    double next_pointx;
    double next_pointy;
    bool up2down = false;
    int move_mode = 0;
    
    // rtree datastructure for fast overlap check
    bool rt = true;
    bgi::rtree<std::pair<boost::geometry::model::box< model::d2::point_xy<int> >, int>, bgi::quadratic<16> > rtree;

    // annealing parameters
    double t_0 = 1;
    double Temperature;
    int outer_loop_iter = 1001;
    int inner_loop_iter = 25;
    double eps = -1.0;
    bool var = false;
    //double lambda_schedule = 0.95;
    double cong_coef = 0.0;
    double shift_var = 1.0;
    double ssamp = 0.0;

    double l1 = 0.9; //weight of hpwl
    double l_2 = 0.1; //weight of overlap
    double l_3 = 0;//weight of alignment
    bool begin_ali = false;
    bool update_cost = false;
    bool pseudo_routing = false;

    // annealing move parameters
    float rotate_proba = 0.15;
    //default = 0.1 
    float layer_change_proba = 0;
    float swap_proba = 0.25;
    //default = 0.5
    float shift_proba =  0.6;
    bool rotate_flag = 0;

    bool Is_routing_cost = false;
    int routing_time = 10;
    double via_normalization;
    double routingwl_normalization;
    // boost mt random number generator
    boost::mt19937 rng;

    // board boundaries
    double mMinX = std::numeric_limits<double>::max();
    double mMaxX = std::numeric_limits<double>::min();
    double mMinY = std::numeric_limits<double>::max();
    double mMaxY = std::numeric_limits<double>::min();

    const unsigned int inputScale = 10;
    const float grid_factor = 0.1; 
    const int debug = 0;

    // sigma change
    vector < double > s_area;
    double S_all;

    bool do_hplace = false;
    bool lam = false;
    double lambda_schedule = 0.9753893051539414;
    double AcceptRate = 0.5;
    double LamRate = 0.5;
    double lamtemp_update = 0.8853585421875213;
    double base_lam = 0.1329209929630061;
};