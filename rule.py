
from __future__ import annotations

class rule(list):
    def apply(self, word: str) -> str:
        for pattern, repl in self:
            word = pattern.sub(repl, word)
        return word