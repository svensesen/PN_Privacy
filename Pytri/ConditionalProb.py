from Dummy import DummyStopEvent

# Value used to catch rounding error close to 0
epsilon = 0.1**12

# Create a DFA requiring a single label to have occurred
def create_single_DFA(label, other_labels):
    dfa = DFA()
    dfa.initial_state = dfa.add_state("q0")
    dfa.final_states.append(dfa.add_state("q1"))

    DFA_Arc(dfa.identifier_to_state["q0"], dfa.identifier_to_state["q1"], label)
    DFA_Arc(dfa.identifier_to_state["q1"], dfa.identifier_to_state["q1"], label)

    for other_label in [sub_label for sub_label in other_labels if sub_label != label]:
        DFA_Arc(dfa.identifier_to_state["q0"], dfa.identifier_to_state["q0"], other_label)
        DFA_Arc(dfa.identifier_to_state["q1"], dfa.identifier_to_state["q1"], other_label)
    
    return dfa


state_number = 0

# Create a DFA requiring a list of labels to have occurred
def create_multiple_DFA(labels, other_labels):
    global state_number

    dfa = DFA()
    dfa.initial_state = dfa.add_state("qi")

    final_state = dfa.add_state("qf")
    for label in labels + list(other_labels):
        DFA_Arc(final_state, final_state, label)
    dfa.final_states.append(final_state)

    state_number = 0
    create_multiple_DFA_iterative(dfa, dfa.initial_state, labels, list(other_labels))

    return dfa


def create_multiple_DFA_iterative(dfa, last_state, labels_left, other_labels):
    global state_number
    for label in other_labels:
         DFA_Arc(last_state, last_state, label)

    for label in labels_left:
        if len(labels_left) == 1:
            DFA_Arc(last_state, dfa.final_states[0], label)

        else:
            state_number += 1
            new_state = dfa.add_state(f"q{state_number}")

            DFA_Arc(last_state, new_state, label)

            new_labels_left = labels_left.copy()
            new_labels_left.remove(label)
            create_multiple_DFA_iterative(dfa, new_state, new_labels_left, other_labels + [label])
        

# Note: changes the DFA
def add_sensitive_to_background(sensitive_label, background_DFA):
    new_final_states = []
    
    og_states = background_DFA.states.copy()

    # Create a "double" for each of the sensitive has happened states
    for state in og_states:
        sensitive_state_label = f"{state.identifier}+{sensitive_label}"

        new_state = background_DFA.add_state(sensitive_state_label)

        if state in background_DFA.final_states:
            new_final_states.append(new_state)

    # Set the new final states
    background_DFA.final_states = new_final_states

    # Assigns all arcs
    for state in og_states:

        og_arcs = state.outgoing_arcs.copy()
        for arc in og_arcs:

            # Add arc to the new side
            DFA_Arc(background_DFA.identifier_to_state[f"{state.identifier}+{sensitive_label}"], background_DFA.identifier_to_state[f"{arc.output.identifier}+{sensitive_label}"], arc.label)

            # Change the outgoing part of the arc to new side (if needed)
            if arc.label == sensitive_label:
                output_identifier = arc.output.identifier

                arc.destroy()
                del arc

                DFA_Arc(state, background_DFA.identifier_to_state[f"{output_identifier}+{sensitive_label}"], sensitive_label)


    return background_DFA


# The probability of a label occurring in the reachability graph
def prob_label(reachability_graph, label):
    all_labels = set(arc.transition.label for arc in chain.from_iterable(state.outgoing_arcs for state in reachability_graph.states))

    label_DFA = create_multiple_DFA([label], all_labels-set([label]))
    prl = verify_prob(reachability_graph, label_DFA)

    return prl


# The probability of a label occurring in the reachability graph given a list of background labels
def conditional_prob(reachability_graph, label, background_labels):
    if type(background_labels) != list: background_labels = [background_labels]

    all_labels = set(arc.transition.label for arc in chain.from_iterable(state.outgoing_arcs for state in reachability_graph.states))

    # Compute a background dfa for the given background labels
    background_DFA = create_multiple_DFA(background_labels, all_labels-set(background_labels))

    # Calculate pr(b)
    prb = verify_prob(reachability_graph, deepcopy(background_DFA))

    # Calculate pr(s+b)
    full_DFA = add_sensitive_to_background(label, deepcopy(background_DFA))
    prlb = verify_prob(reachability_graph, full_DFA)

    return prlb/prb if prb != 0 else 0


