package app.freerouting.interactive;

import app.freerouting.board.RoutingBoard;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.Serializable;
import java.util.Arrays;

/** Contains the values of the interactive settings of the board handling. */
public class Settings implements Serializable {
  /** The array of manual trace half widths, initially equal to the automatic trace half widths. */
  public AutorouteSettings autoroute_settings;
  /** the current layer */
  int layer;

  /**
   * indicates if interactive selections are made on all visible layers or only on the current layer
   */
  boolean select_on_all_visible_layers;
  /** Route mode: stitching or dynamic */
  boolean is_stitch_route;
  /** The width of the pull tight region of traces around the cursor */
  int trace_pull_tight_region_width;
  /** The accuracy of the pull tight algorithm. */
  int trace_pull_tight_accuracy;
  /** Via snaps to smd center, if attach smd is allowed. */
  boolean via_snap_to_smd_center;
  /** The horizontal placement grid when moving components, if {@literal >} 0. */
  int horizontal_component_grid;
  /** The vertical placement grid when moving components, if {@literal >} 0. */
  int vertical_component_grid;
  /**
   * If true, the trace width at static pins smaller the trace width will be lowered
   * automatically to the pin with, if necessary.
   */
  boolean automatic_neckdown;
  /**
   * Indicates if the routing rule selection is manual by the user or automatic by the net rules.
   */
  boolean manual_rule_selection;
  /** If true, the current routing obstacle is hilightet in dynamic routing. */
  boolean hilight_routing_obstacle;
  /**
   * The index of the clearance class used for traces in interactive routing in the clearance
   * matrix, if manual_route_selection is on.
   */
  int manual_trace_clearance_class;
  /**
   * The index of the via rule used in routing in the board via rules if manual_route_selection is
   * on.
   */
  int manual_via_rule_index;
  /** If true, the mouse wheel is used for zooming. */
  boolean zoom_with_wheel;
  
  /**
   * Indicates, if the data of this class are not allowed to be changed in interactive board
   * editing.
   */
  private transient boolean read_only = false;

  /** Creates a new interactive settings variable. */
  public Settings(RoutingBoard p_board) {
    // Initialise with default values.
    layer = 0;
    select_on_all_visible_layers = true; // else selection is only on the current layer
    is_stitch_route = false; // else interactive routing is dynamic
    trace_pull_tight_region_width = Integer.MAX_VALUE;
    trace_pull_tight_accuracy = 500;
    via_snap_to_smd_center = true;
    horizontal_component_grid = 0;
    vertical_component_grid = 0;
    automatic_neckdown = true;
    manual_rule_selection = false;
    hilight_routing_obstacle = false;
    manual_trace_clearance_class = 1;
    manual_via_rule_index = 0;
    zoom_with_wheel = true;
    autoroute_settings = new AutorouteSettings(p_board);
  }

  /** Copy constructor */
  public Settings(Settings p_settings) {
    this.read_only = p_settings.read_only;
    this.layer = p_settings.layer;
    this.select_on_all_visible_layers = p_settings.select_on_all_visible_layers;
    this.is_stitch_route = p_settings.is_stitch_route;
    this.trace_pull_tight_region_width = p_settings.trace_pull_tight_region_width;
    this.trace_pull_tight_accuracy = p_settings.trace_pull_tight_accuracy;
    this.via_snap_to_smd_center = p_settings.via_snap_to_smd_center;
    this.horizontal_component_grid = p_settings.horizontal_component_grid;
    this.vertical_component_grid = p_settings.vertical_component_grid;
    this.automatic_neckdown = p_settings.automatic_neckdown;
    this.manual_rule_selection = p_settings.manual_rule_selection;
    this.hilight_routing_obstacle = p_settings.hilight_routing_obstacle;
    this.zoom_with_wheel = p_settings.zoom_with_wheel;
    this.manual_trace_clearance_class = p_settings.manual_trace_clearance_class;
    this.manual_via_rule_index = p_settings.manual_via_rule_index;
    
    this.autoroute_settings = new AutorouteSettings(p_settings.autoroute_settings);
  }

  public int get_layer() {
    return this.layer;
  }

  /** Route mode: stitching or dynamic */
  public boolean get_is_stitch_route() {
    return this.is_stitch_route;
  }

  /**
   * indicates if interactive selections are made on all visible layers or only on the current
   * layer.
   */
  public boolean get_select_on_all_visible_layers() {
    return this.select_on_all_visible_layers;
  }

  /** Sets, if item selection is on all board layers or only on the current layer. */
  public void set_select_on_all_visible_layers(boolean p_value) {
    if (read_only) {
      return;
    }
    select_on_all_visible_layers = p_value;
  }

  /**
   * Indicates if the routing rule selection is manual by the user or automatic by the net rules.
   */
  public boolean get_manual_rule_selection() {
    return this.manual_rule_selection;
  }

