

from typing import Iterable
from dataclasses import dataclass

from rule_ast import ast_node, expression_node, optional_node, sound_node, rule_node

from multipledispatch import dispatch

@dataclass
class match_data():
    start: int
    end: int
    is_match: bool
    contents: str = ""

    def __bool__(self):
        return self.is_match
    
    def __str__(self):
        return self.contents

def merge_matches(first: match_data, second: match_data,/) -> match_data:
    if first.end == second.start:
        return match_data(
                start = first.start,
                end = second.end,
                is_match = first.is_match and second.is_match,
                contents = first.contents + second.contents
            )
    else:
        raise ValueError("Matches must be consecutive to be merged!")


@dispatch(sound_node)
def visit(node: sound_node, word: str, pos: int) -> Iterable[match_data]:
    end_pos = pos + len(node.sound)
    match = match_data(pos, end_pos, False)
    match.is_match = word[pos: end_pos] == node.sound
    match.contents += node.sound
    yield match

@dispatch(optional_node)
def visit(node: optional_node, word: str, pos: int):
    for match in visit(node.expression, word = word, pos = pos):
        if match:
            yield match
        else:
            pass
    yield match_data(pos, pos, True)

# skip anything else for now, returning an empty match for compatability with other code
@dispatch(ast_node)
def visit(node: ast_node, word: str, pos: int):
    return match_data(pos, pos, False)

@dispatch(expression_node)
def visit(node: expression_node, word: str, pos: int) -> Iterable[match_data]:
    # seek through the word, attempting to match each element successively
    element = node.elements[0]
    result: match_data
    for result in filter(None, visit(element, word = word, pos = pos)):
        if len(node.elements) > 1:
            for m in filter(None, visit(expression_node(node.elements[1:]), word = word, pos = result.end)):
                yield merge_matches(result, m)
        else:
            yield result


def match_rule(rule: rule_node, word:str) -> list[match_data]:
    matches: list[match_data] = []
    for idx, _ in enumerate(word):
        match = next(filter(None, visit(rule.changes[0].expressions[0], word = word, pos = idx)), None)
        if match is not None:
            matches.append(match)
    return matches


if __name__ == "__main__":
    from rule_ast import parse_tokens
    from rule_tokenizer import tokenize_rule
    root = parse_tokens(tokenize_rule("abc(d) -> 123"))

    word = "abcdefabcg"
    matches = match_rule(root, word)
    
    print(matches)

