#! /usr/bin/env python3

import base
from base import Agent, Name
from base import typefilter


class Replication(base.Replication):

    def __new__(typ, agent: Agent) -> base.Replication:
        obj = super().__new__(typ, frozenset({agent}))
        return obj


    def __str__(self) -> str:
        return '!%s' % self.agent


    def reduce(self, bindings: frozenset = frozenset()) -> Agent:
        # Reduction cannot be performed directly inside a replicator
        agent = self.agent

        # NOTE: !(!(P)) == !(P)
        while isinstance(agent, Replication):
            agent = agent.agent

        # NOTE: !(x)(P | !Q) -> (u)(!(x)(P | uz) | !(w)(uw | Q{w/z}))
        #       Flattening Theorem
        for (s, c, r) in ((s, c, r)
                          for s in typefilter(base.Scope, {agent})
                          for c in typefilter(base.Composition, s)
                          for r in typefilter(Replication, c)):
            z = tuple(sorted(r.free_names(bindings | s.bindings)))
            P = c - {r}
            Q = r.agent
            u = Name.fresh(self.names | bindings, 'u')
            ws = frozenset()
            for _ in z:
                ws |= {Name.fresh(self.names | bindings | frozenset(ws), 'w')}
            wt = tuple(ws)
            Io, _ = base.Solo.types
            Prep = base.Scope(s.bindings,
                              base.Composition({P, Io(u, z)}))
            Qrep = base.Match(base.Scope(ws, base.Composition({Io.inverse(u, wt), Q})), 
                              dict(zip(z, wt)))
            return base.Scope({u}, base.Composition({Replication(Prep.reduce(bindings)), 
                                                     Replication(Qrep.reduce(bindings))}))

        if agent:
            return Replication(agent)
        else:
            return base.Inaction()


    def match(self, matches: dict, bindings: frozenset) -> Agent:
        return type(self)(self.agent.match(matches, bindings))

    
    @classmethod
    def id(cls, agent: Agent) -> Agent:
        # This is the best we can do...
        return None



base.Replication = Replication