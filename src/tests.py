#! /usr/bin/env python3

import unittest

from calculus import build_agent


# TODO: Negative test cases
class TestSoloCalculus(unittest.TestCase):

    def test_fusion(self):
        print('testing standard fusion')
        agent = build_agent('(x)(u x | ^u y | p x y)')
        self.assertEqual(str(agent.reduce().reduce()), 'p y y')


    def test_cross_replicator(self):
        print('testing cross-replicator fusion')
        agent = build_agent('(y)(u x | !(x)(^u y | p x y))')
        print(agent.reduce().reduce())


    def test_inter_replicator(self):
        print('testing inter-replicator fusion')
        agent = build_agent('(xy)(!(z)(u x | p x y) | !(z)(^u y | p u z))')
        agent = agent.reduce()
        

    def test_multi_replicator(self):
        print('testing multi-replicator fusion')


if __name__ == '__main__':
    unittest.main()
