package app.freerouting.geometry.planar;

import app.freerouting.datastructures.Stoppable;

import java.io.Serializable;
import java.util.Arrays;
import java.util.Collection;
import java.util.Iterator;
import java.util.LinkedList;

/**
 * A PolylineArea is an Area, where the outside border curve and the hole borders consist of
 * straight lines.
 */
public class PolylineArea implements Area, Serializable {

  final PolylineShape border_shape;
  final PolylineShape[] hole_arr;
  private transient TileShape[] precalculated_convex_pieces;

  /** Creates a new instance of PolylineShapeWithHoles */
  public PolylineArea(PolylineShape p_border_shape, PolylineShape[] p_hole_arr) {
    border_shape = p_border_shape;
    hole_arr = p_hole_arr;
  }

  private static void cutout_hole_piece(
      TileShape p_divide_piece, TileShape p_hole_piece, Collection<TileShape> p_result_pieces) {
    TileShape[] result_pieces = p_divide_piece.cutout(p_hole_piece);
    for (int i = 0; i < result_pieces.length; ++i) {
      TileShape curr_piece = result_pieces[i];
      if (curr_piece.dimension() == 2) {
        p_result_pieces.add(curr_piece);
      }
    }
  }

  @Override
  public int dimension() {
    return border_shape.dimension();
  }

  @Override
  public boolean is_bounded() {
    return border_shape.is_bounded();
  }

  @Override
  public boolean is_empty() {
    return border_shape.is_empty();
  }

  @Override
  public boolean is_contained_in(IntBox p_box) {
    return border_shape.is_contained_in(p_box);
  }

  @Override
  public PolylineShape get_border() {
    return border_shape;
  }

  @Override
  public PolylineShape[] get_holes() {
    return hole_arr;
  }

  @Override
  public IntBox bounding_box() {
    return border_shape.bounding_box();
  }

  @Override
  public IntOctagon bounding_octagon() {
    return border_shape.bounding_octagon();
  }

  @Override
  public boolean contains(FloatPoint p_point) {
    if (!border_shape.contains(p_point)) {
      return false;
    }
    for (int i = 0; i < hole_arr.length; ++i) {
      if (hole_arr[i].contains(p_point)) {
        return false;
      }
    }
    return true;
  }

  @Override
  public boolean contains(Point p_point) {
    if (!border_shape.contains(p_point)) {
      return false;
    }
    for (int i = 0; i < hole_arr.length; ++i) {
      if (hole_arr[i].contains_inside(p_point)) {
        return false;
      }
    }
    return true;
  }

  @Override
  public FloatPoint nearest_point_approx(FloatPoint p_from_point) {
    double min_dist = Double.MAX_VALUE;
    FloatPoint result = null;
    TileShape[] convex_shapes = split_to_convex();
    for (int i = 0; i < convex_shapes.length; ++i) {
      FloatPoint curr_nearest_point = convex_shapes[i].nearest_point_approx(p_from_point);
      double curr_dist = curr_nearest_point.distance_square(p_from_point);
      if (curr_dist < min_dist) {
        min_dist = curr_dist;
        result = curr_nearest_point;
      }
    }
    return result;
  }

  @Override
  public PolylineArea translate_by(Vector p_vector) {
    if (p_vector.equals(Vector.ZERO)) {
      return this;
    }
    PolylineShape translated_border = border_shape.translate_by(p_vector);
    PolylineShape[] translated_holes = new PolylineShape[hole_arr.length];
    for (int i = 0; i < hole_arr.length; ++i) {
      translated_holes[i] = hole_arr[i].translate_by(p_vector);
    }
    return new PolylineArea(translated_border, translated_holes);
  }

  @Override
  public FloatPoint[] corner_approx_arr() {
    int corner_count = border_shape.border_line_count();
    for (int i = 0; i < hole_arr.length; ++i) {
      corner_count += hole_arr[i].border_line_count();
    }
    FloatPoint[] result = new FloatPoint[corner_count];
    FloatPoint[] curr_corner_arr = border_shape.corner_approx_arr();
    System.arraycopy(curr_corner_arr, 0, result, 0, curr_corner_arr.length);
    int dest_pos = curr_corner_arr.length;
    for (int i = 0; i < hole_arr.length; ++i) {
      curr_corner_arr = hole_arr[i].corner_approx_arr();
      System.arraycopy(curr_corner_arr, 0, result, dest_pos, curr_corner_arr.length);
      dest_pos += curr_corner_arr.length;
    }
    return result;
  }

