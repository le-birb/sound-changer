
from __future__ import annotations
import enum
from typing import Iterable, Union
from dataclasses import dataclass

from rule_tokenizer import token, token_type


class ast_node:
    "base class for abstract syntax tree nodes"

@dataclass
class sound_node(ast_node):
    sound: str

@dataclass
class sound_class_node(ast_node):
    sound_class: str

@dataclass
class numbered_sound_class_node(ast_node):
    sound_class: sound_class_node
    number: str

@dataclass
class sound_list_node(ast_node):
    expressions: list[expression_node]

@dataclass
class optional_node(ast_node):
    expression: expression_node | element_node

@dataclass
class repetition_node(ast_node):
    expression: expression_node | element_node

@dataclass
class word_border_node(ast_node):
    pass

# convenience type alias
element_node = Union[sound_node, sound_list_node, sound_class_node, numbered_sound_class_node, optional_node, repetition_node]

@dataclass
class expression_node(ast_node):
    expression: list[element_node]

@dataclass
class expression_list_node(ast_node):
    expressions: list[expression_node]

@dataclass
class environment_node(ast_node):
    pre_expression: expression_node
    post_expression: expression_node
    positive: bool = True

@dataclass
class environment_list_node(ast_node):
    positive_environments: list[environment_node] = None
    negative_environments: list[environment_node] = None

@dataclass
class changes_node(ast_node):
    changes: list[expression_list_node]


@dataclass
class rule_node(ast_node):
    changes: changes_node
    environments: environment_list_node = None



class marker(enum.Enum):
    """Enum for 'markers' added to parsing stack to indicate points relevant to parsing purposes but not
    ultimately represented in the ast."""
    space = enum.auto()
    comma = enum.auto()

    paren = enum.auto()
    brace = enum.auto()

    pos_env = enum.auto()
    neg_env = enum.auto()

    stack_start = enum.auto()

