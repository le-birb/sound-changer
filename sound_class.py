
from __future__ import annotations

from itertools import chain, product
from typing import Iterable

from ordered_set import OrderedSet as ordered_set


class sound_class(ordered_set):

    def __init__(self, sound_list: Iterable[str] = None, name: str = "") -> None:
        super().__init__(sound_list)
        self.name = name

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name + "=" + ",".join(sound for sound in self)

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
