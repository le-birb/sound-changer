
from typing import TypeVar
from collections.abc import Sequence, Iterator
from itertools import tee


T = TypeVar('T')

# taken from https://docs.python.org/3/library/itertools.html#itertools-recipes
def pairwise(i: Sequence[T]) -> Iterator[tuple[T, T]]:
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    # makes 2 "copies" of i, advances one once and zips the now offest copies together
    a: T
    b: T
    a, b = tee(i)
    next(b, None)
    return zip(a, b)