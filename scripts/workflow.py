"""Stage, build and inspect the archived teaching engine without live-project access."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ENGINE = Path('tmp/tutorial_base/tutorial3')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime():
    home = Path.home()
    deps = Path(os.environ.get('CODEX_DEPENDENCIES', home / '.cache/codex-runtimes/codex-primary-runtime/dependencies'))
    node = Path(os.environ.get('TEACHING_NODE', deps / 'node/bin/node.exe'))
    python = Path(os.environ.get('TEACHING_PYTHON', deps / 'python/python.exe'))
    tex = os.environ.get('TEX_BIN')
    candidates = [Path(tex)] if tex else []
    found = shutil.which('latex.exe')
    if found:
        candidates.append(Path(found).parent)
    candidates += [Path('D:/TeX/bin/windows')]
    for base in [Path('C:/texlive'), Path('D:/texlive'), Path('E:/texlive')]:
        if base.exists():
            candidates.extend(sorted(base.glob('*/bin/windows'), reverse=True))
    tex_path = next((p for p in candidates if (p / 'latex.exe').is_file() and (p / 'dvisvgm.exe').is_file()), None)
    return deps, node, python, tex_path


def environment():
    deps, node, python, tex = runtime()
    missing = [str(p) for p in [node, python, deps / 'node/node_modules/@oai/artifact-tool', deps / 'node/node_modules/sharp'] if not p.exists()]
    if tex is None:
        missing.append('latex.exe + dvisvgm.exe (set TEX_BIN)')
    if missing:
        raise RuntimeError('Missing prerequisites, no environment changes made: ' + ', '.join(missing))
    env = os.environ.copy()
    env.update(CODEX_DEPENDENCIES=deps.as_posix(), TEACHING_PYTHON=python.as_posix(),
               TEX_BIN=tex.as_posix(), RUNTIME_NODE_MODULES=(deps / 'node/node_modules').as_posix(),
               PRESENTATION_SKILL_DIR=(SKILL / 'assets/vendor/presentations').as_posix(),
               TEACHING_SCHEMA=(SKILL / 'assets/vendor/schemas/ISO-IEC29500-4_2016/pml.xsd').as_posix(),
               PYTHONDONTWRITEBYTECODE='1', TUTORIAL_NUMBER='5', T4_EDITION='classroom')
    return node, python, env


def run(command, env=None):
    subprocess.run([str(v) for v in command], env=env, check=True)


def patch_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'Archive adapter mismatch: {label} expected one match, found {count}')
    return text.replace(old, new)


def stage(workspace):
    workspace = workspace.resolve()
    if workspace.exists():
        raise ValueError('Choose a NEW isolated workspace; stage never overwrites an existing directory')
    source = SKILL / 'assets/recipe/project'
    if workspace.is_relative_to(SKILL):
        raise ValueError('Keep archive immutable: stage outside the skill directory')
    shutil.copytree(source, workspace)
    engine = workspace / ENGINE
    # Raw sources stay archived verbatim; adapt only this isolated working copy.
    for file in engine.glob('*'):
        if file.suffix not in ('.py', '.mjs'):
            continue
        text = file.read_text(encoding='utf-8')
        text = text.replace("const deps='C:/Users/10486/.cache/codex-runtimes/codex-primary-runtime/dependencies';",
                            "const deps=process.env.CODEX_DEPENDENCIES;if(!deps)throw Error('Run through workflow.py');")
        text = text.replace("python=deps+'/python/python.exe'", "python=process.env.TEACHING_PYTHON||deps+'/python/python.exe'")
        schema = 'C:/Users/10486/.codex/skills/pptx/scripts/office/schemas/ISO-IEC29500-4_2016/pml.xsd'
        text = text.replace("Path('" + schema + "')", "Path(__import__('os').environ['TEACHING_SCHEMA'])")
        text = text.replace("E.parse('" + schema + "')", "E.parse(__import__('os').environ['TEACHING_SCHEMA'])")
        if schema in text:
            raise RuntimeError('Unadapted external schema dependency in ' + file.name)
        if file.name == 't4-build.mjs':
            for line in ["import {content as fullContent} from './t4-mainline-story.mjs';",
                         "import {classroomContent} from './t4-classroom.mjs';",
                         "import {generateReceiverDemos} from './t4-receiver-demos.mjs';",
                         "import {generateDemos} from './t4-lecture-demos.mjs';"]:
                text = patch_once(text, line, '', 'unused T4 import')
            text = patch_once(text, "await (await import('./t5-demos.mjs')).generateDemos({run,sharp,python})",
                              "await (await import(process.env.TEACHING_DEMOS?pathToFileURL(path.resolve(process.env.TEACHING_DEMOS)).href:'./t5-demos.mjs')).generateDemos({run,sharp,python})", 'demo override')
            text = patch_once(text, "(await import('./t5-story.mjs')).content",
                              "(await import(process.env.TEACHING_STORY?pathToFileURL(path.resolve(process.env.TEACHING_STORY)).href:'./t5-story.mjs')).content", 'story override')
            text = patch_once(text, "if(classroom&&pages[v.slide-1].id==='end'&&v.name==='title')",
                              "if(!process.env.TEACHING_STORY&&classroom&&pages[v.slide-1].id==='end'&&v.name==='title')", 'generic end navigation')
            text = patch_once(text, "await fs.writeFile(path.join(run,'manifest.json'),JSON.stringify(manifest,null,2));",
                              "manifest.genericContent=!!process.env.TEACHING_STORY;\nif(manifest.genericContent){manifest.topic=process.env.TEACHING_TOPIC||'Teaching presentation';manifest.note7Aligned=false;delete manifest.sourceNote;}\nawait fs.writeFile(path.join(run,'manifest.json'),JSON.stringify(manifest,null,2));", 'generic manifest')
        if file.name == 't4-finalize.mjs':
            text = patch_once(text, "const skill=process.env.PRESENTATION_SKILL_DIR||'C:/Users/10486/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';", "const skill=process.env.PRESENTATION_SKILL_DIR;if(!skill)throw Error('Run through workflow.py');", 'vendored finalizer')
        if file.name == 't4-template.py':
            text = patch_once(text, "ending_ref=reference_slides[39]", "if manifest.get('genericContent'):opening_refs={}\n    ending_ref=reference_slides[39]", 'no copied course opening')
            text = patch_once(text, "ref=reference_slides[0] if info['id']=='cover' else ending_ref if info['id']=='end' else course_ref if is_course else title_ref",
                              "ref=title_ref if manifest.get('genericContent') else reference_slides[0] if info['id']=='cover' else ending_ref if info['id']=='end' else course_ref if is_course else title_ref", 'generic layout')
            text = patch_once(text, "if info['id'] in ['cover','end']:", "if info['id'] in ['cover','end'] and not manifest.get('genericContent'):", 'no copied identity')
        if file.name == 't4-package.py':
            text = patch_once(text, "and p['id'] not in {'cover','end'}", "and (m.get('genericContent') or p['id'] not in {'cover','end'})", 'generic cover and end endpoint coverage')
        if file.name == 'export-pdf.mjs':
            text = text.replace("execFileSync(deps+'/python/python.exe'", "execFileSync(process.env.TEACHING_PYTHON||deps+'/python/python.exe'")
        if file.name == 'export-pdf.py':
            text = text.replace("package['clickMedia']['mediaIndex']", "package.get('clickMedia',{}).get('mediaIndex',{})")
            text = patch_once(text, "for event in specs:", "manifest_relocated=set()\n            for event in specs:", 'PDF relocation ledger')
            text = patch_once(text, "manifest['motionEndpoints'].append({'slide':number,'shape':nv[0].get('id')})", "manifest_relocated.add(nv[0].get('id'))\n                manifest['motionEndpoints'].append({'slide':number,'shape':nv[0].get('id')})", 'PDF track resolved relocations')
            text = patch_once(text, "for sid,(dx,dy) in endpoints.items():", "for sid,(dx,dy) in endpoints.items():\n            if t4_manifest is not None and sid in manifest_relocated:continue", 'PDF avoid double relocation')
            text = patch_once(text, "c.setAuthor('WANG, Runbang; TIAN, Feng')", "c.setAuthor(os.environ.get('PDF_AUTHOR',''))", 'generic PDF author')
        file.write_text(text, encoding='utf-8')
    receipt = {'workspace': str(workspace), 'archive': str(SKILL), 'immutableArchive': True,
               'adapter': 'portable-t5-v1', 'liveCourseDirectoryRequired': False,
               'genericMode': 'Use --story and --demos; author your own cover, route, notes and end page'}
    write_json(workspace / 'stage-receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


def build(args):
    node, python, env = environment()
    workspace = args.workspace.resolve()
    if not (workspace / 'stage-receipt.json').is_file():
        raise ValueError('Not a staged workspace')
    if not args.run_id.replace('-', '').replace('_', '').isalnum():
        raise ValueError('run-id must contain only letters, digits, hyphens or underscores')
    env['BUILD_ID'] = args.run_id
    env['RENDER_PAGES'] = args.render_pages
    if args.story:
        if not args.demos:
            raise ValueError('A different topic must supply its own --demos module, even if it returns an empty object')
        env['TEACHING_STORY'] = args.story.resolve().as_posix()
        env['TEACHING_DEMOS'] = args.demos.resolve().as_posix()
        env['TEACHING_TOPIC'] = args.topic
    else:
        env.pop('TEACHING_STORY', None)
        env.pop('TEACHING_DEMOS', None)
    run([node, workspace / ENGINE / 't4-build.mjs'], env)
    print('Private build only. Nothing was published or opened in PowerPoint.')


def review(args):
    node, python, env = environment()
    engine = args.workspace.resolve() / ENGINE
    folder = engine / 'methods-work' / args.run_id
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    package = json.loads((folder / 'package-check.json').read_text(encoding='utf-8'))
    inherited = set(package.get('inheritedSlides', []))
    pages = args.pages or [i + 1 for i, p in enumerate(manifest['pages'])
                           if i + 1 not in inherited and (manifest.get('genericContent') or p['id'] not in ['cover', 'end'])]
    run([python, '-B', engine / 't4-timeline.py', folder, '--pages', *pages, '--times', 0, 350, 700, 1050], env)
    run([node, SKILL / 'scripts/review.mjs', folder], env)
    run([python, '-B', SKILL / 'scripts/audit-installed.py', folder], env)
    if args.golden:
        if manifest.get('genericContent'):
            raise ValueError('Golden regression assertions do not apply to different-topic content')
        run([node, engine / 't5-review.mjs', folder], env)


def export_pdf(args):
    node, python, env = environment()
    engine = args.workspace.resolve() / ENGINE
    folder = engine / 'methods-work' / args.run_id
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    output = args.output.resolve()
    if output.suffix.lower() != '.pdf':
        raise ValueError('Choose a .pdf output path')
    if output.exists():
        raise ValueError('PDF output already exists; no silent overwrite')
    if not output.parent.is_dir():
        raise ValueError('PDF output parent must already exist')
    env.update(PDF_RUN=str(folder / args.pdf_id), PDF_SOURCE=str(folder / 'static-preview.pptx'),
               PDF_OUTPUT=str(output), PDF_EXPECTED_SLIDES=str(manifest['total']),
               PDF_TITLE=manifest.get('topic', 'Teaching presentation'), PDF_AUTHOR=args.author)
    env.pop('PDF_T4_MANIFEST', None)
    env.pop('PDF_T4_PACKAGE', None)
    run([node, engine / 'export-pdf.mjs'], env)


def verify():
    index = json.loads((SKILL / 'archive-index.json').read_text(encoding='utf-8'))
    failures = []
    for item in index['files']:
        file = (SKILL / item['path']).resolve()
        if not file.is_relative_to(SKILL):
            failures.append(item['path'] + ': unsafe path')
        elif not file.is_file() or digest(file) != item['sha256']:
            failures.append(item['path'])
    if failures:
        raise ValueError('Archive integrity failure: ' + '; '.join(failures))
    print(json.dumps({'verifiedFiles': len(index['files']), 'bytes': sum(i['bytes'] for i in index['files']), 'allSha256Match': True}))


def compare(args):
    from PIL import Image, ImageChops
    folder = args.run.resolve()
    report = []
    pairs = [(p, folder / p.name) for p in sorted((SKILL / 'assets/golden').glob('slide-???.png'))]
    if args.states:
        pairs += [(p, folder / 'review-stages' / p.name) for p in sorted((SKILL / 'assets/golden/review-stages').glob('*.png'))]
    for golden, actual in pairs:
        if not actual.exists():
            raise ValueError('Missing render: ' + str(actual))
        with Image.open(golden) as a, Image.open(actual) as b:
            a, b = a.convert('RGB'), b.convert('RGB')
            label = golden.relative_to(SKILL / 'assets/golden').as_posix()
            if a.size != b.size:
                report.append({'file': label, 'samePixels': False, 'reason': 'size', 'golden': a.size, 'actual': b.size})
                continue
            difference = ImageChops.difference(a, b)
            bounds = difference.getbbox()
            report.append({'file': label, 'samePixels': bounds is None, 'differenceBounds': bounds})
            if bounds:
                difference.save(folder / ('difference-' + golden.name))
    result = {'pages': report, 'allPixelsEqual': all(p['samePixels'] for p in report), 'purpose': 'unchanged-topic golden replay only'}
    write_json(folder / 'golden-comparison.json', result)
    print(json.dumps({'imagesCompared': len(report), 'allPixelsEqual': result['allPixelsEqual'],
                      'reportPath': str(folder / 'golden-comparison.json')}, indent=2))
    if not result['allPixelsEqual']:
        raise ValueError('Inspect golden comparison differences; not automatically a teaching failure')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor')
    commands.add_parser('verify')
    p = commands.add_parser('self-test'); p.add_argument('workspace', type=Path)
    p = commands.add_parser('stage'); p.add_argument('workspace', type=Path)
    p = commands.add_parser('build'); p.add_argument('workspace', type=Path)
    p.add_argument('--run-id', default='lesson-r1'); p.add_argument('--render-pages', default='')
    p.add_argument('--story', type=Path); p.add_argument('--demos', type=Path); p.add_argument('--topic', default='Teaching presentation')
    p = commands.add_parser('review'); p.add_argument('workspace', type=Path)
    p.add_argument('--run-id', default='lesson-r1'); p.add_argument('--pages', nargs='+', type=int); p.add_argument('--golden', action='store_true')
    p = commands.add_parser('compare'); p.add_argument('run', type=Path); p.add_argument('--states', action='store_true')
    p = commands.add_parser('pdf'); p.add_argument('workspace', type=Path)
    p.add_argument('--run-id', default='lesson-r1'); p.add_argument('--pdf-id', default='pdf-export')
    p.add_argument('--output', type=Path, required=True); p.add_argument('--author', default='')
    args = parser.parse_args()
    for field in ('run_id', 'pdf_id'):
        value = getattr(args, field, None)
        if value is not None and (not value or not value.replace('-', '').replace('_', '').isalnum()):
            parser.error(field + ' must be a simple name, not a path')
    if args.command == 'doctor':
        node, python, env = environment()
        run([node, '-e', "const r=require('node:module').createRequire(process.env.RUNTIME_NODE_MODULES+'/package.json');for(const n of ['@oai/artifact-tool','sharp'])console.log(n+': '+r.resolve(n));"], env)
        run([python, '-B', '-c', "import PIL,lxml,pypdf;print('Python imaging/XML/PDF imports OK')"], env)
        run([env['TEX_BIN'] + '/latex.exe', '--version'], env)
        print(json.dumps({'node': str(node), 'python': str(python), 'tex': env['TEX_BIN'], 'vendorTools': env['PRESENTATION_SKILL_DIR']}))
    elif args.command == 'stage': stage(args.workspace)
    elif args.command == 'build': build(args)
    elif args.command == 'review': review(args)
    elif args.command == 'verify': verify()
    elif args.command == 'self-test':
        node, python, env = environment()
        run([python, '-B', args.workspace.resolve() / ENGINE / 't4-click-media.py', 'self-test'], env)
    elif args.command == 'compare': compare(args)
    elif args.command == 'pdf': export_pdf(args)


if __name__ == '__main__':
    main()
