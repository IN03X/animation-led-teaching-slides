"""Reuse the checked T3 timing helper for the T4 signal-story deck."""
import ast
import hashlib
import json
import posixpath
import sys
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

here=Path(__file__).resolve().parent
helper=here.parent/'slide2_revision/merge.py'
tree=ast.parse(helper.read_text(encoding='utf-8'));lib={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))],type_ignores=[]),str(helper),'exec'),lib)
read,slides,relpath,serialize,resolve_part,staged_entrance,repair_package,P,A,R,PKG,NS=[lib[k] for k in ('read','slides','relpath','serialize','resolve_part','staged_entrance','repair_package','P','A','R','PKG','NS')]
mode=sys.argv[1];run=Path(sys.argv[2])
if mode=='gif':
    from PIL import Image
    frames=[Image.open(p).convert('RGB') for p in sorted((run/'sweep-frames').glob('*.png'))]
    frames[0].save(run/'exact-fm-sweep.gif',save_all=True,append_images=frames[1:],duration=160,optimize=False,disposal=1)
    with Image.open(run/'exact-fm-sweep.gif') as im:
        assert im.n_frames>=40 and 'loop' not in im.info
        duration=0
        for i in range(im.n_frames):
            im.seek(i);duration+=im.info['duration']
        assert duration==9600
    print('Exact FM sweep: 60 frames, single play, 9.6 seconds.')
    sys.exit(0)

m=json.loads((run/'manifest.json').read_text(encoding='utf-8'));data=read(run/'donor.pptx');ordered=slides(data)
assert len(ordered)==m['total']
types=E.fromstring(data['[Content_Types].xml']);CT=E.QName(types).namespace
for ext,ctype in [('svg','image/svg+xml'),('gif','image/gif')]:
    if not any(t.get('Extension')==ext for t in types):E.SubElement(types,'{'+CT+'}Default',Extension=ext,ContentType=ctype)
ASVG='http://schemas.microsoft.com/office/drawing/2016/SVG/main'
images={};report={'slides':len(ordered),'clicks':{},'motionPaths':0,'links':0,'nativePlaybackTested':False};static={}
def add_media(payload,ext):
    digest=hashlib.sha256(payload).hexdigest();name='ppt/media/t4_'+digest[:24]+'.'+ext
    data[name]=payload
    return name
def add_rel(rels,owner,rid,kind,target):
    assert rid not in {r.get('Id') for r in rels}
    E.SubElement(rels,'{'+PKG+'}Relationship',Id=rid,Type=R+'/'+kind,Target=posixpath.relpath(target,posixpath.dirname(owner)))
for i,owner in enumerate(ordered,1):
    page=E.fromstring(data[owner]);rels=E.fromstring(data[relpath(owner)]);pics=page.findall('.//p:pic',NS)
    equations=[e for e in m['equations'] if e['slide']==i];gifs=[g for g in m['gifs'] if g['slide']==i]
    assert len(pics)==len(equations)+len(gifs),(i,len(pics),len(equations),len(gifs))
    for index,(pic,e) in enumerate(zip(pics[len(gifs):],equations)):
        nv=pic.find('p:nvPicPr/p:cNvPr',NS);nv.set('name',e['name']);nv.set('descr',e['tex'])
        svg=E.fromstring((run/e['file']).read_bytes());bounds=[float(x) for x in svg.get('viewBox').split()];svg.set('width',str(bounds[2]*32)+'px');svg.set('height',str(bounds[3]*32)+'px')
        part=add_media(serialize(svg),'svg');rid='rIdMathSvg'+str(index);add_rel(rels,owner,rid,'image',part)
        blip=pic.find('p:blipFill/a:blip',NS);ext=E.SubElement(E.SubElement(blip,'{'+A+'}extLst'),'{'+A+'}ext',uri='{96DAC541-7B7A-43D3-8B79-37D633B846F1}')
        E.SubElement(ext,'{'+ASVG+'}svgBlip',{'{'+R+'}embed':rid})
    for pic,g in zip(pics,gifs):
        nv=pic.find('p:nvPicPr/p:cNvPr',NS);nv.set('name',g['name']);nv.set('descr',g.get('description','Numerical signal demonstration.'))
        blip=pic.find('p:blipFill/a:blip',NS);rid=blip.get('{'+R+'}embed');rel=next(r for r in rels if r.get('Id')==rid)
        if not g.get('playOnClick'):
            static[owner]=(rid,rel.get('Target'))
            rel.set('Target',posixpath.relpath(add_media((run/g['file']).read_bytes(),'gif'),posixpath.dirname(owner)))
    data[owner]=serialize(page);data[relpath(owner)]=serialize(rels)

