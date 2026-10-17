"""Preserve the approved T4 opening after t4-template.inherit (no file writes).

Call preserve(data, types, manifest, root, lib) with preservePrefixT4=5 (or 9) and
sourceHashes[PUBLIC_SOURCE] set to the public T4 hash captured by the build.
Set sourceManifestT4 to the source run's manifest path, relative to root or
absolute. Without it, discovery requires a unique hash-matched publication.
Merge the returned slides into the template audit BEFORE computing the
packager's inherited_slides, so staged_entrance cannot replace their timing.
The helper removes generated per-slide metadata, not the original hyperlinks.

Read-only CLI: python -B t4-preserve-prefix.py compare CANDIDATE SOURCE
              [--manifest NEW_MANIFEST] [--count N]
"""

import ast
import hashlib
import importlib.util
import json
import posixpath
from copy import deepcopy
from pathlib import Path

from lxml import etree as E

PUBLIC_SOURCE = 'output/tutorial4/ELEG2310B_Tutorial4.pptx'
# Legacy test callers may reference this constant; source selection does not.
OLD_MANIFEST = 'tmp/tutorial_base/tutorial3/methods-work/t4-causal-r4/manifest.json'
CONTENT = 'application/vnd.openxmlformats-officedocument.presentationml.'
METADATA = ('links', 'animation', 'equations', 'geometry', 'formulaGroups', 'lineage', 'gifs')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _library():
    path = Path(__file__).resolve().parent.parent / 'slide2_revision/merge.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    body = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef))]
    lib = {}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), lib)
    return lib