# Calculate the cc as it is in the paper for the given reachability_graph, L and sensitive events
# Requires the upper_cc and lower_cc from 'lower' layers
# This also computes the maximum C for the LKC
def paper_cc_model_all(reachability_graph, L, sensitive_events, previous_upper_cc, previous_lower_cc, stop_event = DummyStopEvent()):
    if type(sensitive_events) == str: sensitive_events = [sensitive_events]

    upper_cc = previous_upper_cc
    lower_cc = previous_lower_cc

    all_labels = set(arc.transition.label for arc in chain.from_iterable(state.outgoing_arcs for state in reachability_graph.states))

    backgrounds = list(combinations(all_labels-set(sensitive_events)-{'None', 'tau'}, L))

    true_sensitive_events = []
    sensitive_events_odds = {}

    for sensitive_event in sensitive_events:

        # Calculate pr(s)
        if stop_event.is_set(): return None
        sensitive_DFA = create_multiple_DFA([sensitive_event], all_labels-set([sensitive_event]))
        if stop_event.is_set():
            # sensitive_DFA.destroy()
            # del sensitive_DFA 
            return None

        prs = verify_prob(reachability_graph, sensitive_DFA, True)
        # sensitive_DFA.destroy()
        # del sensitive_DFA
        
        # This happens if the model has no deadlocks
        if prs == None:
            return None

        if prs > epsilon:
            true_sensitive_events.append(sensitive_event)
            sensitive_events_odds[sensitive_event] = prs
        
    C = 0 

    for background in backgrounds:

        # Compute a background dfa for the given background labels
        if stop_event.is_set(): return None
        background_DFA = create_multiple_DFA(list(background), all_labels-set(background))
        if stop_event.is_set(): 
            # background_DFA .destroy()
            # del background_DFA
            return None
        prb = verify_prob(reachability_graph, deepcopy(background_DFA), True)
       
        
        # If the background can occur
        if prb > epsilon:
            lower_cc += 1
            background_values = [0]

            for sensitive_event in true_sensitive_events:
                prs = sensitive_events_odds[sensitive_event]

                # Calculate pr(s+b)
                if stop_event.is_set(): return None
                full_DFA = add_sensitive_to_background(sensitive_event, deepcopy(background_DFA))
                if stop_event.is_set(): 
                    # background_DFA .destroy()
                    # del background_DFA 
                    # full_DFA.destroy()
                    # del full_DFA
                    return None
                prsb = verify_prob(reachability_graph, full_DFA, True)
                # full_DFA.destroy()
                # del full_DFA

                C = max(prsb/prb, C) 

                RS_1 = max(prsb/prb - prs, 0) # The odds change, or 0
                if RS_1 < epsilon: RS_1 = 0
                RS_2 = prb/prs # Background odds divided by sensitive odds
                RS = (RS_1 * RS_2)**2 # Make it quadratic
                background_values.append(RS)

            upper_cc += max(background_values)

        # background_DFA .destroy()
        # del background_DFA 

    return upper_cc, lower_cc, C

from DFA import DFA
from Arc import DFA_Arc
from Functions import verify_prob

from copy import deepcopy
from itertools import chain, combinations



if __name__ == "__main__":
    # from DFA import DFA
    # from PetriNet import PNP

    dfa = create_multiple_DFA(["A", "B", "C"], ["X", "Y", "Z"])
    for state in dfa.states:
        print(state)
        print(state.outgoing_arcs)
        print("")
    # dfa = DFA.read_text("Testing Graphs\\DFA T.txt")
    # pnp = PNP.read_text("Testing Graphs\\PNP T.txt")

    # rg = pnp.create_reachability_graph()
    # print("probability for e given this background info")
    # result = conditional_probability(rg, "e", dfa)
    # print(f"pr(b): {result[0]}, pr(s+b): {result[1]}, pr(s): {result[2]}")


# Archieved functions kept in case i used them in some code that is still around
# # Note: changes the DFA
# def conditional_probability(reachability_graph, sensitive_label, background_DFA):
#     # Calculate pr(b)
#     prb = verify_prob(reachability_graph, deepcopy(background_DFA))

#     # Calculate pr(s+b)
#     full_DFA = add_sensitive_to_background(sensitive_label, deepcopy(background_DFA))
#     prsb = verify_prob(reachability_graph, full_DFA)

#     # Calculate pr(s)
#     sensitive_DFA = create_single_DFA(sensitive_label, background_DFA.labels)
#     prs = verify_prob(reachability_graph, sensitive_DFA)

#     return prb, prsb, prs


# # The three odds for a sensitive label given background labels
# def odds_of_sensitive_given_background(reachability_graph, sensitive_label, background_labels, all_labels = None):
#     # Get all the labels in the reachability graph
#     if all_labels == None:
#         all_labels = set(arc.transition.label for arc in chain.from_iterable(state.outgoing_arcs for state in reachability_graph.states))

#     # Compute a background dfa for the given background labels
#     background_DFA = create_multiple_DFA(background_labels, all_labels-set(background_labels))

#     # Calculate pr(b)
#     prb = verify_prob(reachability_graph, deepcopy(background_DFA))

#     # Calculate pr(s+b)
#     full_DFA = add_sensitive_to_background(sensitive_label, deepcopy(background_DFA))
#     prsb = verify_prob(reachability_graph, full_DFA)

#     # Calculate pr(s)
#     sensitive_DFA = create_multiple_DFA([sensitive_label], all_labels-set([sensitive_label]))
#     prs = verify_prob(reachability_graph, sensitive_DFA)

#     return prb, prsb, prs

