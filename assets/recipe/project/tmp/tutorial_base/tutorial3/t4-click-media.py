"""Click-start PNG frame playback for T4; no filesystem writes or PowerPoint calls.

Integration (after formula timing, including rewrite_exits, has been generated):

    staged_entrance(page, [s for s in specs if not s.get('playMedia')])
    # Serialize all pages/relationships into data, then:
    media_report = click_media.install(data, types, manifest, run, lib)
    report['clickMedia'] = media_report
    report['clicks'].update(media_report['clicks'])
    data['[Content_Types].xml'] = serialize(types)

manifest.animation contains {slide, name, stage: 1, playMedia: True} for each
manifest.gifs entry. Formulas already have stage 2+. Do NOT add placeholder
clicks, renumber a second time, or run staged_entrance after install. The helper
maps existing groups to sorted NON-media stages and merges new groups by stage.
Stages must be dense, starting at 1; each media stage is its own normal click.
g.name (or g.id) must match a top-level picture. g.initialPoster is frame zero;
g.poster is the final frame. g.file identifies the original GIF directory.
That directory's frames.json supplies ordered PNG names and durations in ms.
Optional g.framesJson overrides the metadata path. g.frames can instead specify
run-relative PNG paths (durations from g.durations or the metadata file).

mediaIndex is keyed by slide number (as string), with one record per animation.
For previews of changed slides, use snapshot_page(page, mediaIndex, slide,
stage=None) for final state, or stage=k, elapsed_ms=0/finite/inf for click states.
This collapses media layers and strips timing in a COPY. Already-collapsed
pages are supported, including a final preview passed through a second time.
Apply the packager's ordinary formula/exit visibility filtering separately,
using the already-renumbered manifest. Skip the old GIF `static` relationship
restore on these slides, and do not infer media visibility from formula specs.
The entry state's original picture name and id stay unchanged.

Why native frames: these demonstrations are 50-60 complete, opaque PNGs with
variable 160-ms steps and longer holds. Native appear/set effects retain every
pixel and exact source duration without H.264 quantization, decoding, poster
rewind, or an independent media-player clock. Each frame appears above its
opaque predecessor; frame zero is unanimated and visible before the click.
One click starts all scheduled frames, once, and fill=hold retains the last.
The existing helper supplies the normal onNext/mainSeq timing scaffold.
Opaque achromatic PNGs can be encoded as 8-bit grayscale with exactly the same
decoded RGBA pixels; colored PNGs stay RGB. Every conversion is pixel-checked,
profiled assets stay verbatim, and existing identical assets are reused.

MP4 was investigated, and ffmpeg is available on this workstation. Microsoft
documents In Click Sequence, embedded p14:media + a:videoFile relationships,
and p:cmd PlayFrom(0.0). An MP4 backend is deliberately NOT emitted here; the
PNG implementation is the native-frame alternative authorized by the task.
Sources:
https://support.microsoft.com/en-us/powerpoint/insert-and-play-a-video-file-from-your-computer
https://learn.microsoft.com/en-us/openspecs/office_standards/ms-pptx/5e1b21c6-979f-45c5-8a46-fbef53a6e80a
https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.command
https://support.microsoft.com/en-us/powerpoint/set-the-start-time-and-speed-of-an-animation-effect

Validation is XSD + relationships + an independent XML timing/state model,
NOT PowerPoint playback. Backward navigation, early Next seeking, actual frame
scheduling, and animation-disabled viewers still need a native Windows test.
There is no replay trigger. Normal editor view may show stacked final frames;
the static initial-state requirement applies to Slide Show with animations on.

Read-only CLI (use -B to suppress Python bytecode files):
    python -B t4-click-media.py self-test
    python -B t4-click-media.py audit RUN [--source PRIVATE.pptx]
        [--legacy-manifest] [--schema PATH_TO_pml.xsd]
Audit converts/validates a private candidate in memory and writes nothing.
--legacy-manifest adds media specs and shifts formulas in a private COPY of
an older manifest; it is not part of the integration API.
"""

import argparse
import ast
import bisect
import hashlib
import io
import json
import math
import posixpath
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from lxml import etree as E
from PIL import Image, ImageChops
from zipfile import ZIP_DEFLATED, ZipFile


P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
NS = {'p': P, 'a': A, 'r': R}
MARKER = '--t4-click-frame-'
SCHEMA = Path('C:/Users/10486/.codex/skills/pptx/scripts/office/schemas/ISO-IEC29500-4_2016/pml.xsd')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _library():
    path = Path(__file__).resolve().parent.parent / 'slide2_revision/merge.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    body = [n for n in tree.body if isinstance(
        n, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef))]
    lib = {}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), lib)
    return lib


def _canonical(node):
    return E.tostring(node, method='c14n')


def _name(g):
    name = g.get('name', g.get('id'))
    _require(isinstance(name, str) and name and MARKER not in name,
             'Media needs an ordinary, nonempty name/id')
    return name


def _asset(root, relative):
    _require(isinstance(relative, str) and relative, 'Missing asset path')
    path = (root / relative).resolve()
    _require(path.is_relative_to(root) and path.is_file(),
             'Asset must be a file inside the private run: ' + relative)
    return path


def _pixels(payload):
    with Image.open(io.BytesIO(payload)) as image:
        _require(image.format == 'PNG' and getattr(image, 'n_frames', 1) == 1,
                 'Playback frames/posters must be static PNGs')
        rgba = image.convert('RGBA')
        _require(rgba.getchannel('A').getextrema() == (255, 255),
                 'Native layers require complete opaque frames')
        return rgba.size, hashlib.sha256(rgba.tobytes()).hexdigest()


