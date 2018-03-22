#! /usr/bin/env python3

from functools import reduce
from json import dumps
import unittest

from diagrams import Node, Input, Output, Graph, Box, Boxes, Map, Diagram


def big_diagram():
    # edge-edge
    ee = [Node('y'), Node('z'), Node(), Node('x')]
    ee_edges = [Input(reversed(ee[0:2])),
                Output(ee[1:3]),
                Input((ee[3], *ee[0:3]))]
    # edge-box
    eb = [Node('y'), Node('z'), Node('x'), Node(), Node()]
    eb_edges = [Input((eb[2], *eb[0:2]))]
    eb_boxes = [([Output(eb[2:5]), Input(eb[3:5])], eb[3:5])]
    # box-box
    """bb = [Node('y'), Node('z'), Node(), Node(), Node(), Node('x')]
    bb_edges = []
    bb_boxes = [([Output(reversed(bb[0:3]))], bb[0:2]), 
                ([Input(bb[2:5]), Output(reversed(bb[3:6]))], bb[3:5])]
    # internal box
    ib = [Node(), Node(), Node(), Node('x')]
    ib_edges = []
    ib_boxes = [([Input(reversed(ib[0:2])), Output(ib[1:3]),
                  Input((ib[3], ib[0], ib[2]))], ib[0:3])]"""
    # graph, boxes, diagram
    g = Graph(ee_edges + eb_edges)# + bb_edges + ib_edges)
    m = Boxes([Box((Graph(g), frozenset(i))) for g, i in eb_boxes])# + bb_boxes + ib_boxes])
    d = Diagram((g, m))
    return d



class TestDiagrams(unittest.TestCase):

    def test_everything(self):
        d = big_diagram()
        # print(d.json, d.reduce().json, sep='\n\n')
        with open('graph.json', 'w') as file:
            file.write(dumps(reduce(lambda d, _: d.reduce(), range(0), d).json))



if __name__ == '__main__':
    unittest.main()
