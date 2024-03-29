#! /usr/bin/env python3

from collections.abc import Hashable



class graph(dict):

    def insert_node(self, node: Hashable) -> None:
        self[node] = frozenset()


    def insert_edge(self, *nodes: Hashable) -> None:
        for node in nodes:
            if node not in self.keys():
                self.insert_node(node)
            self[node] |= frozenset(nodes) - {node}


    def span(self, node: Hashable) -> frozenset:
        assert node in self.keys()
        frontier, span = self[node], {node}
        while frontier:
            span |= frontier
            next_frontier: frozenset = frozenset()
            for node in frontier:
                next_frontier |= self[node]
            frontier = next_frontier - span
        return frozenset(span)


    def partitions(self) -> frozenset:
        nodes = set(self.keys())
        partitions: frozenset = frozenset()
        while nodes:
            span = self.span(nodes.pop())
            partitions |= {span}
            nodes -= span
        return partitions
