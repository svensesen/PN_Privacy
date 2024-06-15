import xml.etree.ElementTree as ET
import re

def prom_pnml_to_pnp(pnml_path, txt_path):
    tree = ET.parse(pnml_path)
    root = tree.getroot()
    page = root.find("net/page")
    
    with open(txt_path, 'w', encoding="utf-8") as f:
        id_to_label = {}

        f.write("# Places")
        initial_places = []
        for child in page:
            if child.tag == "place":
                place_id = child.items()[0][1]
                
                id_to_label[place_id] = place_id
                initial_marking = child.find("initialMarking/text")
                if not initial_marking == None: initial_places.append([place_id, initial_marking.text])
                    
                f.write(f"\np {place_id}")
        
        
        f.write("\n\n# Transitions")
        transition_labels = []
        for child in page:
            if child.tag == "transition":
                transition_id = child.items()[0][1]
                transition_text = child.find("name/text").text.replace(' ', '\u2588')
                if "tau" in transition_text: transition_text = "tau"
                
                id_to_label[transition_id] = f"{transition_text}({transition_labels.count(transition_text)})"
                transition_labels.append(transition_text)
                
                f.write(f"\nt {id_to_label[transition_id]} 1")
                

        f.write("\n\n# Arcs")
        for child in page:
            if child.tag == "arc":
                arc_source = child.items()[1][1]
                arc_target = child.items()[2][1]
                
                f.write(f"\na {id_to_label[arc_source]} {id_to_label[arc_target]}")
        
        f.write(f"\n\n# Initial State\ni{''.join(f' {i[0]} {i[1]}' for i in initial_places)}")
        
        f.write("\n\n# Deadlock States")
        final_markings = root.find("net/finalmarkings")
        if final_markings:
            for marking in final_markings:
                current_marking = "\nf"

                for place in marking:
                    place_id = place.get("idref")
                    for object in place:
                        if object.tag.endswith("text"):
                            number = int(object.text)
                            if number > 0:
                                current_marking += f" {place_id} {number}"
                
                if current_marking != "\nf":
                    f.write(current_marking)
        else:
            f.write("\n# No Deadlock States Found")
        


def prom_stochastic_pnml_to_pnp(stochastic_pnml_path, txt_path):
    tree = ET.parse(stochastic_pnml_path)
    root = tree.getroot()
    page = root.find("{http://www.pnml.org/version-2009/grammar/pnml}net/{http://www.pnml.org/version-2009/grammar/pnml}page")
    
    with open(txt_path, 'w') as f:
        id_to_label = {}
        
        f.write("# Places")
        initial_places = []
        for child in page:
            if child.tag == "{http://www.pnml.org/version-2009/grammar/pnml}place":
                place_id = child.items()[0][1]
                
                id_to_label[place_id] = place_id
                initial_marking = child.find("{http://www.pnml.org/version-2009/grammar/pnml}initialMarking/{http://www.pnml.org/version-2009/grammar/pnml}text")
                if not initial_marking == None: initial_places.append([place_id, initial_marking.text])
                    
                f.write(f"\np {place_id}")
        

        f.write("\n\n# Transitions")
        transition_labels = []
        for child in page:
            if child.tag ==  "{http://www.pnml.org/version-2009/grammar/pnml}transition":
                transition_id = child.items()[0][1]
                transition_text = child.find("{http://www.pnml.org/version-2009/grammar/pnml}name/{http://www.pnml.org/version-2009/grammar/pnml}text").text.replace(' ', '_')
                if  bool(re.match(r'^n\d+$', transition_text)): transition_text = "tau"
                if "tau" in transition_text: transition_text = "tau"
                
                
                id_to_label[transition_id] = f"{transition_text}({transition_labels.count(transition_text)})"
                transition_labels.append(transition_text)
                
                for childer in child.find("{http://www.pnml.org/version-2009/grammar/pnml}toolspecific"):
                    if childer.items()[0][1] == "weight":
                        transition_weight = childer.text
                        break
                
                f.write(f"\nt {id_to_label[transition_id]} {transition_weight}")
                

        f.write("\n\n# Arcs")
        for child in page:
            if child.tag == "{http://www.pnml.org/version-2009/grammar/pnml}arc":
                arc_source = child.items()[1][1]
                arc_target = child.items()[2][1]
                
                f.write(f"\na {id_to_label[arc_source]} {id_to_label[arc_target]}")

        f.write(f"\n\n# Initial State\ni{''.join(f' {i[0]} {i[1]}' for i in initial_places)}")
        
        # We let Pytri figure it out when it makes a reachability graph
        f.write("\n\n# Deadlock States Not Recorded")




