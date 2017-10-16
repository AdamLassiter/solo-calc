#! /usr/bin/env python3

from functools import reduce
from multiset import Multiset as multiset


class Node:
    """
    A node N represents a named particle in a solo.
    """

    def __init__(self, name: str) -> None:
        self.name = name


class Edge(tuple):
    """
    An edge E is a tuple of nodes.
    There are two kinds of edges: input edges and output edges.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for node in self:
            assert isinstance(node, Node)
        if kwargs.get('input', False):
            self.kind = 'input'
        elif kwargs.get('output', False):
            self.kind = 'output'
        else:
            self.kind = 'irrelevant'
        self.subject: Node = self[0]
        self.objects = self[1:]
        self.arity = len(self.objects)

    @property
    def nodes(self):
        return {node for node in self}


class Graph(multiset):
    """
    A graph G is a finite multiset of edges.
    """
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for edge in self:
            assert isinstance(edge, Edge)

    @property
    def nodes(self) -> set:
        return reduce(lambda a, b: a | b, (edge.nodes for edge in self))


class Box:
    """
    A box B is a pair <G, S> where G is a graph and S <= nodes[G].
    S is called the internal nodes of B and nodes[G]\S the principal nodes.
    """

    def __init__(self, graph: Graph, nodes: set) -> None:
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
    """
    A typechecked multiset of boxes, M.
    """

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


class Diagram:
    """
    A solo diagram SD is a triple (G, M, l) where:
        G is a graph, or finite multiset of edges,
        M is a finite multiset of boxes,
        l is a map s.t. nodes[G] u principals[M] -> N := { all Nodes }
    """

    def __init__(self, graph: Graph, boxes: Boxes, l: dict) -> None:
        for box in boxes:
            assert (graph.nodes - box.internals).isdisjoint(box.internals)
        for key, value in l:
            assert isinstance(key, Node) and isinstance(value, Node)
            assert key in graph.nodes | boxes.principals
        self.graph = graph
        self.boxes = boxes
        self.l = l


if __name__ == "__main__":
    pass
