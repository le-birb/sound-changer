
from __future__ import annotations

# import dataclass with an underscore so it isn't caught in a * import
from dataclasses import dataclass as _dataclass

from sound_class import sound_class

class ast_node:
    "base class for abstract syntax tree nodes"

@_dataclass
class sound_node(ast_node):
    sound: str

@_dataclass
class sound_class_node(ast_node):
    sound_class: sound_class

@_dataclass
class numbered_sound_class_node(ast_node):
    sound_class: sound_class_node
    number: str

@_dataclass
class sound_list_node(ast_node):
    expressions: list[expression_node]

@_dataclass
class optional_node(ast_node):
    expression: expression_node | element_node

@_dataclass
class repetition_node(ast_node):
    expression: expression_node | element_node

@_dataclass
class word_border_node(ast_node):
    pass

# convenience type alias
element_node = sound_node | sound_list_node | sound_class_node | numbered_sound_class_node | optional_node | repetition_node | word_border_node

@_dataclass
class expression_node(ast_node):
    elements: list[element_node]

# this one inherits from list as it's a more structural component than a meaningful one
# it's still its own thing to distinguish it from other lists of things that may
# arise during parsing
class expression_list_node(ast_node, list):
    # expressions: list[expression_node]
    pass

@_dataclass
class environment_node(ast_node):
    pre_expression: expression_node
    post_expression: expression_node
    is_positive: bool = True

@_dataclass
class change_node(ast_node):
    target: expression_list_node
    replacement: expression_list_node


@_dataclass
class rule_node(ast_node):
    changes: list[change_node]
    positive_environments: list[environment_node] = None
    negative_environments: list[environment_node] = None

