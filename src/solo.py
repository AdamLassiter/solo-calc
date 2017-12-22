#! /usr/bin/env python3

from calculus import Agent, Name, Solo as BaseClass


class Solo(BaseClass):

    def __init__(self, subject: Name, objects: tuple) -> None:
        for name in objects:
            assert isinstance(name, Name)

        self.subject = subject
        self.objects = objects
        self.arity = len(objects)

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
        return '%s ' % self.subject + ''.join(map(str, self.objects))
    


class Output(Solo):

    def __str__(self) -> str:
        return '\u0305%s %s' % ('\u0305'.join(str(self.subject)),
                                ''.join(map(str, self.objects)))

Solo.types = frozenset({Input, Output})
Input.inverse = Output
Output.inverse = Input
