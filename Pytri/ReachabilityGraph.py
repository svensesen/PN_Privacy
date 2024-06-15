# This is a labelled transitions system
class ReachabilityGraph:
    def __init__(self):
        self.states = []
        self.identifier_to_state = defaultdict(lambda: None)
        self.initial_state = None
        self.deadlock_states = [] # Also called accepting states
    
    # Add creates and adds a state
    # Append adds and existing state
    def add_initial_state(self, _initial_tokens_per_place):
        self.initial_state = self.add_state(_initial_tokens_per_place)
        return self.initial_state

    def add_deadlock_state(self, _tokens_per_place):
        state = self.add_state(_tokens_per_place)
        self.deadlock_states.append(state)
        return state

    def add_state(self, _tokens_per_place):
        state = RG_State(RG_State.tpp_to_id(_tokens_per_place), _tokens_per_place)
        self.states.append(state)
        self.identifier_to_state[state.identifier] = state
        return state

    def ttp_to_state(self, tokens_per_place):
        return self.identifier_to_state[RG_State.tpp_to_id(tokens_per_place)]
    
    def append_initial_state(self, state):
        self.initial_state = state
        self.append_state(state)

    def append_deadlock_state(self, state):
        self.deadlock_states.append(state)
        self.append_state(state)

    def append_state(self, state):
        self.states.append(state)
        self.identifier_to_state[state.identifier] = state
    
    def destroy(self):
        for state in self.states:
            for arc in state.incoming_arcs:
                arc.destroy()
                del arc
            for arc in state.outgoing_arcs:
                arc.destroy()
                del arc
            state.destroy()
            del state
        
        del self.states
        del self.identifier_to_state 
        del self.initial_state 
        del self.deadlock_states 

from Element import RG_State
from collections import defaultdict
