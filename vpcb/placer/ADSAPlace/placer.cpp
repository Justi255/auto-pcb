#include "placer.hpp"
#include "router/GridBasedRouter.h"

#define PI 3.14159265

using namespace std::chrono;

BOOST_GEOMETRY_REGISTER_BOOST_TUPLE_CS(cs::cartesian)

namespace bg = boost::geometry;
namespace bnu = boost::numeric::ublas;
namespace bgi = boost::geometry::index;
typedef bg::model::box< bg::model::d2::point_xy<double> > box2d;
typedef boost::geometry::model::polygon<boost::geometry::model::d2::point_xy<double> > polygon;
typedef bgi::rtree<std::pair<boost::geometry::model::box< model::d2::point_xy<int> >, int>, bgi::quadratic<16> > rtree_t;

vector < element > element_Id;
//todo():place by kicad_pcb files 
vector < Module * > moduleId;
map < string, int > name2id;


void placer::placer_flow(){
    //srand(time(NULL));
    int opt;
    string out_file;

    long long int id = -1;

    string parg = "";
    string initial_pl = "";

    std::cout << "=================placer==================" << std::endl;

    cout << "calculating boundaries..." << endl;
    double pminx, pmaxx, pminy, pmaxy;
    mDb.getBoardBoundaryByEdgeCuts(pminx, pmaxx, pminy ,pmaxy);

    //by ourself temporarily
    mMinX = pminx;
    mMaxX = pmaxx;
    mMinY = pminy;
    mMaxY = pmaxy;
    next_pointx = pminx;
    next_pointy = pminy;

    cout << mMinX << "," << mMinY << " " << mMaxX << "," << mMaxY << endl;

    map<int, vector<pPin> > netToCell;
    std::vector<instance> &instances =  mDb.getInstances();
    std::vector<net> &nets = mDb.getNets();

    for (int i = 0; i < instances.size(); ++i) {
        element e;
        element_Id.push_back(e);
    }

    bool fixed = false;
    int mirror = 1;
    for (auto &inst : instances){
        bool throughhole = false;
        point_2d bbox;

        mDb.getCompBBox(inst.getComponentId(), &bbox); 
        element e;
        int layer = inst.getLayer();
        if(layer == 0) {
            mirror = 1;
        } else {
            mirror = -1;
        }
        // if (bbox.m_x > 1000 || bbox.m_x < 0.001) {
        //     bbox.m_x = 5;
        // }
	    // if (bbox.m_y > 1000 || bbox.m_y < 0.001) {
        //     bbox.m_y = 5;
        // }

    auto &comp = mDb.getComponent(inst.getComponentId());
    if (comp.hasFrontCrtyd() && comp.hasBottomCrtyd()) {
		throughhole = true;
    }
    e.setParameter(inst.getName(), bbox.m_x + 0.2, bbox.m_y + 0.2, false, inst.getId(), mirror, throughhole);
    // e.setParameter(inst.getName(), bbox.m_x + 0.2, bbox.m_y + 0.2, false, inst.getId(), mirror, throughhole);
    
    //s_area.push_back(bbox.m_x*bbox.m_y);

    
    
    element_Id[inst.getId()] = e;
    name2id.insert(pair < string, int > (inst.getName(), inst.getId()));
    
    double angle = inst.getAngle();
    string ang = "";
    if (angle == 0) {
        ang = "N";
    } else if (angle == 90) {
        ang = "E";
    } else if (angle == 180) {
        ang = "S";
    } else if (angle == 270) {
        ang = "W";
    }
    if(inst.isLocked()) {
        fixed = true;
    } else {
        fixed = false;
    }

    if(e.fixed == false){
        S_all += bbox.m_x * bbox.m_y;   
    }

    element_Id[name2id[inst.getName()]].setParameterPl(inst.getX()- bbox.m_x/2.0, inst.getY()-bbox.m_y/2.0, ang, fixed);
    element_Id[name2id[inst.getName()]].printParameter();
}
    for(auto &net : nets){
        vector < pPin > pinTemp;
        for(auto pin : net.getPins()){
            pPin p;
            auto &inst = mDb.getInstance(pin.getInstId());
            element_Id[name2id[inst.getName()]].setNetList(net.getId());

            auto &comp = mDb.getComponent(pin.getCompId());
            point_2d pos;
            mDb.getPinPosition(pin, &pos);

            auto &pad = comp.getPadstack(pin.getPadstackId());

            // Fix for pad rotation problem here:
            Point_2D<double> offset(
                    pos.m_x - element_Id[name2id[inst.getName()]].center_x,
                    pos.m_y - element_Id[name2id[inst.getName()]].center_y
            );
            Point_2D<double> r_offset;
            double orient = inst.getAngle();

        if(orient == 0) { 
                    r_offset.m_x = offset.m_x;
                    r_offset.m_y = offset.m_y;
            } else if(orient == 90) { 
                    r_offset.m_x = -offset.m_y;
                    r_offset.m_y = offset.m_x;
            } else if(orient == 180) { 
                    r_offset.m_x = -offset.m_x;
                    r_offset.m_y = -offset.m_y;
            } else if(orient == 270) { 
                    r_offset.m_x = offset.m_y;
                    r_offset.m_y = -offset.m_x;
            }

            p.set_params(
                    inst.getName(),
                    r_offset.m_x,
                    r_offset.m_y,
                    element_Id[name2id[inst.getName()]].id
            );
            pinTemp.push_back(p);
        }
    netToCell.insert(pair < int, vector< pPin > > (net.getId(), pinTemp));
    }
    num_nets = netToCell.size();

    //rudy(netToCell);
    //cout << "initial cost: "<< endl;
    //cost(netToCell);
    //writePlFile("initial_pl.pl");
    iii = 1;
    // int T_sa;
    // if(outer_loop_iter > 3000){
    //     T_sa = floor(outer_loop_iter/3000);
    // }
    // for(int t=0; t<T_sa ; t++){
    //     outer_loop_iter = 3000;
    //     cout << "annealing:" << t << endl;
    //     float cost = annealer(netToCell, initial_pl);
    // }
    cout << "annealing" << endl;
    float cost = annealer(netToCell, initial_pl);

//for 0-overlap
    // while(cell_overlap() != 0){
    //     float cost = annealer(netToCell, initial_pl);
    // }

    if (bestSol.size() > 0) {
        element_Id = bestSol; 
    }

    // double n_hpwl = Hpwl(netToCell)/wl_normalization.second;
    // double n_overlap = cell_overlap()/area_normalization.second;
    // double n_rudy = rudy(netToCell)/routability_normalization.second;
    // double n_alignment = order(netToCell)/order_normalization.second;
    // double b_cost = l1*n_hpwl + l_2*n_overlap + l_3*n_rudy + l_4*n_alignment;

    cout << "Solution: " << "overlap: " << best_overlap<< " Hpwl: " << best_wl
    <<" Order: "<< best_od<<" Best_cost: "<< best_cost <<endl;

    // cout <<"wl norma:"<<wl_normalization.second<<"  overlap norma: "<<area_normalization.second
    // <<"  order norma:"<<order_normalization.second<<endl;

    // write back to db
    cout << "writing back to db..." << endl;
    int top = 0;
    int bot = 31;
    for (auto &inst : instances) {
        point_2d bbox;
        mDb.getCompBBox(inst.getComponentId(), &bbox);

        int angle = element_Id[inst.getId()].orientation;
        double ang = 0;
        if (angle == 0) {
            ang = 0;
        } else if (angle == 2) {
            ang = 90;
        } else if (angle == 4) {
            ang = 180;
        } else if (angle == 6) {
            ang = 270;
        }
        inst.setAngle(ang);
        double cx = element_Id[inst.getId()].center_x;
        double cy = element_Id[inst.getId()].center_y;
        inst.setX(cx);
        inst.setY(cy);

        if (element_Id[inst.getId()].layer == 1) {
          inst.setLayer(top);
        } else {
          inst.setLayer(bot);                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        }
    }
  
}

void placer::test_flow(){ 
    int opt;
    string out_file;

    long long int id = -1;

    string parg = "";
    string initial_pl = "";

    std::cout << "=================counter==================" << std::endl;

    cout << "calculating boundaries..." << endl;
    double pminx, pmaxx, pminy, pmaxy;
    mDb.getBoardBoundaryByEdgeCuts(pminx, pmaxx, pminy ,pmaxy);

    //by ourself temporarily
    mMinX = pminx;
    mMaxX = pmaxx;
    mMinY = pminy;
    mMaxY = pmaxy;
    next_pointx = pminx;
    next_pointy = pminy;

    cout << mMinX << "," << mMinY << " " << mMaxX << "," << mMaxY << endl;

    map<int, vector<pPin> > netToCell;
    std::vector<instance> &instances =  mDb.getInstances();
    std::vector<net> &nets = mDb.getNets();

    for (int i = 0; i < instances.size(); ++i) {
        element e;
        element_Id.push_back(e);
    }

    bool fixed = false;
    int mirror = 1;
    for (auto &inst : instances){
        bool throughhole = false;
        point_2d bbox;

        mDb.getCompBBox(inst.getComponentId(), &bbox); 
        element e;
        int layer = inst.getLayer();
        if(layer == 0) {
            mirror = 1;
        } else {
            mirror = -1;
        }
        if (bbox.m_x > 1000 || bbox.m_x < 0.001) {
            bbox.m_x = 5;
        }
	if (bbox.m_y > 1000 || bbox.m_y < 0.001) {
            bbox.m_y = 5;
        }

    auto &comp = mDb.getComponent(inst.getComponentId());
    if (comp.hasFrontCrtyd() && comp.hasBottomCrtyd()) {
		throughhole = true;
    }
    // e.setParameter(inst.getName(), bbox.m_x + 0.2, bbox.m_y + 0.2, false, inst.getId(), mirror, throughhole);
    e.setParameter(inst.getName(), bbox.m_x + 0.2, bbox.m_y + 0.2, false, inst.getId(), mirror, throughhole);

    element_Id[inst.getId()] = e;
    name2id.insert(pair < string, int > (inst.getName(), inst.getId()));
    
    double angle = inst.getAngle();
    string ang = "";
    if (angle == 0) {
        ang = "N";
    } else if (angle == 90) {
        ang = "E";
    } else if (angle == 180) {
        ang = "S";
    } else if (angle == 270) {
        ang = "W";
    }
    if(inst.isLocked()) {
        fixed = true;
    } else {
        fixed = false;
    }

    element_Id[name2id[inst.getName()]].setParameterPl(inst.getX()- bbox.m_x/2.0, inst.getY()-bbox.m_y/2.0, ang, fixed);
    element_Id[name2id[inst.getName()]].printParameter();
}
    for(auto &net : nets){
        vector < pPin > pinTemp;
        for(auto pin : net.getPins()){
            pPin p;
            auto &inst = mDb.getInstance(pin.getInstId());
            element_Id[name2id[inst.getName()]].setNetList(net.getId());

            auto &comp = mDb.getComponent(pin.getCompId());
            point_2d pos;
            mDb.getPinPosition(pin, &pos);

            auto &pad = comp.getPadstack(pin.getPadstackId());

            // Fix for pad rotation problem here:
            Point_2D<double> offset(
                    pos.m_x - element_Id[name2id[inst.getName()]].center_x,
                    pos.m_y - element_Id[name2id[inst.getName()]].center_y
            );
            Point_2D<double> r_offset;
            double orient = inst.getAngle();

        if(orient == 0) { 
                    r_offset.m_x = offset.m_x;
                    r_offset.m_y = offset.m_y;
            } else if(orient == 90) { 
                    r_offset.m_x = -offset.m_y;
                    r_offset.m_y = offset.m_x;
            } else if(orient == 180) { 
                    r_offset.m_x = -offset.m_x;
                    r_offset.m_y = -offset.m_y;
            } else if(orient == 270) { 
                    r_offset.m_x = offset.m_y;
                    r_offset.m_y = -offset.m_x;
            }

            p.set_params(
                    inst.getName(),
                    r_offset.m_x,
                    r_offset.m_y,
                    element_Id[name2id[inst.getName()]].id
            );
            pinTemp.push_back(p);
        }
    netToCell.insert(pair < int, vector< pPin > > (net.getId(), pinTemp));
    }
    num_nets = netToCell.size();

    //test for initial_placement
    high_resolution_clock::time_point t1 = high_resolution_clock::now();
    for(int i=0;i<1000000;i++){
        initial_placement();
    }
    // if(ini_placemode != 0){
    //     initial_placement();
    // }
    high_resolution_clock::time_point t2 = high_resolution_clock::now();
    duration<double> time_span = duration_cast< duration<double> >(t2 - t1);
    std::cout<<"time: "<<time_span.count()/1000000<<" (s)"<<std::endl;
    //initialize_params(netToCell);
    std::cout << "hpwl: "<<Hpwl(netToCell)
                  <<", overlap: "<<cell_overlap()
                  <<",wl:" << wl_normalization.first
                  <<",wl2:" << wl_normalization.second
                  <<",oa:" << area_normalization.first
                  <<",oa2:" << area_normalization.second
                    <<std::endl;

    cout << "writing back to db..." << endl;
    int top = 0;
    int bot = 31;
    for (auto &inst : instances) {
        point_2d bbox;
        mDb.getCompBBox(inst.getComponentId(), &bbox);

        int angle = element_Id[inst.getId()].orientation;
        double ang = 0;
        if (angle == 0) {
            ang = 0;
        } else if (angle == 2) {
            ang = 90;
        } else if (angle == 4) {
            ang = 180;
        } else if (angle == 6) {
            ang = 270;
        }
        inst.setAngle(ang);
        double cx = element_Id[inst.getId()].center_x;
        double cy = element_Id[inst.getId()].center_y;
        inst.setX(cx);
        inst.setY(cy);

        if (element_Id[inst.getId()].layer == 1) {
          inst.setLayer(top);
        } else {
          inst.setLayer(bot);
        }
    }

}

