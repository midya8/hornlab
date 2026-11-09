"""Independent set and truth-table checker; never calls rule_audit."""
import json
from itertools import combinations
from .core import validate


def verify_rules(report):
    try:
        data = validate(report['input'])
        atoms, facts, rules = data['atoms'], set(data['facts']), data['rules']
        universe = set(range(len(rules)))
        sets = [set(i for i in universe if m & (1 << i)) for m in range(2 ** len(rules))]
        masks = lambda s: sum(2 ** i for i in s)
        ordered = lambda s: [a for a in atoms if a in s]
        closures, rows = [], []
        for retained in sets:
            current = set(facts)
            steps = []
            while True:
                heads = {rules[i]['then'] for i in retained if set(rules[i]['if']) <= current}
                added = heads - current
                steps.append(ordered(added))
                if not added: break
                current.update(added)
            models = []
            for size in range(len(atoms) + 1):
                for tup in combinations(atoms, size):
                    assignment = set(tup)
                    if facts <= assignment and all(not set(rules[i]['if']) <= assignment or rules[i]['then'] in assignment for i in retained):
                        models.append(assignment)
            intersection = set(atoms)
            for model in models: intersection.intersection_update(model)
            if current != intersection: return False
            closures.append(current)
            rows.append({'mask': masks(retained), 'retained': sorted(retained), 'closure': ordered(current), 'added_rounds': steps})
        def minimal(candidates):
            return [s for s in candidates if not any(t < s for t in candidates)]
        def hitting(family):
            return [masks(s) for s in minimal([s for s in sets if all(s & f for f in family)])]
        qs = []
        for atom in atoms:
            supports = minimal([s for s in sets if atom in closures[masks(s)]])
            cuts = minimal([s for s in sets if atom not in closures[masks(universe - s)]])
            qs.append({'atom': atom, 'full_entailed': atom in closures[-1],
                       'supports': [{'mask': masks(s), 'rules': sorted(s), 'deletions': [{'removed': i, 'remaining_mask': masks(s - {i}), 'closure': ordered(closures[masks(s - {i})])} for i in sorted(s)]} for s in supports],
                       'cuts': [{'mask': masks(c), 'removed': sorted(c), 'retained_mask': masks(universe - c), 'closure': ordered(closures[masks(universe - c)]), 'restorations': [{'restored': i, 'retained_mask': masks(universe - (c - {i})), 'closure': ordered(closures[masks(universe - (c - {i}))])} for i in sorted(c)]} for c in cuts],
                       'minimal_hitting_supports': hitting(supports), 'minimal_hitting_cuts': hitting(cuts),
                       'intersections': [{'support': masks(s), 'cut': masks(c), 'rules': sorted(s & c)} for s in supports for c in cuts]})
            if hitting(supports) != [masks(s) for s in cuts] or hitting(cuts) != [masks(s) for s in supports]: return False
        expected = {'schema': 'hornlab-rules-v1', 'input': data, 'subsets': rows, 'queries': qs}
        canonical = lambda obj: json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)
        return canonical(report) == canonical(expected)
    except (KeyError, ValueError, TypeError, IndexError, OverflowError, RecursionError):
        return False