def _bundle(g, run):
    root = Path(run).resolve()
    source = _asset(root, g['file'])
    metadata = _asset(root, g.get('framesJson',
                      (source.parent / 'frames.json').relative_to(root).as_posix()))
    config = json.loads(metadata.read_text(encoding='utf-8'))
    if 'frames' in g:
        paths = [_asset(root, name) for name in g['frames']]
    else:
        paths = [_asset(metadata.parent, name) for name in config['frames']]
    durations = g.get('durations', config['durations'])
    payloads = [path.read_bytes() for path in paths]
    _require(2 <= len(payloads) <= 1000 and len(durations) == len(payloads),
             'Frame count and duration count must match (2..1000)')
    _require(all(type(d) is int and d > 0 for d in durations),
             'Each duration must be a positive integer number of milliseconds')
    total = sum(durations)
    _require(total < 2147483647, 'Playback duration exceeds Office time range')
    _require(g.get('durationMs', total) == total, 'Manifest durationMs disagrees with frames')
    pixels = [_pixels(payload) for payload in payloads]
    _require(len({item[0] for item in pixels}) == 1, 'All frames must have the same dimensions')
    initial = _asset(root, g.get('initialPoster', g.get('first',
                     paths[0].relative_to(root).as_posix())))
    final = _asset(root, g['poster'])
    _require(_pixels(initial.read_bytes()) == pixels[0], 'initialPoster is not frame zero')
    _require(_pixels(final.read_bytes()) == pixels[-1], 'poster is not the final frame')
    return {'payloads': payloads, 'durations': list(durations),
            'size': list(pixels[0][0]), 'metadata': metadata.relative_to(root).as_posix(),
            'initialPoster': initial.relative_to(root).as_posix(),
            'finalPoster': final.relative_to(root).as_posix()}


def _main(page):
    nodes = page.xpath('./p:timing/p:tnLst/p:par/p:cTn/p:childTnLst/'
                       'p:seq/p:cTn[@nodeType="mainSeq"]/p:childTnLst', namespaces=NS)
    _require(len(nodes) <= 1, 'Expected one native main sequence')
    return nodes[0] if nodes else None


def _new_ids(node, next_id):
    nodes = node.findall('.//p:cTn', NS)
    mapping = {n.get('id'): str(next_id + i) for i, n in enumerate(nodes)}
    for n in nodes:
        n.set('id', mapping[n.get('id')])
    for n in node.findall('.//p:tn', NS):
        _require(n.get('val') in mapping, 'New timing fragment references an external node')
        n.set('val', mapping[n.get('val')])
    return next_id + len(nodes)


def _fresh_relationship(rels, owner, part):
    used = {r.get('Id') for r in rels}
    index = 1
    while 'rIdT4ClickFrame' + str(index) in used:
        index += 1
    rid = 'rIdT4ClickFrame' + str(index)
    E.SubElement(rels, '{' + PKG + '}Relationship', Id=rid, Type=R + '/image',
                 Target=posixpath.relpath(part, posixpath.dirname(owner)))
    return rid


def _lossless_png(payload):
    with Image.open(io.BytesIO(payload)) as image:
        # Preserve profiles: equal channel values alone do not guarantee equal
        # appearance when an image declares a different color space.
        if any(key in image.info for key in ('icc_profile', 'gamma', 'srgb', 'chromaticity', 'exif')):
            return payload
        rgba = image.convert('RGBA')
        _require(rgba.getchannel('A').getextrema() == (255, 255), 'Frames must be opaque')
        red, green, blue = rgba.convert('RGB').split()
        gray = (ImageChops.difference(red, green).getbbox() is None and
                ImageChops.difference(red, blue).getbbox() is None)
        encoded = io.BytesIO()
        (red if gray else rgba.convert('RGB')).save(encoded, format='PNG', optimize=True, compress_level=9)
        candidate = encoded.getvalue()
        with Image.open(io.BytesIO(candidate)) as decoded:
            _require(decoded.convert('RGBA').tobytes() == rgba.tobytes(),
                     'Lossless PNG re-encoding changed pixels')
        return candidate if len(candidate) < len(payload) else payload


