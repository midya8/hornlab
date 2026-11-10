import copy
import itertools
import random
import unittest
from hornlab.updates import maintain, validate_updates
from hornlab.update_verify import verify_updates
from make_update_controls import controls


class UpdateTests(unittest.TestCase):
    def test_controls(self):
        reports = [maintain(c['request']) for c in controls()]
        for report in reports:
            self.assertTrue(verify_updates(report))
        first = reports[0]['steps'][0]
        self.assertEqual(first['closure_after'], [])
        self.assertEqual(first['unsupported_retained'], ['p', 'q'])
        self.assertEqual(reports[1]['steps'][0]['restored'], ['x', 'y'])
        self.assertEqual(reports[4]['steps'][0]['closure_after'], ['a', 'b'])
        self.assertEqual(reports[-1]['final_closure'], [])

    def test_every_two_atom_program_and_fact_transition(self):
        atoms = ['a', 'b']
        subsets = [[a for i, a in enumerate(atoms) if m & (1 << i)] for m in range(4)]
        rules = [{'if': body, 'then': head} for body in subsets for head in atoms]
        count = 0
        for rmask in range(256):
            rs = [r for i, r in enumerate(rules) if rmask & (1 << i)]
            for old, new in itertools.product(subsets, repeat=2):
                data = {'program': {'atoms': atoms, 'facts': old, 'rules': rs},
                        'updates': [{'delete': [a for a in old if a not in new],
                                     'insert': [a for a in new if a not in old]}]}
                self.assertTrue(verify_updates(maintain(data)))
                count += 1
        self.assertEqual(count, 4096)

    def test_seeded_six_atom_update_sequences(self):
        rng = random.Random(73051)
        for _ in range(350):
            atoms = list('abcdef')[:rng.randrange(7)]
            subset = lambda: [a for a in atoms if rng.randrange(2)]
            rules = [{'if': subset(), 'then': rng.choice(atoms)} for _ in range(rng.randrange(9))] if atoms else []
            updates = []
            for _ in range(8):
                deleted = subset()
                updates.append({'delete': deleted,
                                'insert': [a for a in subset() if a not in deleted]})
            self.assertTrue(verify_updates(maintain({'program': {'atoms': atoms,
                                       'facts': subset(), 'rules': rules}, 'updates': updates})))

    def test_every_leaf_and_record_forgery(self):
        report = maintain(controls()[1]['request'])
        paths = []
        def visit(value, path):
            if isinstance(value, dict):
                for k, v in value.items():
                    visit(v, path + [k])
            elif isinstance(value, list):
                paths.append((path, value))
                for i, v in enumerate(value):
                    visit(v, path + [i])
            else:
                paths.append((path, value))
        visit(report, [])
        for path, value in paths:
            if path and path[0] == 'input':
                continue
            altered = copy.deepcopy(report)
            target = altered
            for key in path[:-1]:
                target = target[key]
            replacement = value + ['forged'] if isinstance(value, list) else (
                int(value) if type(value) is bool else value + 1 if type(value) is int else str(value) + 'forged')
            target[path[-1]] = replacement
            with self.assertRaises((ValueError, TypeError)):
                verify_updates(altered)
        for key in report:
            altered = copy.deepcopy(report)
            del altered[key]
            with self.assertRaises(ValueError):
                verify_updates(altered)
        altered = copy.deepcopy(report)
        altered['extra'] = True
        with self.assertRaises(ValueError):
            verify_updates(altered)

    def test_cli_atomic_and_mutually_exclusive_modes(self):
        import json, subprocess, sys, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d)/'input.json', Path(d)/'out.json'
            inp.write_text(json.dumps(controls()[0]['request']))
            subprocess.run([sys.executable,'-m','hornlab','--updates',str(inp),'-o',str(out)],check=True,capture_output=True)
            self.assertTrue(verify_updates(json.loads(out.read_text())))
            self.assertEqual(json.loads(subprocess.check_output([sys.executable,'-m','hornlab','--updates','--verify',str(out)])),{'valid':True})
            inp.write_text('{}')
            before=out.read_bytes()
            self.assertEqual(subprocess.run([sys.executable,'-m','hornlab','--updates',str(inp),'-o',str(out)],capture_output=True).returncode,2)
            self.assertEqual(out.read_bytes(),before)
            self.assertEqual(subprocess.run([sys.executable,'-m','hornlab','--updates','--rules',str(inp)],capture_output=True).returncode,2)
            inp.write_text('{"program":{},"program":{},"updates":[]}')
            self.assertEqual(subprocess.run([sys.executable,'-m','hornlab','--updates',str(inp)],capture_output=True).returncode,2)

    def test_immutability_empty_sequence_and_reordered_atoms(self):
        for c in controls():
            data=copy.deepcopy(c['request']);before=copy.deepcopy(data)
            report=maintain(data);verify_updates(report)
            self.assertEqual(data,before)
            altered=copy.deepcopy(data);altered['program']['atoms'].reverse()
            other=maintain(altered)
            self.assertEqual(set(other['final_closure']),set(report['final_closure']))
            for x,y in zip(other['steps'],report['steps']):
                for key in ['closure_after','overdeleted','restored','unsupported_retained']:
                    self.assertEqual(set(x[key]),set(y[key]))
        empty={'program':{'atoms':[],'facts':[],'rules':[]},'updates':[]}
        self.assertTrue(verify_updates(maintain(empty)))
        self.assertEqual(maintain(empty)['steps'],[])

    def test_checker_does_not_call_generators(self):
        from unittest.mock import patch
        report=maintain(controls()[0]['request'])
        with patch('hornlab.updates.maintain',side_effect=AssertionError('generator called')), patch('hornlab.core.analyze',side_effect=AssertionError('base generator called')):
            self.assertTrue(verify_updates(report))

    def test_strict_scope(self):
        good = controls()[0]['request']
        for change in [lambda x: x.update(extra=1),
                       lambda x: x.update(updates=[{}]),
                       lambda x: x.update(updates=[{'delete': ['p'], 'insert': ['p']}]),
                       lambda x: x.update(updates=[{'delete': ['missing'], 'insert': []}]),
                       lambda x: x.update(updates=[{'delete': ['p', 'p'], 'insert': []}]),
                       lambda x: x.update(updates=[{'delete': [], 'insert': []}] * 9),
                       lambda x: x['program']['rules'][0].update(negative=['p'])]:
            bad = copy.deepcopy(good)
            change(bad)
            with self.assertRaises(ValueError):
                validate_updates(bad)


if __name__ == '__main__':
    unittest.main()
