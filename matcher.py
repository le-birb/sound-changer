

from typing import Iterable
from dataclasses import dataclass, field
from warnings import warn

from rule_ast_nodes import * 
from sound_class import sound_class

from multipledispatch import dispatch

#TODO: redo much of this in a different way maybe
#  or just add global state

#TODO: make better names for things
@dataclass
class match_data():
    start: int
    end: int
    contents: str = ""
    matched_sound_classes: list[sound_class] = field(default_factory = list)
    
    def __str__(self):
        return self.contents

    def __bool__(self):
        # any zero-length data should be falsey,
        # as it is a container-ish type
        return self.start != self.end

def merge_matches(first: match_data, second: match_data,/) -> match_data:
    if first.end == second.start:
        return match_data(
                start = first.start,
                end = second.end,
                contents = first.contents + second.contents,
                matched_sound_classes = first.matched_sound_classes + second.matched_sound_classes
            )
    else:
        raise ValueError("Matches must be consecutive to be merged!")


# all calls to _match must have word and pos as keyword arguments due to how @dispatch
# dispatches on ALL non-keyword arguments

@dispatch(sound_node)
def _match(node: sound_node, word: str, pos: int) -> Iterable[match_data]:
    end_pos = pos + len(node.sound)
    if word[pos: end_pos] == node.sound:
        match = match_data(pos, end_pos)
        match.contents = node.sound
        yield match

@dispatch(optional_node)
def _match(node: optional_node, word: str, pos: int):
    yield from _match(node.expression, word = word, pos = pos)
    yield match_data(pos, pos) # 0-length match can be merged with other matches in a larger expression

@dispatch(sound_list_node)
def _match(node: sound_list_node, word: str, pos: int):
    for expr in node.expressions:
        yield from _match(expr, word = word, pos = pos)

@dispatch(sound_class_node)
def _match(node: sound_class_node, word: str, pos: int):
    for sound in node.sound_class:
        end_pos = pos + len(sound)
        if word[pos: end_pos] == sound:
            yield match_data(pos, end_pos, sound, [node.sound_class])
            break # only ever match a single sound

@dispatch(expression_node)
def _match(node: expression_node, word: str, pos: int) -> Iterable[match_data]:
    # seek through the word, attempting to match each element successively
    element = node.elements[0]
    result: match_data
    for result in _match(element, word = word,  pos = pos):
        if len(node.elements) > 1:
            for m in _match(expression_node(node.elements[1:]), word = word, pos = result.end):
                yield merge_matches(result, m)
        else:
            yield result

# skip anything unimplemented for now, returning an empty match for compatability with other code
@dispatch(ast_node)
def _match(node: ast_node, word: str, pos: int):
    warn(f"Matching currently unimplemented for {node.__class__.__name__} type nodes")
    yield match_data(pos, pos)


def match_change(change: change_node, word: str) -> list[match_data]:
    matches: list[match_data] = []
    idx = 0
    while idx < len(word):
        # the _match implementation will generate every possible match for the rule at a given position;
        # we only take the first (if any)
        match_result: match_data = next(_match(change.target[0], word = word, pos = idx), None)
        if match_result:
            matches.append(match_result)
            idx = match_result.end
        else:
            idx += 1
    return matches


def environment_works(env: environment_node, word: str, match: match_data) -> bool:
    word_before_match = word[:match.start]
    # instead of writing reversed matching logic for pre-environments,
    # we may reverse the environment and the part of the word of interest
    # and do a forwards match
    pre_match = next(_match(_reverse_node(env.pre_expression), word = "".join(reversed(word_before_match)), pos = 0), None)
    # post-environments don't need anything fancy
    post_match = next(_match(env.post_expression, word = word, pos = match.end), None)

    return (bool(pre_match) == env.is_positive) and (bool(post_match) == env.is_positive)


def _reverse_node(node: ast_node) -> ast_node:
    match node:
        case sound_node(sound = s):
            return sound_node("".join(reversed(s)))
        case expression_node(elements = elms):
            rev_elms = [_reverse_node(e) for e in reversed(elms)]
            return expression_node(rev_elms)
        case sound_class_node(sound_class = c):
            return sound_class_node(c.reverse())
        case sound_list_node(expressions = exprs):
            return sound_list_node([_reverse_node(e) for e in exprs])
        case optional_node(expression = e):
            return optional_node(_reverse_node(e))
        case repetition_node(expression = e):
            return repetition_node(_reverse_node(e))
        case expression_list_node() as n:
            return expression_list_node([_reverse_node(e) for e in reversed(n)])
        case word_border_node():
            return node
        case _:
            raise ValueError(f"Reversing not supported on nodes of type {type(node)}")
