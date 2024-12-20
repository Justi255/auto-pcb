import os
import sys
import pcbnew

def ses2kicad(input_brd_file_path:str, input_ses_file_path:str, output_dir:str):
    brd = pcbnew.LoadBoard(input_brd_file_path)
    pcbnew.ImportSpecctraSES(brd, input_ses_file_path)
    file_name = os.path.basename(input_brd_file_path).split('.')[0] + '.routed.kicad_pcb'
    pcbnew.SaveBoard(os.path.join(output_dir, file_name), brd)

if __name__ == "__main__":
    print(sys.argv[0])
    ses2kicad(sys.argv[1], sys.argv[2], sys.argv[3])
