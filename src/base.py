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
        * Applying the flattening theorem for 
        * Finite reduction of (non-nested) replications
            See paper implementation

Fusions are performed as follows:
    Input/Output on u of (bound) x and (free) y -> Define/rename x := y
    (x)(̅u x | u y | P) -> P{y / x}

Renaming functions σ are found as follows:
    * Construct graph(s) G, H ... by treating all names as graph nodes and the pairs x̃, ỹ as
      graph edges
    * Check there is at most one free node fn per connected graph G
    * Define σ[bn] := fn ∀ bn ϵ G
'''

from functools import reduce


# Set typefilter: agent_t, set -> set<agent_t> or {}
def tf(agent_t: type, agents: frozenset) -> frozenset:
    return frozenset(filter(lambda x: isinstance(x, agent_t), agents))


# Non-empty typefilter: agent_t, set -> nonempty set<agent_t>
def netf(agent_t: type, agents: frozenset) -> frozenset:
    return frozenset({agent if isinstance(agent, agent_t) else agent_t.id(agent)
                      for agent in agents}) - {None}

typefilter = netf



class Agent(frozenset):

    def equals(self, other) -> bool:
        return type(self) == type(other) \
           and getattr(self, 'bindings', None) == getattr(other, 'bindings', None) \
           and self <= other and other <= self

    def __le__(self, other) -> bool:
        return all(any(mine.equals(yours)
                       for yours in other)
                  for mine in self)

    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return '%s [%s]' % (type(self), str(self))

    def reduce(self, matches: dict = {}, bindings: frozenset = frozenset()) -> object:
        raise NotImplementedError

    def _attrs(self, attr: str) -> frozenset:
       return reduce(frozenset.union,
                     map(lambda x: frozenset(getattr(x, attr)), self),
                     frozenset())
    
    @staticmethod
    def id(agent: object) -> object:
        raise NotImplementedError

    @property
    def agent(self) -> object:
        if len(self) == 1:
            agent, *_ = self
            return agent
        elif len(self) == 0:
            return None
        else:
            raise TypeError('Ambiguous: agent contains multiple children')

    @property
    def names(self) -> frozenset:
        return self._attrs('names')

    def free_names(self, bindings: frozenset = frozenset()) -> frozenset:
        return self.names - bindings


class Name(str):

    def __new__(cls, *args):
        ret = super().__new__(cls, *args)
        return ret

    def __copy__(self):
        return type(self)(self)

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
