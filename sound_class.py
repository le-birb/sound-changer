
from itertools import product
from typing import Dict, Iterable, List
import regex as re
from ordered_set import OrderedSet as ordered_set


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

    def __mult__(self, other):
        """Returns a sound class formed from combination of its sounds with the items in mult.
        Useful for making classes that include long sounds, for instance, as (class file definition):
        T=ptk
        T=T*ː #T=p,t,k,pː,tː,kː"""
        if isinstance(other, str):
            # if mult is just a string, wrap it in a tuple for the next part
            other = tuple(other)
        # pair off each mult with "" to make each individually optional
        # so that for, say, A=abc
        # A*(1,2) = a,b,c,a1,b1,c1,a2,b2,c2,a12,b12,c12
        # instead of a,b,c,a1,a2,b1,b2,c1,c2
        # combinations() isn't used because we need the base sounds to always be present
        sound_sets = product(self, *(("", sound) for sound in other))
        new_sounds = list("".join(s) for s in sound_sets)
        # does not need a reference to the other sound classes since it is guaranteed to only contain sounds (strings)
        return sound_class("", new_sounds)

    def __rmult__(self, other):
        return self * other

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
