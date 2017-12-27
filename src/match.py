#! /usr/bin/env python3

import base
from base import Agent, Name


class Match(base.Match):

    def __init__(self, agent: Agent, matches: dict) -> None:
        super().__init__()

        for key, value in matches.items():
            assert isinstance(key, Name) and isinstance(value, Name)
            # NOTE: Here, {a: c, b: c} renames both a and b to c
        assert isinstance(agent, base.Scope)

        self.agent = agent
        self.agent.bindings -= matches.keys()
        self.matches = matches


    def __str__(self) -> str:
        return '%s{%s}' % (self.agent, ', '.join(['%s/%s' % (value, key)
                                                 for key, value in self.matches.items()]))
    
    
    def reduce(self, matches: dict = {}) -> Agent:
        return self.agent.reduce(dict(matches, **self.matches))

    
    @staticmethod
    def id(agent: Agent) -> Agent:
        return Match(agent, dict())


base.Match = Match
