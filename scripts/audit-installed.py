"""Read-only verification of frame timing already installed in a private PPTX."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

run = Path(sys.argv[1]).resolve()
helper = run.parent.parent / 't4-click-media.py'
spec = importlib.util.spec_from_file_location('archived_click_media', helper)
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)
lib = media._library()
data = lib['read'](run / 'candidate.pptx')
package = json.loads((run / 'package-check.json').read_text(encoding='utf-8'))
if 'clickMedia' in package:
    checks = media.validate(data, package['clickMedia'], lib)
else:
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
    assert not manifest['gifs'] and not any(v.get('playMedia') for v in manifest['animation']), 'Missing installed media ledger'
    checks = {'embeddedPngFrames': 0, 'reason': 'No frame demonstrations authored; native object/formula animation remains reviewed separately', 'nativePlaybackTested': False}
print(json.dumps({'candidateSha256': hashlib.sha256((run / 'candidate.pptx').read_bytes()).hexdigest(),
                  'readOnly': True, 'installedMediaChecks': checks}))
