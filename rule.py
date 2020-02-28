
import regex as re
from typing import List
from sound_class import sound_class
from itertools import zip_longest

class rule:

    def __init__(self, rule_str: str):
        # change to regex syntax
        self.rule_str = re.sub("#", "\b", rule_str)

        self.target, self.replacement, self.environment = self.rule_str.split("/")

        self.environment = re.sub("(\(.+?\))", "\1?", self.environment)

        self.regex_match = re.sub("_", self.target, self.environment)


    def apply(self, word: str, sound_classes: List[sound_class] = None) -> str:

        if sound_classes is None:
            return re.sub(self.regex_match, self.substitution, word)
        
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
                    return re.sub(self.regex_match, self.substitution, word)

            # e.g. CV/CVN/
            # what should be written for the replacement sound classes is ambiguous, and so illegal
            elif  len(target_classes) < len(replacement_classes):
                print("Rule \"" + self.rule_str + "\" invalid: replacement classes cannot exceed target classes in number.")
            
            # len(target_classes) >= len(replacement_classes)
            # e.g. CV/V/ or N/L/_#
            else:
                # get regex expresions for all target classes
                # substitute those into rule string
                regex_string = self.target

                for c in target_classes:
                    regex_string = re.sub(c.name, c.get_regex(), regex_string)
                
                # try that on word
                match_iter = re.finditer(regex_string, word)

                # if no matches, return word (empty iterator skips loop)
                for match in match_iter:
                    # if matches, take list of those matches
                    # determine which parts of the matches correspond to which character classes
                    match_groups = match.groups()

                    group_count = 0
                    for sound_match in match_groups:
                        # grab the corresponding sound class
                        sound_class = target_classes[group_count]

                        # the sound_match is escaped because the get_string_matches() strings are escaped
                        idx = sound_class.get_string_matches().index(re.escape(sound_match))
                        repl_sound = replacement_classes[group_count].get_string_matches()[idx]

                        # use a direct substitution back into the original word
                        word = re.sub(re.escape(sound_match), repl_sound, word)

                return word