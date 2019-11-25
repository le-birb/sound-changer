#!/bin/python3

import argparse
# this library works much better with unicode than the built in re
import regex as re
from typing import List, Dict, Tuple

def raw_str(s: str):
    return s.encode('unicode-escape').decode()

def get_regex(rule_str: str, substitutions: dict) -> Tuple[str, str]:
    # strip whitespace from the string
    rule_str = re.sub(pattern = r"\s", repl = "", string = rule_str)

    # a sound change rule is of the form sound/replacement/environment
    # 'sound' is whatever is being changed, and must be nonempty
    # 'replacement' is what it changes to, and can be empty
    # 'environment' is the phological environment, and must either contain exactly one _ or be empty
    # a '#' in the environment means a word boundary, 
    assert re.match("[^#_/]+[>/][^#_/]*/(#?[^#_/]*_[^#_/]*#?|)", rule_str)

    parts = rule_str.split("/")

    target_str = parts[0]
    repl_str = parts[1]
    env_str = parts[2]

    if env_str != "" and env_str != "_":
        if env_str.startswith("_"):
            befores = ""
            # take everything but the underscore
            afters = env_str[1:]

        elif env_str.endswith("_"):
            # take everything but the underscore
            befores = env_str[:-1]
            afters = ""

        else:
            befores, afters = env_str.split("_")

        # add the environment criteria as lookaround non-capturing groups
        # e.g. we don't want s/z/V_V to capture either of the vowels
        if befores != "":
            target_str = "(?<=" + befores + ")" + target_str 

        if afters != "":    
            target_str = target_str + "(?=" + afters + ")"

    for key in substitutions:
        if key in target_str:
            target_str = re.sub(string = target_str, pattern = key, repl = raw_str(substitutions[key]))

    return target_str, repl_str


def apply_rule(rule_str: str, word_list: List[str], substitutions: dict) -> List[str]:

    target, repl = get_regex(rule_str, substitutions)

    new_words = []

    for word in word_list:
        new_words.append(re.sub(string = word, pattern = target, repl = repl))

    return new_words


class RuleError(RuntimeError):
    pass


def error_dialog(error_str: str) -> None:
    while True:
        print(error_str)
        choice = input("> ")

        if choice.lower() == "" or choice == "n":
            raise RuleError

        elif choice.lower() == "y":
            print("Resuming sound changes")
            break

        else:
            print("Please enter one of: yYnN")


def apply_rules(rule_list: List[str], word_list: List[str], substitutions: dict) -> List[str]:

    new_words = word_list

    rule_counter = 0

    for rule in rule_list:
        rule_counter += 1

        if rule == "\n" or rule == "" or rule.startswith('%'):
            continue

        try:
            new_words = apply_rule(rule, new_words, substitutions)

        except AssertionError:
            error_str = "Malformed sound change rule at line " + str(rule_counter) + ".\nKeep going? y/N"
            error_dialog(error_str)

    return new_words


# a phonological class if defined on a single line in the input file, and is of the form
# ID=phonemes, e.g.
# V=aeiou
# or, digraphs, trigraphs, etc. can be defined and treated as single units by comma separation, e.g
# C=t,th,d,dh,f 
def get_class_regex(class_str: str) -> Dict[str, str]:
    #TODO: recursive character class definitions
    # e.g
    # N=nm
    # C=Ntpksxlr

    class_str = class_str.strip()

    # must have exactly one =, and cannot contain the reserved symbol #
    # also cannot have an empty id or phoneme list
    assert(re.fullmatch(r"[^#=]+=[^#=]+", class_str))
    symbol, sounds = class_str.split('=')

    # handle the case with comma separation
    # requires the use of (str1|str2) regex syntax
    if ',' in sounds:
        sound_list = []
        # escape and regex characters that might occur in each sound string
        for sound in sounds.split(','):
            sound_list.append(re.escape(sound))
        
        return_regex = '(' + '|'.join(sound_list) + ')'

    # handle the simpler case of single-letter phonemes
    # can take advantage of [abcd]  syntax
    else:
        return_regex = '[' + re.escape(sounds) + ']'

    return {symbol: return_regex}


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("lex_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    parser.add_argument("rules_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    parser.add_argument("-o", "--out", action = "store", type = argparse.FileType("w", encoding = "utf-8"), dest = "out_file", default = None)
    parser.add_argument("-c", "--classes", action = "store", type = argparse.FileType("r", encoding = "utf-8"), dest = "phon_classes_file", default = None)
    parser.add_argument("--null_strings", action = "store", type = list, dest = "null_strings", default = ["#N/A", ""])

    args = parser.parse_args()

    lexicon = [word for word in filter(lambda w: w not in args.null_strings, [line.strip() for line in args.lex_file])]

    rule_list = [rule.strip() for rule in args.rules_file]

    # substitutions required to match regex syntax
    substitutions = {'#': r'\b'}

    if args.phon_classes_file:
        class_line_counter = 0
        
        for line in args.phon_classes_file:
            class_line_counter += 1
            
            if line == "\n" or line.startswith('%'):
                continue

            try:
                substitutions.update(get_class_regex(line))

            except AssertionError:
                error_str = "Malformed sound class at line " + str(class_line_counter) +  "\ncontinue? y/N"
                error_dialog(error_str)

    word_list = apply_rules(rule_list, lexicon, substitutions)

    if not args.out_file:
        out_file = open("./changed_words", "w")

    args.out_file.write("\n".join(word for word in word_list))

