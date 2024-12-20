package app.freerouting.rules;

import app.freerouting.library.Padstack;

import java.io.Serializable;
import java.util.LinkedList;
import java.util.List;
import java.util.Locale;
import java.util.ResourceBundle;

/**
 * Contains an array of vias used for routing. Vias at the beginning of the array are preferred to
 * later vias.
 */
public class ViaRule
    implements Serializable {

  /** Empty via rule. Must not be changed. */
  public static final ViaRule EMPTY = new ViaRule("empty");
  public final String name;
  private final List<ViaInfo> list = new LinkedList<>();

  public ViaRule(String p_name) {
    name = p_name;
  }

  public void append_via(ViaInfo p_via) {
    list.add(p_via);
  }

  /** Removes p_via from the rule. Returns false, if p_via was not contained in the rule. */
  public boolean remove_via(ViaInfo p_via) {
    return list.remove(p_via);
  }

  public int via_count() {
    return list.size();
  }

  public ViaInfo get_via(int p_index) {
    assert p_index >= 0 && p_index < list.size();
    return list.get(p_index);
  }

  @Override
  public String toString() {
    return this.name;
  }

  /** Returns true, if p_via_info is contained in the via list of this rule. */
  public boolean contains(ViaInfo p_via_info) {
    for (ViaInfo curr_info : this.list) {
      if (p_via_info == curr_info) {
        return true;
      }
    }
    return false;
  }

  /** Returns true, if this rule contains a via with padstack p_padstack */
  public boolean contains_padstack(Padstack p_padstack) {
    for (ViaInfo curr_info : this.list) {
      if (curr_info.get_padstack() == p_padstack) {
        return true;
      }
    }
    return false;
  }

  /**
   * Searches a via in this rule with first layer = p_from_layer and last layer = p_to_layer. Returns
   * null, if no such via exists.
   */
  public ViaInfo get_layer_range(int p_from_layer, int p_to_layer) {
    for (ViaInfo curr_info : this.list) {
      if (curr_info.get_padstack().from_layer() == p_from_layer
          && curr_info.get_padstack().to_layer() == p_to_layer) {
        return curr_info;
      }
    }
    return null;
  }

  /**
   * Swaps the locations of p_1 and p_2 in the rule. Returns false, if p_1 or p_2 were not found in
   * the list.
   */
  public boolean swap(ViaInfo p_1, ViaInfo p_2) {
    int index_1 = this.list.indexOf(p_1);
    int index_2 = this.list.indexOf(p_2);
    if (index_1 < 0 || index_2 < 0) {
      return false;
    }
    if (index_1 == index_2) {
      return true;
    }
    this.list.set(index_1, p_2);
    this.list.set(index_2, p_1);
    return true;
  }
}
