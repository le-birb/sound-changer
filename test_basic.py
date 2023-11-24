
from pathlib import Path
import filecmp

from sound_changer import change_sounds, write_output

test_folder = Path("./test")


for sub_dir in test_folder.iterdir():
    lex_path = sub_dir/"lex"
    rule_path = sub_dir/"rules"
    out_path = sub_dir/"output"
    expected_out_path = sub_dir/"expected_output"
    if sub_dir.is_dir() and all(p.is_file() for p in (lex_path, rule_path, out_path, expected_out_path)):
        with open(lex_path, "r") as lex_file,\
                open(rule_path, "r") as rule_file,\
                open(out_path, "a") as out_file:
            word_list = change_sounds(lex_file, rule_file)
            write_output(word_list, out_file)
        
        assert filecmp.cmp(out_path, expected_out_path)

