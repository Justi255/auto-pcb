package app.freerouting.board;

import app.freerouting.geometry.planar.ConvexShape;

import java.util.Locale;
import java.util.ResourceBundle;

/** Information of a clearance violation between 2 items. */
public class ClearanceViolation {

  /** The first item of the clearance violation */
  public final Item first_item;
  /** The second item of the clearance violation */
  public final Item second_item;
  /** The shape of the clearance violation */
  public final ConvexShape shape;
  /** The layer of the clearance violation */
  public final int layer;
  public final double expected_clearance;
  public final double actual_clearance;

  /** Creates a new instance of ClearanceViolation */
  public ClearanceViolation(Item p_first_item, Item p_second_item, ConvexShape p_shape, int p_layer, double p_expected_clearance, double p_actual_clearance) {
    first_item = p_first_item;
    second_item = p_second_item;
    shape = p_shape;
    layer = p_layer;
    expected_clearance = p_expected_clearance;
    actual_clearance = p_actual_clearance;
  }
}
