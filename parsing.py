
from __future__ import annotations

from io import FileIO
from itertools import chain, product

import regex as re

from regex_util import *
from rule_ast import rule_node, parse_tokens
from rule_tokenizer import tokenize_rule
from sound_class import sound_class


class parse_error(Exception):
    pass


def _is_blank(string: str) -> bool:
    return re.fullmatch("\s*", string)

_comment_chars = "#%"

def _is_comment(string: str) -> bool:
    return any(string.startswith(c) for c in _comment_chars)

def _remove_whitespace(string:str) -> str:
    return re.sub(r"\s", "", string)


#########################################################################################################################
# class stuff here


class sound_sequence(list):
    "Encapsulates lists of sounds to define a mul function that makes evaluation much easier."
    def __mul__(self, other):
        # If the other argument is a sound class, defer to sound_class's __rmul__
        if isinstance(other, sound_class):
            return NotImplemented

        # join each sound in this set with each sound from the other set plus the empty string
        # e.g. (a,b)*(1,2) -> a1,a2,a,b1,b2,b
        sound_sets = product(self, chain(other, ("",) ))
        return sound_sequence("".join(s) for s in sound_sets)


def _eval_class_expression(expression: str) -> sound_class | sound_sequence:
    if expression in sound_class.class_map:
        return sound_class.class_map[expression]

    # evaluate stuff in parentheses as a group: may remove this or change to have fuller parentheses support
    elif re.fullmatch(r"\([^)]*\)", expression):
        return _eval_class_expression(expression[1:-1])

    elif "*" in expression:
        # rsplit here to evaluate from right to left, which will tend to put longer sounds first
        left, right = expression.rsplit("*", maxsplit = 1)
        return _eval_class_expression(left) * _eval_class_expression(right)

    else:
        if "," in expression:
            sound_list = expression.split(",")
        else:
            sound_list = list(expression)

        return sound_sequence(sound_list)


def _parse_sound_class(class_str: str, linenum: int) -> sound_class:
    if "=" not in class_str:
        raise parse_error(f"Sound class definition on line {linenum} is not of the form:\nname=expression")

    name, expression = class_str.split('=', maxsplit = 1)

    new_class = _eval_class_expression(expression)
    if not isinstance(new_class, sound_class):
        new_class = sound_class(new_class)
    new_class.name = name

    return new_class


def parse_sound_classes(file: FileIO) -> int:
    class_map = {}

    try:
        # start with checking for sound class definitions
        for linenum, line in enumerate(file):
            line = _remove_whitespace(line)

            if _is_comment(line) or _is_blank(line):
                continue

            elif line.startswith("classes:"):
                # this will probably do something at some point but for now it is skipped
                continue

            elif line.startswith("rules:"):
                # classes are over, move on to rules
                break

            else:
                new_class = _parse_sound_class(line, linenum)
                class_map[new_class.name] = new_class

    except parse_error as error:
        # add info about the rule and line that a parse error happend on to the exception and reraise it
        # don't use raise from as that creates a *new* exception, cluttering the output
        # only the caught exception actually matters, we just want to add context to it
        augmented_error_string = "\n".join( (f"Line {linenum}:", f"Class \"{line.strip()}\":", error.args[0]) )
        error.args = (augmented_error_string,)
        raise

    # define a convenience class of all defined sounds if not user-defined
    if "_ALL" not in class_map:
        class_map["_ALL"] = sound_class(sound_class.union(class_map.values()), name = "_ALL")

    # temporary backwards compatability thing for matcher.py
    sound_class.class_map = class_map

    return class_map, linenum


######################################################################################################################
# rule stuff here

def parse_rule(rule_str: str, linenum: int, sound_classes: dict[str, sound_class]) -> rule_node:
    tokens = tokenize_rule(rule_str, sound_classes, sound_classes["_ALL"])

    return parse_tokens(tokens, sound_classes)



def parse_rules(file: FileIO, start_line: int, classes: dict[str, sound_class]) -> list[rule_node]:
    rule_list: list[rule_node] = []

    try:
        for linenum, line in enumerate(file, start = start_line):
            line = line.strip()

            if _is_comment(line) or _is_blank(line):
                # skip comments and blank lines
                continue

            else:
                rule_list.append(parse_rule(line, linenum, classes))

    except parse_error as error:
        # add info about the rule and line that a parse error happend on to the exception and reraise it
        # don't use raise from as that creates a *new* exception, cluttering the output
        # only the caught exception actually matters, we just want to add context to it
        augmented_error_str = "\n".join( (f"Line {linenum}:", f"Rule \"{line.strip()}\":", error.args[0]) )
        error.args = (augmented_error_str,)
        raise

    return rule_list


#########################################################################################################################
# overall parsing

def parse_rule_file(file):
    classes, offset = parse_sound_classes(file)

    rules = parse_rules(file, offset, classes)

    return rules, classes


