#! /usr/bin/env python3

import base
from base import Agent, Name


class Solo(base.Solo):

    def __init__(self, subject: Name, objects: tuple) -> None:
        for name in objects:
            assert isinstance(name, Name)

        self.subject = subject
        self.objects = objects
        self.arity = len(objects)

    def __str__(self) -> str:
        return ' '.join(map(str, self.objects))

    def reduce(self) -> Agent:
        return type(self)(self.subject, self.objects)

    @property
    def agents(self) -> set:
        return set()

    @property
    def names(self) -> set:
        return {self.subject} | {obj for obj in self.objects}

    @property
    def bound_names(self) -> set:
        return set()



class Input(Solo):

    def __str__(self) -> str:
        return '%s %s' % (self.subject, super().__str__())
    


class Output(Solo):

    def __str__(self) -> str:
        return '\u0305%s %s' % ('\u0305'.join(str(self.subject)), super().__str__())


base.Solo = Solo
Solo.types = frozenset({Input, Output})
Input.inverse = Output
Output.inverse = Input
