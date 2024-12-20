package app.freerouting.designforms.specctra;

import java.io.IOException;
import java.util.Iterator;
import java.util.Map;
import java.util.TreeMap;

/** Handles the placement data of a library component. */
public class Component extends ScopeKeyword {

  /** Creates a new instance of Component */
  public Component() {
    super("component");
  }

  /** Used also when reading a session file. */
  public static ComponentPlacement read_scope(IJFlexScanner p_scanner) throws IOException {
    Object next_token = p_scanner.next_token();
    if (!(next_token instanceof String)) {
      System.out.println("Component.read_scope: component name expected at '" + p_scanner.get_scope_identifier() + "'");
      return null;
    }
    String name = (String) next_token;
    ComponentPlacement component_placement = new ComponentPlacement(name);
    Object prev_token = next_token;
    next_token = p_scanner.next_token();
    while (next_token != CLOSED_BRACKET) {
      if (prev_token == OPEN_BRACKET && next_token == PLACE) {
        ComponentPlacement.ComponentLocation next_location = read_place_scope(p_scanner);
        if (next_location != null) {
          component_placement.locations.add(next_location);
        }
      }
      prev_token = next_token;
      next_token = p_scanner.next_token();
    }
    return component_placement;
  }

  private static ComponentPlacement.ComponentLocation read_place_scope(IJFlexScanner p_scanner) {
    try {
      Map<String, ComponentPlacement.ItemClearanceInfo> pin_infos =
          new TreeMap<>();
      Map<String, ComponentPlacement.ItemClearanceInfo> keepout_infos =
          new TreeMap<>();
      Map<String, ComponentPlacement.ItemClearanceInfo> via_keepout_infos =
          new TreeMap<>();
      Map<String, ComponentPlacement.ItemClearanceInfo> place_keepout_infos =
          new TreeMap<>();

      String name = p_scanner.next_string(true);

      Object next_token;
      double[] location = new double[2];
      for (int i = 0; i < 2; ++i) {
        next_token = p_scanner.next_token();
        if (next_token instanceof Double) {
          location[i] = (Double) next_token;
        } else if (next_token instanceof Integer) {
          location[i] = (Integer) next_token;
        } else if (next_token == CLOSED_BRACKET) {
          // component is not yet placed
          return new ComponentPlacement.ComponentLocation(
              name,
              null,
              true,
              0,
              false,
              pin_infos,
              keepout_infos,
              via_keepout_infos,
              place_keepout_infos);
        } else {
          System.out.println("Component.read_place_scope: Double was expected as the second and third parameter of the component/place command at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
      }

      next_token = p_scanner.next_token();
      boolean is_front = true;
      if (next_token == BACK) {
        is_front = false;
      } else if (next_token != FRONT) {
        System.out.println("Component.read_place_scope: Keyword.FRONT expected at '" + p_scanner.get_scope_identifier() + "'");
      }
      double rotation;
      next_token = p_scanner.next_token();
      if (next_token instanceof Double) {
        rotation = (Double) next_token;
      } else if (next_token instanceof Integer) {
        rotation = (Integer) next_token;
      } else {
        System.out.println("Component.read_place_scope: number expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      boolean position_fixed = false;
      next_token = p_scanner.next_token();
      while (next_token == OPEN_BRACKET) {
        next_token = p_scanner.next_token();
        if (next_token == LOCK_TYPE) {
          position_fixed = read_lock_type(p_scanner);
        } else if (next_token == PIN) {
          ComponentPlacement.ItemClearanceInfo curr_pin_info = read_item_clearance_info(p_scanner);
          if (curr_pin_info == null) {
            return null;
          }
          pin_infos.put(curr_pin_info.name, curr_pin_info);
        } else if (next_token == KEEPOUT) {
          ComponentPlacement.ItemClearanceInfo curr_keepout_info =
              read_item_clearance_info(p_scanner);
          if (curr_keepout_info == null) {
            return null;
          }
          keepout_infos.put(curr_keepout_info.name, curr_keepout_info);
        } else if (next_token == VIA_KEEPOUT) {
          ComponentPlacement.ItemClearanceInfo curr_keepout_info =
              read_item_clearance_info(p_scanner);
          if (curr_keepout_info == null) {
            return null;
          }
          via_keepout_infos.put(curr_keepout_info.name, curr_keepout_info);
        } else if (next_token == PLACE_KEEPOUT) {
          ComponentPlacement.ItemClearanceInfo curr_keepout_info =
              read_item_clearance_info(p_scanner);
          if (curr_keepout_info == null) {
            return null;
          }
          place_keepout_infos.put(curr_keepout_info.name, curr_keepout_info);
        } else {
          skip_scope(p_scanner);
        }
        next_token = p_scanner.next_token();
      }
      if (next_token != CLOSED_BRACKET) {
        System.out.println("Component.read_place_scope: ) expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      return new ComponentPlacement.ComponentLocation(
              name,
              location,
              is_front,
              rotation,
              position_fixed,
              pin_infos,
              keepout_infos,
              via_keepout_infos,
              place_keepout_infos);
    } catch (IOException e) {
      //FRLogger.error("Component.read_scope: IO error scanning file", e);
      return null;
    }
  }

  private static ComponentPlacement.ItemClearanceInfo read_item_clearance_info(
      IJFlexScanner p_scanner) throws IOException {
    p_scanner.yybegin(SpecctraDsnFileReader.NAME);
    Object next_token = p_scanner.next_token();
    if (!(next_token instanceof String)) {
      System.out.println("Component.read_item_clearance_info: String expected at '" + p_scanner.get_scope_identifier() + "'");
      return null;
    }
    String name = (String) next_token;
    String cl_class_name = null;
    next_token = p_scanner.next_token();
    while (next_token == OPEN_BRACKET) {
      next_token = p_scanner.next_token();
      if (next_token == CLEARANCE_CLASS) {
        cl_class_name = DsnFile.read_string_scope(p_scanner);
      } else {
        skip_scope(p_scanner);
      }
      next_token = p_scanner.next_token();
    }
    if (next_token != CLOSED_BRACKET) {
      System.out.println("Component.read_item_clearance_info: ) expected at '" + p_scanner.get_scope_identifier() + "'");
      return null;
    }
    if (cl_class_name == null) {
      System.out.println("Component.read_item_clearance_info: clearance class name not found at '" + p_scanner.get_scope_identifier() + "'");
      return null;
    }
    return new ComponentPlacement.ItemClearanceInfo(name, cl_class_name);
  }

  private static boolean read_lock_type(IJFlexScanner p_scanner) throws IOException {
    boolean result = false;
    for (; ; ) {
      Object next_token = p_scanner.next_token();
      if (next_token == CLOSED_BRACKET) {
        break;
      }
      if (next_token == POSITION) {
        result = true;
      }
    }
    return result;
  }

  /** Overwrites the function read_scope in ScopeKeyword */
  @Override
  public boolean read_scope(ReadScopeParameter p_par) {
    try {
      ComponentPlacement component_placement = read_scope(p_par.scanner);
      if (component_placement == null) {
        return false;
      }
      p_par.placement_list.add(component_placement);
    } catch (IOException e) {
      //FRLogger.error("Component.read_scope: IO error scanning file", e);
      return false;
    }
    return true;
  }
}
