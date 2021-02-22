
from typing import Iterable


_no_match = "(*FAIL)"
_skip_attempt = "(*PRUNE)" + _no_match

def regex_concat(*matches: str) -> str:
    return "".join(matches)

def regex_or(*matches: str) -> str:
    """Note: does not automatically group the output."""
    return '|'.join(matches)

def regex_optional(match: str) -> str:
    if match:
        return match + "?"
    else:
        return ""


def regex_group(match: str, name: str = None, silent: bool = False) -> str:
    if silent:
        return "(?:" + match + ")"

    elif name:
        return "(?<" + name + ">" + match + ")"
    else:
        return "(" + match + ")"


def regex_list_match(name: str) -> str:
    return r"\L<" + name + ">"


def regex_define(*groups: str) -> str:
    return "(?(DEFINE)" + "".join(groups) + ")"


def regex_conditional(condition: str, branch_true: str, branch_false: str = "") -> str:
    if branch_true == branch_false:
        # a choice between A and A is always A
        return branch_true
    
    elif condition == "":
        # an empty condition will always match
        return branch_true
    
    else:
        if not branch_false:
            # (?(A)B|) is equivalent to (?(A)B), and the latter has less clutter when reading
            return "(?({}){})".format(condition, branch_true)
        else:
            return "(?({}){}|{})".format(condition, branch_true, branch_false)


def lookbehind(match: str, positive = True):
    if not match:
        # typically, match is an empty string here, we don't need to wrap empty strings
        return ""

    if positive:
        return "(?<=" + match + ")"
    else:
        return "(?<!" + match + ")"

def lookbehind_mult(matches: Iterable[str], positive = True):
    return lookbehind(regex_or(matches), positive)


def lookahead(match: str, positive = True):
    if not match:
        # typically, match is an empty string here, we don't need to wrap empty strings
        return ""

    if positive:
        return "(?=" + match + ")"
    else:
        return "(?!" + match + ")"

def lookahead_mult(matches: Iterable[str], positive = True):
    return lookahead(regex_or(matches), positive)

