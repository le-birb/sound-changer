

from typing import Iterable
from dataclasses import dataclass
from warnings import warn

from rule_ast_nodes import * 

from multipledispatch import dispatch

@dataclass
class match_data():
    start: int
    end: int
    contents: str = ""
    
    def __str__(self):
        return self.contents

def merge_matches(first: match_data, second: match_data,/) -> match_data:
    if first.end == second.start:
        return match_data(
                start = first.start,
                end = second.end,
                contents = first.contents + second.contents
            )
    else:
        raise ValueError("Matches must be consecutive to be merged!")


@dispatch(sound_node)
def visit(node: sound_node, word: str, pos: int) -> Iterable[match_data]:
    end_pos = pos + len(node.sound)
    if word[pos: end_pos] == node.sound:
        match = match_data(pos, end_pos)
        match.contents = node.sound
        yield match

@dispatch(optional_node)
def visit(node: optional_node, word: str, pos: int):
    yield from visit(node.expression, word = word, pos = pos)
    yield match_data(pos, pos)

@dispatch(sound_list_node)
def visit(node: sound_list_node, word: str, pos: int):
    for expr in node.expressions:
        yield from visit(expr, word = word, pos = pos)

@dispatch(expression_node)
def visit(node: expression_node, word: str, pos: int) -> Iterable[match_data]:
    # seek through the word, attempting to match each element successively
    element = node.elements[0]
    result: match_data
    for result in visit(element, word = word, pos = pos):
        if len(node.elements) > 1:
            for m in visit(expression_node(node.elements[1:]), word = word, pos = result.end):
                yield merge_matches(result, m)
        else:
            yield result

# skip anything unimplemented for now, returning an empty match for compatability with other code
@dispatch(ast_node)
def visit(node: ast_node, word: str, pos: int):
    warn(f"Matching currently unimplemented for {node.__class__.__name__} type nodes")
    return match_data(pos, pos, False)


def match_rule(rule: rule_node, word:str) -> list[match_data]:
    matches: list[match_data] = []
    for idx, _ in enumerate(word):
        match = next(visit(rule.changes[0].expressions[0], word = word, pos = idx), None)
        if match is not None:
            matches.append(match)
    return matches


if __name__ == "__main__":
    from rule_ast import parse_tokens
    from rule_tokenizer import tokenize_rule
    rule_1 = parse_tokens(tokenize_rule("abc(d) -> 123"))
    rule_2 = parse_tokens(tokenize_rule("c{d,e} -> C"))

    word = "abcdefabcgaceg"
    matches_1 = match_rule(rule_1, word)
    matches_2 = match_rule(rule_2, word)
    print(matches_1)
    print(matches_2)

