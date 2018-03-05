#! /usr/bin/env python3

import base
from base import Agent


class Inaction(base.Inaction):

    def __str__(self) -> str:
        return '0'


    def __bool__(self) -> bool:
        return False


    def reduce(self, bindings: frozenset = frozenset()) -> base.Inaction:
        return Inaction()
    
    
    def match(self, matches: dict, bindings: frozenset) -> base.Inaction:
        return Inaction()

    
    @classmethod
    def id(cls, agent: Agent) -> Agent:
        return cls()



base.Inaction = Inaction