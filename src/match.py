#! /usr/bin/env python3

import base
from base import Agent, Name


class Match(base.Match):

    def __init__(self, agent: Agent, matches: dict) -> None:
        super().__init__()

        for key, value in matches.items():
            assert isinstance(key, Name) and isinstance(value, Name)
            # NOTE: Here, {a: c, b: c} renames both a and b to c
            assert key in agent.bound_names
        assert isinstance(agent, base.Scope)

        self.agent = agent
        self.matches = matches


    def __str__(self) -> str:
        return '%s{%s}' % (self.agent, ', '.join(['%s/%s' % (value, key)
                                                 for key, value in self.matches.items()]))


    def reduce(self) -> Agent:
        agent = self.agent
        agent.bindings -= frozenset(self.matches.keys())

        for key, value in self.matches.items():
            key.fuse_into(value)

        return agent.reduce()


base.Match = Match
