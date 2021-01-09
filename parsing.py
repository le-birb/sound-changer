from io import FileIO
from itertools import chain, product
from typing import Iterable, List, Tuple, Union
from sound_class import sound_class
from rule import rule
import regex as re

from regex_util import *

class parse_error(Exception):
    pass


def is_blank(string: str) -> bool:
    return re.fullmatch("\s*", string)

comment_chars = "#%"

def is_comment(string: str) -> bool:
    return any(string.startswith(c) for c in comment_chars)

def remove_whitespace(string:str) -> str:
    return re.sub(r"\s", "", string)


#########################################################################################################################
# class stuff here


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


def parse_sound_class(class_str: str) -> sound_class:
    if "=" not in class_str:
        raise parse_error("Sound class definition must be of the form:\nname=expression")

    name, expression = class_str.split('=', maxsplit = 1)

    new_class = eval_class_expression(expression)
    if not isinstance(new_class, sound_class):
        new_class = sound_class(new_class)
    new_class.name = name


def parse_sound_classes(file: FileIO) -> int:

    line_counter = 0

    try:
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
                new_class = parse_sound_class(line)
                sound_class.class_map.update({new_class.name: new_class})

    except parse_error:
        parse_error.args[0] = "Line {}:\nRule \"{}\":\n".format(line_counter, line.strip()) + parse_error.args[0] # type: ignore
        raise parse_error

    return line_counter


######################################################################################################################
# rule stuff here

def parse_environments(environments: Iterable[str]) -> Tuple[str, str]:
    pre_envs_str = ""
    post_envs_str = ""

    # positive environments are checked in a set of | to match any of them, not just one
    # the easiest way to do this is to just stick 'em in a list for now and '|'.join() them later
    positive_pre_envs: List[str] = []

    neg_counter = 0
    pos_counter = 0

    for env in environments:
        # first, check if the environment is negative
        neg = False
        if env.startswith("!"):
            neg = True
            # get rid of the ! if so
            env = env[1:]

        env = env.strip()

        try:
            pre_env, post_env = env.split("_")
        except ValueError:
            raise parse_error("Environment \"{}\" does not contain an underscore".format(env))

        if neg:
            neg_counter += 1
            name = "neg{}".format(neg_counter)
            post_name = name + "_post"
            pre_envs_str += regex_optional(lookbehind(regex_group(name = name, match = pre_env)))

            # the post string negative check consists of 2 parts:
            # see if the corresponding pre env matched, and if so try to match the post env
            # if the post env matched, skip the match attempt at the current character:
            # a negative environment matched, so no change should happen even if a positive
            # environment happens to match as well
            fail_group = regex_optional(regex_group(name = post_name, match = post_env))
            fail_check = regex_conditional(post_name, skip_attempt)

            post_envs_str += regex_conditional(name, regex_concat(fail_group, fail_check))

        else:
            pos_counter += 1
            name = "pos{}".format(pos_counter)
            positive_pre_envs.append( lookbehind(regex_group(name = name, match = pre_env)) )

            # the post string positive check is much simpler
            # we only need to check if the pre matched, then check the post
            # if it matches the regex is done, otherwise it goes back to check others
            # either way the engine handles that for us
            post_envs_str += regex_conditional(name, post_env)

    # now we add any positive pre envs to the pre_envs_str
    pre_envs_str += regex_group(match = regex_or(*positive_pre_envs), silent = True)

    # wrap the post env checking in a lookahead so it doesn't get returned from a match
    post_envs_str = lookahead(post_envs_str)

    return pre_envs_str, post_envs_str


arrows = ["=>", "->", ">", "→", "/"]

# TODO: process rule strings before passing to any parsing functions
def parse_rule(rule_str: str):
    # first thing we do is split up the rule string into target, replacement, and environments
    # target => replacement / env /! negenv
    # target must come before a valid arrow, so grab that if it's there
    for arrow in arrows:
        if arrow in rule_str:
            target, remainder = rule_str.split(arrow, maxsplit = 1)
            break
    else:
        raise parse_error("Rule must have an arrow from the target to the replacement.")

    remainder = remainder.split('/')
    # the replacement is always the first thing, before any slashes (if present)
    replacement = remainder[0]
    # anything else will be an environment
    environments = remainder[1:]

    pre_env, post_env = parse_environments(environments)


def parse_rules(file: FileIO, start_line) -> List[rule]:
    rule_list: List[rule] = []
    line_counter = start_line

    try:
        for line in file:
            line_counter += 1
            line = line.strip()

            if is_comment(line) or is_blank(line):
                # skip comments and blank lines
                continue

            else:
                # rule_list.append(rule(line))
                rule_list.append(parse_rule(line))

    except parse_error:
        parse_error.args[0] = "Line {}:\nRule \"{}\":\n".format(line_counter, line.strip()) + parse_error.args[0] # type: ignore
        raise parse_error

    return rule_list


#########################################################################################################################
# overall parsing

def parse_rule_file(file):
    offset = parse_sound_classes(file)

    return parse_rules(file, offset)
