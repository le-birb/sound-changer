
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class rule(list):
    pattern: Any # not actually Any, but compiled regexes don't have typing support
    repl: str | Callable

    def apply(self, word: str) -> str:
        for pattern, repl in self:
            word = pattern.sub(repl, word)
        return word