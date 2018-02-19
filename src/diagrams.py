#! /usr/bin/env python3

from functools import reduce
from multiset import FrozenMultiset as multiset

set = frozenset


def typefilter(iterable, obj_t: type) -> set:
    return set(filter(lambda obj: isinstance(obj, obj_t), iterable))



class pair(tuple):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert len(self) == 2



class triple(tuple):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert len(self) == 3



class Node(str):
    '''
    A node N represents a named particle in a solo.
    '''

    def __init__(self, name: str = None) -> None:
        super().__init__(name)
        self.name = name



class Edge(tuple):
    '''
    An edge E is a tuple of nodes.
    There are two kinds of edges: input edges and output edges.
    '''

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for node in self:
            assert isinstance(node, Node)
        self.subject: Node = self[0]
        self.objects = self[1:]
        self.arity = len(self.objects)


    @property
    def nodes(self) -> set:
        return {node for node in self}



class Input(Edge):
    pass

class Output(Edge):
    pass

Input.inverse = Output
Output.inverse = Input



class Graph(multiset):
    '''
    A graph G is a finite multiset of edges.
    '''
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for edge in self:
            assert isinstance(edge, Edge)


    @property
    def nodes(self) -> set:
        return reduce(lambda a, b: a | b, (edge.nodes for edge in self))



class Box(pair):
    '''
    A box B is a pair <G, S> where G is a graph and S <= nodes[G].
    S is called the internal nodes of B and nodes[G]\S the principal nodes.
    '''

    def __init__(self, graph: Graph, nodes: set) -> None:
        super().__init__(graph, nodes)
        for node in nodes:
            assert isinstance(node, Node)
        assert nodes <= graph.nodes
        self.graph = graph
        self._nodes = nodes


    @property
    def nodes(self) -> set:
        return self.graph.nodes


    @property
    def internals(self) -> set:
        return self._nodes


    @property
    def principals(self) -> set:
        return self.nodes - self.internals



class Boxes(multiset):
    '''
    A typechecked multiset of boxes, M.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for box in self:
            assert isinstance(box, Box)


    @property
    def nodes(self) -> set:
        return reduce(lambda a, b: a | b, (box.nodes for box in self))


    @property
    def internals(self) -> set:
        return reduce(lambda a, b: a | b, (box.internals for box in self))


    @property
    def principals(self) -> set:
        return reduce(lambda a, b: a | b, (box.internals for box in self))



class Map(dict):

    def __call__(self, obj: multiset) -> multiset:
        if hasattr(obj, '__iter__'):
            return type(obj)(map(self, obj))
        else:
            return self.get(obj, obj)


    @property
    def domain(self) -> set:
        return set(self.keys())


    @property
    def range(self) -> set:
        return set(self.values())



class Diagram(triple):
    '''
    A solo diagram SD is a triple (G, M, l) where:
        G is a graph: graph = multiset<edge>,
        M is a finite multiset of boxes: box = pair<graph, set<node>>,
        l is a labelling of nodes: labelling = map<node, node>
    '''

    def __init__(self, graph: Graph, boxes: Boxes, l: Map) -> None:
        super().__init__(graph, boxes, l)
        for box in boxes:
            assert (graph.nodes - box.internals).isdisjoint(box.internals)
        for node in l.domain:
            assert isinstance(node, Node)
            assert node in graph.nodes | boxes.principals
        for node in l.range:
            assert isinstance(node, Node) 
        self.graph = graph
        self.boxes = boxes
        self.l = l

    
    # TODO: Implement sigma construction
    def construct_sigma(self, alpha: Input, beta: Output) -> Map:
        if alpha.subject == beta.subject and alpha.arity == beta.arity:
            sigma = Map()
            raise NotImplementedError
            assert sigma.range & sigma.domain == set()
            assert sigma.domain & self.l.domain == set()
            return sigma

    
    # TODO: Implement rho construction
    def construct_rho(self, internals: set) -> Map:
        raise NotImplementedError


    def reduce(self):
        # NOTE: edge-edge reduction
        for alpha, beta in ((alpha, beta)
                            for alpha in typefilter(self.graph.nodes, Input)
                            for beta in  typefilter(self.graph.nodes, Output)):
            sigma = self.construct_sigma(alpha, beta)
            graph = Graph(self.graph - {alpha, beta})
            boxes = self.boxes
            l = Map({k:v for k, v in self.l.items() if k not in sigma.keys()})
            return Diagram(sigma(graph), sigma(boxes), l)

        # NOTE: edge-box reduction
        for alpha, beta, box in ((alpha, beta, box)
                                 for Io in {Input, Output}
                                 for alpha in typefilter(self.graph.nodes, Io)
                                 for box in self.boxes
                                 for beta in typefilter(box.graph.nodes, Io.inverse)):
            sigma = self.construct_sigma(alpha, beta)
            rho = self.construct_rho(box.internals)
            ag = self.graph - {alpha}
            bg = box.graph - {beta}
            graph = Graph(ag + rho(bg))
            boxes = self.boxes
            l = Map({k:v for k, v in self.l.items()
                     if k in sigma(graph).nodes | sigma(boxes).nodes})
            return Diagram(sigma(graph), sigma(boxes), l)

        # NOTE: box-box reduction
        for alpha, beta, abox, bbox in ((alpha, beta, abox, bbox)
                                        for Io in {Input, Output}
                                        for abox in self.boxes
                                        for alpha in typefilter(abox.graph.nodes, Io)
                                        for bbox in self.boxes - {abox}
                                        for beta in typefilter(bbox.graph.nodes, Io.inverse)):
            sigma = self.construct_sigma(alpha, beta)
            rho = self.construct_rho(abox.internals | bbox.internals)
            g = self.graph
            ag = abox.graph - {alpha}
            bg = bbox.graph - {beta}
            graph = Graph(g + rho(ag) + rho(bg))
            boxes = self.boxes
            l = Map({k:v for k, v in self.l.items()
                     if k in sigma(graph).nodes | sigma(boxes).nodes})
            return Diagram(sigma(graph), sigma(boxes), l)

        # NOTE: internal box reduction
        for alpha, beta in ((alpha, beta)
                            for Io in {Input, Output}
                            for box in self.boxes
                            for alpha in typefilter(box.graph.nodes, Io)
                            for beta in typefilter(box.graph.nodes, Io.inverse)):
            sigma = self.construct_sigma(alpha, beta)
            rho = self.construct_rho(box.internals)
            ag = self.graph
            bg = box.graph - {alpha, beta}
            graph = Graph(ag + rho(bg))
            boxes = self.boxes
            l = Map({k:v for k, v in self.l.items()
                     if k in sigma(graph).nodes | sigma(boxes).nodes})
            return Diagram(sigma(graph), sigma(boxes), l)



if __name__ == "__main__":
    pass