void placer::pseudo_flow(){
    int opt;
    string out_file;

    long long int id = -1;

    string parg = "";
    string initial_pl = "";

    std::cout << "=================placer==================" << std::endl;

    cout << "calculating boundaries..." << endl;
    double pminx, pmaxx, pminy, pmaxy;
    mDb.getBoardBoundaryByEdgeCuts(pminx, pmaxx, pminy ,pmaxy);

    //by ourself temporarily
    mMinX = pminx;
    mMaxX = pmaxx;
    mMinY = pminy;
    mMaxY = pmaxy;
    next_pointx = pminx;
    next_pointy = pminy;

    cout << mMinX << "," << mMinY << " " << mMaxX << "," << mMaxY << endl;

    map<int, vector<pPin> > netToCell;
    std::vector<instance> &instances =  mDb.getInstances();
    std::vector<net> &nets = mDb.getNets();

    for (int i = 0; i < instances.size(); ++i) {
        element e;
        element_Id.push_back(e);
    }

    bool fixed = false;
    int mirror = 1;
    for (auto &inst : instances){
        bool throughhole = false;
        point_2d bbox;

        mDb.getCompBBox(inst.getComponentId(), &bbox); 
        element e;
        int layer = inst.getLayer();
        if(layer == 0) {
            mirror = 1;
        } else {
            mirror = -1;
        }
        if (bbox.m_x > 1000 || bbox.m_x < 0.001) {
            bbox.m_x = 5;
        }
	    if (bbox.m_y > 1000 || bbox.m_y < 0.001) {
            bbox.m_y = 5;
        }

    auto &comp = mDb.getComponent(inst.getComponentId());
    if (comp.hasFrontCrtyd() && comp.hasBottomCrtyd()) {
		throughhole = true;
    }
    e.setParameter(inst.getName(), bbox.m_x+0.2, bbox.m_y+0.2, false, inst.getId(), mirror, throughhole);
    element_Id[inst.getId()] = e;
    name2id.insert(pair < string, int > (inst.getName(), inst.getId()));
    
    double angle = inst.getAngle();
    string ang = "";
    if (angle == 0) {
        ang = "N";
    } else if (angle == 90) {
        ang = "E";
    } else if (angle == 180) {
        ang = "S";
    } else if (angle == 270) {
        ang = "W";
    }
    if(inst.isLocked()) {
        fixed = true;
    } else {
        fixed = false;
    }

    if(e.fixed == false){
        S_all += bbox.m_x * bbox.m_y;   
    }

    element_Id[name2id[inst.getName()]].setParameterPl(inst.getX()- bbox.m_x/2.0, inst.getY()-bbox.m_y/2.0, ang, fixed);
    element_Id[name2id[inst.getName()]].printParameter();
}
    for(auto &net : nets){
        vector < pPin > pinTemp;
        for(auto pin : net.getPins()){
            pPin p;
            auto &inst = mDb.getInstance(pin.getInstId());
            element_Id[name2id[inst.getName()]].setNetList(net.getId());

            auto &comp = mDb.getComponent(pin.getCompId());
            point_2d pos;
            mDb.getPinPosition(pin, &pos);

            auto &pad = comp.getPadstack(pin.getPadstackId());

            // Fix for pad rotation problem here:
            Point_2D<double> offset(
                    pos.m_x - element_Id[name2id[inst.getName()]].center_x,
                    pos.m_y - element_Id[name2id[inst.getName()]].center_y
            );
            Point_2D<double> r_offset;
            double orient = inst.getAngle();

        if(orient == 0) { 
                    r_offset.m_x = offset.m_x;
                    r_offset.m_y = offset.m_y;
            } else if(orient == 90) { 
                    r_offset.m_x = -offset.m_y;
                    r_offset.m_y = offset.m_x;
            } else if(orient == 180) { 
                    r_offset.m_x = -offset.m_x;
                    r_offset.m_y = -offset.m_y;
            } else if(orient == 270) { 
                    r_offset.m_x = offset.m_y;
                    r_offset.m_y = -offset.m_x;
            }

            p.set_params(
                    inst.getName(),
                    r_offset.m_x,
                    r_offset.m_y,
                    element_Id[name2id[inst.getName()]].id
            );
            pinTemp.push_back(p);
        }
    netToCell.insert(pair < int, vector< pPin > > (net.getId(), pinTemp));
    }
    num_nets = netToCell.size();
    
    int j = 0;
    int num_components = 0;
    l1 = 0;
    l_2 = 1.0;
    double oa_cost = cell_overlap();
    initialize_params(netToCell);

    vector < element > ::iterator itElement;
    for (itElement = element_Id.begin(); itElement != element_Id.end(); ++itElement) { 
        num_components += 1;
    }
    double Q = S_all/num_components;

    vector < element > ::iterator esigma;
    for (esigma = element_Id.begin(); esigma != element_Id.end(); ++esigma) { 
        if (esigma->fixed){
            continue;
        }
        if(esigma->S <= Q){
            esigma->sigma = 100;
        }
        else{
            esigma->sigma = 100;
        }
    }
    while(best_overlap > 0 && j < 3000){
        cout<<"This is "<<j<<" iterations"<<endl;
        cout<<"Best oa is "<< best_overlap<<endl;
        oa_cost = solve_oa(oa_cost);
        j++;
    }

    cout << "writing back to db..." << endl;
    int top = 0;
    int bot = 31;
    for (auto &inst : instances) {
        point_2d bbox;
        mDb.getCompBBox(inst.getComponentId(), &bbox);

        int angle = element_Id[inst.getId()].orientation;
        double ang = 0;
        if (angle == 0) {
            ang = 0;
        } else if (angle == 2) {
            ang = 90;
        } else if (angle == 4) {
            ang = 180;
        } else if (angle == 6) {
            ang = 270;
        }
        inst.setAngle(ang);
        double cx = element_Id[inst.getId()].center_x;
        double cy = element_Id[inst.getId()].center_y;
        inst.setX(cx);
        inst.setY(cy);

        if (element_Id[inst.getId()].layer == 1) {
          inst.setLayer(top);
        } else {
          inst.setLayer(bot);
        }
    }
}

void placer::write_back(){
    //element_Id = bestSol;
    std::vector<instance> &instances =  mDb.getInstances();
    int top = 0;
    int bot = 31;
    for (auto &inst : instances) {
        point_2d bbox;
        mDb.getCompBBox(inst.getComponentId(), &bbox);

        int angle = element_Id[inst.getId()].orientation;
        double ang = 0;
        if (angle == 0) {
            ang = 0;
        } else if (angle == 2) {
            ang = 90;
        } else if (angle == 4) {
            ang = 180;
        } else if (angle == 6) {
            ang = 270;
        }
        inst.setAngle(ang);
        double cx = element_Id[inst.getId()].center_x;
        double cy = element_Id[inst.getId()].center_y;
        inst.setX(cx);
        inst.setY(cy);

        if (element_Id[inst.getId()].layer == 1) {
          inst.setLayer(top);
        } else {
          inst.setLayer(bot);                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        }
    }
}

void placer::rwrite_back(){
    element_Id = bestSol;
    //vector <double> routing_bestcost = cost(routingcell);
    //cout<<"routing bestSol's placement cost: " <<routing_bestcost[0] <<endl;
    write_back();
}

bool placer::routing_move(){
    temp_sol = element_Id;
    int state = -1;
    vector < element > ::iterator rand_element1;
    vector < element > ::iterator rand_element2;

    int r = 0;
    rand_element1 = random_element();
    while(rand_element1->terminal || rand_element1->name == "" || rand_element1->fixed) {
        rand_element1 = random_element();
    }

    double rand_element1_orig_x = rand_element1->xC;
    double rand_element1_orig_y = rand_element1->yC;
    double rand_element2_orig_x = 0.0;
    double rand_element2_orig_y = 0.0;

    boost::uniform_real<> uni_dist(0,1);
    boost::variate_generator<boost::mt19937&, boost::uniform_real<> >uni(rng, uni_dist);
    double i = uni();
    // action:swap
    if (i < swap_proba) { 
        state = 0;
        if(debug > 1) {
        cout << "swap" << endl;
        }
        rand_element2 = random_element();//TODO:change
        while(rand_element2->terminal || rand_element2->id == rand_element1->id || rand_element2->name == "" || rand_element2->fixed) {
            rand_element2 = random_element();
        }


        validate_move(*rand_element1, rand_element2_orig_x, rand_element2_orig_y);
        validate_move(*rand_element2, rand_element1_orig_x, rand_element1_orig_y);
    }
    //action:shift
    else if(swap_proba <= i && i< shift_proba + swap_proba){ 
        state = 1;
        if(debug > 1){
            cout<< "shift" <<endl;
        }

        double sigma = rand_element1 -> sigma;
        double sigma_leftx = min(sigma, rand_element1->xC - mMinX);
        double sigma_rightx = min(sigma, mMaxX - rand_element1->xC - rand_element1->width);
        double sigma_downy = min(sigma, rand_element1->yC - mMinY);
        double sigma_upy = min(sigma, mMaxY - rand_element1->yC - rand_element1->height);
        
        boost::uniform_real<> nd(-1*sigma_leftx, sigma_rightx);
        boost::variate_generator<boost::mt19937&,
                                 boost::uniform_real<> > var_nor(rng, nd);

        boost::uniform_real<> ny(-1*sigma_downy, sigma_upy);
        boost::variate_generator<boost::mt19937&,
                                 boost::uniform_real<> > var_nory(rng, ny);

        //old
        // boost::uniform_real<> nd(-1*sigma,sigma);
        // boost::variate_generator<boost::mt19937&,
        //                      boost::uniform_real<> > var_nor(rng, nd);
        double dx = var_nor();
        //double dy = var_nor();
        double dy = var_nory();

        double rx = rand_element1_orig_x + dx;
        double ry = rand_element1_orig_y + dy;

        validate_move(*rand_element1, rx, ry);
        }
    //action:rotate
    else if(shift_proba + swap_proba <= i && i< shift_proba + swap_proba + rotate_proba){
        state = 2;
        if(debug > 1){
             cout << "rotate" << endl;
        }

        if(rotate_flag == 0){
            boost::uniform_int<>uni_dist(0,3);
            boost::variate_generator<boost::mt19937&, boost::uniform_int<> > uni(rng, uni_dist);
            r = uni();
            r = r*2;
        } else {
            boost::uniform_int<> uni_dist(0,7);
            boost::variate_generator<boost::mt19937&, boost::uniform_int<> > uni(rng, uni_dist);
            r = uni();
            }
        rand_element1->setRotation(r);
        // bug1:宽超过PCB宽的旋转后会超出边界
        //validate_move(*rand_element1, rand_element1_orig_x, rand_element1_orig_y);
        validate_move(*rand_element1, rand_element1->xC, rand_element1->yC);       
        }
    //action:layer change
    else{
        state = 3;
        if(debug > 1){
            cout << "layer change" << endl;
        }
    }
    double  move_oa = cell_overlap();
    if(move_oa <= best_overlap){
        return true;
    }
    else{
        element_Id = temp_sol;
        return false;
    }
}

