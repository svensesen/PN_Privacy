import re
import os
from collections import deque, defaultdict
import xml.etree.ElementTree as ET
from Dummy import DummyStopEvent

current_directory = os.path.dirname(os.path.realpath(__file__))
code_folder = os.path.abspath(os.path.join(current_directory, ".."))

class NoInitialMarkingError(Exception):
    pass

class PNP:
    def __init__(self):
        self.petri_net = None
        self.initial_state = None
        self.deadlock_states = []

    
    # Creates a PNP object from a txt file (according to a custom format)
    @classmethod
    def read_text(cls, path):
        pnp = cls()
        pnp.petri_net = PetriNet()
        with open(path, 'r', encoding='utf-8') as f:
            petri_net_text_parts = f.readlines()

        petri_net_text_arcs = []
        pnp_text_deadlock_markings = []

        # For each of the entries
        for part in petri_net_text_parts:
            tokens = part.split() + [""]
            type = tokens[0]

            # If its an arc, pass it along
            if type == "a":
                petri_net_text_arcs.append(part)
            
            # If its the initial marking
            elif type == "i":
                pnp_text_initial_marking = part
            
            # If its a deadlock marking
            elif type == "d":
                pnp_text_deadlock_markings.append(part)

            # Else create the element
            elif type in ["p", "t"]:
                identifier = tokens[1].replace('\u2588', ' ')
                
                if type == "p":
                    pnp.petri_net.add_place(identifier)

                elif type == "t":
                    label = re.sub(r'\(.*\)', '', identifier)
                    odds = float(tokens[2])
                    pnp.petri_net.add_transition(identifier, label, odds)

        # Add all the arcs
        for part in petri_net_text_arcs:
            tokens = part.split() + ["1"]
            input_id = tokens[1].replace('\u2588', ' ')
            output_id = tokens[2].replace('\u2588', ' ')

            input_element = pnp.petri_net.identifier_to_element[input_id]
            output_element = pnp.petri_net.identifier_to_element[output_id]

            PetriArc(input_element, output_element)
        
        # Add initial state
        if not pnp_text_initial_marking:
            raise NoInitialMarkingError("No initial marking present")
        pnp.initial_state = RG_State.state_from_part(pnp_text_initial_marking, pnp.petri_net)

        # Add deadlock states
        if pnp_text_deadlock_markings == []:
            pnp.deadlock_states = None
        else:
            pnp.deadlock_states = [RG_State.state_from_part(part, pnp.petri_net) for part in pnp_text_deadlock_markings]

        return pnp


    # Creates a txt file for the PNP (according to a custom format)
    def write_text(self, path):
        with open(path, 'w') as f:
            
            f.write("# Places")
            for place in self.petri_net.places:
                f.write(f"\np {place.identifier}")
            
            f.write("\n\n# Transitions")
            for transition in self.petri_net.transitions:
                f.write(f"\nt {transition.identifier} {transition.odds}")
            
            f.write("\n\n# Arcs")
            for place in self.petri_net.places:
                for arc in place.outgoing_arcs:
                    f.write(f"\na {arc.input.identifier} {arc.output.identifier}")
            
            for transition in self.petri_net.transitions:
                for arc in transition.outgoing_arcs:
                    f.write(f"\na {arc.input.identifier} {arc.output.identifier}")

            f.write(f"\n\n# Initial State\ni{''.join(f' {key.identifier} {value}' for key,value in self.initial_state.tokens_per_place.items())}")
        
            # We let Pytri figure it out when it makes a reachability graph
            f.write("\n\n# Deadlock States Not Recorded")
    

    # Creates a pnml file from the PNP (note, weights are not copied)
    def write_pnml(self, path):
        tree = ET.parse(os.path.join(code_folder, "models/empty.pnml"))
        pnml_root = tree.getroot()
        net = pnml_root.find("net")
        page = net.find("page")
        
        arc_id = 10000
        for place in self.petri_net.places:
            place_element = ET.SubElement(page, "place", id=str(place.identifier))
            if place in self.initial_state.tokens_per_place.keys():
                place_initial_marking = ET.SubElement(place_element , "initialMarking")
                ET.SubElement(place_initial_marking, "text").text = str(self.initial_state.tokens_per_place[place])


            for arc in place.outgoing_arcs:
                ET.SubElement(page, "arc", id=f"a{str(arc_id)}", source=arc.input.identifier, target=arc.output.identifier)
                arc_id += 1
        
        for transition in self.petri_net.transitions:
            transition_element = ET.SubElement(page, "transition", id=transition.identifier)
            transition_name = ET.SubElement( transition_element , "name")
            ET.SubElement(transition_name, "text").text = transition.label

            for arc in transition.outgoing_arcs:
                ET.SubElement(page, "arc", id=f"a{str(arc_id)}", source=arc.input.identifier, target=arc.output.identifier)
                arc_id += 1
        
        final_markings = ET.SubElement(net, "finalmarkings")
        if self.deadlock_states != None:
            for deadlock_state in self.deadlock_states:
                marking = ET.SubElement(final_markings, "marking")
                for place in deadlock_state.tokens_per_place.keys():
                    place_element = ET.SubElement(marking, "place", idref=place.identifier)
                    ET.SubElement(place_element, "text").text = str(deadlock_state.tokens_per_place[place])

        indent(pnml_root)
        with open(path, "w") as f:
            xml_str = ET.tostring(tree.getroot(), encoding='utf-8', method='xml').decode()
            xml_with_declaration = "<?xml version='1.0' encoding='UTF-8'?>\n" + xml_str
            f.write(xml_with_declaration)

        

    # Output the reachability graph of the pnp
    def create_reachability_graph(self, stop_event = DummyStopEvent()):

        # The reachability graph being created
        reachability_graph = ReachabilityGraph()

        # Adds the pnp initial state to the reachability graph
        reachability_graph.append_initial_state(self.initial_state)

        if self.deadlock_states != None:
            for state in self.deadlock_states:
                reachability_graph.append_deadlock_state(state)

        # The transitions enables for each state, now only has the initial state
        transitions = {arc.output for place in self.initial_state.tokens_per_place if self.initial_state.tokens_per_place[place] > 0 for arc in place.outgoing_arcs if all(self.initial_state.tokens_per_place.get(predecessor_arc.input, 0) > 0 for predecessor_arc in arc.output.incoming_arcs)}
        enabled_transitions = {self.initial_state: transitions}

        # This queue will have every newly added state added to it
        queue = deque([self.initial_state])

        # While there are still states for whom the predecessors are not yet added
        while queue:
            if stop_event.is_set():
                return None
            
            current_state = queue.popleft()

            # The sum of all transition odds for this state to calculate the state-to-state odds
            sum_transition_odds = sum([transition.odds for transition in enabled_transitions[current_state]])

            # For each of the transitions that may be activated from this current state
            for transition in enabled_transitions[current_state]:
                new_tokens_per_place = current_state.tokens_per_place.copy()
                new_enabled_transitions =  enabled_transitions[current_state].copy()

                # Takes a token from the incoming places
                for place in [arc.input for arc in transition.incoming_arcs]:
                    new_tokens_per_place[place] -= 1
                    
                    # Remove any transitions that are now no longer possible
                    if new_tokens_per_place[place] == 0:
                        new_enabled_transitions -= {arc.output for arc in place.outgoing_arcs}

                # Gives a token to the outgoing place
                for place in [arc.output for arc in transition.outgoing_arcs]:
                    new_tokens_per_place[place] += 1

                    # Add all transition that are now possible
                    if new_tokens_per_place[place] == 1:
                        new_enabled_transitions = new_enabled_transitions | {arc.output for arc in place.outgoing_arcs if all(new_tokens_per_place[predecessor_arc.input] > 0 for predecessor_arc in arc.output.incoming_arcs)}
                        # CIRCULAR

                # Deletes places with zero tokens from the dictionary
                keys_to_delete = []
                for state in new_tokens_per_place:
                    if new_tokens_per_place[state] == 0:
                        keys_to_delete.append(state)
                
                for state in keys_to_delete:
                    del new_tokens_per_place[state]

                # Sort so the ordering doesn't matter
                new_tokens_per_place = defaultdict(lambda: 0, dict(sorted(new_tokens_per_place.items()))) # CIRCULAR

                # Either get the relevant state if it exists, or otherwise create it
                new_state = reachability_graph.ttp_to_state(new_tokens_per_place)
                if not new_state:         
                    new_state = reachability_graph.add_state(new_tokens_per_place)
                    enabled_transitions[new_state] = new_enabled_transitions
                    queue.append(new_state)
                
                # Adds an arc corresponding to the just triggered transition 
                if sum_transition_odds == 0:
                    GraphArc(current_state, new_state, transition.odds, transition)
                else:
                    GraphArc(current_state, new_state, transition.odds/sum_transition_odds, transition) # CIRCULAR
        
        for state in reachability_graph.states:
            if state.outgoing_arcs == []:
                reachability_graph.deadlock_states.append(state)
        
        try: del new_enabled_transitions
        except: pass
        
        return reachability_graph
    
    # Output the traces and their odds of the pnp
    def get_traces(self):
        
        # Dictionary of traces and their odds
        traces = defaultdict(lambda: 0)

        # The transitions enables for this state, now only has the initial state
        transitions = {arc.output for place in self.initial_state.tokens_per_place if self.initial_state.tokens_per_place[place] > 0 for arc in place.outgoing_arcs if all(self.initial_state.tokens_per_place.get(predecessor_arc.input, 0) > 0 for predecessor_arc in arc.output.incoming_arcs)}
        
        # Contains the current version the trace, the odds, the tokens per place and the active transitions
        starting_version_trace = ("", 1, self.initial_state.tokens_per_place, transitions)

        # This queue will have every newly added state added to it
        queue = deque([starting_version_trace])

        # While there are still versions for whom the predecessors are not yet added
        while queue:
            current_version = queue.popleft()

            # For each of the transitions that may be activated from this current state
            for transition in current_version[3]:
                new_tokens_per_place = current_version[2].copy()
                new_enabled_transitions = current_version[3].copy()

                # Takes a token from the incoming places
                for place in [arc.input for arc in transition.incoming_arcs]:
                    new_tokens_per_place[place] -= 1
                    
                    # Remove any transitions that are now no longer possible
                    if new_tokens_per_place[place] == 0:
                        new_enabled_transitions -= {arc.output for arc in place.outgoing_arcs}

                # Gives a token to the outgoing place
                for place in [arc.output for arc in transition.outgoing_arcs]:
                    new_tokens_per_place[place] += 1

                    # Add all transition that are now possible
                    if new_tokens_per_place[place] == 1:
                        new_enabled_transitions = new_enabled_transitions | {arc.output for arc in place.outgoing_arcs if all(new_tokens_per_place[predecessor_arc.input] > 0 for predecessor_arc in arc.output.incoming_arcs)}

                # Deletes places with zero tokens from the dictionary
                keys_to_delete = []
                for state in new_tokens_per_place:
                    if new_tokens_per_place[state] == 0:
                        keys_to_delete.append(state)
                
                for state in keys_to_delete:
                    del new_tokens_per_place[state]

                # Sort so the ordering doesn't matter
                new_tokens_per_place = defaultdict(lambda: 0, dict(sorted(new_tokens_per_place.items())))

                new_trace = f"{current_version[0]};{transition.label}"
                # append the new version to the queue if there are transitions, otherwise finish
                if new_enabled_transitions: 
                    queue.append((new_trace, current_version[1]*transition.odds, new_tokens_per_place, new_enabled_transitions))

                else:
                    traces[new_trace] += current_version[1]*transition.odds

        return [(trace, odds) for trace, odds in traces.items()]

    
