
import unittest

from rule_tokenizer import tokenize_rule, token, token_type, _arrows, _null_sounds, tokenization_error

class tokenizer_test_case(unittest.TestCase):

    def test_tokens(self):
        """Tests that each token type individually tokenizes properly"""
        for arrow in _arrows:
            self.assertEqual(tokenize_rule(arrow), [token(token_type.arrow), token(token_type.eol)])

        self.assertEqual(tokenize_rule("/"), [token(token_type.pos_slash), token(token_type.eol)])
        self.assertEqual(tokenize_rule("/!"), [token(token_type.neg_slash), token(token_type.eol)])
        self.assertEqual(tokenize_rule("_"), [token(token_type.underscore), token(token_type.eol)])
        self.assertEqual(tokenize_rule("..."), [token(token_type.ellipsis), token(token_type.eol)])
        self.assertEqual(tokenize_rule(","), [token(token_type.comma), token(token_type.eol)])
        # can't just test a space alone since leading/trailing whitespace is stripped
        self.assertEqual(tokenize_rule(", ,"), [token(token_type.comma), token(token_type.space), token(token_type.comma), token(token_type.eol)])

        self.assertEqual(tokenize_rule("#"), [token(token_type.word_border), token(token_type.eol)])
        for null in _null_sounds:
            self.assertEqual(tokenize_rule(null), [token(token_type.null_sound), token(token_type.eol)])

        self.assertEqual(tokenize_rule(")"), [token(token_type.r_paren), token(token_type.eol)])
        self.assertEqual(tokenize_rule("("), [token(token_type.l_paren), token(token_type.eol)])
        self.assertEqual(tokenize_rule("}"), [token(token_type.r_brace), token(token_type.eol)])
        self.assertEqual(tokenize_rule("{"), [token(token_type.l_brace), token(token_type.eol)])

        self.assertEqual(tokenize_rule("C", ["C"]), [token(token_type.sound_class, "C"), token(token_type.eol)])
        self.assertEqual(tokenize_rule("C1", ["C",]), [token(token_type.sound_class, "C"), token(token_type.sound_class_number, "1"), token(token_type.eol)])
        self.assertEqual(tokenize_rule("a"), [token(token_type.sound, "a"), token(token_type.eol)])

        self.assertEqual(tokenize_rule(""), [token(token_type.eol)])


    def test_errors(self):
        self.assertRaises(tokenization_error, tokenize_rule, "a", [], defined_sounds = ["b"], require_defined = True)

    def test_strings(self):
        """Tests a few different "weird" strings as a sanity check"""

        # make sure grapheme segmentation is relatively sane
        self.assertEqual(tokenize_rule("ů̠̟̩̈̃a̍̊"), [token(token_type.sound, "ů̠̟̩̈̃"), token(token_type.sound, "a̍̊"), token(token_type.eol)])


if __name__ == "__main__":
    unittest.main()
