#! /usr/bin/env python3

from __future__ import annotations
from functools import reduce
from itertools import count
from string import digits
from typing import Iterator, Iterable, List, Tuple, TypeVar, Union, FrozenSet as Set

from multiset import FrozenMultiset as multiset

from graph import graph

mutableset, set = set, frozenset


def fresh_name(working_set: Set[str], name_hints: List[str] = ['u']) -> List[str]:
    names: List[str] = []
    for name_hint in name_hints:
        name_hint = name_hint.rstrip(digits)
        for name in (str(name_hint + str(i)) for i in count()):
            if name not in working_set | set(names):
                names += [name]
                break
    return names



class Agent:

    def __str__(self) -> str:
        raise NotImplementedError

    
    def equals(self, other) -> bool:
        raise NotImplementedError


    def flatten(self) -> Agent:
        raise NotImplementedError


    def reduce(self) -> Agent:
        return self


    @property
    def names(self) -> Set[str]:
        raise NotImplementedError


    @property
    def bound_names(self) -> Set[str]:
        raise NotImplementedError


    @property
    def free_names(self) -> Set[str]:
        return self.names - self.bound_names



class Scope(Agent):

    def __init__(self, child: Agent, scope: Set[str]) -> None:
        self.child = child
        self.scope = scope


    def __str__(self) -> str:
        return '(%s)%s' % (' '.join(self.scope), str(self.child))


    def flatten(self) -> Scope:
        child = self.child.flatten()
        if isinstance(child, Scope):
            return type(self)(child.child,
                              self.scope | child.scope)
        elif isinstance(child, (Replication, Solo)):
            return type(self)(Composition(set({child})), self.scope)
        else:
            assert isinstance(child, Composition)
            return type(self)(child, self.scope)


    @property
    def names(self) -> Set[str]:
        return self.scope | self.child.names


    @property
    def bound_names(self) -> Set[str]:
        return self.scope | self.child.bound_names



class Composition(Agent):

    def __init__(self, children: Set[Agent]) -> None:
        self.children = children


    def __str__(self) -> str:
        return '(%s)' % (' | '.join(map(str, self.children)),)


    def flatten(self) -> Agent:
        children = set({child.flatten() for child in self.children})
        for child in children:
            if isinstance(child, Composition):
                return type(self)(children - {child} | child.children).flatten()
            elif isinstance(child, Scope):
                alpha = Composition(children).construct_alpha(child)
                alpha_child = alpha(child)
                return Scope(Composition(children - {child} | {alpha_child.child}),
                             alpha_child.scope).flatten()
            else:
                assert isinstance(child, (Replication, Solo))
        else:
            return type(self)(children)


    @property
    def names(self) -> Set[str]:
        return reduce(set.union, map(lambda x: x.names, self.children), set())


    @property
    def bound_names(self) -> Set[str]:
        return reduce(set.union, map(lambda x: x.bound_names, self.children), set())



class Replication(Agent):

    def __init__(self, child: Agent) -> None:
        self.child = child


    def __str__(self) -> str:
        return '!%s' % (str(self.child),)


    def flatten(self) -> Agent:
        child = self.child.flatten()
        if not isinstance(child, Scope):
            child = Scope(child, set())
        if not isinstance(child.child, Composition):
            child = Scope(Composition(set({child.child})), child.scope)
        composition = child.child.children
        replicators = set(filter(lambda x: isinstance(x, Replication), composition))
        for Q in replicators:
            P = composition - replicators
            x = child.scope
            z = list(Q.free_names)
            y, *_ = fresh_name(child.names, ['y'])
            w = fresh_name(child.names | {y}, z)
            alpha = Alpha(zip(z, w))
            Prep = Replication(Scope(Composition(set({P, Solo(y, z, True)})), x))
            Qrep = Replication(Scope(Composition(set({alpha(Q), Solo(y, w, False)})), set(w)))
            return Scope(Composition(set({Prep, Qrep})), set({y})).flatten()
        return type(self)(child)


    @property
    def names(self) -> Set[str]:
        return self.child.names


    @property
    def bound_names(self) -> Set[str]:
        return self.child.bound_names



