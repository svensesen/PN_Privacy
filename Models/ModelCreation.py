import os
import sys

current_directory = os.path.dirname(os.path.realpath(__file__))
code_folder = os.path.abspath(os.path.join(current_directory, ".."))
sys.path.insert(1, code_folder)
from LKC.LKC import event_column, case_column


def create_flower_model(log, path):
    with open(path, 'w', encoding="utf-8") as f:
        f.write("p start")
        f.write("\np pistil")
        f.write("\np end")

        f.write("\nt tau(0) 1")
        f.write("\nt tau(1) 1")

        f.write("\na start tau(0)")
        f.write("\na tau(0) pistil")
        f.write("\na pistil tau(1)")
        f.write("\na tau(1) end")

        f.write("\ni start 1")
        f.write("\nd end 1")

        unique_events = list(log[event_column].unique())
        for event in unique_events:
            event_name = event.replace(' ', '\u2588')
            f.write(f"\nt {event_name}(0) 1")
            f.write(f"\na pistil {event_name}(0)")
            f.write(f"\na {event_name}(0) pistil")
        
        
def create_event_log_model(log, path):
    with open(path, 'w', encoding="utf-8") as f:
        f.write("p start")
        f.write("\np end")
        f.write("\ni start 1")
        f.write("\nd end 1")

        current_place = "start"
        current_transition = ""
        event_counter = {event: 0  for event in list(log[event_column].unique())}
        place_counter = 0
        for case in log.groupby(case_column):
            for event in case[1][event_column]:
                if current_transition != "":
                    current_place = f"p{place_counter}"
                    f.write(f"\np {current_place}")
                    f.write(f"\na {current_transition} {current_place}")
                    place_counter += 1

                event_name = event.replace(' ', '\u2588')
                current_transition = f"{event_name}({event_counter[event]})"
                f.write(f"\nt {current_transition} 1")
                f.write(f"\na {current_place} {current_transition}")
                
                event_counter[event] += 1
            
            current_place = "start"
            current_transition = ""
            
            f.write(f"\na {current_transition} end")