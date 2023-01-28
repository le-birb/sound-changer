
from dataclasses import dataclass
from rule_ast import ast_visitor, ast_node, rule_node, sound_node, expression_node, element_node
from iterutil import pairwise

# going to start with just a simple plain text replacement

def _match(element: element_node, word: str, position: int) -> tuple(bool, int):
    is_match: bool
    end_pos: int
    match element:
        case sound_node(sound):
            # TODO: check if len(sound) == 1 always
            end_pos = position + len(sound)
            try:
                is_match = word[position, end_pos + 1] == sound
            except:
                pass
        case ast_node():
            # temporary "do nothing" for other matching types
            is_match = False
            end_pos = position
        case _:
            pass
    return is_match, end_pos

# TODO: rewrite this and associated code to include more data in the match
@dataclass
class match_data():
    start: int
    end: int

class target_matcher(ast_visitor):
    def visit(self, node: ast_node, word: str, pos: int) -> tuple[bool, int, dict]:
        func_name = f"visit_{node.__class__.__name__}"
        visit_func = getattr(self, func_name, self._visit_default)
        return *visit_func(node, word, pos), {}

    def visit_sound_node(self, node: sound_node, word: str, pos: int):
        end_pos = pos + len(node.sound)
        return (word[pos, end_pos + 1] == node.sound, end_pos)

    def visit_expression_node(self, node: expression_node, word: str, pos: int):
        results: list[tuple[bool, int]] = []
        child_pos = pos
        # seek through the word, attempting to match each element successively
        for element in node.elements:
            result = self.visit(element, word, child_pos)
            results.append(result)
            child_pos = result[1]

        matches, ends = zip(*results)
        is_overall_match = all(matches)
        end = ends[-1]
        return is_overall_match, end

    def _visit_default(self, node: ast_node, word: str, pos: int):
        # skip over anything non-sound for now
        return (False, 0)


class replacement_builder(ast_visitor):
    def visit(self, node: ast_node, data) -> str:
        func_name = f"visit_{node.__class__.__name__}"
        visit_func = getattr(self, func_name, self._visit_default)
        return visit_func(node, data)

    def visit_sound_node(self, node: sound_node, _):
        return node.sound

    def visit_expression_node(self, node: expression_node, data):
        return "".join(self.visit(n) for n in node.elements)

    def _visit_default(self, node: ast_node, data):
        return ""


def interpret_rule(rule: rule_node, word: str):
    for target, replacement in pairwise(rule.changes):
        # for now, I'm only implementing a single replacement at a time
        # e.g. a > e
        # stuff like a, e > e, i will come later
        target, replacement = target[0].expression, replacement[0].expression
        t_idx: int = 0
        matches: list[tuple[int]] = []
        matcher = target_matcher()
        for char, c_idx in enumerate(word):
            match, pos, data = matcher.visit(target)

