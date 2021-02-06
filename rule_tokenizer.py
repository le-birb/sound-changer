
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

    r_paren = auto()
    l_paren = auto()
    r_brace = auto()
    l_brace = auto()
    r_bracket = auto()
    l_bracket = auto()

    sound_class = auto()
    matched_sound_class = auto() # e.g. V0, C0
    sound = auto()

    eol = auto()

    def __repr__(self):
        return "token_type." + self.name


class token:
    def __init__(self, type: token_type, string: str):
        self.type: token_type = type
        self.string: str = string

    def __repr__(self):
        return repr(self.type) + ": " + self.string


class tokenization_error(Exception):
    pass

_arrows = {"=>", "->", ">", "→"}
_special_chars = {"/", "/!", "_", "...", ",", " ", "#", "(", ")", "{", "}", "[", "]"} | _arrows

def tokenize_special_char(string: str) -> token:
    "Takes a special 'character' (may be longer that 1 character) and spits out a corresponding token."
    if string in _arrows:
        return token(token_type.arrow, string)
    elif string == "/":
        return token(token_type.pos_slash, string)
    elif string == "/!":
        return token(token_type.neg_slash, string)
    elif string == "_":
        return token(token_type.underscore, string)
    elif string == "...":
        return token(token_type.ellipsis, string)
    elif string == ",":
        return token(token_type.comma, string)
    elif string == " ":
        return token(token_type.space, string)

    elif string == "#":
        return token(token_type.word_border, string)

    elif string == "(":
        return token(token_type.l_paren, string)
    elif string == ")":
        return token(token_type.r_paren, string)
    elif string == "{":
        return token(token_type.l_brace, string)
    elif string == "}":
        return token(token_type.r_brace, string)
    elif string == "[":
        return token(token_type.l_bracket, string)
    elif string == "]":
        return token(token_type.r_bracket, string)


def tokenize_rule(rule_str: str, sound_classes: Iterable[str], defined_sounds: Iterable[str] = [], require_defined: bool = False) -> list[token]:
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
        special_char = re.match(r"\L<special_chars>", rule_str, pos = current_pos, special_chars = _special_chars)
        if special_char:
            match = special_char[0]
            token_list.append(tokenize_special_char(match))
            current_pos += len(match)
            # skip to next part of the string after creating a token
            continue

        # then, check for a sound class
        sound_class = re.match(r"\L<sound_classes>", rule_str, pos = current_pos, sound_classes = sound_classes)
        if sound_class:
            match = sound_class[0]

            # check if the found sound class is directly followed by a number
            number = re.match(r"\d+", rule_str, pos = current_pos + len(match))
            if number:
                match += number[0]
                token_list.append(token(token_type.matched_sound_class, match))
            else:
                token_list.append(token(token_type.sound_class, match))
            
            current_pos += len(match)
            # skip to next part of the string after creating a token
            continue

        # check for sounds defined in defined_sounds
        # primarily to get multi-char sounds matched properly
        defined_sound = re.match(r"\L<defined_sounds>", rule_str, pos = current_pos, defined_sounds = defined_sounds)
        if defined_sound:
            match = defined_sound[0]
            token_list.append(token(token_type.sound, match))
            current_pos += len(match)
            # skip to next part of the string after creating a token
            continue

        # at this point, the next character is not anything the tokenizer has been specifically told to accept
        # match the next unicode grapheme with \X, as 999 times in 1000 that'll be more useful than a character
        # if there's diacritics involved
        next_char = re.match(r"\X", rule_str, pos = current_pos)
        
        if require_defined:
            raise tokenization_error("unrecognized character '{}' found".format(next_char))
        else:
            token_list.append(token(token_type.sound, next_char))
            current_pos += len(next_char)

    token_list.append(token(token_type.eol, ""))

    return token_list