class Solo(Agent):

    def __init__(self, subject: str, objects: Iterable[str], parity: bool) -> None:
        self.subject = subject
        self.objects = objects
        self.parity = parity


    def __str__(self) -> str:
        subject = self.subject if self.parity else '\u0305' + '\u0305'.join(self.subject)
        return ' '.join((subject,) + self.objects)


    def flatten(self) -> Agent:
        return type(self)(self.subject, self.objects, self.parity)


    @property
    def arity(self) -> int:
        return len(self.objects)


    @property
    def names(self) -> Set[str]:
        return set({self.subject} | {*self.objects})
    

    def bound_names(self) -> Set[str]:
        return set()



class CanonicalAgent(Agent):

    @staticmethod
    def typefilter(agent_t: type, agents: Iterator) -> Iterator:
        return filter(lambda x: isinstance(x, agent_t), agents)


    def __init__(self, agent: Union[Agent, Tuple[Set[str],
                                                 Set[Solo],
                                                 Set[CanonicalAgent]]] = None)-> None:
        self.scope: Set[str] = None
        self.solos: Set[Solo] = None
        self.replicators: Set[CanonicalAgent] = None
        if isinstance(agent, Agent):
            base = CanonicalAgent((set(), set(), set()))
            base |= agent
            self.scope, self.solos, self.replicators = base
        elif isinstance(agent, tuple):
            self.scope, self.solos, self.replicators = agent


    def __iter__(self) -> Iterable:
        yield self.scope
        yield self.solos
        yield self.replicators


    def __str__(self) -> str:
        return '(%s)(%s)' % (' '.join(self.scope),
                             ' | '.join(set(map(str, self.solos)) 
                                        | {'!%s' % r for r in self.replicators}))


    def construct_alpha(self, collisions: Set[str]) -> Alpha:
        sorted_collisions = list(collisions)
        fresh_names = fresh_name(self.names, sorted_collisions)
        return Alpha(zip(sorted_collisions, fresh_names))


    def construct_sigma(self, input: Solo, output: Solo,
                        bound_names: Set[str] = set()) -> Tuple[Sigma, Set[str]]:
        if any([input.subject != output.subject,
                input.arity != output.arity,
                input.parity == output.parity]):
            return None, None
        g = graph()
        sigma = Sigma()
        fresh_names: Set[str] = set()
        for i_obj, o_obj in zip(input.objects, output.objects):
            g.insert_edge(i_obj, o_obj)
        for partition in g.partitions:
            intersect = partition - (self.scope | bound_names)
            if len(intersect) == 0:
                free_name, *_ = fresh_name(self.names | fresh_names)
                fresh_names |= {free_name}
            elif len(intersect) == 1:
                free_name, *_ = intersect
            else:
                return None, None
            for name in partition - {free_name}:
                sigma[name] = free_name
        return sigma, fresh_names


    def __or__(self, agent: Agent) -> CanonicalAgent:
        if isinstance(agent, Scope):
            collisions = agent.scope & self.names
            if collisions:
                return self | self.construct_alpha(collisions)(agent)
            else:
                ret = self | agent.child
                ret.scope |= agent.scope
                return ret

        elif isinstance(agent, Composition):
            return reduce(type(self).__or__, agent.children, self)

        elif isinstance(agent, Replication):
            p = type(self)(agent.child)
            for q in p.replicators:
                p.replicators -= {q}
                y, *_ = fresh_name(agent.names, ['y'])
                z = list(q.free_names)
                ws = fresh_name(agent.names | {y}, z)
                alpha = Alpha(zip(z, ws))
                P = p | Solo(y, z, True)
                Q = Scope(Composition(set({alpha(q), Solo(y, z, False)})), set(ws))
                return self | Scope(Composition(set({P.to_agent, Q})), set({y}))
            else:
                assert p.replicators == set()
                collisions = self.scope & p.scope
                return type(self)((self.scope,
                                   self.solos,
                                   self.replicators | {self.construct_alpha(collisions)(p)}))

        elif isinstance(agent, Solo):
            collisions = self.scope & agent.names
            return type(self)((self.scope,
                               self.solos | {self.construct_alpha(collisions)(agent)},
                               self.replicators))

        else:
            assert isinstance(agent, type(self))
            return self | agent.to_agent
    

    def flatten(self) -> CanonicalAgent:
        return self


    def reduce(self) -> CanonicalAgent:
        for input, output in ((input, output)
                              for input in self.solos
                              for output in self.solos - {input}):
            sigma, rescope = self.construct_sigma(input, output)
            if sigma:
                scope, solos, replicators = self
                solos -= {input, output}
                return sigma(CanonicalAgent((scope | rescope, solos, replicators)))

        for input, replicator, output in ((input, replicator, output)
                              for input in self.solos
                              for replicator in self.replicators
                              for output in replicator.solos):
            sigma, _ = self.construct_sigma(input, output, replicator.scope)
            if sigma:
                return self | replicator

        for input, ireplicator, output, oreplicator in ((input, ireplicator, output, oreplicator)
                              for ireplicator in self.replicators
                              for input in ireplicator.solos
                              for oreplicator in self.replicators
                              for output in oreplicator.solos):
            sigma, _ = self.construct_sigma(input, output, ireplicator.scope | oreplicator.scope)
            if sigma:
                return self | ireplicator | oreplicator

        return self


    @property
    def to_agent(self) -> Agent:
        return Scope(Composition(self.solos | set(map(Replication, self.replicators))), self.scope)
    

    @property
    def names(self) -> Set[str]:
        return self.scope \
            | set(reduce(lambda red, solo: red | solo.names, self.solos, set())) \
            | set(reduce(lambda red, rep: red | rep.names, self.replicators, set()))



