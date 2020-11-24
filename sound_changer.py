
from fsm import *

string_rule = "ab*"

def match_rule(rule: str) -> fsm:

    match_machine = fsm()

    new_state = previous_state = None

    for c in rule:

        if c == "*":
            previous_state.add_transition(prev_c, previous_state)

        else:
            new_state = state()
            match_machine.add_state(new_state)

            if previous_state: 
                previous_state.add_transition(c, new_state)
            
            else:
                match_machine.set_start_state(new_state)
        
            previous_state = new_state
        
        prev_c = c
    
    match_machine.add_end_state(previous_state)

    return match_machine

fsm = match_rule(string_rule)

print(fsm.check("abbb"))