from itertools import combinations
import json
import numpy as np

event_column = "concept:name"
case_column = "case:concept:name"


# Get the highest K and lowest C that may be satisfied for a given L
def max_LKC(L, log, sensitive_events):
    # All non-sensitive events
    quasi_events = list(set(log[event_column]) - set(sensitive_events))

    # For each sensitive event the cases belonging to it
    reverse_assignment = []
    for sensitive_event in sensitive_events:
        applicable_cases = set(log[log[event_column] == sensitive_event][case_column])
        reverse_assignment.append(applicable_cases)
    
    # Check K and C by creating background sets progressively
    return sub_max_LKC(log, [quasi_events]*L, reverse_assignment)


# Function used by max_LKC
def sub_max_LKC(cur_log, divisions_left, reverse_assignment):
    K = float('inf')
    C = 0
    
    # If the background is fully filtered for
    if not divisions_left:
        applicable_cases = set(cur_log[case_column])
        if len(applicable_cases) > 0:
            # K is the number of cases which have this background
            K = len(applicable_cases)
            
            for sensitive_event_cases in reverse_assignment:
                number_shared_cases = len(set(sensitive_event_cases).intersection(applicable_cases))
                if number_shared_cases > 0:
                    # C is the highest occurring sensitive set percentage for this background
                    C = max(number_shared_cases/len(applicable_cases), C)

    # Filter another background layer
    else:
        cur_background = divisions_left[0]
        new_divisions_left = divisions_left[1:]

        for i in range(len(cur_background)):
            new_log = filter_cases(cur_log, cur_background[i])
            calc_K, calc_C = sub_max_LKC(new_log, [x[i+1:] for x in new_divisions_left], reverse_assignment)

            K = min(calc_K, K)
            C = max(calc_C, C) 
    
    return K, C



# Returns the log with only the cases of the given event
def filter_cases(log, event):
    return log[log[case_column].isin(log[log[event_column] == event][case_column])]



# Probability of events
def pr_e(log, events):
    number_applicable_cases = len(set(log[log[event_column].isin(events)][case_column]))
    return number_applicable_cases/len(set(log[case_column]))


# Probability of events given a background of events
def pr_e_b(log, events, background):
    return pr_e(log, background.union(events))/pr_e(log, background)


# Probability change of events from the default odds when background is know 
def pr_e_b_c(log, events, background, absolute = False, percentage = False):
    event_odds = pr_e(log, events)
    odds_change = pr_e_b(log, events, background) - event_odds
    return (abs(odds_change) if absolute else odds_change)/ (event_odds if percentage else 1)


# Calculates for each combination of event how many times it occurs
def calculate_case_numbers(log, L, save_path):
    events = list(log[event_column].value_counts().index)
    events.reverse()
    info = iterative_calculate_case_numbers(log, [events]*L, ListIntegerMap(L), [], L)
    info.save_to_file(save_path)

def iterative_calculate_case_numbers(cur_log, divisions_left, info, path, L):
    if divisions_left:
        cur_background = divisions_left[0]
        new_divisions_left = divisions_left[1:]

        for i in range(len(cur_background)):
            new_log = filter_cases(cur_log, cur_background[i])
            info = iterative_calculate_case_numbers(new_log, [x[i+1:] for x in new_divisions_left], info, path + [cur_background[i]], L)
        
    info[path] = len(set(cur_log[case_column]))

    return info


# Different scaling functions
def basic(x): return x
def quadratic(x): return pow(x, 2)
def cubic(x): return pow(x, 3)


