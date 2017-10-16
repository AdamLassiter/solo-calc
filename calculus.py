#! /usr/bin/env python3

class Agent(object):
    pass


class Name(str):
    pass


class Solo(Agent):

    def __init__(self, subject: Name, objects: tuple) -> None:
        for name in objects:
            assert isinstance(name, Name)
        self.subject = subject
        self.objects = objects


class Input(Solo):

    def __str__(self) -> str:
        return '%s ' % self.subject + ''.join(map(str, self.objects))


class Output(Solo):

    def __str__(self) -> str:
        return '\u0305%s ' % self.subject + ''.join(map(str, self.objects))


class Inaction(Agent):

    def __str__(self) -> str:
        return '0'


class Composition(Agent):

    def __init__(self, left: Agent, right: Agent) -> None:
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return '(%s | %s)' % (self.left, self.right)


class Scope(Agent):

    def __init__(self, binding: Name, agent: Agent) -> None:
        self.binding = binding
        self.agent = agent

    def __str__(self) -> str:
        return '(%s)(%s)' % (self.binding, self.agent)


class Replication(Agent):

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def __str__(self) -> str:
        return '!%s' % self.agent


if __name__ == '__main__':
    expr = Replication(Composition(Composition(Input(Name('x'), (Name('y'),)), Inaction()),
                                   Scope(Name('z'), Output(Name('z'), (Name('x'),)))))
    print(expr)
