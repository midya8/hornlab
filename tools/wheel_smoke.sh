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
uv build --wheel --out-dir "$scratch/dist"
uv venv "$scratch/env"
uv pip install --python "$scratch/env/bin/python" "$scratch"/dist/*.whl
cp tools/verify_installed.py "$scratch/verify_installed.py"
cd "$scratch"
PATH="$scratch/env/bin:$PATH" PYTHONPATH= "$scratch/env/bin/python" verify_installed.py "$root" expected.json
