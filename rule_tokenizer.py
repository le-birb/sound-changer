
from __future__ import annotations

from enum import Enum, auto
from typing import Iterable

import regex as re


class token_type(Enum):
    arrow = auto()
    pos_slash = auto()
    neg_slash = auto()
    underscore = auto()
    ellipsis = auto()
    comma = auto()
    space = auto()

    word_border = auto()
    null_sound = auto()

    r_paren = auto()
    l_paren = auto()
    r_brace = auto()
    l_brace = auto()
    # brackets will likely be used eventually but are currently not
    # r_bracket = auto()
    # l_bracket = auto()

    sound_class = auto()
    sound_class_number = auto()
    sound = auto()

    eol = auto()

    def __repr__(self):
        return "token_type." + self.name


class token:
    def __init__(self, type: token_type, string: str = None):
        self.type: token_type = type
        self.string: str = string

    def __repr__(self):
        if self.string:
            return f"token({self.type}, \"{self.string}\")"
        else:
            return f"token({self.type})"

    def __eq__(self, other) -> bool:
        if isinstance(other, token):
            return self.type == other.type and self.string == other.string
        else:
            return False


class tokenization_error(Exception):
    pass

_arrows = {"=>", "->", ">", "→"}
_null_sounds = {"0", "∅"}
_special_chars = {"/", "/!", "_", "...", ",", " ", "#", "(", ")", "{", "}", "[", "]"} | _arrows | _null_sounds 

def _tokenize_special_char(string: str) -> token:
    "Takes a special 'character' (may be longer that 1 character) and spits out a corresponding token."
    if string in _arrows:
        return token(token_type.arrow)
    elif string == "/":
        return token(token_type.pos_slash)
    elif string == "/!":
        return token(token_type.neg_slash)
    elif string == "_":
        return token(token_type.underscore)
    elif string == "...":
        return token(token_type.ellipsis)
    elif string == ",":
        return token(token_type.comma)
    elif string == " ":
        return token(token_type.space)

    elif string == "#":
        return token(token_type.word_border)
    elif string in _null_sounds:
        return token(token_type.null_sound)

    elif string == "(":
        return token(token_type.l_paren)
    elif string == ")":
        return token(token_type.r_paren)
    elif string == "{":
        return token(token_type.l_brace)
    elif string == "}":
        return token(token_type.r_brace)
    # brackets will likely be used eventually but are currently not
    # elif string == "[":
    #     return token(token_type.l_bracket, string)
    # elif string == "]":
    #     return token(token_type.r_bracket, string)


def tokenize_rule(rule_str: str, sound_classes: Iterable[str] = [], defined_sounds: Iterable[str] = [], require_defined: bool = False) -> list[token]:
    """Takes in a rule string and a set of sound classes and returns a list of tokens.
    
    defined_sounds is used to provide a list of all sounds that should be recognized as individual units,
    particularly sounds represented with multiple characters, e.g. 'ts'
    
    require_defined tells the tokenizer whether to raise an exception if it encounters a character that doesn't
    match any special characters, sound classes, or sounds defined by defined_sounds"""

    # leading/trailing whitespace is never of interest
    rule_str = rule_str.strip()

    # keeps track of where we're looking
    current_pos = 0
    token_list: list[token] = []
    
    while current_pos < len(rule_str):
        # first, check for a special char
        special_char_match = re.match(r"\L<special_chars>", rule_str, pos = current_pos, special_chars = _special_chars)
        if special_char_match:
            match = special_char_match[0]
            token_list.append(_tokenize_special_char(match))
            current_pos += len(match)
            # skip to next part of the string after creating a token
            continue

        # then, check for a sound class
        sound_class_match = re.match(r"\L<sound_classes>", rule_str, pos = current_pos, sound_classes = sound_classes)
        if sound_class_match and sound_classes:
            match = sound_class_match[0]
            token_list.append(token(token_type.sound_class, match))
            current_pos += len(match)
            # skip to next part of the string after creating a token
            continue

        # now check for a number coming directly after a sound class
        if token_list and token_list[-1].type is token_type.sound_class and rule_str[current_pos] in '0123456789':
            number = re.match(r"\d+", rule_str, pos = current_pos)[0]
            token_list.append(token(token_type.sound_class_number, number))
            continue

        # check for sounds defined in defined_sounds
        # primarily to get multi-char sounds matched properly
        defined_sound_match = re.match(r"\L<defined_sounds>", rule_str, pos = current_pos, defined_sounds = defined_sounds)
        if defined_sound_match and defined_sounds:
            match = defined_sound_match[0]
            token_list.append(token(token_type.sound, match))
            current_pos += len(match)
            # skip to next part of the string after creating a token
            continue

        # at this point, the next character is not anything the tokenizer has been specifically told to accept
        # match the next unicode grapheme with \X, as 999 times in 1000 that'll be more useful than a character
        # if there's diacritics involved
        next_char_match = re.match(r"\X", rule_str, pos = current_pos)[0]
        
        if require_defined:
            raise tokenization_error("unrecognized character '{}' found".format(next_char_match))
        else:
            token_list.append(token(token_type.sound, next_char_match))
            current_pos += len(next_char_match)

    token_list.append(token(token_type.eol))

    return token_list
