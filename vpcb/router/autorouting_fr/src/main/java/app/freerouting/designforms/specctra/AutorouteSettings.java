package app.freerouting.designforms.specctra;

import java.io.IOException;

public class AutorouteSettings {

  static app.freerouting.interactive.AutorouteSettings read_scope(
      IJFlexScanner p_scanner, LayerStructure p_layer_structure) {
    app.freerouting.interactive.AutorouteSettings result =
        new app.freerouting.interactive.AutorouteSettings(p_layer_structure.arr.length);
    boolean with_fanout = false;
    boolean with_autoroute = true;
    boolean with_postroute = true;
    Object next_token = null;
    for (; ; ) {
      Object prev_token = next_token;
      try {
        next_token = p_scanner.next_token();
      } catch (IOException e) {
        //FRLogger.error("AutorouteSettings.read_scope: IO error scanning file", e);
        return null;
      }
      if (next_token == null) {
        System.out.println("AutorouteSettings.read_scope: unexpected end of file at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      if (next_token == Keyword.CLOSED_BRACKET) {
        // end of scope
        break;
      }
      if (prev_token == Keyword.OPEN_BRACKET) {
        if (next_token == Keyword.FANOUT) {
          with_fanout = DsnFile.read_on_off_scope(p_scanner);
        } else if (next_token == Keyword.AUTOROUTE) {
          with_autoroute = DsnFile.read_on_off_scope(p_scanner);
        } else if (next_token == Keyword.POSTROUTE) {
          with_postroute = DsnFile.read_on_off_scope(p_scanner);
        } else if (next_token == Keyword.VIAS) {
          result.set_vias_allowed(DsnFile.read_on_off_scope(p_scanner));
        } else if (next_token == Keyword.VIA_COSTS) {
          result.set_via_costs(DsnFile.read_integer_scope(p_scanner));
        } else if (next_token == Keyword.PLANE_VIA_COSTS) {
          result.set_plane_via_costs(DsnFile.read_integer_scope(p_scanner));
        } else if (next_token == Keyword.START_RIPUP_COSTS) {
          result.set_start_ripup_costs(DsnFile.read_integer_scope(p_scanner));
        } else if (next_token == Keyword.START_PASS_NO) {
          result.set_start_pass_no(DsnFile.read_integer_scope(p_scanner));
        } else if (next_token == Keyword.LAYER_RULE) {
          result = read_layer_rule(p_scanner, p_layer_structure, result);
          if (result == null) {
            return null;
          }
        } else {
          ScopeKeyword.skip_scope(p_scanner);
        }
      }
    }
    result.set_with_fanout(with_fanout);
    result.set_with_autoroute(with_autoroute);
    result.set_with_postroute(with_postroute);
    return result;
  }

  static app.freerouting.interactive.AutorouteSettings read_layer_rule(
      IJFlexScanner p_scanner,
      LayerStructure p_layer_structure,
      app.freerouting.interactive.AutorouteSettings p_settings) {
    p_scanner.yybegin(SpecctraDsnFileReader.NAME);
    Object next_token;
    try {
      next_token = p_scanner.next_token();
    } catch (IOException e) {
      //FRLogger.error("AutorouteSettings.read_layer_rule: IO error scanning file", e);
      return null;
    }
    if (!(next_token instanceof String)) {
      System.out.println("AutorouteSettings.read_layer_rule: String expected at '" + p_scanner.get_scope_identifier() + "'");
      return null;
    }
    int layer_no = p_layer_structure.get_no((String) next_token);
    if (layer_no < 0) {
      System.out.println("AutorouteSettings.read_layer_rule: layer not found at '" + p_scanner.get_scope_identifier() + "'");
      return null;
    }
    for (; ; ) {
      Object prev_token = next_token;
      try {
        next_token = p_scanner.next_token();
      } catch (IOException e) {
        //FRLogger.error("AutorouteSettings.read_layer_rule: IO error scanning file", e);
        return null;
      }
      if (next_token == null) {
        System.out.println("AutorouteSettings.read_layer_rule: unexpected end of file at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      if (next_token == Keyword.CLOSED_BRACKET) {
        // end of scope
        break;
      }
      if (prev_token == Keyword.OPEN_BRACKET) {
        if (next_token == Keyword.ACTIVE) {
          p_settings.set_layer_active(layer_no, DsnFile.read_on_off_scope(p_scanner));
        } else if (next_token == Keyword.PREFERRED_DIRECTION) {
          try {
            boolean pref_dir_is_horizontal = true;
            next_token = p_scanner.next_token();
            if (next_token == Keyword.VERTICAL) {
              pref_dir_is_horizontal = false;
            } else if (next_token != Keyword.HORIZONTAL) {
              System.out.println("AutorouteSettings.read_layer_rule: unexpected key word at '" + p_scanner.get_scope_identifier() + "'");
              return null;
            }
            p_settings.set_preferred_direction_is_horizontal(layer_no, pref_dir_is_horizontal);
            next_token = p_scanner.next_token();
            if (next_token != Keyword.CLOSED_BRACKET) {
              System.out.println("AutorouteSettings.read_layer_rule: closing bracket expected at '" + p_scanner.get_scope_identifier() + "'");
              return null;
            }
          } catch (IOException e) {
            //FRLogger.error("AutorouteSettings.read_layer_rule: IO error scanning file", e);
            return null;
          }
        } else if (next_token == Keyword.PREFERRED_DIRECTION_TRACE_COSTS) {
          p_settings.set_preferred_direction_trace_costs(
              layer_no, DsnFile.read_float_scope(p_scanner));
        } else if (next_token == Keyword.AGAINST_PREFERRED_DIRECTION_TRACE_COSTS) {
          p_settings.set_against_preferred_direction_trace_costs(
              layer_no, DsnFile.read_float_scope(p_scanner));
        } else {
          ScopeKeyword.skip_scope(p_scanner);
        }
      }
    }
    return p_settings;
  }
}
