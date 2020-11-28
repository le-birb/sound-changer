
from enum import Enum

class token_type(Enum):
    sound = "sound"
    sound_class = "sound class"
    matched_sound = "matched sound"
    empty_sound = "empty sound"

    open_paren = "open parenthesis"
    close_paren = "close parenthesis"
    open_brace = "open brace"
    close_brace = "close brace"

    ellipsis = "ellipsis"
    word_boundary = "word boundary"
    syllable_boundary = "syllable_boundary"
    env_pos = "environment position"
    comma = "comma"

    arrow = "arrow"
    env_separator = "environment separator"
    neg_env_separator = "negative environment separator"

    def __repr__(self):
        return(str(self))


class token:
    def __init__(self, type, value = None):
        self.type = type
        self.value = value

    def __str__(self):
        string = str(self.type) + " token"
        if self.value:
            string = string + " with value " + str(self.value)
        return string
    
    def __repr__(self):
        rep = "token(" + repr(self.type)
        if self.value:
            rep = rep + ", \"" + repr(self.value) + '"'
        rep = rep + ")"
        return rep


def match_at(string: str, match: str, idx: int):
    if len(string) < idx + len(match):
        return False # match cannot possibly fit
    else:
        return string[idx:idx+len(match)] == match


def tokenize(rule: str, classes):
    tokens = []

    i = 0

    # use a while loop to allow skippping characters
    while i < len(rule):

        if match_at(rule, "->", i) or match_at(rule, "=>", i):
            tokens.append(token(token_type.arrow))
            i = i + 1
        elif rule[i] == "→":
            tokens.append(token(token_type.arrow))
            pass
        elif match_at(rule, "/!", i):
            tokens.append(token(token_type.neg_env_separator))
            i = i + 1
        elif rule[i] == "/":
            tokens.append(token(token_type.env_separator))
        elif match_at(rule, "...", i):
            tokens.append(token(token_type.ellipsis))
            i = i +2
        elif rule[i] == "#":
            tokens.append(token(token_type.word_boundary))
        elif rule[i] == "_":
            tokens.append(token(token_type.env_pos))
        elif rule[i] == ",":
            tokens.append(token(token_type.comma))
        elif rule[i] == "∅":
            tokens.append(token(token_type.empty_sound))
        
        elif rule[i] == "(":
            tokens.append(token(token_type.open_paren))
        elif rule[i] == ")":
            tokens.append(token(token_type.close_paren))
        elif rule[i] == "{":
            tokens.append(token(token_type.open_brace))
        elif rule[i] == "}":
            tokens.append(token(token_type.close_brace))

        elif rule[i] == " " or rule[i] == "\t":
            pass # ignore spaces and tabs

        else:
            for c in classes:
                if match_at(rule, c, i):
                    tokens.append(token(token_type.sound_class, c))
                    break
            else:
                # TODO: have certain defined allowable sounds?
                # or just defined multichar sounds?
                tokens.append(token(token_type.sound, rule[i]))

        # incrememnt index to behave mostly like a for loop
        i = i + 1

    return tokens

tokens = tokenize("cab -> bac / A_(C...)A /! ts_", classes = ["A", "C"])

print(*tokens, sep = "\n")