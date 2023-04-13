
from __future__ import annotations

# import dataclass with an underscore so it isn't caught in a * import
from dataclasses import dataclass as _dataclass


class ast_node:
    "base class for abstract syntax tree nodes"

@_dataclass
class sound_node(ast_node):
    sound: str

@_dataclass
class sound_class_node(ast_node):
    name: str

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
element_node = sound_node | sound_list_node | sound_class_node | numbered_sound_class_node | optional_node | repetition_node

@_dataclass
class expression_node(ast_node):
    elements: list[element_node]

@_dataclass
class expression_list_node(ast_node):
    expressions: list[expression_node]

@_dataclass
class environment_node(ast_node):
    pre_expression: expression_node
    post_expression: expression_node
    positive: bool = True

@_dataclass
class environment_list_node(ast_node):
    positive_environments: list[environment_node] = None
    negative_environments: list[environment_node] = None


@_dataclass
class rule_node(ast_node):
    changes: list[expression_list_node]
    environments: environment_list_node = None