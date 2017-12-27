#! /usr/bin/env python3

import base
from base import Agent, Name
from base import typefilter
from graph import Graph


class Scope(base.Scope):

    def __init__(self, bindings: frozenset, agent: Agent) -> None:
        super().__init__()

        for binding in bindings:
            assert isinstance(binding, Name)

        self.bindings = bindings
        self.agent = agent


    def __str__(self) -> str:
        return '(%s)%s' % (' '.join(map(str, self.bindings)), self.agent)


    def construct_sigma(self, iagent: Agent, oagent: Agent) -> dict:
        # NOTE: Graph partitioning > naive pairwise cases for intersection
        graph = Graph()
        sigma = dict()
        for pair in zip(iagent.objects, oagent.objects):
            graph.insert_edge(*pair)

        for partition in graph.partitions():
            intersect = (iagent.free_names & oagent.free_names) & partition
            assert len(intersect) <= 1
            if len(intersect) == 0:
                free_name = Name.fresh(self.names, 'u')
            else:
                free_name, = intersect
            for bound_name in partition - {free_name}:
                sigma[bound_name] = free_name

        return sigma


    def outer_outer(self, c: base.Composition, i: base.Solo, o: base.Solo) -> Agent:
        bindings = self.bindings
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse):
            P = base.Composition(c.agents - {i, o})
            sigma = self.construct_sigma(i, o)
            return base.Match(Scope(bindings, P), sigma)
        else:
            return None


    def outer_inner(self, c: base.Composition, i: base.Solo, r: Agent, s: Agent,
                    c1: base.Composition, o: base.Solo) -> Agent:
        bindings = self.bindings
        self.freeze = True
        P = base.Composition(c.agents - {i, r})
        Q = base.Composition(c1.agents - {o})
        if i.subject == o.subject and i.arity == o.arity \
        and isinstance(i, o.inverse) and o.subject not in s.bindings \
        and not s.bindings & P.free_names - bindings:
            sigma = self.construct_sigma(i, o)
            if bindings <= sigma.keys() <= bindings | s.bindings:
                ret = base.Match(Scope(s.bindings | bindings, base.Composition({P, Q, r})), sigma)
                ret.freeze = False
            else:
                ret = None
        else:
            ret = None
        self.freeze = False
        return ret


    def inner_inner(self, c: base.Composition, r1: Agent, s1: Agent, c1: base.Composition,
                    i: base.Solo, r2: Agent, s2: Agent, c2: base.Composition,
                    o: base.Solo) -> Agent:
        bindings = self.bindings
        self.freeze = True
        P = base.Composition(c.agents - {r1, r2})
        Q = base.Composition(c1.agents - {i})
        R = base.Composition(c2.agents - {o})
        binds = s1.bindings | s2.bindings
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse) \
        and i.subject not in s1.bindings | s2.bindings \
        and not binds & P.free_names - bindings \
        and not s1.bindings & R.free_names - bindings \
        and not s2.bindings & Q.free_names - bindings:
            sigma = self.construct_sigma(i, o)
            assert bindings <= sigma.keys() <= bindings | binds
            ret =  base.Match(Scope(binds, base.Composition({P, Q, R, r1, r2})), sigma)
            ret.freeze = False
        else:
            ret = None
        self.freeze = False
        return ret


    def inner_fusion(self, c: base.Composition, r: Agent, s: Agent, c1: base.Composition,
                     i: base.Solo, o: base.Solo) -> Agent:
        bindings = self.bindings
        P = base.Composition(c.agents - {r})
        Q = base.Composition(c1.agents - {i, o})
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse):
            sigma = self.construct_sigma(i, o)
            assert bindings <= sigma.keys() <= bindings | s.bindings
            return base.Match(Scope(s.bindings, base.Composition({P, Q, r})), sigma)
        else:
            return None


    def reduce(self, matches: dict = {}) -> Agent:
        agent = self.reduction = self.agent.reduce(matches)
        bindings = self.bindings

        # NOTE: (x)(y)(P) == (xy)(P)
        if isinstance(agent, Scope):
            bindings |= agent.bindings
            agent = self.reduction = agent.agent

        # NOTE: ()(P) == P
        if not bindings:
            return agent.reduce(matches)
 
        for Io in base.Solo.types:

            # NOTE: (z)(̅u x | u y | P) -> Pσ
            for agents in ((c, i, o)
                           for c in typefilter(base.Composition, {agent})
                           for i in typefilter(Io, c.agents)
                           for o in typefilter(Io.inverse, c.agents)):
                ret = self.outer_outer(*agents)
                if ret:
                    return ret

            # NOTE: (z)(P | !(w)(̅u x | u y | Q)) ->
            #       (w)(P | Q |  !(w)(̅u x | u y | Q))σ
            for agents in ((c, r, s, c1, i, o)
                           for c in typefilter(base.Composition, {agent})
                           for r in typefilter(base.Replication, c.agents)
                           for s in typefilter(Scope, r.agents)
                           for c1 in typefilter(base.Composition, s.agents)
                           for i in typefilter(Io, c1.agents)
                           for o in typefilter(Io.inverse, c1.agents)):
                ret = self.inner_fusion(*agents)
                if ret:
                    return ret

            # NOTE: (z)(P | !(v)(u x | Q) | !(w)(̅u x | R)) ->
            #       (vw)(P | Q | R | !(v)(u x | Q) | !(w)(̅u x | R))σ
            for agents in ((c, r1, s1, c1, i, r2, s2, c2, o)
                           for c in typefilter(base.Composition, {agent})
                           for r1 in typefilter(base.Replication, agent.agents)
                           for s1 in typefilter(Scope, r1.agents)
                           for c1 in typefilter(base.Composition, s1.agents)
                           for i in typefilter(Io, c1.agents)
                           for r2 in typefilter(base.Replication, agent.agents - {r1})
                           for s2 in typefilter(Scope, r2.agents)
                           for c2 in typefilter(base.Composition, s2.agents)
                           for o in typefilter(Io.inverse, c2.agents)):
                ret = self.inner_inner(*agents)
                if ret:
                    return ret

            # NOTE: (z)(̅u x | !(w)(u x | Q) | P) -> (w)(P | Q | !(w)(u x | Q)σ
            for agents in ((c, i, r, s, c1, o)
                           for c in typefilter(base.Composition, {agent})
                           for i in typefilter(Io, agent.agents)
                           for r in typefilter(base.Replication, agent.agents)
                           for s in typefilter(Scope, r.agents)
                           for c1 in typefilter(base.Composition, s.agents)
                           for o in typefilter(Io.inverse, c1.agents)):
                ret = self.outer_inner(*agents)
                if ret:
                    return ret
    
        if bindings:
            return Scope(bindings, agent)
        elif agent:
            return agent
        else:
            return base.Inaction()


    @staticmethod
    def id(agent: Agent) -> Agent:
        return Scope(frozenset(), agent)


    @property
    def bound_names(self) -> frozenset:
        return self._bound_names | self._bindings


    @bound_names.setter
    def bound_names(self, value: frozenset):
        self._bound_names = value


    @property
    def bindings(self) -> frozenset:
        return self._bindings


    @bindings.setter
    @base._rebind
    def bindings(self, value: frozenset) -> None:
        self._bindings = value


base.Scope = Scope
