
from fsm import *

illegal_start_chars = ["*", "+"]

string_rules = ["ab*", "+r", "á+b"]


def validate_rule(rule: str):
    if any(rule.startswith(char) for char in illegal_start_chars):
        return False
    return True


def match_rule(rule: str) -> fsm:

    if not validate_rule(rule):
        return fsm() # silently exit for now because I don't want to do error handling rn

    match_machine = fsm()

    previous_state = match_machine.get_start_state()

    for c in rule:
        # TODO: put all of these into their own functions
        if c == "*":
            previous_state.add_transition(prev_c, previous_state) # type: ignore

        elif c == "+":
            state_1 = state()
            state_2 = state()

            state_1.add_transition(prev_c, state_2) # type: ignore
            state_2.add_transition(prev_c, state_2) # type: ignore

            previous_state = state_2

        else:
            new_state = state()
            match_machine.add_state(new_state)

            previous_state.add_transition(c, new_state)
        
            previous_state = new_state
        
        prev_c = c
    
    match_machine.add_end_state(previous_state)

    return match_machine


words = ["abbb", "ábá", "ááb", "rob", "a"]

for rule in string_rules:

    machine = match_rule(rule)

    for word in words:
        print(", ".join([word, rule, str(machine.check(word))]))