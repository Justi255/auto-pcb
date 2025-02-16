package app.freerouting.board;

import app.freerouting.geometry.planar.FloatPoint;
import app.freerouting.geometry.planar.IntOctagon;
import app.freerouting.geometry.planar.Point;
import app.freerouting.geometry.planar.TileShape;
import app.freerouting.rules.Net;
import app.freerouting.rules.Nets;

import java.awt.Color;
import java.io.Serializable;
import java.util.*;

/** Class describing functionality required for traces in the plane. */
public abstract class Trace extends Item implements Connectable, Serializable {

  private final int half_width; // half width of the trace pen
  private int layer; // board layer of the trace

  Trace(
      int p_layer,
      int p_half_width,
      int[] p_net_no_arr,
      int p_clearance_type,
      int p_id_no,
      int p_group_no,
      FixedState p_fixed_state,
      BasicBoard p_board) {
    super(p_net_no_arr, p_clearance_type, p_id_no, p_group_no, p_fixed_state, p_board);
    half_width = p_half_width;
    p_layer = Math.max(p_layer, 0);
    if (p_board != null) {
      p_layer = Math.min(p_layer, p_board.get_layer_count() - 1);
    }
    layer = p_layer;
  }

  /** returns the first corner of the trace */
  public abstract Point first_corner();

  /** returns the last corner of the trace */
  public abstract Point last_corner();

  @Override
  public int first_layer() {
    return this.layer;
  }

  @Override
  public int last_layer() {
    return this.layer;
  }

  public int get_layer() {
    return this.layer;
  }

  public void set_layer(int p_layer) {
    this.layer = p_layer;
  }

  public int get_half_width() {
    return half_width;
  }

  /** Returns the length of this trace. */
  public abstract double get_length();

  /**
   * Returns the half with enlarged by the clearance compensation value for the tree with id number
   * p_tree_id_no Equals get_half_width(), if no clearance compensation is used in this tree.
   */
  public int get_compensated_half_width(ShapeSearchTree p_search_tree) {
    return this.half_width
            + p_search_tree.clearance_compensation_value(clearance_class_no(), this.layer);
  }

  @Override
  public boolean is_obstacle(Item p_other) {
    if (p_other == this
        || p_other instanceof ViaObstacleArea
        || p_other instanceof ComponentObstacleArea) {
      return false;
    }
    if (p_other instanceof ConductionArea && !((ConductionArea) p_other).get_is_obstacle()) {
      return false;
    }
    return !p_other.shares_net(this);
  }

  /**
   * Get a list of all items with a connection point on the layer of this trace equal to its first
   * corner.
   */
  public Set<Item> get_start_contacts() {
    return get_normal_contacts(first_corner(), false);
  }

  /**
   * Get a list of all items with a connection point on the layer of this trace equal to its last
   * corner.
   */
  public Set<Item> get_end_contacts() {
    return get_normal_contacts(last_corner(), false);
  }

  @Override
  public Point normal_contact_point(Item p_other) {
    return p_other.normal_contact_point(this);
  }

  @Override
  public Set<Item> get_normal_contacts() {
    Set<Item> result = new TreeSet<>();
    Point start_corner = this.first_corner();
    if (start_corner != null) {
      result.addAll(get_normal_contacts(start_corner, false));
    }
    Point end_corner = this.last_corner();
    if (end_corner != null) {
      result.addAll(get_normal_contacts(end_corner, false));
    }
    return result;
  }

  @Override
  public boolean is_routable() {
    return !is_user_fixed() && (this.net_count() > 0);
  }

  /** Returns true, if this trace is not contacted at its first or at its last point. */
  @Override
  public boolean is_tail() {
    Collection<Item> contact_list = this.get_start_contacts();
    if (contact_list.isEmpty()) {
      return true;
    }
    contact_list = this.get_end_contacts();
    return (contact_list.isEmpty());
  }