  /**
   * Splits this polygon shape with holes into convex pieces. The result is not exact, because
   * rounded intersections of lines are used in the result pieces. It can be made exact, if
   * Polylines are returned instead of Polygons, so that no intersection points are needed in the
   * result.
   */
  @Override
  public TileShape[] split_to_convex() {
    return split_to_convex(null);
  }

  /**
   * Splits this polygon shape with holes into convex pieces. The result is not exact, because
   * rounded intersections of lines are used in the result pieces. It can be made exact, if
   * Polylines are returned instead of Polygons, so that no intersection points are needed in the
   * result. If p_stoppable_thread != null, this function can be interrupted.
   */
  public TileShape[] split_to_convex(Stoppable p_stoppable_thread) {
    if (precalculated_convex_pieces == null) {
      TileShape[] convex_border_pieces = border_shape.split_to_convex();
      if (convex_border_pieces == null) {
        // split failed
        return null;
      }
      Collection<TileShape> curr_piece_list = new LinkedList<>(Arrays.asList(convex_border_pieces));
      for (int i = 0; i < hole_arr.length; ++i) {
        if (hole_arr[i].dimension() < 2) {
          System.out.println("PolylineArea. split_to_convex: dimension 2 for hole expected");
          continue;
        }
        TileShape[] convex_hole_pieces = hole_arr[i].split_to_convex();
        if (convex_hole_pieces == null) {
          return null;
        }
        for (int j = 0; j < convex_hole_pieces.length; ++j) {
          TileShape curr_hole_piece = convex_hole_pieces[j];
          Collection<TileShape> new_piece_list = new LinkedList<>();
          for (TileShape curr_divide_piece : curr_piece_list) {
            if (p_stoppable_thread != null && p_stoppable_thread.is_stop_requested()) {
              return null;
            }
            cutout_hole_piece(curr_divide_piece, curr_hole_piece, new_piece_list);
          }
          curr_piece_list = new_piece_list;
        }
      }
      precalculated_convex_pieces = new TileShape[curr_piece_list.size()];
      Iterator<TileShape> it = curr_piece_list.iterator();
      for (int i = 0; i < precalculated_convex_pieces.length; ++i) {
        precalculated_convex_pieces[i] = it.next();
      }
    }
    return precalculated_convex_pieces;
  }

  @Override
  public PolylineArea turn_90_degree(int p_factor, IntPoint p_pole) {
    PolylineShape new_border = border_shape.turn_90_degree(p_factor, p_pole);
    PolylineShape[] new_hole_arr = new PolylineShape[hole_arr.length];
    for (int i = 0; i < new_hole_arr.length; ++i) {
      new_hole_arr[i] = hole_arr[i].turn_90_degree(p_factor, p_pole);
    }
    return new PolylineArea(new_border, new_hole_arr);
  }

  @Override
  public PolylineArea rotate_approx(double p_angle, FloatPoint p_pole) {
    PolylineShape new_border = border_shape.rotate_approx(p_angle, p_pole);
    PolylineShape[] new_hole_arr = new PolylineShape[hole_arr.length];
    for (int i = 0; i < new_hole_arr.length; ++i) {
      new_hole_arr[i] = hole_arr[i].rotate_approx(p_angle, p_pole);
    }
    return new PolylineArea(new_border, new_hole_arr);
  }

  @Override
  public PolylineArea mirror_vertical(IntPoint p_pole) {
    PolylineShape new_border = border_shape.mirror_vertical(p_pole);
    PolylineShape[] new_hole_arr = new PolylineShape[hole_arr.length];
    for (int i = 0; i < new_hole_arr.length; ++i) {
      new_hole_arr[i] = hole_arr[i].mirror_vertical(p_pole);
    }
    return new PolylineArea(new_border, new_hole_arr);
  }

  @Override
  public PolylineArea mirror_horizontal(IntPoint p_pole) {
    PolylineShape new_border = border_shape.mirror_horizontal(p_pole);
    PolylineShape[] new_hole_arr = new PolylineShape[hole_arr.length];
    for (int i = 0; i < new_hole_arr.length; ++i) {
      new_hole_arr[i] = hole_arr[i].mirror_horizontal(p_pole);
    }
    return new PolylineArea(new_border, new_hole_arr);
  }
}
