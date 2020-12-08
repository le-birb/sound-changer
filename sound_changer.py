
import argparse
# this library works much better with unicode than the built in re
import regex as re
from typing import List, Dict, Tuple, IO
from time import time

class sound_class:

    def __init__(self, def_string: str, class_list = None) -> None:
        self.name, self.member_string = def_string.split("=")
        self.members = []

        if "," in self.member_string:
            member_list = self.member_string.split(",")
        else:
            member_list = [char for char in self.member_string]

        for member in member_list:
            if class_list:
                for sound_class in class_list:
                    if sound_class.name == member:
                        self.add_member(sound_class)
                        break
                else:
                    self.add_member(member)
            else:
                self.add_member(member)

    def __str__(self):
        return self.name + "=" + self.member_string
    
    def __repr__(self):
        return str(self)

    def add_member(self, pMember) -> None:
        self.members.append(pMember)


    def get_string_matches(self) -> List[str]:
        "Returns a list of regex-escaped strings that correspond to the sounds of the class"

        string_matches = []

        for member in self.members:
            if type(member) is str:
                string_matches.append(re.escape(member))

            elif type(member) is sound_class:
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

# end sound_class

def parse_class_file(pFile: IO) -> List[sound_class]:

    classes = []

    if not pFile:
        return classes

    for line in pFile:

        if line.startswith('%') or line.startswith('\n'):
            continue # the line is either empty or to be ignored

        # make sure the line is a well-formed class string with no illegal characters
        assert(re.fullmatch(r"[^#=]+=[^#=]+", line))

        classes.append(sound_class(line.strip(), classes))

    return classes


def lookaround(behind: str, match: str, forward: str) -> str:
    return "(?<=" + behind + ")" + match + "(?=" + forward + ")"

def capture_group(s: str) -> str:
    if re.match("\(.*\)", s):
        return s
    else:
        return "("+s+")"

class rule:

    class parseError(Exception):
        """Thrown when rule parsing encounters an error"""
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
            raise rule.parseError()
        
        if "/" in string:
            repl, env = string.split("/", maxsplit = 1)
        else:
            repl = string
            env = ""
        
        return target, repl, env

    def __init__(self, rule_str: str, sound_classes: List[sound_class]):
        # a sound change rule is of the form target/replacement/environment
        # 'target' is whatever is being changed, and must be nonempty
        # 'replacement' is what it changes to, and can be empty
        # 'environment' is the phological environment, and must either contain exactly one _ or be empty
        # a '#' in the environment means a word boundary
        # this checks if the rule string passed is valid
        assert re.match("[^#_/]+/[^#_/]*/(#?[^#_/]*_[^#_/]*#?|)", rule_str)

        # change to regex syntax and strip whitespace
        self.rule_str = re.sub(r"\s", "", rule_str)
        # the regex for a word boundary is \b, but the \b sequence in python strings behaves really weirdly
        # and it needs to be double escaped here to work, even in a raw string
        self.rule_str = re.sub("#", r"\\b", self.rule_str)

        self.target, self.replacement, self.environment = self.rule_str.split("/")

        # parentheses indicate optional sounds in the environment
        self.environment = re.sub("(\(.+?\))", "\1?", self.environment)

        # split up the before and after environments since they're handled differently by regex
        if self.environment:
            self.pre_env, self.post_env = self.environment.split("_")
        else:
            # if the environment is blank, both parts should also be blank
            self.pre_env = self.post_env = ""

        # count sound classes in pre an post environments so they can be ignored while applying the rule
        # each class will be a match group, which can be skipped
        # TODO: try to come up with a better way to do this
        self.pre_class_count = 0
        self.post_class_count = 0
        # substitute in sound classes
        for sound_class in sound_classes:
            if sound_class.name in self.pre_env:
                self.pre_env = re.sub(sound_class.name, capture_group(sound_class.get_regex()), self.pre_env)
                self.pre_class_count += 1
            
            if sound_class.name in self.post_env:
                self.post_env = re.sub(sound_class.name, capture_group(sound_class.get_regex()), self.post_env)
                self.post_class_count += 1

        # wrap environment in lookaround so it isn't deleted when substitution occurs
        self.regex_match = lookaround(self.pre_env, self.target, self.post_env)

    def __str__(self):
        return self.rule_str
    
    def __repr__(self):
        return str(self)

    def apply(self, word: str, sound_classes: List[sound_class] = None) -> str:

        if not sound_classes:
            return re.sub(self.regex_match, self.replacement, word)
        
        else:
            target_classes = []
            replacement_classes = []

            for sound_class in sound_classes:
                if sound_class.name in self.target:
                    target_classes.append(sound_class)
                if sound_class.name in self.replacement:
                    replacement_classes.append(sound_class)

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
                        sound_class = target_classes[group_count]

                        # sub in the match for the sound class in the target regex
                        target_regex = re.sub(sound_class.name, sound_match, target_regex)

                        # the sound_match is escaped because the get_string_matches() strings are escaped
                        idx = sound_class.get_string_matches().index(re.escape(sound_match))
                        
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


def apply_rules(rule_list: List[str], word_list: List[str], sound_classes: List[sound_class]) -> List[str]:

    new_words = word_list

    rule_counter = 0

    for rule_str in rule_list:
        rule_counter += 1

        if rule_str == "\n" or rule_str == "" or rule_str.startswith('%'):
            continue

        try:
            curr_rule = rule(rule_str, sound_classes)

            new_words = [curr_rule.apply(word, sound_classes) for word in new_words]

        except rule.parseError:
            error_str = "Malformed sound change rule at line " + str(rule_counter) + ".\nKeep going? y/N"
            if not ask_to_continue(error_str):
                # return an empty list; no changes 
                return []
        
        except:
            # print the current rule to help in debugging
            print(curr_rule) # type: ignore
            raise

    return new_words

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("lex_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    parser.add_argument("rules_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    # the out file is read in with r+ because that won't delete the contents immediately
    # if the program exits before finishing, an existing file should not be wiped
    parser.add_argument("-o", "--out", action = "store", type = argparse.FileType("r+", encoding = "utf-8"),\
        dest = "out_file", default = None)
    parser.add_argument("-c", "--classes", action = "store", type = argparse.FileType("r", encoding = "utf-8"),\
        dest = "phon_classes_file", default = None)
    parser.add_argument("--null_strings", action = "store", type = list, dest = "null_strings", default = ["#N/A", ""])
    parser.add_argument("--time", action = "store_true")

    args = parser.parse_args()

    if args.time:
        start_time = time()

    lexicon = [word for word in filter(lambda w: w not in args.null_strings, [line.strip() for line in args.lex_file])]
    rule_list = [rule.strip() for rule in args.rules_file]
    phon_classes = parse_class_file(args.phon_classes_file)

    word_list = apply_rules(rule_list, lexicon, phon_classes)

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