class PetriNet:
    def __init__(self):
        self.places = []
        self.transitions = []
        self.identifier_to_element = {}
        self.label_to_elements = {}

    # Creates a new places and does all the bookkeeping
    def add_place(self, _identifier):
        place = Place(_identifier)
        self.__add_element(place, _identifier, _identifier)
        self.places.append(place)

        return place

    # Creates a new transition and does all the bookkeeping
    def add_transition(self, _identifier, _label, _odds):
        transition = Transition(_identifier, _label, _odds)
        self.__add_element(transition, _identifier, _label)
        self.transitions.append(transition)

        return transition

    # Private function which houses some of the element creation bookkeeping
    def __add_element(self, element, _identifier, _label):
        self.identifier_to_element[_identifier] = element

        if _label in self.label_to_elements:
            self.label_to_elements[_label].append(element)
        else:
            self.label_to_elements[_label] = [element]
    

    def destroy(self):
        for place in self.places:
            for arc in place.incoming_arcs:
                arc.destroy()
                del arc
            for arc in place.outgoing_arcs:
                arc.destroy()
                del arc
            place.destroy()
            del place
        
        del self.states
        del self.identifier_to_state 
        del self.initial_state 
        del self.final_states
        del self.labels 


def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


from Element import Place, Transition, RG_State
from Arc import PetriArc, GraphArc
from ReachabilityGraph import ReachabilityGraph