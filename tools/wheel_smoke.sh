#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
cd "$root"
python - "$scratch/expected.json" <<'PY'
import json,sys
from hornlab import analyze
cs=json.load(open('docs/controls.json'))
json.dump([{'input':c['input'],'report':analyze(c['input'])} for c in cs],open(sys.argv[1],'w'))
PY
python - "$scratch/expected-rules.json" <<'PYRULES'
import json,sys
from hornlab.rule_audit import audit_rules
cs=json.load(open('docs/rule-controls.json'))
json.dump([{'input':c['input'],'report':audit_rules(c['input'])} for c in cs],open(sys.argv[1],'w'))
PYRULES
python - "$scratch/expected-updates.json" <<'PYUPDATES'
import json,sys
from hornlab.updates import maintain
cs=json.load(open('docs/update-controls.json'))
json.dump([{'input':c['request'],'report':maintain(c['request'])} for c in cs],open(sys.argv[1],'w'))
PYUPDATES
uv build --wheel --out-dir "$scratch/dist"
uv venv "$scratch/env"
uv pip install --python "$scratch/env/bin/python" "$scratch"/dist/*.whl
cp tools/verify_installed.py "$scratch/verify_installed.py"
cp tools/verify_rules_installed.py "$scratch/verify_rules_installed.py"
cp tools/verify_updates_installed.py "$scratch/verify_updates_installed.py"
cd "$scratch"
PATH="$scratch/env/bin:$PATH" PYTHONPATH= "$scratch/env/bin/python" verify_installed.py "$root" expected.json
PATH="$scratch/env/bin:$PATH" PYTHONPATH= "$scratch/env/bin/python" verify_rules_installed.py "$root" expected-rules.json

PATH="$scratch/env/bin:$PATH" PYTHONPATH= "$scratch/env/bin/python" verify_updates_installed.py "$root" expected-updates.json
