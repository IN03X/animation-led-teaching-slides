"""Lossless OPC cleanup: remove unreachable assets and share identical media."""
import ast
import argparse
import hashlib
import json
import posixpath
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
from PIL import Image

here=Path(__file__).resolve().parent;root=here.parents[2]
helper=here.parent/'slide2_revision'/'merge.py'
tree=ast.parse(helper.read_text(encoding='utf-8'));lib={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))],type_ignores=[]),str(helper),'exec'),lib)
read,slides,relpath,serialize,resolve_part,R,NS=[lib[k] for k in ('read','slides','relpath','serialize','resolve_part','R','NS')]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path)
parser.add_argument('--run',type=Path)
parser.add_argument('--expected-hash')
parser.add_argument('--slides',type=int,default=61)
parser.add_argument('--manifest',type=Path)
args=parser.parse_args()
generic=args.source is not None
source=args.source if generic else root/'output/tutorial3/ELEG2310B_Tutorial3.pptx'
sha=lambda b:hashlib.sha256(b).hexdigest()
expected=args.expected_hash if generic else '21e8fa1518e797d001d87887f2b32597a239b440efce6b297955ca43b37ed53c'
assert sha(source.read_bytes())==expected
run=args.run if generic else here/'methods-work/lossless-compact-r1';run.mkdir(exist_ok=False)
data=read(source);out=data.copy();active=slides(data);assert len(active)==args.slides
pres=E.fromstring(data['ppt/presentation.xml'])
used_ids={value for node in pres.iter() for name,value in node.attrib.items() if name.startswith('{'+R+'}')}
pres_rels=E.fromstring(data['ppt/_rels/presentation.xml.rels'])
obsolete_rel_ids=[]
for rel in list(pres_rels):
    if rel.get('Type')==R+'/slide' and rel.get('Id') not in used_ids:
        obsolete_rel_ids.append(rel.get('Id'));pres_rels.remove(rel)
out['ppt/_rels/presentation.xml.rels']=serialize(pres_rels)

def dependencies(package):
    visited=set();parts={'[Content_Types].xml'};queue=['']
    while queue:
        owner=queue.pop()
        if owner in visited:continue
        visited.add(owner)
        if owner:
            assert owner in package,owner
            parts.add(owner)
        rp=relpath(owner) if owner else '_rels/.rels'
        if rp not in package:continue
        parts.add(rp)
        for rel in E.fromstring(package[rp]):
            if rel.get('TargetMode')!='External':queue.append(resolve_part(owner,rel.get('Target')))
    return parts

reachable=dependencies(out)
# Only these known stale asset families may be omitted. Preserve other metadata.
unused=sorted(n for n in out if n not in reachable and n.startswith(('ppt/media/','ppt/slides/','ppt/notesSlides/')))
out={n:b for n,b in out.items() if n not in set(unused)}
assert all(p in out and out[p]==data[p] for p in active)
types=E.fromstring(out['[Content_Types].xml'])
defaults={e.get('Extension'):e.get('ContentType') for e in types if E.QName(e).localname=='Default'}
overrides={e.get('PartName').lstrip('/'):e.get('ContentType') for e in types if E.QName(e).localname=='Override'}
groups=defaultdict(list)
for name,body in out.items():
    if name.startswith('ppt/media/'):
        ext=Path(name).suffix.lower().lstrip('.')
        groups[(ext,overrides.get(name,defaults.get(ext)),sha(body))].append(name)
aliases={}
for group in groups.values():
    ordered=sorted(group,key=lambda n:(len(n),n));canonical=ordered[0]
    for duplicate in ordered[1:]:
        assert out[canonical]==out[duplicate]
        aliases[duplicate]=canonical
