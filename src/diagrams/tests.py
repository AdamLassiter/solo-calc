#! /usr/bin/env python3

from json import dumps
import unittest

from diagrams import Node, Input, Output, Graph, Boxes, Map, Diagram


class TestDiagrams(unittest.TestCase):
    
    def test_everything(self):
        a = Node()
        b = Node()
        c = Node()

        d = Input(b, a)
        e = Output(b, c)
        
        g = Graph({d, e})
        m = Boxes()
        l = Map({a: 'a'})

        d = Diagram(g, m, l)

        print(d.json, d.reduce().json, sep='\n\n')
        with open('graph.json', 'w') as file:
            file.write(dumps(d.json))



if __name__ == '__main__':
    unittest.main()
