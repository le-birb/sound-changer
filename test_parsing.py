
import unittest

import parsing
from sound_class import sound_class

class class_parse_test_case(unittest.TestCase):

    def setUp(self):
        self.C = sound_class('bc', 'C')
        self.V = sound_class('ae', 'V')
        sound_class.class_map = {
            'C': self.C,
            'V': self.V
        }

    def test_class_parse(self):
        self.assertEqual(parsing.eval_class_expression('C'), self.C)
        self.assertEqual(parsing.eval_class_expression('V'), self.V)

    def test_sound_parse(self):
        self.assertEqual(parsing.eval_class_expression('a,b,c'), parsing.eval_class_expression('abc'))
        self.assertEqual(parsing.eval_class_expression('a,b,c'), parsing.sound_sequence('abc'))

    def test_class_mult(self):
        self.assertEqual(parsing.eval_class_expression('C*V'), self.C * self.V)

    def test_sounds_mult(self):
        self.assertEqual(parsing.eval_class_expression('ptk*ʰ'), parsing.sound_sequence('ptk') * parsing.sound_sequence('ʰ'))

    def test_class_sound_mul(self):
        self.assertEqual(parsing.eval_class_expression('C*ː'), self.C * parsing.sound_sequence('ː'))


if __name__ == "__main__":
    unittest.main()