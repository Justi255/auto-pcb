package app.freerouting.library;

import app.freerouting.geometry.planar.Area;
import app.freerouting.geometry.planar.Shape;
import app.freerouting.geometry.planar.Vector;

import java.io.Serializable;
import java.util.Locale;
import java.util.ResourceBundle;

/**
 * Component package templates describing the padstacks and relative locations of the package pins,
 * and optional other stuff like an outline package keepouts.
 */
public class Package
    implements Comparable<Package>,
        Serializable {

  /** The name of the package. */
  public final String name;
  /** Internally generated package number. */
  public final int no;
  /** The outline of the component, which may be null. */
  public final Shape[] outline;
  public final Keepout[] keepout_arr;
  public final Keepout[] via_keepout_arr;
  public final Keepout[] place_keepout_arr;
  /** If false, the package is placed on the back side of the board */
  public final boolean is_front;
  /** The array of pins of this padstack. */
  private final Pin[] pin_arr;
  private final Packages package_list;

  /**
   * Creates a new instance of Package. p_package_list is the list of packages containing this
   * package.
   */
  public Package(
      String p_name,
      int p_no,
      Pin[] p_pin_arr,
      Shape[] p_outline,
      Keepout[] p_keepout_arr,
      Keepout[] p_via_keepout_arr,
      Keepout[] p_place_keepout_arr,
      boolean p_is_front,
      Packages p_package_list) {
    name = p_name;
    no = p_no;
    pin_arr = p_pin_arr;
    outline = p_outline;
    keepout_arr = p_keepout_arr;
    via_keepout_arr = p_via_keepout_arr;
    place_keepout_arr = p_place_keepout_arr;
    is_front = p_is_front;
    package_list = p_package_list;
  }

  /** Compares 2 packages by name. Useful for example to display packages in alphabetic order. */
  @Override
  public int compareTo(Package p_other) {
    return this.name.compareToIgnoreCase(p_other.name);
  }

  /** Returns the pin with the input number from this package. */
  public Pin get_pin(int p_no) {
    if (p_no < 0 || p_no >= pin_arr.length) {
      System.out.println("Package.get_pin: p_no out of range");
      return null;
    }
    return pin_arr[p_no];
  }

  /**
   * Returns the pin number of the pin with the input name from this package, or -1, if no such pin
   * exists Pin numbers are from 0 to pin_count - 1.
   */
  public int get_pin_no(String p_name) {
    for (int i = 0; i < pin_arr.length; ++i) {
      if (pin_arr[i].name.equals(p_name)) {
        return i;
      }
    }
    return -1;
  }

  /** Returns the pin count of this package. */
  public int pin_count() {
    return pin_arr.length;
  }

  @Override
  public String toString() {
    return this.name;
  }

  /** Describes a pin padstack of a package. */
  public static class Pin implements Serializable {
    /** The name of the pin. */
    public final String name;
    /** The number of the padstack mask of the pin. */
    public final int padstack_no;
    /** The location of the pin relative to its package. */
    public final Vector relative_location;
    /** the rotation of the pin padstack */
    public final double rotation_in_degree;

    /** Creates a new package pin with the input coordinates relative to the package location. */
    public Pin(
        String p_name, int p_padstack_no, Vector p_relative_location, double p_rotation_in_degree) {
      name = p_name;
      padstack_no = p_padstack_no;
      relative_location = p_relative_location;
      rotation_in_degree = p_rotation_in_degree;
    }
  }

  /** Describes a named keepout belonging to a package, */
  public static class Keepout implements Serializable {
    public final String name;
    public final Area area;
    public final int layer;
    public Keepout(String p_name, Area p_area, int p_layer) {
      name = p_name;
      area = p_area;
      layer = p_layer;
    }
  }
}
