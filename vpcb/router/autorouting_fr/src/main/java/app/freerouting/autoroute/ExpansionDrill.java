package app.freerouting.autoroute;

import app.freerouting.board.SearchTreeObject;
import app.freerouting.geometry.planar.Point;
import app.freerouting.geometry.planar.TileShape;

import java.awt.Color;
import java.awt.Graphics;
import java.util.Collection;
import java.util.Iterator;

/** Layer change expansion object in the maze search algorithm. */
public class ExpansionDrill implements ExpandableObject {

  /** The location, where the drill is checked. */
  public final Point location;
  /** The first layer of the drill */
  public final int first_layer;
  /** The last layer of the drill */
  public final int last_layer;
  /** Array of dimension last_layer - first_layer + 1. */
  public final CompleteExpansionRoom[] room_arr;
  private final MazeSearchElement[] maze_search_info_arr;
  /** The shape of the drill. */
  private final TileShape shape;

  /** Creates a new instance of Drill */
  public ExpansionDrill(TileShape p_shape, Point p_location, int p_first_layer, int p_last_layer) {
    shape = p_shape;
    location = p_location;
    first_layer = p_first_layer;
    last_layer = p_last_layer;
    int layer_count = p_last_layer - p_first_layer + 1;
    room_arr = new CompleteExpansionRoom[layer_count];
    maze_search_info_arr = new MazeSearchElement[layer_count];
    for (int i = 0; i < maze_search_info_arr.length; ++i) {
      maze_search_info_arr[i] = new MazeSearchElement();
    }
  }

  /**
   * Looks for the expansion room of this drill on each layer. Creates a
   * CompleteFreeSpaceExpansionRoom, if no expansion room is found. Returns false, if that was not
   * possible because of an obstacle at this.location on some layer in the compensated search tree.
   */
  public boolean calculate_expansion_rooms(AutorouteEngine p_autoroute_engine) {
    TileShape search_shape = TileShape.get_instance(location);
    Collection<SearchTreeObject> overlaps =
        p_autoroute_engine.autoroute_search_tree.overlapping_objects(search_shape, -1);
    for (int i = this.first_layer; i <= this.last_layer; ++i) {
      CompleteExpansionRoom found_room = null;
      Iterator<SearchTreeObject> it = overlaps.iterator();
      while (it.hasNext()) {
        SearchTreeObject curr_ob = it.next();
        if (!(curr_ob instanceof CompleteExpansionRoom)) {
          it.remove();
          continue;
        }
        CompleteExpansionRoom curr_room = (CompleteExpansionRoom) curr_ob;
        if (curr_room.get_layer() == i) {
          found_room = curr_room;
          it.remove();
          break;
        }
      }
      if (found_room == null) {
        // create a new expansion room on this layer
        IncompleteFreeSpaceExpansionRoom new_incomplete_room =
            new IncompleteFreeSpaceExpansionRoom(null, i, search_shape);
        Collection<CompleteFreeSpaceExpansionRoom> new_rooms =
            p_autoroute_engine.complete_expansion_room(new_incomplete_room);
        if (new_rooms.size() != 1) {
          // the size may be 0 because of an obstacle in the compensated tree at this.location
          return false;
        }
        Iterator<CompleteFreeSpaceExpansionRoom> it2 = new_rooms.iterator();
        if (it2.hasNext()) {
          found_room = it2.next();
        }
      }
      this.room_arr[i - first_layer] = found_room;
    }
    return true;
  }

  @Override
  public TileShape get_shape() {
    return this.shape;
  }

  @Override
  public int get_dimension() {
    return 2;
  }

  @Override
  public CompleteExpansionRoom other_room(CompleteExpansionRoom p_room) {
    return null;
  }

  @Override
  public int maze_search_element_count() {
    return this.maze_search_info_arr.length;
  }

  @Override
  public MazeSearchElement get_maze_search_element(int p_no) {
    return this.maze_search_info_arr[p_no];
  }

  @Override
  public void reset() {
    for (MazeSearchElement curr_info : maze_search_info_arr) {
      curr_info.reset();
    }
  }
}
