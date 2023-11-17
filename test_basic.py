
from pathlib import Path
import filecmp

from sound_changer import change_sounds, write_output

test_folder = Path("./test")


for sub_dir in test_folder.iterdir(): 
    if sub_dir.is_dir():
        with open(sub_dir/"lex", "r") as lex_file,\
                open(sub_dir/"rules", "r") as rule_file,\
                open(sub_dir/"output", "a") as out_file:
            word_list = change_sounds(lex_file, rule_file)
            write_output(word_list, out_file)
        
        assert filecmp.cmp(sub_dir/"output", sub_dir/"expected_output")