import importlib.util
template_spec=importlib.util.spec_from_file_location('t4_template',here/'t4-template.py')
template=importlib.util.module_from_spec(template_spec);template_spec.loader.exec_module(template)
report['template']=template.inherit(data,types,m,here.parents[2],lib)
if m.get('preservePrefixT4'):
    prefix_spec=importlib.util.spec_from_file_location('t4_preserve_prefix',here/'t4-preserve-prefix.py')
    prefix=importlib.util.module_from_spec(prefix_spec);prefix_spec.loader.exec_module(prefix)
    report['preservedPrefix']=prefix.preserve(data,types,m,here.parents[2],lib)

def rewrite_exits(page,specs):
    next_id=max([int(n.get('id')) for n in page.findall('.//p:cTn',NS)]+[0])+1
    for spec in (s for s in specs if s.get('exitAfterMs') is not None):
        nv=page.xpath('//p:cNvPr[@name=$n]',namespaces=NS,n=spec['name'])[0];spid=nv.get('id')
        effects=page.xpath('//p:cTn[@presetClass][p:childTnLst//p:spTgt[@spid=$s]]/p:childTnLst',namespaces=NS,s=spid)
        if spec.get('exitOnly'):
            ordered_specs=[s for stage in sorted({s['stage'] for s in specs if s['stage']>0}) for s in specs if s['stage']==stage]
            effect_node=page.xpath('//p:cTn[@presetClass]',namespaces=NS)[ordered_specs.index(spec)]
            effect_node.set('presetClass','exit');effect_node.set('presetID','10')
            effects=[effect_node.find('p:childTnLst',NS)]
        assert len(effects)==1,spec
        if spec['name'].endswith('-rewrite-source'):
            # Let the copy clear its retained source before making it visible.
            for entrance in effects[0].findall('p:set',NS)+effects[0].findall('p:animEffect',NS):
                timing=entrance.find('p:cBhvr/p:cTn',NS)
                conditions=timing.find('p:stCondLst',NS)
                if conditions is None:conditions=E.SubElement(timing,'{'+P+'}stCondLst')
                condition=conditions.find('p:cond',NS)
                if condition is None:condition=E.SubElement(conditions,'{'+P+'}cond')
                condition.set('delay','500')
                if entrance.tag=='{'+P+'}animEffect':timing.set('dur','200')
        exit_duration=0 if spec.get('instantExit') else 200
        effect=E.SubElement(effects[0],'{'+P+'}animEffect',transition='out',filter='fade')
        behavior=E.SubElement(effect,'{'+P+'}cBhvr');timing=E.SubElement(behavior,'{'+P+'}cTn',id=str(next_id),dur=str(max(1,exit_duration)),fill='hold');next_id+=1
        E.SubElement(E.SubElement(timing,'{'+P+'}stCondLst'),'{'+P+'}cond',delay=str(spec['exitAfterMs']))
        E.SubElement(E.SubElement(behavior,'{'+P+'}tgtEl'),'{'+P+'}spTgt',spid=spid)
        setter=E.SubElement(effects[0],'{'+P+'}set');behavior=E.SubElement(setter,'{'+P+'}cBhvr');timing=E.SubElement(behavior,'{'+P+'}cTn',id=str(next_id),dur='1',fill='hold');next_id+=1
        E.SubElement(E.SubElement(timing,'{'+P+'}stCondLst'),'{'+P+'}cond',delay=str(spec['exitAfterMs']+exit_duration))
        E.SubElement(E.SubElement(behavior,'{'+P+'}tgtEl'),'{'+P+'}spTgt',spid=spid)
        E.SubElement(E.SubElement(behavior,'{'+P+'}attrNameLst'),'{'+P+'}attrName').text='style.visibility'
        E.SubElement(E.SubElement(setter,'{'+P+'}to'),'{'+P+'}strVal',val='hidden')

