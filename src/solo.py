#! /usr/bin/env python3

import base
from base import Agent, Name


class Solo(base.Solo):

    def __init__(self, subject: Name, objects: tuple) -> None:
        super().__init__()

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
