
from dataclasses import dataclass
from rule_ast import ast_visitor, ast_node, rule_node, sound_node, expression_node, element_node, optional_node
from itertools import pairwise

import matcher

from multipledispatch import dispatch

class replacement_builder(ast_visitor):
    @dispatch(ast_node)
    def visit(self, node: ast_node, data: matcher.match_data) -> str:
        super().visit(node, match = matcher.match_data)
        return ""

    @dispatch(sound_node)
    def visit(self, node: sound_node, data: matcher.match_data):
        return node.sound

    @dispatch(expression_node)
    def visit(self, node: expression_node, data: matcher.match_data):
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
    
    replacer = replacement_builder()

    word = "abcdefabcg"
    matches: list[matcher.match_data] = []
    for idx, char in enumerate(word):
        match = next(matcher.visit(root.changes[0].expressions[0], word = word, pos = idx), None)
        if match is not None:
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

    
