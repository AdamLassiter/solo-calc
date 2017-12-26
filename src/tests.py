#! /usr/bin/env python3

import unittest

from calculus import build_agent, reduce


# TODO: Negative test cases
class TestSoloCalculus(unittest.TestCase):

    def test_fusion(self):
        print('\ntesting standard fusion')
        agent = build_agent('(x)(u x | ^u y | p x y)')
        reduction = build_agent('p y y')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))
        

    def test_flattening(self):
        print('\ntesting flattening theorem')
        agent = build_agent('!(x)(p x | !(q y))')
        reduction = build_agent('(u0)(!(x)(p x | ^u0 q y) | !(q y | (w1 w0)u0 w1 w0))')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))
       

    def test_cross_replicator(self):
        print('\ntesting cross-replicator fusion')
        agent = build_agent('(y)(u y | !(x)(^u x | p x y))')
        reduction = build_agent('(p u0 u0 | !(x)(^u x | p x y))')
        print(agent, '->', reduce(agent))
        self.assertTrue(reduction.equals(reduce(agent)))


    def test_inter_replicator(self):
        print('\ntesting inter-replicator fusion')
        agent = build_agent('(z)(!(x y)(u x | p x y) | !(x y)(^u y | p u z))')
        #reduction = build_agent('')
        print(agent, '->', reduce(agent))
        #self.assertTrue(reduction.equals(reduce(agent)))
       

    def test_multi_replicator(self):
        print('\ntesting multi-replicator fusion')


if __name__ == '__main__':
    unittest.main()
