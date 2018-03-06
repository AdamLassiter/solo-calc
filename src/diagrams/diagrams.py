#! /usr/bin/env python3

from __future__ import annotations
from collections.abc import Callable, Iterable
from copy import deepcopy
from functools import reduce, wraps
from uuid import uuid4

from multiset import FrozenMultiset as multiset

from graph import graph

set = frozenset


def typefilter(iterable: Iterable, obj_t: type) -> set:
    return set(filter(lambda obj: isinstance(obj, obj_t), iterable))



class pair(tuple):

    def __new__(cls, *args) -> tuple:
        ret = super().__new__(cls, *args)
        assert len(ret) == 2
        return ret



class triple(tuple):

    def __new__(cls, *args) -> tuple:
        ret = super().__new__(cls, *args)
        assert len(ret) == 3
        return ret



class Node(str):
    '''
    A node N represents a named particle in a solo.
    '''
    size = 10

    def __new__(cls, name: str = None, uuid: str = None) -> Node:
        uuid = uuid if uuid else str(uuid4())
        obj = super().__new__(cls, uuid)
        obj._name = name
        obj._uuid = uuid
        return obj


    @property
    def name(self) -> str:
        return self._name if self.named else self._uuid


    @name.setter
    def name(self, value: str):
        self._name = value


    @property
    def named(self) -> bool:
        return self._name is not None

    
    @property
    def json(self) -> dict:
        return {'id': self._uuid, 'title': self._name, 'r': self.size}



class HiddenNode(Node):
    '''
    A connection point between the subject edge and the object edges.
    '''
    size = 0



class Edge(tuple):
    '''
    An edge E is a tuple of nodes.
    There are two kinds of edges: input edges and output edges.
    '''

    def __init__(self, *args) -> None:
        for node in self:
            assert isinstance(node, Node)
        self.subject: Node = self[0]
        self.objects = self[1:]
        self._edge = HiddenNode()
        self.arity = len(self.objects)


    @property
    def nodes(self) -> set:
        return set({node for node in self})

    
    @property
    def json(self) -> object:
        if type(self) == Input:
            arrow = 1
            source = self.subject.json['id']
            target = self._edge.json['id']
        else:
            arrow = -1
            source = self._edge.json['id']
            target = self.subject.json['id']
        return [{'source': source, 'target': target, 'value': 1, 'arrow': arrow}] + \
                [{'source': self._edge.json['id'], 'target': obj.json['id'], 'value': 1, 'arrow': 0}
                 for obj in self.objects]



class Input(Edge):
    inverse: type = None

class Output(Edge):
    inverse: type = None

Input.inverse = Output
Output.inverse = Input



class Graph(multiset):
    '''
    A graph G is a finite multiset of edges.
    '''
    
    def __init__(self, *args) -> None:
        super().__init__(*args)
        for edge in self:
            assert isinstance(edge, Edge)


    @property
    def nodes(self) -> set:
        return reduce(lambda a, b: a | b, (edge.nodes for edge in self), set())


    @property
    def edges(self) -> set:
        return set(self)


    @property
    def json(self) -> object:
        return {'nodes': [node.json for node in (self.nodes
                                                | {edge._edge for edge in self})],
                'edges': reduce(lambda a, b: a + b.json, self, [])}



class Box(pair):
    '''
    A box B is a pair <G, S> where G is a graph and S <= nodes[G].
    S is called the internal nodes of B and nodes[G]\S the principal nodes.
    '''

    def __init__(self, *args) -> None:
        graph, internals = self
        for node in internals:
            assert isinstance(node, Node)
        assert internals <= graph.nodes
        self.graph = graph
        self.internals = internals


    @property
    def nodes(self) -> set:
        return self.graph.nodes


    @property
    def principals(self) -> set:
        return self.nodes - self.internals


    @property
    def json(self) -> object:
        return {'graph': self.graph.json,
                'perimeter': [node.json for node in self.principals]}



class Boxes(multiset):
    '''
    A typechecked multiset of boxes, M.
    '''

    def __init__(self, *args):
        super().__init__(*args)
        for box in self:
            assert isinstance(box, Box)


    @property
    def nodes(self) -> set:
        return reduce(lambda a, b: a | b, (box.nodes for box in self), set())


    @property
    def internals(self) -> set:
        return reduce(lambda a, b: a | b, (box.internals for box in self), set())


    @property
    def principals(self) -> set:
        return reduce(lambda a, b: a | b, (box.internals for box in self), set())


    @property
    def json(self) -> object:
        return [box.json for box in self]



