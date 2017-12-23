#! /usr/bin/env python3

import base
from base import Agent, Name
from base import typefilter


class Replication(base.Replication):

    def __init__(self, agent: Agent) -> None:
        super().__init__()
        self.agent = agent


    def __str__(self) -> str:
        return '!(%s)' % self.agent


    def reduce(self):
        # FIXME: Should this reduce?
        # Reduction inside of a replication is shaky
        agent = self.agent

        # NOTE: !(!(P)) == !(P)
        if isinstance(agent, Replication):
            agent = agent.agent

        # NOTE: !(x)(P | !Q) -> (u)(!(x)(P | uz) | !(w)(uw | Q{w/z}))
        #       Flattening Theorem
        if isinstance(agent, base.Scope) and isinstance(agent.agent, base.Composition) \
        and typefilter(Replication, agent.agent.agents) != set():
            P, xs = agent.agent, agent.bindings
            Q = base.Composition(typefilter(Replication, P.agents))
            P.agents -= Q.agents
            z = tuple(sorted(Q.free_names, key=lambda x: x.name))
            u = Name.fresh(self.names, 'u')
            ws = []
            for _ in z:
                ws += [Name.fresh(self.names | set(ws), 'w')]
            Io, = base.Solo.types
            Prep = Replication(base.Scope(xs, base.Composition({P, Io(u, z)})))
            Qrep = base.Match(base.Scope(set(ws), base.Composition({Q, Io.inverse(u, ws)})), dict(zip(ws, z)))
            return base.Scope({u}, base.Composition({Prep, Qrep}))
        
        if agent:
            return Replication(agent)
        else:
            return base.Inaction()
 

base.Replication = Replication
