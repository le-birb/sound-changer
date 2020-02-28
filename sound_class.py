
from typing import Union, List, IO
import regex as re

class sound_class:

    def __init__(self, def_string: str, class_list = None) -> None:
        self.name, self.member_string = def_string.split("=")

        if "," in self.member_string:
            member_list = self.member_string.split(",")
        else:
            member_list = [char for char in self.member_string]

        for member in member_list:
            if class_list is not None:
                for sound_class in class_list:
                    if sound_class.name == member:
                        self.add_member(sound_class)
                        break
            else:
                self.add_member(member)
        
        if class_list is not None:
            class_list.update({self.name: self})


    def add_member(self, pMember: Union[str, sound_class]) -> None:
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


def parse_class_file(pFile: IO) -> List[sound_class]:

    classes = []

    for line in pFile:

        if line.startswith('%') or line.startswith('\n'):
            continue # the line is either empty or to be ignored

        # make sure the line is a well-formed class string with no illegal characters
        assert(re.fullmatch(r"[^#=]+=[^#=]+", line))

        classes.append(sound_class(line, classes))

    return classes