double placer::solve_oa(double oa_cost){

    double current_oa = oa_cost;
    double prev_oa = 0.0;

    int state = -1;

    vector < element > ::iterator rand_element1;
    vector < element > ::iterator rand_element2;

    vector < element* > perturbed_elements;

    int r = 0;
    rand_element1 = random_element();
    while(rand_element1->terminal || rand_element1->name == "" || rand_element1->fixed) {
        rand_element1 = random_element();
    }
    perturbed_elements.push_back(&(*rand_element1));

    double rand_element1_orig_x = rand_element1->xC;
    double rand_element1_orig_y = rand_element1->yC;
    double rand_element2_orig_x = 0.0;
    double rand_element2_orig_y = 0.0;

    boost::uniform_real<> uni_dist(0,1);
    boost::variate_generator<boost::mt19937&, boost::uniform_real<> >uni(rng, uni_dist);
    double i = uni();
    // action:swap
    if (i < swap_proba) { 
        state = 0;
        rand_element2 = random_element();//TODO:change
        while(rand_element2->terminal || rand_element2->id == rand_element1->id || rand_element2->name == "" || rand_element2->fixed) {
            rand_element2 = random_element();
        }

        perturbed_elements.push_back(&(*rand_element2));
        prev_oa = cell_overlap_partial(perturbed_elements);

        rand_element2_orig_x = rand_element2->xC;
        rand_element2_orig_y = rand_element2->yC;

        validate_move(*rand_element1, rand_element2_orig_x, rand_element2_orig_y);
        validate_move(*rand_element2, rand_element1_orig_x, rand_element1_orig_y);
    }
    //action:shift
    else if(swap_proba <= i && i< shift_proba + swap_proba){ 
        state = 1;
        if(debug > 1){
            cout<< "shift" <<endl;
        }
        prev_oa = cell_overlap_partial(perturbed_elements);

        double sigma = rand_element1 -> sigma;
        double sigma_leftx = min(sigma, rand_element1->xC - mMinX);
        double sigma_rightx = min(sigma, mMaxX - rand_element1->xC - rand_element1->width);
        double sigma_downy = min(sigma, rand_element1->yC - mMinY);
        double sigma_upy = min(sigma, mMaxY - rand_element1->yC - rand_element1->height);
        
        boost::uniform_real<> nd(-1*sigma_leftx, sigma_rightx);
        boost::variate_generator<boost::mt19937&,
                                 boost::uniform_real<> > var_nor(rng, nd);

        boost::uniform_real<> ny(-1*sigma_downy, sigma_upy);
        boost::variate_generator<boost::mt19937&,
                                 boost::uniform_real<> > var_nory(rng, ny);

        double dx = var_nor();
        double dy = var_nory();

        double rx = rand_element1_orig_x + dx;
        double ry = rand_element1_orig_y + dy;

        validate_move(*rand_element1, rx, ry);
        }
    //action:rotate
    else if(shift_proba + swap_proba <= i && i< shift_proba + swap_proba + rotate_proba){
        state = 2;
        prev_oa = cell_overlap_partial(perturbed_elements);

        if(rotate_flag == 0){
            boost::uniform_int<>uni_dist(0,3);
            boost::variate_generator<boost::mt19937&, boost::uniform_int<> > uni(rng, uni_dist);
            r = uni();
            r = r*2;
        } else {
            boost::uniform_int<> uni_dist(0,7);
            boost::variate_generator<boost::mt19937&, boost::uniform_int<> > uni(rng, uni_dist);
            r = uni();
            }
        rand_element1->setRotation(r);
        validate_move(*rand_element1, rand_element1->xC, rand_element1->yC);
        
        }
    //action:layer change
    else{
        state = 3;
        prev_oa = cell_overlap_partial(perturbed_elements);
        rand_element1->layerChange();
        }
        double transition_oa = cell_overlap_partial(perturbed_elements);

        double updated_oa = current_oa - prev_oa + transition_oa;
        if(updated_oa >= current_oa){            
            //换回初始位置
            if(state == 0){
                rand_element1->setPos(rand_element1_orig_x,rand_element1_orig_y);
                rand_element2->setPos(rand_element2_orig_x,rand_element2_orig_y);
            }
            else if(state == 1){
                rand_element1->setPos(rand_element1_orig_x,rand_element1_orig_y);
            }
            else if(state == 2){
                rand_element1->setRotation(8-r);
                rand_element1->setPos(rand_element1_orig_x,rand_element1_orig_y);
            }
            else if(state == 3){
                rand_element1->layerChange();
            }
            return current_oa;
        }
        else{
            best_overlap = cell_overlap();
            bestSol = element_Id;
            return best_overlap;
        }
}

void placer::out_check(bool pseudo_result){
    if(pseudo_result){
        bestSol = element_Id;
    }
    else{
        element_Id = temp_sol;
    }
}

void placer::validate_move(element &et, double rx, double ry){
    double validated_rx = max(rx, mMinX);
    double validated_ry = max(ry, mMinY);

    validated_rx = min(validated_rx, mMaxX - et.width);
    validated_ry = min(validated_ry, mMaxY - et.height);//在左下角

    // if (et.terminal || et.fixed) {
    //     validated_rx = rx;
    //     validated_ry = ry;
    // }
    et.setPos(validated_rx,validated_ry);
}

void placer::random_placement(int xmin, int xmax, int ymin, int ymax, element &e){
    boost::uniform_int<> uni_distx(xmin,xmax);
    boost::variate_generator<boost::mt19937&, boost::uniform_int<> > unix(rng, uni_distx);
    int rx = unix();

    boost::uniform_int<> uni_disty(ymin,ymax);
    boost::variate_generator<boost::mt19937&, boost::uniform_int<> > uniy(rng, uni_disty);
    int ry = uniy();

    int ro = 0;
    if (rotate_flag == 0) {
        boost::uniform_int<> uni_disto(0,3);
        boost::variate_generator<boost::mt19937&, boost::uniform_int<> > unio(rng, uni_disto);
        ro = unio();
        ro = ro * 2;
    } else {
        boost::uniform_int<> uni_disto(0,7);
        boost::variate_generator<boost::mt19937&, boost::uniform_int<> > unio(rng, uni_disto);
        ro = unio();
    }

    string ostr = e.orient2str(ro);
    e.setParameterPl(rx, ry, ostr, e.fixed);
    validate_move(e, rx, ry);
}

void placer::random_initial_placement(){
    vector < element > :: iterator itElement;
    for(itElement = element_Id.begin();itElement != element_Id.end();++itElement){
        if(!itElement -> fixed && !itElement -> terminal){
            random_placement(mMinX,mMaxX,mMinY,mMaxY,*itElement);
        }
    }
}

void placer::center_placement(int xmin, int xmax, int ymin, int ymax, element &e){
    e.setPos(xmin + (xmax - xmin)/2 - e.width/2, ymin + (ymax - ymin)/2 - e.height/2);
}

void placer::spiral_placement(int grid_x, int grid_y, double xmove, double ymove, element &e){

    if(mMinX + grid_x*xmove + e.width < mMaxX && mMinY + grid_y*ymove + e.height < mMaxY){
        e.setPos(mMinX + grid_x * xmove, mMinY + grid_y*ymove);
    }
    else if(mMinX + grid_x*xmove + e.width < mMaxX && mMinY + grid_y*ymove + e.height > mMaxY){
        e.setPos(mMinX + grid_x * xmove, mMaxY - e.height);
    }
    else if(mMinX + grid_x*xmove + e.width > mMaxX && mMinY + grid_y*ymove + e.height < mMaxY){
        e.setPos(mMaxX - e.width, mMinY + grid_y*ymove);
    }
    else{
        e.setPos(mMaxX - e.width, mMaxY - e.height);
    }
}

void placer::greedy_placement(int xmin, int xmax, int ymin, int ymax, element &e){
    if((next_pointx + e.width) < xmax && (next_pointy + e.height) < ymax && up2down == false){
        e.setPos(next_pointx,next_pointy);
        next_pointx += e.width;
        next_pointy += e.height;
    }
    else if(up2down == false){
        next_pointx = xmin;
        next_pointy = ymax - e.height;
        e.setPos(next_pointx,next_pointy);
        up2down = true;
    }
    else if((next_pointx + e.width) < xmax && (next_pointy - e.height) > ymin && up2down == true){
        next_pointx += e.width;
        next_pointy -= e.height;
        e.setPos(next_pointx,next_pointy);
    }
    else{
        e.setPos(xmin + (xmax - xmin)/2 - e.width/2, ymin + (ymax - ymin)/2 - e.height/2);
    }
}

void placer::my_iniplacement(double xmin, double xmax, double ymin, double ymax, element &e){
    vector < element > :: iterator itElement;

    double left_x   = mMinX + (mMaxX - mMinX)/4;
    double right_x  = mMaxX - (mMaxX - mMinX)/4;
    double down_y   = mMinY + (mMaxY - mMinY)/4;
    double up_y     = mMaxY - (mMaxY - mMinY)/4;
    
    double i_coordinate_x = mMinX + (mMaxX - mMinX)/2 - e.width/2;
    double i_coordinate_y = mMinY + (mMaxY - mMinY)/2 - e.height/2;

    //nums of elements
    // int num_component = 0;
    // for(itElement = element_Id.begin();itElement != element_Id.end();++itElement){
    //     if(!itElement -> fixed && !itElement -> terminal){
    //        num_component += 1;
    //     }
    // }
    boost::uniform_real<> uni_dist(0,1);
    boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni(rng, uni_dist);
    double i = uni();
    //outer
    if((e.name.find("J") != string::npos)||(e.name.find("JP") != string::npos)||(e.name.find("B") != string::npos)||(e.name.find("A") != string::npos)||(e.name.find("S") != string::npos)||(e.name.find("Y") != string::npos)||(e.name.find("E") != string::npos)){
            if(i < 0.25){
                boost::uniform_real<> uni_distx(xmin, left_x);
                boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
                double x = uni_x();

                boost::uniform_real<> uni_disty(down_y , ymax);
                boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
                double y = uni_y();
                validate_move(e,x,y);
                //e.setPos(o_lx,ry);
            }
            else if(i < 0.5){
                boost::uniform_real<> uni_distx(left_x, xmax);
                boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
                double x = uni_x();

                boost::uniform_real<> uni_disty(up_y, ymax);
                boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
                double y = uni_y();
                validate_move(e,x,y);
                //e.setPos(o_rx,ry);
            }
            else if(i < 0.75){
                boost::uniform_real<> uni_distx(right_x, xmax);
                boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
                double x = uni_x();

                boost::uniform_real<> uni_disty(ymin, up_y);
                boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
                double y = uni_y();
                validate_move(e,x,y);
                //e.setPos(rx,o_dy);
            }
            else{
                boost::uniform_real<> uni_distx(xmin, right_x);
                boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
                double x = uni_x();

                boost::uniform_real<> uni_disty(ymin, down_y);
                boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
                double y = uni_y();
                validate_move(e,x,y);
                //e.setPos(rx,o_uy);
            }
    }
    //middle
    else if((e.name.find("R") != string::npos)||(e.name.find("C") != string::npos)||(e.name.find("D") != string::npos)){
        boost::uniform_real<> uni_distx(left_x, right_x - e.width);
        boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
        double x = uni_x();

        boost::uniform_real<> uni_disty(down_y , up_y - e.height);
        boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
        double y = uni_y();
        validate_move(e,x,y);
    }
    else if((e.name.find("U") != string::npos)){
        e.setPos(i_coordinate_x,i_coordinate_y);
    }
    else {
        boost::uniform_real<> uni_distx(left_x, right_x - e.width);
        boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
        double x = uni_x();

        boost::uniform_real<> uni_disty(down_y , up_y - e.height);
        boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
        double y = uni_y();
        validate_move(e,x,y);
    }
}