class Map(dict):

    def __call__(self, obj):
        if not isinstance(obj, Node):
            return type(obj)(map(self, obj)) if len(obj) else obj
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

    def __init__(self, *args) -> None:
        graph, boxes, labelling = self
        for box in boxes:
            assert (graph.nodes - box.internals).isdisjoint(box.internals)
        for node in labelling.domain:
            assert isinstance(node, Node)
            assert node in graph.nodes | boxes.principals
        self.graph = graph
        self.boxes = boxes
        self.labelling = labelling


    def construct_sigma(self, alpha: Edge, beta: Edge) -> Map:
        if alpha.subject == beta.subject and alpha.arity == beta.arity:
            g = graph()
            sigma = Map()
            for edge in zip(alpha.objects, beta.objects):
                g.insert_edge(*edge)
            for partition in g.partitions():
                intersect = set(filter(lambda x: x.named, partition))
                if len(intersect) == 0:
                    free_node, *_ = partition
                elif len(intersect) == 1:
                    free_node, *_ = intersect
                else:
                    return None
                for node in partition - {free_node}:
                    sigma[node] = free_node
            assert not sigma.range & sigma.domain
            assert not sigma.domain & self.labelling.domain
            return sigma
        return None

    
    # TODO: Implement rho construction
    # However, this is technically correct
    def construct_rho(self, internals: set) -> Callable:
        copies: dict = {}
        @wraps
        def freshcopy(*args, **kwargs):
            ret = deepcopy(*args, **kwargs)
            for node in ret.nodes:
                if node.name in copies.keys():
                    node.name = copies[node.name]
                else:
                    copies[node.name] = node.name
            return ret
        return freshcopy


    def reduce(self):
        # NOTE: edge-edge reduction
        for alpha, beta in ((alpha, beta)
                            for alpha in typefilter(self.graph.edges, Input)
                            for beta in  typefilter(self.graph.edges, Output)):
            sigma = self.construct_sigma(alpha, beta)
            if sigma:
                assert alpha.subject == beta.subject
                graph = Graph(self.graph - {alpha, beta})
                boxes = self.boxes
                l = Map({k:v for k, v in self.labelling.items() if k not in sigma.domain})
                return Diagram((sigma(graph), sigma(boxes), l))

        # NOTE: edge-box reduction
        for alpha, beta, box in ((alpha, beta, box)
                                 for Io in {Input, Output}
                                 for alpha in typefilter(self.graph.edges, Io)
                                 for box in self.boxes
                                 for beta in typefilter(box.graph.edges, Io.inverse)):
            sigma = self.construct_sigma(alpha, beta)
            if sigma:
                rho = self.construct_rho(box.internals)
                ag = self.graph - {alpha}
                bg = box.graph - {beta}
                graph = Graph(ag + rho(bg))
                boxes = self.boxes
                l = Map({k:v for k, v in self.labelling.items()
                         if k in sigma(graph).nodes | sigma(boxes).nodes})
                return Diagram((sigma(graph), sigma(boxes), l))

        # NOTE: box-box reduction
        for alpha, beta, abox, bbox in ((alpha, beta, abox, bbox)
                                        for Io in {Input, Output}
                                        for abox in self.boxes
                                        for alpha in typefilter(abox.graph.edges, Io)
                                        for bbox in self.boxes - {abox}
                                        for beta in typefilter(bbox.graph.edges, Io.inverse)):
            sigma = self.construct_sigma(alpha, beta)
            if sigma:
                rho = self.construct_rho(abox.internals | bbox.internals)
                g = self.graph
                ag = abox.graph - {alpha}
                bg = bbox.graph - {beta}
                graph = Graph(g + rho(ag) + rho(bg))
                boxes = self.boxes
                l = Map({k:v for k, v in self.labelling.items()
                         if k in sigma(graph).nodes | sigma(boxes).nodes})
                return Diagram((sigma(graph), sigma(boxes), l))

        # NOTE: internal box reduction
        for alpha, beta in ((alpha, beta)
                            for Io in {Input, Output}
                            for box in self.boxes
                            for alpha in typefilter(box.graph.edges, Io)
                            for beta in typefilter(box.graph.edges, Io.inverse)):
            sigma = self.construct_sigma(alpha, beta)
            if sigma:
                rho = self.construct_rho(box.internals)
                ag = self.graph
                bg = box.graph - {alpha, beta}
                graph = Graph(ag + rho(bg))
                boxes = self.boxes
                l = Map({k:v for k, v in self.labelling.items()
                         if k in sigma(graph).nodes | sigma(boxes).nodes})
                return Diagram((sigma(graph), sigma(boxes), l))

        return self


    @property
    def json(self) -> object:
        return {'graph': Graph(self.graph - multiset((box.graph for box in self.boxes))).json,
                'boxes': self.boxes.json}