# TODO: add checks for syntax errors
def parse_to_ast(tokens: Iterable[token]) -> rule_node:
    parsing_stack: list[ast_node | marker] = [marker.stack_start]

    finished_changes = False

    for token in tokens:
        if token.type is token_type.sound:
            parsing_stack.append(sound_node(token.string))
        elif token.type is token_type.sound_class:
            parsing_stack.append(sound_class_node(token.string))
        elif token.type is token_type.sound_class_number:
            number = int(token.string)
            class_node = parsing_stack.pop()
            parsing_stack.append(numbered_sound_class_node(class_node, number))

        elif token.type is token_type.null_sound:
            parsing_stack.append(sound_node(""))
        elif token.type is token_type.word_border:
            parsing_stack.append(word_border_node())

        elif token.type is token_type.l_brace:
            parsing_stack.append(marker.brace)
        elif token.type is token_type.l_paren:
            parsing_stack.append(marker.brace)

        elif token.type is token_type.space and not finished_changes:
            parsing_stack.append(marker.space)
        elif token.type is token_type.space:
            pass # once changes are done, spaces are no longer meaningful
        elif token.type is token_type.comma:
            parsing_stack.append(marker.comma)

        elif token.type is token_type.ellipsis:
            parsing_stack.append(repetition_node(parsing_stack.pop()))

        elif token.type is token_type.r_brace:
            # parse a list of sound expressions, separated by commas
            # could restrict this further but there's no present need to
            expressions: list[expression_node] = []
            curr_expression: list[element_node] = []
            # take everything up to the open brace (and discard the brace, too)
            while element := parsing_stack.pop() is not marker.brace:
                if element is marker.comma:
                    # reverse since we pulled things off in reverse
                    curr_expression.reverse()
                    expressions.append(expression_node(curr_expression))
                    curr_expression = []
                elif element is marker.space:
                    # intentionally skip spaces within braces
                    pass
                else:
                    curr_expression.append(element)
            expressions.reverse()
            parsing_stack.append(sound_list_node(expressions))

        elif token.type is token_type.r_paren:
            # parse one expression back to the open parenthesis
            expression: list[element_node] = []
            # take everything up to the open parenthesis (and discard it the paren)
            while element := parsing_stack.pop() is not marker.brace:
                expression.append(element)
            expression.reverse()
            parsing_stack.append(optional_node(expression_node(expression)))

        elif token.type is token_type.arrow:
            # we've hit the end of one section but not of all of the changes
            parsing_stack.append(_parse_expression_list(parsing_stack))

        elif token.type in (token_type.neg_slash, token_type.pos_slash, token_type.eol) and not finished_changes:
            # we've hit the end of the changes
            # get the last expression list
            parsing_stack.append(_parse_expression_list(parsing_stack))
            # then collect the lists into a changes_node
            changes: list[expression_list_node] = []
            while parsing_stack:
                peek = parsing_stack[-1]
                if isinstance(peek, expression_list_node):
                    changes.append(parsing_stack.pop())
                else:
                    # something has gone wrong
                    # TODO: raise an appropriate error
                    pass
            finished_changes = True
            changes.reverse()
            parsing_stack.append(changes_node(changes))

            # add a marker to let the parser know later which kind of environment is currently being parsed
            if token.type is token_type.pos_slash:
                parsing_stack.append(marker.pos_env)
            elif token.type is token_type.neg_slash:
                parsing_stack.append(marker.neg_env)

        elif token.type is token_type.underscore:
            expression = []
            while parsing_stack[-1] not in (marker.pos_env, marker.neg_env):
                expression.append(parsing_stack.pop())
            expression.reverse()
            parsing_stack.append(expression_node(expression))

        elif token.type in (token_type.neg_slash, token_type.pos_slash):
            # we've hit the end of an environment
            # parse the post-environment expression and add it to the stack, then make an environment node
            expression = []
            while not isinstance(parsing_stack[-1], expression_node):
                expression.append(parsing_stack.pop())
            expression.reverse()
            post_expression = expression_node(expression)
            pre_expression = parsing_stack.pop()
            is_positive = parsing_stack.pop() is marker.pos_env
            parsing_stack.append(environment_node(pre_expression, post_expression, is_positive))

            # add a marker to let the parser know later which kind of environment it's parsing next
            if token.type is token_type.pos_slash:
                parsing_stack.append(marker.pos_env)
            elif token.type is token_type.neg_slash:
                parsing_stack.append(marker.neg_env)

        elif token.type is token_type.eol:
            # we've hit the end of all things, and also know that the latest things are environments
            # as above, make the latest environment node
            # parse the post-environment expression and add it to the stack, then make an environment node
            expression = []
            while not isinstance(parsing_stack[-1], expression_node):
                expression.append(parsing_stack.pop())
            expression.reverse()
            post_expression = expression_node(expression)
            pre_expression = parsing_stack.pop()
            is_positive = parsing_stack.pop() is marker.pos_env
            parsing_stack.append(environment_node(pre_expression, post_expression, is_positive))

            # then collect all environment nodes into an environment list node
            pos_envs = []
            neg_envs = []
            while isinstance(parsing_stack[-1], environment_node):
                env_node: environment_node = parsing_stack.pop()
                if env_node.positive:
                    pos_envs.append(env_node)
                else:
                    neg_envs.append(env_node)
            parsing_stack.append(environment_list_node(pos_envs, neg_envs))

    else:
        # the iterator ran out somehow
        # TODO: raise an appropriate error
        pass

    # finally, the parsing stack should now look like [changes_node, environment_list_node]
    return rule_node(*parsing_stack)


def _parse_expression_list(stack: list[ast_node | marker]) -> expression_list_node:
    expressions: list[expression_node] = []
    curr_expression: list[element_node] = []
    while stack:
        peek = stack[-1]

        if peek is marker.space:
            # the current expression, if it exists, is done, add it to the list
            if curr_expression:
                curr_expression.reverse()
                expressions.append(expression_node(curr_expression))
                curr_expression = []
            # pop the space off the stack
            stack.pop()

        elif isinstance(peek, expression_list_node):
            # we're done
            # add the current expression to the list if there's anything in it
            if curr_expression:
                curr_expression.reverse()
                expressions.append(expression_node(curr_expression))
            # and exit the loop
            break

        if peek is marker.stack_start:
            # we're also done
            # add the current expression to the list if there's anything in it
            if curr_expression:
                curr_expression.reverse()
                expressions.append(expression_node(curr_expression))
            # pop the start marker off - it's not needed anymore
            stack.pop()
            # and exit the loop
            break

        elif isinstance(peek, (sound_node, sound_list_node, sound_class_node, optional_node, repetition_node)):
            # we have a valid child of an expression node, throw it on the pile
            curr_expression.append(stack.pop())

        else:
            # we've got something that can't be a child of an expression
            # TODO: raise an appropriate error
            pass

    expressions.reverse()
    return expression_list_node(expressions)
