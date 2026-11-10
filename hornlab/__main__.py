import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import analyze
from .verify import verify
from .rule_audit import audit_rules
from .rule_verify import verify_rules
from .updates import maintain
from .update_verify import verify_updates


def strict(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError('Duplicate JSON key: ' + k)
        out[k] = v
    return out


def main():
    p = argparse.ArgumentParser(description='Inspect finite positive propositional Horn inference')
    p.add_argument('input')
    p.add_argument('--verify', action='store_true')
    modes = p.add_mutually_exclusive_group()
    modes.add_argument('--updates', action='store_true', help='Maintain a fact-update sequence, or verify its report with --verify')
    modes.add_argument('--rules', action='store_true', help='Audit rule subsets with fixed facts, or verify a rule report with --verify')
    p.add_argument('-o', '--output')
    a = p.parse_args()
    try:
        raw = Path(a.input).read_bytes()
        if len(raw) > (8 * 1024 * 1024 if a.verify else 65536):
            raise ValueError('Input exceeds byte limit')
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=strict, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Non-finite JSON')))
        checker = verify_updates if a.updates else verify_rules if a.rules else verify
        generator = maintain if a.updates else audit_rules if a.rules else analyze
        out = {'valid': checker(data)} if a.verify else generator(data)
        if a.verify and not out['valid']:
            raise ValueError('Invalid HornLab report')
        text = json.dumps(out, indent=2, allow_nan=False) + '\n'
        if a.output:
            target = Path(a.output)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as f:
                tmp = f.name
                f.write(text)
            try:
                os.replace(tmp, target)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
        else:
            print(text, end='')
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as e:
        p.exit(2, 'hornlab: ' + str(e) + '\n')


if __name__ == '__main__':
    main()
