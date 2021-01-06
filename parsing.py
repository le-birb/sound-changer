from io import FileIO
from itertools import chain, product
from typing import Dict, List, Tuple, Union
from sound_class import sound_class
from rule import rule
import regex as re


class parse_error(Exception):
    pass


def is_blank(string: str) -> bool:
    return re.fullmatch("\s*", string)

comment_chars = "#%"

def is_comment(string: str) -> bool:
    return any(string.startswith(c) for c in comment_chars)

def remove_whitespace(string:str) -> str:
    return re.sub(r"\s", "", string)

class sound_sequence(list):
    "Encapsulates lists of sounds to define a mul function that makes evaluation much easier."
    def __mul__(self, other):
        # If the other argument is a sound class, defer to sound_class's __rmul__
        if isinstance(other, sound_class):
            return NotImplemented

        sound_sets = product(self, chain(other, ("",) ))
        return sound_sequence("".join(s) for s in sound_sets)


def eval_class_expression(expression: str) -> Union[sound_class, sound_sequence]:
    if expression in sound_class.class_map:
        return sound_class.class_map[expression]

    # evaluate stuff in parentheses as a group: may remove this or change to have fuller parentheses support
    elif re.fullmatch(r"\([^)]*\)", expression):
        return eval_class_expression(expression[1:-1])

    elif "*" in expression:
        # rsplit here to evaluate from right to left, which will tend to put longer sounds first
        left, right = expression.rsplit("*", maxsplit = 1)
        return eval_class_expression(left) * eval_class_expression(right)

    else:
        if "," in expression:
            sound_list = expression.split(",")
        else:
            sound_list = list(expression)

        return sound_sequence(sound_list)


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

        elif line.startswith("rules:"):
            # classes are over, move on to rules
            break

        else:
            if "=" not in line:
                raise parse_error("Line {}:".format(line_counter),\
                            "Sound class definition must be of the form:\nname=expression")

            name, expression = line.split('=', maxsplit = 1)

            new_class = eval_class_expression(expression)
            if not isinstance(new_class, sound_class):
                new_class = sound_class(new_class)
            new_class.name = name

            sound_classes.update({name: new_class})

    return sound_classes, line_counter



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


if __name__ == "__main__":
    # some simple unit tests
    # TODO: make unit tests more official
    sound_class.class_map = {'A': sound_class(eval_class_expression("abcd"), "A")}
    c1 = eval_class_expression("A*n")
    c2 = eval_class_expression("n*A")
    c3 = eval_class_expression("ⁿ*A*ː")
    pass