"""Bounded positive-Horn fact maintenance by delete/rederive and delta insertion.

A transparent single-stratum specialization, not the optimized full Datalog
algorithm. Published foundations and exact limits belong in UPDATES.md.
"""
from copy import deepcopy
from .core import validate


def validate_updates(data):
    if type(data) is not dict or set(data) != {'program', 'updates'}:
        raise ValueError('Expected exactly program and updates')
    program = validate(data['program'])
    updates = data['updates']
    if type(updates) is not list or len(updates) > 8:
        raise ValueError('Use at most eight fact updates')
    for update in updates:
        if type(update) is not dict or set(update) != {'delete', 'insert'}:
            raise ValueError('Each update has exactly delete and insert')
        for key in ['delete', 'insert']:
            xs = update[key]
            if type(xs) is not list or any(type(a) is not str or a not in program['atoms'] for a in xs) or len(set(xs)) != len(xs):
                raise ValueError('Update lists contain unique declared atoms')
        if set(update['delete']) & set(update['insert']):
            raise ValueError('An update cannot both delete and insert one atom')
    return {'program': program, 'updates': deepcopy(updates)}


def maintain(data):
    data = validate_updates(data)
    program = data['program']
    atoms, rules = program['atoms'], program['rules']
    bits = {a: 1 << i for i, a in enumerate(atoms)}
    mask = lambda xs: sum(bits[a] for a in xs)
    names = lambda m: [a for a in atoms if bits[a] & m]
    compiled = [(mask(r['if']), bits[r['then']]) for r in rules]

    def closure(seed):
        current = seed
        while True:
            nxt = current
            for body, head in compiled:
                if body & current == body:
                    nxt |= head
            if nxt == current:
                return current
            current = nxt

    def forward(survivors, seeds):
        delta = seeds & ~survivors
        current = survivors | delta
        rounds = []
        while True:
            decisions = []
            nxt = 0
            for i, (body, head) in enumerate(compiled):
                touched = bool(body & delta)
                missing = body & ~current
                fires = touched and not missing
                new_head = fires and not bool(head & current)
                decisions.append({'rule': i, 'touched_delta': touched,
                                  'missing': names(missing), 'fires': fires,
                                  'new_head': new_head})
                if new_head:
                    nxt |= head
            rounds.append({'round': len(rounds) + 1, 'before': names(current),
                           'delta': names(delta), 'rules': decisions,
                           'added': names(nxt), 'after': names(current | nxt)})
            if not nxt:
                return current, rounds
            current |= nxt
            delta = nxt

    facts = mask(program['facts'])
    current = closure(facts)
    initial = current
    steps = []
    for update in data['updates']:
        removed = facts & mask(update['delete'])
        inserted = mask(update['insert']) & ~facts
        new_facts = (facts & ~removed) | inserted
        # Inverse propagation over the old materialization only. Retain every
        # affected rule ID for evidence, not a count of proof trees.
        deleted = 0
        delta = removed
        over_rounds = []
        while True:
            decisions = []
            nxt = 0
            for i, (body, head) in enumerate(compiled):
                old_ready = body & current == body
                touched = bool(body & delta)
                fires = old_ready and touched
                new_head = fires and not bool(head & (deleted | delta))
                decisions.append({'rule': i, 'old_body_holds': old_ready,
                                  'touched_delta': touched, 'fires': fires,
                                  'new_head': new_head})
                if new_head:
                    nxt |= head
            over_rounds.append({'round': len(over_rounds) + 1,
                                'deleted_before': names(deleted),
                                'delta': names(delta), 'rules': decisions,
                                'added': names(nxt),
                                'deleted_after': names(deleted | delta)})
            deleted |= delta
            if not nxt:
                break
            delta = nxt
        survivors = current & ~deleted
        reseed = []
        rederived = 0
        for atom in atoms:
            head = bits[atom]
            if not deleted & head:
                continue
            supports = [i for i, (body, h) in enumerate(compiled)
                        if h == head and body & survivors == body]
            explicit = bool(head & (facts & ~removed))
            recovered = explicit or bool(supports)
            reseed.append({'atom': atom, 'surviving_explicit': explicit,
                           'surviving_rule_ids': supports,
                           'rederived': recovered})
            if recovered:
                rederived |= head
        final, insert_rounds = forward(survivors, rederived | inserted)
        # This intentionally weaker baseline asks only for local support. It is
        # not the published Counting algorithm, recursive counting, or DRedC.
        naive = current | inserted
        prune_rounds = []
        while True:
            decisions = []
            gone = 0
            for atom in atoms:
                b = bits[atom]
                if not naive & b:
                    continue
                ids = [i for i, (body, head) in enumerate(compiled)
                       if head == b and body & naive == body]
                explicit = bool(new_facts & b)
                count = int(explicit) + len(ids)
                decisions.append({'atom': atom, 'explicit': explicit,
                                  'rule_ids': ids, 'local_count': count})
                if count == 0:
                    gone |= b
            prune_rounds.append({'round': len(prune_rounds) + 1,
                                 'before': names(naive), 'support': decisions,
                                 'removed': names(gone),
                                 'after': names(naive & ~gone)})
            if not gone:
                break
            naive &= ~gone
        naive_final = closure(naive)
        assert final == closure(new_facts), 'DRed must match rematerialization'
        steps.append({'step': len(steps), 'update': deepcopy(update),
                      'facts_before': names(facts), 'closure_before': names(current),
                      'effective_delete': names(removed), 'effective_insert': names(inserted),
                      'facts_after': names(new_facts), 'overdelete_rounds': over_rounds,
                      'overdeleted': names(deleted), 'survivors': names(survivors),
                      'rederive': reseed, 'one_step_rederived': names(rederived),
                      'insertion_seed': names((rederived | inserted) & ~survivors),
                      'insertion_rounds': insert_rounds, 'closure_after': names(final),
                      'lost': names(current & ~final), 'gained': names(final & ~current),
                      'restored': names(deleted & final),
                      'local_prune_rounds': prune_rounds,
                      'local_prune_closure': names(naive_final),
                      'unsupported_retained': names(naive_final & ~final),
                      'local_prune_agrees': naive_final == final})
        facts, current = new_facts, final
    return {'schema': 'hornlab-updates-v1', 'input': data,
            'initial_closure': names(initial), 'steps': steps,
            'final_facts': names(facts), 'final_closure': names(current)}
