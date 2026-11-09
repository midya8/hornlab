import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from hornlab.rule_audit import audit_rules
from hornlab.rule_verify import verify_rules

CONTROLS = json.loads((Path(__file__).parents[1] / 'docs/rule-controls.json').read_text())

class RuleTests(unittest.TestCase):
    def test_controls_and_dualities(self):
        for c in CONTROLS:
            r = audit_rules(c['input'])
            self.assertTrue(verify_rules(r), c['name'])
            for q in r['queries']:
                self.assertEqual(q['minimal_hitting_supports'], [s['mask'] for s in q['cuts']])
                self.assertEqual(q['minimal_hitting_cuts'], [s['mask'] for s in q['supports']])
    def test_exhaustive_two_atom_programs(self):
        atoms = ['a', 'b']
        bodies = [[], ['a'], ['b'], ['a', 'b']]
        rules = [{'if': b, 'then': h} for b in bodies for h in atoms]
        for mask in range(256):
            selected = [r for i, r in enumerate(rules) if mask & (1 << i)]
            for fm in range(4):
                data = {'atoms': atoms, 'facts': [a for i, a in enumerate(atoms) if fm & (1 << i)], 'rules': selected}
                self.assertTrue(verify_rules(audit_rules(data)), (mask, fm))
    def test_seeded_and_immutable(self):
        rng = random.Random(733)
        for _ in range(150):
            atoms = list('abcdef')[:rng.randrange(7)]
            data = {'atoms': atoms, 'facts': [a for a in atoms if rng.randrange(2)], 'rules': [{'if': [a for a in atoms if rng.randrange(2)], 'then': rng.choice(atoms)} for _ in range(rng.randrange(9))] if atoms else []}
            original = copy.deepcopy(data)
            self.assertTrue(verify_rules(audit_rules(data)))
            self.assertEqual(data, original)
    def test_routes_boundaries_duplicates(self):
        r = audit_rules(CONTROLS[0]['input'])
        q = r['queries'][-1]
        self.assertEqual([s['rules'] for s in q['supports']], [[0], [1, 2]])
        self.assertEqual([s['removed'] for s in q['cuts']], [[0, 1], [0, 2]])
        q = r['queries'][0]
        self.assertEqual([s['mask'] for s in q['supports']], [0])
        self.assertEqual(q['cuts'], [])
        data = {'atoms': ['a'], 'facts': [], 'rules': [{'if': ['a'], 'then': 'a'}]}
        q = audit_rules(data)['queries'][0]
        self.assertEqual(q['supports'], [])
        self.assertEqual([s['mask'] for s in q['cuts']], [0])
        data['rules'] = [{'if': [], 'then': 'a'}] * 2
        q = audit_rules(data)['queries'][0]
        self.assertEqual([s['mask'] for s in q['supports']], [1, 2])
        self.assertEqual([s['mask'] for s in q['cuts']], [3])
    def test_independence_and_forgeries(self):
        r = audit_rules(CONTROLS[0]['input'])
        with patch('hornlab.rule_audit.audit_rules', side_effect=AssertionError('generator called')):
            self.assertTrue(verify_rules(r))
        for change in [lambda x: x.update(extra=True), lambda x: x['subsets'][0].update(mask=False), lambda x: x['subsets'][0]['closure'].append('goal'), lambda x: x['subsets'][-1]['added_rounds'].pop(), lambda x: x['queries'][-1]['supports'].pop(), lambda x: x['queries'][-1]['cuts'][0]['restorations'].pop(), lambda x: x['queries'][-1]['minimal_hitting_supports'].pop(), lambda x: x['queries'][-1]['intersections'][0].update(rules=[])]:
            forged = copy.deepcopy(r)
            change(forged)
            self.assertFalse(verify_rules(forged))
    def test_permutation_equivariance(self):
        data = CONTROLS[0]['input']
        r = audit_rules(data)
        reverse = copy.deepcopy(data)
        reverse['rules'].reverse()
        rr = audit_rules(reverse)
        for q, qq in zip(r['queries'], rr['queries']):
            for field, items in [('supports', 'rules'), ('cuts', 'removed')]:
                expected = {tuple(sorted(len(data['rules']) - 1 - i for i in s[items])) for s in q[field]}
                self.assertEqual(expected, {tuple(s[items]) for s in qq[field]})
    def test_cli_strict_and_atomic(self):
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d) / 'input.json', Path(d) / 'out.json'
            inp.write_text(json.dumps(CONTROLS[0]['input']))
            command = [sys.executable, '-m', 'hornlab', '--rules']
            subprocess.run(command + [str(inp), '-o', str(out)], check=True, capture_output=True)
            r = json.loads(out.read_text())
            self.assertEqual(r, audit_rules(CONTROLS[0]['input']))
            subprocess.run(command + ['--verify', str(out)], check=True, capture_output=True)
            original = out.read_bytes()
            for bad in ['{"atoms":[],"atoms":[],"facts":[],"rules":[]}', '{"atoms":NaN,"facts":[],"rules":[]}', ' ' * 65537]:
                inp.write_text(bad)
                p = subprocess.run(command + [str(inp), '-o', str(out)], capture_output=True)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(out.read_bytes(), original)
    def test_invalid_boundaries(self):
        for data in [{}, {'atoms': ['a'] * 2, 'facts': [], 'rules': []}, {'atoms': [], 'facts': [], 'rules': [{}] * 9}]:
            with self.assertRaises(ValueError): audit_rules(data)
        self.assertFalse(verify_rules({}))
        self.assertTrue(verify_rules(audit_rules({'atoms': [], 'facts': [], 'rules': []})))
