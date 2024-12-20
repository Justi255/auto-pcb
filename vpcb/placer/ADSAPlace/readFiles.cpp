
#include "readFiles.hpp"

using namespace std;
using boost::is_any_of;

/**
readNodesFile
read nodes file
*/
int readNodesFile(string fname) {
  fstream file;
  string buf;
  int i = 0;
  vector < string > strVec;
  int terminal = 2;
  int idx = 0;

  file.open(fname, ios:: in );
  while (getline(file, buf)) {
    i++;
    if (i > 7) {
      boost::trim(buf);
      boost::algorithm::split(strVec, buf, is_any_of("\t, "), boost::token_compress_on);
      if (strVec[0] == "" || strVec[0] == " "){
        continue;
      }
      element n;

      if (strVec.size() > 3 && (strVec[3] == "terminal" || strVec[3] == "terminal_NI")) {
        terminal = 1;
      } else {
        terminal = 0;
      }
      n.setParameter(strVec[0], atof(strVec[1].c_str()), atof(strVec[2].c_str()), terminal, idx);
      element_Id.push_back(n);
      name2id.insert(pair < string, int > (strVec[0], idx));
      idx += 1;
    }
  }
  file.close();
  return 0;
}

/**
readShapesFile
read shapes file
*/
int readShapesFile(string fname) {
  fstream file;
  string buf;
  int i = 0;
  vector < string > strVec;

  file.open(fname, ios:: in );
  while (getline(file, buf)) {
    i++;
    if (i > 7) {
      boost::trim(buf);
      boost::algorithm::split(strVec, buf, is_any_of("\t,  "), boost::token_compress_on);
      if (strVec[0] == "" || strVec[0] == " "){
        continue;
      }
      strVec.erase(strVec.begin());
      element_Id[name2id[strVec[0]]].setParameterShapes(boost::algorithm::join(strVec,""));
    }
  }
  file.close();
  return 0;
}

/**
readWtsFile
read weights file
*/
int readWtsFile(string fname) {
  fstream file;
  string buf;
  int i = 0;
  vector < string > strVec;
  map < string, element > ::iterator itr;

  file.open(fname, ios:: in );
  while (getline(file, buf)) {
    i++;
    boost::trim(buf);
    if (i > 5) {
      boost::algorithm::split(strVec, buf, is_any_of("\t,  "), boost::token_compress_on);
      element_Id[name2id[strVec[1]]].setParameterWts(atof(strVec[2].c_str()));
    }
  }
  file.close();
  return 0;
}

/**
readPlFile
read placement file
*/
int readPlFile(string fname) {
  fstream file;
  string buf;
  int i = 0;
  int fixed = 0;
  vector < string > strVec;

  file.open(fname, ios:: in );
  while (getline(file, buf)) {
    i++;
    if (i > 4) {
      boost::trim(buf);
      boost::algorithm::split(strVec, buf, is_any_of("\t,  "), boost::token_compress_on);
      if (strVec[0] == "" || strVec[0] == " "){
        continue;
      }
      if (strVec.size() > 5 && (strVec[5] == "/FIXED" || strVec[5] == "/FIXED_NI")) {
        fixed = 1;
      } else {
        fixed = 0;
      }
      element_Id[name2id[strVec[0]]].setParameterPl(atof(strVec[1].c_str()), atof(strVec[2].c_str()), strVec[4], fixed);
    }
  }
  file.close();
  return 0;
}

/**
readNetsFile
read nets file
*/
map<int, vector<pPin> > readNetsFile(string fname) {
  fstream file;
  string buf;
  int i = 0, a = 0, j = 0, NetId = 1;
  vector < string > strVec;
  map<int, vector<pPin> > netToCell;

  string pat = "NetDegree : ";
  string Out;

  file.open(fname, ios:: in );
  while (getline(file, buf)) {
    i++;
    if (i > 7) {
      boost::trim_all(buf);

      std::size_t found = buf.find(pat);
      if(found!=std::string::npos) {
        std::vector<std::string> results;
        boost::split(results, buf, [](char c){return c == ' ';});
        //Out = buf.substr(buf.rfind(" ") + 1);
        Out = results.at(2);
      } else {
        continue;
      }
      a = stoi(Out);
      vector < string > strTemp;
      vector < pPin > pinTemp;
      for (j = 0; j < a; j++) {
        getline(file, buf);
        boost::trim_all(buf);
        boost::algorithm::split(strVec, buf, is_any_of("\t,  "), boost::token_compress_on);
        strTemp.push_back(strVec[0]);
        element_Id[name2id[strVec[0]]].setNetList(NetId);
        pPin p;
        if(strVec.size() > 2) {
          p.set_params(strVec[0].c_str(), atof(strVec[3].c_str()), atof(strVec[4].c_str()), element_Id[name2id[strVec[0]]].id);
        } else {
          p.set_params(strVec[0].c_str(), 0, 0, -1);
        }
        pinTemp.push_back(p);
      }
      netToCell.insert(pair < int, vector< pPin > > (NetId, pinTemp));
      NetId++;
    }
  }
  return netToCell;
}

