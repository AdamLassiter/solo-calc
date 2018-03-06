#! /usr/bin/env python3

from json import dumps
import unittest

from diagrams import Node, Input, Output, Graph, Box, Boxes, Map, Diagram


class TestDiagrams(unittest.TestCase):
    
    def test_everything(self):
        # edge-edge
        ee_node = [Node('a'), Node('b'), Node(), Node('p')]
        ee_edges = [Input((ee_node[1], ee_node[0])),
                    Output((ee_node[1], ee_node[2])),
                    Input((ee_node[3], *ee_node[0:3]))]

        # edge-box
        eb_node = [Node('c'), Node('d'), Node('x'), Node(), Node()]
        eb_edges = [Input((eb_node[2], *eb_node[0:2]))]
        eb_boxes = [([Output(eb_node[2:5]),
                      Input(eb_node[3:5])],
                     eb_node[3:5])]

        loop_node = [Node() for _ in range(10)]
        loop_edges = [Input((loop_node[i-1], loop_node[i])) for i, _ in enumerate(loop_node)]
        
        g = Graph(ee_edges + eb_edges)
        m = Boxes([Box((Graph(g), frozenset(i))) for g, i in eb_boxes])
        l = Map()

        d = Diagram((g, m, l))

        print(d.json, d.reduce().json, sep='\n\n')
        with open('graph.json', 'w') as file:
            file.write(dumps(d.json))


if __name__ == '__main__':
    unittest.main()
