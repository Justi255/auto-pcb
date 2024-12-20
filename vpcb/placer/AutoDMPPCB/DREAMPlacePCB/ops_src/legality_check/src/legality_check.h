/**
 * @file   legality_check.h
 * @author Yibo Lin
 * @date   Oct 2018
 */

#ifndef DREAMPLACE_LEGALITY_CHECK_H
#define DREAMPLACE_LEGALITY_CHECK_H

#include <algorithm>
#include <cassert>
#include <iostream>
#include <vector>
#include "utility/src/utils.h"
#include "utility/src/defs.h"

DREAMPLACE_BEGIN_NAMESPACE

/// compare nodes with x center
/// resolve ambiguity by index
template <typename T>
struct CompareByNodeXCenter {
  const T* x;
  const T* node_size_x;

  CompareByNodeXCenter(const T* xx, const T* size_x)
      : x(xx), node_size_x(size_x) {}

  bool operator()(int i, int j) const {
    T xc1 = x[i] + node_size_x[i] / 2;
    T xc2 = x[j] + node_size_x[j] / 2;
    return (xc1 < xc2) || (xc1 == xc2 && i < j);
  }
};

template <typename T>
bool boundaryCheck(const T* x, const T* y, const T* node_size_x,
                   const T* node_size_y, const T scale_factor, T xl, T yl, T xh, T yh,
                   const int num_movable_nodes) {
  // use scale factor to control the precision
  T precision = (scale_factor == 1.0) ? 1e-6 : scale_factor * 0.1;
  bool legal_flag = true;
  // check node within boundary
  for (int i = 0; i < num_movable_nodes; ++i) {
    T node_xl = x[i];
    T node_yl = y[i];
    T node_xh = node_xl + node_size_x[i];
    T node_yh = node_yl + node_size_y[i];
    if (node_xl + precision < xl || node_xh > xh + precision || node_yl + precision < yl || node_yh > yh + precision) {
      dreamplacePrint(kDEBUG, "node %d (%g, %g, %g, %g) out of boundary\n", i,
                      node_xl, node_yl, node_xh, node_yh);
      legal_flag = false;
    }
  }
  return legal_flag;
}

template <typename T>
bool overlapCheck(const T* node_size_x, const T* node_size_y, const T* x,
                  const T* y, T site_width, T row_height, T scale_factor, T xl, T yl, T xh,
                  T yh, const int num_nodes, const int num_movable_nodes) {
  bool legal_flag = true;

  // general to node and fixed boxes
  auto getXL = [&](int id) { return x[id]; };
  auto getYL = [&](int id) { return y[id]; };
  auto getXH = [&](int id) { return x[id] + node_size_x[id]; };
  auto getYH = [&](int id) { return y[id] + node_size_y[id]; };

  auto checkOverlap2Nodes = [&](int node_id1, T xl1, T yl1, T xh1, T yh1, 
                                int node_id2, T xl2, T yl2, T xh2, T yh2) {
    if (std::min(xh1, xh2) > std::max(xl1, xl2) &&
        std::min(yh1, yh2) > std::max(yl1, yl2)) {
      dreamplacePrint(kERROR,
                      "macro %d (%g, %g, %g, %g) overlaps with macro %d "
                      "(%g, %g, %g, %g) fixed: %d\n",
                      node_id1, xl1, yl1, xh1, yh1, node_id2, xl2, yl2, xh2,
                      yh2, (int)(node_id2 >= num_movable_nodes));
      return true;
    }
    return false;
  };

  // check overlap
  for (unsigned int i = 0; i < num_nodes; ++i) {
    for (unsigned int j = i + 1; j < num_nodes; ++j) {
      if (i < num_movable_nodes ||
          j < num_movable_nodes) // ignore two fixed nodes
      {
        T xl1 = getXL(i);
        T yl1 = getYL(i);
        T xh1 = getXH(i);
        T yh1 = getYH(i);
        T xl2 = getXL(j);
        T yl2 = getYL(j);
        T xh2 = getXH(j);
        T yh2 = getYH(j);

        // detect overlap
        bool overlap = checkOverlap2Nodes(i, xl1, yl1, xh1, yh1,
                                          j, xl2, yl2, xh2, yh2);
        if (overlap) {
          dreamplacePrint(
              kERROR,
              "overlap node %d (%g, %g, %g, %g) with "
              "node %d (%g, %g, %g, %g)\n",
              i, xl1, yl1, xh1, yh1,
              j, xl2, yl2, xh2, yh2);
          legal_flag = false;
        }
      }
    }
  }

  return legal_flag;
}