void placer::classification_placement(double xmin, double xmax, double ymin, double ymax, element &e){
    vector < element > :: iterator itElement;

    double left_x   = mMinX + (mMaxX -mMinX)/4;
    double right_x  = mMaxX - (mMaxX -mMinX)/4;
    double down_y   = mMinY + (mMaxY - mMinY)/4;
    double up_y     = mMaxY - (mMaxY - mMinY)/4;
    
    double i_coordinate_x = mMinX + (mMaxX - mMinX)/2 - e.width/2;
    double i_coordinate_y = mMinY + (mMaxY - mMinY)/2 - e.height/2;
    boost::uniform_real<> uni_dist(0,1);
    boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni(rng, uni_dist);
    double i = uni();
    //inner
    if(e.S < 8.0){
        boost::uniform_real<> uni_distx(left_x, right_x - e.width);
        boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
        double x = uni_x();

        boost::uniform_real<> uni_disty(down_y , up_y - e.height);
        boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
        double y = uni_y();
        validate_move(e,x,y);
    }
    else if(e.Netlist.size() <= 6)
    //outer
        if(i < 0.25){
            boost::uniform_real<> uni_distx(xmin, left_x);
            boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
            double x = uni_x();

            boost::uniform_real<> uni_disty(down_y , ymax);
            boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
            double y = uni_y();
            validate_move(e,x,y);
        //e.setPos(o_lx,ry);
        }
        else if(i < 0.5){
            boost::uniform_real<> uni_distx(left_x, xmax);
            boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
            double x = uni_x();

            boost::uniform_real<> uni_disty(up_y, ymax);
            boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
            double y = uni_y();
            validate_move(e,x,y);
            //e.setPos(o_rx,ry);
        }
        else if(i < 0.75){
            boost::uniform_real<> uni_distx(right_x, xmax);
            boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
            double x = uni_x();

            boost::uniform_real<> uni_disty(ymin, up_y);
            boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
            double y = uni_y();
            validate_move(e,x,y);
        //e.setPos(rx,o_dy);
        }
        else{
            boost::uniform_real<> uni_distx(xmin, right_x);
            boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_x(rng, uni_distx);
            double x = uni_x();

            boost::uniform_real<> uni_disty(ymin, down_y);
            boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni_y(rng, uni_disty);
            double y = uni_y();
            validate_move(e,x,y);
            //e.setPos(rx,o_uy);
        }
    //inner
    else{
        e.setPos(i_coordinate_x,i_coordinate_y);
    }
}

void placer::initial_placement(){
    vector < element > :: iterator itElement;

    //for spiral placement
    int num_component = 0;
    for(itElement = element_Id.begin();itElement != element_Id.end();++itElement){
        if(!itElement -> fixed && !itElement -> terminal){
           num_component += 1;
        }
    }
    // int gridby2 = ceil(sqrt(num_component));
    int bdry_x = 0;
    int bdry_y = 0; //boundry
    while (bdry_x * bdry_y < num_component)
    {
        if(bdry_x <= bdry_y){
            bdry_x += 1;
        }
        else{
            bdry_y += 1;
        }
    }
    double xmove = (mMaxX - mMinX) / bdry_x;
    double ymove = (mMaxY - mMinY) / bdry_y;
    int grid_x = 0;
    int grid_y = 0;
    int move_mode = 0; // 0:up, 1:right, 2:down, 3:left
    int begin_x = 1;
    int begin_y = 0;



    //all element
    for(itElement = element_Id.begin();itElement != element_Id.end();++itElement){
        if(!itElement -> fixed && !itElement -> terminal){
            if(ini_placemode == 1){
                center_placement(mMinX,mMaxX,mMinY,mMaxY,*itElement);
            }
            else if(ini_placemode == 2){
                switch (move_mode)
                {
                //up
                case 0:
                    if(grid_y < bdry_y-1){
                        spiral_placement(grid_x, grid_y, xmove, ymove, *itElement);
                        grid_y += 1;
                    }
                    else{
                        bdry_y -= 1;
                        move_mode = 1;
                    }
                    break;
                //right
                case 1:
                    if(grid_x < bdry_x-1){
                        spiral_placement(grid_x, grid_y, xmove, ymove, *itElement);
                        grid_x += 1;
                    }
                    else{
                        bdry_x -= 1;
                        move_mode = 2;
                    }
                    break;
                //down
                case 2:
                    if(grid_y > begin_y){
                        spiral_placement(grid_x, grid_y, xmove, ymove, *itElement);
                        grid_y -= 1;
                    }
                    else{
                        begin_y += 1;
                        move_mode = 3;
                    }
                    break;
                //left
                case 3:
                    if(grid_x > begin_x){
                        spiral_placement(grid_x, grid_y, xmove, ymove, *itElement);
                        grid_x -= 1;
                    }
                    else{
                        begin_x += 1;
                        move_mode = 0;
                    }
                    break;
                default:random_placement(mMinX,mMaxX,mMinY,mMaxY,*itElement);
                    break;
                }
            }
            else if(ini_placemode == 3){
                greedy_placement(mMinX,mMaxX,mMinY,mMaxY,*itElement);
            }
            else if(ini_placemode == 4){
                my_iniplacement(mMinX,mMaxX,mMinY,mMaxY,*itElement);
            }
            else if(ini_placemode == 5){
                classification_placement(mMinX,mMaxX,mMinY,mMaxY,*itElement);
            }
            else{
                random_placement(mMinX,mMaxX,mMinY,mMaxY,*itElement);
            }
        }
    }

}

void placer::overlap_soln(){
    //double oa = cell_overlap();
    vector < element > ::iterator elementit1;
    vector < element > ::iterator elementit2;
    
    box2d env1;
    box2d env2;

    //while (oa > eps) {
    for (elementit1 = element_Id.begin(); elementit1 != element_Id.end(); ++elementit1) {
        if(elementit1->fixed){continue;}
        if (!elementit1->terminal) {
            env1 = elementit1->envelope_d;
            for (elementit2 = elementit1; elementit2 != element_Id.end(); ++elementit2) {
                if(elementit2->id == elementit1->id){continue;}
                if(elementit2->fixed){continue;}
                if(!intersects(elementit1->poly, elementit2->poly)) {
                    continue;
                } else {
                // Project out of envelope
                    env2 = elementit2->envelope_d;

                    double dx = 0.0;
                    double dy = 0.0;
                    double rx = elementit1->xC;
                    double ry = elementit1->yC;
                    double env1minx = env1.min_corner().x();
                    double env1miny = env1.min_corner().y();
                    double env1maxx = env1.max_corner().x();
                    double env1maxy = env1.max_corner().y();

                    double env2minx = env2.min_corner().x();
                    double env2miny = env2.min_corner().y();
                    double env2maxx = env2.max_corner().x();
                    double env2maxy = env2.max_corner().y();

                    // will get stuck in boundary edge case
                    if (abs(env1maxx - env2minx) < abs(env1minx - env2maxx)) {
                    // shift left
                        dx = env2minx - env1maxx;
                    } else {
                    // shift right
                        dx = env2maxx - env1minx;
                    }
                    if (abs(env1maxy - env2miny) < abs(env1miny - env2maxy)) {
                    // shift down
                        dy = env2miny - env1maxy;
                    } else {
                    // shift up
                        dy = env2maxy - env1miny;
                    }

                    if (dx < dy) {
                    // project in x direction
                        validate_move(*elementit1,rx + dx,ry);
                    } else {
                    // project in y direction
                        validate_move(*elementit1,rx,ry + dy);
                    }
                }
                }
            }
        }
    //}
}

void placer::initialize_params(map<int, vector<pPin> > &netToCell){
    vector < std::pair <double,double> > normalization_terms;

    int num_components = 0;
    vector < element > ::iterator itElement;
    for(itElement = element_Id.begin(); itElement != element_Id.end();++itElement){
        if(!itElement -> terminal){
            num_components += 1;
        }
    }
    std::pair < double, double > wl;
    std::pair < double, double > area;
    std::pair < double, double > odr;

    double sum_wl = 0.0;
    double sum_oa = 0.0;
    double sum_od = 0.0;

    begin_ali = true;
    for(int i=0; i<initial_loop_iter; i++){
        random_initial_placement();
        sum_wl += Hpwl(netToCell);
        sum_oa += cell_overlap();
        sum_od += order(netToCell);
    }
    begin_ali = false;

    wl.first = 0.0;
    wl.second = sum_wl / (float)initial_loop_iter;

    area.first = 0.0;
    area.second = sum_oa / (float)initial_loop_iter;
    area.second = max(area.second, 1.0); 

    odr.first = 0.0;
    odr.second = sum_od / (float)initial_loop_iter;

    normalization_terms.push_back(wl);
    normalization_terms.push_back(area);
    normalization_terms.push_back(odr);

    wl_normalization = normalization_terms[0];
    area_normalization = normalization_terms[1];
    order_normalization = normalization_terms[2];
}


/**
 * 计算HPWL
*/
double placer::Hpwl(map<int, vector<pPin> > &netToCell){
    map<int, vector < pPin > > :: iterator itNet;
    vector < pPin > ::iterator itCellList;
    double xVal, yVal, hpwl = 0;
    for (itNet = netToCell.begin(); itNet != netToCell.end(); ++itNet) {
        double minXW = mMaxX, minYW = mMaxY, maxXW = mMinX, maxYW = mMinY;
        
        // ignore "GND" etc.
        // vector < pPin > net = itNet->second;
        // if(net.size() > 10){
        //     continue;
        // }
        for (itCellList = itNet -> second.begin(); itCellList != itNet -> second.end(); ++itCellList) {
        if(itCellList->name == "") {
            continue;
        }
        int orient = element_Id[itCellList->id].orientation;
        int layer = element_Id[itCellList->id].layer;
        xVal = element_Id[itCellList->id].center_x;
        yVal = element_Id[itCellList->id].center_y;
        
        if (layer == 1) {
            if(orient == 0) { 
                xVal = xVal + itCellList->x_offset;
                yVal = yVal + itCellList->y_offset;
            } else if(orient == 2) { 
                xVal = xVal + itCellList->y_offset;
                yVal = yVal - itCellList->x_offset;
            } else if(orient == 4) {
                xVal = xVal - itCellList->x_offset;
                yVal = yVal - itCellList->y_offset;
            } else if(orient == 6) {
                xVal = xVal - itCellList->y_offset;
                yVal = yVal + itCellList->x_offset;
            } else {
                double rad = (orient*45.0*PI/180.0);
                xVal = itCellList->y_offset*sin(rad) + itCellList->x_offset*cos(rad) + xVal;
                yVal = itCellList->y_offset*cos(rad) - itCellList->x_offset*sin(rad) + yVal;
            }
        } else {
            if(orient == 0) {
            xVal = xVal + itCellList->x_offset;
            yVal = yVal + itCellList->y_offset;
            } else if(orient == 2) {
            xVal = xVal + itCellList->y_offset;
            yVal = yVal - itCellList->x_offset;
            } else if(orient == 4) {
            xVal = xVal - itCellList->x_offset;
            yVal = yVal - itCellList->y_offset;
            } else if(orient == 6) {
            xVal = xVal - itCellList->y_offset;
            yVal = yVal + itCellList->x_offset;
            } else {
            double rad = (orient*45.0*PI/180.0);
            xVal = itCellList->y_offset*sin(rad) + itCellList->x_offset*cos(rad) + xVal;
            yVal = itCellList->y_offset*cos(rad) - itCellList->x_offset*sin(rad) + yVal;
            }
        }
        if (xVal < minXW)
            minXW = xVal;
        if (xVal > maxXW)
            maxXW = xVal;
        if (yVal < minYW)
            minYW = yVal;
        if (yVal > maxYW)
            maxYW = yVal;
        }
        //cout<<"hpwl: "<<(abs((maxXW - minXW)) + abs((maxYW - minYW)))<<endl;
        hpwl += (abs((maxXW - minXW)) + abs((maxYW - minYW)));
    }
    return hpwl;
}

