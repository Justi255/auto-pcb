package app.freerouting.interactive;

import app.freerouting.autoroute.BatchAutorouter;
import app.freerouting.board.AngleRestriction;
import app.freerouting.board.TestLevel;
import app.freerouting.board.Unit;
import app.freerouting.geometry.planar.FloatLine;
import app.freerouting.geometry.planar.FloatPoint;
import app.freerouting.tests.Validate;

import java.awt.Color;
import java.awt.Graphics;
import java.util.ResourceBundle;

/** GUI interactive thread for the batch autorouter. */
public class BatchAutorouterThread extends InteractiveActionThread {
  private final BatchAutorouter batch_autorouter;

  /** Creates a new instance of BatchAutorouterThread */
  protected BatchAutorouterThread(BoardHandling p_board_handling) {
    super(p_board_handling);
    AutorouteSettings autoroute_settings = p_board_handling.get_settings().autoroute_settings;
    this.batch_autorouter =
        new BatchAutorouter(
            this,
            !autoroute_settings.get_with_fanout(),
            true,
            autoroute_settings.get_start_ripup_costs());

    int num_threads = p_board_handling.get_num_threads();
    
    if (num_threads > 1)
    {
      System.out.println("Multi-threaded route optimization is broken and it is known to generate clearance violations. It is highly recommended to use the single-threaded route optimization instead by setting the number of threads to 1 with the '-mt 1' command line argument.");//FRLogger.warn("Multi-threaded route optimization is broken and it is known to generate clearance violations. It is highly recommended to use the single-threaded route optimization instead by setting the number of threads to 1 with the '-mt 1' command line argument.");
    }
  }

  @Override
  protected void thread_action() {
    try {
      boolean saved_board_read_only = hdlg.is_board_read_only();
      hdlg.set_board_read_only(true);
      
      if (hdlg.get_settings().autoroute_settings.get_with_autoroute()
          && !this.is_stop_auto_router_requested()) {
        batch_autorouter.autoroute_passes();//hdlg.save_intermediate_stages);
      }
      hdlg.get_routing_board().finish_autoroute();

      hdlg.set_board_read_only(saved_board_read_only);
      
      if (hdlg.get_routing_board().rules.get_trace_angle_restriction()
              == AngleRestriction.FORTYFIVE_DEGREE
          && hdlg.get_routing_board().get_test_level()
              != TestLevel.RELEASE_VERSION) {
        Validate.multiple_of_45_degree(
            "after autoroute: ", hdlg.get_routing_board());
      }
    } catch (Exception e) {
      //FRLogger.error(e.getLocalizedMessage(), e);
    }
  }
}
