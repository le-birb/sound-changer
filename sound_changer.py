
import argparse
from sound_class import sound_class
from rule import rule
# this library works much better with unicode than the built in re
import regex as re
from itertools import product

from typing import Dict, Iterable, List, TextIO, Union
from time import time

def ask_to_continue(error_str: str) -> bool:
    while True:
        print(error_str)
        choice = input("> ")

        if choice.lower() == "n" or choice == "":
            print("Exiting...")
            return False

        elif choice.lower() == "y":
            print("Resuming sound changes")
            return True

        else:
            print("Please enter one of: yYnN")


def apply_rules(rule_list: List[rule], word_list: List[str]) -> List[str]:

    new_words = word_list

    for rule in rule_list:
        try:
            new_words = [rule.apply(word) for word in new_words]
        except:
            # print the current rule to help in debugging
            print(rule) # type: ignore
            raise

    return new_words


def is_blank(string: str) -> bool:
    return re.fullmatch("\s*", string)

comment_chars = "%#"

def parse_rule_file(rule_file: TextIO) -> List[rule]:

    sound_classes: Dict[str, sound_class] = {}

    line_counter = 0
    
    # start with checking for sound class definitions
    for line in rule_file:
        line_counter += 1
        line = line.strip()

        if any(line.startswith(c) for c in comment_chars) or is_blank(line):
            # skip comments and blank lines
            continue

        elif line.startswith("classes:"):
            # this will probably do something at some point but for now it is skipped
            continue

        elif "*" in line:
            name, expression = line.split("=")
            base, multiplicand = expression.split("*")
            base = sound_classes[base]

            # if multiplicand looks like (stuff)
            if re.fullmatch("\(.*\)", multiplicand):
                # strip parentheses
                multiplicand = multiplicand[1:-1]
                # get comma-separated pieces to multiply
                multiplicand = ",".split(multiplicand)

            new_class = base * multiplicand
            new_class.name = name

            if name in sound_classes:
                sound_classes[name].update(new_class)
            else:
                sound_classes[name] = new_class

        elif line.startswith("rules:"):
            # classes are over, move on to rules
            break

        else:
            try:
                new_class = sound_class.parse_string(line, sound_classes)
                sound_classes.update({new_class.name: new_class})
            except sound_class.parse_error:
                error_str = "Bad sound class definition found at line {}:\n{}\nKeep going?".format(line_counter, line)
                if not ask_to_continue(error_str):
                    # return an empty list; no changes 
                    return []
    
    rule.sound_classes = sound_classes

    rule_list: List[rule] = []

    # continue looping, but now we have different rules
    for line in rule_file:
        line_counter += 1
        line = line.strip()

        if any(line.startswith(c) for c in comment_chars) or is_blank(line):
            # skip comments and blank lines
            continue

        else:
            try:
                rule_list.append(rule(line))
            except rule.parse_error:
                error_str = "Malformed sound change rule at line {}.\nKeep going? y/N".format(line_counter)
                if not ask_to_continue(error_str):
                    # return an empty list; no changes 
                    return []
    
    return rule_list


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

