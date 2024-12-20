package app.freerouting.designforms.specctra;

import app.freerouting.board.Item;
import app.freerouting.library.Padstack;

import java.io.IOException;
import java.util.Collection;
import java.util.Iterator;
import java.util.LinkedList;

/** Class for reading and writing package scopes from dsn-files. */
public class Package {

  public final String name;
  /** List of objects of type PinInfo. */
  public final PinInfo[] pin_info_arr;
  /** The outline of the package. */
  public final Collection<Shape> outline;
  /** Collection of keepoouts belonging to this package */
  public final Collection<Shape.ReadAreaScopeResult> keepouts;
  /** Collection of via keepoouts belonging to this package */
  public final Collection<Shape.ReadAreaScopeResult> via_keepouts;
  /** Collection of place keepoouts belonging to this package */
  public final Collection<Shape.ReadAreaScopeResult> place_keepouts;
  /** If false, the package is placed on the back side of the board */
  public final boolean is_front;

  /** Creates a new instance of Package */
  public Package(
      String p_name,
      PinInfo[] p_pin_info_arr,
      Collection<Shape> p_outline,
      Collection<Shape.ReadAreaScopeResult> p_keepouts,
      Collection<Shape.ReadAreaScopeResult> p_via_keepouts,
      Collection<Shape.ReadAreaScopeResult> p_place_keepouts,
      boolean p_is_front) {
    name = p_name;
    pin_info_arr = p_pin_info_arr;
    outline = p_outline;
    keepouts = p_keepouts;
    via_keepouts = p_via_keepouts;
    place_keepouts = p_place_keepouts;
    is_front = p_is_front;
  }

