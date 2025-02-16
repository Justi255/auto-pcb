package app.freerouting.rules;

import java.io.Serializable;
import java.util.LinkedList;
import java.util.List;
import java.util.Locale;
import java.util.ResourceBundle;

/**
 * Contains the lists of different ViaInfo's, which can be used in interactive and automatic
 * routing.
 */
public class ViaInfos
    implements Serializable {
  private final List<ViaInfo> list = new LinkedList<>();

  /**
   * Adds a via info consisting of padstack, clearance class and drill_to_smd_allowed. Return false,
   * if the insertion failed, for example if the name existed already.
   */
  public boolean add(ViaInfo p_via_info) {
    if (name_exists(p_via_info.get_name())) {
      return false;
    }
    this.list.add(p_via_info);
    return true;
  }

  /** Returns the number of different vias, which can be used for routing. */
  public int count() {
    return this.list.size();
  }

  /** Returns the p_no-th via af the via types, which can be used for routing. */
  public ViaInfo get(int p_no) {
    assert p_no >= 0 && p_no < this.list.size();
    return this.list.get(p_no);
  }

  /** Returns the via info with name p_name, or null, if no such via exists. */
  public ViaInfo get(String p_name) {
    for (ViaInfo curr_via : this.list) {
      if (curr_via.get_name().equals(p_name)) {
        return curr_via;
      }
    }
    return null;
  }

  /** Returns true, if a via info with name p_name is already wyisting in the list. */
  public boolean name_exists(String p_name) {
    for (ViaInfo curr_via : this.list) {
      if (curr_via.get_name().equals(p_name)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Removes p_via_info from this list. Returns false, if p_via_info was not contained in the list.
   */
  public boolean remove(ViaInfo p_via_info) {
    return this.list.remove(p_via_info);
  }
}
