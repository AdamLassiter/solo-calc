#! /usr/bin/env python3

from calculus import Agent, Inaction as BaseClass


class Inaction(BaseClass):

    def __str__(self) -> str:
        return '0'

    def reduce(self) -> Agent:
        return type(self)()

    @property
    def agents(self) -> set:
        return set()

    @property
    def names(self) -> set:
        return set()

    @property
    def bound_names(self) -> set:
        return set()
