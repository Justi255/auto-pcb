package app.freerouting.interactive;

import app.freerouting.board.BoardObservers;
import app.freerouting.board.Communication;
import app.freerouting.board.LayerStructure;
import app.freerouting.board.TestLevel;
import app.freerouting.datastructures.IdNoGenerator;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.designforms.specctra.SpecctraSesFileWriter;
import app.freerouting.geometry.planar.IntBox;
import app.freerouting.geometry.planar.PolylineShape;
import app.freerouting.rules.BoardRules;
import app.freerouting.rules.Net;
import app.freerouting.rules.NetClass;
import app.freerouting.rules.ViaRule;

import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Rectangle;
import java.awt.geom.Point2D;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.OutputStream;
import java.util.Collection;
import java.util.Locale;
import java.util.ResourceBundle;
import java.util.Set;
import java.util.TreeSet;
import javax.swing.JOptionPane;
import javax.swing.JPopupMenu;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

/** Central connection class between the graphical user interface and the board database. */
public class BoardHandling extends BoardHandlingHeadless {

  /** thread pool size */
  private int num_threads;

  /** Used for running an interactive action in a separate thread. */
  private InteractiveActionThread interactive_action_thread;
  
  /**
   * True if currently a logfile is being processed. Used to prevent interactive changes of the
   * board database in this case.
   */
  private boolean board_is_read_only = false;

  /** Creates a new BoardHandling */
  public BoardHandling(
      Locale p_locale ) {
    super(p_locale);
  }

  /** Return true, if the board is set to read only. */
  public boolean is_board_read_only() {
    return this.board_is_read_only;
  }

  /**
   * Sets the board to read only for example when running a separate action thread to avoid
   * unsynchronized change of the board.
   */
  public void set_board_read_only(boolean p_value) {
    this.board_is_read_only = p_value;
    this.settings.set_read_only(p_value);
  }

  /** Return the current language for the GUI messages. */
  @Override
  public Locale get_locale() {
    return this.locale;
  }

  /** returns the number of layers of the board design. */
  public int get_layer_count() {
    if (board == null) {
      return 0;
    }
    return board.get_layer_count();
  }

  /** Gets the trace half width used in interactive routing for the input net on the input layer. */
  public int get_trace_halfwidth(int p_net_no, int p_layer) {
    int result;
    if (settings.manual_rule_selection) {
      result = 0;//settings.manual_trace_half_width_arr[p_layer];
    } else {
      result = board.rules.get_trace_half_width(p_net_no, p_layer);
    }
    return result;
  }

  /** Returns if p_layer is active for interactive routing of traces. */
  public boolean is_active_routing_layer(int p_net_no, int p_layer) {
    if (settings.manual_rule_selection) {
      return true;
    }
    Net curr_net = this.board.rules.nets.get(p_net_no);
    if (curr_net == null) {
      return true;
    }
    NetClass curr_net_class = curr_net.get_class();
    if (curr_net_class == null) {
      return true;
    }
    return curr_net_class.is_active_routing_layer(p_layer);
  }

  /** Gets the trace clearance class used in interactive routing. */
  public int get_trace_clearance_class(int p_net_no) {
    int result;
    if (settings.manual_rule_selection) {
      result = settings.manual_trace_clearance_class;
    } else {
      result = board.rules.nets.get(p_net_no).get_class().get_trace_clearance_class();
    }
    return result;
  }

  /** Gets the via rule used in interactive routing. */
  public ViaRule get_via_rule(int p_net_no) {
    ViaRule result = null;
    if (settings.manual_rule_selection) {
      result = board.rules.via_rules.get(this.settings.manual_via_rule_index);
    }
    if (result == null) {
      result = board.rules.nets.get(p_net_no).get_class().get_via_rule();
    }
    return result;
  }

  /** Creates the Routingboard, the graphic context and the interactive settings. */
  @Override
  public void create_board(
      IntBox p_bounding_box,
      LayerStructure p_layer_structure,
      PolylineShape[] p_outline_shapes,
      String p_outline_clearance_class_name,
      BoardRules p_rules,
      Communication p_board_communication,
      TestLevel p_test_level) {
    super.create_board(
        p_bounding_box,
        p_layer_structure,
        p_outline_shapes,
        p_outline_clearance_class_name,
        p_rules,
        p_board_communication,
        p_test_level);
  }

  /**
   * Imports a board design from a Specctra dsn-file. The parameters p_item_observers and
   * p_item_id_no_generator are used, in case the board is embedded into a host system. Returns
   * false, if the dsn-file is corrupted.
   */
  public DsnFile.ReadResult import_design(
      InputStream p_design,
      BoardObservers p_observers,
      IdNoGenerator p_item_id_no_generator,
      TestLevel p_test_level) {
    if (p_design == null) {
      return DsnFile.ReadResult.ERROR;
    }

    DsnFile.ReadResult read_result;
    try {
      read_result = DsnFile.read(p_design, this, p_observers, p_item_id_no_generator, p_test_level);
    } catch (Exception e) {
      read_result = DsnFile.ReadResult.ERROR;
      //FRLogger.error("There was an error while reading DSN file.", e);
    }
    if (read_result == DsnFile.ReadResult.OK) {
      this.board.reduce_nets_of_route_items();
    }

    try {
      p_design.close();
    } catch (IOException e) {
      read_result = DsnFile.ReadResult.ERROR;
    }
    return read_result;
  }

  /** Writes a .SES session file in the Specctra ses-format. */
  public boolean export_specctra_session_file(String p_design_name, OutputStream p_output_stream) {
    if (board_is_read_only) {
      return false;
    }
    return SpecctraSesFileWriter.write(this.get_routing_board(), p_output_stream, p_design_name);
  }

  /** Start the batch autorouter on the whole Board */
  public InteractiveActionThread start_batch_autorouter() {
    if (board_is_read_only) {
      return null;
    }
    board.generate_snapshot();
    this.interactive_action_thread = InteractiveActionThread.get_batch_autorouter_instance(this);

    this.interactive_action_thread.start();

    return this.interactive_action_thread;
  }

  public int get_num_threads() {
    return num_threads;
  }

  public void set_num_threads(int p_value) {
    num_threads = p_value;
  }
}
