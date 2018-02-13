#! /usr/bin/env python3

import base
from base import Agent
from base import typefilter


class Composition(base.Composition):
    
    def __init__(self, agents: frozenset) -> None:
        super().__init__()
        for agent in agents:
            assert isinstance(agent, Agent)


    def __str__(self) -> str:
        return '(%s)' % (' | '.join(map(str, self)))


    def __sub__(self, other: frozenset) -> base.Composition:
        if not isinstance(other, type(self)):
            other = type(self)(other)
        ret = type(self)(super().__sub__(other))
        return ret


    def reduce(self, matches: dict = {}, bindings: frozenset = frozenset()) -> Agent:
        agents = frozenset(agent.reduce(matches, bindings) for agent in self)
        rescope = frozenset()

        # NOTE: ((x)P | Q) -> (x)(P | Q)
        for sagent in typefilter(base.Scope, agents):
            rescope |= sagent.bindings - self.free_names(bindings)
            sagent.bindings &= self.free_names(bindings)
            if not sagent.bindings:
                agents -= {sagent}
                agents |= sagent

        # NOTE: (0 | P) -> P
        agents -= typefilter(base.Inaction, agents)

        # NOTE: ((a | b) | c) == (a | (b | c)) -> (a | b | c)
        for cagent in typefilter(Composition, agents):
            agents -= {cagent}
            agents |= cagent

        if rescope:
            return base.Scope(rescope, Composition(agents))
        if len(agents) > 1:
            return Composition(agents)
        elif len(agents) == 1:
            agent, = agents
            return agent
        else:
            return base.Inaction()


    @classmethod
    def id(cls, agent: Agent) -> Agent:
        return cls(frozenset({agent}))
 

base.Composition = Composition
