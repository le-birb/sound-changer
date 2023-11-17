
from __future__ import annotations

import argparse
from io import TextIOWrapper
from time import time
from matcher import match_rule

from parsing import parse_rule_file
from replacer import replace_matches
from rule_ast import rule_node


def apply_rules(rule_list: list[rule_node], word_list: list[str]) -> list[str]:

    # iterate in this order, applying each rule to every word before moving on,
    # to keep open possibilities for pausing or halting execution at certain "times"
    # within a rule list
    for rule in rule_list:
        for change in rule.changes:
            for idx, word in enumerate(word_list):
                matches = match_rule(change, word)
                if matches:
                    word_list[idx] = replace_matches(word, matches, change)

    return word_list


def load_lexicon(lex_file: TextIOWrapper):
    return [word for word in [line.strip() for line in lex_file]]


def change_sounds(lex_file: TextIOWrapper, rule_file: TextIOWrapper) -> list[str]:
    lexicon = load_lexicon(lex_file)
    rule_list = parse_rule_file(rule_file)
    return apply_rules(rule_list, lexicon)


def write_output(word_list: list[str], out_file: TextIOWrapper):
    # if there are any words to record, write to the output
    # otherwise don't mess with the output file to avoid
    # erasing anything when not needed
    if word_list:
        if not out_file:
            # no r+ this time since we already know we want to overwrite this one
            out_file = open("./changed_words", "w", encoding = "utf-8")
        else:
            # clear anything already in an existing file passed in from the command line
            out_file.truncate(0)

        out_file.write("\n".join(word for word in word_list))



if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("lex_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    parser.add_argument("rules_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    # the out file is read in with a because that won't delete the contents immediately
    # if the program exits before finishing, an existing file should not be wiped
    # r+ is not used since that can't create a new file
    parser.add_argument("-o", "--out", action = "store", type = argparse.FileType("a", encoding = "utf-8"),\
        dest = "out_file", default = None)
    parser.add_argument("--time", action = "store_true")

    args = parser.parse_args()

    if args.time:
        start_time = time()

    word_list = change_sounds(args.rule_file, args.lex_file)

    write_output(word_list)

    if args.time:
        run_time = time() - start_time # type: ignore
        print("Execution time: " + str(run_time))

