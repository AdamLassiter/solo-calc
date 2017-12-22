#! /usr/bin/env python3

import re, unittest

from base import Agent, Name

from inaction import Inaction
from solo import Input, Output

from composition import Composition
from replication import Replication
from scope import Scope
from match import Match


class TestSoloCalculus(unittest.TestCase):
    pass


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

composition = re.compile(r'\s?\((?P<agents>(.+\|?)+)\)\s?')
def build_composition(match, names: dict) -> Composition:
    agents = {build_agent(string, names) for string in match['agents'].split('|')}
    return Composition(agents)

replication = re.compile(r'\s?!\((?P<agent>.*)\)\s')
def build_replication(match, names: dict) -> Replication:
    agent = build_agent(match['agent'], names)
    return Replication(agent)

scope = re.compile(r'\s?\((?P<bindings>([a-z]+\s?)+)\)(?P<agent>\(.+\))\s?')
def build_scope(match, names: dict) -> Scope:
    agent = build_agent(match['agent'], names)
    bindings = {names[name] for name in match['bindings'].split()}
    return Scope(bindings, agent)

def build_agent(string: str, names: dict = {}) -> Agent:
    for regex, build_func in [(_input, build_input), (output, build_output), (inaction, build_inaction),
                               (scope, build_scope), (composition, build_composition),
                               (replication, build_replication)]:
        match = regex.fullmatch(string)
        if match:
            return build_func(match, names)
    raise Exception()


def repl():
    agent = Inaction()
    print('solo calculus repl (q to quit)...')
    while True:
        user_in = input('>> ')
        if user_in == 'q':
            return
        elif user_in in ['', '->']:
            agent = agent.reduce()
        else:
            agent = build_agent(user_in)
        print(agent)


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        repl()
