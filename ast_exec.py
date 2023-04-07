
from dataclasses import dataclass
from rule_ast import ast_visitor, ast_node, rule_node, sound_node, expression_node, element_node, optional_node
from itertools import pairwise

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

#TODO: think about having these not even be classes

class target_matcher(ast_visitor):
    """
    visit(node, word, pos) attempts to match node in word at pos, returning corresponding match_data
    """
    @dispatch(sound_node)
    def visit(self, node: sound_node, word: str, pos: int) -> match_data:
        end_pos = pos + len(node.sound)
        match = match_data(pos, end_pos, False)
        match.is_match = word[pos: end_pos] == node.sound
        match.contents += node.sound
        return match

    @dispatch(optional_node)
    def visit(self, node: optional_node, word: str, pos: int):
        match = self.visit(node.expression, word = word, pos = pos)
        if match:
            return match
        else:
            pass
        return match_data(pos, pos, True)

    @dispatch(expression_node)
    def visit(self, node: expression_node, word: str, pos: int) -> match_data:
        match = match_data(pos, pos, True)
        # keeps track of where the child will be attempting to match
        child_pos = pos
        # seek through the word, attempting to match each element successively
        for element in node.elements:
            result = self.visit(element, word = word, pos = child_pos)
            if result:
                match = merge_matches(match, result)
                child_pos = match.end
            else:
                match.is_match = False
                break # we already know we don't match, no need to check further

        return match
    
    # skip anything else for now, returning an empty match for compatability with other code
    @dispatch(ast_node)
    def visit(self, node: ast_node, word: str, pos: int):
        super().visit(node, word = word, pos = pos)
        return match_data(pos, pos, False)


class replacement_builder(ast_visitor):
    @dispatch(ast_node)
    def visit(self, node: ast_node, data: match_data) -> str:
        super().visit(node, match = match_data)
        return ""

    @dispatch(sound_node)
    def visit(self, node: sound_node, data: match_data):
        return node.sound

    @dispatch(expression_node)
    def visit(self, node: expression_node, data: match_data):
        return "".join(self.visit(n, data = data) for n in node.elements)


# def interpret_rule(rule: rule_node, word: str):
#     for target, replacement in pairwise(rule.changes):
#         # for now, I'm only implementing a single replacement at a time
#         # e.g. a > e
#         # stuff like a, e > e, i will come later
#         target, replacement = target.expressions[0], replacement.expressions[0]
#         t_idx: int = 0
#         matches: list[tuple[int]] = []
#         matcher = target_matcher()
#         for char, c_idx in enumerate(word):
#             match, pos, data = matcher.visit(target)


if __name__ == "__main__":
    from rule_ast import parse_tokens
    from rule_tokenizer import tokenize_rule
    root = parse_tokens(tokenize_rule("abc(d) -> 123"))
    matcher = target_matcher()
    
    replacer = replacement_builder()

    word = "abcdefabcg"
    matches: list[match_data] = []
    for idx, char in enumerate(word):
        match = matcher.visit(root.changes[0].expressions[0], word = word, pos = idx)
        matches.append(match)
    
    new_str_pieces:list[str] = []
    # keeps track of where in the word we're trying to fill in
    word_ptr = 0
    for match in filter(None, matches):
        new_str_pieces.append(word[word_ptr:match.start])
        repl = replacer.visit(root.changes[1].expressions[0], data = match)
        new_str_pieces.append(repl)
        word_ptr = match.end
    # make sure to include any trailing bits after any matches
    new_str_pieces.append(word[word_ptr:])
    
    new_word = "".join(new_str_pieces)
    print(new_word)

    
