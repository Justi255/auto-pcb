package app.freerouting.designforms.specctra;

import app.freerouting.board.AngleRestriction;
import app.freerouting.board.BasicBoard;
import app.freerouting.board.BoardOutline;
import app.freerouting.board.Communication;
import app.freerouting.board.ConductionArea;
import app.freerouting.board.FixedState;
import app.freerouting.board.ObstacleArea;
import app.freerouting.board.RoutingBoard;
import app.freerouting.board.TestLevel;
import app.freerouting.datastructures.UndoableObjects;
import app.freerouting.datastructures.UndoableObjects.Storable;
import app.freerouting.geometry.planar.Area;
import app.freerouting.geometry.planar.IntBox;
import app.freerouting.geometry.planar.Limits;
import app.freerouting.geometry.planar.Point;
import app.freerouting.geometry.planar.PolylineShape;
import app.freerouting.geometry.planar.TileShape;
import app.freerouting.library.BoardLibrary;
import app.freerouting.library.Padstack;
import app.freerouting.rules.BoardRules;
import app.freerouting.rules.ClearanceMatrix;
import app.freerouting.rules.DefaultItemClearanceClasses;
import app.freerouting.rules.DefaultItemClearanceClasses.ItemClass;

import java.io.IOException;
import java.util.Collection;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Objects;

/** Class for reading and writing structure scopes from dsn-files. */
class Structure extends ScopeKeyword {

  /** Creates a new instance of Structure */
  public Structure() {
    super("structure");
  }

  private static boolean read_boundary_scope(
      IJFlexScanner p_scanner, BoardConstructionInfo p_board_construction_info) {
    Shape curr_shape = Shape.read_scope(p_scanner, null);
    // overread the closing bracket.
    try {
      Object prev_token = null;
      for (; ; ) {
        Object next_token = p_scanner.next_token();
        if (next_token == Keyword.CLOSED_BRACKET) {
          break;
        }
        if (prev_token == Keyword.OPEN_BRACKET) {
          if (next_token == Keyword.CLEARANCE_CLASS) {
            p_board_construction_info.outline_clearance_class_name =
                DsnFile.read_string_scope(p_scanner);
          } else {
            //FRLogger.error(
            //    "There are multiple shapes defined in the boundary section of the DSN file. This scenario is not currently supported. If you have more than one board outlines defined, try to merge them into one.",
            //    null);
            return false;
          }
        }
        prev_token = next_token;
      }
    } catch (IOException e) {
      //FRLogger.error("Structure.read_boundary_scope: IO error scanning file", e);
      return false;
    }
    if (curr_shape == null) {
      System.out.println("Structure.read_boundary_scope: shape is null at '" + p_scanner.get_scope_identifier() + "'");
      return true;
    }
    if (curr_shape.layer == Layer.PCB) {
      if (p_board_construction_info.bounding_shape == null) {
        p_board_construction_info.bounding_shape = curr_shape;
      } else {
        System.out.println("Structure.read_boundary_scope: exact 1 bounding_shape expected at '" + p_scanner.get_scope_identifier() + "'");
      }
    } else if (curr_shape.layer == Layer.SIGNAL) {
      p_board_construction_info.outline_shapes.add(curr_shape);
    } else {
      System.out.println("Structure.read_boundary_scope: unexpected layer at '" + p_scanner.get_scope_identifier() + "'");
    }
    return true;
  }

  static boolean read_layer_scope(
      IJFlexScanner p_scanner,
      BoardConstructionInfo p_board_construction_info,
      String p_string_quote) {
    try {
      boolean layer_ok = true;
      boolean is_signal = true;

      String layer_string = p_scanner.next_string();

      Collection<String> net_names = new LinkedList<>();
      Object next_token = p_scanner.next_token();
      while (next_token != Keyword.CLOSED_BRACKET) {
        if (next_token != Keyword.OPEN_BRACKET) {
          System.out.println("Structure.read_layer_scope: ( expected at '" + p_scanner.get_scope_identifier() + "'");
          return false;
        }
        next_token = p_scanner.next_token();
        if (next_token == Keyword.TYPE) {
          next_token = p_scanner.next_token();
          if (next_token == Keyword.POWER) {
            is_signal = false;
          } else if ((next_token != Keyword.SIGNAL) && (!Objects.equals(next_token.toString(),Keyword.JUMPER.get_name()))) {
            if (next_token instanceof String) {
              System.out.println("Structure.read_layer_scope: the layer '" + layer_string + "' has an unknown layer type '" + next_token + "'");
            } else {
              System.out.println("Structure.read_layer_scope: the layer '" + layer_string + "' has an unknown layer type at '" + p_scanner.get_scope_identifier() + "'");
            }
            layer_ok = false;
          }
          next_token = p_scanner.next_token();
          if (next_token != Keyword.CLOSED_BRACKET) {
            System.out.println("Structure.read_layer_scope: ) expected at '" + p_scanner.get_scope_identifier() + "'");
            return false;
          }
        } else if (next_token == Keyword.RULE) {
          Collection<Rule> curr_rules = Rule.read_scope(p_scanner);
          p_board_construction_info.layer_dependent_rules.add(
              new LayerRule(layer_string, curr_rules));
        } else if (next_token == Keyword.USE_NET) {
          for (; ; ) {
            p_scanner.yybegin(SpecctraDsnFileReader.NAME);
            next_token = p_scanner.next_token();
            if (next_token == Keyword.CLOSED_BRACKET) {
              break;
            }
            if (next_token instanceof String) {
              net_names.add((String) next_token);
            } else {
              System.out.println("Structure.read_layer_scope: string expected at '" + p_scanner.get_scope_identifier() + "'");
            }
          }
        } else {
          skip_scope(p_scanner);
        }
        next_token = p_scanner.next_token();
      }
      if (layer_ok) {
        Layer curr_layer =
            new Layer(
                layer_string, p_board_construction_info.found_layer_count, is_signal, net_names);
        p_board_construction_info.layer_info.add(curr_layer);
        ++p_board_construction_info.found_layer_count;
      }
    } catch (IOException e) {
      //FRLogger.error("Layer.read_scope: IO error scanning file", e);
      return false;
    }
    return true;
  }

