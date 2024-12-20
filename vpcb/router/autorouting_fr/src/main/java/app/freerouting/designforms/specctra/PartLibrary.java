package app.freerouting.designforms.specctra;

import java.io.IOException;
import java.util.Collection;
import java.util.LinkedList;
import java.util.SortedSet;
import java.util.TreeSet;

public class PartLibrary extends ScopeKeyword {

  /** Creates a new instance of PartLibrary */
  public PartLibrary() {
    super("part_library");
  }

  @Override
  public boolean read_scope(ReadScopeParameter p_par) {
    Object next_token = null;
    for (; ; ) {
      Object prev_token = next_token;
      try {
        next_token = p_par.scanner.next_token();
      } catch (IOException e) {
        //FRLogger.error("PartLibrary.read_scope: IO error scanning file", e);
        return false;
      }
      if (next_token == null) {
        System.out.println("PartLibrary.read_scope: unexpected end of file at '" + p_par.scanner.get_scope_identifier() + "'");
        return false;
      }
      if (next_token == CLOSED_BRACKET) {
        // end of scope
        break;
      }
      if (prev_token == OPEN_BRACKET) {
        if (next_token == LOGICAL_PART_MAPPING) {
          LogicalPartMapping next_mapping = read_logical_part_mapping(p_par.scanner);
          if (next_mapping == null) {
            return false;
          }
          p_par.logical_part_mappings.add(next_mapping);
        } else if (next_token == LOGICAL_PART) {
          LogicalPart next_part = read_logical_part(p_par.scanner);
          if (next_part == null) {
            return false;
          }
          p_par.logical_parts.add(next_part);
        } else {
          skip_scope(p_par.scanner);
        }
      }
    }
    return true;
  }

