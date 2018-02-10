#! /usr/bin/env python3

import unittest

from calculus import build_agent, reduce
from base import Solo


# TODO: Multiple +ve/-ve test cases
class TestSoloCalculus(unittest.TestCase):

    @staticmethod
    def walk(agent, func):
        print(agent, type(agent), func(agent), sep=' -> ')
        if not isinstance(agent, Solo):
            for ag in agent:
                TestSoloCalculus.walk(ag, func)


    def test_standard_fusion(self): 
        print('\ntesting standard fusion')
        # both bound names
        agent = build_agent('(x y)(u x | ^u y | p x y)')
        reduction = build_agent('(u0)p u0 u0')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))
        # one bound, one free name
        agent = build_agent('(x)(u x | ^u y | p x y)')
        reduction = build_agent('p y y')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))
        # both free names
        agent = build_agent('(u x | ^u y | p x y)')
        reduction = build_agent('(u x | ^u y | p x y)')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))


    def test_flattening(self):
        print('\ntesting flattening theorem')
        # both bound names
        agent = build_agent('!(y)(p x | !(q y))')
        reduction = build_agent('(u0)(!(y)(p x | ^u0 q) | !(w0)(w0 y | u0 w0))')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))


    def test_cross_replicator(self):
        print('\ntesting cross-replicator fusion')
        agent = build_agent('(y)(u y | !(x)(^u x | p x y))')
        reduction = build_agent('(u0)(p u0 u0 | !(x)(^u x | p x y))')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))


    def test_inter_replicator(self):
        print('\ntesting inter-replicator fusion')
        agent = build_agent('(x)(!(y)(u x | ^u y | p x y))')
        reduction = build_agent('(u0)(!(y)(u x | ^u y | p x y) | p u0 u0)')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))


    def test_multi_replicator(self):
        print('\ntesting multi-replicator fusion')
        agent = build_agent('(x y)(!(x)(u x) | !(y)(^u y) | p x y)')
        reduction = build_agent('(u0)(!(x)(u x) | !(y)(^u y) | p u0 u0)')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))


if __name__ == '__main__':
    unittest.main()
