class Program:
    '''Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize,coverage,edges,ORs etc
    Also want it to set absolute number covered, coverage frac (coverage amongst entire pop), normalised coverage (coverage amongst target pop)'''
    def __init__(self, kwargs): # TODO: set the effectiveness of each intervention to no effect unless specified otherwise
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    def add_edge(self, node):
        '''Edges denote dependence upon adjacent nodes'''
        self.edges.append(node)