/**
readConstriantsFile
read constraints file
*/
map<int, vector<pPin> > readConstraintsFile(string fname, map<int, vector<pPin>> & netToCell, kicadPcbDataBase& mdb) {
  fstream file;
  string buf;
  int i = 0, a = 0, j = 0, NetId = netToCell.size();
  vector < string > strVec;
  //num_nets = netToCell.size();

  string Out;

  file.open(fname, ios:: in );
  while (getline(file, buf)) {
    i++;

      vector < string > strTemp;
      vector < pPin > pinTemp;

	getline(file, buf);
	boost::trim_all(buf);
	boost::algorithm::split(strVec, buf, is_any_of("(, (,) (,))"), boost::token_compress_on);

	strTemp.push_back(strVec[2]);
	element_Id[name2id[strVec[2]]].setNetList(NetId);

	pPin p;
	// todo pads
	//p.set_params(strVec[1].c_str(), atof(strVec[3].c_str()), atof(strVec[4].c_str()), nodeId[name2id[strVec[0]]].idx);
	p.set_params(strVec[2].c_str(), 0, 0, -1);
	pinTemp.push_back(p);

	pPin p2;
	p.set_params(strVec[5].c_str(), 0, 0, -1);
	pinTemp.push_back(p2);

      netToCell.insert(pair < int, vector< pPin > > (NetId, pinTemp));
      NetId++;
  }
  return netToCell;
}

/**
readClstFile
read cluster file
*/
int readClstFile(string fname) {
  fstream file;
  string buf;
  int i = 0;
  vector < string > strVec;
  int value = 2;
  int idx = 0;

  int num_levels = 0;
  vector < int > num_modules;
  string Out = ""; // tmp string

  file.open(fname, ios:: in);
  while (getline(file, buf)) {
    i++;
    boost::trim(buf);
    boost::algorithm::split(strVec, buf, is_any_of("\t, "), boost::token_compress_on);
    if (i == 1) {
        std::vector<std::string> results;
        boost::split(results, buf, [](char c){return c == ' ';});
        num_levels = atoi(results.at(1).c_str());
    } else if (i == 2) {
        std::vector<std::string> results;
        boost::split(results, buf, [](char c){return c == ' ';});
        results.erase (results.begin());
        for (auto &res : results) {
          num_modules.push_back(atoi(res.c_str()));
        }
        // INIT HIERARCHY
        //H.init_hierarchy(num_levels, num_modules);
    } else {
      idx += 1;
      
      std::vector<std::string> results;
      boost::split(results, buf, [](char c){return c == '\t';});
      string cell_name = results[0];
      results.erase (results.begin());

      vector <int> cluster_id_vec;
      for (auto &res : results) {
        // insert cells into hierarchy
        cluster_id_vec.push_back(atoi(res.c_str()));
      }
      //H.insert_cell(name2id[strVec[0]], cluster_id_vec, H.root, 0);
    }
  }

  file.close();
  return 0;
}

/**
writePlFile
read placement file
*/
int writePlFile(string fname) {
  vector < string > strVec;
  fstream file;
  string buf;
  ofstream myfile (fname);
  if (myfile.is_open()) {
    myfile << "\n\n\n\n";
    vector <element> ::iterator itNode;

    // print components
    for (itNode = element_Id.begin(); itNode != element_Id.end(); ++itNode) {
      if(!itNode->terminal) {
        myfile << itNode->name << " " << itNode->xC << " " << itNode->yC <<  " : " << itNode->orient2str(itNode->orientation) << " " << itNode->layer;
        if (itNode->fixed) {
          myfile << " /FIXED_NI\n";
        } else {
          myfile << "\n";
        }
      }
    }

    myfile << "\n";
    // print terminals
    for (itNode = element_Id.begin(); itNode != element_Id.end(); ++itNode) {
      if(itNode->terminal) {
        myfile << itNode->name << " " << itNode->xC << " " << itNode->yC << " : " << itNode->orient2str(itNode->orientation) << " " << itNode->layer;
        myfile << " /FIXED_NI\n";
      }
    }
    myfile.close();
    return 0;
  } else{ cout << "[ERR] Unable to open cache dir" <<endl; return 1;}
}

int writeRadFile(string fname) {
    fstream file;
    string buf;
    ofstream myfile (fname);
    myfile << "\n\n\n\n";
    vector < element > ::iterator itNode;
    if (myfile.is_open()) {
        for (itNode = element_Id.begin(); itNode != element_Id.end(); ++itNode) {
            myfile << itNode->name << " " << itNode->sigma << "\n";
        }
    }
    myfile.close();
    return 0;
}

/**
writeNodesFile
read nodes (modules) file
*/
int writeNodesFile(string fname) {
  vector < string > strVec;
  fstream file;
  string buf;
  ofstream myfile (fname);
  if (myfile.is_open()) {
    myfile << "\n\n\n\n";
    vector <element> ::iterator itNode;

    // print components
    for (itNode = element_Id.begin(); itNode != element_Id.end(); ++itNode) {
      if(!itNode->terminal) {
        myfile << itNode->name << " " << itNode->width << " " << itNode->height << "\n";
      }
    }

    myfile.close();
    return 0;
  } else{ cout << "[ERR] Unable to open cache dir" <<endl; return 1;}
}

int writeFlippedFile(string fname) {
    fstream file;
    string buf;
    ofstream myfile (fname);

    vector < element > ::iterator itModule;
    if (myfile.is_open()) {
        for (itModule = element_Id.begin(); itModule != element_Id.end(); ++itModule) {
            if (itModule->flipped == 1) {
                myfile << itModule->name << "\n";
            }
        }
    }
    myfile.close();
    return 0;
}
