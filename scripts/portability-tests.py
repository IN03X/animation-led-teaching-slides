"""Regression checks for the bundled two-slide edge fixture after build/review/PDF."""
import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from lxml import etree as E
from PIL import Image, ImageChops
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('teaching_workflow', HERE / 'workflow.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('workspace', type=Path)
parser.add_argument('--run-id', default='edge')
parser.add_argument('--pdf', type=Path, required=True)
args = parser.parse_args()
engine = args.workspace.resolve() / workflow.ENGINE
folder = engine / 'methods-work' / args.run_id
manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
package = json.loads((folder / 'package-check.json').read_text(encoding='utf-8'))
stages = json.loads((folder / 'stages.json').read_text(encoding='utf-8'))
timeline = json.loads((folder / 'timeline-stages.json').read_text(encoding='utf-8'))
assert manifest['genericContent'] and manifest['total'] == 2
assert not package.get('inheritedSlides') and 'clickMedia' not in package
assert {v['target'] for v in manifest['links']} == {'cover'}
assert {(v['slide'], v['stage']) for v in stages} == {(1, 0), (1, 1), (1, 2), (2, 0), (2, 1)}
assert {v['slide'] for v in timeline['frames']} == {1, 2}
old_schema = 'C:/Users/10486/.codex/skills/pptx/scripts/office/schemas/'
assert not any(old_schema in p.read_text(encoding='utf-8') for p in engine.glob('*.py'))
node, python, env = workflow.environment()
native_run = folder / ('pdf-manifest-regression-' + uuid4().hex[:8])
env.update(PDF_RUN=str(native_run), PDF_SOURCE=str(folder / 'candidate.pptx'),
           PDF_T4_MANIFEST=str(folder / 'manifest.json'), PDF_T4_PACKAGE=str(folder / 'package-check.json'),
           PDF_EXPECTED_SLIDES='2')
subprocess.run([str(python), '-B', str(engine / 'export-pdf.py'), 'prepare'], env=env, check=True)
ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(native_run / 'static.pptx') as archive:
    page = E.fromstring(archive.read('ppt/slides/slide1.xml'))
point = next(s for s in page.findall('p:cSld/p:spTree/p:sp', ns)
             if s.find('p:nvSpPr/p:cNvPr', ns).get('name') == 'moving-point')
x = int(point.find('p:spPr/a:xfrm/a:off', ns).get('x'))
assert x == 200 * 9525, f'Relocation applied more than once: {x / 9525}'
pdf = PdfReader(args.pdf)
assert len(pdf.pages) == 2 and sum(len(p.get('/Annots', [])) for p in pdf.pages) == 2
assert not pdf.metadata.get('/Author')
for number, page in enumerate(pdf.pages, 1):
    expected_path = folder / 'pdf-export' / f'slide-{number:03}.png'
    with Image.open(expected_path) as expected:
        actual = page.images[0].image
        assert ImageChops.difference(expected.convert('RGB'), actual.convert('RGB')).getbbox() is None
result = {'genericEndNavigation': True, 'emptyDemosReview': True, 'authoredCoverEndEndpoints': 5,
          'authoredCoverEndModeledFrames': len(timeline['frames']), 'externalAuthorSchemaPathAbsent': True,
          'singleRelocationLogicalX': x / 9525, 'manifestPdfWithoutMedia': True,
          'pdfPages': 2, 'pdfLinks': 2, 'pdfImagePixelsPreserved': True, 'pdfAuthorLeak': False,
          'nativePlaybackTested': False}
workflow.write_json(folder / 'portability-checks.json', result)
print(json.dumps(result, indent=2))