  /** Reads the component list of a logical part mapping. Returns null, if an error occurred. */
  private LogicalPartMapping read_logical_part_mapping(IJFlexScanner p_scanner) {
    try {
      Object next_token = p_scanner.next_token();
      if (!(next_token instanceof String)) {
        System.out.println("PartLibrary.read_logical_part_mapping: string expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      String name = (String) next_token;
      next_token = p_scanner.next_token();
      if (next_token != OPEN_BRACKET) {
        System.out.println("PartLibrary.read_logical_part_mapping: open bracket expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      next_token = p_scanner.next_token();
      if (next_token != COMPONENT_SCOPE) {
        System.out.println("PartLibrary.read_logical_part_mapping: Keyword.COMPONENT_SCOPE expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      SortedSet<String> result = new TreeSet<>();
      for (; ; ) {
        p_scanner.yybegin(SpecctraDsnFileReader.NAME);
        next_token = p_scanner.next_token();
        if (next_token == CLOSED_BRACKET) {
          break;
        }
        if (!(next_token instanceof String)) {
          System.out.println("PartLibrary.read_logical_part_mapping: string expected at '" + p_scanner.get_scope_identifier() + "'");
          return null;
        }
        result.add((String) next_token);
      }
      next_token = p_scanner.next_token();
      if (next_token != CLOSED_BRACKET) {
        System.out.println("PartLibrary.read_logical_part_mapping: closing bracket expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      return new LogicalPartMapping(name, result);
    } catch (IOException e) {
      //FRLogger.error("PartLibrary.read_logical_part_mapping: IO error scanning file", e);
      return null;
    }
  }

  private LogicalPart read_logical_part(IJFlexScanner p_scanner) {
    Collection<PartPin> part_pins = new LinkedList<>();
    Object next_token;
    try {
      next_token = p_scanner.next_token();
    } catch (IOException e) {
      //FRLogger.error("PartLibrary.read_logical_part: IO error scanning file", e);
      return null;
    }
    if (!(next_token instanceof String)) {
      System.out.println("PartLibrary.read_logical_part: string expected at '" + p_scanner.get_scope_identifier() + "'");
      return null;
    }
    String part_name = (String) next_token;
    p_scanner.set_scope_identifier(part_name);
    for (; ; ) {
      Object prev_token = next_token;
      try {
        next_token = p_scanner.next_token();
      } catch (IOException e) {
        //FRLogger.error("PartLibrary.read_logical_part: IO error scanning file", e);
        return null;
      }
      if (next_token == null) {
        System.out.println("PartLibrary.read_logical_part: unexpected end of file at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      if (next_token == CLOSED_BRACKET) {
        // end of scope
        break;
      }
      boolean read_ok = true;
      if (prev_token == OPEN_BRACKET) {
        if (next_token == PIN) {
          PartPin curr_part_pin = read_part_pin(p_scanner);
          if (curr_part_pin == null) {
            return null;
          }
          part_pins.add(curr_part_pin);
        } else {
          skip_scope(p_scanner);
        }
      }
      if (!read_ok) {
        return null;
      }
    }
    return new LogicalPart(part_name, part_pins);
  }

  private PartPin read_part_pin(IJFlexScanner p_scanner) {
    try {
      p_scanner.yybegin(SpecctraDsnFileReader.NAME);
      Object next_token = p_scanner.next_token();
      if (!(next_token instanceof String)) {
        System.out.println("PartLibrary.read_part_pin: string expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      String pin_name = (String) next_token;
      p_scanner.set_scope_identifier(pin_name);
      next_token = p_scanner.next_token();
      if (!(next_token instanceof Integer)) {
        System.out.println("PartLibrary.read_part_pin: integer expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      p_scanner.yybegin(SpecctraDsnFileReader.NAME);
      next_token = p_scanner.next_token();
      if (!(next_token instanceof String)) {
        System.out.println("PartLibrary.read_part_pin: string expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      String gate_name = (String) next_token;
      p_scanner.set_scope_identifier(gate_name);
      next_token = p_scanner.next_token();
      if (!(next_token instanceof Integer)) {
        System.out.println("PartLibrary.read_part_pin: integer expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      int gate_swap_code = (Integer) next_token;
      p_scanner.yybegin(SpecctraDsnFileReader.NAME);
      next_token = p_scanner.next_token();
      if (!(next_token instanceof String)) {
        System.out.println("PartLibrary.read_part_pin: string expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      String gate_pin_name = (String) next_token;
      p_scanner.set_scope_identifier(gate_pin_name);
      next_token = p_scanner.next_token();
      if (!(next_token instanceof Integer)) {
        System.out.println("PartLibrary.read_part_pin: integer expected at '" + p_scanner.get_scope_identifier() + "'");
        return null;
      }
      int gate_pin_swap_code = (Integer) next_token;
      // overread subgates
      do {
        next_token = p_scanner.next_token();
      } while (next_token != CLOSED_BRACKET);
      return new PartPin(pin_name, gate_name, gate_swap_code, gate_pin_name, gate_pin_swap_code);
    } catch (IOException e) {
      //FRLogger.error("PartLibrary.read_part_pin: IO error scanning file", e);
      return null;
    }
  }

  public static class LogicalPartMapping {
    /** The name of the mapping. */
    public final String name;
    /** The components belonging to the mapping. */
    public final SortedSet<String> components;

    private LogicalPartMapping(String p_name, SortedSet<String> p_components) {
      name = p_name;
      components = p_components;
    }
  }

  public static class PartPin {
    public final String pin_name;
    public final String gate_name;
    public final int gate_swap_code;
    public final String gate_pin_name;
    public final int gate_pin_swap_code;
    private PartPin(
        String p_pin_name,
        String p_gate_name,
        int p_gate_swap_code,
        String p_gate_pin_name,
        int p_gate_pin_swap_code) {
      pin_name = p_pin_name;
      gate_name = p_gate_name;
      gate_swap_code = p_gate_swap_code;
      gate_pin_name = p_gate_pin_name;
      gate_pin_swap_code = p_gate_pin_swap_code;
    }
  }

  public static class LogicalPart {
    /** The name of the mapping. */
    public final String name;
    /** The pins of this logical part */
    public final Collection<PartPin> part_pins;

    private LogicalPart(String p_name, Collection<PartPin> p_part_pins) {
      name = p_name;
      part_pins = p_part_pins;
    }
  }
}
