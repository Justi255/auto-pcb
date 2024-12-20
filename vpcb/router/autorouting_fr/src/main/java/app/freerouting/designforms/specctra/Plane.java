package app.freerouting.designforms.specctra;

import app.freerouting.board.ConductionArea;
import app.freerouting.geometry.planar.Area;

import java.io.IOException;

/** Class for reading and writing plane scopes from dsn-files. */
public class Plane extends ScopeKeyword {

  /** Creates a new instance of Plane */
  public Plane() {
    super("plane");
  }

  @Override
  public boolean read_scope(ReadScopeParameter p_par) {
    // read the net name
    String net_name;
    boolean skip_window_scopes =
        p_par.host_cad != null && p_par.host_cad.equalsIgnoreCase("allegro");
    // Cadence Allegro cutouts the pins on power planes, which leads to performance problems
    // when dividing a conduction area into convex pieces.
    Shape.ReadAreaScopeResult conduction_area;
    try {
      Object next_token = p_par.scanner.next_token();
      if (!(next_token instanceof String)) {
        System.out.println("Plane.read_scope: String expected at '" + p_par.scanner.get_scope_identifier() + "'");
        return false;
      }
      net_name = (String) next_token;
      p_par.scanner.set_scope_identifier(net_name);
      conduction_area =
          Shape.read_area_scope(p_par.scanner, p_par.layer_structure, skip_window_scopes);
    } catch (IOException e) {
      //FRLogger.error("Plane.read_scope: IO error scanning file", e);
      return false;
    }
    ReadScopeParameter.PlaneInfo plane_info =
        new ReadScopeParameter.PlaneInfo(conduction_area, net_name);
    p_par.plane_list.add(plane_info);
    return true;
  }
}
