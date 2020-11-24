

class state:
    def __init__(self):
        self.transitions = {}

    def add_transition(self, match, target_state):
        self.transitions[match] = target_state

    def transition(self, c: str):
        # advance only if c is matched by a transition from the current state
        return self.transitions.get(c, self)


class fsm:
    def __init__(self, states = [], end_states = [], start_state = None):
        self.states = states
        self.end_states = end_states
        self.start_state = start_state
    
    def add_state(self, state, end_state = False):
        self.states.append(state)
        if end_state:
            self.add_end_state(state)
    
    def add_end_state(self, state):
        self.end_states.append(state)

    def set_start_state(self, state):
        if state not in self.states:
            self.add_state(state)
        self.start_state = state

    def check(self, input: str):
        "Returns whether this fsm accepts the input string."
        current_state = self.start_state
        
        for c in input:
            current_state = current_state.transition(c)

        if current_state in self.end_states:
            return True

        return False