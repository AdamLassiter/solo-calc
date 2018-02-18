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
                    o: base.Solo) -> base.Match:
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse):
            P = base.Composition(c - {i, o})
            sigmas = self.construct_sigma(bindings, i, o)
            for sigma in sigmas:
                return base.Match(P, sigma)
        return None


    def outer_inner(self, bindings: frozenset, c: base.Composition, i: base.Solo,
                    r: base.Replication, s: base.Scope, c1: base.Composition,
                    o: base.Solo) -> base.Match:
        P = base.Composition(c - {i, r})
        Q = base.Composition(c1 - {o})
        if i.subject == o.subject and i.arity == o.arity \
        and isinstance(i, o.inverse) and o.subject not in s.bindings \
        and not s.bindings & P.free_names(bindings) - bindings:
            sigmas = self.construct_sigma(bindings | s.bindings, i, o)
            for sigma in sigmas:
                if bindings <= sigma.keys() <= bindings | s.bindings:
                    inner_bindings = s.bindings
                    return base.Match(Scope(inner_bindings,
                                            base.Composition({P, Q, r})),
                                      sigma)
        return None


    def inner_inner(self, bindings: frozenset, c: base.Composition, r1: base.Replication,
                    s1: base.Scope, c1: base.Composition, i: base.Solo, r2: base.Replication,
                    s2: base.Scope, c2: base.Composition, o: base.Solo) -> base.Match:
        P = base.Composition(c - {r1, r2})
        Q = base.Composition(c1 - {i})
        R = base.Composition(c2 - {o})
        inner_bindings = s1.bindings | s2.bindings
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse) \
        and i.subject not in s1.bindings | s2.bindings \
        and not inner_bindings & P.free_names(bindings) - bindings \
        and not s1.bindings & R.free_names(bindings | s1.bindings) - bindings \
        and not s2.bindings & Q.free_names(bindings | s2.bindings) - bindings:
            sigmas = self.construct_sigma(bindings | inner_bindings, i, o)
            for sigma in sigmas:
                if sigma.keys() <= bindings | inner_bindings:
                    return base.Match(base.Scope(inner_bindings,
                                                 base.Composition({P, Q, R, r1, r2})),
                                      sigma)
        return None


    def inner_fusion(self, bindings: frozenset, c: base.Composition, r: base.Replication,
                     s: base.Scope, c1: base.Composition, i: base.Solo,
                     o: base.Solo) -> base.Match:
        P = base.Composition(c - {r})
        Q = base.Composition(c1 - {i, o})
        if i.subject == o.subject and i.arity == o.arity and isinstance(i, o.inverse):
            sigmas = self.construct_sigma(bindings | s.bindings, i, o)
            for sigma in sigmas:
                if bindings <= sigma.keys() <= bindings | s.bindings:
                    inner_bindings = s.bindings | (self.bindings & set(sigma.values()))
                    return base.Match(Scope(inner_bindings,
                                        base.Composition({P, Q, r})),
                                  sigma)
        return None


    def attempt_fusion(self, agent: Agent, all_bindings: frozenset) -> base.Match:
        for Io in base.Solo.types:

            # NOTE: (z)(̅u x | u y | P) -> Pσ
            for agents in ((c, i, o)
                           for c in typefilter(base.Composition, {agent})
                           for i in typefilter(Io, c)
                           for o in typefilter(Io.inverse, c)):
                ret = self.outer_outer(all_bindings, *agents)
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
                ret = self.inner_fusion(all_bindings, *agents)
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
                ret = self.inner_inner(all_bindings, *agents)
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
                ret = self.outer_inner(all_bindings, *agents)
                if ret:
                    return ret

        return None


    def reduce(self, bindings: frozenset = frozenset()) -> Agent:
        my_bindings = self.bindings
        agent = self.agent.reduce(my_bindings | bindings)

        # NOTE: (x)(y)(P) == (xy)(P)
        if isinstance(agent, Scope):
            my_bindings |= agent.bindings
            agent = agent.agent

        # NOTE: ()(P) == P and (x)y == y
        my_bindings &= agent.names
        if not my_bindings:
            return agent

        reduction = self.attempt_fusion(agent, my_bindings | bindings)
        if reduction is not None:
            return Scope(my_bindings, reduction)

        if agent:
            return Scope(my_bindings, agent)
        else:
            return base.Inaction()


    def match(self, matches: dict, bindings: frozenset) -> Agent:
        matches = dict(matches)
        # Stop matching if name is scoped again ( (x)(P | (x)Q) )
        for name in self.bindings & bindings:
            if name in matches.keys():
                del matches[name]
            if name in matches.values():
                for key in {key for key in matches.keys() if matches[key] == name}:
                    del matches[key]
        # Otherwise, as expected, rename variables just scoped
        return type(self)(frozenset({matches.get(x, x) for x in self.bindings}),
                          self.agent.match(matches, bindings | self.bindings))


    def free_names(self, bindings: frozenset) -> frozenset:
        return super().free_names(bindings | self.bindings)


    @classmethod
    def id(cls, agent: Agent) -> Agent:
        return cls(frozenset(), agent)



base.Scope = Scope
