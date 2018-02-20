#! /usr/bin/env python3

class graph(dict):

    def insert_node(self, node):
        self[node] = frozenset()


    def insert_edge(self, *nodes):
        nodes = frozenset(nodes)
        for node in nodes:
            if node not in self.keys():
                self.insert_node(node)
            self[node] |= nodes - {node}


    def span(self, node) -> frozenset:
        assert node in self.keys()
        frontier, span = self[node], {node}
        while frontier:
            span |= frontier
            next_frontier = frozenset()
            for node in frontier:
                next_frontier |= self[node]
            frontier = next_frontier - span
        return frozenset(span)


    def partitions(self) -> frozenset:
        nodes = set(self.keys())
        partitions = frozenset()
        while nodes:
            span = self.span(nodes.pop())
            partitions |= {span}
            nodes -= span
        return partitions
