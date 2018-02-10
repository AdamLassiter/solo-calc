#! /usr/bin/env python3

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

    def __str__(self) -> str:
        return ' '.join(map(str, self.objects))
    
    def equals(self, other) -> bool:
        return type(self) == type(other) \
           and self.subject == other.subject \
           and self.objects == other.objects

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
        return frozenset({self.subject} | {obj for obj in self.objects})

 
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
