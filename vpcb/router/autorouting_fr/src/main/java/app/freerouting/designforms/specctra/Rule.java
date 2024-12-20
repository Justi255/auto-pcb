package app.freerouting.designforms.specctra;

import app.freerouting.rules.BoardRules;
import app.freerouting.rules.ClearanceMatrix;

import java.io.IOException;
import java.util.Collection;
import java.util.LinkedList;
import java.util.List;
import java.util.Objects;

/** Class for reading and writing rule scopes from dsn-files. */
public abstract class Rule {
  /** Returns a collection of objects of class Rule. */
  public static Collection<Rule> read_scope(IJFlexScanner p_scanner) {
    Collection<Rule> result = new LinkedList<>();
    Object current_token = null;
    for (; ; ) {
      Object prev_token = current_token;
      try {
        current_token = p_scanner.next_token();
      } catch (IOException e) {
        //FRLogger.error("Rule.read_scope: IO error scanning file", e);
        return null;
      }
      if (current_token == null) {
        System.out.println("Rule.read_scope: unexpected end of file at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      if (current_token == Keyword.CLOSED_BRACKET) {
        // end of scope
        break;
      }

      if (prev_token == Keyword.OPEN_BRACKET) {
        // every rule starts with a "("
        Rule curr_rule = null;
        if (current_token == Keyword.WIDTH) {
          // this is a "(width" rule
          curr_rule = read_width_rule(p_scanner);
        } else if (current_token == Keyword.CLEARANCE) {
          // this is a "(clear" rule
          curr_rule = read_clearance_rule(p_scanner);
        } else {
          ScopeKeyword.skip_scope(p_scanner);
        }

        if (curr_rule != null) {
          result.add(curr_rule);
        }
      }
    }
    return result;
  }

  /** Reads a LayerRule from dsn-file. */
  public static LayerRule read_layer_rule_scope(IJFlexScanner p_scanner) {
    try {
      Collection<String> layer_names = new LinkedList<>();
      Collection<Rule> rule_list = new LinkedList<>();
      for (; ; ) {
        p_scanner.yybegin(SpecctraDsnFileReader.LAYER_NAME);
        Object next_token = p_scanner.next_token();
        if (next_token == Keyword.OPEN_BRACKET) {
          break;
        }
        if (!(next_token instanceof String)) {

          System.out.println("Rule.read_layer_rule_scope: string expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
        layer_names.add((String) next_token);
      }
      for (; ; ) {
        Object next_token = p_scanner.next_token();
        if (next_token == Keyword.CLOSED_BRACKET) {
          break;
        }
        if (next_token != Keyword.RULE) {

          System.out.println("Rule.read_layer_rule_scope: rule expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
        rule_list.addAll(read_scope(p_scanner));
      }
      return new LayerRule(layer_names, rule_list);
    } catch (IOException e) {
      //FRLogger.error("Rule.read_layer_rule_scope: IO error scanning file", e);
      return null;
    }
  }

  public static WidthRule read_width_rule(IJFlexScanner p_scanner) {
    double value = p_scanner.next_double();

    if (!p_scanner.next_closing_bracket()) {
      return null;
    }

    return new WidthRule(value);
  }

  public static ClearanceRule read_clearance_rule(IJFlexScanner p_scanner) {
    try {
      double value = p_scanner.next_double();

      Collection<String> class_pairs = new LinkedList<>();
      Object next_token = p_scanner.next_token();
      if (next_token != Keyword.CLOSED_BRACKET) {
        // look for "(type"
        if (next_token != Keyword.OPEN_BRACKET) {
          System.out.println("Rule.read_clearance_rule: ( expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
        next_token = p_scanner.next_token();
        if (next_token != Keyword.TYPE) {
          System.out.println("Rule.read_clearance_rule: type expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }

        class_pairs.addAll(List.of(p_scanner.next_string_list(DsnFile.CLASS_CLEARANCE_SEPARATOR)));

        // check the closing ")" of "(type"
        if (!p_scanner.next_closing_bracket()) {
          System.out.println("Rule.read_clearance_rule: closing bracket expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }

        // check the closing ")" of "(clear"
        if (!p_scanner.next_closing_bracket()) {
          System.out.println("Rule.read_clearance_rule: closing bracket expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
      }

      return new ClearanceRule(value, class_pairs);
    } catch (IOException e) {
      //FRLogger.error("Rule.read_clearance_rule: IO error scanning file", e);
      return null;
    }
  }

  public static class WidthRule extends Rule {
    final double value;

    public WidthRule(double p_value) {
      value = p_value;
    }
  }

  public static class ClearanceRule extends Rule {
    final double value;
    final Collection<String> clearance_class_pairs;
    public ClearanceRule(double p_value, Collection<String> p_class_pairs) {
      value = p_value;
      clearance_class_pairs = p_class_pairs;
    }
  }

  public static class LayerRule {
    final Collection<String> layer_names;
    final Collection<Rule> rules;
    LayerRule(Collection<String> p_layer_names, Collection<Rule> p_rules) {
      layer_names = p_layer_names;
      rules = p_rules;
    }
  }
}
