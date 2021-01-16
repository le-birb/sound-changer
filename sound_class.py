
from __future__ import annotations

from itertools import product, chain
from typing import Iterable
import regex as re
from ordered_set import OrderedSet as ordered_set


class sound_class(ordered_set):

    class_map: dict[str, sound_class] = {}

    def __init__(self, sound_list: Iterable[str | sound_class] = None, name: str = "") -> None:
        if sound_list:
            super().__init__(sound_list)
        else:
            super().__init__()
        self.name = name

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
        return hash(repr(self))

    def __mul__(self, other):
        """Returns a sound class formed from combination of its sounds with the items in mult.
        Useful for making classes that include long sounds, for instance, as (class file definition):
        T=ptk
        T=T*ː
        now, T=pː,tː,kː,p,t,k"""
        if isinstance(other, str):
            # if mult is just a string, wrap it in a list for the next part
            other = [other]
        # add "" to each set to make additions optional
        # so that for, say, A=abc
        # A*(1, 2) == a1,b1,c1,a2,b2,c2,a,b,c
        # combinations() isn't used because we need the base sounds to always be present
        sound_sets = product(self, chain(other, ("",) ))
        new_sounds = list("".join(s) for s in sound_sets)
        return sound_class(new_sounds)

    def __rmul__(self, other):
        """Works like mul but prepending instead of appending."""
        if isinstance(other, str):
            other = [other]
        sound_sets = product(chain(other, ("",) ), self)
        new_sounds = list("".join(s) for s in sound_sets)
        return sound_class(new_sounds)

    def get_string_matches(self) -> list[str]:
        """DEPRECATED: just iterate though the sounds and escape them there if you need it
        
        Returns a list of regex-escaped strings that correspond to the sounds of the class"""

        string_matches = []

        for member in self:
            if isinstance(member, str):
                string_matches.append(re.escape(member))

            elif isinstance(member, sound_class):
                string_matches += member.get_string_matches()

        return string_matches

    def get_regex(self)-> str:
        """DEPRECATED
        
        Returns a regular expression string that matches any member of the class"""

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