retargeted=[]
for name,body in list(out.items()):
    if not name.endswith('.rels'):continue
    owner='' if name=='_rels/.rels' else name.replace('/_rels/','/')[:-5]
    rels=E.fromstring(body);changed=False
    for rel in rels:
        if rel.get('TargetMode')=='External':continue
        old=resolve_part(owner,rel.get('Target'))
        if old in aliases:
            new=aliases[old];assert data[old]==out[new]
            rel.set('Target',posixpath.relpath(new,posixpath.dirname(owner)))
            retargeted.append({'owner':owner,'id':rel.get('Id'),'old':old,'new':new});changed=True
    if changed:out[name]=serialize(rels)
out={n:b for n,b in out.items() if n not in aliases}
for item in list(types):
    if E.QName(item).localname=='Override' and item.get('PartName').lstrip('/') not in out:types.remove(item)
out['[Content_Types].xml']=serialize(types)
assert dependencies(out)==reachable-set(unused)-set(aliases)
assert slides(out)==active

# Prove retained objects, timings, links and referenced media have not changed.
relations_checked=0;gif_bindings=[]
for name,body in out.items():
    if name!='[Content_Types].xml' and not name.endswith('.rels'):assert body==data[name],name
    if not name.endswith('.rels'):continue
    owner='' if name=='_rels/.rels' else name.replace('/_rels/','/')[:-5]
    old_rels={r.get('Id'):r for r in E.fromstring(data[name])}
    new_rels={r.get('Id'):r for r in E.fromstring(body)}
    assert len(new_rels)==len(E.fromstring(body)),name
    expected_removed=set(obsolete_rel_ids) if name=='ppt/_rels/presentation.xml.rels' else set()
    assert set(old_rels)-set(new_rels)==expected_removed and not(set(new_rels)-set(old_rels))
    for rid,new in new_rels.items():
        old=old_rels[rid]
        assert {k:v for k,v in old.attrib.items() if k!='Target'}=={k:v for k,v in new.attrib.items() if k!='Target'}
        if new.get('TargetMode')=='External':assert dict(old.attrib)==dict(new.attrib)
        else:
            old_target=resolve_part(owner,old.get('Target'));new_target=resolve_part(owner,new.get('Target'))
            assert new_target in out,(name,new_target)
            if old_target.startswith('ppt/media/'):
                assert data[old_target]==out[new_target]
                if owner in active and new_target.endswith('.gif'):
                    gif=Image.open(BytesIO(out[new_target]))
                    if not generic:assert gif.info['loop']==0
                    duration=0
                    for i in range(gif.n_frames):gif.seek(i);duration+=gif.info['duration']
                    gif_bindings.append({'slide':active.index(owner)+1,'frames':gif.n_frames,'durationMs':duration,'bytesIdentical':True,'sha256':sha(out[new_target])})
            else:assert old_target==new_target
        relations_checked+=1
if not generic:assert len(gif_bindings)==13
candidate=run/'candidate.pptx'
with ZipFile(candidate,'x',ZIP_DEFLATED,compresslevel=9) as z:
    for name,body in out.items():z.writestr(name,body)
with ZipFile(candidate) as z:assert z.testzip() is None
m=json.loads((args.manifest if generic else here/'methods-work/exercise-title-r1/manifest.json').read_text(encoding='utf-8'))
m['sourceHash']=expected
if not generic:m['sourceHashes']['output/tutorial3/ELEG2310B_Tutorial3.pptx']=expected
(run/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
report={'beforeBytes':source.stat().st_size,'afterBytes':candidate.stat().st_size,'activeSlides':len(active),'activeSlideXmlByteIdentical':True,'allRetainedNonRelationshipPartsByteIdentical':True,'relationshipsChecked':relations_checked,'prunedPresentationSlideRelationshipIds':obsolete_rel_ids,'omittedUnreachableParts':unused,'deduplicatedMediaAliases':aliases,'retargetedMediaRelationships':retargeted,'gifBindings':gif_bindings,'nativePlaybackTested':False}
(run/'lossless-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'run':str(run),'beforeBytes':report['beforeBytes'],'afterBytes':report['afterBytes'],'unusedParts':len(unused),'duplicateMedia':len(aliases),'relationshipsChecked':relations_checked,'gifBindings':len(gif_bindings)}))