double placer::cell_overlap(){
    double overlap = 0.0;
    for(size_t i = 0; i< element_Id.size();i++){
        for(size_t j = 0; j<element_Id.size();j++){
            if(i == j){continue;}
            // if((element_Id[i].fixed && element_Id[j].fixed) || ((element_Id[i].layer != element_Id[j].layer) && (!element_Id[i].through_hole && !element_Id[j].through_hole))){
            //     continue;
            // }else{
                double oa = 0.0;
                std::deque<polygon> intersect_poly;

                double center_dist = abs(element_Id[i].center_x - element_Id[j].center_x) + abs(element_Id[i].center_y - element_Id[j].center_y);
                boost::geometry::intersection(element_Id[i].poly, element_Id[j].poly, intersect_poly);
                BOOST_FOREACH(polygon const& p, intersect_poly) {
                oa +=  bg::area(p);//计算重叠面积
                // }
                // if(oa < 0.00001){
                //     continue;
                // }
                if(oa == 0){
                    continue;
                }
                overlap += pow(oa,2)+ oa;// +1.0/(1.0+center_dist); //waiting for learning
            }
        }
    }
    return overlap;
}


double placer::order(map<int, vector<pPin> > &netToCell){
    map<int, vector < pPin > > ::iterator itNet;
    vector < pPin > ::iterator itCellList;
    double odr = 0.0;
        
    for (itNet = netToCell.begin(); itNet != netToCell.end(); ++itNet){
        if(!begin_ali){
            //std::cout<<"no calculate order"<<endl;
            return 0;
        }
        double x_0,y_0 = 0.0;
        double x_next,y_next = 0.0;
        vector <double> pad_x, pad_y;
        int num_pad = 0;
        double m_x = 0.0, m_y = 0.0;
        int id = 0;
        for (itCellList = itNet -> second.begin(); itCellList != itNet -> second.end(); ++itCellList){
            int orient = element_Id[itCellList->id].orientation;
            

            x_next = element_Id[itCellList->id].center_x;
            y_next = element_Id[itCellList->id].center_y; 
            
            if(orient == 0) { // 0
                x_next = x_next + itCellList->x_offset;
                y_next = y_next + itCellList->y_offset;
            } else if(orient == 2) { // 90
                x_next = x_next + itCellList->y_offset;
                y_next = y_next - itCellList->x_offset;
            } else if(orient == 4) { // 180
                x_next = x_next - itCellList->x_offset;
                y_next = y_next - itCellList->y_offset;
            } else if(orient == 6) { // 270
                x_next = x_next - itCellList->y_offset;
                y_next = y_next + itCellList->x_offset;
            } else {
                double rad = (orient*45.0*PI/180.0);
                x_next = itCellList->y_offset*sin(rad) + itCellList->x_offset*cos(rad) + x_next;
                y_next = itCellList->y_offset*cos(rad) - itCellList->x_offset*sin(rad) + y_next;
            }
            pad_x.push_back(x_next);
            pad_y.push_back(y_next);

            //old version, multi
            // if(id == 0){
            //     x_0 = x_next;
            //     y_0 = y_next;
            //     id = 1;
            // }
            // if(m_x < abs(x_0 - x_next)){
            //     m_x = abs(x_0 - x_next);
            // }
            // if(m_y < abs(y_0 - y_next)){
            //     m_y = abs(y_0 - y_next);
            // }
            // odr += abs((x_0 - x_next) * (y_0 - y_next));

            //one by one alignment
            // if(id == 1){
            //     if((x_0 - x_next) == 0 || (y_0 - y_next) == 0){
            //         x_0 = x_next;
            //         y_0 = y_next;
            //         continue;
            //     }
            //     odr += min(abs((x_0 - x_next)/(y_0 - y_next)),abs((y_0 - y_next)/(x_0 - x_next)));
            //     x_0 = x_next;
            //     y_0 = y_next;
            // }

            
        }
        //odr += m_x * m_y;
        num_pad = pad_x.size();
        if(num_pad < 2){
            continue;
        }
        else if(num_pad == 2){
            // double x = abs(pad_x[0] - pad_x[1]);
            // double y = abs(pad_y[0] - pad_y[1]);
            // if(x==0 || y==0){
            //     odr += 0;
            // }
            // else{
            //     odr += min(x/y,y/x);
            // }
            continue;
        }
        //align with one pad
        // for (int i = 0; i < num_pad; i++){
        //     double min_alignment = std::numeric_limits<double>::max();
        //     double min_xy = 0.0;
        //     if(i > 0){
        //         for(int k = i-1;k >= 0;k--){
        //             double x = abs(pad_x[k] - pad_x[i]);
        //             double y = abs(pad_y[k] - pad_y[i]);
        //             if(x==0 || y==0){
        //                 min_alignment = 0.0;
        //                 break;
        //             }
        //             min_xy = min(x/y, y/x);
        //             min_alignment = min(min_alignment, min_xy);
        //         }
        //     }
        //     for(int j = i + 1; j < num_pad; j++){
        //         if(min_alignment == 0.0){
        //             break;
        //         }
        //         double x = abs(pad_x[i] - pad_x[j]);
        //         double y = abs(pad_y[i] - pad_y[j]);
        //         if(x==0 || y==0){
        //             min_alignment = 0.0;
        //             break;
        //         }
        //         min_xy = min(x/y, y/x);
        //         min_alignment = min(min_alignment, min_xy);
        //     }
        //     odr += min_alignment;
        // }
        
        //alignment for routing
        if(begin_ali){
            vector <int> order_id;
            double minLength = std::numeric_limits<double>::max();
            int minLengthId1 = -1;
            int minLengthId2 = -1;
            for (int i = 0; i < num_pad; ++i) {
                for (int j = i + 1; j < num_pad; ++j) {
                    double absx = abs(pad_x[i] - pad_x[j]);
                    double absy = abs(pad_y[i] - pad_y[j]);
                    double MaxDiff = max(absx,absy);
                    double MinDiff = min(absx,absy);
                    double dis = MaxDiff - MinDiff + sqrt(2)*MinDiff;
                    if (dis < minLength) {
                        minLength = dis;
                        minLengthId1 = i;
                        minLengthId2 = j;
                    }
                }
            }
            order_id.push_back(minLengthId1);
            order_id.push_back(minLengthId2);
            while(order_id.size() < num_pad){
                double minLength = std::numeric_limits<double>::max();
                int minLengthId = -1;
                for (const auto id : order_id) {
                    for (int i = 0; i < num_pad; ++i) {
                        auto it = std::find(order_id.begin(), order_id.end(), i);
                        if (it != order_id.end()) {
                            continue;
                        }
                        double absx = abs(pad_x[i] - pad_x[id]);
                        double absy = abs(pad_y[i] - pad_y[id]);
                        double MaxDiff = max(absx,absy);
                        double MinDiff = min(absx,absy);
                        double dis = MaxDiff - MinDiff + sqrt(2)*MinDiff;
                        if (dis < minLength) {
                            minLength = dis;
                            minLengthId = i;
                        }
                    }                
                }
                order_id.push_back(minLengthId);
            }
            for(int i = 0;i < num_pad-1;i++){
                double x = abs(pad_x[order_id[i]] - pad_x[order_id[i+1]]);
                double y = abs(pad_y[order_id[i]] - pad_y[order_id[i+1]]);
                if(x==0 || y==0){
                    odr += 0;
                }
                else{
                    odr += min(x/y,y/x);
                }      
            }
        }
        
    }

    return odr;
}

double placer::order_partial(vector < element* > &elements, map<int, vector<pPin> > &netToCell){
    vector < pPin > net;
    vector < int > ::iterator itNet;
    vector < pPin > ::iterator itCellList;
    vector < element *>::iterator itElement;
    unordered_set < int > net_history;
    double odr = 0.0;
    
    if(!begin_ali){
            //std::cout<<"no calculate order"<<endl;
            return 0;
    }

    for (itElement = elements.begin(); itElement != elements.end(); ++itElement) {
        for (itNet = (*itElement)->Netlist.begin(); itNet != (*itElement)->Netlist.end(); ++itNet) {

            //在容器中找不到对应net则插入
            if (net_history.find(*itNet) == net_history.end()) {
                net_history.insert(*itNet);
            } else {
                continue;
            }
            net = netToCell.find(*itNet)->second;
            int id = 0;
            double m_x = 0.0, m_y = 0.0;
            double x_0,y_0 = 0.0;
            double x_next,y_next = 0.0;
            vector <double> pad_x, pad_y;
            int num_pad = 0;
            for (itCellList = net.begin(); itCellList != net.end(); ++itCellList) {
                if(itCellList->name == "") {
                    continue;
                }
                int orient = element_Id[itCellList->id].orientation;
                x_next = element_Id[itCellList->id].center_x;
                y_next = element_Id[itCellList->id].center_y;

                if(orient == 0) { // 0
                    x_next = x_next + itCellList->x_offset;
                    y_next = y_next + itCellList->y_offset;
                } else if(orient == 2) { // 90
                    x_next = x_next + itCellList->y_offset;
                    y_next = y_next - itCellList->x_offset;
                } else if(orient == 4) { // 180
                    x_next = x_next - itCellList->x_offset;
                    y_next = y_next - itCellList->y_offset;
                } else if(orient == 6) { // 270
                    x_next = x_next - itCellList->y_offset;
                    y_next = y_next + itCellList->x_offset;
                } else {
                    double rad = (orient*45.0*PI/180.0);
                    x_next = itCellList->y_offset*sin(rad) + itCellList->x_offset*cos(rad) + x_next;
                    y_next = itCellList->y_offset*cos(rad) - itCellList->x_offset*sin(rad) + y_next;
                }
                pad_x.push_back(x_next);
                pad_y.push_back(y_next);
                // if(id == 0){
                //     x_0 = x_next;
                //     y_0 = y_next;
                //     id = 1;
                // }
                // if(m_x < abs(x_0 - x_next)){
                //     m_x = abs(x_0 - x_next);
                // }
                // if(m_y < abs(y_0 - y_next)){
                //     m_y = abs(y_0 - y_next);
                // }
                //odr += abs((x_0 - x_next)*(y_0 - y_next));

                // if(id == 1){
                //     if((x_0 - x_next) == 0 || (y_0 - y_next) == 0){
                //         continue;
                // }
                // odr += min(abs((x_0 - x_next)/(y_0 - y_next)),abs((y_0 - y_next)/(x_0 - x_next)));
                // x_0 = x_next;
                // y_0 = y_next;
                // }
            }
            //odr += m_x * m_y;
            num_pad = pad_x.size();
            if(num_pad < 2){
                continue;
            }
            else if(num_pad == 2){
                // double x = abs(pad_x[0] - pad_x[1]);
                // double y = abs(pad_y[0] - pad_y[1]);
                // if(x==0 || y==0){
                //     odr += 0;
                // }
                // else{
                //     odr += min(x/y,y/x);
                // }
                continue;
            }
            //align with one pad
            // for (int i = 0; i < num_pad; i++){
            //     double min_alignment = std::numeric_limits<double>::max();
            //     double min_xy = 0.0;
            //     if(i>0){
            //         for(int k = i;k > 0;k--){
            //             double x = abs(pad_x[k] - pad_x[i]);
            //             double y = abs(pad_y[k] - pad_y[i]);
            //             if(x==0 || y==0){
            //                 min_alignment = 0.0;
            //                 break;
            //             }
            //                 min_xy = min(x/y, y/x);
            //                 min_alignment = min(min_alignment, min_xy);
            //         }
            //     }
            //     for (int j = i + 1; j < num_pad; j++){                    
            //         if(min_alignment == 0.0){
            //             break;
            //         }
            //         double x = abs(pad_x[i] - pad_x[j]);
            //         double y = abs(pad_y[i] - pad_y[j]);
            //         if(x==0 || y==0){
            //             min_alignment = 0.0;
            //             break;
            //         }
            //         min_xy = min(x/y, y/x);
            //         min_alignment = min(min_alignment, min_xy);
            //     }
            //     odr += min_alignment;
            // }

            //alignment for routing
            if(begin_ali){
                vector <int> order_id;
                double minLength = std::numeric_limits<double>::max();
                int minLengthId1 = -1;
                int minLengthId2 = -1;
                for (int i = 0; i < num_pad; ++i) {
                    for (int j = i + 1; j < num_pad; ++j) {
                        double absx = abs(pad_x[i] - pad_x[j]);
                        double absy = abs(pad_y[i] - pad_y[j]);
                        double MaxDiff = max(absx,absy);
                        double MinDiff = min(absx,absy);
                        double dis = MaxDiff - MinDiff + sqrt(2)*MinDiff;
                        if (dis < minLength) {
                            minLength = dis;
                            minLengthId1 = i;
                            minLengthId2 = j;
                        }
                    }
                }
                order_id.push_back(minLengthId1);
                order_id.push_back(minLengthId2);
                while(order_id.size() < num_pad){
                    double minLength = std::numeric_limits<double>::max();
                    int minLengthId = -1;
                    for (const auto id : order_id) {
                        for (int i = 0; i < num_pad; ++i) {
                            auto it = std::find(order_id.begin(), order_id.end(), i);
                            if (it != order_id.end()) {
                                continue;
                            }
                            double absx = abs(pad_x[i] - pad_x[id]);
                            double absy = abs(pad_y[i] - pad_y[id]);
                            double MaxDiff = max(absx,absy);
                            double MinDiff = min(absx,absy);
                            double dis = MaxDiff - MinDiff + sqrt(2)*MinDiff;
                            if (dis < minLength) {
                                minLength = dis;
                                minLengthId = i;
                            }
                        }
                    }
                    order_id.push_back(minLengthId);
                }
                for(int i = 0;i < num_pad-1;i++){
                    double x = abs(pad_x[order_id[i]] - pad_x[order_id[i+1]]);
                    double y = abs(pad_y[order_id[i]] - pad_y[order_id[i+1]]);
                    if(x==0 || y==0){
                        odr += 0;
                    }
                    else{
                        odr += min(x/y,y/x);
                    }      
                }
            }
        }
            
    }   

    return odr;
}

