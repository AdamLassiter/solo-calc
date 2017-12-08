#! /usr/bin/env python3

class Agent(object):
    
    def reduce(self):
        raise NotImplementedError


class Name(object):
    
    def __init__(self, name: str) -> None:
        self.name = name
        self.fusions = {self}

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self in other.fusions
    
    def fuse_into(self, other):
        assert isinstance(other, type(self))
        self.fusions |= {other}
        other.fusions |= {self}
        self.name = other.name


class Solo(Agent):

    def __init__(self, subject: Name, objects: tuple) -> None:
        for name in objects:
            assert isinstance(name, Name)
        self.subject = subject
        self.objects = objects
        self.arity = len(objects)


class Input(Solo):

    def __str__(self) -> str:
        return '%s ' % self.subject + ''.join(map(str, self.objects))
    
    def reduce(self):
        return type(self)(self.subject, self.objects)


class Output(Solo):

    def __str__(self) -> str:
        return '\u0305%s ' % self.subject + ''.join(map(str, self.objects))

    def reduce(self):
        return type(self)(self.subject, self.objects)


class Inaction(Agent):

    def __str__(self) -> str:
        return '0'

    def reduce(self):
        return type(self)()


class Composition(Agent):

    def __init__(self, *agents) -> None:
        for agent in agents:
            assert isinstance(agent, Agent)
        self.agents = set(agents)

    def __str__(self) -> str:
        return '(%s)' % (' | '.join(map(str, self.agents)))

    def reduce(self):
        agents = set()
        # (a | b) | c == a | (b | c)
        for agent in map(lambda x: x.reduce(), self.agents):
            if isinstance(agent, Composition):
                agents |= agent.agents
            else:
                agents |= {agent}
        # (x)(̅u x | u y | P) == P{y / x}
        for iagent in set(filter(lambda x: isinstance(x, Input), agents)):
            for oagent in set(filter(lambda x: isinstance(x, Output), agents)):
                if iagent.subject == oagent.subject \
                and iagent.arity == oagent.arity:
                    for iobject, oobject in zip(iagent.objects, oagent.objects):
                        oobject.fuse_into(iobject)
                    agents.remove(iagent)
                    agents.remove(oagent)
        return type(self)(*agents)


class Scope(Agent):

    def __init__(self, bindings: set, agent: Agent) -> None:
        for binding in bindings:
            assert isinstance(binding, Name)
        self.bindings = bindings
        self.agent = agent

    def __str__(self) -> str:
        return '(%s)(%s)' % (''.join(map(str, self.bindings)), self.agent)

    def reduce(self):
        bindings = self.bindings
        agent = self.agent.reduce()
        # (x)(y)(P) == (xy)(P)
        if isinstance(agent, Scope):
            bindings |= agent.bindings
            agent = agent.agent
        return type(self)(bindings, agent)


class Replication(Agent):

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def __str__(self) -> str:
        return '!%s' % self.agent

    def reduce(self):
        agent = self.agent.reduce()
        # !(!(P)) == !(P)
        if isinstance(agent, Replication):
            agent = agent.agent
        return type(self)(agent)


if __name__ == '__main__':
    x, y, z = Name('x'), Name('y'), Name('z')
    expr = Replication(Composition(Input(z, (y,)),
                                   Output(x, (y,)),
                                   Output(z, (x,))))

    while True:
        print(expr)
        input()
        expr = expr.reduce()
