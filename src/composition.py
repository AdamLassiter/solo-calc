#! /usr/bin/env python3

from functools import reduce

import base
from base import Agent
from base import typefilter


class Composition(base.Composition):

    def __init__(self, agents: set) -> None:
        for agent in agents:
            assert isinstance(agent, Agent)

        self._agents = agents


    def __str__(self) -> str:
        return '(%s)' % (' | '.join(map(str, self._agents)))


    def reduce(self) -> Agent:
        agents = set()
        rescope = set()

        # NOTE: ((a | b) | c) == (a | (b | c)) -> (a | b | c)
        for agent in map(lambda x: x.reduce(), self._agents):
            if isinstance(agent, Composition):
                agents |= agent.agents
            else:
                agents |= {agent}

        # NOTE: ((x)P | Q) -> (x)(P | Q)
        for sagent in typefilter(base.Scope, agents):
            rescope |= sagent.bindings - self.free_names
            sagent.bindings &= self.free_names
            if not sagent.bindings:
                agents -= {sagent}
                agents |= {sagent.agent}

        return base.Scope(rescope, Composition(agents)) if rescope else Composition(agents)


    @staticmethod
    def _attrs(s: set, attr: str) -> set:
        return set(reduce(set.union,
                          map(lambda x: frozenset(getattr(x, attr)), s),
                          set()))


    @property
    def agents(self) -> set:
        return self._agents


    @agents.setter
    def agents(self, value: set):
        self._agents = value


    @property
    def names(self) -> set:
        return self._attrs(self._agents, 'names')


    @property
    def bound_names(self) -> set:
        return self._attrs(self._agents, 'bound_names')


base.Composition = Composition
