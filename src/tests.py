#! /usr/bin/env python3

import unittest

from calculus import build_agent, reduce, Agent


class TestCase(unittest.TestCase):
    
    def setUp(self):
        self.addTypeEqualityFunc(Agent, Agent.equals)


class TestStandardFusion(TestCase):

    def test_two_bound(self):
         # both bound names
        agent = build_agent('(x y)(u x | ^u y | p x y)')
        reduction = build_agent('(u0)p u0 u0')
        print('\n', agent, '->', reduce(agent))
        self.assertEqual(reduction, reduce(agent))

    def test_one_bound(self):
        # one bound, one free name
        agent = build_agent('(x)(u x | ^u y | p x y)')
        reduction = build_agent('p y y')
        print('\n', agent, '->', reduce(agent))
        self.assertEqual(reduction, reduce(agent))

    def test_zero_bound(self):
         # both free names
        agent = build_agent('(u x | ^u y | p x y)')
        reduction = build_agent('(u x | ^u y | p x y)')
        print('\n', agent, '->', reduce(agent))
        self.assertEqual(reduction, reduce(agent))


# TODO: Multiple +ve/-ve test cases
class TestFlatteningTheorem(TestCase):                      

    def test_one_bound(self):
        # one bound names
        agent = build_agent('!(y)(p x | !(q y))')
        reduction = build_agent('(u0)(!(y)(p x | ^u0 q) | !(w0)(w0 y | u0 w0))')
        print('\n', agent, '->', reduce(agent))
        self.assertEqual(reduction, reduce(agent))


# TODO: Multiple +ve/-ve test cases
class TestCrossReplicatorFusion(TestCase):

    def test_two_bound(self):
        # one bound inner and one bound outer
        agent = build_agent('(y)(u y | !(x)(^u x | p x y))')
        reduction = build_agent('(u0)(p u0 u0 | !(x)(^u x | p x y))')
        print('\n', agent, '->', reduce(agent))
        self.assertEqual(reduction, reduce(agent))


# TODO: Multiple +ve/-ve test cases
class TestInterReplicatorFusion(TestCase):

    def test_two_bound(self):
        # one bound inner, one bound outer
        agent = build_agent('(x)(!(y)(u x | ^u y | p x y))')
        reduction = build_agent('(u0)(!(y)(u x | ^u y | p x y) | p u0 u0)')
        print('\n', agent, '->', reduce(agent))
        self.assertEqual(reduction, reduce(agent))


# TODO: Multiple +ve/-ve test cases
class TestMultiReplicatorFusion(TestCase):

    def test_multi_replicator(self):
        # one bound per replicator
        agent = build_agent('(x y)(!(x)(u x) | !(y)(^u y) | p x y)')
        reduction = build_agent('(u0)(!(x)(u x) | !(y)(^u y) | p u0 u0)')
        print('\n', agent, '->', reduce(agent))
        self.assertEqual(reduction, reduce(agent))


if __name__ == '__main__':
    unittest.main(verbosity=2)
