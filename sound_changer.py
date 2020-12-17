
import argparse
# this library works much better with unicode than the built in re
import regex as re
# this library class has pretty much exactly what I want for sound classes
from ordered_set import OrderedSet as ordered_set
from itertools import product

from typing import Dict, Iterable, List, Tuple, TextIO, Union
from warnings import warn
from time import time

class sound_class(ordered_set):

    def __init__(self, name, sound_list: Iterable[str] = None, previous_classes: dict = None) -> None:
        super().__init__()
        self.name = name
        for member in sound_list:
            if previous_classes and member in previous_classes:
                # member is a sound class
                self.add(previous_classes[member])
            else:
                # member is a regular string
                self.add(member)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name + "=" + ",".join(sound for sound in self)

    def __iter__(self):
        """Overrides the ordered set's default iter method so that all member sound classes are iterated through too.
        The result is that `for sound in sound_class` will go through every sound sound_class would match."""
        for member in super().__iter__():
            if isinstance(member, sound_class):
                yield from member
            else:
                yield member

    # we need this so that sound classes can be added to themselves, since set members must be hashable
    def __hash__(self):
        return hash(self.name)

    def get_string_matches(self) -> List[str]:
        "Returns a list of regex-escaped strings that correspond to the sounds of the class"

        string_matches = []

        for member in self:
            if isinstance(member, str):
                string_matches.append(re.escape(member))

            elif isinstance(member, sound_class):
                string_matches += member.get_string_matches()

        return string_matches

    def get_regex(self)-> str:
        "Returns a regular expression string that matches any member of the class"

        string_matches = self.get_string_matches()
        
        # any sound represented by more than one character prevents us from
        # using a regex character class to match
        if any([len(string) > 1 for string in string_matches]):
            match_body = "|".join(string_matches)
            regex = "(" + match_body + ")"
        
        else:
            match_body = "".join(string_matches)
            regex = "[" + match_body + "]"
        
        return regex

    class parse_error(Exception):
        "Thrown when sound class parsing encounters an error"
        pass

    def parse_string(string: str, sound_classes: Dict = None):
        if not re.fullmatch(r"[^#=]+=[^#=]+", string):
            raise sound_class.parse_error

        name, member_string = string.split("=")
        sounds = []

        if "," in member_string:
            sounds = member_string.split(",")
        else:
            sounds = list(member_string)

        return sound_class(name, sounds, sound_classes)


def parse_class_file(pFile: TextIO) -> Dict[str, sound_class]:

    classes = {}

    if not pFile:
        return classes

    for line in pFile:
        line = line.strip()

        if line.startswith('%') or line == "":
            continue # the line is either empty or a comment

        new_class = sound_class.parse_string(line, classes)

        classes.update({new_class.name: new_class})

    return classes


def lookaround(behind: str, match: str, forward: str) -> str:
    return "(?<=" + behind + ")" + match + "(?=" + forward + ")"

def capture_group(s: str) -> str:
    if re.match("\(.*\)", s):
        return s
    else:
        return "("+s+")"

