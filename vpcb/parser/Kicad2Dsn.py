import os
import sys
import pcbnew

def kicad2dsn(input_file_path:str, output_dir:str):
    brd = pcbnew.LoadBoard(input_file_path)
    root, ext = os.path.splitext(os.path.basename(input_file_path))
    file_name = root + ".dsn"
    pcbnew.ExportSpecctraDSN(brd, os.path.join(output_dir, file_name))

if __name__ == "__main__":
    kicad2dsn(sys.argv[1], sys.argv[2])
