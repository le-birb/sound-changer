
from multipledispatch import dispatch

from rule_ast_nodes import *
from matcher import match_data

class replacer:
    sound_classes_seen: int

    def __init__(self):
        self.sound_classes_seen = 0

    @dispatch(ast_node)
    def _replace(self, node: ast_node, data: match_data) -> str:
        self._replace(node, data = data)
        return ""

    @dispatch(sound_node)
    def _replace(self, node: sound_node, data: match_data) -> str:
        return node.sound

    @dispatch(sound_class_node)
    def _replace(self, node: sound_class_node, data: match_data) -> str:
        matched_class = data.matched_sound_classes[self.sound_classes_seen]
        self.sound_classes_seen += 1
        replacer_class = node.sound_class
        sound_idx = matched_class.index(data.contents)
        return replacer_class[sound_idx]

    @dispatch(expression_node)
    def _replace(self, node: expression_node, data: match_data) -> str:
        return "".join(self._replace(n, data = data) for n in node.elements)



def replace_matches(word: str, matches: list[match_data], rule: change_node) -> str:
    r = replacer()
    new_str_pieces:list[str] = []
    # keeps track of where in the word we're trying to fill in
    word_ptr = 0
    for m in filter(None, matches):
        r.sound_classes_seen = 0
        new_str_pieces.append(word[word_ptr: m.start])
        repl = r._replace(rule.replacement[0], data = m)
        new_str_pieces.append(repl)
        word_ptr = m.end
    # make sure to include any trailing bits after any matches
    new_str_pieces.append(word[word_ptr:])
    return "".join(new_str_pieces)

