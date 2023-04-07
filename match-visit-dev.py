

from typing import Iterable


from ast_exec import match_data, merge_matches
from rule_ast import ast_node, expression_node, optional_node, sound_node

from multipledispatch import dispatch

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


if __name__ == "__main__":
    from rule_ast import parse_tokens
    from rule_tokenizer import tokenize_rule
    root = parse_tokens(tokenize_rule("abc(d) -> 123"))

    word = "abcdefabcg"
    matches: list[match_data] = []
    for idx, char in enumerate(word):
        if (match := next(visit(root.changes[0].expressions[0], word = word, pos = idx), None)) is not None:
            matches.append(match)
    
    print(list(filter(None, matches)))

