class DFA:
    def __init__(self):
        self.states = []
        self.identifier_to_state = {}
        self.initial_state = None
        self.final_states = []
        self.labels = []

    # Creates a DFA object from a txt file (according to a custom format)
    @classmethod
    def read_text(cls, path):
        dfa = cls()
        dfa_text_parts = open(path, 'r').readlines()
        dfa_text_arcs = []
        dfa_text_final = []

        # For each of the entries
        for part in dfa_text_parts:
            tokens = part.split() + [""]
            type = tokens[0]

            # If its an arc, pass it along
            if type == "a":
                dfa_text_arcs.append(part)
            
            elif type == "l":
                dfa.labels = part.split()[1:]

            # If its the initial marking
            elif type == "i":
                dfa_text_initial_place = part
            
            # If its a final marking
            elif type == "f":
                dfa_text_final.append(part)

            # Else create the state
            elif type == "s":
                identifier = tokens[1]
                dfa.add_state(identifier)

        # Add all the arcs
        for part in dfa_text_arcs:
            tokens = part.split() + ["1"]
            input_id = tokens[1]
            output_id = tokens[2]
            label = tokens[3]

            input_element = dfa.identifier_to_state[input_id]
            output_element = dfa.identifier_to_state[output_id]
            
            # If it is a connection of all labels
            if label == "+":
                for sub_label in dfa.labels:
                    DFA_Arc(input_element, output_element, sub_label)
            
            # If it is a connection of all except certain labels
            elif label[0] == "-":
                non_labels = label.split("-")
                for sub_label in dfa.labels:
                    if sub_label not in non_labels:
                        DFA_Arc(input_element, output_element, sub_label)
            
            # If it is a normal connection
            else:
                DFA_Arc(input_element, output_element, label)
        
        # Add initial state
        dfa.initial_state = dfa.identifier_to_state[dfa_text_initial_place.split()[1]]

        # Add final states
        dfa.final_states = [dfa.identifier_to_state[part.split()[1]] for part in dfa_text_final]

        return dfa

    # Creates a new state and does all the bookkeeping
    def add_state(self, _identifier):
        state = DFA_State(_identifier)
        self.identifier_to_state[_identifier] = state
        self.states.append(state)
        return state

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
        del self.final_states 
        del self.labels 
        
    
from Arc import DFA_Arc
from Element import DFA_State