  public static Package read_scope(IJFlexScanner p_scanner, LayerStructure p_layer_structure) {
    try {
      boolean is_front = true;
      Collection<Shape> outline = new LinkedList<>();
      Collection<Shape.ReadAreaScopeResult> keepouts = new LinkedList<>();
      Collection<Shape.ReadAreaScopeResult> via_keepouts =
          new LinkedList<>();
      Collection<Shape.ReadAreaScopeResult> place_keepouts =
          new LinkedList<>();
      Object next_token = p_scanner.next_token();
      if (!(next_token instanceof String)) {
        System.out.println("Package.read_scope: String expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      String package_name = (String) next_token;
      p_scanner.set_scope_identifier(package_name);
      Collection<PinInfo> pin_info_list = new LinkedList<>();
      for (; ; ) {
        Object prev_token = next_token;
        next_token = p_scanner.next_token();

        if (next_token == null) {
          System.out.println("Package.read_scope: unexpected end of file at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
        if (next_token == Keyword.CLOSED_BRACKET) {
          // end of scope
          break;
        }
        if (prev_token == Keyword.OPEN_BRACKET) {
          if (next_token == Keyword.PIN) {
            PinInfo next_pin = read_pin_info(p_scanner);
            if (next_pin == null) {
              return null;
            }
            pin_info_list.add(next_pin);
          } else if (next_token == Keyword.SIDE) {
            is_front = read_placement_side(p_scanner);
          } else if (next_token == Keyword.OUTLINE) {
            Shape curr_shape = Shape.read_scope(p_scanner, p_layer_structure);
            if (curr_shape != null) {
              outline.add(curr_shape);
            }
            // overread closing bracket
            next_token = p_scanner.next_token();
            if (next_token != Keyword.CLOSED_BRACKET) {
              System.out.println("Package.read_scope: closed bracket expected at '" + p_scanner.get_scope_identifier() + "'");
              return null;
            }
          } else if (next_token == Keyword.KEEPOUT) {
            Shape.ReadAreaScopeResult keepout_area =
                Shape.read_area_scope(p_scanner, p_layer_structure, false);
            if (keepout_area != null) {
              keepouts.add(keepout_area);
            } else {
              System.out.println("Package.read_scope: could not read keepout area of package '"+package_name+"'");
            }
          } else if (next_token == Keyword.VIA_KEEPOUT) {
            Shape.ReadAreaScopeResult keepout_area =
                Shape.read_area_scope(p_scanner, p_layer_structure, false);
            if (keepout_area != null) {
              via_keepouts.add(keepout_area);
            }
          } else if (next_token == Keyword.PLACE_KEEPOUT) {
            Shape.ReadAreaScopeResult keepout_area =
                Shape.read_area_scope(p_scanner, p_layer_structure, false);
            if (keepout_area != null) {
              place_keepouts.add(keepout_area);
            }
          } else {
            ScopeKeyword.skip_scope(p_scanner);
          }
        }
      }
      PinInfo[] pin_info_arr = new PinInfo[pin_info_list.size()];
      Iterator<PinInfo> it = pin_info_list.iterator();
      for (int i = 0; i < pin_info_arr.length; ++i) {
        pin_info_arr[i] = it.next();
      }
      return new Package(
          package_name, pin_info_arr, outline, keepouts, via_keepouts, place_keepouts, is_front);
    } catch (IOException e) {
      //FRLogger.error("Package.read_scope: IO error scanning file", e);
      return null;
    }
  }

  /** Reads the information of a single pin in a package. */
  private static PinInfo read_pin_info(IJFlexScanner p_scanner) {
    try {
      // Read the padstack name.
      p_scanner.yybegin(SpecctraDsnFileReader.NAME);
      Object next_token = p_scanner.next_token();
      if (!(next_token instanceof String) && !(next_token instanceof Integer)) {
        System.out.println("Package.read_pin_info: String or Integer expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      String padstack_name = next_token.toString();
      double rotation = 0;

      p_scanner.yybegin(
          SpecctraDsnFileReader.NAME); // to be able to handle pin names starting with a digit.
      next_token = p_scanner.next_token();
      if (next_token == Keyword.OPEN_BRACKET) {
        // read the padstack rotation
        next_token = p_scanner.next_token();
        if (next_token == Keyword.ROTATE) {
          rotation = read_rotation(p_scanner);
        } else {
          ScopeKeyword.skip_scope(p_scanner);
        }
        p_scanner.yybegin(SpecctraDsnFileReader.NAME);
        next_token = p_scanner.next_token();
      }
      // Read the pin name.
      if (!(next_token instanceof String) && !(next_token instanceof Integer)) {
        System.out.println("Package.read_pin_info: String or Integer expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      String pin_name = next_token.toString();

      double[] pin_coor = new double[2];
      for (int i = 0; i < 2; ++i) {
        next_token = p_scanner.next_token();
        if (next_token instanceof Double) {
          pin_coor[i] = (Double) next_token;
        } else if (next_token instanceof Integer) {
          pin_coor[i] = (Integer) next_token;
        } else {
          System.out.println("Package.read_pin_info: number expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
      }
      // Handle scopes at the end of the pin scope.
      for (; ; ) {
        Object prev_token = next_token;
        next_token = p_scanner.next_token();

        if (next_token == null) {
          System.out.println("Package.read_pin_info: unexpected end of file at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
        if (next_token == Keyword.CLOSED_BRACKET) {
          // end of scope
          break;
        }
        if (prev_token == Keyword.OPEN_BRACKET) {
          if (next_token == Keyword.ROTATE) {
            rotation = read_rotation(p_scanner);
          } else {
            ScopeKeyword.skip_scope(p_scanner);
          }
        }
      }
      return new PinInfo(padstack_name, pin_name, pin_coor, rotation);
    } catch (IOException e) {
      //FRLogger.error("Package.read_pin_info: IO error while scanning file", e);
      return null;
    }
  }

  private static double read_rotation(IJFlexScanner p_scanner) {
    double result = 0;

    try {
      String next_string = p_scanner.next_string();
      result = Double.parseDouble(next_string);

      // Overread The closing bracket.
      Object next_token = p_scanner.next_token();
      if (next_token != Keyword.CLOSED_BRACKET) {
        System.out.println("Package.read_rotation: closing bracket expected at '" + p_scanner.get_scope_identifier() + "'");
      }
    } catch (IOException e) {
      //FRLogger.error("Package.read_rotation: IO error while scanning file", e);
    }

    return result;
  }

  private static boolean read_placement_side(IJFlexScanner p_scanner) throws IOException {
    Object next_token = p_scanner.next_token();
    boolean result = (next_token != Keyword.BACK);

    next_token = p_scanner.next_token();
    if (next_token != Keyword.CLOSED_BRACKET) {
      System.out.println("Package.read_placement_side: closing bracket expected at '" + p_scanner.get_scope_identifier() + "'");
    }
    return result;
  }

  /** Describes the Iinformation of a pin in a package. */
  public static class PinInfo {
    /** Phe name of the pastack of this pin. */
    public final String padstack_name;
    /** Phe name of this pin. */
    public final String pin_name;
    /** The x- and y-coordinates relative to the package location. */
    public final double[] rel_coor;
    /** The rotation of the pin relative to the package. */
    public final double rotation;
    PinInfo(String p_padstack_name, String p_pin_name, double[] p_rel_coor, double p_rotation) {
      padstack_name = p_padstack_name;
      pin_name = p_pin_name;
      rel_coor = p_rel_coor;
      rotation = p_rotation;
    }
  }
}
