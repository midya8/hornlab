"""Independent set replay plus exhaustive truth tables, not a generator call."""
import json
from .core import validate


def verify(report):
    try:
        if type(report) is not dict:
            return False
        data = validate(report.get('input'))
        atoms, facts, rules = data['atoms'], data['facts'], data['rules']
        def ordered(xs):
            return [a for a in atoms if a in xs]
        def num(xs):
            return sum(2 ** atoms.index(a) for a in xs)
        def members(m):
            return {a for i, a in enumerate(atoms) if (m // (2 ** i)) % 2}
        def closure(seed):
            known = set(seed)
            while True:
                old = set(known)
                for rule in rules:
                    if set(rule['if']) <= known:
                        known.add(rule['then'])
                if known == old:
                    return known
        all_sets = [members(m) for m in range(2 ** len(atoms))]
        models = [s for s in all_sets if set(facts) <= s and all(not set(r['if']) <= s or r['then'] in s for r in rules)]
        least = set.intersection(*models)
        if closure(facts) != least:
            return False
        current, rounds = set(facts), []
        while True:
            next_set = current | {r['then'] for r in rules if set(r['if']) <= current}
            decisions = [{'rule': i, 'missing': ordered(set(r['if']) - current), 'ready': set(r['if']) <= current, 'new_head': set(r['if']) <= current and r['then'] not in current} for i, r in enumerate(rules)]
            rounds.append({'round': len(rounds) + 1, 'before': ordered(current), 'added': ordered(next_set - current), 'after': ordered(next_set), 'rules': decisions})
            if next_set == current:
                break
            current = next_set
        seeds = [s for s in all_sets if s <= set(facts)]
        closures = {num(s): closure(s) for s in seeds}
        queries = []
        for a in atoms:
            supports = []
            for s in seeds:
                if a not in closures[num(s)] or any(t < s and a in closures[num(t)] for t in seeds):
                    continue
                supports.append({'mask': num(s), 'facts': ordered(s), 'deletions': [{'removed': f, 'remaining': ordered(s - {f}), 'closure': ordered(closures[num(s - {f})])} for f in ordered(s)]})
            first = 0 if a in facts else next((r['round'] for r in rounds if a in r['added']), None)
            achievers = [] if first in (0, None) else [i for i, r in enumerate(rules) if r['then'] == a and set(r['if']) <= set(rounds[first - 1]['before']) and a not in rounds[first - 1]['before']]
            queries.append({'atom': a, 'entailed': a in least, 'first_round': first, 'first_achievers': achievers, 'countermodel': next((num(s) for s in models if a not in s), None), 'minimal_supports': supports})
        expected = {'schema': 'hornlab-v1', 'input': data, 'rounds': rounds, 'least_model': ordered(least), 'models': [{'mask': num(s), 'atoms': ordered(s), 'supported': s == set(facts) | {r['then'] for r in rules if set(r['if']) <= s}, 'least': s == least} for s in models], 'ablations': [{'mask': num(s), 'facts': ordered(s), 'closure': ordered(closures[num(s)])} for s in seeds], 'queries': queries}
        dump = lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
        return dump(report) == dump(expected)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError):
        return False
