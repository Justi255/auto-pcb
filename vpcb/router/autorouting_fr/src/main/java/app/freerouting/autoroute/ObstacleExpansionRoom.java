package app.freerouting.autoroute;

import app.freerouting.board.Item;
import app.freerouting.board.PolylineTrace;
import app.freerouting.board.SearchTreeObject;
import app.freerouting.board.ShapeSearchTree;
import app.freerouting.geometry.planar.TileShape;

import java.awt.Color;
import java.awt.Graphics;
import java.util.Collection;
import java.util.LinkedList;
import java.util.List;

/** Expansion Room used for pushing and ripping obstacles in the autoroute algorithm. */
public class ObstacleExpansionRoom implements CompleteExpansionRoom {

  private final Item item;
  private final int index_in_item;
  private final TileShape shape;
  /** The list of doors to neighbour expansion rooms */
  private List<ExpansionDoor> doors;
  private boolean doors_calculated = false;

  /** Creates a new instance of ObstacleExpansionRoom */
  ObstacleExpansionRoom(Item p_item, int p_index_in_item, ShapeSearchTree p_shape_tree) {
    this.item = p_item;
    this.index_in_item = p_index_in_item;
    this.shape = p_item.get_tree_shape(p_shape_tree, p_index_in_item);
    this.doors = new LinkedList<>();
  }

  public int get_index_in_item() {
    return this.index_in_item;
  }

  @Override
  public int get_layer() {
    return this.item.shape_layer(this.index_in_item);
  }

  @Override
  public TileShape get_shape() {
    return this.shape;
  }

  /** Checks, if this room has already a 1-dimensional door to p_other */
  @Override
  public boolean door_exists(ExpansionRoom p_other) {
    if (doors != null) {
      for (ExpansionDoor curr_door : this.doors) {
        if (curr_door.first_room == p_other || curr_door.second_room == p_other) {
          return true;
        }
      }
    }
    return false;
  }

  /** Adds a door to the door list of this room. */
  @Override
  public void add_door(ExpansionDoor p_door) {
    this.doors.add(p_door);
  }

  /**
   * Creates a 2-dim door with the other obstacle room, if that is useful for the autoroute
   * algorithm. It is assumed that this room and p_other have a 2-dimensional overlap. Returns
   * false, if no door was created.
   */
  public boolean create_overlap_door(ObstacleExpansionRoom p_other) {
    if (this.door_exists(p_other)) {
      return false;
    }
    if (!(this.item.is_routable() && p_other.item.is_routable())) {
      return false;
    }
    if (!this.item.shares_net(p_other.item)) {
      return false;
    }
    if (this.item == p_other.item) {
      if (!(this.item instanceof PolylineTrace)) {
        return false;
      }
      // create only doors between consecutive trace segments
      if (this.index_in_item != p_other.index_in_item + 1
          && this.index_in_item != p_other.index_in_item - 1) {
        return false;
      }
    }
    ExpansionDoor new_door = new ExpansionDoor(this, p_other, 2);
    this.add_door(new_door);
    p_other.add_door(new_door);
    return true;
  }

  /** Returns the list of doors of this room to neighbour expansion rooms */
  @Override
  public List<ExpansionDoor> get_doors() {
    return this.doors;
  }

  /** Removes all doors from this room. */
  @Override
  public void clear_doors() {
    this.doors = new LinkedList<>();
  }

  @Override
  public void reset_doors() {
    for (ExpandableObject curr_door : this.doors) {
      curr_door.reset();
    }
  }

  @Override
  public Collection<TargetItemExpansionDoor> get_target_doors() {
    return new LinkedList<>();
  }

  public Item get_item() {
    return this.item;
  }

  @Override
  public SearchTreeObject get_object() {
    return this.item;
  }

  @Override
  public boolean remove_door(ExpandableObject p_door) {
    return this.doors.remove(p_door);
  }

  /** Returns, if all doors to the neighbour rooms are calculated. */
  boolean all_doors_calculated() {
    return this.doors_calculated;
  }

  void set_doors_calculated(boolean p_value) {
    this.doors_calculated = p_value;
  }
}
