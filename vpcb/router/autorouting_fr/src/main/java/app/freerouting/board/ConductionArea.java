package app.freerouting.board;

import app.freerouting.geometry.planar.Area;
import app.freerouting.geometry.planar.FloatPoint;
import app.freerouting.geometry.planar.Point;
import app.freerouting.geometry.planar.TileShape;
import app.freerouting.geometry.planar.Vector;

import java.awt.Color;
import java.util.Locale;
import java.util.ResourceBundle;
import java.util.Set;
import java.util.TreeSet;

/** A ObstacleArea, which can be electrically connected to other items. */
public class ConductionArea extends ObstacleArea implements Connectable {

  private boolean is_obstacle;

  /** Creates a new instance of ConductionArea */
  ConductionArea(
      Area p_area,
      int p_layer,
      Vector p_translation,
      double p_rotation_in_degree,
      boolean p_side_changed,
      int[] p_net_no_arr,
      int p_clearance_class,
      int p_id_no,
      int p_group_no,
      String p_name,
      boolean p_is_obstacle,
      FixedState p_fixed_state,
      BasicBoard p_board) {
    super(
        p_area,
        p_layer,
        p_translation,
        p_rotation_in_degree,
        p_side_changed,
        p_net_no_arr,
        p_clearance_class,
        p_id_no,
        p_group_no,
        p_name,
        p_fixed_state,
        p_board);
    is_obstacle = p_is_obstacle;
  }

  @Override
  public Item copy(int p_id_no) {
    if (this.net_count() != 1) {
      System.out.println("ConductionArea.copy not yet implemented for areas with more than 1 net");
      return null;
    }
    return new ConductionArea(
        get_relative_area(),
        get_layer(),
        get_translation(),
        get_rotation_in_degree(),
        get_side_changed(),
        net_no_arr,
        clearance_class_no(),
        p_id_no,
        get_component_no(),
        this.name,
        is_obstacle,
        get_fixed_state(),
        board);
  }

  @Override
  public Set<Item> get_normal_contacts() {
    Set<Item> result = new TreeSet<>();
    for (int i = 0; i < tile_shape_count(); ++i) {
      TileShape curr_shape = get_tile_shape(i);
      Set<SearchTreeObject> overlaps = board.overlapping_objects(curr_shape, get_layer());
      for (SearchTreeObject curr_ob : overlaps) {
        if (!(curr_ob instanceof Item)) {
          continue;
        }
        Item curr_item = (Item) curr_ob;
        if (curr_item != this && curr_item.shares_net(this) && curr_item.shares_layer(this)) {
          if (curr_item instanceof Trace) {
            Trace curr_trace = (Trace) curr_item;
            if (curr_shape.contains(curr_trace.first_corner())
                || curr_shape.contains(curr_trace.last_corner())) {
              result.add(curr_item);
            }
          } else if (curr_item instanceof DrillItem) {
            DrillItem curr_drill_item = (DrillItem) curr_item;
            if (curr_shape.contains(curr_drill_item.get_center())) {
              result.add(curr_item);
            }
          }
        }
      }
    }
    return result;
  }

  @Override
  public TileShape get_trace_connection_shape(ShapeSearchTree p_search_tree, int p_index) {
    if (p_index < 0 || p_index >= this.tree_shape_count(p_search_tree)) {
      System.out.println("ConductionArea.get_trace_connection_shape p_index out of range");
      return null;
    }
    return this.get_tree_shape(p_search_tree, p_index);
  }

  @Override
  public Point[] get_ratsnest_corners() {
    Point[] result;
    FloatPoint[] corners = this.get_area().corner_approx_arr();
    result = new Point[corners.length];
    for (int i = 0; i < corners.length; ++i) {
      result[i] = corners[i].round();
    }

    return result;
  }

  @Override
  public boolean is_obstacle(Item p_other) {
    if (this.is_obstacle) {
      return super.is_obstacle(p_other);
    }
    return false;
  }

  /** Returns if this conduction area is regarded as obstacle to traces of foreign nets. */
  public boolean get_is_obstacle() {
    return this.is_obstacle;
  }

  /** Sets, if this conduction area is regarded as obstacle to traces and vias of foreign nets. */
  public void set_is_obstacle(boolean p_value) {
    this.is_obstacle = p_value;
  }

  @Override
  public boolean is_trace_obstacle(int p_net_no) {
    return this.is_obstacle && !this.contains_net(p_net_no);
  }

  @Override
  public boolean is_drillable(int p_net_no) {
    return !this.is_obstacle || this.contains_net(p_net_no);
  }

  @Override
  public boolean is_selected_by_filter(ItemSelectionFilter p_filter) {
    if (!this.is_selected_by_fixed_filter(p_filter)) {
      return false;
    }
    return p_filter.is_selected(ItemSelectionFilter.SelectableChoices.CONDUCTION);
  }
}