  static Collection<String> read_via_padstacks(IJFlexScanner p_scanner) {
    try {
      Collection<String> normal_vias = new LinkedList<>();
      Collection<String> spare_vias = new LinkedList<>();
      for (; ; ) {
        Object next_token = p_scanner.next_token();
        if (next_token == Keyword.CLOSED_BRACKET) {
          break;
        }
        if (next_token == Keyword.OPEN_BRACKET) {
          next_token = p_scanner.next_token();
          if (next_token == Keyword.SPARE) {
            spare_vias = read_via_padstacks(p_scanner);
          } else {
            skip_scope(p_scanner);
          }
        } else if (next_token instanceof String) {
          normal_vias.add((String) next_token);
        } else {
          System.out.println("Structure.read_via_padstack: String expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
      }
      // add the spare vias to the end of the list
      normal_vias.addAll(spare_vias);
      return normal_vias;
    } catch (IOException e) {
      //FRLogger.error("Structure.read_via_padstack: IO error scanning file", e);
      return null;
    }
  }

  private static boolean read_control_scope(ReadScopeParameter p_par) {
    Object next_token = null;
    for (; ; ) {
      Object prev_token = next_token;
      try {
        next_token = p_par.scanner.next_token();
      } catch (IOException e) {
        //FRLogger.error("Structure.read_control_scope: IO error scanning file", e);
        return false;
      }
      if (next_token == null) {
        System.out.println("Structure.read_control_scope: unexpected end of file at '" + p_par.scanner.get_scope_identifier() + "'");
        return false;
      }
      if (next_token == CLOSED_BRACKET) {
        // end of scope
        break;
      }
      if (prev_token == OPEN_BRACKET) {
        if (next_token == Keyword.VIA_AT_SMD) {
          p_par.via_at_smd_allowed = DsnFile.read_on_off_scope(p_par.scanner);
        } else {
          skip_scope(p_par.scanner);
        }
      }
    }
    return true;
  }

  static AngleRestriction read_snap_angle(IJFlexScanner p_scanner) {
    try {
      Object next_token = p_scanner.next_token();
      AngleRestriction snap_angle;
      if (next_token == Keyword.NINETY_DEGREE) {
        snap_angle = AngleRestriction.NINETY_DEGREE;
      } else if (next_token == Keyword.FORTYFIVE_DEGREE) {
        snap_angle = AngleRestriction.FORTYFIVE_DEGREE;
      } else if (next_token == Keyword.NONE) {
        snap_angle = AngleRestriction.NONE;
      } else {
        System.out.println("Structure.read_snap_angle_scope: unexpected token at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      next_token = p_scanner.next_token();
      if (next_token != Keyword.CLOSED_BRACKET) {
        System.out.println("Structure.read_selection_layer_scop: closing bracket expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      return snap_angle;
    } catch (IOException e) {
      //FRLogger.error("Structure.read_snap_angle: IO error scanning file", e);
      return null;
    }
  }

  private static void insert_missing_power_planes(
      Collection<Layer> p_layer_info, NetList p_netlist, BasicBoard p_board) {
    Collection<ConductionArea> conduction_areas =
        p_board.get_conduction_areas();
    for (Layer curr_layer : p_layer_info) {
      if (curr_layer.is_signal) {
        continue;
      }
      boolean conduction_area_found = false;
      for (ConductionArea curr_conduction_area : conduction_areas) {
        if (curr_conduction_area.get_layer() == curr_layer.no) {
          conduction_area_found = true;
          break;
        }
      }
      if (!conduction_area_found && !curr_layer.net_names.isEmpty()) {
        String curr_net_name = curr_layer.net_names.iterator().next();
        Net.Id curr_net_id = new Net.Id(curr_net_name, 1);
        if (!p_netlist.contains(curr_net_id)) {
          Net new_net = p_netlist.add_net(curr_net_id);
          if (new_net != null) {
            p_board.rules.nets.add(new_net.id.name, new_net.id.subnet_number, true);
          }
        }
        app.freerouting.rules.Net curr_net =
            p_board.rules.nets.get(curr_net_id.name, curr_net_id.subnet_number);
        {
          if (curr_net == null) {
            System.out.println("Structure.insert_missing_power_planes: net not found at '" + curr_net_id.name + "'");
            continue;
          }
        }
        int[] net_numbers = new int[1];
        net_numbers[0] = curr_net.net_number;
        p_board.insert_conduction_area(
            p_board.bounding_box,
            curr_layer.no,
            net_numbers,
            BoardRules.clearance_class_none(),
            false,
            FixedState.SYSTEM_FIXED);
      }
    }
  }

  /**
   * Calculates shapes in p_outline_shapes, which are holes in the outline and returns them in the
   * result list.
   */
  private static Collection<PolylineShape> separate_holes(
      Collection<PolylineShape> p_outline_shapes) {
    OutlineShape[] shape_arr = new OutlineShape[p_outline_shapes.size()];
    Iterator<PolylineShape> it = p_outline_shapes.iterator();
    for (int i = 0; i < shape_arr.length; ++i) {
      shape_arr[i] = new OutlineShape(it.next());
    }
    for (int i = 0; i < shape_arr.length; ++i) {
      OutlineShape curr_shape = shape_arr[i];
      for (int j = 0; j < shape_arr.length; ++j) {
        // check if shape_arr[j] may be contained in shape_arr[i]
        OutlineShape other_shape = shape_arr[j];
        if (i == j || other_shape.is_hole) {
          continue;
        }
        if (!other_shape.bounding_box.contains(curr_shape.bounding_box)) {
          continue;
        }
        curr_shape.is_hole = other_shape.contains_all_corners(curr_shape);
      }
    }
    Collection<PolylineShape> hole_list = new LinkedList<>();
    for (int i = 0; i < shape_arr.length; ++i) {
      if (shape_arr[i].is_hole) {
        p_outline_shapes.remove(shape_arr[i].shape);
        hole_list.add(shape_arr[i].shape);
      }
    }
    return hole_list;
  }
  // Check, if a conduction area is inserted on each plane,
  // and insert evtl. a conduction area

  /** Updates the board rules from the rules read from the dsn file. */
  private static void update_board_rules(
      ReadScopeParameter p_par,
      BoardConstructionInfo p_board_construction_info,
      BoardRules p_board_rules) {
    boolean smd_to_turn_gap_found = false;
    // update the clearance matrix
    for (Rule curr_ob : p_board_construction_info.default_rules) {
      if (curr_ob instanceof Rule.ClearanceRule) {
        Rule.ClearanceRule curr_rule = (Rule.ClearanceRule) curr_ob;
        if (set_clearance_rule(
            curr_rule, -1, p_par.coordinate_transform, p_board_rules, p_par.string_quote)) {
          smd_to_turn_gap_found = true;
        }
      }
    }
    // update width rules
    for (Object curr_ob : p_board_construction_info.default_rules) {
      if (curr_ob instanceof Rule.WidthRule) {
        double wire_width = ((Rule.WidthRule) curr_ob).value;
        int trace_halfwidth =
            (int) Math.round(p_par.coordinate_transform.dsn_to_board(wire_width) / 2);
        p_board_rules.set_default_trace_half_widths(trace_halfwidth);
      }
    }
    for (LayerRule layer_rule : p_board_construction_info.layer_dependent_rules) {
      int layer_no = p_par.layer_structure.get_no(layer_rule.layer_name);
      if (layer_no < 0) {
        continue;
      }
      for (Rule curr_ob : layer_rule.rule) {
        if (curr_ob instanceof Rule.WidthRule) {
          double wire_width = ((Rule.WidthRule) curr_ob).value;
          int trace_halfwidth =
              (int) Math.round(p_par.coordinate_transform.dsn_to_board(wire_width) / 2);
          p_board_rules.set_default_trace_half_width(layer_no, trace_halfwidth);
        } else if (curr_ob instanceof Rule.ClearanceRule) {
          Rule.ClearanceRule curr_rule = (Rule.ClearanceRule) curr_ob;
          set_clearance_rule(
              curr_rule, layer_no, p_par.coordinate_transform, p_board_rules, p_par.string_quote);
        }
      }
    }
    if (!smd_to_turn_gap_found) {
      p_board_rules.set_pin_edge_to_turn_dist(p_board_rules.get_min_trace_half_width());
    }
  }

  /**
   * Converts a dsn clearance rule into a board clearance rule. If p_layer_no < 0, the rule is set
   * on all layers. Returns true, if the string smd_to_turn_gap was found.
   */
  static boolean set_clearance_rule(
      Rule.ClearanceRule p_rule,
      int p_layer_no,
      CoordinateTransform p_coordinate_transform,
      BoardRules p_board_rules,
      String p_string_quote) {
    boolean result = false;
    int curr_clearance = (int) Math.round(p_coordinate_transform.dsn_to_board(p_rule.value));
    if (p_rule.clearance_class_pairs.isEmpty()) {
      if (p_layer_no < 0) {
        p_board_rules.clearance_matrix.set_default_value(curr_clearance);
      } else {
        p_board_rules.clearance_matrix.set_default_value(p_layer_no, curr_clearance);
      }
      return result;
    }
    if (contains_wire_clearance_pair(p_rule.clearance_class_pairs)) {
      create_default_clearance_classes(p_board_rules);
    }
    for (String curr_string : p_rule.clearance_class_pairs) {
      if (curr_string.equalsIgnoreCase("smd_to_turn_gap")) {
        p_board_rules.set_pin_edge_to_turn_dist(curr_clearance);
        result = true;
        continue;
      }
      String[] curr_pair;
      if (curr_string.startsWith(p_string_quote)) {
        // split at the second occurrence of p_string_quote
        curr_string = curr_string.substring(p_string_quote.length());
        curr_pair = curr_string.split(p_string_quote, 2);
        if (curr_pair.length != 2 || !curr_pair[1].startsWith("_")) {
          System.out.println("Structure.set_clearance_rule: '_' expected at '" + curr_string + "'");
          System.out.println("You probably get this error because your clearance rule name has spaces or special characters in its name. Please change them first, and try again.");
          continue;
        }
        curr_pair[1] = curr_pair[1].substring(1);
      } else {
        curr_pair = curr_string.split("_", 2);
        if (curr_pair.length != 2) {
          // pairs with more than 1 underline like smd_via_same_net are not implemented
          continue;
        }
      }

      if (curr_pair[1].startsWith(p_string_quote) && curr_pair[1].endsWith(p_string_quote)) {
        // remove the quotes
        curr_pair[1] = curr_pair[1].substring(1, curr_pair[1].length() - 1);
      } else {
        String[] tmp_pair = curr_pair[1].split("_", 2);
        if (tmp_pair.length != 1) {
          // pairs with more than 1 underline like smd_via_same_net are not implemented
          continue;
        }
      }

      int first_class_no;
      if (curr_pair[0].equals("wire")) {
        first_class_no = 1; // default class
      } else {
        first_class_no = p_board_rules.clearance_matrix.get_no(curr_pair[0]);
      }
      if (first_class_no < 0) {
        first_class_no = append_clearance_class(p_board_rules, curr_pair[0]);
      }
      int second_class_no;
      if (curr_pair[1].equals("wire")) {
        second_class_no = 1; // default class
      } else {
        second_class_no = p_board_rules.clearance_matrix.get_no(curr_pair[1]);
      }
      if (second_class_no < 0) {
        second_class_no = append_clearance_class(p_board_rules, curr_pair[1]);
      }
      if (p_layer_no < 0) {
        p_board_rules.clearance_matrix.set_value(first_class_no, second_class_no, curr_clearance);
        p_board_rules.clearance_matrix.set_value(second_class_no, first_class_no, curr_clearance);
      } else {
        p_board_rules.clearance_matrix.set_value(
            first_class_no, second_class_no, p_layer_no, curr_clearance);
        p_board_rules.clearance_matrix.set_value(
            second_class_no, first_class_no, p_layer_no, curr_clearance);
      }
    }
    return result;
  }

  static boolean contains_wire_clearance_pair(Collection<String> p_clearance_pairs) {
    for (String curr_pair : p_clearance_pairs) {
      if (curr_pair.startsWith("wire_") || curr_pair.endsWith("_wire")) {
        return true;
      }
    }
    return false;
  }

  private static void create_default_clearance_classes(BoardRules p_board_rules) {
    append_clearance_class(p_board_rules, "via");
    append_clearance_class(p_board_rules, "smd");
    append_clearance_class(p_board_rules, "pin");
    append_clearance_class(p_board_rules, "area");
  }

  private static int append_clearance_class(BoardRules p_board_rules, String p_name) {
    p_board_rules.clearance_matrix.append_class(p_name);
    int result = p_board_rules.clearance_matrix.get_no(p_name);
    app.freerouting.rules.NetClass default_net_class = p_board_rules.get_default_net_class();
    switch (p_name) {
      case "via"  -> default_net_class.default_item_clearance_classes.set(ItemClass.VIA, result);
      case "pin"  -> default_net_class.default_item_clearance_classes.set(ItemClass.PIN, result);
      case "smd"  -> default_net_class.default_item_clearance_classes.set(ItemClass.SMD, result);
      case "area" -> default_net_class.default_item_clearance_classes.set(ItemClass.AREA, result);
    }
    return result;
  }

  /** Returns true, if all clearance values on the 2 input layers are equal. */
  private static boolean clearance_equals(
      ClearanceMatrix p_cl_matrix, int p_layer_1, int p_layer_2) {
    if (p_layer_1 == p_layer_2) {
      return true;
    }
    for (int i = 1; i < p_cl_matrix.get_class_count(); ++i) {
      for (int j = i; j < p_cl_matrix.get_class_count(); ++j) {
        if (p_cl_matrix.get_value(i, j, p_layer_1, false) != p_cl_matrix.get_value(i, j, p_layer_2, false)) {
          return false;
        }
      }
    }
    return true;
  }

  private static boolean insert_keepout(
      Shape.ReadAreaScopeResult p_area,
      ReadScopeParameter p_par,
      KeepoutType p_keepout_type,
      FixedState p_fixed_state) {
    Area keepout_area =
        Shape.transform_area_to_board(p_area.shape_list, p_par.coordinate_transform);
    if (keepout_area.dimension() < 2) {
      System.out.println("Structure.insert_keepout: keepout is not an area at '" + p_area.area_name + "'");
      return true;
    }
    BasicBoard board = p_par.board_handling.get_routing_board();
    if (board == null) {
      System.out.println("Structure.insert_keepout: board not initialized");
      return false;
    }
    Layer curr_layer = (p_area.shape_list.iterator().next()).layer;
    if (curr_layer == Layer.SIGNAL) {
      for (int i = 0; i < board.get_layer_count(); ++i) {
        if (p_par.layer_structure.arr[i].is_signal) {
          insert_keepout(
              board, keepout_area, i, p_area.clearance_class_name, p_keepout_type, p_fixed_state);
        }
      }
    } else if (curr_layer.no >= 0) {
      insert_keepout(
          board,
          keepout_area,
          curr_layer.no,
          p_area.clearance_class_name,
          p_keepout_type,
          p_fixed_state);
    } else {
      System.out.println("Structure.insert_keepout: unknown layer name at '" + p_par.scanner.get_scope_identifier() + "'");
      return false;
    }

    return true;
  }

  private static void insert_keepout(
      BasicBoard p_board,
      Area p_area,
      int p_layer,
      String p_clearance_class_name,
      KeepoutType p_keepout_type,
      FixedState p_fixed_state) {
    int clearance_class_no;
    if (p_clearance_class_name == null) {
      clearance_class_no =
          p_board
              .rules
              .get_default_net_class()
              .default_item_clearance_classes
              .get(ItemClass.AREA);
    } else {
      clearance_class_no = p_board.rules.clearance_matrix.get_no(p_clearance_class_name);
      if (clearance_class_no < 0) {
        System.out.println("Keepout.insert_keepout: clearance class not found at '" + p_clearance_class_name + "'");
        clearance_class_no = BoardRules.clearance_class_none();
      }
    }
    if (p_keepout_type == KeepoutType.via_keepout) {
      p_board.insert_via_obstacle(p_area, p_layer, clearance_class_no, p_fixed_state);
    } else if (p_keepout_type == KeepoutType.place_keepout) {
      p_board.insert_component_obstacle(p_area, p_layer, clearance_class_no, p_fixed_state);
    } else {
      p_board.insert_obstacle(p_area, p_layer, clearance_class_no, p_fixed_state);
    }
  }

  @Override
  public boolean read_scope(ReadScopeParameter p_par) {
    BoardConstructionInfo board_construction_info = new BoardConstructionInfo();

    // If true, components on the back side are rotated before mirroring
    // The correct location is the scope PlaceControl, but Electra writes it here.
    boolean flip_style_rotate_first = false;

    Collection<Shape.ReadAreaScopeResult> keepout_list =
        new LinkedList<>();
    Collection<Shape.ReadAreaScopeResult> via_keepout_list =
        new LinkedList<>();
    Collection<Shape.ReadAreaScopeResult> place_keepout_list =
        new LinkedList<>();

    Object next_token = null;
    for (; ; ) {
      Object prev_token = next_token;
      try {
        next_token = p_par.scanner.next_token();
      } catch (IOException e) {
        //FRLogger.error("Structure.read_scope: IO error scanning file", e);
        return false;
      }
      if (next_token == null) {
        System.out.println("Structure.read_scope: unexpected end of file at '" + p_par.scanner.get_scope_identifier() + "'");
        return false;
      }
      if (next_token == CLOSED_BRACKET) {
        // end of scope
        break;
      }
      boolean read_ok = true;
      if (prev_token == OPEN_BRACKET) {
        if (next_token == Keyword.BOUNDARY) {
          read_boundary_scope(p_par.scanner, board_construction_info);
        } else if (next_token == Keyword.LAYER) {
          read_ok = read_layer_scope(p_par.scanner, board_construction_info, p_par.string_quote);
          if (p_par.layer_structure != null) {
            // correct the layer_structure because another layer isr read
            p_par.layer_structure = new LayerStructure(board_construction_info.layer_info);
          }
        } else if (next_token == Keyword.VIA) {
          p_par.via_padstack_names = read_via_padstacks(p_par.scanner);
        } else if (next_token == Keyword.RULE) {
          board_construction_info.default_rules.addAll(Rule.read_scope(p_par.scanner));
        } else if (next_token == Keyword.KEEPOUT) {
          if (p_par.layer_structure == null) {
            p_par.layer_structure = new LayerStructure(board_construction_info.layer_info);
          }
          keepout_list.add(Shape.read_area_scope(p_par.scanner, p_par.layer_structure, false));
        } else if (next_token == Keyword.VIA_KEEPOUT) {
          if (p_par.layer_structure == null) {
            p_par.layer_structure = new LayerStructure(board_construction_info.layer_info);
          }
          via_keepout_list.add(Shape.read_area_scope(p_par.scanner, p_par.layer_structure, false));
        } else if (next_token == Keyword.PLACE_KEEPOUT) {
          if (p_par.layer_structure == null) {
            p_par.layer_structure = new LayerStructure(board_construction_info.layer_info);
          }
          place_keepout_list.add(
              Shape.read_area_scope(p_par.scanner, p_par.layer_structure, false));
        } else if (next_token == Keyword.PLANE_SCOPE) {
          if (p_par.layer_structure == null) {
            p_par.layer_structure = new LayerStructure(board_construction_info.layer_info);
          }
          Keyword.PLANE_SCOPE.read_scope(p_par);
        } else if (next_token == Keyword.AUTOROUTE_SETTINGS) {
          if (p_par.layer_structure == null) {
            p_par.layer_structure = new LayerStructure(board_construction_info.layer_info);
            p_par.autoroute_settings =
                AutorouteSettings.read_scope(p_par.scanner, p_par.layer_structure);
          }
        } else if (next_token == Keyword.CONTROL) {
          read_ok = read_control_scope(p_par);
        } else if (next_token == Keyword.FLIP_STYLE) {
          flip_style_rotate_first = PlaceControl.read_flip_style_rotate_first(p_par.scanner);
        } else if (next_token == Keyword.SNAP_ANGLE) {

          AngleRestriction snap_angle = read_snap_angle(p_par.scanner);
          if (snap_angle != null) {
            p_par.snap_angle = snap_angle;
          }
        } else {
          skip_scope(p_par.scanner);
        }
      }
      if (!read_ok) {
        return false;
      }
    }

    boolean result = true;
    if (p_par.board_handling.get_routing_board() == null) {
      result = create_board(p_par, board_construction_info);
    }
    RoutingBoard board = p_par.board_handling.get_routing_board();
    if (board == null) {
      return false;
    }
    if (flip_style_rotate_first) {
      board.components.set_flip_style_rotate_first(true);
    }
    FixedState fixed_state;
    if (board.get_test_level() == TestLevel.RELEASE_VERSION) {
      fixed_state = FixedState.SYSTEM_FIXED;
    } else {
      fixed_state = FixedState.USER_FIXED;
    }
    // insert the keepouts
    for (Shape.ReadAreaScopeResult curr_area : keepout_list) {
      if (!insert_keepout(curr_area, p_par, KeepoutType.keepout, fixed_state)) {
        return false;
      }
    }

    for (Shape.ReadAreaScopeResult curr_area : via_keepout_list) {
      if (!insert_keepout(curr_area, p_par, KeepoutType.via_keepout, FixedState.SYSTEM_FIXED)) {
        return false;
      }
    }

    for (Shape.ReadAreaScopeResult curr_area : place_keepout_list) {
      if (!insert_keepout(curr_area, p_par, KeepoutType.place_keepout, FixedState.SYSTEM_FIXED)) {
        return false;
      }
    }

    // insert the planes.
    for (ReadScopeParameter.PlaneInfo plane_info : p_par.plane_list) {
      Net.Id net_id = new Net.Id(plane_info.net_name, 1);
      if (!p_par.netlist.contains(net_id)) {
        Net new_net = p_par.netlist.add_net(net_id);
        if (new_net != null) {
          board.rules.nets.add(new_net.id.name, new_net.id.subnet_number, true);
        }
      }
      app.freerouting.rules.Net curr_net = board.rules.nets.get(plane_info.net_name, 1);
      if (curr_net == null) {
        System.out.println("Plane.read_scope: net not found at '" + p_par.scanner.get_scope_identifier() + "'");
        continue;
      }
      Area plane_area =
          Shape.transform_area_to_board(plane_info.area.shape_list, p_par.coordinate_transform);
      Layer curr_layer = (plane_info.area.shape_list.iterator().next()).layer;
      if (curr_layer.no >= 0) {
        int clearance_class_no;
        if (plane_info.area.clearance_class_name != null) {
          clearance_class_no =
              board.rules.clearance_matrix.get_no(plane_info.area.clearance_class_name);
          if (clearance_class_no < 0) {
            System.out.println("Structure.read_scope: clearance class not found at '" + p_par.scanner.get_scope_identifier() + "'");
            clearance_class_no = BoardRules.clearance_class_none();
          }
        } else {
          clearance_class_no =
              curr_net
                  .get_class()
                  .default_item_clearance_classes
                  .get(ItemClass.AREA);
        }
        int[] net_numbers = new int[1];
        net_numbers[0] = curr_net.net_number;
        board.insert_conduction_area(
            plane_area,
            curr_layer.no,
            net_numbers,
            clearance_class_no,
            false,
            FixedState.SYSTEM_FIXED);
      } else {
        System.out.println("Plane.read_scope: unexpected layer name at '" + p_par.scanner.get_scope_identifier() + "'");
        return false;
      }
    }
    insert_missing_power_planes(board_construction_info.layer_info, p_par.netlist, board);
    
    if (p_par.autoroute_settings != null) {
      p_par.board_handling.get_settings().autoroute_settings = p_par.autoroute_settings;
    }
    return result;
  }

  private boolean create_board(
      ReadScopeParameter p_par, BoardConstructionInfo p_board_construction_info) {
    int layer_count = p_board_construction_info.layer_info.size();
    if (layer_count == 0) {
      System.out.println("Structure.create_board: layers missing in structure scope at '" + p_par.scanner.get_scope_identifier() + "'");
      return false;
    }
    if (p_board_construction_info.bounding_shape == null) {
      // happens if the boundary shape with layer pcb is missing
      if (p_board_construction_info.outline_shapes.isEmpty()) {
        System.out.println("Structure.create_board: outline missing at '" + p_par.scanner.get_scope_identifier() + "'");
        p_par.board_outline_ok = false;
        return false;
      }
      Iterator<Shape> it = p_board_construction_info.outline_shapes.iterator();

      Rectangle bounding_box = it.next().bounding_box();
      while (it.hasNext()) {
        bounding_box = bounding_box.union(it.next().bounding_box());
      }
      p_board_construction_info.bounding_shape = bounding_box;
    }
    Rectangle bounding_box = p_board_construction_info.bounding_shape.bounding_box();
    app.freerouting.board.Layer[] board_layer_arr = new app.freerouting.board.Layer[layer_count];
    Iterator<Layer> it = p_board_construction_info.layer_info.iterator();
    for (int i = 0; i < layer_count; ++i) {
      Layer curr_layer = it.next();
      if (curr_layer.no < 0 || curr_layer.no >= layer_count) {
        System.out.println("Structure.create_board: illegal layer number at '" + p_par.scanner.get_scope_identifier() + "'");
        return false;
      }
      board_layer_arr[i] = new app.freerouting.board.Layer(curr_layer.name, curr_layer.is_signal);
    }
    app.freerouting.board.LayerStructure board_layer_structure =
        new app.freerouting.board.LayerStructure(board_layer_arr);
    p_par.layer_structure = new LayerStructure(p_board_construction_info.layer_info);

    // Calculate an approximate scaling between dsn coordinates and board coordinates.
    int scale_factor = Math.max(p_par.resolution, 1);

    double max_coor = 0;
    for (int i = 0; i < 4; ++i) {
      max_coor = Math.max(max_coor, Math.abs(bounding_box.coor[i] * p_par.resolution));
    }
    if (max_coor == 0) {
      p_par.board_outline_ok = false;
      return false;
    }
    // make scalefactor smaller, if there is a danger of integer overflow.
    while (5 * max_coor >= Limits.CRIT_INT) {
      scale_factor /= 10;
      max_coor /= 10;
    }

    p_par.coordinate_transform = new CoordinateTransform(scale_factor, 0, 0);

    IntBox bounds = (IntBox) bounding_box.transform_to_board(p_par.coordinate_transform);
    bounds = bounds.offset(1000);

    Collection<PolylineShape> board_outline_shapes = new LinkedList<>();
    for (Shape curr_shape : p_board_construction_info.outline_shapes) {
      if (curr_shape instanceof PolygonPath) {
        PolygonPath curr_path = (PolygonPath) curr_shape;
        if (curr_path.width != 0) {
          // set the width to 0, because the offset function used in transform_to_board is not
          // implemented
          // for shapes, which are not convex.
          curr_shape = new PolygonPath(curr_path.layer, 0, curr_path.coordinate_arr);
        }
      }
      PolylineShape curr_board_shape =
          (PolylineShape) curr_shape.transform_to_board(p_par.coordinate_transform);
      if (curr_board_shape.dimension() > 0) {
        board_outline_shapes.add(curr_board_shape);
      }
    }
    if (board_outline_shapes.isEmpty()) {
      // construct an outline from the bounding_shape, if the outline is missing.
      PolylineShape curr_board_shape =
          (PolylineShape)
              p_board_construction_info.bounding_shape.transform_to_board(
                  p_par.coordinate_transform);
      board_outline_shapes.add(curr_board_shape);
    }
    Collection<PolylineShape> hole_shapes = separate_holes(board_outline_shapes);
    ClearanceMatrix clearance_matrix =
        ClearanceMatrix.get_default_instance(board_layer_structure, 0);
    BoardRules board_rules =
        new BoardRules(board_layer_structure, clearance_matrix);
    Communication.SpecctraParserInfo specctra_parser_info =
        new Communication.SpecctraParserInfo(
            p_par.string_quote,
            p_par.host_cad,
            p_par.host_version,
            p_par.constants,
            p_par.write_resolution,
            p_par.dsn_file_generated_by_host);
    Communication board_communication =
        new Communication(
            p_par.unit,
            p_par.resolution,
            specctra_parser_info,
            p_par.coordinate_transform,
            p_par.item_id_no_generator,
            p_par.observers);

    if (board_communication.host_is_old_kicad())
    {
      System.out.println("Structure.create_board: The DSN file was exported from an old KiCad version that has known compatibility issues. Please update KiCad to version 6 or newer.");
    }

    PolylineShape[] outline_shape_arr = new PolylineShape[board_outline_shapes.size()];
    Iterator<PolylineShape> it2 = board_outline_shapes.iterator();
    for (int i = 0; i < outline_shape_arr.length; ++i) {
      outline_shape_arr[i] = it2.next();
    }
    update_board_rules(p_par, p_board_construction_info, board_rules);
    board_rules.set_trace_angle_restriction(p_par.snap_angle);
    p_par.board_handling.create_board(
        bounds,
        board_layer_structure,
        outline_shape_arr,
        p_board_construction_info.outline_clearance_class_name,
        board_rules,
        board_communication,
        p_par.test_level);

    BasicBoard board = p_par.board_handling.get_routing_board();

    // Insert the holes in the board outline as keepouts.
    for (PolylineShape curr_outline_hole : hole_shapes) {
      for (int i = 0; i < board_layer_structure.arr.length; ++i) {
        board.insert_obstacle(curr_outline_hole, i, 0, FixedState.SYSTEM_FIXED);
      }
    }

    return true;
  }

  enum KeepoutType {
    keepout,
    via_keepout,
    place_keepout
  }

  private static class BoardConstructionInfo {

    Collection<Layer> layer_info = new LinkedList<>();
    Shape bounding_shape;
    List<Shape> outline_shapes = new LinkedList<>();
    String outline_clearance_class_name;
    int found_layer_count = 0;
    Collection<Rule> default_rules = new LinkedList<>();
    Collection<LayerRule> layer_dependent_rules = new LinkedList<>();
  }

  private static class LayerRule {

    final String layer_name;
    final Collection<Rule> rule;
    LayerRule(String p_layer_name, Collection<Rule> p_rule) {
      layer_name = p_layer_name;
      rule = p_rule;
    }
  }

  /** Used to separate the holes in the outline. */
  private static class OutlineShape {

    final PolylineShape shape;
    final IntBox bounding_box;
    final TileShape[] convex_shapes;
    boolean is_hole;
    public OutlineShape(PolylineShape p_shape) {
      shape = p_shape;
      bounding_box = p_shape.bounding_box();
      convex_shapes = p_shape.split_to_convex();
      is_hole = false;
    }

    /** Returns true, if this shape contains all corners of p_other_shape. */
    private boolean contains_all_corners(OutlineShape p_other_shape) {
      if (this.convex_shapes == null) {
        // calculation of the convex shapes failed
        return false;
      }
      int corner_count = p_other_shape.shape.border_line_count();
      for (int i = 0; i < corner_count; ++i) {
        Point curr_corner = p_other_shape.shape.corner(i);
        boolean is_contained = false;
        for (int j = 0; j < this.convex_shapes.length; ++j) {
          if (this.convex_shapes[j].contains(curr_corner)) {
            is_contained = true;
            break;
          }
        }
        if (!is_contained) {
          return false;
        }
      }
      return true;
    }
  }
}
