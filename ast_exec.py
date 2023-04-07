
from rule_ast import ast_visitor, ast_node, rule_node, sound_node, expression_node, element_node, optional_node

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


if __name__ == "__main__":
    from rule_ast import parse_tokens
    from rule_tokenizer import tokenize_rule
    root = parse_tokens(tokenize_rule("abc(d) -> 123"))
    
    replacer = replacement_builder()

    word = "abcdefabcg"
    matches = matcher.match_rule(root, word)
    
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

    