def _png_part(data, payload, cache):
    source_hash = hashlib.sha256(payload).hexdigest()
    if source_hash in cache:
        return cache[source_hash]
    encoded = _lossless_png(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    if digest in cache:
        cache[source_hash] = cache[digest]
        return cache[digest]
    part = 'ppt/media/t4_click_' + digest + '.png'
    _require(part not in data or data[part] == encoded, 'Content-addressed PNG collision')
    data[part] = encoded
    cache[source_hash] = cache[digest] = part
    return part


def _set_blip(pic, rid):
    fill = pic.find('p:blipFill', NS)
    blip = fill.find('a:blip', NS)
    _require(blip is not None, 'Picture needs an embedded blip')
    # Replace the entire blip so a stale SVG extension cannot select a different image.
    fill.replace(blip, E.Element('{' + A + '}blip', {'{' + R + '}embed': rid}))


def _frame_click(page, record, lib):
    scratch = deepcopy(page)
    first = 0 if record.get('hiddenUntilPlay') else 1
    specs = [{'name': name, 'stage': 1, 'delayMs': delay}
             for name, delay in zip(record['frameNames'][first:], record['startsMs'][first:])]
    lib['staged_entrance'](scratch, specs)
    click = _main(scratch)[0]
    outer = click.find('p:cTn', NS)
    outer.set('restart', 'never')
    outer.set('repeatCount', '1000')  # OOXML repeatCount uses thousandths, not integers.
    parallel = outer.find('p:childTnLst/p:par/p:cTn', NS)
    parallel.set('dur', str(record['durationMs']))
    for effect in click.xpath('.//p:cTn[@presetClass]', namespaces=NS):
        effect.set('presetID', '1')  # Appear, without fading or moving a signal.
        effect.set('restart', 'never')
        children = effect.find('p:childTnLst', NS)
        for fade in list(children.findall('p:animEffect', NS)):
            children.remove(fade)
    return scratch.find('p:timing', NS), click


def install(data, types, manifest, run, lib=None, *, schema_path=None):
    """Atomically update the caller's in-memory package and content-types tree.

    No files are written; no existing package parts are removed. On error, both
    data and types are unchanged. Return a JSON-serializable mediaIndex/report.
    Native formula timing must already exist, with playMedia specs filtered out.
    """
    lib = lib or _library()
    entries = manifest.get('gifs', [])
    bundles = {(_name(g), g['slide']): _bundle(g, run) for g in entries}
    return _install(data, types, manifest, bundles, lib, schema_path)


def _install(data, types, manifest, bundles, lib, schema_path):
    ordered = lib['slides'](data)
    _require(manifest.get('total', len(ordered)) == len(ordered), 'Manifest slide count mismatch')
    entries = manifest.get('gifs', [])
    animation = manifest.get('animation', [])
    media_specs = [s for s in animation if s.get('playMedia')]
    keys = [(g['slide'], _name(g)) for g in entries]
    _require(len(set(keys)) == len(keys), 'Duplicate media name on a slide')
    _require(sorted(keys) == sorted((s['slide'], s['name']) for s in media_specs),
             'Each GIF needs exactly one matching playMedia spec')
    _require(all(type(i) is int and 1 <= i <= len(ordered) for i, _ in keys),
             'Invalid media slide number')
    _require(all(i > manifest.get('preservePrefixT4', 0) for i, _ in keys),
             'Cannot replace media inside the preserved T4 prefix')
    output = data.copy()
    png_cache = {hashlib.sha256(payload).hexdigest(): part for part, payload in data.items()
                 if part.startswith('ppt/media/') and part.lower().endswith('.png') and
                 payload.startswith(b'\x89PNG\r\n\x1a\n')}
    new_types = deepcopy(types)
    png_types = new_types.xpath('./ct:Default[@Extension="png"]', namespaces={'ct': CT})
    _require(len(png_types) <= 1, 'Duplicate PNG content type')
    if png_types:
        _require(png_types[0].get('ContentType') == 'image/png', 'Incorrect PNG content type')
    else:
        E.SubElement(new_types, '{' + CT + '}Default', Extension='png', ContentType='image/png')
    report = {'backend': 'native-png-frames', 'mediaIndex': {}, 'clicks': {},
              'nativePlaybackTested': False, 'formulaTimingPreserved': True,
              'limitations': ['No native PowerPoint playback test.',
                              'Early Next / backward navigation behavior needs native testing.',
                              'Animations must be enabled; PNG layers increase package size.']}
    for number in sorted({i for i, _ in keys}):
        owner = ordered[number - 1]
        page = E.fromstring(data[owner])
        rels = E.fromstring(data[lib['relpath'](owner)])
        tree = page.find('p:cSld/p:spTree', NS)
        specs = [s for s in animation if s['slide'] == number]
        _require(all(type(s.get('stage')) is int and s['stage'] >= 0 for s in specs),
                 'Animation stages must be nonnegative integers')
        visual_specs = [s for s in specs if s.get('playMedia')]
        visual_stages = [s['stage'] for s in visual_specs]
        formula_stages = sorted({s['stage'] for s in specs if not s.get('playMedia') and s['stage'] > 0})
        stages = sorted(set(visual_stages) | set(formula_stages))
        _require(len(visual_stages) == len(set(visual_stages)) and 0 not in visual_stages,
                 'Each media needs a separate positive click stage')
        _require(not set(visual_stages) & set(formula_stages),
                 'Media and formulas cannot share a click stage')
        _require(stages == list(range(1, len(stages) + 1)), 'Click stages must be dense from 1')
        main = _main(page)
        old_groups = list(main) if main is not None else []
        _require(len(old_groups) == len(formula_stages),
                 'Native groups must match non-media stages; do not add empty slots')
        _require(all(g.tag == '{' + P + '}par' for g in old_groups), 'Unsupported main sequence')
        for stage, group in zip(formula_stages, old_groups):
            expected = set()
            for spec in (s for s in specs if not s.get('playMedia') and s['stage'] == stage):
                matches = page.xpath('.//p:cNvPr[@name=$n]', namespaces=NS, n=spec['name'])
                _require(len(matches) == 1, 'Formula/object name is ambiguous: ' + spec['name'])
                expected.add(matches[0].get('id'))
            _require(set(group.xpath('.//p:spTgt/@spid', namespaces=NS)) == expected,
                     'Native formula group order disagrees with manifest stages')
            gate = group.find('p:cTn/p:stCondLst/p:cond', NS)
            _require(gate is not None and dict(gate.attrib) == {'delay': 'indefinite'},
                     'Existing formula groups must wait for separate clicks')
        old_canonical = [_canonical(group) for group in old_groups]
        groups = dict(zip(formula_stages, old_groups))
        next_shape = max(int(n.get('id')) for n in page.findall('.//p:cNvPr', NS)) + 1
        next_time = max([int(n.get('id')) for n in page.findall('.//p:cTn', NS)] + [0]) + 1
        records = []
        for spec in sorted(visual_specs, key=lambda s: s['stage']):
            name = spec['name']
            bundle = bundles[(name, number)]
            matches = tree.xpath('./p:pic[p:nvPicPr/p:cNvPr[@name=$n]]', namespaces=NS, n=name)
            _require(len(matches) == 1, 'Expected one top-level media picture: ' + name)
            original = matches[0]
            original_nv = original.find('p:nvPicPr/p:cNvPr', NS)
            spid = original_nv.get('id')
            _require(original_nv.get('hidden', '0') in ('0', 'false'),
                     'Initial media picture is hidden: ' + name)
            reveals = [s for s in specs if s['name'] == name and not s.get('playMedia')]
            hidden_until_play = next(g for g in manifest['gifs'] if g['slide'] == number and _name(g) == name).get('hiddenUntilPlay', False)
            _require(not (hidden_until_play and reveals), 'Continuation cannot also have a preview reveal')
            reveal_stage = None
            if reveals:
                _require(len(reveals) == 1 and reveals[0].get('revealMedia') and
                         0 < reveals[0]['stage'] < spec['stage'] and
                         not reveals[0].get('motion') and not reveals[0].get('exitOnly'),
                         'Media needs one separate initial reveal before playback: ' + name)
                reveal_stage = reveals[0]['stage']
            else:
                _require(not page.xpath('.//p:spTgt[@spid=$s]', namespaces=NS, s=spid),
                         'Media picture already has timing: ' + name)
            _require(not page.xpath('.//p:cNvPr[starts-with(@name,$n)]', namespaces=NS, n=name + MARKER),
                     'Media already installed: ' + name)
            _require(not original.xpath('.//a:hlinkClick|.//a:hlinkHover|.//a:videoFile', namespaces=NS),
                     'Media picture has interactive actions: ' + name)
            original_index = list(tree).index(original)
            record = {'name': name, 'slide': number, 'owner': owner, 'stage': spec['stage'],
                      'durationsMs': bundle['durations'], 'durationMs': sum(bundle['durations']),
                      'startsMs': [0], 'frameNames': [name], 'frameIds': [spid],
                      'frameParts': [], 'frameRids': [], 'frameSha256': [], 'pixelSize': bundle['size'],
                      'initialPoster': bundle['initialPoster'], 'finalPoster': bundle['finalPoster'],
                      'framesMetadata': bundle['metadata'], 'revealStage': reveal_stage,
                      'hiddenUntilPlay': hidden_until_play}
            for d in bundle['durations'][:-1]:
                record['startsMs'].append(record['startsMs'][-1] + d)
            template = deepcopy(original)
            for index, payload in enumerate(bundle['payloads']):
                part = _png_part(output, payload, png_cache)
                rid = _fresh_relationship(rels, owner, part)
                record['frameParts'].append(part)
                record['frameRids'].append(rid)
                record['frameSha256'].append(hashlib.sha256(output[part]).hexdigest())
                pic = original if index == 0 else deepcopy(template)
                if index:
                    nv = pic.find('p:nvPicPr/p:cNvPr', NS)
                    frame_name = name + MARKER + str(index).zfill(3)
                    _require(not page.xpath('.//p:cNvPr[@name=$n]', namespaces=NS, n=frame_name),
                             'Frame name collision: ' + frame_name)
                    nv.set('id', str(next_shape))
                    nv.set('name', frame_name)
                    # Clones must not duplicate creation IDs or future drawing extensions.
                    for extension in list(nv.findall('a:extLst', NS)):
                        nv.remove(extension)
                    record['frameIds'].append(str(next_shape))
                    record['frameNames'].append(frame_name)
                    next_shape += 1
                    tree.insert(original_index + index, pic)
                _set_blip(pic, rid)
            timing, click = _frame_click(page, record, lib)
            if main is None:
                _require(page.find('p:timing', NS) is None, 'Unsupported timing without a main sequence')
                next_time = _new_ids(timing, next_time)
                extension = page.find('p:extLst', NS)
                page.insert(list(page).index(extension) if extension is not None else len(page), timing)
                main = _main(page)
                main.remove(click)
            else:
                next_time = _new_ids(click, next_time)
            groups[spec['stage']] = click
            records.append(record)
        for child in list(main):
            main.remove(child)
        for stage in stages:
            main.append(groups[stage])
        _require([_canonical(groups[s]) for s in formula_stages] == old_canonical,
                 'Existing formula timing changed')
        report['mediaIndex'][str(number)] = records
        report['clicks'][str(number)] = len(stages)
        output[owner] = lib['serialize'](page)
        output[lib['relpath'](owner)] = lib['serialize'](rels)
    output['[Content_Types].xml'] = lib['serialize'](new_types)
    report['checks'] = validate(output, report, lib, schema_path=schema_path)
    report['size'] = {'sourceFrameBytes': sum(len(p) for bundle in bundles.values() for p in bundle['payloads']),
                      'newPngBytes': sum(len(payload) for part, payload in output.items() if part not in data),
                      'newPngParts': len(set(output) - set(data)), 'decodedPixelsUnchanged': True,
                      'existingPartsDeleted': 0}
    report['objectCounts'] = {
        str(i): {'before': len(E.fromstring(data[owner]).findall('.//p:cNvPr', NS)) - 1,
                 'after': len(E.fromstring(output[owner]).findall('.//p:cNvPr', NS)) - 1}
        for i, owner in enumerate(ordered, 1)}
    data.update(output)
    types[:] = [deepcopy(child) for child in new_types]
    return report


def validate(data, report, lib=None, *, schema_path=None):
    """Check changed slide XSD, bindings, click gates, durations and all frame states."""
    lib = lib or _library()
    path = Path(schema_path) if schema_path is not None else SCHEMA
    _require(path.is_file(), 'Required pml.xsd is unavailable; supply schema_path')
    schema = E.XMLSchema(E.parse(str(path)))
    types = E.fromstring(data['[Content_Types].xml'])
    defaults = {n.get('Extension'): n.get('ContentType') for n in types if E.QName(n).localname == 'Default'}
    overrides = {n.get('PartName').lstrip('/'): n.get('ContentType') for n in types if E.QName(n).localname == 'Override'}
    points = 0
    frames = 0
    for number, records in report['mediaIndex'].items():
        owner = records[0]['owner']
        page = E.fromstring(data[owner])
        _require(schema.validate(page), owner + ': ' + str(schema.error_log))
        shape_ids = page.xpath('.//p:cNvPr/@id', namespaces=NS)
        timing_ids = page.xpath('.//p:cTn/@id', namespaces=NS)
        _require(len(shape_ids) == len(set(shape_ids)), 'Duplicate shape IDs')
        _require(len(timing_ids) == len(set(timing_ids)), 'Duplicate timing IDs')
        _require(set(page.xpath('.//p:tn/@val', namespaces=NS)) <= set(timing_ids),
                 'Timing condition refers to a missing time node')
        _require(set(page.xpath('.//p:spTgt/@spid', namespaces=NS)) <= set(shape_ids),
                 'Timing refers to a missing shape')
        main = _main(page)
        _require(main is not None and len(main) == report['clicks'][number], 'Wrong native click count')
        seq = main.getparent().getparent()
        _require(seq.find('p:nextCondLst/p:cond/p:tgtEl/p:sldTgt', NS) is not None and
                 seq.find('p:nextCondLst/p:cond', NS).get('evt') == 'onNext',
                 'Main sequence must respond to normal presentation Next')
        rels = E.fromstring(data[lib['relpath'](owner)])
        lookup = {r.get('Id'): r for r in rels}
        _require(len(lookup) == len(rels), 'Duplicate relationship IDs')
        for node in page.iter():
            for attribute, rid in node.attrib.items():
                if attribute in ('{' + R + '}embed', '{' + R + '}link', '{' + R + '}id') and rid:
                    _require(rid in lookup, 'Unbound relationship: ' + rid)
        for r in rels:
            if r.get('TargetMode') != 'External':
                _require(lib['resolve_part'](owner, r.get('Target')) in data, 'Dangling relationship')
        for record in records:
            click = main[record['stage'] - 1]
            outer = click.find('p:cTn', NS)
            gate = outer.find('p:stCondLst/p:cond', NS)
            _require(gate is not None and dict(gate.attrib) == {'delay': 'indefinite'} and len(gate) == 0,
                     'Media click must wait for main-sequence Next, not autoplay/object click')
            _require(outer.get('fill') == 'hold' and outer.get('restart') == 'never' and
                     outer.get('repeatCount') == '1000', 'Playback must hold and run only once')
            duration_node = outer.find('p:childTnLst/p:par/p:cTn', NS)
            _require(duration_node.get('dur') == str(record['durationMs']), 'Lost initial/final hold')
            effects = click.xpath('.//p:cTn[@presetClass]', namespaces=NS)
            first = 0 if record.get('hiddenUntilPlay') else 1
            _require(len(effects) == len(record['frameIds']) - first, 'Wrong number of frame effects')
            initial_targets = page.xpath('.//p:spTgt[@spid=$s]', namespaces=NS, s=record['frameIds'][0])
            reveal_stage = record.get('revealStage')
            if record.get('hiddenUntilPlay'):
                targets = click.xpath('.//p:spTgt[@spid=$s]', namespaces=NS, s=record['frameIds'][0])
                _require(len(targets) == 1 and len(initial_targets) == 1,
                         'Continuation frame zero must enter on its own playback click')
            elif reveal_stage is None:
                _require(not initial_targets, 'Frame zero must be static at slide entry')
            else:
                _require(0 < reveal_stage < record['stage'], 'Initial reveal must precede playback')
                reveal = main[reveal_stage - 1]
                targets = reveal.xpath('.//p:spTgt[@spid=$s]', namespaces=NS, s=record['frameIds'][0])
                _require(initial_targets and len(initial_targets) == len(targets),
                         'Frame zero may only enter on its declared reveal click')
                ancestors = targets[0].xpath('ancestor::p:cTn[@presetClass]', namespaces=NS)
                _require(ancestors and all(n.get('presetClass') == 'entr' for n in ancestors),
                         'Initial media reveal must be an entrance')
            xml_events = []
            for index, effect in enumerate(effects, first):
                _require(effect.get('presetClass') == 'entr' and effect.get('presetID') == '1' and
                         effect.get('nodeType') == ('clickEffect' if index == first else 'withEffect'),
                         'Frames must be native appear entrances')
                _require(effect.get('fill') == 'hold' and effect.get('restart') == 'never',
                         'Frame should hold without restarting')
                children = effect.find('p:childTnLst', NS)
                _require(len(children) == 1 and children[0].tag == '{' + P + '}set',
                         'Unexpected fade, motion, media call or formula in playback group')
                setter = children[0]
                _require(setter.find('p:to/p:strVal', NS).get('val') == 'visible', 'Invalid visibility')
                behavior = setter.find('p:cBhvr', NS)
                _require(behavior.find('p:attrNameLst/p:attrName', NS).text == 'style.visibility',
                         'Unexpected frame animation property')
                target = behavior.find('p:tgtEl/p:spTgt', NS).get('spid')
                delay = int(effect.find('p:stCondLst/p:cond', NS).get('delay'))
                _require(target == record['frameIds'][index] and delay == record['startsMs'][index],
                         'Frame order or start time mismatch')
                _require(behavior.find('p:cTn', NS).get('fill') == 'hold' and
                         behavior.find('p:cTn', NS).get('dur') == '1', 'Frame visibility must persist')
                xml_events.append((delay, index))
            for index, (spid, rid, part) in enumerate(zip(record['frameIds'], record['frameRids'], record['frameParts'])):
                pics = page.xpath('./p:cSld/p:spTree/p:pic[p:nvPicPr/p:cNvPr[@id=$s]]', namespaces=NS, s=spid)
                _require(len(pics) == 1 and pics[0].find('p:blipFill/a:blip', NS).get('{' + R + '}embed') == rid,
                         'Wrong frame picture binding')
                rel = lookup[rid]
                _require(rel.get('Type') == R + '/image' and rel.get('TargetMode') != 'External' and
                         lib['resolve_part'](owner, rel.get('Target')) == part and data[part].startswith(b'\x89PNG\r\n\x1a\n'),
                         'Every playback image must be an embedded PNG')
                _require(overrides.get(part, defaults.get('png')) == 'image/png',
                         'Frame has incorrect content type')
                _require(hashlib.sha256(data[part]).hexdigest() == record['frameSha256'][index],
                         'Embedded frame bytes differ from the source PNG')
                if index:
                    _require(list(pics[0].getparent()).index(pics[0]) > prior_position, 'Incorrect frame z-order')
                prior_position = list(pics[0].getparent()).index(pics[0])
            # Independent sampling of XML events against the source-duration ledger.
            samples = {0, record['durationMs'], record['durationMs'] + 60000}
            for offset in record['startsMs'][1:]:
                samples.update((offset - 1, offset, offset + 1))
            for elapsed in samples:
                actual = max([index for delay, index in xml_events if delay <= elapsed] + [0])
                expected = bisect.bisect_right(record['startsMs'], elapsed) - 1
                _require(actual == expected, 'XML event model shows an incorrect frame')
            points += len(samples) + 1
            frames += len(record['frameIds'])
    return {'xsd': str(path), 'changedSlidesXsdValid': len(report['mediaIndex']),
            'embeddedPngFrames': frames, 'modeledFrameSamples': points,
            'relationshipChecks': True, 'nativePlaybackTested': False}


def snapshot_page(page, media_index, slide, stage=None, elapsed_ms=math.inf):
    """Copy a page, collapse media to one PNG each, strip timing; formulas untouched.

    stage=None means final static preview. stage=0 is static slide entry.
    For the current media click, elapsed_ms=0 shows frame zero; default inf
    shows its completed state. Future media remain at frame zero. Any optional
    initial reveal is handled by the caller's ordinary object-stage filtering.
    """
    result = deepcopy(page)
    tree = result.find('p:cSld/p:spTree', NS)
    _require(stage is None or (type(stage) is int and stage >= 0), 'Invalid preview stage')
    _require(elapsed_ms >= 0, 'Invalid preview elapsed time')
    for record in media_index.get(str(slide), []):
        if stage is None or stage > record['stage']:
            index = len(record['frameIds']) - 1
        elif stage < record['stage']:
            index = 0
        else:
            index = bisect.bisect_right(record['startsMs'], elapsed_ms) - 1
        pics = {pic.find('p:nvPicPr/p:cNvPr', NS).get('id'): pic for pic in tree.findall('p:pic', NS)}
        _require(record['frameIds'][0] in pics, 'Preview needs the original media picture')
        overlays = set(record['frameIds'][1:]) & set(pics)
        _require(not overlays or overlays == set(record['frameIds'][1:]),
                 'Preview received a partially collapsed media sequence')
        _set_blip(pics[record['frameIds'][0]], record['frameRids'][index])
        for spid in overlays:
            tree.remove(pics[spid])
        if record.get('hiddenUntilPlay') and stage is not None and stage < record['stage']:
            tree.remove(pics[record['frameIds'][0]])
    for timing in list(result.findall('p:timing', NS)):
        result.remove(timing)
    return result


def _fixture(lib, media_count=1, formula_stages=(2, 3), reveal_stage=None):
    def png(value):
        buffer = io.BytesIO()
        Image.new('RGB', (8, 4), (value, value, value)).save(buffer, format='PNG')
        return buffer.getvalue()

    page = E.Element('{' + P + '}sld', nsmap=NS)
    tree = E.SubElement(E.SubElement(page, '{' + P + '}cSld'), '{' + P + '}spTree')
    nv = E.SubElement(tree, '{' + P + '}nvGrpSpPr')
    E.SubElement(nv, '{' + P + '}cNvPr', id='1', name='')
    E.SubElement(nv, '{' + P + '}cNvGrpSpPr')
    E.SubElement(nv, '{' + P + '}nvPr')
    E.SubElement(tree, '{' + P + '}grpSpPr')
    names = ['demo' + str(i) for i in range(media_count)] + ['equation-0', 'equation-1']
    for i, name in enumerate(names, 2):
        pic = E.SubElement(tree, '{' + P + '}pic')
        nv = E.SubElement(pic, '{' + P + '}nvPicPr')
        E.SubElement(nv, '{' + P + '}cNvPr', id=str(i), name=name)
        E.SubElement(nv, '{' + P + '}cNvPicPr')
        E.SubElement(nv, '{' + P + '}nvPr')
        fill = E.SubElement(pic, '{' + P + '}blipFill')
        E.SubElement(fill, '{' + A + '}blip', {'{' + R + '}embed': 'rIdImage'})
        E.SubElement(E.SubElement(fill, '{' + A + '}stretch'), '{' + A + '}fillRect')
        E.SubElement(pic, '{' + P + '}spPr')
    specs = [{'slide': 1, 'name': 'equation-' + str(i), 'stage': stage}
             for i, stage in enumerate(formula_stages)]
    if reveal_stage is not None:
        specs.append({'slide': 1, 'name': 'demo0', 'stage': reveal_stage,
                      'revealMedia': True, 'instantEntrance': True})
    lib['staged_entrance'](page, specs)
    owner = 'ppt/slides/slide1.xml'
    rels = E.Element('{' + PKG + '}Relationships')
    E.SubElement(rels, '{' + PKG + '}Relationship', Id='rIdImage', Type=R + '/image', Target='../media/old.png')
    pres = E.Element('{' + P + '}presentation', nsmap=NS)
    E.SubElement(E.SubElement(pres, '{' + P + '}sldIdLst'), '{' + P + '}sldId',
                 {'id': '256', '{' + R + '}id': 'rIdSlide'})
    pr = E.Element('{' + PKG + '}Relationships')
    E.SubElement(pr, '{' + PKG + '}Relationship', Id='rIdSlide', Type=R + '/slide', Target='slides/slide1.xml')
    types = E.Element('{' + CT + '}Types')
    E.SubElement(types, '{' + CT + '}Default', Extension='png', ContentType='image/png')
    payloads = [png(v) for v in (255, 120, 0)]
    data = {owner: lib['serialize'](page), lib['relpath'](owner): lib['serialize'](rels),
            'ppt/presentation.xml': lib['serialize'](pres),
            'ppt/_rels/presentation.xml.rels': lib['serialize'](pr),
            'ppt/media/old.png': payloads[-1], '[Content_Types].xml': lib['serialize'](types)}
    ordinary_stages = set(formula_stages) | ({reveal_stage} if reveal_stage is not None else set())
    available_stages = [i for i in range(1, len(ordinary_stages) + media_count + 1) if i not in ordinary_stages]
    gifs = [{'name': name, 'slide': 1} for name in names[:media_count]]
    specs += [{'slide': 1, 'name': g['name'], 'stage': stage, 'playMedia': True}
              for g, stage in zip(gifs, available_stages)]
    bundles = {(g['name'], 1): {'payloads': payloads, 'durations': [900, 160, 1500],
               'size': [8, 4], 'initialPoster': 'first.png', 'finalPoster': 'last.png',
               'metadata': 'frames.json'} for g in gifs}
    return data, types, {'total': 1, 'gifs': gifs, 'animation': specs}, bundles


class PlaybackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = _library()

    def build(self, **kwargs):
        self.data, self.types, self.manifest, self.bundles = _fixture(self.lib, **kwargs)
        self.before = self.data.copy()
        self.report = _install(self.data, self.types, self.manifest, self.bundles, self.lib, None)
        self.owner = 'ppt/slides/slide1.xml'
        self.page = E.fromstring(self.data[self.owner])
        return self.report

    def test_first_frame_and_every_boundary(self):
        self.build()
        record = self.report['mediaIndex']['1'][0]
        for stage, ms, expected in [(0, math.inf, 0), (1, 0, 0), (1, 899, 0),
                                    (1, 900, 1), (1, 1059, 1), (1, 1060, 2),
                                    (1, 99999, 2), (2, 0, 2), (None, 0, 2)]:
            page = snapshot_page(self.page, self.report['mediaIndex'], 1, stage, ms)
            blip = page.xpath('.//p:pic[p:nvPicPr/p:cNvPr[@name="demo0"]]/p:blipFill/a:blip', namespaces=NS)[0]
            self.assertEqual(blip.get('{' + R + '}embed'), record['frameRids'][expected])
            self.assertIsNone(page.find('p:timing', NS))
            self.assertEqual(len(page.findall('.//p:pic', NS)), 3)

    def test_formula_groups_preserved_without_second_shift(self):
        self.build()
        original = E.fromstring(self.before[self.owner])
        self.assertEqual([_canonical(g) for g in _main(original)],
                         [_canonical(g) for g in list(_main(self.page))[1:]])
        self.assertEqual(self.report['clicks'], {'1': 3})
        self.assertEqual([s['stage'] for s in self.manifest['animation']], [2, 3, 1])

    def test_continuation_waits_for_its_own_click(self):
        data, types, manifest, bundles = _fixture(self.lib)
        manifest['gifs'][0]['hiddenUntilPlay'] = True
        report = _install(data, types, manifest, bundles, self.lib, None)
        page = E.fromstring(data['ppt/slides/slide1.xml'])
        before = snapshot_page(page, report['mediaIndex'], 1, stage=0)
        self.assertFalse(before.xpath('.//p:cNvPr[@name="demo0"]', namespaces=NS))
        for time in (0, 900, 1060, 99999):
            shown = snapshot_page(page, report['mediaIndex'], 1, stage=1, elapsed_ms=time)
            self.assertEqual(len(shown.xpath('.//p:cNvPr[@name="demo0"]', namespaces=NS)), 1)
        validate(data, report, self.lib)

    def test_initial_reveal_before_separate_playback(self):
        self.build(formula_stages=(1, 2), reveal_stage=2)
        record = self.report['mediaIndex']['1'][0]
        self.assertEqual((record['revealStage'], record['stage']), (2, 3))
        original = E.fromstring(self.before[self.owner])
        self.assertEqual([_canonical(g) for g in _main(original)],
                         [_canonical(g) for g in list(_main(self.page))[:2]])
        malformed = self.data.copy()
        bad_report = deepcopy(self.report)
        bad_report['mediaIndex']['1'][0]['revealStage'] = 1
        with self.assertRaisesRegex(ValueError, 'declared reveal click'):
            validate(malformed, bad_report, self.lib)

    def test_collapsed_final_preview_can_be_snapshotted_again(self):
        self.build()
        final = snapshot_page(self.page, self.report['mediaIndex'], 1)
        repeated = snapshot_page(final, self.report['mediaIndex'], 1, stage=3)
        self.assertEqual(_canonical(repeated), _canonical(final))
        initial = snapshot_page(final, self.report['mediaIndex'], 1, stage=0)
        direct = snapshot_page(self.page, self.report['mediaIndex'], 1, stage=0)
        self.assertEqual(_canonical(initial), _canonical(direct))

    def test_wrong_formula_order_rejected(self):
        data, types, manifest, bundles = _fixture(self.lib)
        page = E.fromstring(data['ppt/slides/slide1.xml'])
        main = _main(page)
        main.insert(0, main[-1])
        data['ppt/slides/slide1.xml'] = self.lib['serialize'](page)
        with self.assertRaisesRegex(ValueError, 'group order'):
            _install(data, types, manifest, bundles, self.lib, None)

    def test_media_only_page(self):
        self.build(formula_stages=())
        self.assertEqual(self.report['clicks'], {'1': 1})

    def test_interleaved_media_and_formulas(self):
        self.build(media_count=2, formula_stages=(2, 4))
        self.assertEqual([r['stage'] for r in self.report['mediaIndex']['1']], [1, 3])
        self.assertEqual(self.report['clicks'], {'1': 4})
        records = self.report['mediaIndex']['1']
        snapshot = snapshot_page(self.page, self.report['mediaIndex'], 1, 2, 0)
        for record, index in zip(records, (2, 0)):
            pic = snapshot.xpath('.//p:pic[p:nvPicPr/p:cNvPr[@name=$n]]', namespaces=NS, n=record['name'])[0]
            self.assertEqual(pic.find('p:blipFill/a:blip', NS).get('{' + R + '}embed'), record['frameRids'][index])

    def test_repeat_install_is_rejected_atomically(self):
        self.build()
        before, types = self.data.copy(), _canonical(self.types)
        with self.assertRaises(ValueError):
            _install(self.data, self.types, self.manifest, self.bundles, self.lib, None)
        self.assertEqual(self.data, before)
        self.assertEqual(_canonical(self.types), types)

    def test_media_formula_same_click_rejected(self):
        data, types, manifest, bundles = _fixture(self.lib)
        manifest['animation'][-1]['stage'] = 2
        before = data.copy()
        with self.assertRaisesRegex(ValueError, 'cannot share'):
            _install(data, types, manifest, bundles, self.lib, None)
        self.assertEqual(data, before)

    def test_prefix_guard(self):
        data, types, manifest, bundles = _fixture(self.lib)
        manifest['preservePrefixT4'] = 1
        with self.assertRaisesRegex(ValueError, 'preserved'):
            _install(data, types, manifest, bundles, self.lib, None)

    def test_missing_spec_and_empty_slot_rejected(self):
        data, types, manifest, bundles = _fixture(self.lib)
        manifest['animation'].pop()
        with self.assertRaisesRegex(ValueError, 'matching playMedia'):
            _install(data, types, manifest, bundles, self.lib, None)
        data, types, manifest, bundles = _fixture(self.lib)
        page = E.fromstring(data['ppt/slides/slide1.xml'])
        _main(page).insert(0, deepcopy(_main(page)[0]))
        data['ppt/slides/slide1.xml'] = self.lib['serialize'](page)
        with self.assertRaisesRegex(ValueError, 'empty slots'):
            _install(data, types, manifest, bundles, self.lib, None)

    def test_xsd_and_relationship_negative_controls(self):
        self.build()
        malformed = self.data.copy()
        page = deepcopy(self.page)
        _main(page)[0].find('p:cTn', NS).set('restart', 'nonsense')
        malformed[self.owner] = self.lib['serialize'](page)
        with self.assertRaises(ValueError):
            validate(malformed, self.report, self.lib)
        malformed = self.data.copy()
        rels = E.fromstring(malformed[self.lib['relpath'](self.owner)])
        rels[-1].set('Target', '../media/missing.png')
        malformed[self.lib['relpath'](self.owner)] = self.lib['serialize'](rels)
        with self.assertRaisesRegex(ValueError, 'Dangling'):
            validate(malformed, self.report, self.lib)

    def test_autoplay_and_corrupted_png_rejected(self):
        self.build()
        malformed = self.data.copy()
        page = deepcopy(self.page)
        _main(page)[0].find('p:cTn/p:stCondLst/p:cond', NS).set('delay', '0')
        malformed[self.owner] = self.lib['serialize'](page)
        with self.assertRaisesRegex(ValueError, 'autoplay'):
            validate(malformed, self.report, self.lib)
        malformed = self.data.copy()
        record = self.report['mediaIndex']['1'][0]
        malformed[record['frameParts'][0]] = malformed[record['frameParts'][-1]]
        with self.assertRaisesRegex(ValueError, 'source PNG'):
            validate(malformed, self.report, self.lib)

    def test_bundle_metadata_and_posters(self):
        _, _, _, bundles = _fixture(self.lib)
        frames = bundles[('demo0', 1)]['payloads']
        root = Path(__file__).resolve().parent
        config = {'frames': ['frame-000.png', 'frame-001.png', 'frame-002.png'],
                  'durations': [900, 160, 1500]}
        assets = {root / ('frame-' + str(i).zfill(3) + '.png'): payload for i, payload in enumerate(frames)}
        assets.update({root / 'first.png': frames[0], root / 'last.png': frames[-1],
                       root / 'animation.gif': b'GIF89a',
                       root / 'frames.json': json.dumps(config).encode()})
        g = {'file': 'animation.gif', 'initialPoster': 'first.png', 'poster': 'last.png', 'durationMs': 2560}
        with patch.object(Path, 'is_file', lambda path: path in assets), \
                patch.object(Path, 'read_bytes', lambda path: assets[path]), \
                patch.object(Path, 'read_text', lambda path, **kwargs: assets[path].decode()):
            self.assertEqual(_bundle(g, root)['durations'], [900, 160, 1500])
            with self.assertRaisesRegex(ValueError, 'frame zero'):
                _bundle(dict(g, initialPoster='last.png'), root)
            with self.assertRaisesRegex(ValueError, 'final frame'):
                _bundle(dict(g, poster='first.png'), root)
            with self.assertRaisesRegex(ValueError, 'durationMs'):
                _bundle(dict(g, durationMs=1), root)
            with self.assertRaisesRegex(ValueError, 'positive integer'):
                _bundle(dict(g, durations=[900, 0, 1500]), root)
            with self.assertRaisesRegex(ValueError, 'inside the private run'):
                _bundle(dict(g, frames=['../outside.png']), root)

    def test_transparent_frames_are_rejected(self):
        buffer = io.BytesIO()
        Image.new('RGBA', (8, 4), (0, 0, 0, 100)).save(buffer, format='PNG')
        with self.assertRaisesRegex(ValueError, 'opaque'):
            _pixels(buffer.getvalue())

    def test_lossless_encoding_and_existing_asset_reuse(self):
        for colored in (False, True):
            values = bytearray()
            for i in range(400):
                value = i % 256
                values.extend((value, (value * 3) % 256 if colored else value, value, 255))
            buffer = io.BytesIO()
            Image.frombytes('RGBA', (20, 20), bytes(values)).save(buffer, format='PNG', compress_level=0)
            original = buffer.getvalue()
            optimized = _lossless_png(original)
            self.assertEqual(_pixels(original), _pixels(optimized))
            self.assertLess(len(optimized), len(original))
        self.build(media_count=2, formula_stages=(2, 4))
        first, second = self.report['mediaIndex']['1']
        self.assertEqual(first['frameParts'], second['frameParts'])
        self.assertEqual(first['frameParts'][-1], 'ppt/media/old.png')
        self.assertEqual(self.report['size']['newPngParts'], 2)


def _legacy_manifest(manifest):
    result = deepcopy(manifest)
    _require(not any(s.get('playMedia') for s in result['animation']),
             '--legacy-manifest is only for manifests without media specs')
    for number in sorted({g['slide'] for g in result.get('gifs', [])}):
        gifs = [g for g in result['gifs'] if g['slide'] == number]
        for spec in result['animation']:
            if spec['slide'] == number and spec['stage'] > 0:
                spec['stage'] += len(gifs)
        for stage, g in enumerate(gifs, 1):
            result['animation'].append({'slide': number, 'name': _name(g), 'stage': stage, 'playMedia': True})
    return result


def _audit(args):
    run = Path(args.run).resolve()
    source = Path(args.source).resolve() if args.source else run / 'candidate.pptx'
    _require('output' not in {part.lower() for part in source.parts}, 'Audit only a private candidate')
    lib = _library()
    data = lib['read'](source)
    before = data.copy()
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
    if args.legacy_manifest:
        manifest = _legacy_manifest(manifest)
    types = E.fromstring(data['[Content_Types].xml'])
    report = install(data, types, manifest, run, lib, schema_path=args.schema)
    changed_slides = {r['owner'] for records in report['mediaIndex'].values() for r in records}
    allowed = changed_slides | {lib['relpath'](p) for p in changed_slides} | {'[Content_Types].xml'}
    _require(all(payload == data[part] for part, payload in before.items() if part not in allowed),
             'Unrelated package part changed')
    report['unrelatedPartsUnchanged'] = True
    report['newPngBytes'] = sum(len(payload) for part, payload in data.items() if part not in before)
    archive = io.BytesIO()
    with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=9) as zipped:
        for part, payload in data.items():
            zipped.writestr(part, payload)
    report['zipBytesInMemory'] = archive.tell()
    report['sourceZipBytes'] = source.stat().st_size
    with ZipFile(archive) as zipped:
        _require(zipped.testzip() is None, 'In-memory ZIP round-trip failed')
    report['zipRoundTripValid'] = True
    report['animations'] = [{'slide': r['slide'], 'name': r['name'], 'stage': r['stage'],
                             'frames': len(r['frameIds']), 'durationMs': r['durationMs']}
                            for records in report['mediaIndex'].values() for r in records]
    report.pop('mediaIndex')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('self-test', help='Run in-memory tests; no files are created')
    audit = commands.add_parser('audit', help='Convert/validate a private candidate only in memory')
    audit.add_argument('run')
    audit.add_argument('--source')
    audit.add_argument('--legacy-manifest', action='store_true')
    audit.add_argument('--schema')
    args = parser.parse_args()
    if args.command == 'self-test':
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(PlaybackTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)
    _audit(args)


if __name__ == '__main__':
    main()
