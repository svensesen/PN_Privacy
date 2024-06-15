# PN_Privacy
This is the code used for the paper "Stochastic Petri Net Calculations for Model Privacy Protection".
All python (.py) files set up the core code used, the jupyter notebook (.pynb) files utilise these libraries to perform the code used in the paper.
The purpose off all files and folders is as follows

- LKC: contains the implimentation of probability calculation methdos for the event logs
	- Calculate Papper CC: Actually calculates the Maximum C and Model Risk Score for the event logs
	- LKC: Provides code which creates ListIntegerMaps which can then be used to calculate the the Maximum C, Model Risk Score and more
	- LKC_vis: Used for creating some visualizations
	- Number_Calc: Sets up the ListIntegerMaps used in Calculate Papper CC
	- Paper Graphs: The code used to create the graphs in the paper
	
- Models: Creates non-miner models and converts certain models between formats
	- Coverting Models: Converts all models in need of conversion
	- Creating Models: Creates the used Enumeration and Flower models
	- Empty.pnml: A file used for the model conversion
	- ModelConversion: The code which converts from pnml (default model format) to pnp (custom model format)
	- ModelCreation: Code able to create Flower and Enumeration models

- Pytri: Implements Petri nets and everything surrounding them
	- Arc: Implements Petri net, DFA and reachability graph arcs
	- ConditionalProb: Code for computing probabilites and the Maximum C and Model Risk Score
	- DFA: Implements and DFA
	- Dummy: Contains dummy value for everything requiring dummy values
	- Element: Implements places, transitions and states for Petri nets, DFA's and reachability graphs
	- Functions: Implements the functions from 'Reasoning on Labelled Petri Nets and Their Dynamics in a Stochastic Setting'
	- PetriNet: Implement PNP's and Petri nets
	- ReachabilityGraph: Implements reachability graphs

- Stochastic Creation Paper Code: This folder is here for the code implementation of "Stochastic Process Discovery By Weight Estimation". Requires turning it into a .jar file

- Synthetic: Contains various synthetic models

- Main:
	- Calculate Paper CC Model: Actually calculates the Maximum C and Model Risk Score for the Petri Nets
	- Create Stochastic Models: Uses the 'Stochastic Creation Paper Code' to turn models stochastic
	- Synthetic Models: Tests the Synthetic models on various aspects
