"""Developed synthetic controls for finite fact-update maintenance."""
import json
from pathlib import Path


def program(atoms, facts, *rules):
    return {'atoms': atoms.split() if atoms else [],
            'facts': facts.split() if facts else [],
            'rules': [{'if': body.split() if body else [], 'then': head}
                      for body, head in rules]}


def update(delete='', insert=''):
    return {'delete': delete.split() if delete else [],
            'insert': insert.split() if insert else []}


def controls():
    cases = [
        ('A local count can keep a dead cycle',
         program('p q', 'p', ('p', 'q'), ('q', 'p')),
         [update('p'), update(insert='q'), update('q')]),
        ('Overdeleted does not mean finally lost',
         program('a b x y', 'a b', ('a', 'x'), ('b', 'x'), ('x', 'y')),
         [update('a'), update('b')]),
        ('A conjunction loses one prerequisite',
         program('a b x', 'a b', ('a b', 'x')),
         [update('a'), update(insert='a')]),
        ('An explicit fact survives a broken derivation',
         program('a x y', 'a x', ('a', 'x'), ('x', 'y')),
         [update('a'), update('x')]),
        ('An empty-body rule restores the seed',
         program('a b', 'a', ('', 'a'), ('a', 'b')),
         [update('a')]),
        ('Insertion crosses several delta rounds',
         program('a b c d', '', ('a', 'b'), ('b', 'c'), ('b c', 'd')),
         [update(insert='a'), update('a')]),
        ('A deleted explicit fact can remain inferred',
         program('a b c', 'a b', ('a', 'b'), ('b', 'c')),
         [update('b'), update('a')]),
        ('Delete and insert in the same transaction',
         program('a b x y g', 'a', ('a', 'x'), ('b', 'y'), ('x y', 'g')),
         [update('a', 'b'), update(insert='a'), update('b', 'x')]),
        ('Self-support is not an external derivation',
         program('a', 'a', ('a', 'a')),
         [update('a'), update(insert='a')]),
        ('No-op sets do not invent a materialization change',
         program('a b', 'a', ('a', 'b')),
         [update('b', 'a'), update(), update('a'), update('a')]),
        ('Duplicate indexed rules and a six-atom cycle',
         program('a b c d e f', 'a f', ('a', 'b'), ('a', 'b'),
                 ('b', 'c'), ('c', 'd'), ('d', 'e'), ('e', 'f'), ('f', 'a')),
         [update('a'), update('f'), update(insert='c')]),
        ('Empty vocabulary and empty update', program('', ''), [update()]),
    ]
    return [{'name': title, 'request': {'program': p, 'updates': us}}
            for title, p, us in cases]


if __name__ == '__main__':
    Path('docs/update-controls.json').write_text(json.dumps(controls(), indent=2) + '\n')
