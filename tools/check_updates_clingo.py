"""Optional external clingo check of finite positive update results.

Install clingo separately; it is not a package/runtime dependency. This checks
stable families of positive programs, not the UI or DRed trace obligations.
"""
import itertools
import random
import json
import clingo
from hornlab.updates import maintain
from make_update_controls import controls


def reference(program, facts):
    lines = [a + '.' for a in facts]
    for r in program['rules']:
        lines.append(r['then'] + (' :- ' + ', '.join(r['if']) if r['if'] else '') + '.')
    ctl = clingo.Control(['0', '--warn=none'])
    ctl.add('base', [], '\n'.join(lines))
    ctl.ground([('base', [])])
    models = []
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            models.append({str(a) for a in model.symbols(atoms=True)})
    assert len(models) == 1
    return [a for a in program['atoms'] if a in models[0]]


def cases():
    yield from (c['request'] for c in controls())
    atoms = ['a', 'b']
    subsets = [[a for i, a in enumerate(atoms) if m & (1 << i)] for m in range(4)]
    rules = [{'if': body, 'then': head} for body in subsets for head in atoms]
    for rmask in range(256):
        rs = [r for i, r in enumerate(rules) if rmask & (1 << i)]
        for old, new in itertools.product(subsets, repeat=2):
            yield {'program': {'atoms': atoms, 'facts': old, 'rules': rs},
                   'updates': [{'delete': [a for a in old if a not in new],
                                'insert': [a for a in new if a not in old]}]}
    rng = random.Random(73051)
    for _ in range(350):
        atoms = list('abcdef')[:rng.randrange(7)]
        subset = lambda: [a for a in atoms if rng.randrange(2)]
        rules = [{'if': subset(), 'then': rng.choice(atoms)} for _ in range(rng.randrange(9))] if atoms else []
        updates = []
        for _ in range(8):
            d = subset()
            updates.append({'delete': d, 'insert': [a for a in subset() if a not in d]})
        yield {'program': {'atoms': atoms, 'facts': subset(), 'rules': rules}, 'updates': updates}


if __name__ == '__main__':
    programs = transactions = families = 0
    for data in cases():
        r = maintain(data)
        assert reference(data['program'], data['program']['facts']) == r['initial_closure']
        families += 1
        for step in r['steps']:
            assert reference(data['program'], step['facts_after']) == step['closure_after']
            transactions += 1
            families += 1
        programs += 1
    print(json.dumps({'reference': 'clingo', 'version': clingo.__version__,
                      'requests': programs, 'transactions': transactions,
                      'stable_families': families}))
