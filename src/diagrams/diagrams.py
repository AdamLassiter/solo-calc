#! /usr/bin/env python3

from __future__ import annotations
from collections.abc import Iterable
from functools import reduce
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


    def __str__(self) -> str:
        return self.name


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


    @staticmethod
    def from_json(json: dict, nodes: dict = {}) -> Node:
        return Node(json['title'], json['id'])



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

    def __init__(self, *args, uuid: str = None) -> None:
        for node in self:
            assert isinstance(node, Node)
        self.subject: Node = self[0]
        self.objects = self[1:]
        self._node = HiddenNode(uuid=uuid)
        self._uuid = uuid if uuid else str(uuid4())
        self.arity = len(self.objects)


    @property
    def _uuid(self) -> str:
        return self.__uuid


    @_uuid.setter
    def _uuid(self, value: str):
        self.__uuid = value
        # Leaving this on causes edges to 'stick' on reduction
        # Leaving this off causes edges to 'tug' inwards on reduction
        self._node._uuid = value


    @property
    def nodes(self) -> set:
        return set({node for node in self})

    
    @property
    def json(self) -> list:
        if type(self) == Input:
            arrow = 1
            source = self.subject.json['id']
            target = self._node.json['id']
        else:
            arrow = -1
            source = self._node.json['id']
            target = self.subject.json['id']
        return [{'source': source, 'target': target, 'value': 1, 'arrow': arrow}] + \
                [{'source': self._node.json['id'], 'target': obj.json['id'], 'value': 1, 'arrow': 0}
                 for obj in self.objects]

    @staticmethod
    def from_json(json: list, nodes: dict = {}) -> Edge:
        subject = json[0]['source' if json[0]['arrow'] == 1 else 'target']
        uuid = json[1]['id']
        objects = list(map(lambda x: x['target'], json[1:]))
        return Edge(map(nodes.get, [subject] + objects), uuid=uuid)



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

    def __init__(self, *args, uuid: str = None) -> None:
        super().__init__(*args)
        for edge in self:
            assert isinstance(edge, Edge)
        self._uuid = uuid if uuid else str(uuid4())


    @property
    def nodes(self) -> set:
        return reduce(lambda a, b: a | b, (edge.nodes for edge in self), set())


    @property
    def edges(self) -> set:
        return set(self)


    @property
    def json(self) -> dict:
        return {'nodes': [node.json for node in (self.nodes
                                                | {edge._node for edge in self})],
                'edges': reduce(lambda a, b: a + b.json, self, []),
                'id': self._uuid}
    

    @staticmethod
    def from_json(json: dict, nodes: dict = {}) -> Graph:
        for j in json['nodes']:
            nodes[j['id']] = Node.from_json(j, nodes)
        return Graph([Edge.from_json(j, nodes) for j in json['edges']], uuid=json['id'])



class Box(pair):
    '''
    A box B is a pair <G, S> where G is a graph and S <= nodes[G].
    S is called the internal nodes of B and nodes[G]\S the principal nodes.
    '''

    def __init__(self, *args, uuid: str = None) -> None:
        graph, internals = self
        for node in internals:
            assert isinstance(node, Node)
        assert internals <= graph.nodes
        self.graph = graph
        self.internals = internals
        self._uuid = uuid if uuid else str(uuid4())


    @property
    def nodes(self) -> set:
        return self.graph.nodes


    @property
    def principals(self) -> set:
        return self.nodes - self.internals


    @property
    def json(self) -> dict:
        return {'id': self._uuid,
                'graph': self.graph.json,
                'perimeter': [node.json for node in self.principals]}


    @staticmethod
    def from_json(json: dict, nodes: dict = {}) -> Box:
        graph = Graph.from_json(json['graph'], nodes)
        internals = graph.nodes - set(json['perimeter'])
        return Box(graph, internals, uuid=json['id'])



class Boxes(multiset):
    '''
    A typechecked multiset of boxes, M.
    '''

    def __init__(self, *args, uuid: str = None):
        super().__init__(*args)
        for box in self:
            assert isinstance(box, Box)
        self._uuid = uuid if uuid else str(uuid4())


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
    def json(self) -> list:
        return [box.json for box in self]

    
    @staticmethod
    def from_json(json: list, nodes: dict = {}) -> Boxes:
        return Boxes([Box.from_json(j, nodes) for j in json])


class Map(dict):

    def __call__(self, obj):
        if not isinstance(obj, Node):
            return type(obj)(map(self, obj)) if hasattr(obj, '__iter__') else obj
        else:
            return self.get(obj, obj)


    @property
    def domain(self) -> set:
        return set(self.keys())


    @property
    def range(self) -> set:
        return set(self.values())



