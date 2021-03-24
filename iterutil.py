
from typing import Iterable
from itertools import tee

# taken from https://docs.python.org/3/library/itertools.html#itertools-recipes
def pairwise(i: Iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    # makes 2 "copies" of i, advances one once and zips the now offest copies together
    a, b = tee(i)
    next(b, None)
    return zip(a, b)