  /**
   * Get a list of all items having a connection point at p_point on the layer of this trace. If
   * p_ignore_net is false, only contacts to items sharing a net with this trace are calculated.
   * This is the normal case.
   */
  public Set<Item> get_normal_contacts(Point p_point, boolean p_ignore_net) {
    if (p_point == null
        || !(p_point.equals(this.first_corner()) || p_point.equals(this.last_corner()))) {
      return new TreeSet<>();
    }
    TileShape search_shape = TileShape.get_instance(p_point);
    Set<SearchTreeObject> overlaps = board.overlapping_objects(search_shape, this.layer);
    Set<Item> result = new TreeSet<>();
    for (SearchTreeObject curr_ob : overlaps) {
      if (!(curr_ob instanceof Item)) {
        continue;
      }
      Item curr_item = (Item) curr_ob;
      if (curr_item != this
          && curr_item.shares_layer(this)
          && (p_ignore_net || curr_item.shares_net(this))) {
        if (curr_item instanceof Trace) {
          Trace curr_trace = (Trace) curr_item;
          if (p_point.equals(curr_trace.first_corner())
              || p_point.equals(curr_trace.last_corner())) {
            result.add(curr_item);
          }
        } else if (curr_item instanceof DrillItem) {
          DrillItem curr_drill_item = (DrillItem) curr_item;
          if (p_point.equals(curr_drill_item.get_center())) {
            result.add(curr_item);
          }
        } else if (curr_item instanceof ConductionArea) {
          ConductionArea curr_area = (ConductionArea) curr_item;
          if (curr_area.get_area().contains(p_point)) {
            result.add(curr_item);
          }
        }
      }
    }
    return result;
  }

  @Override
  Point normal_contact_point(DrillItem p_drill_item) {
    return p_drill_item.normal_contact_point(this);
  }

  @Override
  Point normal_contact_point(Trace p_other) {
    if (this.layer != p_other.layer) {
      return null;
    }
    boolean contact_at_first_corner =
        this.first_corner().equals(p_other.first_corner())
            || this.first_corner().equals(p_other.last_corner());
    boolean contact_at_last_corner =
        this.last_corner().equals(p_other.first_corner())
            || this.last_corner().equals(p_other.last_corner());
    Point result;
    if (!(contact_at_first_corner || contact_at_last_corner)
        || contact_at_first_corner && contact_at_last_corner) {
      // no contact point or more than 1 contact point
      result = null;
    } else if (contact_at_first_corner) {
      result = this.first_corner();
    } else // contact at last corner
    {
      result = this.last_corner();
    }
    return result;
  }

  @Override
  public boolean is_drillable(int p_net_no) {
    return this.contains_net(p_net_no);
  }

  /** looks, if this trace is connected to the same object at its start and its end point */
  @Override
  public boolean is_overlap() {
    Set<Item> start_contacts = this.get_start_contacts();
    Set<Item> end_contacts = this.get_end_contacts();
    return !Collections.disjoint(start_contacts, end_contacts);
  }

  /**
   * Returns true, if it is not allowed to change the location of this item by the push algorithm.
   */
  @Override
  public boolean is_shove_fixed() {
    if (super.is_shove_fixed()) {
      return true;
    }

    // check, if the trace  belongs to a net, which is not shovable.
    Nets nets = this.board.rules.nets;
    for (int curr_net_no : this.net_no_arr) {
      if (Nets.is_normal_net_no(curr_net_no)) {
        if (nets.get(curr_net_no).get_class().is_shove_fixed()) {
          return true;
        }
      }
    }
    return false;
  }

  /** returns the endpoint of this trace with the shortest distance to p_from_point */
  public Point nearest_end_point(Point p_from_point) {
    Point p1 = first_corner();
    Point p2 = last_corner();
    FloatPoint from_point = p_from_point.to_float();
    double d1 = from_point.distance(p1.to_float());
    double d2 = from_point.distance(p2.to_float());
    Point result;
    if (d1 < d2) {
      result = p1;
    } else {
      result = p2;
    }
    return result;
  }

