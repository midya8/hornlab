"""Set-based reconstruction and exhaustive model-intersection update checker.

Shares only strict update/input validation with generation. It does not import
or call the update generator or its closure routine.
"""
import json
from .updates import validate_updates


def verify_updates(report):
    if type(report) is not dict or 'input' not in report:
        raise ValueError('Expected an update evidence report')
    data = validate_updates(report['input'])
    atoms = data['program']['atoms']
    rules = data['program']['rules']
    bodies = [set(r['if']) for r in rules]
    order = lambda xs: [a for a in atoms if a in xs]

    def intersection(seed):
        # All definite-Horn models contain the least model. Their intersection
        # computes it without running forward chaining.
        result = set(atoms)
        for m in range(1 << len(atoms)):
            model = {a for i, a in enumerate(atoms) if m & (1 << i)}
            if not seed <= model:
                continue
            if any(body <= model and r['then'] not in model
                   for body, r in zip(bodies, rules)):
                continue
            result &= model
        return result

    explicit = set(data['program']['facts'])
    materialized = intersection(explicit)
    initial = order(materialized)
    steps = []
    for index, change in enumerate(data['updates']):
        deletes = explicit.intersection(change['delete'])
        adds = set(change['insert']).difference(explicit)
        next_explicit = (explicit - deletes) | adds
        erased = set()
        frontier = set(deletes)
        over = []
        while True:
            rows = []
            successors = set()
            for i, (body, rule) in enumerate(zip(bodies, rules)):
                old_ready = body <= materialized
                touched = not body.isdisjoint(frontier)
                active = old_ready and touched
                new = active and rule['then'] not in erased | frontier
                rows.append({'rule': i, 'old_body_holds': old_ready,
                             'touched_delta': touched, 'fires': active,
                             'new_head': new})
                if new:
                    successors.add(rule['then'])
            over.append({'round': len(over) + 1,
                         'deleted_before': order(erased), 'delta': order(frontier),
                         'rules': rows, 'added': order(successors),
                         'deleted_after': order(erased | frontier)})
            erased.update(frontier)
            if not successors:
                break
            frontier = successors
        assert erased <= materialized
        retained = materialized - erased
        one_step = set()
        reconstruction = []
        for atom in order(erased):
            ids = [i for i, rule in enumerate(rules)
                   if rule['then'] == atom and bodies[i] <= retained]
            seed = atom in explicit - deletes
            recovers = seed or bool(ids)
            reconstruction.append({'atom': atom, 'surviving_explicit': seed,
                                   'surviving_rule_ids': ids, 'rederived': recovers})
            if recovers:
                one_step.add(atom)
        delta = (one_step | adds) - retained
        insertion_seed = order(delta)
        state = retained | delta
        insertion = []
        while True:
            rows = []
            new = set()
            for i, (body, rule) in enumerate(zip(bodies, rules)):
                touched = bool(body & delta)
                missing = body - state
                fires = touched and not missing
                novel = fires and rule['then'] not in state
                rows.append({'rule': i, 'touched_delta': touched,
                             'missing': order(missing), 'fires': fires,
                             'new_head': novel})
                if novel:
                    new.add(rule['then'])
            insertion.append({'round': len(insertion) + 1, 'before': order(state),
                              'delta': order(delta), 'rules': rows,
                              'added': order(new), 'after': order(state | new)})
            state.update(new)
            if not new:
                break
            delta = new
        truth = intersection(next_explicit)
        if state != truth:
            raise ValueError('Incremental result differs from definite-model intersection')
        local = materialized | adds
        pruning = []
        while True:
            support = []
            gone = set()
            for atom in order(local):
                ids = [i for i, rule in enumerate(rules)
                       if rule['then'] == atom and bodies[i] <= local]
                seed = atom in next_explicit
                count = int(seed) + len(ids)
                support.append({'atom': atom, 'explicit': seed, 'rule_ids': ids,
                                'local_count': count})
                if not count:
                    gone.add(atom)
            pruning.append({'round': len(pruning) + 1, 'before': order(local),
                            'support': support, 'removed': order(gone),
                            'after': order(local - gone)})
            local.difference_update(gone)
            if not gone:
                break
        local_final = intersection(local)
        steps.append({'step': index, 'update': change,
                      'facts_before': order(explicit), 'closure_before': order(materialized),
                      'effective_delete': order(deletes), 'effective_insert': order(adds),
                      'facts_after': order(next_explicit), 'overdelete_rounds': over,
                      'overdeleted': order(erased), 'survivors': order(retained),
                      'rederive': reconstruction, 'one_step_rederived': order(one_step),
                      'insertion_seed': insertion_seed, 'insertion_rounds': insertion,
                      'closure_after': order(truth), 'lost': order(materialized - truth),
                      'gained': order(truth - materialized), 'restored': order(erased & truth),
                      'local_prune_rounds': pruning, 'local_prune_closure': order(local_final),
                      'unsupported_retained': order(local_final - truth),
                      'local_prune_agrees': local_final == truth})
        explicit, materialized = next_explicit, truth
    expected = {'schema': 'hornlab-updates-v1', 'input': data,
                'initial_closure': initial, 'steps': steps,
                'final_facts': order(explicit), 'final_closure': order(materialized)}
    # JSON canonicalization distinguishes booleans and integers, unlike Python
    # dict equality; it also rejects extra/missing fields and reordered arrays.
    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if canonical(report) != canonical(expected):
        raise ValueError('Update evidence does not match the independent reconstruction')
    return True
