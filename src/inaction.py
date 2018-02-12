#! /usr/bin/env python3

import base
from base import Agent


class Inaction(base.Inaction):

    def __str__(self) -> str:
        return '0'


    def __bool__(self) -> bool:
        return False

    
    def reduce(self, matches: dict = {}, bindings: frozenset = frozenset()) -> Agent:
        return Inaction()

    
    @staticmethod
    def id(agent: Agent) -> Agent:
        return Inaction()



base.Inaction = Inaction
