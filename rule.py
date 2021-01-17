
from __future__ import annotations

from warnings import warn

import regex as re

from sound_class import sound_class


def lookaround(behind: str, match: str, forward: str) -> str:
    return "(?<=" + behind + ")" + match + "(?=" + forward + ")"

def capture_group(s: str) -> str:
    if re.match("\(.*\)", s):
        return s
    else:
        return "("+s+")"

class rule:
    class parse_error(Exception):
        """Thrown when rule parsing encounters an error, typically a syntax error"""
        pass

    class spaceWarning(Warning):
        """A warning for whitespace within rules"""
        pass

    arrows = ["=>", "->", ">", "→", "/"]

    def parse(string: str) -> tuple[str]:
        
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
        for class_name in sound_class.class_map:
            if class_name in self.pre_env:
                self.pre_env = re.sub(class_name, capture_group(sound_class.class_map[class_name].get_regex()), self.pre_env)
                self.pre_class_count += 1

            if class_name in self.post_env:
                self.post_env = re.sub(class_name, capture_group(sound_class.class_map[class_name].get_regex()), self.post_env)
                self.post_class_count += 1

        # wrap environment in lookaround so it isn't deleted when substitution occurs
        self.regex_match = lookaround(self.pre_env, self.target, self.post_env)

    def __str__(self):
        return self.rule_str
    
    def __repr__(self):
        return str(self)

    def apply(self, word: str) -> str:

        if not sound_class.class_map:
            return re.sub(self.regex_match, self.replacement, word)
        
        else:
            target_classes: list[sound_class] = []
            replacement_classes: list[sound_class] = []

            for class_name in sound_class.class_map:
                if class_name in self.target:
                    target_classes.append(sound_class.class_map[class_name])
                if class_name in self.replacement:
                    replacement_classes.append(sound_class.class_map[class_name])

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
