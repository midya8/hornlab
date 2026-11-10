import json,subprocess,sys
from pathlib import Path
import hornlab.updates,hornlab.update_verify
from hornlab.updates import maintain
from hornlab.update_verify import verify_updates
root=Path(sys.argv[1]).resolve()
for m in [hornlab.updates,hornlab.update_verify]:assert not Path(m.__file__).resolve().is_relative_to(root)
controls=json.load(open('expected-updates.json'))
for c in controls:
 assert maintain(c['input'])==c['report'] and verify_updates(c['report'])
 Path('input.json').write_text(json.dumps(c['input']))
 for cli in [[sys.executable,'-m','hornlab'],['hornlab']]:
  subprocess.run(cli+['--updates','input.json','-o','report.json'],check=True,capture_output=True)
  assert json.load(open('report.json'))==c['report']
  assert json.loads(subprocess.check_output(cli+['--updates','--verify','report.json']))=={'valid':True}
  forged=json.loads(Path('report.json').read_text());forged['final_closure']=['forged'];Path('forged.json').write_text(json.dumps(forged))
  assert subprocess.run(cli+['--updates','--verify','forged.json'],capture_output=True).returncode==2
print('installed update reports',len(controls),'both entry points, forgery rejected')
