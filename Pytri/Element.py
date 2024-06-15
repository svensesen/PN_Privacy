class Element:
    def __init__(self, _identifier):
        self.identifier = _identifier

        self.outgoing_arcs = []
        self.incoming_arcs = []

    def __repr__(self):
        return f"E){self.identifier}"
    
    def __hash__(self):
        return int.from_bytes(self.identifier.encode(), "little")
    
    def __eq__(self, other):
        return self.identifier == other.identifier

    def __gt__(self, other):
        return self.identifier > other.identifier
    
    def __lt__(self, other):
        return self.identifier < other.identifier
    
    def destroy(self):
        for arc in self.outgoing_arcs:
            arc.destroy()
            del arc
        for arc in self.incoming_arcs:
            arc.destroy()
            del arc
        del self.outgoing_arcs
        del self.incoming_arcs


class Place(Element):
    def __init__(self, _identifier):
        super().__init__(_identifier)
    
    def __repr__(self):
        return f"P){self.identifier}"


class Transition(Element):
    def __init__(self, _identifier, _label, _odds):
        super().__init__(_identifier)
        self.label = _label
        self.odds = _odds

    def __repr__(self):
        return f"T){self.identifier}){self.odds}"


# For the DFA
class DFA_State(Element):
    def __init__(self, _identifier):
        super().__init__(_identifier)
        self.label_to_incoming_arc = {}
        self.label_to_outgoing_arc = {}
    
    def __repr__(self):
        return f"DS){self.identifier}"
    
    def destroy(self):
        super().destroy()
        del self.label_to_incoming_arc
        del self.label_to_outgoing_arc


# For the reachability graph
# Also called marking
class RG_State(Element):
    def __init__(self, _identifier, _tokens_per_place):
        super().__init__(_identifier)
        self.tokens_per_place = _tokens_per_place

    def __repr__(self):
        return f"RS){self.identifier}"
    
    # Helper function to create the identifiers
    @staticmethod
    def tpp_to_id(tokens_per_place):
        return ";".join(f"{key}:{tokens_per_place[key]}" for key in tokens_per_place)

    @classmethod
    def state_from_part(cls, part, petri_net):
        tokens = part.split()[1:]
        tokens_per_place = defaultdict(lambda: 0)

        for i in range(int(len(tokens)/2)):
            tokens_per_place[petri_net.identifier_to_element[tokens[i*2]]] = int(tokens[i*2 + 1])
 
        return cls(RG_State.tpp_to_id(tokens_per_place), tokens_per_place)

    def destroy(self):
        del self.tokens_per_place 
        super().destroy()
    

from collections import defaultdict