  /** Via snaps to smd center, if attach smd is allowed. */
  public boolean get_via_snap_to_smd_center() {
    return this.via_snap_to_smd_center;
  }

  /** Changes, if vias snap to smd center, if attach smd is allowed. */
  public void set_via_snap_to_smd_center(boolean p_value) {
    if (read_only) {
      return;
    }
    via_snap_to_smd_center = p_value;
  }

  /** If true, the current routing obstacle is hilightet in dynamic routing. */
  public boolean get_hilight_routing_obstacle() {
    return this.hilight_routing_obstacle;
  }

  /** If true, the current routing obstacle is hilightet in dynamic routing. */
  public void set_hilight_routing_obstacle(boolean p_value) {
    if (read_only) {
      return;
    }
    this.hilight_routing_obstacle = p_value;
  }

  /**
   * If true, the trace width at static pins smaller the trace width will be lowered
   * automatically to the pin with, if necessary.
   */
  public boolean get_automatic_neckdown() {
    return this.automatic_neckdown;
  }

  /**
   * If true, the trace width at static pins smaller the trace width will be lowered
   * automatically to the pin with, if necessary.
   */
  public void set_automatic_neckdown(boolean p_value) {
    if (read_only) {
      return;
    }
    this.automatic_neckdown = p_value;
  }

  /** If true, the mouse wheel is used for zooming. */
  public boolean get_zoom_with_wheel() {
    return this.zoom_with_wheel;
  }

  /** If true, the wheel is used for zooming. */
  public void set_zoom_with_wheel(boolean p_value) {
    if (read_only) {
      return;
    }
    if (zoom_with_wheel != p_value) {
      zoom_with_wheel = p_value;
    }
  }

  /** The width of the pull tight region of traces around the cursor */
  public int get_trace_pull_tight_region_width() {
    return this.trace_pull_tight_region_width;
  }

  /** The horizontal placement grid when moving components, if {@literal >} 0. */
  public int get_horizontal_component_grid() {
    return this.horizontal_component_grid;
  }

  /** The horizontal placement grid when moving components, if {@literal >} 0. */
  public void set_horizontal_component_grid(int p_value) {
    if (read_only) {
      return;
    }
    this.horizontal_component_grid = p_value;
  }

  /** The vertical placement grid when moving components, if {@literal >} 0. */
  public int get_vertical_component_grid() {
    return this.vertical_component_grid;
  }

  /** The vertical placement grid when moving components, if {@literal >} 0. */
  public void set_vertical_component_grid(int p_value) {
    if (read_only) {
      return;
    }
    this.vertical_component_grid = p_value;
  }

  /**
   * The index of the clearance class used for traces in interactive routing in the clearance
   * matrix, if manual_route_selection is on.
   */
  public int get_manual_trace_clearance_class() {
    return this.manual_trace_clearance_class;
  }

  /**
   * The index of the clearance class used for traces in interactive routing in the clearance
   * matrix, if manual_route_selection is on.
   */
  public void set_manual_trace_clearance_class(int p_index) {
    if (read_only) {
      return;
    }
    manual_trace_clearance_class = p_index;
  }

  /**
   * The index of the via rule used in routing in the board via rules if manual_route_selection is
   * on.
   */
  public int get_manual_via_rule_index() {
    return this.manual_via_rule_index;
  }

  /**
   * The index of the via rule used in routing in the board via rules if manual_route_selection is
   * on.
   */
  public void set_manual_via_rule_index(int p_value) {
    if (read_only) {
      return;
    }
    this.manual_via_rule_index = p_value;
  }

  /** The accuracy of the pull tight algorithm. */
  public int get_trace_pull_tight_accuracy() {
    return this.trace_pull_tight_accuracy;
  }

  /** Route mode: stitching or dynamic */
  public void set_stitch_route(boolean p_value) {
    if (read_only) {
      return;
    }
    is_stitch_route = p_value;

  }

  /** Changes the current width of the tidy region for traces. */
  public void set_current_pull_tight_region_width(int p_value) {
    if (read_only) {
      return;
    }
    trace_pull_tight_region_width = p_value;
  }

  /** Changes the current width of the pull tight accuracy for traces. */
  public void set_current_pull_tight_accuracy(int p_value) {
    if (read_only) {
      return;
    }
    trace_pull_tight_accuracy = p_value;
  }

  /** Sets the current trace width selection to manual or automatic. */
  public void set_manual_tracewidth_selection(boolean p_value) {
    if (read_only) {
      return;
    }
    manual_rule_selection = p_value;
  }

  /** Defines, if the setting attributes are allowed to be changed interactively or not. */
  public void set_read_only(Boolean p_value) {
    this.read_only = p_value;
  }

  /** Reads an instance of this class from a file */
  private void readObject(ObjectInputStream p_stream)
      throws IOException, ClassNotFoundException {
    p_stream.defaultReadObject();

    this.read_only = false;
  }
}
