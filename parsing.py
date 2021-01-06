from io import FileIO
from typing import Dict, List, Tuple
from sound_class import sound_class
from rule import rule
import regex as re


def is_blank(string: str) -> bool:
    return re.fullmatch("\s*", string)

comment_chars = "#%"

def is_comment(string: str) -> bool:
    return any(string.startswith(c) for c in comment_chars)

def remove_whitespace(string:str) -> str:
    return re.sub(r"\s", "", string)

def parse_sound_classes(file: FileIO) -> Tuple[Dict[str, sound_class], int]:
    sound_classes: Dict[str, sound_class] = {}

    line_counter = 0
    
    # start with checking for sound class definitions
    for line in file:
        line_counter += 1
        line = remove_whitespace(line)

        if is_comment(line) or is_blank(line):
            continue

        elif line.startswith("classes:"):
            # this will probably do something at some point but for now it is skipped
            continue

        elif "*" in line:
            assignee, expression = line.split("=")
            base, multiplicand = expression.split("*")
            base = sound_classes[base]

            # if multiplicand looks like (stuff)
            if re.fullmatch("\(.*\)", multiplicand):
                # strip parentheses
                multiplicand = multiplicand[1:-1]
                # get comma-separated pieces to multiply
                multiplicand = ",".split(multiplicand)

            new_class: sound_class = base * multiplicand
            new_class.name = assignee

            sound_classes[assignee] = new_class

        elif line.startswith("rules:"):
            # classes are over, move on to rules
            break

        else:
            new_class = sound_class.parse_string(line, sound_classes)
            sound_classes.update({new_class.name: new_class})



def parse_rules(file: FileIO, start_line) -> List[rule]:
    rule_list: List[rule] = []
    line_counter = start_line

    # continue looping, but now we have different rules
    for line in file:
        line_counter += 1
        line = line.strip()

        if any(line.startswith(c) for c in comment_chars) or is_blank(line):
            # skip comments and blank lines
            continue

        else:
            rule_list.append(rule(line))
    
    return rule_list



def parse_rule_file(file):
    classes, offset = parse_sound_classes(file)

    sound_class.class_map = classes

    return parse_rules(file, offset)