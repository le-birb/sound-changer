
from __future__ import annotations

import argparse
from time import time
from matcher import match_rule

from parsing import parse_rule_file
from replacer import replace_matches
from rule import rule


def apply_rules(rule_list: list[rule], word_list: list[str]) -> list[str]:

    # iterate in this order, applying each rule to every word before moving on,
    # to keep open possibilities for pausing or halting execution at certain "times"
    # within a rule list
    for rule in rule_list:
        for idx, word in enumerate(word_list):
            matches = match_rule(rule, word)
            if matches:
                word_list[idx] = replace_matches(word, matches, rule)

    return word_list


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

    lexicon = [word for word in [line.strip() for line in args.lex_file]]
    
    rule_list = parse_rule_file(args.rules_file)

    word_list = apply_rules(rule_list, lexicon)

    # if there are any words to record, write to the output
    # otherwise don't mess with the output file
    if word_list:
        if not args.out_file:
            # open a file to write to
            # no r+ this time since we already know we want to overwrite this one
            args.out_file = open("./changed_words", "w", encoding = "utf-8")
        else:
            # clear anything already in an existing file passed in from the command line
            args.out_file.truncate(0)

        args.out_file.write("\n".join(word for word in word_list))

    if args.time:
        run_time = time() - start_time # type: ignore
        print("Execution time: " + str(run_time))

