#! /usr/bin/env python3

import unittest

from repl import build_agent, reduce, Agent, CanonicalAgent


class TestSuiteMeta(type):
    full_suite = unittest.TestSuite()

    def __new__(metacls, name, bases, attr):
        def cls_init(self, *args, **kwargs):
            def setUp(self):
                def eq(a, b, msg=None):
                    ret = a.alpha_eq(b)
                    if ret is None:
                        raise self.failureException()
                    return True
                self.addTypeEqualityFunc(CanonicalAgent, eq)
                print('\n', self.__class__.__name__)

            def tearDown(self):
                pass
           
            super(type(self), self).__init__(*args, **kwargs)
            for fname in filter(lambda x: x[:4] == 'test', dir(self)):
                cname = ''.join(x.title() for x in fname.split('_'))
                TestCase = type(
                    '.'.join([self.__class__.__name__, cname]),
                    (unittest.TestCase,),
                    {
                        'runTest': getattr(self, fname),
                        'setUp': setUp,
                        'tearDown': tearDown
                    }
                )
                self.addTest(TestCase())

        def cls_run(self, *args, **kwargs):
            print('=' * 70)
            print(self.__class__.__name__)
            super(type(self), self).run(*args, **kwargs)
 
        cls_obj = super().__new__(
            metacls,
            name,
            bases + (unittest.TestSuite, unittest.TestCase),
            dict(attr, __init__=cls_init, run=cls_run)
        )
        TestSuiteMeta.full_suite.addTest(cls_obj())
        return cls_obj


class TestEqualityOperator(metaclass=TestSuiteMeta):

    def test_alpha_equivalence(self):
        agent1 = build_agent('(x)(p x)')
        agent2 = build_agent('(y)(p y)')
        agent3 = build_agent('(x)(p y)')
        print(agent1, '==' if agent1.alpha_eq(agent2) else '!=', agent2)
        print(agent2, '==' if agent2.alpha_eq(agent3) else '!=', agent3)
        assert agent1.alpha_eq(agent2)
        assert not agent2.alpha_eq(agent3)

    def test_multiset_property(self):
        agent1 = build_agent('(x)(p x | p x)')
        agent2 = build_agent('(x)(p x)')
        print(agent1, '==' if agent1.alpha_eq(agent2) else '!=', agent2)
        assert not agent1.alpha_eq(agent2)


class TestStandardFusion(metaclass=TestSuiteMeta):

    def test_two_bound(self):
         # both bound names
        agent = build_agent('(x y)(u x | ^u y | p x y)')
        reduction = build_agent('(y)p y y')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_one_bound(self):
        # one bound, one free name
        agent = build_agent('(x)(u x | ^u y | p x y)')
        reduction = build_agent('p y y')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_zero_bound(self):
         # both free names
        agent = build_agent('(u x | ^u y | p x y)')
        reduction = build_agent('(u x | ^u y | p x y)')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)


class TestFlatteningTheorem(metaclass=TestSuiteMeta):

    def test_two_bound(self):
        # both bound names
        agent = build_agent('!(q y)(p x | !(q y))')
        flattened = build_agent('(y0)(!(^y0 | q y) | !(y q)(p x | y0))')
        print('!(q y)(p x | !(q y))', '->', agent)
        assert agent.alpha_eq(flattened)

    def test_one_bound(self):
        # one bound, one free
        agent = build_agent('!(q)(p x | !(q y))')
        flattened = build_agent('(y0)(!(q)(y0 y | p x) | !(y1)(q y1 | ^y0 y1))')
        print('!(q)(p x | !(q y))', '->', agent)
        assert agent.alpha_eq(flattened)

    def test_zero_bound(self):
        agent = build_agent('!(p x | !(q y))')
        print('!(p x | !(q y))', '->', agent)
        flattened = build_agent('(y0)(!(p x | y0 q y) | !(q0 y1)(q0 y1 | ^y0 q0 y1))')
        assert agent.alpha_eq(flattened)


class TestCrossReplicatorFusion(metaclass=TestSuiteMeta):

    def test_two_bound(self):
        # both bound names (one outer, one inner)
        agent = build_agent('(x)(u x | !(y)(^u y | p x y))')
        reduction = build_agent('(x)(p x x | !(y)(^u y | p x y))')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_one_bound_outer(self):
        # one bound (outer), one free (inner)
        agent = build_agent('(x)(u x | !(^u y | p x y))')
        reduction = build_agent('(p y y | !(^u y | p y y))')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_one_bound_inner(self):
        # one bound (inner), one free (outer)
        agent = build_agent('(u x | !(y)(^u y | p x y))')
        reduction = build_agent('(p x x | !(y)(^u y | p x y))')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_zero_bound(self):
        # both free names
        agent = build_agent('(u x | !(^u y | p x y))')
        reduction = build_agent('(u x | !(^u y | p x y))')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)


class TestInterReplicatorFusion(metaclass=TestSuiteMeta):

    def test_two_bound(self):
        # both bound names (outer)
        agent = build_agent('(x y)(!(u x | ^u y) | p x y)')
        reduction = build_agent('(x)(p x x | u x | ^u x | !(u x | ^u x))')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_one_bound_outer(self):
        # one bound (outer), one free (inner)
        agent = build_agent('(x)(!(u x | ^u y) | p x y)')
        reduction = build_agent('(u y | ^u y | p y y | !(u y | ^u y))')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_one_bound_inner(self):
        # one bound (inner), one free (outer)
        # reduction happens but is not demonstrable
        agent = build_agent('(!(x)(u x | ^u y) | p x y)')
        reduction = build_agent('(!(x)(u x | ^u y) | p x y)')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_zero_bound(self):
        # both free names
        agent = build_agent('!(u x | ^u y | p x y)')
        reduction = build_agent('!(u x | ^u y | p x y)')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)


class TestMultiReplicatorFusion(metaclass=TestSuiteMeta):

    def test_two_bound_outer_outer(self):
        # both bound names (outer)
        agent = build_agent('(x y)(!(u x) | !(^u y) | p x y)')
        reduction = build_agent('(x)(p x x | !(u x) | !(^u x))')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_two_bound_outer_inner(self):
        # both bound names (one outer, one inner)
        # interesting case of reduction happening but not doing anything
        # adding another term to !(y)(^u y | P) will cause non-finite reduction
        # same is true for one bound inner
        # any residue is non-finitely replicable
        agent = build_agent('(x)(!(u x) | !(y)(^u y) | p x y)')
        reduction = build_agent('(x)(p x y | !(u x) | !(y)(^u y))')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_one_bound_outer(self):
        # one bound (outer), one free (inner)
        agent = build_agent('(x)(!(u x) | !(^u y) | p x y)')
        reduction = build_agent('(!(u y) | !(^u y) | p y y)')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)

    def test_one_bound_inner(self):
        # one bound (inner), one free (outer)
        # but nothing happened...
        agent = build_agent('(!(x)(u x) | !(^u y) | p x y)')
        reduction = build_agent('(!(x)(u x) | !(^u y) | p x y)')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)
    
    def test_zero_bound(self):
        # both free names
        agent = build_agent('(!(u x) | !(^u y) | p x y)')
        reduction = build_agent('(!(u x) | !(^u y) | p x y)')
        print(agent, '->', reduce(agent))
        assert reduce(agent).alpha_eq(reduction)


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    for suite in TestSuiteMeta.full_suite:
        runner.run(suite)
