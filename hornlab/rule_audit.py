"""Exact retained-rule lattice, with facts held fixed throughout."""
from .core import validate


def audit_rules(data):
    data = validate(data)
    atoms, facts, rules = data['atoms'], data['facts'], data['rules']
    bit = {a: 1 << i for i, a in enumerate(atoms)}
    names = lambda m: [a for a in atoms if bit[a] & m]
    ids = lambda m: [i for i in range(len(rules)) if m & (1 << i)]
    compiled = [(sum(bit[a] for a in r['if']), bit[r['then']]) for r in rules]
    full = (1 << len(rules)) - 1
    lattice = []
    closed = []
    for mask in range(full + 1):
        current = sum(bit[a] for a in facts)
        steps = []
        while True:
            nxt = current
            for i, (body, head) in enumerate(compiled):
                if mask & (1 << i) and current & body == body:
                    nxt |= head
            steps.append(names(nxt & ~current))
            if nxt == current:
                break
            current = nxt
        closed.append(current)
        lattice.append({'mask': mask, 'retained': ids(mask), 'closure': names(current), 'added_rounds': steps})
    def hitting(family):
        hits = [m for m in range(full + 1) if all(m & s for s in family)]
        return [m for m in hits if all(m ^ (1 << i) not in hits for i in ids(m))]
    queries = []
    for atom in atoms:
        target = bit[atom]
        supports = [m for m in range(full + 1) if closed[m] & target and all(not closed[m ^ (1 << i)] & target for i in ids(m))]
        cuts = [m for m in range(full + 1) if not closed[full ^ m] & target and all(closed[full ^ (m ^ (1 << i))] & target for i in ids(m))]
        queries.append({'atom': atom, 'full_entailed': bool(closed[full] & target),
                        'supports': [{'mask': m, 'rules': ids(m), 'deletions': [{'removed': i, 'remaining_mask': m ^ (1 << i), 'closure': names(closed[m ^ (1 << i)])} for i in ids(m)]} for m in supports],
                        'cuts': [{'mask': m, 'removed': ids(m), 'retained_mask': full ^ m, 'closure': names(closed[full ^ m]), 'restorations': [{'restored': i, 'retained_mask': full ^ (m ^ (1 << i)), 'closure': names(closed[full ^ (m ^ (1 << i))])} for i in ids(m)]} for m in cuts],
                        'minimal_hitting_supports': hitting(supports), 'minimal_hitting_cuts': hitting(cuts),
                        'intersections': [{'support': s, 'cut': c, 'rules': ids(s & c)} for s in supports for c in cuts]})
    return {'schema': 'hornlab-rules-v1', 'input': data, 'subsets': lattice, 'queries': queries}