# Maps lists to integers
# The ordering of the lists do not matter
class ListIntegerMap:
    def __init__(self, _set_size):
        self.set_size = _set_size
        self.events = set()
        self.list_to_int = {}
    

    def __setitem__(self, key, value): 
        if type(key) == str: key = [key]
        elif type(key) != list: key = list(key)
        if type(value) != int: value = int(value)
        self.add_mapping(key, value)

    # Adds a list to integer mapping to the dictionary
    def add_mapping(self, list, integer):
        if len(list) < self.set_size:
            list += ["None"]*(self.set_size - len(list))

        list_tuple = tuple(sorted(list))  
        self.list_to_int[list_tuple] = integer
        self.events.update(list)
    

    def __getitem__(self, key):
        return self.get_integer(key)
    
    # Gets the integer for a given list
    def get_integer(self, list):
        list_tuple = tuple(sorted(list + ["None"]*(self.set_size - len(list))))
        return self.list_to_int.get(list_tuple, 0)


    def save_to_file(self, filename):
        data = {"list_to_int": {str(key): value for key, value in self.list_to_int.items()},
                "set_size": self.set_size, "events": str(self.events)}
        
        with open(filename, 'w') as file:
            json.dump(data, file)


    @staticmethod
    def load_from_file(filename):
        map = ListIntegerMap(0)
        with open(filename, 'r') as file:
            data = json.load(file)
            map.list_to_int = {eval(key): value for key, value in data["list_to_int"].items()}
            map.set_size = data["set_size"]
            map.events = eval(data["events"])
        
        return map


    # Probability on events
    def pr_e(self, events):
        return self[events]/self[[]]

    # Probability on events given a background
    def pr_e_b(self, events, background):
        if self[background] == 0: return 0
        else: return self[background + events]/self[background]

    # Probability change on event given a background
    def pr_e_b_c(self, events, background, percentage = False, absolute = False):
        event_odds = self.pr_e(events)
        odds_change = self.pr_e_b(events, background) - event_odds
        return (abs(odds_change) if absolute else odds_change)/(event_odds if percentage else 1)

    # Gets the highest K and C that may be satisfied for a given L
    # Every event that is not a sensitive event is a quasi-identifier
    def max_LKC(self, L, sensitive_events):
        if L+1 > self.set_size:
            raise ValueError("Cannot check for this size L")
        
        K = float('inf')
        C = 0

        for combination in sum(list(list(combinations(self.events-set(sensitive_events)-{'None'}, t)) for t in range(1, L+1)), []) :
            if self[list(combination)] != 0:
                K = min(self[list(combination)], K)
                for event in sensitive_events:
                    C = max(self.pr_e_b([event], list(combination)), C) 
        
        return K, C
    

    def distribution_LKC(self, L, sensitive_events):
        if type(sensitive_events) == str: sensitive_events = [sensitive_events]

        # Min-case, Q1-case, median-case, Q3-case, Max-case. Mean-case.
        Ks = []
        Cs = []

        for t in range(1, L+1):
            for combination in combinations(self.events-set(sensitive_events)-{'None'}, t):
                if self[list(combination)] != 0:
                    Ks.append(self[list(combination)])

                    max_C = 0
                    for event in sensitive_events:
                        max_C = max(self.pr_e_b([event], list(combination)), max_C)
                
                    Cs.append(max_C)
        
        return Ks, Cs


    # Assumptions: 
        # If knowing the background does not change the odds for a sensitive event, there is no leakage 
        # If the change (after absolute) would be less than zero, it is set to zero
        # The bigger the change for a sensitive event, the harder the punishment (a.k.a, one difference of 0.5 is worse than two of 0.25)
            # How big this punishment is will be determined by 'function', which should range from 0 to 1
        # If background_odds = False: each background is equally likely to be known
        # If absolute = False: knowing something did not happen is not leakage
        # If percentage = True: a change should be punished harder if it happens on an event with already small likelihood
    
    # Notes:
        # The result will always be between 0 and 1 (and more precisely between 0 and (1-default change for sensitive event)) (unless percentage == True, then all bets are off)
        # Privacy Confidence values can only be compared if they used the same function

    # Step 1: for each background set of length L, which exists at least once, we compute the odds of the sensitive activity
    # Step 2: we subtract the standard odds of the sensitive activity from those odds (min 0 after absolute)
    # Step 3: for each of the changes we use a function
        # Make it absolute if we want to punish the knowledge the sensitive activity did not occur
        # Divide by the standard odds if we want to have relative change
        # Put it to a power if we want to punish larger changes harder
        # Multiply by odds for background to acount for unlikely or likely backgrounds
    # Step 4: we add all those result together and viola

    def cc_distribution_LKC(self, L, sensitive_events, absolute = False, percentage = False, function = basic, background_odds = False):
        if type(sensitive_events) == str: sensitive_events = [sensitive_events]

        confidence_changes = []

        for t in range(1, L+1):
            for combination in combinations(self.events-set(sensitive_events)-{'None'}, t):
                if self[list(combination)] != 0:
                    max_value = 0

                    for event in sensitive_events:
                        value = self.pr_e_b_c([event], list(combination))

                        if background_odds: value = value*self.pr_e(list(combination)) # Gives bigger results/less impact if it is after the function
                        if percentage: value = value/self.pr_e([event]) # Becomes smaller results/less impact if it is after the function
                        if absolute: value = abs(value)
                        value = function(max(value, 0))

                        max_value = max(value, max_value)

                    confidence_changes.append(max_value)
        
        return sum(confidence_changes) / len(confidence_changes)
    

    # The CC that we use in the paper
    def paper_cc(self, L, sensitive_events):
        if type(sensitive_events) == str: sensitive_events = [sensitive_events]

        upper_cc = 0
        lower_cc = 0

        # All backgrounds of size L or lower which appear at least once
        possible_backgrounds = sum(list(list(combinations(self.events-set(sensitive_events)-{'None'}, t)) for t in range(1, L+1)), []) 
        backgrounds = list(background for background in possible_backgrounds if self[list(background)] != 0)
        
        for background in backgrounds:
            lower_cc += 1
            background_values = []

            for event in sensitive_events:
                RS_1 = max(self.pr_e_b([event], list(background)) - self.pr_e([event]), 0) # The odds change, or 0
                RS_2 = self.pr_e(list(background))/self.pr_e([event]) # Background odds divided by sensitive odds
                RS = (RS_1 * RS_2)**2 # Make it quadratic
                background_values.append(RS)

            upper_cc += max(background_values)

        if lower_cc == 0: return 0
        else: return upper_cc / lower_cc
    


    # The CC that we use in the paper
    # Requires the upper_cc and lower_cc from 'lower' layers
    def paper_cc_all(self, L, sensitive_events, previous_upper_cc, previous_lower_cc):
        if type(sensitive_events) == str: sensitive_events = [sensitive_events]

        upper_cc = previous_upper_cc
        lower_cc = previous_lower_cc

        # All backgrounds of size L or lower which appear at least once
        possible_backgrounds = list(combinations(self.events-set(sensitive_events)-{'None', 'tau'}, L))
        backgrounds = list(background for background in possible_backgrounds if self[list(background)] != 0)
        
        for background in backgrounds:
            lower_cc += 1
            background_values = []

            for event in sensitive_events:
                RS_1 = max(self.pr_e_b([event], list(background)) - self.pr_e([event]), 0) # The odds change, or 0
                RS_2 = self.pr_e(list(background))/self.pr_e([event]) # Background odds divided by sensitive odds
                RS = (RS_1 * RS_2)**2 # Make it quadratic
                background_values.append(RS)

            upper_cc += max(background_values)

        return upper_cc, lower_cc