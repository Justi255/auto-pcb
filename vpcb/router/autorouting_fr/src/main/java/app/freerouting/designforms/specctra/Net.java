package app.freerouting.designforms.specctra;

import java.io.IOException;
import java.util.Collection;
import java.util.Set;
import java.util.TreeSet;

/** Class for reading and writing net scopes from dsn-files. */
public class Net {

  public final Id id;
  /** List of elements of type Pin. */
  private Set<Pin> pin_list;

  /** Creates a new instance of Net */
  public Net(Id p_net_id) {
    id = p_net_id;
  }

  public Set<Pin> get_pins() {
    return pin_list;
  }

  public void set_pins(Collection<Pin> p_pin_list) {
    pin_list = new TreeSet<>(p_pin_list);
  }

  public static class Id implements Comparable<Id> {
    public final String name;
    public final int subnet_number;

    public Id(String p_name, int p_subnet_number) {
      name = p_name;
      subnet_number = p_subnet_number;
    }

    @Override
    public int compareTo(Id p_other) {
      int result = this.name.compareTo(p_other.name);
      if (result == 0) {
        result = this.subnet_number - p_other.subnet_number;
      }
      return result;
    }
  }

  /** Sorted tuple of component name and pin name. */
  public static class Pin implements Comparable<Pin> {
    public final String component_name;
    public final String pin_name;

    public Pin(String p_component_name, String p_pin_name) {
      component_name = p_component_name;
      pin_name = p_pin_name;
    }

    @Override
    public int compareTo(Pin p_other) {
      int result = this.component_name.compareTo(p_other.component_name);
      if (result == 0) {
        result = this.pin_name.compareTo(p_other.pin_name);
      }
      return result;
    }

    @Override
    public String toString() {
      return "Pin{" + component_name + '-' + pin_name + '}';
    }
  }
}
