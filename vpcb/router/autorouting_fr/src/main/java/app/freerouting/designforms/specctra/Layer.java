package app.freerouting.designforms.specctra;

import java.io.IOException;
import java.util.Collection;
import java.util.LinkedList;

/** Describes a layer in a Specctra dsn file. */
public class Layer {
  /** all layers of the board */
  public static final Layer PCB = new Layer("pcb", -1, false);
  /** the signal layers */
  public static final Layer SIGNAL = new Layer("signal", -1, true);
  public final String name;
  public final int no;
  public final boolean is_signal;
  public final Collection<String> net_names;
  /**
   * Creates a new instance of Layer. p_no is the physical layer number starting with 0 at the
   * component side and ending at the solder side. If p_is_signal, the layer is a signal layer,
   * otherwise it is a powerground layer. For Layer objects describing more than 1 layer the number
   * is -1. p_net_names is a list of nets for this layer, if the layer is a power plane.
   */
  public Layer(String p_name, int p_no, boolean p_is_signal, Collection<String> p_net_names) {
    name = p_name;
    no = p_no;
    is_signal = p_is_signal;
    net_names = p_net_names;
  }
  /**
   * Creates a new instance of Layer. p_no is the physical layer number starting with 0 at the
   * component side and ending at the solder side. If p_is_signal, the layer is a signal layer,
   * otherwise it is a powerground layer. For Layer objects describing more than 1 layer the number
   * is -1.
   */
  public Layer(String p_name, int p_no, boolean p_is_signal) {
    name = p_name;
    no = p_no;
    is_signal = p_is_signal;
    net_names = new LinkedList<>();
  }
}