def _notes_helper():
    path = Path(__file__).with_name('t4-notes-integrity.py')
    spec = importlib.util.spec_from_file_location('t4_prefix_notes', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _canonical(payload):
    return E.tostring(E.fromstring(payload) if isinstance(payload, bytes) else payload, method='c14n')


def _type_lookup(types):
    overrides = {e.get('PartName').lstrip('/'): e.get('ContentType') for e in types if E.QName(e).localname == 'Override'}
    defaults = {e.get('Extension'): e.get('ContentType') for e in types if E.QName(e).localname == 'Default'}
    return lambda part: overrides.get(part, defaults.get(posixpath.splitext(part)[1].lstrip('.')))


def _relationships(data, owner, lib):
    part = lib['relpath'](owner)
    relationships = list(E.fromstring(data[part])) if part in data else []
    result = {r.get('Id'): r for r in relationships}
    _require(len(result) == len(relationships), 'Duplicate relationship IDs: ' + owner)
    return result


def _prefix_count(count):
    _require(type(count) is int and count > 0, 'Prefix count must be a positive integer')
    return count


def _source_manifest(root, manifest, source, source_hash, lib):
    """Bind page IDs to a saved output, never to that run's input sourceHashes."""
    hint = source_hash or manifest.get('sourceHashes', {}).get(PUBLIC_SOURCE)
    _require(hint is None or (isinstance(hint, str) and len(hint) == 64
                             and all(c in '0123456789abcdef' for c in hint.lower())),
             'Invalid source SHA256 for manifest selection')
    explicit = manifest.get('sourceManifestT4')
    if explicit is not None:
        _require(isinstance(explicit, (str, Path)) and str(explicit).strip(), 'Invalid sourceManifestT4')
        path = (Path(root) / explicit).resolve()
    else:
        _require(isinstance(hint, str), 'Set sourceManifestT4 for an in-memory source without a known hash')
        matches = []
        for receipt in (Path(root) / 'tmp/tutorial_base/tutorial3/methods-work').glob('*/publication.json'):
            info = json.loads(receipt.read_text(encoding='utf-8'))
            if info.get('sha256', '').lower() == hint.lower() and receipt.with_name('manifest.json').is_file():
                matches.append(receipt.with_name('manifest.json'))
        _require(len(matches) == 1, 'Set sourceManifestT4: expected one hash-matched source manifest')
        path = matches[0].resolve()
    old = json.loads(path.read_text(encoding='utf-8'))
    references = [path.with_name('candidate.pptx')]
    latest_path = path.with_name('latest.json')
    if latest_path.is_file():
        latest = json.loads(latest_path.read_text(encoding='utf-8'))
        if latest.get('finalPath'):
            references.append(Path(root) / latest['finalPath'])
    if hint:
        references.append(path.parent / 'validated' / ('T4-' + hint[:12] + '.pptx'))
    for reference in dict.fromkeys(references):
        if not reference.is_file():
            continue
        digest = _sha(reference.read_bytes())
        if hint is not None and digest != hint.lower():
            continue
        # Package dictionaries have no ZIP hash: compare every part as evidence.
        if source_hash is None and lib['read'](reference) != source:
            continue
        _require(_sha(reference.read_bytes()) == digest, 'Source reference changed while reading')
        return old, path, digest
    raise ValueError('sourceManifestT4 does not match the actual source package: ' + str(path))


def _routes(source, candidate, old, manifest, lib, count=9):
    count = _prefix_count(count)
    old_slides, new_slides = lib['slides'](source), lib['slides'](candidate)
    old_ids = [p['id'] for p in old['pages']]
    new_ids = [p['id'] for p in manifest['pages']]
    _require(len(old_slides) == len(old_ids), 'Old manifest does not describe the source slide order')
    _require(len(new_slides) == len(new_ids), 'New manifest does not describe the donor slide order')
    _require(len(set(old_ids)) == len(old_ids) and len(set(new_ids)) == len(new_ids), 'Duplicate page IDs')
    _require(min(len(old_ids), len(new_ids)) >= count, 'Prefix count exceeds source or donor slide count')
    _require(old_ids[:count] == new_ids[:count], 'The first ' + str(count) + ' page IDs must remain unchanged')
    _require('overview' in new_ids, 'Missing overview navigation anchor')
    positions = {page_id: i + 1 for i, page_id in enumerate(new_ids)}
    if 'destinations' in manifest:
        _require(manifest['destinations'] == positions, 'Stale new manifest destinations')
    destinations = dict(zip(new_ids, new_slides))
    result = {}
    section = 'overview'
    for part, info in zip(old_slides, old['pages']):
        page_id = info['id']
        if page_id in ('overview', 'band-map', 'recover-map'):
            section = page_id
        elif page_id in ('summary', 'course-return', 'end'):
            section = 'overview'
        alias=manifest.get('navigationAliases',{}).get(page_id)
        if alias in destinations:
            target=alias
        elif page_id in destinations:
            target = page_id
        else:
            # Use the old lesson's explicit section labels, not old page numbers.
            subtitle = info.get('subtitle', '').lower()
            parent = info.get('parent')
            if parent in ('band-map', 'recover-map'):
                target = parent
            elif 'demodulation' in subtitle:
                target = 'recover-map'
            elif any(word in subtitle for word in ('spectrum', 'bandwidth', 'transmission', 'narrowband', 'wideband', 'carson')):
                target = 'band-map'
            else:
                target = section
            if target not in destinations:
                target = 'overview'
        result[part] = (destinations[target], page_id, target)
    return result


def preserve(data, types, manifest, root, lib):
    """Transactionally replace donor slides 1..N; mutate only caller-owned data.

    Returns sourceSha256, slides (entireSlideCopied=True), importedParts,
    navigation, notesIntegrity, repairs, and verificationObjects. Does not
    publish, create files, alter PowerPoint, or import linked source tail slides.
    """
    count = manifest.get('preservePrefixT4', 0)
    if type(count) is int and count == 0:
        return {'slides': [], 'skipped': True}
    count = _prefix_count(count)
    path = Path(root) / PUBLIC_SOURCE
    expected = manifest.get('sourceHashes', {}).get(PUBLIC_SOURCE)
    source_hash = _sha(path.read_bytes())
    _require(isinstance(expected, str) and expected.lower() == source_hash, 'Public T4 source hash missing or changed')
    source = lib['read'](path)
    _require(_sha(path.read_bytes()) == source_hash, 'Public T4 changed while reading')
    old, source_manifest, _ = _source_manifest(root, manifest, source, source_hash, lib)
    work, content_types = data.copy(), deepcopy(types)
    routes = _routes(source, work, old, manifest, lib, count)
    read_type = _type_lookup(E.fromstring(source['[Content_Types].xml']))
    CT = E.QName(content_types).namespace
    P, R, PKG, NS = [lib[k] for k in ('P', 'R', 'PKG', 'NS')]
    relpath, resolve, serialize = [lib[k] for k in ('relpath', 'resolve_part', 'serialize')]
    ordered, original = lib['slides'](work), lib['slides'](source)
    imported = dict(zip(original[:count], ordered[:count]))
    navigation = []

    def set_type(part, value):
        _require(value is not None, 'Source content type missing: ' + part)
        matches = [e for e in content_types if e.get('PartName') == '/' + part]
        _require(len(matches) <= 1, 'Duplicate content type: ' + part)
        if matches:
            matches[0].set('ContentType', value)
        else:
            E.SubElement(content_types, '{' + CT + '}Override', PartName='/' + part, ContentType=value)

    def copy_relationships(part, dest):
        if relpath(part) not in source:
            _require(relpath(dest) not in work, 'Unexpected donor relationships: ' + dest)
            return
        rels = E.fromstring(source[relpath(part)])
        for rel in rels:
            if rel.get('TargetMode') == 'External':
                continue
            target = resolve(part, rel.get('Target'))
            new_target = import_part(target)
            if target in routes:
                _, old_id, new_id = routes[target]
                navigation.append({'owner': dest, 'relationship': rel.get('Id'), 'oldId': old_id, 'targetId': new_id, 'target': new_target})
            rel.set('Target', posixpath.relpath(new_target, posixpath.dirname(dest)))
        work[relpath(dest)] = serialize(rels)

    def import_part(part):
        # Slide hyperlinks and notes backrefs terminate here, before recursion.
        if part in routes:
            return routes[part][0]
        if part in imported:
            return imported[part]
        _require(part in source, 'Missing source dependency: ' + part)
        kind = read_type(part)
        _require(kind != CONTENT + 'slide+xml', 'Unlisted source slide: ' + part)
        _require(part != 'ppt/presentation.xml' and 'presentation.main' not in (kind or ''), 'Cannot import a whole presentation')
        dest = posixpath.join(posixpath.dirname(part), 't4_prefix_' + source_hash[:12] + '_' + posixpath.basename(part))
        _require(dest not in work and relpath(dest) not in work, 'Prefix resource collision: ' + dest)
        imported[part] = dest
        work[dest] = source[part]
        set_type(dest, kind)
        copy_relationships(part, dest)
        return dest

    for src, dest in zip(original[:count], ordered[:count]):
        work[dest] = source[src]  # Do not parse/reserialize the slide itself.
        set_type(dest, read_type(src))
        copy_relationships(src, dest)

    pres = E.fromstring(work['ppt/presentation.xml'])
    rels = E.fromstring(work[relpath('ppt/presentation.xml')])
    masters = pres.find('p:sldMasterIdLst', NS)
    _require(masters is not None, 'T3 inheritance must run before preserve')
    registered = {resolve('ppt/presentation.xml', r.get('Target')) for r in rels if r.get('Type') == R + '/slideMaster'}
    used_rids = {r.get('Id') for r in rels}
    used_ids = [int(e.get('id')) for e in masters]
    for src, dest in imported.items():
        if read_type(src) != CONTENT + 'slideMaster+xml' or dest in registered:
            continue
        number = len(rels) + 1
        while 'rIdT4PrefixMaster' + str(number) in used_rids:
            number += 1
        rid = 'rIdT4PrefixMaster' + str(number)
        E.SubElement(rels, '{' + PKG + '}Relationship', Id=rid, Type=R + '/slideMaster', Target=posixpath.relpath(dest, 'ppt'))
        next_id = max(used_ids + [2147483647]) + 1
        E.SubElement(masters, '{' + P + '}sldMasterId', {'id': str(next_id), '{' + R + '}id': rid})
        registered.add(dest)
        used_rids.add(rid)
        used_ids.append(next_id)
    work['ppt/presentation.xml'] = serialize(pres)
    work[relpath('ppt/presentation.xml')] = serialize(rels)
    work['[Content_Types].xml'] = serialize(content_types)
    notes_report = _notes_helper().normalize(work)
    repairs = lib['repair_package'](work)
    verification = verify_prefix(work, path, manifest=manifest, count=count, root=root, lib=lib)
    verification['sourceSha256'] = source_hash
    _require(all(work[b] == source[a] for a, b in zip(original[:count], ordered[:count])), 'Prefix slide bytes changed')
    final_type = _type_lookup(E.fromstring(work['[Content_Types].xml']))
    added_slides = [p for p in work if p not in data and final_type(p) == CONTENT + 'slide+xml']
    _require(not added_slides, 'Imported unwanted slides: ' + str(added_slides))
    _require(_sha(path.read_bytes()) == source_hash, 'Public T4 changed during preservation')

    # Commit only after dependency, preservation and source-race checks pass.
    removed, metadata = {}, {}
    for key in METADATA:
        if key in manifest:
            kept = [item for item in manifest[key] if item['slide'] not in range(1, count + 1)]
            removed[key] = len(manifest[key]) - len(kept)
            metadata[key] = kept
    for key, kept in metadata.items():
        manifest[key][:] = kept
    manifest['pages'][:count] = deepcopy(old['pages'][:count])
    data.clear()
    data.update(work)
    types[:] = list(E.fromstring(work['[Content_Types].xml']))
    audit = [{'slide': i, 'referenceSlide': i, 'entireSlideCopied': True,
              'sourceTimingPreserved': True, 'sourceTransitionPreserved': True,
              'slideXmlByteIdentical': True} for i in range(1, count + 1)]
    return {'sourceSha256': source_hash, 'sourceManifestT4': str(source_manifest),
            'preservePrefixT4': count, 'slides': audit, 'inheritedSlides': list(range(1, count + 1)),
            'importedParts': len(imported) - count, 'navigation': navigation,
            'removedMetadata': removed, 'notesIntegrity': notes_report, 'repairs': repairs,
            'oldTailSlidesImported': 0, 'verificationObjects': verification}


def _note_xml(data, owner, lib):
    """Compare effective run fonts after the existing notes normalizer pins them."""
    NS, A, R = [lib[k] for k in ('NS', 'A', 'R')]
    resolve = lib['resolve_part']
    rel = next(r for r in _relationships(data, owner, lib).values() if r.get('Type') == R + '/notesMaster')
    master = resolve(owner, rel.get('Target'))
    rel = next(r for r in _relationships(data, master, lib).values() if r.get('Type') == R + '/theme')
    theme = E.fromstring(data[resolve(master, rel.get('Target'))])
    notes = E.fromstring(data[owner])
    for run in notes.findall('.//a:r', NS):
        props = run.find('a:rPr', NS)
        if props is None:
            props = E.Element('{' + A + '}rPr')
            run.insert(0, props)
        for script in ('latin', 'ea', 'cs'):
            font = props.find('a:' + script, NS)
            face = font.get('typeface') if font is not None else '+mn-lt'
            if not face or not face.startswith('+'):
                continue
            family = 'major' if face.startswith('+mj') else 'minor'
            face = theme.find('a:themeElements/a:fontScheme/a:' + family + 'Font/a:' + script, NS).get('typeface')
            if not face:
                continue
            if font is None:
                font = E.Element('{' + A + '}' + script)
                following = {'latin': ('ea', 'cs', 'sym', 'hlinkClick', 'hlinkMouseOver', 'extLst'), 'ea': ('cs', 'sym', 'hlinkClick', 'hlinkMouseOver', 'extLst'), 'cs': ('sym', 'hlinkClick', 'hlinkMouseOver', 'extLst')}[script]
                before = next((c for c in props if E.QName(c).localname in following), None)
                props.insert(list(props).index(before) if before is not None else len(props), font)
            font.set('typeface', face)
    return _canonical(notes)


def verify_prefix(candidate, source, *, manifest=None, count=None, root=None, lib=None):
    """Read-only comparison of paths or package dictionaries; raises on mismatch.

    Also supply the new manifest to check exact navigation IDs/fallbacks. Without
    it, internal links are checked for valid presentation targets only. No
    PowerPoint process is used, and no candidate is written or repaired here.
    Count defaults to manifest.preservePrefixT4, or 9 for legacy callers.
    An explicit count overrides the manifest value for read-only comparisons.
    """
    lib = lib or _library()
    root = Path(root) if root is not None else Path(__file__).resolve().parents[3]
    candidate = candidate if isinstance(candidate, dict) else lib['read'](candidate)
    source_path = None if isinstance(source, dict) else Path(source)
    source_hash = None if source_path is None else _sha(source_path.read_bytes())
    source = source if source_path is None else lib['read'](source_path)
    if source_path is not None:
        _require(_sha(source_path.read_bytes()) == source_hash, 'Source changed while comparing')
    if isinstance(manifest, (str, Path)):
        manifest = json.loads(Path(manifest).read_text(encoding='utf-8'))
    count = _prefix_count(count if count is not None else (manifest or {}).get('preservePrefixT4', 9))
    old_slides, new_slides = lib['slides'](source), lib['slides'](candidate)
    _require(min(len(old_slides), len(new_slides)) >= count, 'Prefix count exceeds source or candidate slide count')
    routes = None
    source_manifest = None
    if manifest is not None:
        old, source_manifest, matched_hash = _source_manifest(root, manifest, source, source_hash, lib)
        source_hash = source_hash or matched_hash
        routes = _routes(source, candidate, old, manifest, lib, count)
    source_type = _type_lookup(E.fromstring(source['[Content_Types].xml']))
    candidate_type = _type_lookup(E.fromstring(candidate['[Content_Types].xml']))
    R, NS = lib['R'], lib['NS']
    resolve = lib['resolve_part']
    assets, checked, navigation = [], set(), []

    def compare_part(old_part, new_part):
        if (old_part, new_part) in checked:
            return
        checked.add((old_part, new_part))
        _require(old_part in source and new_part in candidate, 'Missing dependency: ' + new_part)
        kind = source_type(old_part)
        _require(kind == candidate_type(new_part), 'Content type changed: ' + new_part)
        old_xml, new_xml = source[old_part], candidate[new_part]
        rid_map = {}
        if kind and (kind.endswith('+xml') or kind in ('application/xml', 'text/xml', 'image/svg+xml')):
            a, b = E.fromstring(old_xml), E.fromstring(new_xml)
            old_links = a.findall('.//a:hlinkClick', NS) + a.findall('.//a:hlinkMouseOver', NS)
            new_links = b.findall('.//a:hlinkClick', NS) + b.findall('.//a:hlinkMouseOver', NS)
            _require(len(old_links) == len(new_links), 'Hyperlink objects changed: ' + new_part)
            for old_link, new_link in zip(old_links, new_links):
                old_rid, new_rid = old_link.get('{' + R + '}id'), new_link.get('{' + R + '}id')
                if old_rid is not None:
                    _require(new_rid is not None, 'Hyperlink relationship missing: ' + new_part)
                    _require(old_rid not in rid_map or rid_map[old_rid] == new_rid, 'Inconsistent hyperlink remapping')
                    rid_map[old_rid] = new_rid
                    new_link.set('{' + R + '}id', old_rid)
            if kind == CONTENT + 'slideMaster+xml':
                for page in (a, b):
                    for item in page.findall('p:sldLayoutIdLst/p:sldLayoutId', NS):
                        item.set('id', '0')  # Global ID allocation is not layout content.
            if kind == CONTENT + 'notesSlide+xml':
                _require(_note_xml(source, old_part, lib) == _note_xml(candidate, new_part, lib), 'Notes content/style changed: ' + new_part)
            else:
                _require(_canonical(a) == _canonical(b), 'XML content changed: ' + new_part)
        else:
            _require(old_xml == new_xml, 'Asset payload changed: ' + new_part)
        if '/media/' in old_part or not (kind or '').endswith('+xml'):
            _require(old_xml == new_xml, 'Asset payload changed: ' + new_part)
            assets.append({'source': old_part, 'candidate': new_part, 'sha256': _sha(old_xml)})
        old_rels, new_rels = _relationships(source, old_part, lib), _relationships(candidate, new_part, lib)
        _require({rid_map.get(rid, rid) for rid in old_rels} == set(new_rels), 'Relationship set changed: ' + new_part)
        for rid, old_rel in old_rels.items():
            new_rel = new_rels[rid_map.get(rid, rid)]
            clean = lambda rel: {k: v for k, v in rel.attrib.items() if k not in ('Id', 'Target')}
            _require(clean(old_rel) == clean(new_rel), 'Relationship attributes changed: ' + new_part)
            if old_rel.get('TargetMode') == 'External':
                _require(old_rel.get('Target') == new_rel.get('Target'), 'External link changed: ' + new_part)
                continue
            old_target, new_target = resolve(old_part, old_rel.get('Target')), resolve(new_part, new_rel.get('Target'))
            _require(new_target in candidate, 'Broken dependency: ' + new_target)
            if source_type(old_target) == CONTENT + 'slide+xml':
                _require(new_target in new_slides, 'Link imports an unlisted old slide: ' + new_target)
                if routes is not None:
                    _require(old_target in routes and new_target == routes[old_target][0], 'Wrong navigation destination: ' + new_part + ':' + rid)
                elif old_target in old_slides[:count]:
                    _require(new_target == new_slides[old_slides.index(old_target)], 'Wrong prefix navigation/backref')
                navigation.append({'owner': new_part, 'relationship': rid, 'target': new_target})
                continue
            if old_rel.get('Type') == R + '/notesMaster':
                # normalize consolidates notes masters and materializes run fonts.
                _require(_canonical(source[old_target]) == _canonical(candidate[new_target]), 'Notes master content changed')
                continue
            compare_part(old_target, new_target)

    pages = []
    for i, (old_part, new_part) in enumerate(zip(old_slides[:count], new_slides[:count]), 1):
        compare_part(old_part, new_part)
        a, b = E.fromstring(source[old_part]), E.fromstring(candidate[new_part])
        timing = lambda page: [_canonical(n) for n in page.findall('p:timing', NS)]
        transitions = lambda page: [_canonical(n) for n in page if E.QName(n).localname in ('transition', 'AlternateContent')]
        _require(timing(a) == timing(b), 'Timing changed on slide ' + str(i))
        _require(transitions(a) == transitions(b), 'Transition changed on slide ' + str(i))
        pages.append({'slide': i, 'canonicalXmlIdentical': True, 'slideXmlByteIdentical': source[old_part] == candidate[new_part],
                      'timingIdentical': True, 'transitionsIdentical': True,
                      'objects': a.xpath('//p:cNvPr/@name', namespaces=NS)})
    _notes_helper().validate(candidate)
    pres = E.fromstring(candidate['ppt/presentation.xml'])
    pres_rels = _relationships(candidate, 'ppt/presentation.xml', lib)
    masters = [resolve('ppt/presentation.xml', pres_rels[e.get('{' + R + '}id')].get('Target')) for e in pres.findall('p:sldMasterIdLst/p:sldMasterId', NS)]
    _require(len(masters) == len(set(masters)), 'Slide master registered more than once')
    for old_part, new_part in checked:
        if source_type(old_part) == CONTENT + 'slideMaster+xml':
            _require(new_part in masters, 'Unregistered imported slide master')
    if source_path is not None:
        _require(_sha(source_path.read_bytes()) == source_hash, 'Source changed during comparison')
    return {'sourceSha256': source_hash, 'sourceManifestT4': str(source_manifest) if source_manifest else None,
            'preservePrefixT4': count, 'slides': pages, 'assets': assets, 'navigation': navigation,
            'navigationIdsChecked': routes is not None, 'dependenciesCompared': len(checked),
            'nativePlaybackTested': False}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['compare'])
    parser.add_argument('candidate', type=Path)
    parser.add_argument('source', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--count', type=int)
    args = parser.parse_args()
    print(json.dumps(verify_prefix(args.candidate, args.source, manifest=args.manifest, count=args.count), indent=2))
