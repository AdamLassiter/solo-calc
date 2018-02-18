#! /usr/bin/env python3

import unittest

from calculus import build_agent, reduce, Agent


class TestCase(unittest.TestCase):
    
    def setUp(self):
        self.addTypeEqualityFunc(Agent, Agent.equals)


class TestEqualityOperator(TestCase):

    def setUp(self):
        self.addTypeEqualityFunc(Agent, Agent.equals)

    def test_alpha_equivalence(self):
        agent1 = build_agent('(x)(p x)')
        agent2 = build_agent('(y)(^p y)')
        agent3 = build_agent('(x)(p y)')
        print('\n', agent1, '==' if agent1.equals(agent2) else '!=', agent2)
        print('',   agent2, '==' if agent2.equals(agent3) else '!=', agent3)
        assert agent1.equals(agent2)
        assert not agent2.equals(agent3)


class TestStandardFusion(TestCase):

    def test_two_bound(self):
         # both bound names
        agent = build_agent('(x y)(u x | ^u y | p x y)')
        reduction = build_agent('(x)p x x')
        print('\n', agent, '->', reduce(agent))
        assert reduce(agent).equals(reduction)

    def test_one_bound(self):
        # one bound, one free name
        agent = build_agent('(x)(u x | ^u y | p x y)')
        reduction = build_agent('p y y')
        print('\n', agent, '->', reduce(agent))
        assert reduce(agent).equals(reduction)

    def test_zero_bound(self):
         # both free names
        agent = build_agent('(u x | ^u y | p x y)')
        reduction = build_agent('(u x | ^u y | p x y)')
        print('\n', agent, '->', reduce(agent))
        assert reduce(agent).equals(reduction)


# TODO: Multiple +ve/-ve test cases
class TestFlatteningTheorem(TestCase):                      

    def test_two_bound(self):
        # two bound names
        agent = build_agent('!(q y)(p x | !(q y))')
        reduction = build_agent('(!p x | !q y )')
        print('\n', agent, '->', reduce(agent))
        assert reduce(agent).equals(reduction)


# TODO: Multiple +ve/-ve test cases
class TestCrossReplicatorFusion(TestCase):

    def test_two_bound(self):
        # one bound inner and one bound outer
        agent = build_agent('(y)(u y | !(x)(^u x | p x y))')
        reduction = build_agent('(x y)(p x x | !(x)(^u x | p x y))')
        print('\n', agent, '->', reduce(agent))
        assert reduce(agent).equals(reduction)


# TODO: Multiple +ve/-ve test cases
class TestInterReplicatorFusion(TestCase):

    def test_one_bound(self):
        # one bound outer, one free
        agent = build_agent('(x)(!(u x | ^u y | p x y))')
        reduction = build_agent('(!(u y | ^u y | p y y) | p y y)')
        print('\n', agent, '->', reduce(agent))
        assert reduce(agent).equals(reduction)


# TODO: Multiple +ve/-ve test cases
class TestMultiReplicatorFusion(TestCase):

    def test_one_bound(self):
        # one bound outer
        agent = build_agent('(x)(!(u x) | !(^u y) | p x y)')
        reduction = build_agent('(!(u y) | !(^u y) | p y y)')
        print('\n', agent, '->', reduce(agent))
        assert reduce(agent).equals(reduction)


if __name__ == '__main__':
    unittest.main(verbosity=2)
