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
        raise NotImplemented


    def flatten(self) -> Agent:
        raise NotImplemented


    @property
    def names(self) -> Set[str]:
        raise NotImplemented


    @property
    def bound_names(self) -> Set[str]:
        raise NotImplemented


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


    def reduce(self) -> Agent:
        def typefilter(agent_t: type, agents: Iterator) -> Iterator:
            return filter(lambda x: isinstance(x, agent_t), agents)

        agent = self.flatten()
        composition = agent.child.children

        for input, output in ((input, output)
                for input in typefilter(Solo, composition)
                for output in typefilter(Solo, composition - {input})):
            sigma, fresh_names = agent.construct_sigma(input, output)
            if sigma is not None:
                return sigma(Scope(Composition(composition - {input, output}),
                                   agent.scope | fresh_names))
        
        for input, output, replicator in ((input, output, replicator)
                for input in typefilter(Solo, composition)
                for replicator in typefilter(Replication, composition)
                for output in typefilter(Solo, replicator.child.child.children)):
            bound_names = replicator.child.scope
            sigma, fresh_names = agent.construct_sigma(input, output, bound_names)
            if sigma is not None:
                return Scope(Composition(composition | {replicator.child}), agent.scope)

        for input, input_rep, output, output_rep in ((input, input_rep, output, output_rep)
                for input_rep in typefilter(Replication, composition)
                for input in typefilter(Solo, input_rep.child.child.children)
                for output_rep in typefilter(Replication, composition)
                for output in typefilter(Solo, output_rep.child.child.children)):
            bound_names = input_rep.child.scope | output_rep.child.scope
            sigma, fresh_names = agent.construct_sigma(input, output, bound_names)
            if sigma is not None:
                return Scope(Composition(composition | {input_rep.child, output_rep.child}),
                             agent.scope)

        """ NOTE: This is simply a special case of the above where input_rep == output_rep
        for input, output, replicator in ((input, output, replicator)
                for replicator in typefilter(Replication, composition)
                for input in typefilter(Solo, replicator.child.child.children)
                for output in typefilter(Solo, replicator.child.child.children - {input})):
            bound_names = replicator.child.scope
            sigma, fresh_names = agent.construct_sigma(input, output, bound_names)
            if sigma is not None:
                return Scope(Composition(composition | {replicator.child}), agent.scope)
        """

        return agent
    

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


    def construct_alpha(self, child: Scope) -> Alpha:
        others = Composition(self.children - {child})
        bound_names = list(child.scope)
        fresh_names: List[str] = fresh_name(others.names, bound_names)
        alpha = Alpha(zip(bound_names, fresh_names))
        return alpha


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



class CanonicalAgent:

    @staticmethod
    def typefilter(agent_t: type, agents: Iterator) -> Iterator:
        return filter(lambda x: isinstance(x, agent_t), agents)


    def __init__(self, agent: Union[Agent, Tuple[Set[str],
                                                 Set[Solo],
                                                 Set[Replication]]] = None)-> None:
        if isinstance(agent, Agent):
            self.scope: Set[str] = set()
            self.solos: Set[Solo] = set()
            self.replicators: Set[Replication] = set()
            self |= agent
        elif isinstance(agent, tuple):
            self.scope, self.solos, self.replicators = agent
    

    def __or__(self, agent: Agent) -> CanonicalAgent:
        if isinstance(agent, Scope):
            collision = list(agent.scope & self.names)
            if collision:
                fresh_names = fresh_name(self.names, collision)
                alpha = Alpha(zip(collision, fresh_names))
                return self | alpha(agent)
            else:
                return type(self)((self.scope | agent.scope,
                                   self.solos,
                                   self.replicators)) | agent.child

        elif isinstance(agent, Composition):
            return reduce(type(self).__or__, agent.children, self)

        elif isinstance(agent, Replication):
            p = type(self)(agent.child)
            for q in p.replicators:
                p.replicators -= {q}
                y, *_ = fresh_name(agent.names, ['y'])
                z = list(q.free_names)
                ws = fresh_name(agent.names | {y}, z)
                alpha = Alpha(zip(z, fresh_names))
                P = p | Solo(y, z, True)
                Q = Scope(Composition(set({alpha(q), Solo(y, z, False)})), set(ws))
                return self | Scope(Composition(set({P.to_agent, Q})), set({y}))
            else:
                # TODO: Check no collisions
                return type(self)((self.scope,
                                   self.solos,
                                   self.replicators | {p.to_agent}))

        elif isinstance(agent, Solo):
            collisions = list(self.scope & agent.names)
            fresh_names = fresh_name(self.names, collisions)
            alpha = Alpha(zip(collisions, fresh_names))
            return type(self)((self.scope,
                               self.solos | {alpha(agent)},
                               self.replicators))

        else:
            assert isinstance(agent, type(self))
            return self | agent.to_agent
    

    def flatten(self) -> CanonicalAgent:
        return self


    @property
    def to_agent(self) -> Agent:
        return Scope(Composition(self.solos | self.replicators), self.scope)
    

    @property
    def names(self) -> Set[str]:
        return self.scope \
            | set(reduce(lambda red, solo: red | solo.names, self.solos, set())) \
            | set(reduce(lambda red, rep: red | rep.child.names, self.replicators, set()))



T = TypeVar('T', Agent, str)
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
                return type(agent)(self(agent.child), set(agent.scope - self.keys()))
            else:
                return type(agent)(self(agent.child), set(map(self, agent.scope)))
        elif isinstance(agent, Replication):
            return type(agent)(self(agent.child))
        elif isinstance(agent, Solo):
            return type(agent)(self(agent.subject),
                               tuple(map(self, agent.objects)),
                               agent.parity)
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
        redux = reduce(lambda rs, i: rs + [rs[-1].reduce()], range(n), [agent])
        print(*redux, sep='\n-> ')
        print()
