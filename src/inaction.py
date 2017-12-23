#! /usr/bin/env python3

import base
from base import Agent


class Inaction(base.Inaction):

    def __str__(self) -> str:
        return '0'
    
    def __bool__(self) -> bool:
        return True

    def reduce(self) -> Agent:
        return Inaction()

    @property
    def agents(self) -> set:
        return set()

    @property
    def names(self) -> set:
        return set()

    @property
    def bound_names(self) -> set:
        return set()


base.Inaction = Inaction
