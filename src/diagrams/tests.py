#! /usr/bin/env python3

from json import dumps
import unittest

from diagrams import Node, Input, Output, Graph, Boxes, Map, Diagram


class TestDiagrams(unittest.TestCase):
    
    def test_everything(self):
        a = Node('a')
        b = Node('b')
        c = Node()
        p = Node('p')

        d = Input((b, a))
        e = Output((b, c))
        f = Input((p, a, b, c))
        
        g = Graph({d, e, f})
        m = Boxes()
        l = Map()

        d = Diagram((g, m, l))

        print(d.json, d.reduce().json, sep='\n\n')
        with open('graph.json', 'w') as file:
            file.write(dumps(d.reduce().json))


if __name__ == '__main__':
    unittest.main()
