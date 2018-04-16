#! /usr/bin/env python3

import unittest

from repl import build_agent, reduce, Agent, CanonicalAgent


class TestCase(unittest.TestCase):
    
    def setUp(self):
        def eq(a, b, msg=None):
            ret = a.alpha_eq(b)
            if ret is None:
                raise self.failureException()
            return True
        self.addTypeEqualityFunc(CanonicalAgent, eq)
        print()


class TestEqualityOperator(TestCase):

    def test_alpha_equivalence(self):
        agent1 = build_agent('(x)(p x)')
        agent2 = build_agent('(y)(p y)')
        agent3 = build_agent('(x)(p y)')
        print(agent1, '==' if agent1.alpha_eq(agent2) else '!=', agent2)
        print(agent2, '==' if agent2.alpha_eq(agent3) else '!=', agent3)
        self.assertEqual(agent1, agent2)
        self.assertNotEqual(agent2, agent3)


class TestStandardFusion(TestCase):

    def test_two_bound(self):
         # both bound names
        agent = build_agent('(x y)(u x | ^u y | p x y)')
        reduction = build_agent('(y)p y y')
        print(agent, '->', reduce(agent))
        self.assertEqual(reduce(agent), reduction)

    def test_one_bound(self):
        # one bound, one free name
        agent = build_agent('(x)(u x | ^u y | p x y)')
        reduction = build_agent('p y y')
        print(agent, '->', reduce(agent))
        self.assertEqual(reduce(agent), reduction)

    def test_zero_bound(self):
         # both free names
        agent = build_agent('(u x | ^u y | p x y)')
        reduction = build_agent('(u x | ^u y | p x y)')
        print(agent, '->', reduce(agent))
        self.assertEqual(reduce(agent), reduction)


# TODO: Multiple +ve/-ve test cases
class TestFlatteningTheorem(TestCase):

    def test_two_bound(self):
        # two bound names
        agent = build_agent('!(q y)(p x | !(q y))')
        reduction = build_agent('(y0)(!(y1 q0)(^y0 q y | q y) | q y | !(q y)(p x | y0 q y) | p x)')
        print(agent, '->', reduce(agent))
        self.assertEqual(reduce(agent), reduction)

    def test_one_bound(self):
        agent = build_agent('!(q)(p x | !(q y))')
        reduction = build_agent('(u0)(p x | q y | !(p x | u0 y) | !(y)(q y | ^u0 y))')
        print(agent, '->', reduce(agent))
        self.assertEqual(reduce(agent), reduction)


# TODO: Multiple +ve/-ve test cases
class TestCrossReplicatorFusion(TestCase):

    def test_one_bound(self):
        # one bound inner and one bound outer
        agent = build_agent('(x)(u x | !(^u y | p x y))')
        reduction = build_agent('(p y y | !(^u y | p y y))')
        print(agent, '->', reduce(agent))
        self.assertEqual(reduce(agent), reduction)


# TODO: Multiple +ve/-ve test cases
class TestInterReplicatorFusion(TestCase):

    def test_one_bound(self):
        # one bound outer, one free
        agent = build_agent('(x)(!(u x | ^u y | p x y))')
        reduction = build_agent('(!(u y | ^u y | p y y) | p y y)')
        print(agent, '->', reduce(agent))
        self.assertEqual(reduce(agent), reduction)


# TODO: Multiple +ve/-ve test cases
class TestMultiReplicatorFusion(TestCase):

    def test_one_bound(self):
        # one bound outer
        agent = build_agent('(x)(!(u x) | !(^u y) | p x y)')
        reduction = build_agent('(!(u y) | !(^u y) | p y y)')
        print(agent, '->', reduce(agent))
        self.assertEqual(reduce(agent), reduction)


if __name__ == '__main__':
    unittest.main(verbosity=2)
