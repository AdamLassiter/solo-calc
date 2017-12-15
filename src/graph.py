class Graph(dict):

    def insert_node(self, node):
        self[node] = set()

    def insert_edge(self, *nodes):
        nodes = set(nodes)
        for node in nodes:
            if node not in self.keys():
                self.insert_node(node)
            self[node] |= nodes - {node}

    def span(self, node) -> set:
        assert node in self.keys()
        frontier, span = self[node], {node}
        while frontier:
            span |= frontier
            next_frontier = set()
            for node in frontier:
                next_frontier |= self[node]
            frontier = next_frontier - span
        return span

    def partitions(self) -> set:
        nodes = set(self.keys())
        partitions = set()
        while nodes:
            span = frozenset(self.span(nodes.pop()))
            partitions |= {span}
            nodes -= span
        return partitions