# # Petrinet export as pnml
# tree = ET.parse("Traffic Fines/Model/PNML.pnml")
# root = tree.getroot()
# page = root.find("net/page")

# for child in page:
#     if child.tag == "place":
#         place_id = child.items()[0][1]
#         place_text = child.find("name/text").text
#         place_inital = not child.find("initialMarking") == None
#         print(place_id, place_text, place_inital)
    
#     if child.tag == "transition":
#         transition_id = child.items()[0][1]
#         transition_text = child.find("name/text").text
#         print(transition_id, transition_text)
    
#     if child.tag == "arc":
#         arc_id = child.items()[0][1]
#         arc_source = child.items()[1][1]
#         arc_target = child.items()[2][1]
#         print(arc_id, arc_source, arc_target)


# # Petrinet export as epnml
# tree = ET.parse("Traffic Fines/Model/EPNML.pnml")
# root = tree.getroot()
# page = root.find("net")

# for child in page:
#     if child.tag == "place":
#         place_id = child.items()[0][1]
#         place_text = child.find("name/text").text
#         print(place_id, place_text)
    
#     if child.tag == "transition":
#         transition_id = child.items()[0][1]
#         transition_text = child.find("name/text").text
#         print(transition_id, transition_text)
    
#     if child.tag == "arc":
#         arc_id = child.items()[0][1]
#         arc_source = child.items()[1][1]
#         arc_target = child.items()[2][1]
#         print(arc_id, arc_source, arc_target)


# # Petrinet export as cpnxml
# tree = ET.parse("Traffic Fines/Model/CPNXML.cpn")
# root = tree.getroot()
# page = root.find("cpnet/page")

# for child in page:
#     if child.tag == "place":
#         place_id = child.items()[0][1]
#         place_text = child.find("text").text
#         print(place_id, place_text)
    
#     if child.tag == "trans":
#         transition_id = child.items()[0][1]
#         transition_text = child.find("text").text
#         print(transition_id, transition_text)
    
#     if child.tag == "arc":
#         arc_id = child.items()[0][1]
#         arc_orientation = child.items()[1][1]
#         arc_transition = child.find("transend").items()[0][1]
#         arc_place = child.find("placeend").items()[0][1]
#         print(arc_id, arc_orientation, arc_transition, arc_place)


# # StochasticNet export as (stochastic) PNML
# tree = ET.parse("Traffic Fines/Model/Stochastic PNML.pnml")
# root = tree.getroot()
# page = root.find("{http://www.pnml.org/version-2009/grammar/pnml}net/{http://www.pnml.org/version-2009/grammar/pnml}page")

# for child in page:
#     if child.tag == "{http://www.pnml.org/version-2009/grammar/pnml}place":
#         place_id = child.items()[0][1]
#         place_text = child.find("{http://www.pnml.org/version-2009/grammar/pnml}name/{http://www.pnml.org/version-2009/grammar/pnml}text").text
#         print(place_id, place_text)
    
#     if child.tag == "{http://www.pnml.org/version-2009/grammar/pnml}transition":
#         transition_id = child.items()[0][1]
#         transition_text = child.find("{http://www.pnml.org/version-2009/grammar/pnml}name/{http://www.pnml.org/version-2009/grammar/pnml}text").text
        
#         for childer in child.find("{http://www.pnml.org/version-2009/grammar/pnml}toolspecific"):
#             if childer.items()[0][1] == "weight":
#                 transition_weight = childer.text
#         print(transition_id, transition_text, transition_weight)
    
#     if child.tag == "{http://www.pnml.org/version-2009/grammar/pnml}arc":
#         arc_id = child.items()[0][1]
#         arc_source = child.items()[1][1]
#         arc_target = child.items()[2][1]
#         print(arc_id, arc_source, arc_target)


# # StochasticNet export as PNML
# tree = ET.parse("Traffic Fines/Model/SPNML.pnml")
# root = tree.getroot()
# page = root.find("net/page")

# for child in page:
#     if child.tag == "place":
#         place_id = child.items()[0][1]
#         place_text = child.find("name/text").text
#         print(place_id, place_text)
    
#     if child.tag == "transition":
#         transition_id = child.items()[0][1]
#         transition_text = child.find("name/text").text
#         print(transition_id, transition_text)
    
#     if child.tag == "arc":
#         arc_id = child.items()[0][1]
#         arc_source = child.items()[1][1]
#         arc_target = child.items()[2][1]
#         print(arc_id, arc_source, arc_target)