template <typename T>
bool legalityCheckKernelCPU(const T* x, const T* y, const T* node_size_x,
                            const T* node_size_y, const T* flat_region_boxes,
                            const int* flat_region_boxes_start,
                            const int* node2fence_region_map, T xl, T yl, T xh,
                            T yh, T site_width, T row_height, T scale_factor,
                            const int num_nodes,  ///< movable and fixed cells
                            const int num_movable_nodes,
                            const int num_regions) {
  bool legal_flag = true;
  fflush(stdout);

  // check node within boundary
  if (!boundaryCheck(x, y, node_size_x, node_size_y, scale_factor, xl, yl, xh, yh,
                     num_movable_nodes)) {
    legal_flag = false;
  }

  if (!overlapCheck(node_size_x, node_size_y, x, y, site_width, row_height, scale_factor,
                    xl, yl, xh, yh, num_nodes, num_movable_nodes)) {
    legal_flag = false;
  }

  return legal_flag;
}

template <typename T>
bool legalityCheckSiteMapKernelCPU(const T* init_x, const T* init_y,
                                   const T* node_size_x, const T* node_size_y,
                                   const T* x, const T* y, T xl, T yl, T xh,
                                   T yh, T site_width, T row_height,
                                   T scale_factor, const int num_nodes,
                                   const int num_movable_nodes) {
  int num_rows = ceilDiv(yh - yl, row_height);
  int num_sites = ceilDiv(xh - xl, site_width);
  std::vector<std::vector<unsigned char> > site_map(
      num_rows, std::vector<unsigned char>(num_sites, 0));

  // fixed macros
  for (int i = num_movable_nodes; i < num_nodes; ++i) {
    T node_xl = x[i];
    T node_yl = y[i];
    T node_xh = node_xl + node_size_x[i];
    T node_yh = node_yl + node_size_y[i];

    int idxl = floorDiv(node_xl - xl, site_width);
    int idxh = ceilDiv(node_xh - xl, site_width);
    int idyl = floorDiv(node_yl - yl, row_height);
    int idyh = ceilDiv(node_yh - yl, row_height);
    idxl = std::max(idxl, 0);
    idxh = std::min(idxh, num_sites);
    idyl = std::max(idyl, 0);
    idyh = std::min(idyh, num_rows);

    for (int iy = idyl; iy < idyh; ++iy) {
      for (int ix = idxl; ix < idxh; ++ix) {
        T site_xl = xl + ix * site_width;
        T site_xh = site_xl + site_width;
        T site_yl = yl + iy * row_height;
        T site_yh = site_yl + row_height;

        if (node_xl < site_xh && node_xh > site_xl && node_yl < site_yh &&
            node_yh > site_yl)  // overlap
        {
          site_map[iy][ix] = 255;
        }
      }
    }
  }

  bool legal_flag = true;
  // movable cells
  for (int i = 0; i < num_movable_nodes; ++i) {
    T node_xl = x[i];
    T node_yl = y[i];
    T node_xh = node_xl + node_size_x[i];
    T node_yh = node_yl + node_size_y[i];

    int idxl = floorDiv(node_xl - xl, site_width);
    int idxh = ceilDiv(node_xh - xl, site_width);
    int idyl = floorDiv(node_yl - yl, row_height);
    int idyh = ceilDiv(node_yh - yl, row_height);
    idxl = std::max(idxl, 0);
    idxh = std::min(idxh, num_sites);
    idyl = std::max(idyl, 0);
    idyh = std::min(idyh, num_rows);

    for (int iy = idyl; iy < idyh; ++iy) {
      for (int ix = idxl; ix < idxh; ++ix) {
        T site_xl = xl + ix * site_width;
        T site_xh = site_xl + site_width;
        T site_yl = yl + iy * row_height;
        T site_yh = site_yl + row_height;

        if (node_xl < site_xh && node_xh > site_xl && node_yl < site_yh &&
            node_yh > site_yl)  // overlap
        {
          if (site_map[iy][ix]) {
            dreamplacePrint(kERROR,
                            "detect overlap at site (%g, %g, %g, %g) for node "
                            "%d (%g, %g, %g, %g)\n",
                            site_xl, site_yl, site_xh, site_yh, i, node_xl,
                            node_yl, node_xh, node_yh);
            legal_flag = false;
          }
          site_map[iy][ix] += 1;
        }
      }
    }
  }

  return legal_flag;
}

DREAMPLACE_END_NAMESPACE

#endif
