import weakref

class Arc:
    # Creates an arc, also sets up all the information of the input and output
    # Note: I am not doing a check if one element is a state and the other a transition
    def __init__(self, _input, _output):
        self.input = _input# self._input = weakref.ref(_input)
        self.output = _output# self._output = weakref.ref(_output)

        self.input.outgoing_arcs.append(self)
        self.output.incoming_arcs.append(self)

    def __repr__(self):
        return f"A) {self.input} -> {self.output}"
    
    # @property
    # def input(self):
    #     return self._input()

    # @property
    # def output(self):
    #     return self._output()


    def destroy(self):
        pass
        # self.input.outgoing_arcs.remove(self)
        # self.output.incoming_arcs.remove(self)

        # del self.input
        # del self.output
    

class PetriArc(Arc):
    def __init__(self, _input, _output):
        super().__init__(_input, _output)


class DFA_Arc(Arc):
    def __init__(self, _input, _output, _label):
        super().__init__(_input, _output)
        self.label = _label

        _input.label_to_outgoing_arc[_label] = self
        _output.label_to_incoming_arc[_label] = self

    def __repr__(self):
        return f"A) {self.input} -{self.label}> {self.output}"
    
    def destroy(self):
        # try: del self.input.label_to_outgoing_arc[self.label]
        # except: pass
        # try: del self.output.label_to_incoming_arc[self.label]
        # except: pass
        super().destroy()



class GraphArc(Arc):
    def __init__(self, _input, _output, _odds, _transition):
        super().__init__(_input, _output)
        self.odds = _odds
        self.transition = _transition
    
    def __repr__(self):
        return f"A) {self.input} -{self.transition.label},{self.odds}> {self.output}"