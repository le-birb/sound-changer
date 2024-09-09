
from __future__ import annotations

import enum
from typing import Iterable

from rule_ast_nodes import *
from rule_tokenizer import token, token_type


class _marker(enum.Enum):
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
def parse_tokens(tokens: Iterable[token], sound_classes: dict[str, sound_class]) -> rule_node:
    parsing_stack: list[ast_node | _marker] = [_marker.stack_start]

    finished_changes = False

    for token in tokens:
        match token.type:
            case token_type.sound:
                parsing_stack.append(sound_node(token.string))
            case token_type.sound_class:
                parsing_stack.append(sound_class_node(sound_classes[token.string]))
            case token_type.sound_class_number:
                number = int(token.string)
                class_node = parsing_stack.pop()
                parsing_stack.append(numbered_sound_class_node(class_node, number))

            case token_type.null_sound:
                parsing_stack.append(sound_node(""))
            case token_type.word_border:
                parsing_stack.append(word_border_node())

            case token_type.l_brace:
                parsing_stack.append(_marker.brace)
            case token_type.l_paren:
                parsing_stack.append(_marker.paren)

            case token_type.space if not finished_changes:
                parsing_stack.append(_marker.space)
            case token_type.space:
                pass # once changes are done, spaces are no longer meaningful
            case token_type.comma:
                parsing_stack.append(_marker.comma)

            case token_type.ellipsis:
                parsing_stack.append(repetition_node(parsing_stack.pop()))

            case token_type.r_brace:
                # parse a list of sound expressions, separated by commas
                # could restrict this further but there's no present need to
                expressions: list[expression_node] = []
                curr_expression: list[element_node] = []
                # take everything up to the open brace (and discard the brace, too)
                while (element := parsing_stack.pop()) is not _marker.brace:
                    if element is _marker.comma:
                        # reverse since we pulled things off in reverse
                        curr_expression.reverse()
                        expressions.append(expression_node(curr_expression))
                        curr_expression = []
                    elif element is _marker.space:
                        # intentionally skip spaces within braces
                        pass
                    else:
                        curr_expression.append(element)
                # make sure to include the leftmost expression as well
                curr_expression.reverse()
                expressions.append(expression_node(curr_expression))
                expressions.reverse()
                parsing_stack.append(sound_list_node(expressions))

            case token_type.r_paren:
                # parse one expression back to the open parenthesis
                expression: list[element_node] = []
                # take everything up to the open parenthesis (and discard it the paren)
                while (element := parsing_stack.pop()) is not _marker.paren:
                    expression.append(element)
                expression.reverse()
                parsing_stack.append(optional_node(expression_node(expression)))

            case token_type.arrow:
                # we've hit the end of one section but not of all of the changes
                parsing_stack.append(_parse_expression_list(parsing_stack))

            case token_type.neg_slash | token_type.pos_slash | token_type.eol if not finished_changes:
                # we've hit the end of the changes
                # get the last expression list
                parsing_stack.append(_parse_expression_list(parsing_stack))
                # then collect the lists into change_nodes
                changes: list[change_node] = []
                while parsing_stack:
                    curr_repl = parsing_stack.pop()
                    peek = parsing_stack[-1]
                    if isinstance(peek, expression_list_node):
                        changes.append(change_node(target = peek, replacement = curr_repl))
                    elif peek is _marker.stack_start:
                        # get rid of the start marker; it was only used to make peeking
                        # here and in _parse_expression_list easier
                        parsing_stack.pop()
                        break
                    else:
                        raise RuntimeError(f"Parsing stack in invalid state! Raw {type(peek)} left on stack during change collection.")
                else:
                    raise RuntimeError("Parsing stack in invalid state! Start marker was popped before changes finished parsing.")
                finished_changes = True
                changes.reverse()
                parsing_stack.append(changes)

                # add a marker to let the parser know later which kind of environment is currently being parsed
                if token.type is token_type.pos_slash:
                    parsing_stack.append(_marker.pos_env)
                elif token_type is token_type.neg_slash:
                    parsing_stack.append(_marker.neg_env)

            case token_type.underscore:
                expression = []
                while parsing_stack[-1] not in (_marker.pos_env, _marker.neg_env):
                    expression.append(parsing_stack.pop())
                expression.reverse()
                parsing_stack.append(expression_node(expression))

            case token_type.neg_slash | token_type.pos_slash:
                # we've hit the end of an environment
                # parse the post-environment expression and add it to the stack, then make an environment node
                expression = []
                while not isinstance(parsing_stack[-1], expression_node):
                    expression.append(parsing_stack.pop())
                expression.reverse()
                post_expression = expression_node(expression)
                pre_expression = parsing_stack.pop()
                is_positive = parsing_stack.pop() is _marker.pos_env
                parsing_stack.append(environment_node(pre_expression, post_expression, is_positive))

                # add a marker to let the parser know later which kind of environment it's parsing next
                if token.type is token_type.pos_slash:
                    parsing_stack.append(_marker.pos_env)
                elif token.type is token_type.neg_slash:
                    parsing_stack.append(_marker.neg_env)

            case token_type.eol:
                # we've hit the end of all things, and also know that the latest things are environments
                # as above, make the latest environment node
                # parse the post-environment expression and add it to the stack, then make an environment node
                expression = []
                while not isinstance(parsing_stack[-1], expression_node):
                    expression.append(parsing_stack.pop())
                expression.reverse()
                post_expression = expression_node(expression)
                pre_expression = parsing_stack.pop()
                is_positive = parsing_stack.pop() is _marker.pos_env
                parsing_stack.append(environment_node(pre_expression, post_expression, is_positive))

                # then collect all environment nodes into an environment list node
                pos_envs: list[environment_node] = []
                neg_envs: list[environment_node] = []
                while isinstance(parsing_stack[-1], environment_node):
                    env_node: environment_node = parsing_stack.pop()
                    if env_node.is_positive:
                        pos_envs.append(env_node)
                    else:
                        neg_envs.append(env_node)
                parsing_stack.append(pos_envs)
                parsing_stack.append(neg_envs)

            case _:
                raise NotImplementedError(f"Unrecognized token {token} encountered while parsing.")

    # finally, the parsing stack should now look like [list[changes], list[environment_node], list[environment_node]]
    return rule_node(*parsing_stack)


def _parse_expression_list(stack: list[ast_node | _marker]) -> expression_list_node:
    expressions: list[expression_node] = []
    curr_expression: list[element_node] = []
    while stack:
        peek = stack[-1]

        if peek is _marker.space:
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

        if peek is _marker.stack_start:
            # we're also done
            # add the current expression to the list if there's anything in it
            if curr_expression:
                curr_expression.reverse()
                expressions.append(expression_node(curr_expression))
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