T = TypeVar('T', Solo, Scope, Composition, Replication, CanonicalAgent, Agent, str)
class Match(dict):

    def __init__(self, *args, in_scope: multiset = multiset(),
                 fuse: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.in_scope = in_scope
        self.fuse = fuse


    def __call__(self, agent: T) -> T:
        if isinstance(agent, Composition):
            return type(agent)(set({type(self)(self, in_scope=self.in_scope)(child)
                                    for child in agent.children}))
        elif isinstance(agent, Scope):
            self.in_scope |= agent.scope
            if self.fuse:
                # FIXME: This can be removed by culling unused scopes
                return type(agent)(self(agent.child), set(agent.scope - self.keys()))
            else:
                return type(agent)(self(agent.child), set(map(self, agent.scope)))
        elif isinstance(agent, Replication):
            return type(agent)(self(agent.child))
        elif isinstance(agent, Solo):
            return type(agent)(self(agent.subject),
                               tuple(map(self, agent.objects)),
                               agent.parity)
        elif isinstance(agent, CanonicalAgent):
            return type(agent)(self(agent.to_agent))
        else:
            assert isinstance(agent, str)
            return type(agent)(self[agent])


    def __getitem__(self, key: str) -> str:
        return super().get(key, key) if self.in_scope[key] == 1 else key



class Alpha(Match):

    def __init__(self, *args, fuse=False, **kwargs) -> None:
        super().__init__(*args, fuse=fuse, **kwargs)



class Sigma(Match):

    def __init__(self, *args, fuse=True, **kwargs) -> None:
        super().__init__(*args, fuse=fuse, **kwargs)



if __name__ == '__main__':
    a, b, c, p = (str(x) for x in 'abcp')
    ags = [(Scope(Composition(set({Solo(a, (b,), True),
                                   Solo(a, (c,), False),
                                   Solo(p, (a,b,c), True)})), set({p, b})),
            1),

           (Scope(Composition(set({Solo(a, (b,), True),
                                   Replication(Solo(a, (c,), False)),
                                   Solo(p, (a,b,c), True)})), set({p, b})),
            2),

           (Scope(Composition(set({Replication(Solo(a, (b,), True)),
                                  Replication(Solo(a, (c,), False)),
                                  Solo(p, (a,b,c), True)})), set({p, b})),
            2),
          
           (Scope(Composition(set({Replication(Composition(set({Solo(a, (b,), True),
                                                                Solo(a, (c,), False)}))),
                                   Solo(p, (a,b,c), True)})), set({p, b})),
            2)]
    
    for agent, n in ags:
        canonical = CanonicalAgent(agent)
        reduxes = [reduce(lambda rs, i: rs + [rs[-1].reduce()], range(n), [ag])
                   for ag in [canonical]]
        print('\n\n'.join(('\n-> '.join(map(str, redux)) for redux in reduxes)))
        print('----------------')
