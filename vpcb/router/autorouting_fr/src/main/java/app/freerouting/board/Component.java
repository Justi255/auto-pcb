package app.freerouting.board;

import app.freerouting.datastructures.UndoableObjects;
import app.freerouting.geometry.planar.IntPoint;
import app.freerouting.geometry.planar.Point;
import app.freerouting.geometry.planar.Vector;
import app.freerouting.library.LogicalPart;
import app.freerouting.library.Package;

import java.io.Serializable;
import java.util.Locale;
import java.util.ResourceBundle;

/**
 * Describes board components consisting of an array of pins and other stuff like component
 * keepouts.
 */
public class Component
    implements UndoableObjects.Storable, Serializable {
  /** The name of the component. */
  public final String name;
  /** Internal generated unique identification number. */
  public final int no;
  /** If true, the component cannot be moved. */
  public final boolean position_fixed;
  /** The library package of the component if it is placed on the component side. */
  private final Package lib_package_front;
  /** The library package of the component if it is placed on the solder side. */
  private final Package lib_package_back;
  /** The location of the component. */
  private Point location;
  /** The rotation of the library package of the component in degree */
  private double rotation_in_degree;
  /** Contains information for gate swapping and pin swapping, if != null */
  private LogicalPart logical_part;
  /** If false, the component will be placed on the back side of the board. */
  private boolean on_front;

  /**
   * Creates a new instance of Component with the input parameters. If p_on_front is false, the
   * component will be placed on the back side.
   */
  Component(
      String p_name,
      Point p_location,
      double p_rotation_in_degree,
      boolean p_on_front,
      Package p_package_front,
      Package p_package_back,
      int p_no,
      boolean p_position_fixed) {
    name = p_name;
    location = p_location;
    rotation_in_degree = p_rotation_in_degree;
    while (this.rotation_in_degree >= 360) {
      this.rotation_in_degree -= 360;
    }
    while (this.rotation_in_degree < 0) {
      this.rotation_in_degree += 360;
    }
    on_front = p_on_front;
    lib_package_front = p_package_front;
    lib_package_back = p_package_back;
    no = p_no;
    position_fixed = p_position_fixed;
  }

  /** Returns the location of this component. */
  public Point get_location() {
    return location;
  }

  /** Returns the rotation of this component in degree. */
  public double get_rotation_in_degree() {
    return rotation_in_degree;
  }

  public boolean is_placed() {
    return location != null;
  }

  /** If false, the component will be placed on the back side of the board. */
  public boolean placed_on_front() {
    return this.on_front;
  }

  /**
   * Translates the location of this Component by p_p_vector. The Pins in the board must be moved
   * separately.
   */
  public void translate_by(Vector p_vector) {
    if (location != null) {
      location = location.translate_by(p_vector);
    }
  }

  /** Turns this component by p_factor times 90 degree around p_pole. */
  public void turn_90_degree(int p_factor, IntPoint p_pole) {
    if (p_factor == 0) {
      return;
    }
    this.rotation_in_degree = this.rotation_in_degree + p_factor * 90;
    while (this.rotation_in_degree >= 360) {
      this.rotation_in_degree -= 360;
    }
    while (this.rotation_in_degree < 0) {
      this.rotation_in_degree += 360;
    }
    if (location != null) {
      this.location = this.location.turn_90_degree(p_factor, p_pole);
    }
  }

  /** Rotates this component by p_angle_in_degree around p_pole. */
  public void rotate(double p_angle_in_degree, IntPoint p_pole, boolean p_flip_style_rotate_first) {
    if (p_angle_in_degree == 0) {
      return;
    }
    double turn_angle = p_angle_in_degree;
    if (p_flip_style_rotate_first && !this.placed_on_front()) {
      // take care of the order of mirroring and rotating on the back side of the board
      turn_angle = 360 - p_angle_in_degree;
    }
    this.rotation_in_degree = this.rotation_in_degree + turn_angle;
    while (this.rotation_in_degree >= 360) {
      this.rotation_in_degree -= 360;
    }
    while (this.rotation_in_degree < 0) {
      this.rotation_in_degree += 360;
    }
    if (location != null) {
      this.location =
          this.location
              .to_float()
              .rotate(Math.toRadians(p_angle_in_degree), p_pole.to_float())
              .round();
    }
  }

  /**
   * Changes the placement side of this component and mirrors it at the vertical line through
   * p_pole.
   */
  public void change_side(IntPoint p_pole) {
    this.on_front = !this.on_front;
    this.location = this.location.mirror_vertical(p_pole);
  }

  /**
   * Compares 2 components by name. Useful for example to display components in alphabetic order.
   */
  @Override
  public int compareTo(Object p_other) {
    if (p_other instanceof Component) {
      return this.name.compareToIgnoreCase(((Component) p_other).name);
    }
    return 1;
  }

  /** Creates a copy of this component. */
  @Override
  public Component clone() {
    Component result =
        new Component(
            name,
            location,
            rotation_in_degree,
            on_front,
            lib_package_front,
            lib_package_back,
            no,
            position_fixed);
    result.logical_part = this.logical_part;
    return result;
  }

  @Override
  public String toString() {
    return this.name;
  }

  /** Returns information for pin swap and gate swap, if != null. */
  public LogicalPart get_logical_part() {
    return this.logical_part;
  }

  /** Sets the information for pin swap and gate swap. */
  public void set_logical_part(LogicalPart p_logical_part) {
    this.logical_part = p_logical_part;
  }

  /** Returns the library package of this component. */
  public Package get_package() {
    Package result;
    if (this.on_front) {
      result = lib_package_front;
    } else {
      result = lib_package_back;
    }
    return result;
  }
}