  /** Checks, if this trace can be reached by other items via more than one path */
  public boolean is_cycle() {
    if (this.is_overlap()) {
      return true;
    }
    Collection<Item> start_contacts = this.get_start_contacts();
    // a cycle exists if through expanding the start contact we reach
    // this trace again via an end contact
    // make sure, that all direct neighbours are
    // expanded from here, to block coming back to
    // this trace via a start contact.
    Set<Item> visited_items = new TreeSet<>(start_contacts);
    boolean ignore_areas = false;
    if (this.net_no_arr.length > 0) {
      Net curr_net = this.board.rules.nets.get(this.net_no_arr[0]);
      if (curr_net != null && curr_net.get_class() != null) {
        ignore_areas = curr_net.get_class().get_ignore_cycles_with_areas();
      }
    }
    for (Item curr_contact : start_contacts) {
      if (curr_contact.is_cycle_recu(visited_items, this, this, ignore_areas)) {
        return true;
      }
    }
    return false;
  }

  @Override
  public int shape_layer(int p_index) {
    return layer;
  }

  @Override
  public Point[] get_ratsnest_corners() {
    // Use only uncontacted endpoints of the trace.
    // Otherwise, the allocated memory in the calculation of the incompletes might become very big.
    int stub_count = 0;
    boolean stub_at_start = false;
    boolean stub_at_end = false;
    if (get_start_contacts().isEmpty()) {
      ++stub_count;
      stub_at_start = true;
    }
    if (get_end_contacts().isEmpty()) {
      ++stub_count;
      stub_at_end = true;
    }
    Point[] result = new Point[stub_count];
    int stub_no = 0;
    if (stub_at_start) {
      result[stub_no] = first_corner();
      ++stub_no;
    }
    if (stub_at_end) {
      result[stub_no] = last_corner();
    }
    for (int i = 0; i < result.length; ++i) {
      if (result[i] == null) {
        return new Point[0]; // Trace is inconsistent
      }
    }
    return result;
  }

  /**
   * checks, that the connection restrictions to the contact pins are satisfied. If p_at_start, the
   * start of this trace is checked, else the end. Returns false, if a pin is at that end, where the
   * connection is checked and the connection is not ok.
   */
  public abstract boolean check_connection_to_pin(boolean p_at_start);

  @Override
  public boolean is_selected_by_filter(ItemSelectionFilter p_filter) {
    if (!this.is_selected_by_fixed_filter(p_filter)) {
      return false;
    }
    return p_filter.is_selected(ItemSelectionFilter.SelectableChoices.TRACES);
  }

  /**
   * Looks up touching pins at the first corner and the last corner of the trace. Used to avoid acid
   * traps.
   */
  Set<Pin> touching_pins_at_end_corners() {
    Set<Pin> result = new TreeSet<>();
    if (this.board == null) {
      return result;
    }
    Point curr_end_point = this.first_corner();
    for (int i = 0; i < 2; ++i) {
      IntOctagon curr_oct = curr_end_point.surrounding_octagon();
      curr_oct = curr_oct.enlarge(this.half_width);
      Set<Item> curr_overlaps =
          this.board.overlapping_items_with_clearance(
              curr_oct, this.layer, new int[0], this.clearance_class_no());
      for (Item curr_item : curr_overlaps) {
        if ((curr_item instanceof Pin) && curr_item.shares_net(this)) {
          result.add((Pin) curr_item);
        }
      }
      curr_end_point = this.last_corner();
    }
    return result;
  }

  @Override
  public boolean validate() {
    boolean result = super.validate();

    if (this.first_corner().equals(this.last_corner())) {
      System.out.println("Trace.validate: first and last corner are equal");
      result = false;
    }
    return result;
  }

  /**
   * looks, if this trace can be combined with other traces . Returns true, if something has been
   * combined.
   */
  abstract boolean combine();

  /**
   * Looks up traces intersecting with this trace and splits them at the intersection points. In
   * case of an overlaps, the traces are split at their first and their last common point. Returns
   * the pieces resulting from splitting. If nothing is split, the result will contain just this
   * Trace. If p_clip_shape != null, the split may be restricted to p_clip_shape.
   */
  public abstract Collection<PolylineTrace> split(IntOctagon p_clip_shape);

  /**
   * Splits this trace into two at p_point. Returns the 2 pieces of the splitted trace, or null if
   * nothing was splitted because for example p_point is not located on this trace.
   */
  public abstract Trace[] split(Point p_point);

  /**
   * Tries to make this trace shorter according to its rules. Returns true if the geometry of the
   * trace was changed.
   */
  public abstract boolean pull_tight(PullTightAlgo p_pull_tight_algo);
}