class rule:

    sound_classes: Dict[str, sound_class] = {}

    class parse_error(Exception):
        """Thrown when rule parsing encounters an error, typically a syntax error"""
        pass

    class spaceWarning(Warning):
        """A warning for whitespace within rules"""
        pass

    arrows = ["=>", "->", ">", "→", "/"]

    def parse(string: str) -> Tuple[str]:
        
        for arrow in rule.arrows:
            # look for an arrow to define the target -> replacement separation
            if arrow in string:
                target, string = string.split(arrow, maxsplit = 1)
                break
        else:
            # no suitable arrow found
            raise rule.parse_error()
        
        if "/" in string:
            repl, env = string.split("/", maxsplit = 1)
        else:
            repl = string
            env = ""

        # ignore surrounding whitespace in any part of the rule
        # e.g. ' r >   d /   V_V '
        # should be the same as 'r>d/V_V'
        # but not 'r>d/V _V'
        target = target.strip()
        repl = repl.strip()
        env = env.strip()
        # warn about left over whitespace
        # I'll probably add a way to disable this at some point but for now it's always
        if any(re.search(r'\s', place) for place in (target, repl, env)):
            warn("Whitespace found within rule definition\n" + string + "\nAre you sure you want that?", rule.spaceWarning())
        
        # replace a "null" character with an empty string
        # so 's > 0' will delete any s
        if repl == "∅" or repl == "0":
            repl = ""

        if "_" in env:
            try:
                pre_env, post_env = env.split("_")
            
            except ValueError:
                # if there are too many values to unpack, more than 1 underscore was used, and that's not allowed
                raise rule.parse_error() from None
        
        else:
            pre_env = post_env = ""
        
        return target, repl, pre_env, post_env

    def __init__(self, string: str):
        # TODO: refactor parsing of rules completely
        # likely to just do this when updating how rules work in general

        # the regex for a word boundary is \b, but the \b sequence in python strings behaves really weirdly
        # and it needs to be double escaped here to work, even in a raw string
        self.rule_str = re.sub("#", r"\\b", string)

        self.target, self.replacement, self.pre_env, self.post_env = rule.parse(self.rule_str)

        # count sound classes in pre an post environments so they can be ignored while applying the rule
        # each class will be a match group, which can be skipped
        # TODO: try to come up with a better way to do this
        self.pre_class_count = 0
        self.post_class_count = 0
        # substitute in sound classes
        for class_name in rule.sound_classes:
            if class_name in self.pre_env:
                self.pre_env = re.sub(class_name, capture_group(rule.sound_classes[class_name].get_regex()), self.pre_env)
                self.pre_class_count += 1

            if class_name in self.post_env:
                self.post_env = re.sub(class_name, capture_group(rule.sound_classes[class_name].get_regex()), self.post_env)
                self.post_class_count += 1

        # wrap environment in lookaround so it isn't deleted when substitution occurs
        self.regex_match = lookaround(self.pre_env, self.target, self.post_env)

    def __str__(self):
        return self.rule_str
    
    def __repr__(self):
        return str(self)

    def apply(self, word: str) -> str:

        if not rule.sound_classes:
            return re.sub(self.regex_match, self.replacement, word)
        
        else:
            target_classes: List[sound_class] = []
            replacement_classes: List[sound_class] = []

            for class_name in rule.sound_classes:
                if class_name in self.target:
                    target_classes.append(rule.sound_classes[class_name])
                if class_name in self.replacement:
                    replacement_classes.append(rule.sound_classes[class_name])

            # no sound classes to worry about
            if len(target_classes) == 0 == len(replacement_classes) == 0:
                    return re.sub(self.regex_match, self.replacement, word)

            # e.g. CV/CVN/
            # what should be written for the replacement sound classes is ambiguous, and so illegal
            # TODO: make this actually throw and error or something or at least actually handle this case
            elif  len(target_classes) < len(replacement_classes):
                print("Rule \"" + self.rule_str + "\" invalid: replacement classes cannot exceed target classes in number.")
            
            # len(target_classes) >= len(replacement_classes)
            # e.g. CV/V/ or C/G/V_
            else:
                # get regex expresions for all target classes
                # substitute those into rule string
                regex_string = self.target

                for c in target_classes:
                    regex_string = re.sub(c.name, capture_group(c.get_regex()), regex_string)
                
                # add environment to check
                regex_string = lookaround(self.pre_env, regex_string, self.post_env)

                # try that on word
                match_iter = re.finditer(regex_string, word)

                target_regex = self.target
                replacement_string = self.replacement

                # if no matches, return word (empty iterator skips loop)
                for match in match_iter:
                    # if matches, take list of those matches
                    # determine which parts of the matches correspond to which character classes
                    
                    match_groups = match.groups()[self.pre_class_count:len(match.groups()) - self.post_class_count]

                    group_count = 0
                    for sound_match in match_groups:
                        # grab the corresponding sound class
                        target_class = target_classes[group_count]

                        # sub in the match for the sound class in the target regex
                        target_regex = re.sub(target_class.name, sound_match, target_regex)

                        # the sound_match is escaped because the get_string_matches() strings are escaped
                        idx = target_class.get_string_matches().index(re.escape(sound_match))
                        
                        if len(replacement_classes) > group_count:
                            repl_class = replacement_classes[group_count]

                            if len(repl_class.get_string_matches()) > idx:
                                replacement_string = re.sub(repl_class.name, repl_class.get_string_matches()[idx], replacement_string)

                        group_count += 1

                # use a direct substitution back into the original word
                # remembering to also check for the proper environment
                target_regex = lookaround(self.pre_env, target_regex, self.post_env)
                return re.sub(target_regex,replacement_string, word)

# end rule


def raw_str(s: str):
    return s.encode('unicode-escape').decode()

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


def apply_rules(rule_list: List[str], word_list: List[str]) -> List[str]:

    new_words = word_list

    rule_counter = 0

    for rule_str in rule_list:
        rule_counter += 1

        if rule_str == "\n" or rule_str == "" or rule_str.startswith('%'):
            continue

        if rule_str.startswith(":print:"):
            suffix = rule_str[len(":print:"):].strip()
            if suffix:
                out_f = open(args.rules_file.name + suffix, "w")
            else:
                out_f = open(args.rules_file.name + "_debug", "w")
            out_f.write("\n".join(word for word in new_words))
            out_f.close()
            continue

        try:
            curr_rule = rule(rule_str)

            new_words = [curr_rule.apply(word) for word in new_words]

        except rule.parse_error:
            error_str = "Malformed sound change rule at line " + str(rule_counter) + ".\nKeep going? y/N"
            if not ask_to_continue(error_str):
                # return an empty list; no changes 
                return []
        
        except:
            # print the current rule to help in debugging
            print(curr_rule) # type: ignore
            raise

    return new_words


def sound_class_mult(base_class: sound_class, mult: Union[Iterable[str], str]) -> sound_class:
    """Returns a sound class formed from combination of its sounds with the items in mult.
    Useful for making classes that include long sounds, for instance, as (class file definition):
    T=ptk
    T=T*ː #T=p,t,k,pː,tː,kː"""
    if isinstance(mult, str):
        # if mult is just a string, wrap it in a tuple for the next part
        mult = tuple(mult)
    # pair off each mult with "" to make each individually optional
    # so that for, say, A=abc
    # A*(1,2) = a,b,c,a1,b1,c1,a2,b2,c2,a12,b12,c12
    # instead of a,b,c,a1,a2,b1,b2,c1,c2
    # combinations() isn't used because we need the sounds to always be present
    sound_sets = product(base_class, *(("", sound) for sound in mult))
    new_sounds = list("".join(s) for s in sound_sets)
    # does not need a reference to the otehr sound classes since it is guaranteed to only contain sounds (strings)
    return sound_class("", new_sounds)

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

            new_class = sound_class_mult(base, multiplicand)
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
    # r+ is note used since that can't create a new file
    parser.add_argument("-o", "--out", action = "store", type = argparse.FileType("a", encoding = "utf-8"),\
        dest = "out_file", default = None)
    parser.add_argument("-c", "--classes", action = "store", type = argparse.FileType("r", encoding = "utf-8"),\
        dest = "phon_classes_file", default = None)
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

