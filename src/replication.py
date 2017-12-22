#! /usr/bin/env python3

from calculus import Agent, Name, Solo, Scope, Composition, Match, Replication as BaseClass
from calculus import typefilter


class Replication(BaseClass):

    def __init__(self, agent: Agent) -> None:
        self.agent = agent


    def __str__(self) -> str:
        return '!(%s)' % self.agent


    def reduce(self):
        # FIXME: Should this be here?
        # Reduction inside of a replication is shaky
        agent = self.agent.reduce()

        # NOTE: !(!(P)) == !(P)
        if isinstance(agent, Replication):
            agent = agent.agent

        # NOTE: !(x)(P | !Q) -> (u)(!(x)(P | uz) | !(w)(uw | Q{w/z}))
        #       Flattening Theorem
        if isinstance(agent, Scope) and isinstance(agent.agent, Composition) \
        and typefilter(Replication, agent.agent.agents) != set():
            P, xs = agent.agent, agent.bindings
            Q = Composition(typefilter(Replication, P.agents))
            P.agents -= Q.agents
            z = tuple(sorted(Q.free_names, key=lambda x: x.name))
            u = Name.fresh(self.names, 'u')
            ws = []
            for _ in z:
                ws += [Name.fresh(self.names | set(ws), 'w')]
            Io, = Solo.types
            Prep = Replication(Scope(xs, Composition({P, Io(u, z)})))
            Qrep = Match(Scope(set(ws), Composition({Q, Io.inverse(u, ws)})), dict(zip(ws, z)))
            return Scope({u}, Composition({Prep, Qrep}))

        return type(self)(agent)


    @property
    def agents(self) -> set:
        return {self.agent}


    @property
    def names(self) -> set:
        return self.agent.names


    @property
    def bound_names(self) -> set:
        return self.agent.bound_names