vector<double> placer::cost(map<int, vector<pPin> > &netToCell, int temp_debug = 0){
    //double l2 = 1 - l1;

    double wl = Hpwl(netToCell);
    double oa = cell_overlap();
    double od = order(netToCell);

    double normalized_wl = (wl - wl_normalization.first)/(wl_normalization.second - wl_normalization.first);//first = 0, second = average;
    double normalized_oa = (oa - area_normalization.first)/(area_normalization.second - area_normalization.first);

    double normalized_od = (od - order_normalization.first)/(order_normalization.second - order_normalization.first);
    // wl_hist.push_back(normalized_wl);
    // oa_hist.push_back(normalized_oa);

    double wirelength_cost = l1 * normalized_wl;
    //double overlap_cost = l2 * (1-cong_coef) * normalized_oa;
    double overlap_cost = l_2 * normalized_oa;
    double order_cost = l_3 * normalized_od;
    double total_cost = wirelength_cost + overlap_cost + order_cost;//routability_cost;// + order_cost;
    //cout<<"wirelength_cost: "<< wirelength_cost<<endl;
    //cout << "cost: " << total_cost << " wirelength: " << wl << " " << wirelength_cost << " overlap: " << oa << " " << overlap_cost << " congestion: " << rd << " " << routability_cost << endl;
    vector < double > cost_ve;
    cost_ve.push_back(total_cost);
    cost_ve.push_back(wl);
    cost_ve.push_back(oa);
    cost_ve.push_back(od);
    //cost_data1.push_back(wl+oa);


    // if(total_cost < best_cost){
    //     best_cost = total_cost;
    // }

    //if(oa == best_overlap && (wl<best_wl || rd<best_rd))
    //if(oa == 0 && (wl+ rd < best_wl + best_rd))
    //if(oa == best_overlap && ((wl+ rd) < (best_wl + best_rd)))
    //((oa <= best_overlap && normal < best_cost)||(oa==0 && od<best_od))
    if(update_cost){
        best_cost = wirelength_cost + order_cost;
        best_od = od;
    }
    double normal = wirelength_cost + order_cost;
    //double best_normal = l1*best_wl/wl_normalization.second + l_3*best_rd/routability_normalization.second + l_4*best_od/order_normalization.second;
    if(oa <= best_overlap && (normal < best_cost)){//||( od < best_od ))){
        bestSol = element_Id;
        best_wl = wl;
        best_overlap = oa;
        best_od = od;

        best_cost = normal;
        // cout << "cost: " <<wl+oa<<endl;
        //cost_data.push_back(best_wl+best_overlap);

    }
    else if(oa < best_overlap){
        bestSol = element_Id;
        best_wl = wl;
        best_od = od;
        best_overlap = oa;

        best_cost = normal;
        //cost_data.push_back(best_wl+best_overlap);
        // cout << "cost: " <<wl+oa<<endl;
    }
    // else{
    //     cost_data.push_back(best_wl+best_overlap);
    //     }
    

    //return total_cost;+best_wl+best_rd+best_od
    cost_ve.push_back(best_cost);
    return cost_ve;
}

//TOLEARN：改变初始化条件
double placer::initialize_temperature(map<int, vector<pPin> > &netToCell){
    double t = 0.0;
    double emax = 0.0;
    double emin = 0.0;
    double xt = 1.0;
    double x0 = 0.84;
    double p = 2.0;
    vector<double> cst_vec_tmp;
    cst_vec_tmp.push_back(0.0);
    cst_vec_tmp.push_back(0.0);
    cst_vec_tmp.push_back(0.0);
    random_initial_placement();
    for(int i=1; i<=10; i++){
        for(int j=1; j<=10; j++){
        random_initial_placement();
        //emax += exp(cost(netToCell)/t);
        initiate_move(cst_vec_tmp, netToCell);
        //emin += exp(cost(netToCell)/t);
        }
        xt = emax/emin;
        t = t * pow(log(xt),1/p)/log(x0);
    }
    return t;
}

vector < element >::iterator placer::random_element() {
    vector < element > ::iterator itelement = element_Id.begin();
    int size = element_Id.size();
    boost::uniform_int<> uni_dist(0,size-1);
    boost::variate_generator<boost::mt19937&, boost::uniform_int<> > uni(rng, uni_dist);
    int randint = uni();
    std::advance(itelement, randint);
    return itelement;
}

double placer::cell_overlap_partial(vector < element* > &elements){
    double overlap = 0.0;
    unordered_set < int > cell_history;
    for(size_t i = 0; i < elements.size(); i++) {
        cell_history.insert(elements[i]->id);
        if(rt) {
            for (rtree_t::const_query_iterator it = rtree.qbegin(index::intersects(elements[i]->envelope)) ; it != rtree.qend() ; ++it) {
                size_t j = it->second;
                
                if (cell_history.find(element_Id[j].id) != cell_history.end()) {
                    continue;
                }
	            else if((elements[i]->fixed && element_Id[j].fixed)  || (elements[i]->layer != element_Id[j].layer) ) {
                    continue;
                } else {
                    double oa = 0.0;
	            //double center_dist = abs(nodes[i]->xBy2 - nodeId[j].xBy2) + abs(nodes[i]->yBy2 - nodeId[j].yBy2);
                    
                    std::deque<polygon> intersect_poly;
                
                    boost::geometry::intersection(elements[i]->poly, element_Id[j].poly, intersect_poly);

                    BOOST_FOREACH(polygon const& p, intersect_poly) {
                        oa +=  bg::area(p);
                    }
                    overlap +=  pow(oa,2) + oa; //+ 1.0/(1.0 + center_dist);
	  //overlap += oa + 1.0/(1.0 + center_dist);
	            // overlap_x2 += pow(oa,2);
	            // overlap_x += oa;
        //   if (boost::iequals(nodes[i]->name, logger.micro_name) || boost::iequals(nodeId[j].name, logger.micro_name)) {
        //      micro_cdist  += 1.0/(1.0+center_dist);
	    //  micro_overlap_x2 += pow(oa,2);
	    //  overlap_x += oa;
          }
        }
      }
        else{
            for(size_t j = 0; j < element_Id.size(); j++) {
                if (cell_history.find(element_Id[j].id) != cell_history.end()) {
                    continue;
                }
                else if((elements[i]->fixed && element_Id[j].fixed) || (elements[i]->layer != element_Id[j].layer)) {
                    continue;
                } else {
                    double oa = 0.0;
                //double center_dist = abs(elements[i]->center_x - element_Id[j].center_x) + abs(elements[i]->center_y - element_Id[j].center_y);
    
                    std::deque<polygon> intersect_poly;
                    boost::geometry::intersection(elements[i]->poly, element_Id[j].poly, intersect_poly);

                    BOOST_FOREACH(polygon const& p, intersect_poly) {
                        oa +=  bg::area(p);
                    }
                    overlap +=  pow(oa,2) + oa;// + 1.0/(1.0+center_dist);
        //overlap += oa + 1.0/(1.0+center_dist); 
            //}
                }
            }
        //cout <<"nonrt: " << overlap << endl;
        //}
        }
    }
    return overlap;
}
   

double placer::wirelength_partial(vector < element* > &elements, map<int, vector<pPin> > &netToCell){
    vector < pPin > net;
    vector < int > ::iterator itNet;
    vector < pPin > ::iterator itCellList;
    vector < element *>::iterator itElement;
    unordered_set < int > net_history;

    double xVal, yVal, wireLength= 0;
    //double hr, rudy = 0;
    for (itElement = elements.begin(); itElement != elements.end(); ++itElement) {
        for (itNet = (*itElement)->Netlist.begin(); itNet != (*itElement)->Netlist.end(); ++itNet) {
        if (net_history.find(*itNet) == net_history.end()) {
            net_history.insert(*itNet);
        } else {
            continue;
        }
        net = netToCell.find(*itNet)->second;
        // ignore "GND" etc.
        // if(net.size() > 10){
        //     continue;
        // }
        double minXW = mMaxX, minYW = mMaxY, maxXW = mMinX, maxYW = mMinY;
        for (itCellList = net.begin(); itCellList != net.end(); ++itCellList) {
            if(itCellList->name == "") {
            continue;
            }
            int orient = element_Id[itCellList->id].orientation;
            xVal = element_Id[itCellList->id].center_x;
            yVal = element_Id[itCellList->id].center_y;

            if(orient == 0) { // 0
            xVal = xVal + itCellList->x_offset;
            yVal = yVal + itCellList->y_offset;
            } else if(orient == 2) { // 90
            xVal = xVal + itCellList->y_offset;
            yVal = yVal - itCellList->x_offset;
            } else if(orient == 4) { // 180
            xVal = xVal - itCellList->x_offset;
            yVal = yVal - itCellList->y_offset;
            } else if(orient == 6) { // 270
            xVal = xVal - itCellList->y_offset;
            yVal = yVal + itCellList->x_offset;
            } else {
            double rad = (orient*45.0*PI/180.0);
            xVal = itCellList->y_offset*sin(rad) + itCellList->x_offset*cos(rad) + xVal;
            yVal = itCellList->y_offset*cos(rad) - itCellList->x_offset*sin(rad) + yVal;
            }

            if (xVal < minXW)
            minXW = xVal;
            if (xVal > maxXW)
            maxXW = xVal;
            if (yVal < minYW)
            minYW = yVal;
            if (yVal > maxYW)
            maxYW = yVal;
        }
        wireLength += (abs((maxXW - minXW)) + abs((maxYW - minYW)));
        //add rudy;
        // int area = ceil(abs((maxXW - minXW))) * ceil(abs((maxYW - minYW)));
        // rudy += wireLength / (max((maxXW - minXW)*(maxYW - minYW),1.0));
        // hr = wireLength + exp(rudy - 1);
        }
        
    }

    
    return wireLength;
    //return hr;
}


bool placer::check_move(double prevCost, double newCost){
    double delCost = 0;
    boost::uniform_real<> uni_dist(0,1);
    boost::variate_generator<boost::mt19937&, boost::uniform_real<> > uni(rng, uni_dist);
    double prob = uni();
    if(debug > 1) {
        cout << "new cost: " << newCost << endl;
    }
    delCost = newCost - prevCost;
    //cout << delCost << " " << Temperature << " " << prob << " " << exp(-delCost/Temperature) << " " << -delCost << " " << Temperature << " " << -delCost/Temperature << " " << prob << " " <<(prob <= (exp(-delCost/Temperature))) << endl;
    errno = 0;
    double p_thresh = exp(-delCost/Temperature);
    //logger.update_accept_probs(-delCost/Temperature);
    if (errno == ERANGE) {
        //cout << "[ERR]" << " overflow: " << -delCost/Temperature << endl;
        p_thresh = 0.0;
    } 
    if (delCost <= 0 || prob <= p_thresh) {
        prevCost = newCost;
        return true;
    } else {
        return false;
    }
}

