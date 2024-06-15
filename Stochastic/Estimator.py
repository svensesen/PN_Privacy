import os
import sys

current_directory = os.path.dirname(os.path.realpath(__file__))
code_folder = os.path.abspath(os.path.join(current_directory, ".."))
sys.path.insert(1, code_folder)
from LKC.LKC import event_column, case_column

# WARNING: ALL OF THESE ESTIMATORS EDIT THE ORIGINAL PNP

def number_of_pairs(log, value1, value2):
    mask1 = log[event_column] == value1
    grouped = log.groupby(case_column)
    next_event = grouped[event_column].shift(-1)
    mask2 = next_event == value2
    return (mask1 & mask2).sum()

def number_of_label(log, label):
    return (log[event_column] == label).sum()


def frequency_estimator(pnp, log):
    result = dict(log[event_column].value_counts().iteritems())

    for transition in pnp.petri_net.transitions:
        transition.odds = result.get(transition.label, 1)

    return pnp


def activity_pair_estimator(pnp, log, left_hand = False):
    events = list(log[event_column].unique())
    result = {event: 0  for event in events}

    # First event in case
    for key, value in log.groupby(case_column).head(1)[event_column].value_counts().iteritems():
        result[key] += value

    # Last event in case
    for key, value in log.groupby(case_column).tail(1)[event_column].value_counts().iteritems():
        result[key] += value

    # Pairs
    if not left_hand: 

        # Drop the last of each trace to avoid counting double
        log_copy = log.drop(log.groupby(case_column).head(1).index)

        for main_transition in pnp.petri_net.transitions:
            cur_odds = result.get(main_transition.label, 0)

            outgoing_places = [arc.output for arc in main_transition.outgoing_arcs] 
            outgoing_transitions = [arc.output for arc in sum([place.outgoing_arcs for place in outgoing_places], [])]

            for other_transition in outgoing_transitions:
                cur_odds += number_of_pairs(log_copy, main_transition.label, other_transition.label)
            
            main_transition.odds = max(1, cur_odds)
    
    else:

        # Drop the first of each trace to avoid counting double
        log_copy = log.drop(log.groupby(case_column).tail(1).index)

        for main_transition in pnp.petri_net.transitions:
            cur_odds = result.get(main_transition.label, 0)

            incoming_places = [arc.input for arc in main_transition.incoming_arcs] 
            incoming_transitions = [arc.input for arc in sum([place.incoming_arcs for place in incoming_places], [])]

            for other_transition in incoming_transitions:
                cur_odds += number_of_pairs(log_copy, other_transition.label, main_transition.label)
            
            main_transition.odds = max(1, cur_odds)
    
    return pnp


def scaled_pair_estimator(pnp, log, left_hand = False):
    events = list(log[event_column].unique())
    result = {event: 0  for event in events}
    division = len(log)/len(pnp.petri_net.transitions)

    # First event in case
    for key, value in log.groupby(case_column).head(1)[event_column].value_counts().iteritems():
        result[key] += value

    # Last event in case
    for key, value in log.groupby(case_column).tail(1)[event_column].value_counts().iteritems():
        result[key] += value

    # Pairs
    if not left_hand: 

        # Drop the last of each trace to avoid counting double
        log_copy = log.drop(log.groupby(case_column).head(1).index)

        for main_transition in pnp.petri_net.transitions:
            cur_odds = result.get(main_transition.label, 0)

            outgoing_places = [arc.output for arc in main_transition.outgoing_arcs] 
            outgoing_transitions = [arc.output for arc in sum([place.outgoing_arcs for place in outgoing_places], [])]

            for other_transition in outgoing_transitions:
                cur_odds += number_of_pairs(log_copy, main_transition.label, other_transition.label)
            
            main_transition.odds = cur_odds/division if cur_odds != 0 else 1
    
    else:

        # Drop the first of each trace to avoid counting double
        log_copy = log.drop(log.groupby(case_column).tail(1).index)

        for main_transition in pnp.petri_net.transitions:
            cur_odds = result.get(main_transition.label, 0)

            incoming_places = [arc.input for arc in main_transition.incoming_arcs] 
            incoming_transitions = [arc.input for arc in sum([place.incoming_arcs for place in incoming_places], [])]

            for other_transition in incoming_transitions:
                cur_odds += number_of_pairs(log_copy, other_transition.label, main_transition.label)
            
            main_transition.odds = cur_odds/division if cur_odds != 0 else 1
    
    return pnp


def fork_estimator(pnp, log):
    pnp = frequency_estimator(pnp, log)

    for place in pnp.petri_net.places:
        if place.incoming_arcs:
            cur_weight = 0
            incoming_transitions = [arc.input for arc in place.incoming_arcs]
            outgoing_transitions = [arc.output for arc in place.outgoing_arcs]

            for incoming_transition in incoming_transitions:
                for outgoing_transition in outgoing_transitions:
                    cur_weight += number_of_pairs(log, incoming_transition.label, outgoing_transition.label)
            
            place.weight = max(1, cur_weight)

        else:
            place.weight = len(log[case_column].unique())
    
    for transition in pnp.petri_net.transitions:
        cur_odds = 0

        for place in [arc.input for arc in transition.incoming_arcs]:
            cur_odds += place.weight*(transition.odds/sum(arc.output.odds for arc in place.outgoing_arcs))
        
        transition.odds = cur_odds

    return pnp    
