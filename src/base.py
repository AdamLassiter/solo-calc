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
        * Grouping nested operators of the same type
        * Extracting scopes where applicable ((x)P | Q) -> (x)(P | Q) if x ∉ fn(Q)
            TODO: should this be this way? or should scopes go inwards?
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


class Agent(object):
    
    def reduce(self):
        raise NotImplementedError

    @staticmethod
    def id(self, agents: set) -> set:
        raise NotImplementedError

    @property
    def agents(self) -> set:
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
        return self.name == other.name

    def fuse_into(self, other):
        assert isinstance(other, type(self))
        fusions = self.fusions | other.fusions
        for name in fusions:
            name.fusions = fusions - {name}
            name.name = other.name

    @classmethod
    def fresh(cls, names: set, name_hint: str):
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

