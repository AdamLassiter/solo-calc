#! /usr/bin/env python3

import base
from base import Agent, Name, Solo
from base import typefilter
from graph import Graph


class Scope(base.Scope):

    def __init__(self, bindings: set, agent: Agent) -> None:
        for binding in bindings:
            assert isinstance(binding, Name)

        self.bindings = bindings
        self.agent = agent


    def __str__(self) -> str:
        return '(%s)%s' % (' '.join(map(str, self.bindings)), self.agent)


    def construct_sigma(self, iagent: Agent, oagent: Agent) -> dict:
        # NOTE: Graph partitioning > naive pairwise cases for intersection
        graph = Graph()
        sigma = {}
        for pair in zip(iagent.objects, oagent.objects):
            graph.insert_edge(*pair)
        
        for partition in graph.partitions():
            intersect = self.free_names & partition
            assert len(intersect) <= 1
            if len(intersect) == 0:
                free_name = set(partition).pop()
            else:
                free_name = intersect.pop()
            for bound_name in set(partition) - {free_name}:
                sigma[bound_name] = free_name

        return sigma


    def outer_outer(self, i: Solo, o: Solo) -> Agent:
        agent, bindings = self.agent, self.bindings
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse):
            sigma = self.construct_sigma(i, o)
            agent.agents -= {i, o}
            if not agent.agents:
                agent.agents |= {base.Inaction()}
            if len(agent.agents) == 1:
                agent = agent.agents.pop()
            return base.Match(Scope(bindings, agent), sigma)
        else:
            return None


    def outer_inner(self, i: Solo, r: Agent, s: Agent, c: base.Composition, o: Solo) -> Agent:
        agent, bindings = self.agent, self.bindings
        P = base.Composition(agent.agents - {i, r})
        Q = base.Composition(c.agents - {o})
        if i.subject == o.subject \
        and i.arity == o.arity and o.subject not in s.bindings \
        and s.bindings & P.free_names == set():
            sigma = self.construct_sigma(i, o)
            assert bindings <= sigma.keys() <= bindings | s.bindings
            return base.Match(Scope(s.bindings, base.Composition({P, Q, r})), sigma)
        else:
            return None


    def inner_inner(self, r1: Agent, s1: Agent, c1: base.Composition, i: Solo,
                    r2: Agent, s2: Agent, c2: base.Composition, o: Solo) -> Agent:
        agent, bindings = self.agent, self.bindings
        P = base.Composition(agent.agents - {r1, r2})
        Q = base.Composition(c1.agents - {i})
        R = base.Composition(c2.agents - {o})
        binds = s1.bindings | s2.bindings
        if i.subject == o.subject and i.arity == o.arity \
        and o.subject not in s1.bindings | s2.bindings \
        and binds & P.free_names == set() \
        and s1.bindings & R.free_names == s2.bindings & Q.free_names == set():
            sigma = self.construct_sigma(i, o)
            assert bindings <= sigma.keys() <= bindings | binds
            return base.Match(Scope(binds, base.Composition({P, Q, R, r1, r2})), sigma)
        else:
            return None


    def inner_fusion(self, r: Agent, s: Agent, c: base.Composition,
                     i: Solo, o: Solo) -> Agent:
        agent, bindings = self.agent, self.bindings
        P = base.Composition(agent.agents - {r})
        Q = base.Composition(c.agents - {i, o})
        if i.subject == o.subject and i.arity == o.arity:
            sigma = self.construct_sigma(i, o)
            assert bindings <= sigma.keys() <= bindings | s.bindings
            return base.Match(Scope(s.bindings, base.Composition({P, Q, r})), sigma)
        else:
            return None


    def reduce(self):
        agent = self.agent = self.agent.reduce()
        bindings = self.bindings
        
        # NOTE: (x)(y)(P) == (xy)(P)
        if isinstance(agent, Scope):
            bindings |= agent.bindings
            agent = agent.agent

        if isinstance(agent, base.Composition):
 
            for Io in Solo.types:

                # NOTE: (z)(̅u x | u y | P) -> Pσ
                for iagent in typefilter(Io, agent.agents):
                    for oagent in typefilter(Io.inverse, agent.agents):
                        ret = self.outer_outer(iagent, oagent)
                        if ret:
                            return ret

                # NOTE: (z)(P | !(v)(u x | Q) | !(w)(̅u x | R)) ->
                #       (vw)(P | Q | R | !(v)(u x | Q) | !(w)(̅u x | R))σ
                for agents in ((r1, s1, c1, i, r2, s2, c2, o)
                               for r1 in typefilter(base.Replication, agent.agents)
                               for s1 in typefilter(Scope, {r1.agent})
                               for c1 in typefilter(base.Composition, {s1.agent})
                               for i in typefilter(Io, c1.agents)
                               for r2 in typefilter(base.Replication, agent.agents - {r1})
                               for s2 in typefilter(Scope, {r2.agent})
                               for c2 in typefilter(base.Composition, {s2.agent})
                               for o in typefilter(Io.inverse, c2.agents)):
                    ret = self.inner_inner(*agents)
                    if ret:
                        return ret

                # NOTE: (z)(P | !(w)(̅u y | u x | Q)) ->
                #       (w)(P | Q |  !(w)(̅u y | u x | Q))σ
                for agents in ((r, s, c, i, o)
                               for r in typefilter(base.Replication, agent.agents)
                               for s in typefilter(Scope, {r.agent})
                               for c in typefilter(base.Composition, {s.agent})
                               for i in typefilter(Io, c.agents)
                               for o in typefilter(Io.inverse, c.agents)):
                    ret = self.inner_fusion(*agents)
                    if ret:
                        return ret
                
                # NOTE: (z)(̅u x | !(w)(u x | Q) | P) -> (w)(P | Q | !(w)(u x | Q)σ
                for i in typefilter(Io, agent.agents):
                    for r in typefilter(base.Replication, agent.agents):
                        for s in typefilter(Scope, {r.agent}):
                            for c in typefilter(base.Composition, {s.agent}):
                                for o in typefilter(Io.inverse, c.agents):
                                    ret = self.outer_inner(i, r, s, c, o)
                                    if ret:
                                        return ret
               
        return Scope(bindings, agent)


    @property
    def agents(self) -> set:
        return {self.agent}


    @property
    def names(self) -> set:
        return self.bindings | self.agent.names


    @property
    def bound_names(self) -> set:
        return self.bindings | self.agent.bound_names


base.Scope = Scope
