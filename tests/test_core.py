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
from hornlab import analyze, validate, verify

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = json.loads((ROOT / 'docs/controls.json').read_text())


class HornTests(unittest.TestCase):
    def test_controls_and_model_intersection(self):
        for c in CONTROLS:
            r = analyze(c['input'])
            self.assertTrue(verify(r), c['name'])
            intersection = set.intersection(*(set(m['atoms']) for m in r['models']))
            self.assertEqual(intersection, set(r['least_model']))
            self.assertEqual(sum(m['least'] for m in r['models']), 1)
            self.assertLessEqual(len(r['rounds']), len(c['input']['atoms']) + 1)
            for q in r['queries']:
                self.assertEqual(q['entailed'], all(q['atom'] in m['atoms'] for m in r['models']))
                if not q['entailed']:
                    m = next(m for m in r['models'] if m['mask'] == q['countermodel'])
                    self.assertNotIn(q['atom'], m['atoms'])

    def test_circle_not_proof(self):
        r = analyze(CONTROLS[0]['input'])
        self.assertEqual(r['least_model'], ['seed'])
        self.assertGreater(sum(m['supported'] for m in r['models']), 1)
        self.assertTrue(all(not q['entailed'] and q['minimal_supports'] == [] for q in r['queries'][1:]))
        self.assertTrue(any(m['atoms'] == r['input']['atoms'] for m in r['models']))

    def test_supports_not_minimum_only(self):
        r = analyze(CONTROLS[1]['input'])
        self.assertEqual([s['facts'] for s in r['queries'][-1]['minimal_supports']], [['a'], ['b', 'c']])
        self.assertEqual(r['queries'][-1]['first_achievers'], [0, 1])

    def test_synchronous_unit_duplicates_empty(self):
        r = analyze(CONTROLS[2]['input'])
        self.assertEqual([q['first_round'] for q in r['queries']], [0, 1, 2])
        r = analyze(CONTROLS[3]['input'])
        self.assertEqual(r['queries'][1]['minimal_supports'][0]['facts'], [])
        r = analyze(CONTROLS[4]['input'])
        self.assertEqual(r['queries'][1]['first_achievers'], [0, 1])
        r = analyze(CONTROLS[7]['input'])
        self.assertEqual(r['models'], [{'mask': 0, 'atoms': [], 'supported': True, 'least': True}])
        self.assertEqual(r['queries'], [])

    def test_exhaustive_two_atom_programs(self):
        atoms = ['a', 'b']
        choices = [{'if': [a for i, a in enumerate(atoms) if m & (1 << i)], 'then': h} for m in range(4) for h in atoms]
        for rm in range(256):
            for fm in range(4):
                data = {'atoms': atoms, 'facts': [a for i, a in enumerate(atoms) if fm & (1 << i)], 'rules': [r for i, r in enumerate(choices) if rm & (1 << i)]}
                r = analyze(data)
                self.assertTrue(verify(r), (rm, fm))

    def test_random_and_input_immutability(self):
        rng = random.Random(6201)
        for _ in range(400):
            atoms = list('abcdef')[:rng.randrange(7)]
            rules = [{'if': [a for a in atoms if rng.randrange(2)], 'then': rng.choice(atoms)} for _ in range(rng.randrange(9))] if atoms else []
            data = {'atoms': atoms, 'facts': [a for a in atoms if rng.randrange(2)], 'rules': rules}
            old = copy.deepcopy(data)
            r = analyze(data)
            self.assertEqual(data, old)
            self.assertTrue(verify(r))
            r['input']['facts'].clear()
            self.assertEqual(data, old)

    def test_verifier_independent_and_forgery_strict(self):
        r = analyze(CONTROLS[0]['input'])
        with patch('hornlab.core.analyze', side_effect=RuntimeError('generator must not run')):
            self.assertTrue(verify(r))
        for key in r:
            bad = copy.deepcopy(r); bad.pop(key)
            self.assertFalse(verify(bad), key)
        bad = copy.deepcopy(r); bad['extra'] = 1
        self.assertFalse(verify(bad))
        for section in ['rounds', 'models', 'ablations', 'queries']:
            for i, row in enumerate(r[section]):
                for key in row:
                    bad = copy.deepcopy(r); bad[section][i][key] = 'forged'
                    self.assertFalse(verify(bad), (section, i, key))
        bad = copy.deepcopy(r); bad['models'][0]['mask'] = True
        self.assertFalse(verify(bad))
        bad = copy.deepcopy(r); bad['queries'][0]['first_round'] = False
        self.assertFalse(verify(bad))
        bad = copy.deepcopy(r); bad['rounds'][0]['rules'][0]['ready'] = True
        self.assertFalse(verify(bad))
        r = analyze(CONTROLS[1]['input'])
        bad = copy.deepcopy(r); bad['queries'][-1]['minimal_supports'].pop()
        self.assertFalse(verify(bad))
        bad = copy.deepcopy(r); bad['queries'][-1]['minimal_supports'][0]['deletions'][0]['closure'] = ['goal']
        self.assertFalse(verify(bad))

    def test_invalid_programs(self):
        base = CONTROLS[0]['input']
        bads = [None, {}, {**base, 'extra': 1}, {**base, 'atoms': ['a', 'a']}, {**base, 'facts': ['missing']}, {**base, 'facts': ['seed', 'seed']}, {**base, 'rules': [{'if': [], 'then': 'absent'}]}, {**base, 'rules': [{'if': ['seed', 'seed'], 'then': 'seed'}]}, {**base, 'rules': [{'if': [], 'then': 'seed', 'not': []}]}, {**base, 'atoms': ['a'] * 7}, {**base, 'rules': [{'if': [], 'then': 'seed'}] * 9}, {**base, 'atoms': [True]}, {**base, 'atoms': ['<script>']}]
        for bad in bads:
            with self.assertRaises(ValueError): validate(bad)

    def test_permutation_equivariance(self):
        d = copy.deepcopy(CONTROLS[-1]['input']); r = analyze(d)
        d['atoms'].reverse(); d['facts'].reverse(); d['rules'].reverse()
        t = analyze(d)
        self.assertEqual(set(r['least_model']), set(t['least_model']))
        self.assertEqual({frozenset(m['atoms']) for m in r['models']}, {frozenset(m['atoms']) for m in t['models']})
        for q in r['queries']:
            qq = next(x for x in t['queries'] if x['atom'] == q['atom'])
            self.assertEqual({frozenset(s['facts']) for s in q['minimal_supports']}, {frozenset(s['facts']) for s in qq['minimal_supports']})

    def test_cli_atomic_strict_verify(self):
        with tempfile.TemporaryDirectory() as td:
            source, out = Path(td)/'input.json', Path(td)/'out.json'
            source.write_text(json.dumps(CONTROLS[1]['input']))
            p = subprocess.run([sys.executable, '-m', 'hornlab', str(source), '-o', str(out)], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            report = json.loads(out.read_text()); self.assertTrue(verify(report))
            p = subprocess.run([sys.executable, '-m', 'hornlab', '--verify', str(out)], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout), {'valid': True})
            old = out.read_bytes()
            for text in ['{"atoms":[],"atoms":[],"facts":[],"rules":[]}', '{"atoms":NaN,"facts":[],"rules":[]}', '{}', ' ' * 65537]:
                source.write_text(text)
                p = subprocess.run([sys.executable, '-m', 'hornlab', str(source), '-o', str(out)], capture_output=True)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(out.read_bytes(), old)
            source.write_text('{}')
            p = subprocess.run([sys.executable, '-m', 'hornlab', '--verify', str(source)], capture_output=True)
            self.assertEqual(p.returncode, 2)


if __name__ == '__main__': unittest.main()
