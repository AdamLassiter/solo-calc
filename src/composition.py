#! /usr/bin/env python3

import base
from base import Agent
from base import typefilter


class Composition(base.Composition):

    def __init__(self, agents: frozenset) -> None:
        super().__init__()

        for agent in agents:
            assert isinstance(agent, Agent)

        self.agents = agents


    def __str__(self) -> str:
        return '(%s)' % (' | '.join(map(str, self.agents)))


    def reduce(self, matches: dict = {}) -> Agent:
        agents = frozenset(agent.reduce(matches) for agent in self.agents)
        rescope = frozenset()

        # NOTE: ((a | b) | c) == (a | (b | c)) -> (a | b | c)
        for cagent in typefilter(Composition, agents):
            agents -= {cagent}
            agents |= cagent.agents

        # NOTE: (0 | P) -> P
        agents -= typefilter(base.Inaction, agents)

        # NOTE: ((x)P | Q) -> (x)(P | Q)
        for sagent in typefilter(base.Scope, agents):
            rescope |= sagent.bindings - self.free_names
            sagent.bindings &= self.free_names
            if not sagent.bindings:
                agents -= {sagent}
                agents |= {sagent.agent}

        if rescope:
            return base.Scope(rescope, Composition(agents))
        if len(agents) > 1:
            return Composition(agents)
        elif len(agents) == 1:
            agent, = agents
            return agent
        else:
            return base.Inaction()
 

base.Composition = Composition
