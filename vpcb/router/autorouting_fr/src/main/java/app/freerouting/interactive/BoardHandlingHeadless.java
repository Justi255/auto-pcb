package app.freerouting.interactive;

import app.freerouting.board.Communication;
import app.freerouting.board.LayerStructure;
import app.freerouting.board.RoutingBoard;
import app.freerouting.board.TestLevel;
import app.freerouting.geometry.planar.IntBox;
import app.freerouting.geometry.planar.PolylineShape;
import app.freerouting.rules.BoardRules;
import app.freerouting.rules.DefaultItemClearanceClasses;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.Locale;

/** Base implementation for headless mode */
public class BoardHandlingHeadless implements IBoardHandling {
  /** The current settings for interactive actions on the board */
  public Settings settings;
  /** The board database used in this interactive handling. */
  protected RoutingBoard board;
  protected Locale locale;
  private byte[] serializedBoard;
  
  public BoardHandlingHeadless(
      Locale p_locale) {
    this.locale = p_locale;
  }

  /** Gets the routing board of this board handling. */
  @Override
  public RoutingBoard get_routing_board() {
    return this.board;
  }

  public synchronized void update_routing_board(RoutingBoard routing_board) {
    this.board = routing_board;
    serializedBoard = null;
  }

  public synchronized RoutingBoard deep_copy_routing_board() {
    ObjectOutputStream oos = null;
    ObjectInputStream ois = null;

    try {
      if (serializedBoard == null) // cache the board byte array
      {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        oos = new ObjectOutputStream(bos);

        oos.writeObject(this.board); // serialize this.board
        oos.flush();

        serializedBoard = bos.toByteArray();
      }

      ByteArrayInputStream bin = new ByteArrayInputStream(serializedBoard);
      ois = new ObjectInputStream(bin);

      RoutingBoard board_copy = (RoutingBoard) ois.readObject();

      board_copy.set_test_level(this.board.get_test_level()); // test_level is transient

      board_copy.clear_all_item_temporary_autoroute_data();
      board_copy.finish_autoroute();

      return board_copy;
    } catch (Exception e) {
      System.err.println("Exception in deep_copy_routing_board = " + e);
      return null;
    } finally {
      try {
        if (oos != null) oos.close();
        if (ois != null) ois.close();
      } catch (Exception e) {
      }
    }
  }

  @Override
  public Settings get_settings() {
    return settings;
  }

  @Override
  public void create_board(
      IntBox p_bounding_box,
      LayerStructure p_layer_structure,
      PolylineShape[] p_outline_shapes,
      String p_outline_clearance_class_name,
      BoardRules p_rules,
      Communication p_board_communication,
      TestLevel p_test_level) {
    if (this.board != null) {
      System.out.println(" BoardHandling.create_board: app.freerouting.board already created");
    }
    int outline_cl_class_no = 0;

    if (p_rules != null) {
      if (p_outline_clearance_class_name != null && p_rules.clearance_matrix != null) {
        outline_cl_class_no = p_rules.clearance_matrix.get_no(p_outline_clearance_class_name);
        outline_cl_class_no = Math.max(outline_cl_class_no, 0);
      } else {
        outline_cl_class_no =
            p_rules
                .get_default_net_class()
                .default_item_clearance_classes
                .get(DefaultItemClearanceClasses.ItemClass.AREA);
      }
    }
    this.board =
        new RoutingBoard(
            p_bounding_box,
            p_layer_structure,
            p_outline_shapes,
            outline_cl_class_no,
            p_rules,
            p_board_communication,
            p_test_level);

    this.settings = new Settings(this.board);
  }

  @Override
  public Locale get_locale() {
    return this.locale;
  }
}