vector<double> placer::initiate_move(vector<double> current_cost_vec, map<int, vector<pPin> > &netToCell){
    double current_cost = current_cost_vec[0];
    double current_wl = current_cost_vec[1];
    double current_oa = current_cost_vec[2];
    double current_od = current_cost_vec[3];
    double prev_wl = 0.0;
    double prev_oa = 0.0;
    double prev_od = 0.0;
    int state = -1;

    if(debug > 1) {
        cout << "current_cost: " << current_cost << endl;
    }
    vector < element > ::iterator rand_element1;
    vector < element > ::iterator rand_element2;

    vector < element* > perturbed_elements;

    int r = 0;
    rand_element1 = random_element();
    while(rand_element1->terminal || rand_element1->name == "" || rand_element1->fixed) {
        rand_element1 = random_element();
    }
    perturbed_elements.push_back(&(*rand_element1));

    if(rt) {
        rtree.remove(std::make_pair(rand_element1->envelope, rand_element1->id));
    }
    double rand_element1_orig_x = rand_element1->xC;
    double rand_element1_orig_y = rand_element1->yC;
    double rand_element2_orig_x = 0.0;
    double rand_element2_orig_y = 0.0;

    boost::uniform_real<> uni_dist(0,1);
    boost::variate_generator<boost::mt19937&, boost::uniform_real<> >uni(rng, uni_dist);
    double i = uni();
    // action:swap
    if (i < swap_proba) { 
        state = 0;
        if(debug > 1) {
        cout << "swap" << endl;
        }
        rand_element2 = random_element();//TODO:change
        while(rand_element2->terminal || rand_element2->id == rand_element1->id || rand_element2->name == "" || rand_element2->fixed) {
            rand_element2 = random_element();
        }

        perturbed_elements.push_back(&(*rand_element2));

        //prevCost = cost_partial(perturbed_nodes,netToCell);
        prev_wl = wirelength_partial(perturbed_elements, netToCell);
        prev_oa = cell_overlap_partial(perturbed_elements);
        prev_od = order_partial(perturbed_elements, netToCell);
        if(rt) {
            rtree.remove(std::make_pair(rand_element2->envelope, rand_element2->id));
        }

        rand_element2_orig_x = rand_element2->xC;
        rand_element2_orig_y = rand_element2->yC;

        validate_move(*rand_element1, rand_element2_orig_x, rand_element2_orig_y);
        validate_move(*rand_element2, rand_element1_orig_x, rand_element1_orig_y);
        
        if(rt) {
            rtree.insert(std::make_pair(rand_element1->envelope, rand_element1->id));
            rtree.insert(std::make_pair(rand_element2->envelope, rand_element2->id));
        }
        
    }
    //action:shift
    else if(swap_proba <= i && i< shift_proba + swap_proba){ 
        state = 1;
        if(debug > 1){
            cout<< "shift" <<endl;
        }
        prev_wl = wirelength_partial(perturbed_elements, netToCell);
        prev_oa = cell_overlap_partial(perturbed_elements);
        prev_od = order_partial(perturbed_elements, netToCell);

        double sigma = rand_element1 -> sigma;
        double sigma_leftx = min(sigma, rand_element1->xC - mMinX);
        double sigma_rightx = min(sigma, mMaxX - rand_element1->xC - rand_element1->width);
        double sigma_downy = min(sigma, rand_element1->yC - mMinY);
        double sigma_upy = min(sigma, mMaxY - rand_element1->yC - rand_element1->height);
        
        boost::uniform_real<> nd(-1*sigma_leftx, sigma_rightx);
        boost::variate_generator<boost::mt19937&,
                                 boost::uniform_real<> > var_nor(rng, nd);

        boost::uniform_real<> ny(-1*sigma_downy, sigma_upy);
        boost::variate_generator<boost::mt19937&,
                                 boost::uniform_real<> > var_nory(rng, ny);

        //old
        // boost::uniform_real<> nd(-1*sigma,sigma);
        // boost::variate_generator<boost::mt19937&,
        //                      boost::uniform_real<> > var_nor(rng, nd);
        double dx = var_nor();
        //double dy = var_nor();
        double dy = var_nory();

        double rx = rand_element1_orig_x + dx;
        double ry = rand_element1_orig_y + dy;

        validate_move(*rand_element1, rx, ry);
        if(rt) {
            rtree.insert(std::make_pair(rand_element1->envelope, rand_element1->id));
        }
        }
    //action:rotate
    else if(shift_proba + swap_proba <= i && i< shift_proba + swap_proba + rotate_proba){
        state = 2;
        if(debug > 1){
             cout << "rotate" << endl;
        }
        prev_wl = wirelength_partial(perturbed_elements, netToCell);
        prev_oa = cell_overlap_partial(perturbed_elements);
        prev_od = order_partial(perturbed_elements, netToCell);

        if(rotate_flag == 0){
            boost::uniform_int<>uni_dist(0,3);
            boost::variate_generator<boost::mt19937&, boost::uniform_int<> > uni(rng, uni_dist);
            r = uni();
            r = r*2;
        } else {
            boost::uniform_int<> uni_dist(0,7);
            boost::variate_generator<boost::mt19937&, boost::uniform_int<> > uni(rng, uni_dist);
            r = uni();
            }
        rand_element1->setRotation(r);
        // bug1:宽超过PCB宽的旋转后会超出边界
        //validate_move(*rand_element1, rand_element1_orig_x, rand_element1_orig_y);

        validate_move(*rand_element1, rand_element1->xC, rand_element1->yC);
        if(rt) {
            rtree.insert(std::make_pair(rand_element1->envelope, rand_element1->id));
        }
        // if(rand_element1->width > (mMaxX-mMinX) || rand_element1->height > (mMaxY-mMinY)){
        //     rand_element1->setRotation(8-r);
        //     rand_element1->setPos(rand_element1_orig_x,rand_element1_orig_y);
        // }
        // else{
        //     validate_move(*rand_element1, rand_element1->xC, rand_element1->yC);
        // }
        
        }
    //action:layer change
    else{
        state = 3;
        if(debug > 1){
            cout << "layer change" << endl;
        }
        prev_wl = wirelength_partial(perturbed_elements, netToCell);
        prev_oa = cell_overlap_partial(perturbed_elements);
        prev_od = order_partial(perturbed_elements, netToCell);
        rand_element1->layerChange();
        }
        double transition_wl = wirelength_partial(perturbed_elements, netToCell);
        double transition_oa = cell_overlap_partial(perturbed_elements);
        double transition_od = order_partial(perturbed_elements, netToCell);

        double updated_wl = current_wl - prev_wl + transition_wl;
        double updated_oa = current_oa - prev_oa + transition_oa;
        double updated_order = current_od - prev_od + transition_od;
        double normalized_updated_wl  =  (updated_wl - wl_normalization.first) / (wl_normalization.second - wl_normalization.first);
        double normalized_updated_oa  =  (updated_oa - area_normalization.first) / (area_normalization.second - area_normalization.first);
        double normalized_updated_order = (updated_order - order_normalization.first) / (order_normalization.second - order_normalization.first);

        //double updated_cost = l1*normalized_updated_wl + 0.85*(1-l1)*normalized_updated_oa; //+ 0.15*(1-l1)*normalized_updated_rudy;
        double updated_cost = l1 * normalized_updated_wl + l_2 * normalized_updated_oa
                            + l_3*normalized_updated_order;
        // if (boost::iequals(rand_node1->name, logger.micro_name)) {
        //     double dcost = updated_cost - current_cost;
        //     double dhpwl = updated_wl - current_wl;
        //     double doverlap = updated_oa - current_oa;
        //     logger.update_micro_histories(dcost, dhpwl, doverlap, 0, rand_node1->sigma);
        // }

        vector <double> updated_cost_vec;
        updated_cost_vec.push_back(updated_cost);
        updated_cost_vec.push_back(updated_wl);
        updated_cost_vec.push_back(updated_oa);
        updated_cost_vec.push_back(updated_order);

        bool accept = check_move(current_cost, updated_cost);

        if(!accept){
            // AcceptRate = 1.0/500.0 *(499.0*AcceptRate);
            if(debug > 1){
                cout << "reject" << endl;
            }
            // overlap_x2 = 0.0;
            // overlap_x = 0.0;
            // cdist = 0.0;
            // micro_overlap_x2 = 0.0;
            // micro_overlap_x = 0.0;
            // micro_cdist = 0.0;
            
            //换回初始位置
            if(state == 0){
                if(rt) {
                    rtree.remove(std::make_pair(rand_element1->envelope, rand_element1->id));
                    rtree.remove(std::make_pair(rand_element2->envelope, rand_element2->id));
                }
                rand_element1->setPos(rand_element1_orig_x,rand_element1_orig_y);
                rand_element2->setPos(rand_element2_orig_x,rand_element2_orig_y);
                if(rt){
                    rtree.insert(std::make_pair(rand_element1->envelope, rand_element1->id));
                    rtree.insert(std::make_pair(rand_element2->envelope, rand_element2->id)); 
                }
            }
            else if(state == 1){
                if(rt) {
                    rtree.remove(std::make_pair(rand_element1->envelope, rand_element1->id));
                }
                rand_element1->setPos(rand_element1_orig_x,rand_element1_orig_y);
                if(rt){
                    rtree.insert(std::make_pair(rand_element1->envelope, rand_element1->id)); 
                }
            }
            else if(state == 2){
                if(rt) {
                    rtree.remove(std::make_pair(rand_element1->envelope, rand_element1->id));
                }
                rand_element1->setRotation(8-r);
                rand_element1->setPos(rand_element1_orig_x,rand_element1_orig_y);
                if(rt){
                    rtree.insert(std::make_pair(rand_element1->envelope, rand_element1->id)); 
                }
            }
            else if(state == 3){
                rand_element1->layerChange();
            }
            return current_cost_vec;
        }
        else{
            if(debug > 1){
                cout << "accept" << endl;
            }
        }
        // overlap_x2 = 0.0;
        // overlap_x  = 0.0;
        // cdist = 0.0;

        //AcceptRate = 1.0/500 *(499.0*AcceptRate + 1.0);

        return updated_cost_vec;
}


void placer::update_temperature(){
    vector < element > ::iterator elementit = element_Id.begin();
    // l1 = 0.98 * l1;
    // l_2 = 1 - l1;
    // l_4 = 0.125 * l1;
    // l_2 = 1 - l1 - l_4;
    //l_4 = 1.00005*l_4;
    l_2 = 1.02 * l_2;
    if (Temperature > 50e-3) {
        Temperature = (0.985) * Temperature;
        for (elementit = element_Id.begin(); elementit != element_Id.end(); ++elementit) {
            elementit->sigma = 0.9992 * elementit->sigma;
            //elementit->sigma =  max(0.985*elementit->sigma,3/4 * elementit->sigma);
        }
    } else if (Temperature > 10e-3) {
        Temperature = (0.9992) * Temperature;
        for (elementit = element_Id.begin(); elementit != element_Id.end(); ++elementit) {
            elementit->sigma = 0.9955 * elementit->sigma;
            //elementit->sigma =  max(0.9992*elementit->sigma,2/4 * elementit->sigma);
        }
    } else if (Temperature > 50e-4) {
        Temperature = (0.9955) * Temperature;
        for (elementit = element_Id.begin(); elementit != element_Id.end(); ++elementit) {
            elementit->sigma = 0.9965 * elementit->sigma;
            //elementit->sigma =  max(0.9955*elementit->sigma,1/4 * elementit->sigma);
        }
    } else if (Temperature > 10e-4) {
        Temperature = (0.9965) * Temperature;
        for (elementit = element_Id.begin(); elementit != element_Id.end(); ++elementit) {
            elementit->sigma = 0.985 * elementit->sigma;
            //elementit->sigma =  max(0.9965*elementit->sigma,2.0);
        }
    } else {
        if (Temperature > 10e-8) {
            Temperature = (0.885) * Temperature;
        } else {
            Temperature = 0.0000000001;
        }
        for (elementit = element_Id.begin(); elementit != element_Id.end(); ++elementit) {
            elementit->sigma =  max(0.855*elementit->sigma,4.0);
        }
    }
}

