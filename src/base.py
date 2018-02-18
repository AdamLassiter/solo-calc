#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: Need to rename only for the first scoping of a given agent ( i.e. !(x)P )... Accomplish
# by tracking bindings on matching? If something is twice bound, it is forgotten.
# NOTE: Notes for later
'''
Expressions are immutable due to problems with adding mutable items to a set:
    Since a set is stored by object hash value, object hashes must remain constant.
    There is not enough unique immutable data per object to allow for this.
    Furthermore, this allows reductions to make themselves grandchildren of their parents
        (see Composition/Scope reduction and rescoping operation)

Reductions are performed recursively:
    Each agent will first reduce each of its sub-agents.
    Then reduction rules are applied where applicable - this includes:
        * Trivial cases for nested copies of operators and TODO: for identites of operators
        * Extracting scopes where applicable ((x)P | Q) -> (x)(P | Q) if x ∉ fn(Q)
        * Applying the flattening theorem for nested replications
        * Finite reduction of (non-nested) replications
            See paper implementation

Fusions are performed as follows:
    Input/Output on u of (bound) x and (free) y -> Define/rename x := y
    (x)(̅u x | u y | P) -> P{y / x}

Renaming functions σ are found as follows:
    * Construct graph(s) G, H ... by treating all names as graph nodes and the pairs x̃, ỹ as
      graph edges
    * Check there is at most one free node fn per connected graph G
    * Define σ[bn] := fn ∀ bn ϵ G
'''

from functools import reduce
from itertools import permutations

from graph import graph
from hashdict import hashdict


# All pairwise combinations of two sets
def combinations(a: frozenset, b: frozenset) -> frozenset:
    ret = frozenset({zip(x, b) for x in permutations(a, len(b))})
    return ret


# Set typefilter: agent_t, set -> set<agent_t> or {}
def tf(agent_t: type, agents: frozenset) -> frozenset:
    return frozenset(filter(lambda x: isinstance(x, agent_t), agents))


# Non-empty typefilter: agent_t, set -> nonempty set<agent_t>
def netf(agent_t: type, agents: frozenset) -> frozenset:
    return frozenset({agent if isinstance(agent, agent_t) else agent_t.id(agent)
                      for agent in agents}) - {None}

typefilter = netf



class Agent(frozenset):

    def equals(self, other: object) -> bool:
        return bool(self.eq(other, frozenset(), frozenset()))


    def eq(self, other: object, self_bindings: frozenset, other_bindings: frozenset) -> frozenset:
        # Return 'false' for trivial cases
        if type(self) != type(other) or len(self) != len(other):
            return frozenset()
        equalities = frozenset()
        # For each combination of pairs of sub-agents
        for combination in combinations(self, other):
            combination = tuple(combination)
            if not combination:
                continue
            # Check for equality
            pairwise_equalities = frozenset(map(lambda x, y: x.eq(y, self_bindings, other_bindings),
                                                *zip(*combination)))
            # Skip combinations where pairs are not equal
            if not all(pairwise_equalities):
                continue
            # For a given combination, start 'fresh' from no known equalities except the
            # trivial solution (0) == (0) and iteratively add solutions for each pair in
            # the given combination
            combination_equalities = frozenset({hashdict()})
            # Iterate over each pair of agents...
            for pair_equalities in pairwise_equalities:
                partial_equalities = frozenset()
                # ...and their possible equalities, observing all combinations with
                # existing solutions
                for item in combinations(pair_equalities, combination_equalities):
                    try:
                        extension, solution = tuple(*item)
                    except:
                        continue
                    # If an extension and an existing solution don't agree, skip this
                    # extension-solution pair
                    for key in extension.keys() & solution.keys():
                        if extension[key] != solution[key]:
                            break
                    # Otherwise save it as a possible partially-extended solution
                    else:
                        # 'partial_equalities' holds only the next iteration of solutions,
                        # i.e. a temporary set containing solutions for (n + 1)-length pairs where
                        # 'combination_equalities' holds solutions for n-length pairs
                        partial_equalities |= frozenset({hashdict(solution, **extension)})
                # Store successive solutions of increasing numbers of pairs of agents
                # 'combination_equalities' holds solutions for a (increasing) subset of agents
                combination_equalities = partial_equalities
            # Once this has been extended for all pairs, store the new solutions
            # As such, 'equalities' holds only solutions for equality of all children
            equalities |= combination_equalities
        return equalities


    def __str__(self) -> str:
        raise NotImplementedError


    def __repr__(self) -> str:
        return '%s [%s]' % (type(self), str(self))


    def construct_sigma(self, bindings: frozenset, iagent: object, oagent: object) -> frozenset:
        # Find a renaming, sigma s.t. the agents of iagent and oagent are fused under a
        # given set of bindings. There may be multiple such sigma, so return all possible
        # sigma.
        # This is done by constructing a graph...
        g = graph()
        sigmas = [dict()]
        # ...and inserting edges representing each pair of names in the fused agents
        for pair in zip(iagent.objects, oagent.objects):
            g.insert_edge(*pair)
        # Each partition of the graph forms a set of names to be fused to one another
        for partition in g.partitions():
            # At most, only one name per partition may be free
            intersect = partition - bindings
            assert len(intersect) <= 1
            # If none are free, pick a bound name to fuse into, and pretend it may be free
            if len(intersect) == 0:
                temp_sigmas = []
                for name in partition:
                    partial_sigmas = [dict(sigma) for sigma in sigmas]
                    for temp_sigma in partial_sigmas:
                        for bound_name in partition - {name}:
                            temp_sigma[bound_name] = name
                    temp_sigmas.extend(partial_sigmas)
                sigmas = temp_sigmas
            else:
                free_name, = intersect
                # Assign fusions for each bound name into the free or fresh name
                for sigma in sigmas:
                    for bound_name in partition - {free_name}:
                        sigma[bound_name] = free_name
        return frozenset({hashdict(dict) for dict in sigmas})


    def reduce(self, bindings: frozenset = frozenset()) -> object:
        raise NotImplementedError

    
    def match(self, matches: dict, bindings: frozenset) -> object:
        raise NotImplementedError


    def _attrs(self, attr: str) -> frozenset:
       return reduce(frozenset.union,
                     map(lambda x: frozenset(getattr(x, attr)), self),
                     frozenset())
    

    @staticmethod
    def id(agent: object) -> object:
        raise NotImplementedError


    @property
    def agent(self) -> object:
        if len(self) == 1:
            agent, *_ = self
            return agent
        elif len(self) == 0:
            return None
        else:
            raise TypeError('Ambiguous: agent contains multiple children')


    @property
    def names(self) -> frozenset:
        return self._attrs('names')


    def free_names(self, bindings: frozenset = frozenset()) -> frozenset:
        return self.names - bindings



class Name(str):

    def __new__(cls, *args):
        ret = super().__new__(cls, *args)
        return ret


    @classmethod
    def fresh(cls, names: frozenset, name_hint: str) -> object:
        i = 0
        while name_hint + str(i) in names:
            i += 1
        return cls(name_hint + str(i))



class Solo(Agent):
    pass



class Inaction(Agent):
    pass



class Composition(Agent):
    pass



class Replication(Agent):
    pass



class Scope(Agent):
    pass



class Match(Agent):
    pass