class Sigma(Map):

    def __init__(self, alpha: Edge = None, beta: Edge = None, from_dict = None) -> None:
        if from_dict:
            super().__init__(from_dict)
        else:
            super().__init__()
            if alpha.subject == beta.subject and alpha.arity == beta.arity:
                g = graph()
                for edge in zip(alpha.objects, beta.objects):
                    g.insert_edge(*edge)
                for partition in g.partitions():
                    intersect = set(filter(lambda x: x.named, partition))
                    if len(intersect) == 0:
                        free_node, *_ = partition
                    elif len(intersect) == 1:
                        free_node, *_ = intersect
                    else:
                        raise Exception('No such sigma exists - not enough free nodes')
                    for node in partition - {free_node}:
                        self[node] = free_node
                assert not self.range & self.domain
            else:
                raise Exception('No such sigma exists - nonmatching edges')


    def __call__(self, obj):
        ret = super().__call__(obj)
        if hasattr(obj, '_uuid'):
            ret._uuid = obj._uuid
        return ret



class Rho(Map):

    def __init__(self, box_internals: set) -> None:
        super().__init__()
        for node in box_internals:
            self[node] = Node(node.name if node.named else None)


    def __call__(self, obj):
        if isinstance(obj, Sigma):
            return type(obj)(from_dict=[self(item) for item in obj.items()])
        else:
            return super().__call__(obj)

    
class Diagram(pair):
    '''
    A solo diagram SD is a pair (G, M) where:
        G is a graph: graph = multiset<edge>,
        M is a finite multiset of boxes: box = pair<graph, set<node>>
    '''

    def __init__(self, *args) -> None:
        graph, boxes = self
        for box in boxes:
            assert (graph.nodes - box.internals).isdisjoint(box.internals)
        self.graph = graph
        self.boxes = boxes

    def reduce(self):
        # NOTE: edge-edge reduction
        for alpha, beta in ((alpha, beta)
                            for alpha in typefilter(self.graph.edges, Input)
                            for beta in  typefilter(self.graph.edges, Output)):
            try:
                sigma = Sigma(alpha, beta)
                assert alpha.subject == beta.subject
                graph = Graph(self.graph - {alpha, beta})
                boxes = self.boxes
                return Diagram((sigma(graph), sigma(boxes)))
            except:
                pass

        # NOTE: edge-box reduction
        for alpha, beta, box in ((alpha, beta, box)
                                 for Io in {Input, Output}
                                 for alpha in typefilter(self.graph.edges, Io)
                                 for box in self.boxes
                                 for beta in typefilter(box.graph.edges, Io.inverse)):
            try:
                rho = Rho(box.internals)
                sigma = rho(Sigma(alpha, beta))
                ag = self.graph - {alpha}
                bg = box.graph - {beta}
                graph = Graph(ag + rho(bg))
                boxes = self.boxes
                return Diagram((sigma(graph), sigma(boxes)))
            except:
                pass

        # NOTE: internal box reduction
        for alpha, beta in ((alpha, beta)
                            for Io in {Input, Output}
                            for box in self.boxes
                            for alpha in typefilter(box.graph.edges, Io)
                            for beta in typefilter(box.graph.edges, Io.inverse)):
            try:
                rho = Rho(box.internals)
                sigma = rho(Sigma(alpha, beta))
                ag = self.graph
                bg = box.graph - {alpha, beta}
                graph = Graph(ag + rho(bg))
                boxes = self.boxes
                return Diagram((sigma(graph), sigma(boxes)))
            except:
                pass

        # NOTE: box-box reduction
        for alpha, beta, abox, bbox in ((alpha, beta, abox, bbox)
                                        for Io in {Input, Output}
                                        for abox in self.boxes
                                        for alpha in typefilter(abox.graph.edges, Io)
                                        for bbox in self.boxes - {abox}
                                        for beta in typefilter(bbox.graph.edges, Io.inverse)):
            try:
                rho = Rho(abox.internals | bbox.internals)
                sigma = rho(Sigma(alpha, beta))
                g = self.graph
                ag = abox.graph - {alpha}
                bg = bbox.graph - {beta}
                graph = Graph(g + rho(ag) + rho(bg))
                boxes = self.boxes
                return Diagram((sigma(graph), sigma(boxes)))
            except:
                pass
        return self


    @property
    def nodes(self) -> set:
        return self.graph.nodes | self.boxes.nodes


    @property
    def json(self) -> dict:
        return {'graph': Graph(self.graph - multiset((box.graph for box in self.boxes))).json,
                'boxes': self.boxes.json}


    @staticmethod
    def from_json(json: dict, nodes: dict = {}) -> Diagram:
        return Diagram(Graph.from_json(json['graph'], nodes),
                       Boxes.from_json(json['boxes'], nodes))
