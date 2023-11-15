
from multipledispatch import dispatch

from rule_ast_nodes import *
from matcher import match_data

#TODO: redo much of this in a different way maybe
#  or just add global state

#TODO: make better names for things

@dispatch(ast_node)
def _replace(node: ast_node, data: match_data) -> str:
    _replace(node, match = match_data)
    return ""

@dispatch(sound_node)
def _replace(node: sound_node, data: match_data):
    return node.sound

@dispatch(expression_node)
def _replace(node: expression_node, data: match_data):
    return "".join(_replace(n, data = data) for n in node.elements)



def replace_matches(word: str, matches: list[match_data], rule: rule_node) -> str:
    replacement = rule.changes[1].expressions[0]
    new_str_pieces:list[str] = []
    # keeps track of where in the word we're trying to fill in
    word_ptr = 0
    for m in filter(None, matches):
        new_str_pieces.append(word[word_ptr: m.start])
        repl = _replace(replacement, data = m)
        new_str_pieces.append(repl)
        word_ptr = m.end
    # make sure to include any trailing bits after any matches
    new_str_pieces.append(word[word_ptr:])
    return "".join(new_str_pieces)

