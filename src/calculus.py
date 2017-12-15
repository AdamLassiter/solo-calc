#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import reduce
from random import choice

from graph import Graph


# NOTE: Notes for later
"""
Expressions are immutable due to problems with adding mutable items to a set:
    Since a set is stored by object hash value, object hashes must remain constant.
    There is not enough unique immutable data per object to allow for this.
    Furthermore, this allows reductions to make themselves grandchildren of their parents
        (see Composition/Scope reduction and rescoping operation)

Reductions are performed recursively:
    Each agent will first reduce each of its sub-agents.
    Then reduction rules are applied where applicable - this includes:
        * Grouping nested operators of the same type
        * Extracting scopes where applicable ((x)P | Q) -> (x)(P | Q) if x ∉ fn(Q)
        * TODO: (Delayed) expansion of replication operator
            See paper implementation

Fusions are performed as follows:
    Output x on u, input u onto y -> Define/rename x := y
    (x)(̅u x | u y | P) -> P{y / x}

Renaming functions σ are found as follows:
    Construct graph(s) G, H ... by treating all names as nodes and the pairs x̃, ỹ as edges
    Check there is at most one free node fn per connected graph G
    Define σ[bn] := fn ∀ bn ϵ G
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
        fusions = self.fusions | other.fusions
        for name in fusions:
            name.fusions = fusions - {name}
            name.name = other.name


class Solo(Agent):

    def __init__(self, subject: Name, objects: tuple) -> None:
        for name in objects:
            assert isinstance(name, Name)
        self.subject = subject
        self.objects = objects
        self.arity = len(objects)

    def reduce(self) -> Agent:
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

    def reduce(self) -> Agent:
        return type(self)()

    @property
    def names(self) -> set:
        return set()

    @property
    def bound_names(self) -> set:
        return set()


class Composition(Agent):

    def __init__(self, agents: set) -> None:
        for agent in agents:
            assert isinstance(agent, Agent)
        self.agents = agents

    def __str__(self) -> str:
        return '(%s)' % (' | '.join(map(str, self.agents)))

    def reduce(self) -> Agent:
        agents = set()
        rescope = set()
        # NOTE: ((a | b) | c) == (a | (b | c)) -> (a | b | c)
        for agent in map(lambda x: x.reduce(), self.agents):
            if isinstance(agent, Composition):
                agents |= agent.agents
            else:
                agents |= {agent}
        # NOTE: ((x)P | Q) -> (x)(P | Q)
        for sagent in set(filter(lambda x: isinstance(x, Scope), agents)):
            rescope |= sagent.bindings - self.free_names
            sagent.bindings &= self.free_names
            if not sagent.bindings:
                agents -= {sagent}
                agents |= {sagent.agent}
        return Scope(rescope, type(self)(agents)) if rescope else type(self)(agents)

    @staticmethod
    def attrs(s: set, attr: str) -> set:
        return set(reduce(set.union,
                          map(lambda x: frozenset(getattr(x, attr)), s),
                          set()))

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

    def construct_sigma(self, objects_pairs: zip) -> dict:
        # NOTE: Graph partitioning > naive pairwise cases for intersection
        graph = Graph()
        sigma = {}
        for pair in objects_pairs:
            graph.insert_edge(*pair)
        partitions = graph.partitions()
        for partition in partitions:
            intersect = self.free_names & partition
            assert len(intersect) <= 1
            if len(intersect) == 0:
                free_name = choice(partition)
            else:
                free_name = intersect.pop()
            for bound_name in set(partition) - {free_name}:
                sigma[bound_name] = free_name
        return sigma

    def reduce(self):
        bindings = self.bindings
        agent = self.agent.reduce()
        # NOTE: (x)(y)(P) == (xy)(P)
        if isinstance(agent, Scope):
            bindings |= agent.bindings
            agent = agent.agent
        # NOTE: (z)(̅u x | u y | P) -> Pσ
        if isinstance(agent, Composition):
            for iagent in set(filter(lambda x: isinstance(x, Input), agent.agents)):
                for oagent in set(filter(lambda x: isinstance(x, Output), agent.agents)):
                    if iagent.subject == oagent.subject \
                    and iagent.arity == oagent.arity:
                        sigma = self.construct_sigma(zip(iagent.objects, oagent.objects))
                        agent.agents -= {iagent, oagent}
                        if not agent.agents:
                            agent.agents |= {Inaction()}
                        if len(agent.agents) == 1:
                            agent = agent.agents.pop()
                        return Match(type(self)(bindings, agent), sigma)
        return type(self)(bindings, agent)

    @property
    def names(self) -> set:
        return self.bindings | self.agent.names

    @property
    def bound_names(self) -> set:
        return self.bindings | self.agent.bound_names


class Match(Agent):

    def __init__(self, agent: Agent, matches: dict) -> None:
        for key, value in matches.items():
            assert isinstance(key, Name) and isinstance(value, Name)
            # NOTE: Here, {a: c, b: c} renames both a and b to c
            assert key in agent.bound_names
        assert isinstance(agent, Scope)
        self.agent = agent
        self.matches = matches

    def __str__(self) -> str:
        return '%s{%s}' % (self.agent, ', '.join(['%s/%s' % (value, key)
                                                  for key, value in self.matches.items()]))

    def reduce(self) -> Agent:
        agent = self.agent
        agent.bindings -= set(self.matches.keys())
        if not agent.bindings:
            agent = agent.agent
        for key, value in self.matches.items():
            key.fuse_into(value)
        return agent.reduce()

    @property
    def names(self) -> set:
        return self.agent.names
    
    @property
    def bound_names(self) -> set:
        return self.agent.bound_names


class Replication(Agent):

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def __str__(self) -> str:
        return '!(%s)' % self.agent

    def reduce(self):
        agent = self.agent.reduce()
        # NOTE: !(!(P)) == !(P)
        if isinstance(agent, Replication):
            agent = agent.agent
        # TODO: Replication operator
        return type(self)(agent)
    
    @property
    def names(self) -> set:
        return self.agent.names

    @property
    def bound_names(self) -> set:
        return self.agent.bound_names


if __name__ == '__main__':
    w, x, y, z, u = Name('w'), Name('x'), Name('y'), Name('z'), Name('u')
    expr = Scope({w, x}, Composition({Input(u, (x, z)),
                                      Output(u, (y, w)),
                                      Replication(Input(u, (w, x, y, z)))}))
    while True:
        print(expr)
        input()
        expr = expr.reduce()