def refine_incremental_effects(page,specs):
    for spec in specs:
        if spec.get('exitOnly'):continue
        nv=page.xpath('//p:cNvPr[@name=$n]',namespaces=NS,n=spec['name'])[0]
        spid=nv.get('id')
        if spec.get('instantEntrance'):
            for effect in page.xpath('//p:animEffect[@transition="in"][p:cBhvr/p:tgtEl/p:spTgt[@spid=$s]]',namespaces=NS,s=spid):effect.getparent().remove(effect)
        if spec.get('entranceDurationMs'):
            for timing in page.xpath('//p:animEffect[@transition="in"][p:cBhvr/p:tgtEl/p:spTgt[@spid=$s]]/p:cBhvr/p:cTn',namespaces=NS,s=spid):timing.set('dur',str(spec['entranceDurationMs']))
        if spec.get('motion',{}).get('via'):
            xf=nv.getparent().getparent().find('.//a:xfrm',NS)
            off,ext=xf.find('a:off',NS),xf.find('a:ext',NS)
            cx=(int(off.get('x'))+int(ext.get('cx'))/2)/9525
            cy=(int(off.get('y'))+int(ext.get('cy'))/2)/9525
            for motion in page.xpath('//p:animMotion[p:cBhvr/p:tgtEl/p:spTgt[@spid=$s]]',namespaces=NS,s=spid):
                start=motion.get('path').split(' L ')[0]
                via=''.join(f' L {(x-cx)/1280:.8f} {(y-cy)/720:.8f}' for x,y in spec['motion']['via'])
                motion.set('path',start+via+' L 0 0 E')

MC='http://schemas.openxmlformats.org/markup-compatibility/2006'
inherited_slides={entry['slide'] for entry in report['template']['slides'] if entry.get('entireSlideCopied')}
inherited_slides.update(range(1,m.get('preservePrefixT4',0)+1))
report['aliases']={};report['morphTransitions']=0
report['inheritedSlides']=sorted(inherited_slides)
for i,owner in enumerate(ordered,1):
    page=E.fromstring(data[owner]);rels=E.fromstring(data[relpath(owner)])
    specs=[a for a in m['animation'] if a['slide']==i]
    if i in inherited_slides:
        report['clicks'][str(i)]=len(page.xpath('//p:cTn[@nodeType="mainSeq"]/p:childTnLst/p:par',namespaces=NS))
    else:
        # Generated pages enter directly; only the approved opening keeps Morph.
        tables=page.xpath('./p:cSld/p:spTree/p:graphicFrame[a:graphic/a:graphicData/a:tbl]',namespaces=NS)
        table_specs=m['pages'][i-1].get('nativeTables',[])
        if table_specs:
            assert len(tables)==len(table_specs),(i,'Native table count mismatch')
            for frame,table_spec in zip(tables,table_specs):
                frame.find('p:nvGraphicFramePr/p:cNvPr',NS).set('name',table_spec['name'])
        for nv in page.xpath('./p:cSld/p:spTree/p:graphicFrame/p:nvGraphicFramePr/p:cNvPr',namespaces=NS):
            if not nv.get('name'):nv.set('name','Native table '+nv.get('id'))
        for child in list(page):
            if child.tag=='{'+P+'}transition' or (child.tag=='{'+MC+'}AlternateContent' and child.find('.//p:transition',NS) is not None):page.remove(child)
        staged_entrance(page,[s for s in specs if not s.get('playMedia')])
        refine_incremental_effects(page,[s for s in specs if not s.get('playMedia')])
        rewrite_exits(page,[s for s in specs if not s.get('playMedia')])
        report['clicks'][str(i)]=max([s['stage'] for s in specs]+[0])
    report['motionPaths']+=len(page.findall('.//p:animMotion',NS))
    for j,l in enumerate(x for x in m['links'] if x['slide']==i):
        dest=ordered[m['destinations'][l['target']]-1];rid='rIdNav'+str(j);add_rel(rels,owner,rid,'slide',dest)
        nv=page.xpath('//p:cNvPr[@name=$n]',namespaces=NS,n=l['name']);assert len(nv)==1,l
        h=E.Element('{'+A+'}hlinkClick',{'{'+R+'}id':rid,'action':'ppaction://hlinksldjump'})
        ext=nv[0].find('a:extLst',NS)
        if ext is None:nv[0].append(h)
        else:nv[0].insert(list(nv[0]).index(ext),h)
        report['links']+=1
    names=page.xpath('//p:cNvPr/@name',namespaces=NS)
    assert len(set(names))==len(names),f'Duplicate object names on {i}: {[name for name in set(names) if names.count(name)>1]}'
    report['aliases'][str(i)]={name:name for name in names}
    report['morphTransitions']+=len(page.xpath('//*[local-name()="morph"]'))
    data[owner]=serialize(page);data[relpath(owner)]=serialize(rels)
