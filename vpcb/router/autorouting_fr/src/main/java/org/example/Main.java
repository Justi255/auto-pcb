package org.example;

import app.freerouting.board.BoardObserverAdaptor;
import app.freerouting.board.ItemIdNoGenerator;
import app.freerouting.board.TestLevel;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.interactive.BoardHandling;
import app.freerouting.interactive.InteractiveActionThread;

import java.io.*;
import java.util.Locale;

public class Main {
    public static void main(String[] args){
        // Initial Constant Parameters
        Locale current_locale = Locale.getDefault();
        TestLevel test_level = TestLevel.RELEASE_VERSION;
        int num_threads = 1;
        int max_passes = 99999;

        // Initial BoardHandling
        BoardHandling hdlg = new BoardHandling(current_locale);

        String design_file_name;
        String output_dir_name;
        String output_file_name;

        if (args.length < 2) {
            System.out.println("Please enter at least 2 parameters.");
            return;
        }

        File input_file = new File(args[0]);
        if (input_file.exists() && input_file.isFile()) {
            design_file_name = input_file.getName();
            output_dir_name = design_file_name.split("\\.", 2)[0];
            output_file_name = design_file_name.split("\\.", 2)[0] + ".ses";
        } else {
            System.out.println("Design File \"" + args[0] +"\" is not found.");
            return;
        }

        File result_dir = new File(args[1]);
        File output_dir;
        if (result_dir.exists() && result_dir.isDirectory()) {
            output_dir = new File(args[1], output_dir_name);
            if (!output_dir.exists() || !output_dir.isDirectory()) {
                output_dir.mkdir();
            }
        } else {
            result_dir.mkdir();
            output_dir = new File(args[1], output_dir_name);
            output_dir.mkdir();
        }
        output_dir_name = output_dir.getAbsolutePath();

        InputStream input_stream;
        try {
            input_stream = new FileInputStream(input_file);
        } catch (IOException e) {
            input_stream = null;
            throw new RuntimeException(e);
        }
        // import the routing board from design file (.dsn)
        DsnFile.ReadResult read_result =
                hdlg.import_design(input_stream, new BoardObserverAdaptor(), new ItemIdNoGenerator(), test_level);
        if (read_result != DsnFile.ReadResult.OK) {
            System.out.println("Failed to import the routing board from design file");
        }
        hdlg.settings.autoroute_settings.set_stop_pass_no(
                hdlg.settings.autoroute_settings.get_start_pass_no()
                        + max_passes
                        - 1);
        hdlg.set_num_threads(num_threads);
        try {
            input_stream.close();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        // create and start a BatchAutorouterThread
        InteractiveActionThread thread = hdlg.start_batch_autorouter();
        try {
            thread.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        // export the routing board and solution to Specctra session file (.ses)
        File output_file = new File(output_dir_name, output_file_name);
        OutputStream output_stream;
        try {
            output_stream = new FileOutputStream(output_file);
        } catch (Exception e) {
            output_stream = null;
        }
        if (!hdlg.export_specctra_session_file(
                design_file_name, output_stream)) {
            System.out.println("Failed to export the routing board and solution to Specctra session file");
        }
    }
}