void placer::modified_lam_update(int i) {
  double T_update;
//   if(do_hplace){
//     int outer_loop_iter = (H.levels.size()-1) * outer_loop_iter;
//   }

  if ((double)i/(double)outer_loop_iter < 0.15){
    LamRate = base_lam + (1-base_lam) * pow(1000*(1-base_lam), -((double)i/(double)outer_loop_iter)/0.15);
  } else if (0.15 <= (double)i/(double)outer_loop_iter && (double)i/(double)outer_loop_iter <= 0.65) {
    LamRate = base_lam;
    //wl_normalization.second = wl_hist.back();
    //area_normalization.second = oa_hist.back();
  } else if (0.65 <= (double)i/(double)outer_loop_iter) {
    LamRate = base_lam * pow(1000*base_lam, -((double)i/(double)outer_loop_iter - 0.65)/0.35);
    //wl_normalization.second = wl_hist.back();
    //area_normalization.second = oa_hist.back();
  }

  if (AcceptRate > LamRate) {
    T_update = Temperature * lamtemp_update;
    sigma_update = max(0.99, log(Temperature)  / log(T_update));
    Temperature = T_update;
    //l1 = lambda_schedule*l1;
    l_2 = 1.02 * l_2;
    vector <element>::iterator elementit = element_Id.begin();
    for (elementit = element_Id.begin(); elementit != element_Id.end(); ++elementit) {
      elementit->sigma = max(sigma_update * elementit->sigma, 2.0);
    } 
  } else {
    T_update = Temperature / lamtemp_update;
    sigma_update = min(1.01, log(Temperature) / log(T_update));
    vector <element>::iterator elementit = element_Id.begin();
    for (elementit = element_Id.begin(); elementit != element_Id.end(); ++elementit) {
      elementit->sigma = max(sigma_update * elementit->sigma, 2.0);
    }
    Temperature = T_update;
    l_2 = 1.02 * l_2;
    //l1 = lambda_schedule*l1;
  }
}

double placer::stun(map<int, vector<pPin> > &netToCell){
    //vector <double> receiver;
    double E = cost(netToCell)[0];
    double E_0 = best_cost;
    double E_var = E - E_0;
    double gamma = E_var / 0.05;

    return exp( - E_var / gamma);
}

bool  placer::check_entrapment() {
    double alpha;
    // (1) First define X_t
    double mean_cost = accumulate( cost_hist.begin(), cost_hist.end(), 0.0)/cost_hist.size(); 
    vector < double > X_t;
    int N  = cost_hist.size();
    for(int i=0; i<=N; i++){
      double x_t = 0.0;
      for(int j=0; j<=i; j++){
        x_t += cost_hist[j] - mean_cost;
      } 
      X_t.push_back(x_t);
    }
    int numL = 4;

    // (2a) split X_t into windows of length L for k L
    int n = 10;
    vector < double > log_F_L;
    vector < double > log_L;

    for(int i=0; i<numL; i++) {
      int size = (X_t.size() - 1) / n + 1;
      // create array of vectors to store the sub-vectors
      std::vector<double> vec[size];

      // each iteration of this loop process next set of n elements
      // and store it in a vector at k'th index in vec
      for (int k = 0; k < size; ++k) {
        // get range for next set of n elements
        auto start_itr = std::next(X_t.cbegin(), k*n);
        auto end_itr = std::next(X_t.cbegin(), k*n + n);

        // allocate memory for the sub-vector
        vec[k].resize(n);

        // code to handle the last sub-vector as it might
        // contain less elements
        if (k*n + n > X_t.size()) {
          end_itr = X_t.cend();
          vec[k].resize(X_t.size() - k*n);
        }

        // copy elements from the input range to the sub-vector
        std::copy(start_itr, end_itr, vec[k].begin());

        // (2b) LLS fit each segment of X_t and calculate RMSE 
        REAL m,b,r;
        int n_s = vec[k].size();

        if (n_s < 1) {
          continue;
        }

        std::vector<double> x(n_s);
        std::iota(x.begin(), x.end(), 1);
        int ret = linreg(n_s,x,vec[k],m,b,r);
        if(ret == 1) {
          cout << "L singular matrix" << endl;
        }
        //printf("INNER LOOP m=%g b=%g r=%g\n",m,b,r);
        //printf("INNER LOOP r=%g n_s=%g\n",log(r), log(n_s));
        log_F_L.push_back(log(r));
        log_L.push_back(log(n_s));
      }

      n+=10;
    }

    // (4) Estimate LLS slope alpha for log-log L - RMSE. Check  threshold  & return.
    REAL m,b,r;
    int n_s = log_L.size();
    int ret = linreg(n_s,log_L,log_F_L,m,b,r);
    if(ret == 1) {
      cout << "log-log singular matrix" << endl;
    }
    //printf("OUTER LOOP m=%g b=%g r=%g\n",m,b,r);

    alpha = m;

    if(alpha > entrapment_threshold) {
      return true;
    } else {
      return false;
    }
}

float placer::annealer(map<int, vector<pPin> > &netToCell, string initial_pl){
    Temperature = t_0;
    int num_components = 0;
    std::ofstream dataFile("temperature.txt");
    std::ofstream dataFile1("best_cost.txt");

    vector < element > ::iterator itElement;
    //writeNodesFile("./cache/nodes.nodes");
    cout << "calculating initial params..." << endl;
    initial_placement();
    initialize_params(netToCell);
    //element_Id = bestSol;
    // if (initial_pl != "") {
    //     readPlFile(initial_pl);
    // } else {
    //     random_initial_placement();
    // }
    if(ini_placemode != 0){
        initial_placement();
    }
    // wl_normalization.first = 0.0;
    vector <double> cost_vec;
    //cost_vec = cost(netToCell,-1);
    //cost_data1.push_back(cost_vec[5]);

    // cost_vec.push_back(cst);
    // cost_vec.push_back(initial_wl);
    // cost_vec.push_back(initial_oa);
    //cost_vec.push_back(initial_rudy);

    if(var){
        Temperature = initialize_temperature(netToCell);
    }
    int id = 0;

    if(rt) {
        rtree.clear();
        for (itElement = element_Id.begin(); itElement != element_Id.end(); ++itElement) {
            rtree.insert(std::make_pair(itElement -> envelope, itElement -> id));
            num_components += 1;
            id +=1;
        }
    } 
    else {
        for (itElement = element_Id.begin(); itElement != element_Id.end(); ++itElement) { 
            num_components += 1;
            id +=1;
        }
    }

    //sort(s_area.begin(),s_area.end());
    //int Q = s_area[floor(num_components * 0.75)];
    double Q = S_all/num_components;
    vector < element > ::iterator esigma;
    for (esigma = element_Id.begin(); esigma != element_Id.end(); ++esigma) { 
        //esigma -> sigma = 100* max(Q/(esigma->S),1.0);
        if (esigma->fixed){
            continue;
        }
        if(esigma->S <= Q){
            //esigma->sigma = 50;
            //esigma->sigma = 100;
            esigma->sigma = max(mMaxX-mMinX, mMaxY-mMinY);
        }
        else{
            //esigma->sigma = 50;
            //esigma->sigma = 100;
            esigma->sigma = max(mMaxX-mMinX, mMaxY-mMinY)/10;
        }
    }
    

    high_resolution_clock::time_point t1 = high_resolution_clock::now();
    long long int ii = 0; // outer loop iterator
    int i = 0; // inner loop iterator
    //int j = 0;// for state regression
    //double back_cost = 0.0;
    cout << "beginning optimization..." << endl;
    while (ii < outer_loop_iter) {
        i = inner_loop_iter*num_components;

        //back_cost = best_cost; 

        high_resolution_clock::time_point t2 = high_resolution_clock::now();
        duration<double> time_span = duration_cast< duration<double> >(t2 - t1);

        cout << "=====" << ii << "=====" << endl;
        cout << "iteration: " << ii << " time: " <<  time_span.count() << " (s)" << " updates/time: " <<  ii/time_span.count() << 
        " time remaining: " <<  time_span.count()/ii * (outer_loop_iter-ii) << " (s)" << " temperature: " << Temperature << " wl weight: " << l1 << " s samp: " << ssamp <<
        " sigma update: " << sigma_update << " acceptance rate: " << AcceptRate << " lam rate: " << 0 << " entraped: " << entraped << endl;
        //writePlFile("./cache/"+std::to_string( ii )+".pl");
        //writeRadFile("./cache/"+std::to_string( ii )+".rad");
        if (ii % 1 == 0) {
            cost_vec = cost(netToCell);
            if(rt) {
                rtree.clear();
                for (itElement = element_Id.begin(); itElement != element_Id.end(); ++itElement) {
                    rtree.insert(std::make_pair(itElement -> envelope, itElement -> id));
                }
            }
            cost_data1.push_back(cost_vec[4]);
        }
        // if(ii < 200){
        //     cost_vec = cost(netToCell);
        //     cost_data1.push_back(cost_vec[5]);
        // }
        // else if(ii % 50 == 0){
        //     cost_vec = cost(netToCell);
        //     cost_data1.push_back(cost_vec[5]);
        // }
        // cost_vec = cost(netToCell);
        // cost_data1.push_back(cost_vec[4]);
        while (i > 0) {
            // if(entraped){
            //     stun(netToCell);
            // }
            cost_vec = initiate_move(cost_vec, netToCell);
            //cost_hist.push_back(cost_vec[0]);
            //cst = cost_vec[0];
            i -= 1;
            // cost_data.push_back(cost_vec[0]);
            // cost_data1.push_back(cost_vec[1]+cost_vec[2]);
        }
        // entraped = false;
        // if (ii > 1 && ii % 20 == 0) {
        //     if(check_entrapment()) {
        //         // local min
        //         entraped = true;
        //     } else {
        //         entraped = false;
        // }
        // }
        
        if(eps > 0 && abs(cost_hist.end()[-1] - cost_hist.end()[-2]) < eps) {
            break;
        }
        if(lam){
            modified_lam_update(ii);
        }
        else{
            update_temperature();
        }
        ii += 1;

        iii += 1;
    }

    element_Id = bestSol;
    if(rt) {
        rtree.clear();
        for (itElement = element_Id.begin(); itElement != element_Id.end(); ++itElement) {
            rtree.insert(std::make_pair(itElement -> envelope, itElement -> id));
        }
    }


    vector < element > ::iterator elementit;
    for (elementit = element_Id.begin(); elementit != element_Id.end(); ++elementit) {
        //elementit->sigma =  4.0;
        elementit->sigma = min(1/2 * elementit->width,1/2 * elementit->height);
    }

    i = inner_loop_iter * num_components * 10;// * 100;//*1000 for convengence
    //Temperature = 10e-20;
    Temperature = 10e-60;
    // cst = cost(netToCell);

    //int n_oa = 100 * num_components;
    // while( (n_oa > 0) && (i > 0) ){
    //     overlap_soln();
    //     cost_vec = cost(netToCell);
    //     cost_data1.push_back(cost_vec[5]);
    //     //cout << "sigma: "<< element_Id.begin()->sigma <<endl;     
    //     n_oa -= 1;
    // }

    //int j_end = 0; //for overlap
    //element_Id = bestSol;

    element_Id = bestSol;
    //l1 = 0.1;
    
    l_3 = l1/2;
    l1 = l_3;
    begin_ali = true;
    update_cost = true;
    cost(netToCell);
    update_cost = false;

    //only shift and rotate
    swap_proba = 0.0;
    rotate_proba = 0.4;
    
    //best_cost = l1 * Hpwl(netToCell) + l_3 * order(netToCell);
    cout<<"=======Before Fine-tuning======="<<endl;
    cout << "Solution: " << "overlap: " << best_overlap << " Hpwl: " << best_wl 
    <<" Order: "<< best_od <<" Best_cost: "<< best_cost <<endl;
    cout<<"=======After Fine-tuning======="<<endl;
    //high_resolution_clock::time_point t3 = high_resolution_clock::now();
    
    while (i > 0) {
        cost_vec = initiate_move(cost_vec, netToCell);
        cost_vec = cost(netToCell);
        //cst = cost_vec[0];
        // if ((i % 5 == 0)) {
        //     //cst = cost(netToCell);
        //     cost_vec = cost(netToCell);
        //     //cost_data1.push_back(cost_vec[5]);
        // }
        i -= 1;    
    }
    //high_resolution_clock::time_point t4 = high_resolution_clock::now();
    //duration<double> time_span = duration_cast< duration<double> >(t4 - t3);
    //cout<<"Fine_tuning:  "<<time_span.count()<<"(s)"<<endl;
    for(auto x : cost_data){
        dataFile << x <<'\n';
    }

    for(auto y : cost_data1){
        dataFile1 << y <<'\n';
    }
    //dataFile << cost_data[0];
    //dataFile.close();
    return cost(netToCell)[0];
}