click_media=None
if any(g.get('playOnClick') for g in m['gifs']):
    media_spec=importlib.util.spec_from_file_location('t4_click_media',here/'t4-click-media.py')
    click_media=importlib.util.module_from_spec(media_spec);media_spec.loader.exec_module(click_media)
    report['clickMedia']=click_media.install(data,types,m,run,lib)
    report['clicks'].update(report['clickMedia']['clicks'])
data['[Content_Types].xml']=serialize(types)
report['repairs']=repair_package(data)
schema=E.XMLSchema(E.parse('C:/Users/10486/.codex/skills/pptx/scripts/office/schemas/ISO-IEC29500-4_2016/pml.xsd'))
for part in ordered+['ppt/presentation.xml']:
    checked=E.fromstring(data[part])
    for alt in list(checked.findall('.//{'+MC+'}AlternateContent')):
        fallback=alt.find('{'+MC+'}Fallback');parent=alt.getparent();index=list(parent).index(alt)
        for node in reversed(list(fallback)):parent.insert(index,deepcopy(node))
        parent.remove(alt)
    assert schema.validate(checked),(part,[str(v) for v in schema.error_log])
for part,payload in data.items():
    if part.endswith('.rels'):
        owner='' if part=='_rels/.rels' else part.replace('/_rels/','/')[:-5]
        rr=E.fromstring(payload);assert len({r.get('Id') for r in rr})==len(rr)
        for r in rr:
            if r.get('TargetMode')!='External':assert resolve_part(owner,r.get('Target')) in data,(owner,r.get('Target'))
