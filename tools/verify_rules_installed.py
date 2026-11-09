import json
from pathlib import Path
import subprocess
import sys
import hornlab
import hornlab.core
import hornlab.verify
import hornlab.rule_audit
import hornlab.rule_verify
import hornlab.__main__
from hornlab.rule_audit import audit_rules as analyze
from hornlab.rule_verify import verify_rules as verify
root = Path(sys.argv[1]).resolve()
origins = {name: str(Path(sys.modules[name].__file__).resolve()) for name in ['hornlab', 'hornlab.core', 'hornlab.verify', 'hornlab.__main__', 'hornlab.rule_audit', 'hornlab.rule_verify']}
assert all(not Path(p).is_relative_to(root) for p in origins.values())
cs = json.load(open('expected-rules.json'))
for i, c in enumerate(cs):
    assert analyze(c['input']) == c['report'] and verify(c['report'])
    inp, rep = Path('input.json'), Path('report.json')
    inp.write_text(json.dumps(c['input']))
    for cli in [[sys.executable, '-m', 'hornlab'], ['hornlab']]:
        subprocess.run(cli + ['--rules', str(inp), '-o', str(rep)], check=True, capture_output=True)
        assert json.loads(rep.read_text()) == c['report']
        out = subprocess.run(cli + ['--rules', '--verify', str(rep)], check=True, capture_output=True)
        assert json.loads(out.stdout) == {'valid': True}
print(json.dumps({'installed_reports': len(cs), 'CLIs': 2, 'modes': ['analyze', 'verify'], 'module_origins': origins}))
