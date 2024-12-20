package app.freerouting.library;

import java.io.Serializable;
import java.util.Locale;
import java.util.ResourceBundle;

/** Contains information for gate swap and pin swap for a single component. */
public class LogicalPart
    implements Serializable {

  public final String name;
  public final int no;
  private final PartPin[] part_pin_arr;

  /**
   * Creates a new instance of LogicalPart. The part pins are sorted by pin_no. The pin_no's of the
   * part pins must be the same number as in the components' library package.
   */
  public LogicalPart(String p_name, int p_no, PartPin[] p_part_pin_arr) {
    name = p_name;
    no = p_no;
    part_pin_arr = p_part_pin_arr;
  }

  public int pin_count() {
    return part_pin_arr.length;
  }

  /** Returns the pim with index p_no. Pin numbers are from 0 to pin_count - 1 */
  public PartPin get_pin(int p_no) {
    if (p_no < 0 || p_no >= part_pin_arr.length) {
      System.out.println("LogicalPart.get_pin: p_no out of range");
      return null;
    }
    return part_pin_arr[p_no];
  }

  public static class PartPin implements Comparable<PartPin>, Serializable {
    /**
     * The number of the part pin. Must be the same number as in the components library package.
     */
    public final int pin_no;
    /** The name of the part pin. Must be the same name as in the components library package. */
    public final String pin_name;
    /** The name of the gate this pin belongs to. */
    public final String gate_name;
    /**
     * The gate swap code. Gates with the same gate swap code can be swapped. Gates with swap code
     * {@literal <}= 0 are not swappable.
     */
    public final int gate_swap_code;
    /** The identifier of the pin in the gate. */
    public final String gate_pin_name;
    /**
     * The pin swap code of the gate. Pins with the same pin swap code can be swapped inside a gate.
     * Pins with swap code {@literal <}= 0 are not swappable.
     */
    public final int gate_pin_swap_code;

    public PartPin(
        int p_pin_no,
        String p_pin_name,
        String p_gate_name,
        int p_gate_swap_code,
        String p_gate_pin_name,
        int p_gate_pin_swap_code) {
      pin_no = p_pin_no;
      pin_name = p_pin_name;
      gate_name = p_gate_name;
      gate_swap_code = p_gate_swap_code;
      gate_pin_name = p_gate_pin_name;
      gate_pin_swap_code = p_gate_pin_swap_code;
    }

    @Override
    public int compareTo(PartPin p_other) {
      return this.pin_no - p_other.pin_no;
    }
  }
}
