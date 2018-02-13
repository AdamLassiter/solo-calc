#! /usr/bin/env python3

import base
from base import Agent, Name
from base import typefilter


class Scope(base.Scope):

    def __new__(typ, bindings: frozenset, agent: Agent) -> base.Scope:
        obj = super().__new__(typ, frozenset({agent}))
        obj.bindings = bindings
        return obj


    def __init__(self, bindings: frozenset, agent: Agent) -> None:
        super().__init__()
        for binding in bindings:
            assert isinstance(binding, Name)
    
    
    def eq(self, other: Agent, self_bindings: frozenset, other_bindings: frozenset) -> frozenset:
        return super().eq(other, self_bindings | self.bindings,
                          other_bindings | getattr(other, 'bindings', frozenset()))


    def __str__(self) -> str:
        return '(%s)%s' % (' '.join(map(str, self.bindings)), self.agent)


    def outer_outer(self, bindings: frozenset, c: base.Composition, i: base.Solo,
                    o: base.Solo) -> Agent:
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse):
            sigma = self.construct_sigma(bindings, i, o)
            P = base.Composition(c - {i, o})
            return base.Match(Scope(bindings, P), sigma)
        else:
            return None


    def outer_inner(self, bindings: frozenset, c: base.Composition, i: base.Solo, r: Agent,
                    s: Agent, c1: base.Composition, o: base.Solo) -> Agent:
        P = base.Composition(c - {i, r})
        Q = base.Composition(c1 - {o})
        if i.subject == o.subject and i.arity == o.arity \
        and isinstance(i, o.inverse) and o.subject not in s.bindings \
        and not s.bindings & P.free_names(bindings) - bindings:
            sigma = self.construct_sigma(bindings | s.bindings, i, o)
            if bindings <= sigma.keys() <= bindings | s.bindings:
                return base.Match(Scope(bindings | s.bindings, base.Composition({P, Q, r})), sigma)
            else:
                return None
        else:
            return None


    def inner_inner(self, bindings: frozenset, c: base.Composition, r1: Agent, s1: Agent,
                    c1: base.Composition, i: base.Solo, r2: Agent, s2: Agent, c2: base.Composition,
                    o: base.Solo) -> Agent:
        P = base.Composition(c - {r1, r2})
        Q = base.Composition(c1 - {i})
        R = base.Composition(c2 - {o})
        inner_bindings = s1.bindings | s2.bindings # | bindings?
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse) \
        and i.subject not in s1.bindings | s2.bindings \
        and not inner_bindings & P.free_names(bindings) - bindings \
        and not s1.bindings & R.free_names(bindings | s1.bindings) - bindings \
        and not s2.bindings & Q.free_names(bindings | s2.bindings) - bindings:
            sigma = self.construct_sigma(bindings | inner_bindings, i, o)
            if bindings <= sigma.keys() <= bindings | inner_bindings:
                return base.Match(Scope(inner_bindings, base.Composition({P, Q, R, r1, r2})), sigma)
            else:
                return None
        else:
            return None


    def inner_fusion(self, bindings: frozenset, c: base.Composition, r: Agent, s: Agent,
                     c1: base.Composition, i: base.Solo, o: base.Solo) -> Agent:
        P = base.Composition(c - {r})
        Q = base.Composition(c1 - {i, o})
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse):
            sigma = self.construct_sigma(bindings | s.bindings, i, o)
            if bindings <= sigma.keys() <= bindings | s.bindings:
                return base.Match(Scope(s.bindings, base.Composition({P, Q, r})), sigma)
            else:
                return None
        else:
            return None


    def reduce(self, matches: dict = {}, bindings: frozenset = frozenset()) -> Agent:
        agent = self.agent.reduce(matches, bindings)
        sigma_bindings = frozenset(map(lambda x: matches.get(x, x), self.bindings))
        new_bindings = sigma_bindings - self.free_names(bindings)

        # NOTE: (x)(y)(P) == (xy)(P)
        if isinstance(agent, Scope):
            new_bindings |= agent.bindings
            agent = agent.agent

        # NOTE: ()(P) == P
        if not new_bindings:
            return agent.reduce(matches, bindings)
 
        for Io in base.Solo.types:

            # NOTE: (z)(̅u x | u y | P) -> Pσ
            for agents in ((c, i, o)
                           for c in typefilter(base.Composition, {agent})
                           for i in typefilter(Io, c)
                           for o in typefilter(Io.inverse, c)):
                ret = self.outer_outer(new_bindings | bindings, *agents)
                if ret:
                    return ret

            # NOTE: (z)(P | !(w)(̅u x | u y | Q)) ->
            #       (w)(P | Q |  !(w)(̅u x | u y | Q))σ
            for agents in ((c, r, s, c1, i, o)
                           for c in typefilter(base.Composition, {agent})
                           for r in typefilter(base.Replication, c)
                           for s in typefilter(Scope, r)
                           for c1 in typefilter(base.Composition, s)
                           for i in typefilter(Io, c1)
                           for o in typefilter(Io.inverse, c1)):
                ret = self.inner_fusion(new_bindings | bindings, *agents)
                if ret:
                    return ret

            # NOTE: (z)(P | !(v)(u x | Q) | !(w)(̅u x | R)) ->
            #       (vw)(P | Q | R | !(v)(u x | Q) | !(w)(̅u x | R))σ
            for agents in ((c, r1, s1, c1, i, r2, s2, c2, o)
                           for c in typefilter(base.Composition, {agent})
                           for r1 in typefilter(base.Replication, agent)
                           for s1 in typefilter(Scope, r1)
                           for c1 in typefilter(base.Composition, s1)
                           for i in typefilter(Io, c1)
                           for r2 in typefilter(base.Replication, agent - {r1})
                           for s2 in typefilter(Scope, r2)
                           for c2 in typefilter(base.Composition, s2)
                           for o in typefilter(Io.inverse, c2)):
                ret = self.inner_inner(new_bindings | bindings, *agents)
                if ret:
                    return ret

            # NOTE: (z)(̅u x | !(w)(u x | Q) | P) -> (w)(P | Q | !(w)(u x | Q)σ
            for agents in ((c, i, r, s, c1, o)
                           for c in typefilter(base.Composition, {agent})
                           for i in typefilter(Io, agent)
                           for r in typefilter(base.Replication, agent)
                           for s in typefilter(Scope, r)
                           for c1 in typefilter(base.Composition, s)
                           for o in typefilter(Io.inverse, c1)):
                ret = self.outer_inner(new_bindings | bindings, *agents)
                if ret:
                    return ret
        
        if new_bindings:
            return Scope(new_bindings, agent)
        elif agent:
            return agent
        else:
            return base.Inaction()


    def free_names(self, bindings: frozenset) -> frozenset:
        return super().free_names(bindings | self.bindings)


    @classmethod
    def id(cls, agent: Agent) -> Agent:
        return cls(frozenset(), agent)



base.Scope = Scope
