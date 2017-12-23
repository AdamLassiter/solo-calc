#! /usr/bin/env python3

import regex as re
import unittest

from base import Agent, Name
from inaction import Inaction
from solo import Input, Output
from composition import Composition
from replication import Replication
from scope import Scope
from match import Match


_input = re.compile(r'\s?(?P<subject>[a-z]+)\s(?P<objects>([a-z]+\s?)+)\s?')
def build_input(match, names: dict) -> Input:
    subj_name = match['subject']
    if subj_name not in names.keys():
        names[subj_name] = Name(subj_name)
    subject = names[subj_name]
    objects = []
    for obj_name in match['objects'].split():
        if obj_name not in names.keys():
            names[obj_name] = Name(obj_name)
        objects.append(names[obj_name])
    return Input(subject, tuple(objects))


output = re.compile(r'\s?\^(?P<subject>[a-z]+)\s(?P<objects>([a-z]+\s)+)\s?')
def build_output(match, names: dict) -> Output:
    subj_name = match['subject']
    if subj_name not in names.keys():
        names[subj_name] = Name(subj_name)
    subject = names[subj_name]
    objects = []
    for obj_name in match['objects'].split():
        if obj_name not in names.keys():
            names[obj_name] = Name(obj_name)
        objects.append(names[obj_name])
    return Output(subject, tuple(objects))


inaction = re.compile(r'\s?0\s?')
def build_inaction(match, names: dict) -> Inaction:
    return Inaction()


composition = re.compile(r'\s?\((?<agents>(?<agent>([^|()]|(?<rec>\((?:[^()]++|(?&rec))*\)))+)(\|(?&agents))?)\)\s?')
def build_composition(match, names: dict) -> Composition:
    agents = {build_agent(string, names) for string in match.captures('agent')}
    return Composition(agents)


replication = re.compile(r'\s?!(?P<agent>\(.*\))\s?')
def build_replication(match, names: dict) -> Replication:
    agent = build_agent(match['agent'], names)
    return Replication(agent)


scope = re.compile(r'\s?\((?P<bindings>([a-z]+\s?)+)\)(?P<agent>\(.+\))\s?')
def build_scope(match, names: dict) -> Scope:
    agent = build_agent(match['agent'], names)
    for name in match['bindings'].split():
        if name not in names.keys():
            names[name] = Name(name)
    bindings = {names[name] for name in match['bindings'].split()}
    return Scope(bindings, agent)


def build_agent(string: str, names: dict = {}) -> Agent:
    for regex, build_func in [(_input, build_input), (output, build_output), (inaction, build_inaction),
                               (scope, build_scope), (composition, build_composition),
                               (replication, build_replication)]:
        match = regex.fullmatch(string)
        if match:
            return build_func(match, names)
    raise Exception('Cannot build agent: %s' % string)



class TestSoloCalculus(unittest.TestCase):

    def test_fusion(self):
        agent = build_agent('(x)(u x | ^u y | p x y)')
        self.assertEqual(str(agent.reduce().reduce()), 'p y y')
        # TODO: Negative test cases


    def test_replication_inner_outer(self):
        agent = build_agent('(y)(u x | !(x)(^u y | p x y))')
        for i in range(5):
            print(agent)
            agent = agent.reduce()


def repl():
    agent = Inaction()
    print('solo calculus repl (q to quit)...')
    while True:
        user_in = input('>> ')
        if user_in == 'q':
            return
        elif user_in == '->':
            agent = agent.reduce()
        elif user_in:
            agent = build_agent(user_in)
        print(agent)


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        repl()
