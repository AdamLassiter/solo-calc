#! /usr/bin/env python3

import base
from base import Agent, Name


class Match(base.Match):

    def __new__(typ, agent: Agent, matches: dict) -> base.Match:
        obj = super().__new__(typ, frozenset({agent}))
        obj.matches = matches
        return obj


    def __init__(self, agent: Agent, matches: dict) -> None:
        super().__init__()
        for key, value in matches.items():
            assert isinstance(key, Name) and isinstance(value, Name)
            # NOTE: Here, {a: c, b: c} renames both a and b to c
        # assert isinstance(agent, base.Scope)

    
    def eq(self, other: Agent, self_bindings: frozenset, other_bindings: frozenset) -> frozenset:
        if isinstance(other, Match):
            other_agent = other.agent
            other_matches = other.matches
        else:
            other_agent = other
            other_matches = {}
        return self.agent.eq(other_agent, self_bindings, other_bindings)

    def __str__(self) -> str:
        return '%s{%s}' % (self.agent, ', '.join(['%s/%s' % (value, key)
                                                 for key, value in self.matches.items()]))
    

    def reduce(self, bindings: frozenset = frozenset()) -> Agent:
        return self.match(self.matches, bindings).reduce(bindings)


    def match(self, matches: dict, bindings: frozenset) -> Agent:
        return self.agent.match(dict(matches, **self.matches), bindings)


    @classmethod
    def id(cls, agent: Agent) -> Agent:
        return cls(agent, dict())



base.Match = Match
