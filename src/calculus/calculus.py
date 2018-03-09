#! /usr/bin/env python3

from __future__ import annotations
from functools import reduce
from itertools import count
from string import digits
from typing import Tuple, TypeVar, Union, FrozenSet as Set

from multiset import FrozenMultiset as multiset

from graph import graph

set = frozenset


class Name(str):
    
    @staticmethod
    def fresh(working_set: Set[Name], name_hint: str = 'u') -> Name:
        name_hint = name_hint.rstrip(digits)
        for name in (Name(name_hint + str(i)) for i in count()):
            if name not in working_set:
                return name
        return None


class Agent:

    def __str__(self) -> str:
        raise NotImplemented

    def flatten(self) -> Agent:
        raise NotImplemented

    def reduce(self) -> Agent:
        raise NotImplemented

    def reduce(self) -> Agent:
        raise NotImplemented

    @property
    def names(self) -> Set[Name]:
        raise NotImplemented


class Scope(Agent):

    def __init__(self, child: Agent, bound_names: Set[Name]) -> None:
        self.child = child
        self.bound_names = bound_names

    def __str__(self) -> str:
        return '(%s)%s' % (' '.join(self.bound_names), str(self.child))

    def flatten(self) -> Agent:
        child = self.child.flatten()
        if isinstance(child, Scope):
            return type(self)(child.child,
                              self.bound_names | child.bound_names)
        elif isinstance(child, (Replication, Solo)):
            return type(self)(Composition(set({child})), self.bound_names)
        else:
            assert isinstance(self.child, Composition)
            return type(self)(self.child, self.bound_names)

    def construct_sigma(self, input: Solo, output: Solo) -> Tuple[Sigma, Set[Name]]:
        g = graph()
        sigma = Sigma()
        fresh_names: Set[Name] = set()
        for i_obj, o_obj in zip(input.objects, output.objects):
            g.insert_edge(i_obj, o_obj)
        for partition in g.partitions:
            intersect = partition - self.bound_names
            if len(intersect) == 0:
                free_name = Name.fresh(self.names)
                fresh_names |= {free_name}
            elif len(intersect) == 1:
                free_name, *_ = intersect
            else:
                return None, None
            for name in partition - {free_name}:
                sigma[name] = free_name
        return sigma, fresh_names

    def reduce(self) -> Agent:
        agent = self.flatten()
        if not isinstance(agent, Scope) or not isinstance(agent.child, Composition):
            return agent
        composition = agent.child.children
        for io_pair in ({input, output}
                         for input in filter(lambda x: isinstance(x, Solo),
                                             composition)
                         for output in filter(lambda x: isinstance(x, Solo)
                                                    and x.subject == input.subject
                                                    and x.parity != input.parity
                                                    and x.arity == input.arity,
                                              composition)):
            sigma, fresh_names = agent.construct_sigma(*io_pair)
            if sigma is not None:
                return sigma(Scope(Composition(composition - io_pair),
                                   agent.bound_names | fresh_names))
        return agent
    
    @property
    def names(self) -> Set[Name]:
        return self.bound_names | self.child.names


class Composition(Agent):

    def __init__(self, children: Set[Agent]) -> None:
        self.children = children

    def __str__(self) -> str:
        return '(%s)' % (' | '.join(map(str, self.children)),)

    def construct_alpha(self, child: Scope) -> Alpha:
        others = Composition(self.children - {child})
        bound_names = tuple(child.bound_names)
        fresh_names = reduce(lambda ns, n: ns + [Name.fresh(others.names | set(ns), n)],
                             bound_names, [])
        alpha = Alpha(zip(bound_names, fresh_names))
        return alpha

    def flatten(self) -> Agent:
        for child in self.children:
            child = child.flatten()
            if isinstance(child, Composition):
                return type(self)(self.children - {child} | child.children)
            elif isinstance(child, Scope):
                alpha = self.construct_alpha(child)
                alpha_child = alpha(child)
                return Scope(Composition(self.children - {child} | {alpha_child.child}),
                             alpha_child.bound_names)
            else:
                assert isinstance(child, (Replication, Solo))
        else:
            return type(self)(self.children)

    @property
    def names(self) -> Set[Name]:
        return reduce(set.union, map(lambda x: x.names, self.children))


class Replication(Agent):

    def __init__(self, child: Agent) -> None:
        self.child = child

    def __str__(self) -> str:
        return '!%s' % (str(self.child),)

    def flatten(self) -> Agent:
        child = self.child.flatten()

        return self

    @property
    def names(self) -> Set[Name]:
        return self.child.names


class Solo(Agent):

    def __init__(self, subject: Name, objects: Tuple[Name, ...], parity: bool) -> None:
        self.subject = subject
        self.objects = objects
        self.parity = parity

    def __str__(self) -> str:
        return ' '.join((self.subject,) + self.objects)

    def flatten(self) -> Agent:
        return type(self)(self.subject, self.objects, self.parity)

    @property
    def arity(self) -> int:
        return len(self.objects)

    @property
    def names(self) -> Set[Name]:
        return set({self.subject} | {*self.objects})


T = TypeVar('T', Agent, Name)
class Match(dict):

    def __init__(self, *args, in_scope: multiset = multiset(),
                 fuse: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.in_scope = in_scope
        self.fuse = fuse

    def __call__(self, agent: T) -> T:
        if isinstance(agent, Composition):
            return type(agent)(set({type(self)(self, in_scope=self.in_scope)(child)
                                    for child in agent.children}))
        elif isinstance(agent, Scope):
            self.in_scope |= agent.bound_names
            if self.fuse:
                return type(agent)(self(agent.child), set(agent.bound_names - self.keys()))
            else:
                return type(agent)(self(agent.child), set(map(self, agent.bound_names)))
        elif isinstance(agent, Replication):
            return type(agent)(self(agent.child))
        elif isinstance(agent, Solo):
            return type(agent)(self(agent.subject),
                               tuple(map(self, agent.objects)),
                               agent.parity)
        else:
            assert isinstance(agent, Name)
            return type(agent)(self[agent])

    def __getitem__(self, key: Name) -> Name:
        return super().get(key, key) if self.in_scope[key] == 1 else key


class Alpha(Match):

    def __init__(self, *args, fuse=False, **kwargs) -> None:
        super().__init__(*args, fuse=fuse, **kwargs)


class Sigma(Match):

    def __init__(self, *args, fuse=True, **kwargs) -> None:
        super().__init__(*args, fuse=fuse, **kwargs)


if __name__ == '__main__':
    a, b, c, p = (Name(x) for x in 'abcp')
    ag = Scope(Composition(set({Solo(a, (b,), True),
                                Solo(a, (c,), False),
                                Solo(p, (a,b,c), True)})), set({p, b}))
    print(ag, ag.reduce(), sep='\n')
