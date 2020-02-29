
import argparse
# this library works much better with unicode than the built in re
import regex as re
from typing import List, Dict, Tuple, IO

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

    for line in pFile:

        if line.startswith('%') or line.startswith('\n'):
            continue # the line is either empty or to be ignored

        # make sure the line is a well-formed class string with no illegal characters
        assert(re.fullmatch(r"[^#=]+=[^#=]+", line))

        classes.append(sound_class(line.strip(), classes))

    return classes


def lookaround(behind: str, match: str, forward: str) -> str:
    return "(?<=" + behind + ")" + match + "(?=" + forward + ")"

class rule:

    def __init__(self, rule_str: str, sound_classes: List[sound_class]):
        # a sound change rule is of the form target/replacement/environment
        # 'target' is whatever is being changed, and must be nonempty
        # 'replacement' is what it changes to, and can be empty
        # 'environment' is the phological environment, and must either contain exactly one _ or be empty
        # a '#' in the environment means a word boundary
        # this checks if the rule string passed is valid
        assert re.match("[^#_/]+/[^#_/]*/(#?[^#_/]*_[^#_/]*#?|)", rule_str)

        # change to regex syntax and strip whitespace
        self.rule_str = re.sub("#", r"\b", rule_str)
        self.rule_str = re.sub(r"\s", "", self.rule_str)

        self.target, self.replacement, self.environment = self.rule_str.split("/")

        # parentheses indicate optional sounds in the environment
        self.environment = re.sub("(\(.+?\))", "\1?", self.environment)

        # substitute in sound classes
        for sound_class in sound_classes:
            self.environment = re.sub(sound_class.name, sound_class.get_regex(), self.environment)

        # split up the before and after environments since they're handled differently by regex
        if self.environment:
            self.pre_env, self.post_env = self.environment.split("_")
        else:
            # if the environment is blank, both parts should also be blank
            self.pre_env = self.post_env = ""

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
            elif  len(target_classes) < len(replacement_classes):
                print("Rule \"" + self.rule_str + "\" invalid: replacement classes cannot exceed target classes in number.")
            
            # len(target_classes) >= len(replacement_classes)
            # e.g. CV/V/ or C/G/V_
            else:
                # get regex expresions for all target classes
                # substitute those into rule string
                regex_string = self.target

                for c in target_classes:
                    regex_string = re.sub(c.name, "("+c.get_regex()+")", regex_string)
                
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
                    match_groups = match.groups()

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

class RuleError(RuntimeError):
    pass

def error_dialog(error_str: str) -> None:
    while True:
        print(error_str)
        choice = input("> ")

        if choice.lower() == "n" or choice == "":
            raise RuleError

        elif choice.lower() == "y":
            print("Resuming sound changes")
            break

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

        except AssertionError:
            error_str = "Malformed sound change rule at line " + str(rule_counter) + ".\nKeep going? y/N"
            error_dialog(error_str)

    return new_words

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

    phon_classes = parse_class_file(args.phon_classes_file)

    word_list = apply_rules(rule_list, lexicon, phon_classes)

    if not args.out_file:
        out_file = open("./changed_words", "w")

    args.out_file.write("\n".join(word for word in word_list))

