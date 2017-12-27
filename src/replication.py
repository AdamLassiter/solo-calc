#! /usr/bin/env python3

import base
from base import Agent, Name
from base import typefilter


class Replication(base.Replication):

    def __init__(self, agent: Agent) -> None:
        super().__init__()
        self.agent = agent


    def __str__(self) -> str:
        return '!%s' % self.agent


    def reduce(self, matches: dict = {}) -> Agent:
        # FIXME: Should this reduce?
        # Reduction inside of a replication is shaky
        agent = self.agent

        # NOTE: !(!(P)) == !(P)
        if isinstance(agent, Replication):
            agent = agent.agent

        # NOTE: !(x)(P | !Q) -> (u)(!(x)(P | uz) | !(w)(uw | Q{w/z}))
        #       Flattening Theorem
        for (s, c, r) in ((s, c, r)
                          for s in typefilter(base.Scope, {agent})
                          for c in typefilter(base.Composition, s.agents)
                          for r in typefilter(Replication, c.agents)):
            P = base.Composition(c.agents - {r})
            Q = r.agent
            z = tuple(sorted(Q.free_names))
            u = Name.fresh(self.names, 'u')
            ws = frozenset()
            for _ in z:
                ws |= {Name.fresh(self.names | frozenset(ws), 'w')}
            wt = tuple(ws)
            Io, _ = base.Solo.types
            Prep = base.Scope(s.bindings,
                              base.Composition(frozenset({P, Io(u, z)})))
            Qrep = base.Composition(frozenset({base.Scope(ws, Io.inverse(u, wt)),
                                               base.Match(base.Scope(ws, Q),
                                                          dict(zip(wt,z)))}))
            return base.Scope(frozenset({u}),
                              base.Composition(frozenset({Replication(Prep.reduce(matches)), 
                                                          Replication(Qrep.reduce(matches))})))

        if agent:
            return Replication(agent)
        else:
            return base.Inaction()

    
    @staticmethod
    def id(agent: Agent) -> Agent:
        # This is the best we can do...
        return None
 

base.Replication = Replication
