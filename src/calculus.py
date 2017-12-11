#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import reduce


# NOTE: Notes for later
"""
Expressions are immutable due to problems with adding mutable items to a set:
    Since a set is stored by object hash value, object hashes must remain constant.
    There is not enough unique immutable data per object to allow for this.

Reductions are performed recursively:
    Each agent will first reduce each of its sub-agents.
    Then reduction rules are applied where applicable - this includes:
        * Grouping nested operators of the same type
        * Extracting scopes where applicable ((x)P | Q) -> (x)(P | Q) if x ∉ fn(Q)
        * TODO: (Delayed) expansion of replication operator

Fusions are performed as follows:
    Output x on u, input u onto y -> Define/rename y := x
    (x)(̅u x | u y | P) -> P{y / x}
"""


class Agent(object):
    
    def reduce(self):
        raise NotImplementedError

    @property
    def names(self) -> set:
        raise NotImplementedError
    
    @property
    def free_names(self) -> set:
        return self.names - self.bound_names

    @property
    def bound_names(self) -> set:
        raise NotImplementedError


class Name(object):
    
    def __init__(self, name: str) -> None:
        self.name = name
        self.fusions = {self}

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self in other.fusions
    
    def fuse_into(self, other):
        assert isinstance(other, type(self))
        self.fusions |= {other}
        other.fusions |= {self}
        self.name = other.name


class Solo(Agent):

    def __init__(self, subject: Name, objects: tuple) -> None:
        for name in objects:
            assert isinstance(name, Name)
        self.subject = subject
        self.objects = objects
        self.arity = len(objects)

    def reduce(self):
        return type(self)(self.subject, self.objects)

    @property
    def names(self) -> set:
        return {self.subject} | {obj for obj in self.objects}

    @property
    def bound_names(self) -> set:
        return set()


class Input(Solo):

    def __str__(self) -> str:
        return '%s ' % self.subject + ''.join(map(str, self.objects))
    

class Output(Solo):

    def __str__(self) -> str:
        return '\u0305%s ' % self.subject + ''.join(map(str, self.objects))


class Inaction(Agent):

    def __str__(self) -> str:
        return '0'

    def reduce(self):
        return type(self)()

    @property
    def names(self) -> set:
        return set()

    @property
    def bound_names(self) -> set:
        return set()


class Composition(Agent):

    def __init__(self, *agents) -> None:
        for agent in agents:
            assert isinstance(agent, Agent)
        self.agents = set(agents)

    def __str__(self) -> str:
        return '(%s)' % (' | '.join(map(str, self.agents)))

    def reduce(self):
        agents = set()
        rescope = set()
        # ((a | b) | c) == (a | (b | c)) -> (a | b | c)
        for agent in map(lambda x: x.reduce(), self.agents):
            if isinstance(agent, Composition):
                agents |= agent.agents
            else:
                agents |= {agent}
        # (x)(̅u x | u y | P) -> P{y / x}
        for iagent in set(filter(lambda x: isinstance(x, Input), agents)):
            for oagent in set(filter(lambda x: isinstance(x, Output), agents)):
                if iagent.subject == oagent.subject \
                and iagent.arity == oagent.arity:
                    for iobject, oobject in zip(iagent.objects, oagent.objects):
                        oobject.fuse_into(iobject)
                    agents -= {iagent}
                    agents -= {oagent}
        # ((x)P | Q) -> (x)(P | Q)
        for sagent in set(filter(lambda x: isinstance(x, Scope), agents)):
            rescope |= sagent.bindings - self.free_names
            sagent.bindings &= self.free_names
            if not sagent.bindings:
                agents -= {sagent}
                agents |= {sagent.agent}
        return Scope(rescope, type(self)(*agents)) if rescope else type(self)(*agents)

    @staticmethod
    def attrs(s: set, attr: str) -> set:
        return set(reduce(frozenset.union, map(lambda x: frozenset(getattr(x, attr)), s)))

    @property
    def names(self) -> set:
        return self.attrs(self.agents, 'names')

    @property
    def bound_names(self) -> set:
        return self.attrs(self.agents, 'bound_names')


class Scope(Agent):

    def __init__(self, bindings: set, agent: Agent) -> None:
        for binding in bindings:
            assert isinstance(binding, Name)
        self.bindings = bindings
        self.agent = agent

    def __str__(self) -> str:
        return '(%s)%s' % (''.join(map(str, self.bindings)), self.agent)

    def reduce(self):
        bindings = self.bindings
        agent = self.agent.reduce()
        # (x)(y)(P) == (xy)(P)
        if isinstance(agent, Scope):
            bindings |= agent.bindings
            agent = agent.agent
        return type(self)(bindings, agent)

    @property
    def names(self) -> set:
        return self.bindings | self.agent.names

    @property
    def bound_names(self) -> set:
        return self.bindings | self.agent.bound_names


class Replication(Agent):

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def __str__(self) -> str:
        return '!%s' % self.agent

    def reduce(self):
        agent = self.agent.reduce()
        # !(!(P)) == !(P)
        if isinstance(agent, Replication):
            agent = agent.agent
        return type(self)(agent)
    
    @property
    def names(self) -> set:
        return self.agent.names

    @property
    def bound_names(self) -> set:
        return self.agent.bound_names


if __name__ == '__main__':
    x, y, z, s = Name('x'), Name('y'), Name('z'), Name('s')
    expr = Replication(Composition(Scope({s}, Input(z, (y,))),
                                   Output(x, (y,)),
                                   Output(z, (x,))))

    while True:
        print(expr)
        input()
        expr = expr.reduce()
