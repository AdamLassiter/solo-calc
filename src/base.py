#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# NOTE: Notes for later
'''
Expressions are immutable due to problems with adding mutable items to a set:
    Since a set is stored by object hash value, object hashes must remain constant.
    There is not enough unique immutable data per object to allow for this.
    Furthermore, this allows reductions to make themselves grandchildren of their parents
        (see Composition/Scope reduction and rescoping operation)

Reductions are performed recursively:
    Each agent will first reduce each of its sub-agents.
    Then reduction rules are applied where applicable - this includes:
        * Trivial cases for nested copies of operators and TODO: for identites of operators
        * Extracting scopes where applicable ((x)P | Q) -> (x)(P | Q) if x ∉ fn(Q)
        * Finite reduction of (non-nested) replications
            See paper implementation

Fusions are performed as follows:
    Output x on u, input u onto y -> Define/rename x := y
    (x)(̅u x | u y | P) -> P{y / x}

Renaming functions σ are found as follows:
    Construct graph(s) G, H ... by treating all names as nodes and the pairs x̃, ỹ as edges
    Check there is at most one free node fn per connected graph G
    Define σ[bn] := fn ∀ bn ϵ G
'''

from functools import reduce, wraps


# Filters a set for a given type -> set<agent_t> or {}
def typefilter(agent_t: type, agents: frozenset) -> frozenset:
    return frozenset(filter(lambda x: isinstance(x, agent_t), agents))


# Non-empty typefilter -> nonempty set<agent_t>
def netf(agent_t: type, agent) -> frozenset:
    tf = typefilter(agent_t, agent.agents)
    if tf:
        return tf
    else:
        return agent_t.id(agent.agents)


def _rebind(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        ret = func(self, *args, **kwargs)
        if not self.freeze:
            for agent in self.agents:
                agent.bound_names = self.bound_names
        return ret
    return wrapper


class Agent(object):

    def __init__(self) -> None:
        self._freeze = False
        self._agents = frozenset()
        self._bound_names = frozenset()
        self._bindings = frozenset()

    def equals(self, other) -> bool:
        return self._bindings == other._bindings and self <= other and other <= self

    def __le__(self, other) -> bool:
        return all(any(mine.equals(yours)
                       for yours in other.agents)
                  for mine in self.agents)

    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.__str__()

    def reduce(self, matches: dict = {}) -> object:
        raise NotImplementedError

    @staticmethod
    def id(self, agents: frozenset) -> frozenset:
        raise NotImplementedError

    @staticmethod
    def _attrs(s: frozenset, attr: str) -> frozenset:
        return frozenset(reduce(frozenset.union,
                                map(lambda x: frozenset(getattr(x, attr)), s),
                                frozenset()))

    @property
    def agent(self) -> object:
        if len(self._agents) == 1:
            agent, = self.agents
            return agent
        elif len(self.agents) == 0:
            return None
        else:
            raise TypeError('Ambiguous: agent contains multiple children')

    @agent.setter
    def agent(self, value: object):
        if len(self.agents) <= 1:
            self.agents = frozenset({value})
        else:
            raise TypeError('Ambiguous: agent contains multiple children')

    @property
    def freeze(self) -> bool:
       return self._freeze

    @freeze.setter
    def freeze(self, value: bool) -> bool:
        self._freeze = value
        for agent in self.agents:
            agent.freeze = value

    @property
    def agents(self) -> frozenset:
        return self._agents

    @agents.setter
    @_rebind
    def agents(self, value: frozenset) -> None:
        if self._agents:
            raise Exception('Mutation of agents set')
        self._agents = value

    @property
    def names(self) -> frozenset:
        return self._attrs(self._agents, 'names')
    
    @property
    def free_names(self) -> frozenset:
        return self.names - self.bound_names

    @property
    def bound_names(self) -> frozenset:
        return self._bound_names

    @bound_names.setter
    @_rebind
    def bound_names(self, value: frozenset) -> None:
        self._bound_names = value


class Name(str):

    def __new__(cls, *args):
        ret = super().__new__(cls, *args)
        ret.fusion = None
        return ret

    @classmethod
    def fresh(cls, names: frozenset, name_hint: str) -> object:
        i = 0
        while name_hint + str(i) in names:
            i += 1
        return cls(name_hint + str(i))


class Solo(Agent):
    pass


class Inaction(Agent):
    pass


class Composition(Agent):
    pass


class Replication(Agent):
    pass


class Scope(Agent):
    pass


class Match(Agent):
    pass
