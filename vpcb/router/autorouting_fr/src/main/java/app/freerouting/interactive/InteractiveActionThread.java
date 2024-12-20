package app.freerouting.interactive;

import app.freerouting.datastructures.Stoppable;

import java.awt.Graphics;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.ResourceBundle;

/** Used for running an interactive action in a separate thread, that can be stopped by the user. */
public abstract class InteractiveActionThread extends Thread
    implements Stoppable {
  public final BoardHandling hdlg;
  private boolean stop_requested = false;
  private boolean stop_auto_router = false;

  /** Creates a new instance of InteractiveActionThread */
  protected InteractiveActionThread(BoardHandling p_board_handling) {
    this.hdlg = p_board_handling;
  }

  public static InteractiveActionThread get_batch_autorouter_instance(
      BoardHandling p_board_handling) {
    return new BatchAutorouterThread(p_board_handling);
  }

  protected abstract void thread_action();

  @Override
  public void run() {
    thread_action();
  }

  @Override
  public synchronized void request_stop() {
    stop_requested = true;
  }

  @Override
  public synchronized boolean is_stop_requested() {
    return stop_requested;
  }

  public synchronized void request_stop_auto_router() {
    stop_auto_router = true;
  }

  public synchronized boolean is_stop_auto_router_requested() {
    return stop_auto_router;
  }
}