def write(name,payload):
    with ZipFile(run/name,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for part,body in payload.items():z.writestr(part,body)
    with ZipFile(run/name) as z:assert z.testzip() is None
def apply_relocations(page,specs,stage):
    for event in specs:
        if not event.get('moveOnly') or event.get('exitOnly') or event['stage']>stage:continue
        end=event.get('motion',{}).get('to')
        if end is None:continue
        nv=page.xpath('//p:cNvPr[@name=$n]',namespaces=NS,n=event['name'])
        if not nv:continue
        off=nv[0].getparent().getparent().find('.//a:xfrm/a:off',NS)
        off.set('x',str(round(int(off.get('x'))+end['dx']*1280*9525)))
        off.set('y',str(round(int(off.get('y'))+end['dy']*720*9525)))
write('candidate.pptx',data)
preview=data.copy()
for index,owner in enumerate(ordered,1):
    page=E.fromstring(preview[owner])
    if click_media is not None:
        page=click_media.snapshot_page(page,report['clickMedia']['mediaIndex'],index)
    for node in page.findall('p:timing',NS)+page.findall('p:transition',NS)+page.findall('{'+MC+'}AlternateContent'):page.remove(node)
    tree=page.find('p:cSld/p:spTree',NS)
    for obj in list(tree):
        nv=obj.find('.//p:cNvPr',NS)
        if nv is not None and (nv.get('name','').endswith('-rewrite-source') or any(s.get('exitOnly') and report['aliases'][str(index)].get(s['name'])==nv.get('name') for s in m['animation'] if s['slide']==index)):tree.remove(obj)
    apply_relocations(page,[a for a in m['animation'] if a['slide']==index],float('inf'))
    preview[owner]=serialize(page)
for owner,(rid,target) in static.items():
    rels=E.fromstring(preview[relpath(owner)]);next(r for r in rels if r.get('Id')==rid).set('Target',target);preview[relpath(owner)]=serialize(rels)
write('static-preview.pptx',preview)

# Build actual cumulative click endpoints, not only the fully revealed slides.
chosen={p['id'] for i,p in enumerate(m['pages'],1) if i not in inherited_slides and p['id'] not in {'cover','end'}}
snaps=preview.copy();pr=E.fromstring(snaps['ppt/_rels/presentation.xml.rels']);pres=E.fromstring(snaps['ppt/presentation.xml']);listing=pres.find('p:sldIdLst',NS)
for child in list(listing):listing.remove(child)
stypes=E.fromstring(snaps['[Content_Types].xml']);stages=[]
for i,owner in enumerate(ordered,1):
    if m['pages'][i-1]['id'] not in chosen:continue
    specs=[x for x in m['animation'] if x['slide']==i];aliases=report['aliases'][str(i)];stage_map={aliases.get(x['name'],x['name']):x['stage'] for x in specs if not x.get('moveOnly') and not x.get('playMedia')}
    for k in range(report['clicks'][str(i)]+1):
        p=E.fromstring(preview[owner] if k==report['clicks'][str(i)] else data[owner])
        if click_media is not None:
            p=click_media.snapshot_page(p,report['clickMedia']['mediaIndex'],i,stage=k,elapsed_ms=float('inf'))
        spTree=p.find('p:cSld/p:spTree',NS)
        for node in p.findall('p:timing',NS)+p.findall('{'+MC+'}AlternateContent'):p.remove(node)
        for obj in list(spTree):
            nv=obj.find('.//p:cNvPr',NS)
            if nv is not None and (stage_map.get(nv.get('name'),0)>k or nv.get('name','').endswith('-rewrite-source') or any(s.get('exitOnly') and s['stage']<=k and aliases.get(s['name'])==nv.get('name') for s in specs)):spTree.remove(obj)
        if k!=report['clicks'][str(i)]:apply_relocations(p,specs,k)
        dest='ppt/slides/t4_stage_'+str(len(stages)+1)+'.xml';snaps[dest]=serialize(p);snaps[relpath(dest)]=preview[relpath(owner)]
        rid='rIdStage'+str(len(stages)+1);add_rel(pr,'ppt/presentation.xml',rid,'slide',dest)
        E.SubElement(listing,'{'+P+'}sldId',{'id':str(5000+len(stages)),'{'+R+'}id':rid})
        E.SubElement(stypes,'{'+CT+'}Override',PartName='/'+dest,ContentType='application/vnd.openxmlformats-officedocument.presentationml.slide+xml')
        stages.append({'slide':i,'stage':k,'id':m['pages'][i-1]['id']})
snaps['ppt/presentation.xml']=serialize(pres);snaps['ppt/_rels/presentation.xml.rels']=serialize(pr);snaps['[Content_Types].xml']=serialize(stypes)
write('stage-preview.pptx',snaps)
(run/'stages.json').write_text(json.dumps(stages,indent=2),encoding='utf-8')
(run/'package-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# Persist the manifest after replacing the generated opening with source slides.
(run/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({key:value for key,value in report.items() if key not in ['aliases','template','preservedPrefix','clickMedia']}))
