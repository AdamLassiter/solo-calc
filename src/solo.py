#! /usr/bin/env python3

from hashdict import hashdict

import base
from base import Agent, Name


class Solo(base.Solo):

    def __new__(typ, subject, objects) -> object:
        return super().__new__(typ, (subject,) + objects)


    def __init__(self, subject: base.Name, objects: tuple) -> None:
        self.subject = subject
        self.objects = objects
        self.arity = len(self.objects)

        for name in self.objects:
            assert isinstance(name, Name)


    def eq(self, other: Agent, self_bindings: frozenset, other_bindings: frozenset) -> frozenset:
        if type(self) != type(other) or self.arity != other.arity:
            return frozenset()
        solution = {}
        for my_name, your_name in zip(self, other):
            if (my_name in self_bindings) != (your_name in other_bindings):
                return frozenset()
            elif (my_name in solution.keys() or your_name in solution.values()) \
            and solution.get(my_name, None) != your_name:
                return frozenset()
            else:
                solution[my_name] = your_name
        return frozenset([hashdict(solution)])


    def __str__(self) -> str:
        return ' '.join(map(str, self.objects))


    def reduce(self, matches: dict = {}, bindings: frozenset = frozenset()) -> Agent:
        subject =  Name(matches.get(self.subject, self.subject))
        objects = tuple(Name(matches.get(name, name)) for name in self.objects)
        if not objects:
            return base.Inaction()
        else:
            return type(self)(subject, objects)


    @staticmethod
    def id(agent: Agent) -> Agent:
        # This is the best we can do...
        return None


    @property
    def names(self) -> frozenset:
        return frozenset(self)



class Input(Solo):

    def __str__(self) -> str:
        return '%s %s' % (self.subject, super().__str__())



class Output(Solo):

    def __str__(self) -> str:
        return '\u0305%s %s' % ('\u0305'.join(str(self.subject)), super().__str__())



Solo.types = frozenset({Input, Output})
Input.inverse = Output
Output.inverse = Input
base.Solo = Solo
