
from typing import Union, List, IO
import regex as re

class sound_class:

    # class_list = {}

    def __init__(self, pName: str) -> None:
        self.name = pName
        self.members = []
        # sound_class.class_list.update({self.name: self})


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
        "Returns a regular expression that matches any member of the class"

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

        name, body = line.split("=")

        new_class = sound_class(name)

        # TODO: handle recursive sound class definition (definition-time or parse-time?)

        # sounds represented by more than one character can be handles by character classes
        # the syntax is
        # NAME=s1,s2,s3,s4...
        if "," in body:
            for sound in body.spliat(""):
                new_class.add_member(re.escape(sound))

        else:
            for char in body:
                new_class.add_member(re.escape(char))
        
        classes.append(new_class)

    return classes