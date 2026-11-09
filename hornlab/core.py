"""Synchronous inflationary closure, with exhaustive finite model witnesses."""
from copy import deepcopy
import re


def validate(data):
    if type(data) is not dict or set(data) != {'atoms', 'facts', 'rules'}:
        raise ValueError('Expected exactly atoms, facts and rules')
    atoms, facts, rules = data['atoms'], data['facts'], data['rules']
    if type(atoms) is not list or len(atoms) > 6 or any(type(a) is not str or not re.fullmatch(r'[a-z][a-z0-9_]{0,23}', a) for a in atoms) or len(set(atoms)) != len(atoms):
        raise ValueError('Use at most six unique lowercase atom names, 1-24 characters')
    def subset(xs):
        return type(xs) is list and all(type(x) is str and x in atoms for x in xs) and len(set(xs)) == len(xs)
    if not subset(facts):
        raise ValueError('facts must be a unique list of declared atoms')
    if type(rules) is not list or len(rules) > 8:
        raise ValueError('Use at most eight indexed rules')
    for r in rules:
        if type(r) is not dict or set(r) != {'if', 'then'} or not subset(r['if']) or type(r['then']) is not str or r['then'] not in atoms:
            raise ValueError('Each rule has exactly if (unique declared atoms) and then (one declared atom)')
    return deepcopy(data)


def analyze(data):
    data = validate(data)
    atoms, facts, rules = data['atoms'], data['facts'], data['rules']
    bit = {a: 1 << i for i, a in enumerate(atoms)}
    mask = lambda xs: sum(bit[a] for a in xs)
    names = lambda m: [a for a in atoms if bit[a] & m]
    fm = mask(facts)
    compiled = [(mask(r['if']), bit[r['then']]) for r in rules]
    def close(seed, trace=False):
        current, rounds = seed, []
        while True:
            nxt = current
            decisions = []
            for i, (body, head) in enumerate(compiled):
                missing = body & ~current
                ready = not missing
                decisions.append({'rule': i, 'missing': names(missing), 'ready': ready, 'new_head': ready and not bool(current & head)})
                if ready:
                    nxt |= head
            if trace:
                rounds.append({'round': len(rounds) + 1, 'before': names(current), 'added': names(nxt & ~current), 'after': names(nxt), 'rules': decisions})
            if nxt == current:
                return current, rounds
            current = nxt
    least, rounds = close(fm, True)
    models = []
    for m in range(1 << len(atoms)):
        if m & fm != fm or any(m & b == b and not m & h for b, h in compiled):
            continue
        immediate = fm
        for b, h in compiled:
            if m & b == b:
                immediate |= h
        models.append({'mask': m, 'atoms': names(m), 'supported': immediate == m, 'least': m == least})
    ablations = []
    seeds = [s for s in range(1 << len(atoms)) if s & fm == s]
    closures = {}
    for s in seeds:
        out, _ = close(s)
        closures[s] = out
        ablations.append({'mask': s, 'facts': names(s), 'closure': names(out)})
    queries = []
    for a in atoms:
        target = bit[a]
        supports = []
        for s in seeds:
            if not closures[s] & target or any(closures[s ^ bit[f]] & target for f in names(s)):
                continue
            supports.append({'mask': s, 'facts': names(s), 'deletions': [{'removed': f, 'remaining': names(s ^ bit[f]), 'closure': names(closures[s ^ bit[f]])} for f in names(s)]})
        first = 0 if fm & target else next((r['round'] for r in rounds if a in r['added']), None)
        achievers = [] if first in (0, None) else [d['rule'] for d in rounds[first - 1]['rules'] if d['new_head'] and rules[d['rule']]['then'] == a]
        queries.append({'atom': a, 'entailed': bool(least & target), 'first_round': first, 'first_achievers': achievers, 'countermodel': next((m['mask'] for m in models if not m['mask'] & target), None), 'minimal_supports': supports})
    return {'schema': 'hornlab-v1', 'input': data, 'rounds': rounds, 'least_model': names(least), 'models': models, 'ablations': ablations, 'queries': queries}
