
from matcher import match_rule
from replacer import replace_matches


if __name__ == "__main__":
    from rule_ast import parse_tokens
    from rule_tokenizer import tokenize_rule
    root = parse_tokens(tokenize_rule("abc(d) -> 123"))

    word = "abcdefabcg"
    matches = match_rule(root, word)
    new_word = replace_matches(word, matches, root)
    print(new_word)

    
