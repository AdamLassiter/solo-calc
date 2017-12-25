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
def typefilter(agent_t: type, agents: set) -> set:
    return set(filter(lambda x: isinstance(x, agent_t), agents))


# Non-empty typefilter -> set<agent_t> not {}
def netf(agent_t: type, agent) -> set:
    tf = typefilter(agent_t, agent.agents)
    if tf:
        return tf
    else:
        return agent_t.id(agent.agents)


def _rebind(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        ret = func(self, *args, **kwargs)
        for agent in self.agents:
            agent.bound_names = self.bound_names
        return ret
    return wrapper


class Agent(object):

    def __init__(self) -> None:
        self._agents = set()
        self._bound_names = set()
        self._bindings = set()

    def __str__(self) -> str:
        raise NotImplementedError

    def reduce(self):
        raise NotImplementedError

    @staticmethod
    def id(self, agents: set) -> set:
        raise NotImplementedError

    @staticmethod
    def _attrs(s: set, attr: str) -> set:
        return set(reduce(set.union,
                          map(lambda x: frozenset(getattr(x, attr)), s),
                          set()))

    @property
    def agent(self) -> object:
        if len(self._agents) == 1:
            agent, = self._agents
            return agent
        elif len(self._agents) == 0:
            return None
        else:
            raise TypeError('Ambiguous: agent contains multiple children')

    @agent.setter
    def agent(self, value: object):
        if len(self._agents) <= 1:
            self._agents = {value}
        else:
            raise TypeError('Ambiguous: agent contains multiple children')

    @property
    def agents(self) -> set:
        return self._agents

    @agents.setter
    @_rebind
    def agents(self, value: set) -> None:
        self._agents = value 

    @property
    def names(self) -> set:
        return self._attrs(self._agents, 'names')
    
    @property
    def free_names(self) -> set:
        return self.names - self.bound_names

    @property
    def bound_names(self) -> set:
        return self._bound_names

    @bound_names.setter
    @_rebind
    def bound_names(self, value: set) -> None:
        self._bound_names = value


class Name(object):
    
    def __init__(self, name: str) -> None:
        self.name = name
        self.fusions = {self}

    def __hash__(self) -> hash:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        assert isinstance(other, type(self))
        return self.name == other.name

    def fuse_into(self, other) -> None:
        assert isinstance(other, type(self))
        fusions = self.fusions | other.fusions
        for name in fusions:
            name.fusions = fusions - {name}
            name.name = other.name

    @classmethod
    def fresh(cls, names: set, name_hint: str) -> object:
        i = 0
        while name_hint + str(i) in [n.name for n  in names]:
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
