
import unittest

from sound_class import sound_class

class class_parse_test_case(unittest.TestCase):

    def setUp(self):
        self.C = sound_class('bc', 'C')
        self.V = sound_class('ae', 'V')
        sound_class.class_map = {
            'C': self.C,
            'V': self.V
        }


    def test_mul(self):
        self.assertEqual(self.C * self.V, sound_class(['ba', 'be', 'b', 'ca', 'ce', 'c']))