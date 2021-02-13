
from __future__ import annotations

from io import FileIO
from itertools import chain, product
from typing import Iterator

import regex as re

from regex_util import *
from rule import rule
from rule_tokenizer import token, token_type, tokenize_rule
from sound_class import sound_class


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

        # join each sound in this set with each sound from the other set plus the empty string
        # e.g. (a,b)*(1,2) -> a1,a2,a,b1,b2,b
        sound_sets = product(self, chain(other, ("",) ))
        return sound_sequence("".join(s) for s in sound_sets)


def eval_class_expression(expression: str) -> sound_class | sound_sequence:
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

    return new_class


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
                sound_class.class_map[new_class.name] = new_class

    except parse_error as error:
        # add info about the rule and line that a parse error happend on to the exception and reraise it
        # don't use raise from as that creates a *new* exception, cluttering the output
        # only the caught exception actually matters, we just want to add context to it
        augmented_error_string = "Line {}:\nClass \"{}\":\n".format(line_counter, line.strip()) + error.args[0] # type: ignore
        error.args = (augmented_error_string,)
        raise

    # define a convenience class of all defined sounds if not user-defined
    if "_ALL" not in sound_class.class_map:
        sound_class.class_map["_ALL"] = sound_class(sound_class.union(sound_class.class_map.values()), name = "_ALL")

    return line_counter


######################################################################################################################
# rule stuff here

def parse_environments(environments: Iterable[str]) -> tuple[str, str]:
    pre_envs_str = ""
    post_envs_str = ""

    # positive environments are checked in a set of | to match any of them, not just one
    # the easiest way to do this is to just stick 'em in a list for now and '|'.join() them later
    positive_pre_envs: list[str] = []

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

        if env == "":
            # skip empty environments for backwards compatability (for now)
            continue

        try:
            pre_env, post_env = env.split("_")
        except ValueError:
            raise parse_error("Environment \"{}\" must contain exactly one underscore.".format(env))

        if neg:
            neg_counter += 1
            name = "neg{}".format(neg_counter)
            post_name = name + "_post"
            pre_envs_str += regex_optional(lookbehind(regex_group(name = name, match = pre_env)))

            # the post string negative check consists of 2 parts:
            # see if the corresponding pre env matched, and if so try to match the post env in a lookahead
            # if the post env matched, skip the match attempt at the current character:
            # a negative environment matched, so no change should happen even if a positive
            # environment happens to match as well
            fail_group = regex_optional(regex_group(name = post_name, match = lookahead(post_env)))
            fail_check = regex_conditional(post_name, skip_attempt)

            post_envs_str += regex_conditional(name, regex_concat(fail_group, fail_check))

        else:
            pos_counter += 1
            name = "pos{}".format(pos_counter)
            positive_pre_envs.append( lookbehind(regex_group(name = name, match = pre_env)) )

            # the post string positive check is much simpler
            # we only need to check if the pre matched, then check the post (in a lookahead)
            # if it matches the regex is done, otherwise it goes back to check others
            # either way the engine handles that for us
            post_envs_str += regex_conditional(name, lookahead(post_env))

    # now we add any positive pre envs to the pre_envs_str
    pre_envs_str += regex_group(match = regex_or(*positive_pre_envs), silent = True)

    return pre_envs_str, post_envs_str


def get_changes(token_iter: Iterator[token]):
    targets = []
    replacements = []

    curr_tokens = []

    for token in token_iter:
        # hitting either of these means we're in environments territory now
        if token.type == token_type.pos_slash or token.type == token_type.neg_slash:
            replacements.append(curr_tokens)

            # add the slash back into the iterator and exit
            token_iter = chain([token], token_iter)
            break

        elif token.type == token_type.arrow:
            if not targets:
                # this is the first set, so it is only a target
                targets.append(curr_tokens)
            else:
                # this is a subsequent set of tokens, and so must be a replacement
                if replacements:
                    # if replacements is not empty, that means that this is part of a chain,
                    # so the last replacement is also the target for this one
                    targets.append(replacements[-1])
                replacements.append(curr_tokens)

            curr_tokens = []

        else:
            curr_tokens.append(token)

    return list(zip(targets, replacements))


def get_envs(token_iter: Iterator[token]):
    positive_envs = []
    negative_envs = []

    curr_env = []
    curr_positive = True

    for token in token_iter:
        if token.type == token_type.pos_slash:
            # add env to the list only if it's non-empty
            if curr_env:
                if curr_positive:
                    positive_envs.append(curr_env)
                else:
                    negative_envs.append(curr_env)
            curr_env = []
            curr_positive = True

        elif token.type == token_type.neg_slash:
            if curr_env:
                if curr_positive:
                    positive_envs.append(curr_env)
                else:
                    negative_envs.append(curr_env)
            curr_env = []
            curr_positive = False

        else:
            curr_env.append(token)
    
    return positive_envs, negative_envs


def parse_rule(rule_str: str) -> rule:
    tokens = tokenize_rule(rule_str, sound_class.class_map, sound_class.class_map["_ALL"])

    # get ast

    # compile rule



def parse_rules(file: FileIO, start_line) -> list[rule]:
    rule_list: list[rule] = []
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

    except parse_error as error:
        # add info about the rule and line that a parse error happend on to the exception and reraise it
        # don't use raise from as that creates a *new* exception, cluttering the output
        # only the caught exception actually matters, we just want to add context to it
        augmented_error_str = "Line {}:\nRule \"{}\":\n".format(line_counter, line.strip()) + error.args[0] # type: ignore
        error.args = (augmented_error_str,)
        raise

    return rule_list


#########################################################################################################################
# overall parsing

def parse_rule_file(file):
    offset = parse_sound_classes(file)

    return parse_rules(file, offset)
