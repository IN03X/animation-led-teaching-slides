import json
import posixpath
import sys
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P,'a':A,'r':R}
def read(path):
    with ZipFile(path) as z:
        return {name:z.read(name) for name in z.namelist()}
def slides(data):
    rels=E.fromstring(data['ppt/_rels/presentation.xml.rels'])
    targets={r.get('Id'):r.get('Target') for r in rels}
    pres=E.fromstring(data['ppt/presentation.xml'])
    return [posixpath.normpath(posixpath.join('ppt',targets[e.get('{'+R+'}id')])).lstrip('/') for e in pres.findall('p:sldIdLst/p:sldId',NS)]
def relpath(p):
    return posixpath.join(posixpath.dirname(p),'_rels',posixpath.basename(p)+'.rels')

def serialize(node):
    return E.tostring(node, xml_declaration=True, encoding='UTF-8', standalone=True)

def resolve_part(owner, target):
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner),target)).lstrip('/')

def repair_package(data):
    """Consolidate identical notes masters and allocate globally distinct layout IDs."""
    pres = E.fromstring(data['ppt/presentation.xml'])
    rels = E.fromstring(data['ppt/_rels/presentation.xml.rels'])
    lookup = {r.get('Id'):r for r in rels}
    notes_list = pres.find('p:notesMasterIdLst',NS)
    removed = []
    if notes_list is not None and len(notes_list)>1:
        keep_rid=notes_list[0].get('{'+R+'}id')
        keep_part=resolve_part('ppt/presentation.xml',lookup[keep_rid].get('Target'))
        keep_xml=E.fromstring(data[keep_part])
        for entry in list(notes_list)[1:]:
            rid=entry.get('{'+R+'}id')
            duplicate=resolve_part('ppt/presentation.xml',lookup[rid].get('Target'))
            assert E.tostring(keep_xml,method='c14n')==E.tostring(E.fromstring(data[duplicate]),method='c14n'), 'Nonidentical notes masters require explicit style reconciliation'
            for part in list(data):
                if not part.endswith('.rels') or '/_rels/' not in part or part=='ppt/_rels/presentation.xml.rels':
                    continue
                folder,filename=part.rsplit('/_rels/',1)
                owner=folder+'/'+filename[:-5]
                relationships=E.fromstring(data[part])
                changed=False
                for relationship in relationships:
                    if relationship.get('Type')==R+'/notesMaster' and resolve_part(owner,relationship.get('Target'))==duplicate:
                        relationship.set('Target',posixpath.relpath(keep_part,posixpath.dirname(owner)))
                        changed=True
                if changed:data[part]=serialize(relationships)
            notes_list.remove(entry)
            rels.remove(lookup[rid])
            removed.append(duplicate)
            data.pop(duplicate)
            data.pop(relpath(duplicate),None)
    types=E.fromstring(data['[Content_Types].xml'])
    for entry in list(types):
        if entry.get('PartName','').lstrip('/') in removed:types.remove(entry)
    data['[Content_Types].xml']=serialize(types)
    masters=[]
    for entry in pres.findall('p:sldMasterIdLst/p:sldMasterId',NS):
        master=resolve_part('ppt/presentation.xml',lookup[entry.get('{'+R+'}id')].get('Target'))
        masters.append((entry,master,E.fromstring(data[master])))
    all_ids=[int(entry.get('id')) for entry,_,_ in masters]
    all_ids += [int(e.get('id')) for _,_,m in masters for e in m.findall('p:sldLayoutIdLst/p:sldLayoutId',NS)]
    next_id=max(all_ids+[2147483647])+1
    used=set()
    changed_ids=[]
    for entry,part,master in masters:
        changed=False
        for element in [entry]+master.findall('p:sldLayoutIdLst/p:sldLayoutId',NS):
            value=int(element.get('id'))
            if value in used:
                element.set('id',str(next_id))
                changed_ids.append({'part':'ppt/presentation.xml' if element is entry else part,'old':value,'new':next_id})
                value=next_id
                next_id+=1
                if element is not entry:changed=True
            used.add(value)
        if changed:data[part]=serialize(master)
    data['ppt/presentation.xml']=serialize(pres)
    data['ppt/_rels/presentation.xml.rels']=serialize(rels)
    return {'consolidatedNotesMasters':removed,'renumberedIds':changed_ids}

def staged_entrance(page, specs):
    """Extend the existing opening's native click/fade structure to three stages."""
    for old in page.findall('p:timing', NS):
        page.remove(old)
    if not any(s['stage']>0 for s in specs):
        return
    timing = E.Element('{'+P+'}timing')
    counter = iter(range(1, 10000))
    def el(parent, tag, **attrs):
        return E.SubElement(parent, '{'+P+'}'+tag, {k:str(v) for k,v in attrs.items()})
    def ctn(parent, **attrs):
        return el(parent, 'cTn', id=next(counter), **attrs)
    def start(parent, delay):
        el(el(parent, 'stCondLst'), 'cond', delay=delay)
    def behavior(parent, spid, duration, hold=False):
        b = el(parent, 'cBhvr')
        t = ctn(b, dur=duration, **({'fill':'hold'} if hold else {}))
        el(el(b, 'tgtEl'), 'spTgt', spid=spid)
        return b, t
    root = ctn(el(el(timing,'tnLst'),'par'), dur='indefinite', restart='never', nodeType='tmRoot')
    seq = el(el(root,'childTnLst'),'seq', concurrent='1', nextAc='seek')
    main = ctn(seq, dur='indefinite', nodeType='mainSeq')
    clicks = el(main,'childTnLst')
    text_ids = []
    for stage in sorted({s['stage'] for s in specs if s['stage']>0}):
        click = ctn(el(clicks,'par'), fill='hold')
        start(click,'indefinite')
        parallel = ctn(el(el(click,'childTnLst'),'par'), fill='hold')
        start(parallel,'0')
        effects = el(parallel,'childTnLst')
        for index, spec in enumerate(s for s in specs if s['stage']==stage):
            matches = page.xpath('//p:cNvPr[@name=$n]', namespaces=NS, n=spec['name'])
            assert len(matches)==1, spec
            nv = matches[0]
            spid = nv.get('id')
            effect = ctn(el(effects,'par'), presetID='0' if spec.get('moveOnly') else '10', presetClass='path' if spec.get('moveOnly') else 'entr', presetSubtype='0',
                         fill='hold', nodeType='clickEffect' if index==0 else 'withEffect')
            start(effect,str(spec.get('delayMs',0)))
            children = el(effect,'childTnLst')
            if not spec.get('moveOnly'):
                setter = el(children,'set')
                b,t = behavior(setter,spid,'1',True)
                start(t,'0')
                el(el(b,'attrNameLst'),'attrName').text='style.visibility'
                el(el(setter,'to'),'strVal',val='visible')
                fade = el(children,'animEffect',transition='in',filter='fade')
                behavior(fade,spid,'200' if 'motion' in spec else '400')
            if 'motion' in spec:
                delta=spec['motion']
                first=delta.get('from',delta)
                last=delta.get('to',{'dx':0,'dy':0})
                scale_from=delta.get('scaleFrom')
                if 'fromName' in delta:
                    anchor=page.xpath('//p:cNvPr[@name=$n]',namespaces=NS,n=delta['fromName'])
                    assert len(anchor)==1, delta
                    def center(item):
                        xf=item.getparent().getparent().find('.//a:xfrm',NS)
                        off,ext=xf.find('a:off',NS),xf.find('a:ext',NS)
                        return [int(off.get(k))+int(ext.get('c'+k))/2 for k in ('x','y')]
                    src,dst=center(anchor[0]),center(nv)
                    first={'dx':(src[0]-dst[0])/(1280*9525),'dy':(src[1]-dst[1])/(720*9525)}
                    src_ext=anchor[0].getparent().getparent().find('.//a:xfrm/a:ext',NS)
                    dst_ext=nv.getparent().getparent().find('.//a:xfrm/a:ext',NS)
                    ratio=min(1,*[int(src_ext.get(k))/int(dst_ext.get(k)) for k in ('cx','cy')])
                    scale_from=({'x':int(src_ext.get('cx'))/int(dst_ext.get('cx')),
                                 'y':int(src_ext.get('cy'))/int(dst_ext.get('cy'))}
                                if delta.get('matchSourceShape') else {'x':ratio,'y':ratio})
                motion=el(children,'animMotion',origin='layout',pathEditMode='relative',
                          path=f"M {first['dx']:.8f} {first['dy']:.8f} L {last['dx']:.8f} {last['dy']:.8f} E")
                b,t=behavior(motion,spid,'700',True)
                attrs=el(b,'attrNameLst')
                for name in ('ppt_x','ppt_y'):el(attrs,'attrName').text=name
                if scale_from:
                    scale=el(children,'animScale',zoomContents='1')
                    behavior(scale,spid,'700',True)
                    el(scale,'from',x=round(scale_from['x']*100000),y=round(scale_from['y']*100000))
                    el(scale,'to',x=100000,y=100000)
            shape=nv.getparent().getparent()
            if shape.tag=='{'+P+'}sp' and shape.find('p:txBody',NS) is not None:
                text_ids.append(spid)
    for name,event in [('prevCondLst','onPrev'),('nextCondLst','onNext')]:
        cond=el(el(seq,name),'cond',evt=event,delay='0')
        el(el(cond,'tgtEl'),'sldTgt')
    if text_ids:
        builds=el(timing,'bldLst')
        for spid in dict.fromkeys(text_ids):el(builds,'bldP',spid=spid,grpId='0',animBg='1')
    ext=page.find('p:extLst',NS)
    if ext is None:page.append(timing)
    else:page.insert(list(page).index(ext),timing)

def replace_fdm(source_path, donor_path, output_path, manifest_path):
    source,donor=read(source_path),read(donor_path)
    output=source.copy()
    paths=slides(source)
    assert len(paths)==22
    manifest=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    target=paths[6]
    donor_slide=slides(donor)[0]
    page=E.fromstring(source[target])
    donor_page=E.fromstring(donor[donor_slide])
    page.replace(page.find('p:cSld',NS),deepcopy(donor_page.find('p:cSld',NS)))
    rels=E.fromstring(source[relpath(target)])
    for rel in list(rels):
        if rel.get('Type') not in (R+'/slideLayout',R+'/notesSlide'):rels.remove(rel)
    donor_rels={r.get('Id'):r for r in E.fromstring(donor[relpath(donor_slide)])}
    pics=page.findall('.//p:pic',NS)
    assert len(pics)==len(manifest['equations'])
    ASVG='http://schemas.microsoft.com/office/drawing/2016/SVG/main'
    CT='http://schemas.openxmlformats.org/package/2006/content-types'
    types=E.fromstring(output['[Content_Types].xml'])
    for index,(pic,spec) in enumerate(zip(pics,manifest['equations'])):
        blip=pic.find('p:blipFill/a:blip',NS)
        donor_image=resolve_part(donor_slide,donor_rels[blip.get('{'+R+'}embed')].get('Target'))
        image_part='ppt/media/fdm_revision_'+spec['key']+'.png'
        output[image_part]=donor[donor_image]
        png_id='rIdFdmPng'+str(index)
        svg_id='rIdFdmSvg'+str(index)
        blip.set('{'+R+'}embed',png_id)
        svg_part='ppt/media/fdm_revision_'+spec['key']+'.svg'
        svg=E.fromstring((Path(manifest_path).parent/spec['file']).read_bytes())
        dims=[float(n) for n in svg.get('viewBox').split()]
        svg.set('width',str(dims[2]*32)+'px');svg.set('height',str(dims[3]*32)+'px')
        output[svg_part]=serialize(svg)
        for rid,part in [(png_id,image_part),(svg_id,svg_part)]:
            E.SubElement(rels,'{'+PKG+'}Relationship',Id=rid,Type=R+'/image',Target=posixpath.relpath(part,posixpath.dirname(target)))
        extlst=blip.find('a:extLst',NS)
        if extlst is None:extlst=E.SubElement(blip,'{'+A+'}extLst')
        ext=E.SubElement(extlst,'{'+A+'}ext',uri='{96DAC541-7B7A-43D3-8B79-37D633B846F1}')
        E.SubElement(ext,'{'+ASVG+'}svgBlip',{'{'+R+'}embed':svg_id})
        nv=pic.find('p:nvPicPr/p:cNvPr',NS)
        nv.set('name',spec['key']);nv.set('descr',spec['tex'])
    defaults={e.get('Extension') for e in types}
    for ext,mime in [('png','image/png'),('svg','image/svg+xml')]:
        if ext not in defaults:E.SubElement(types,'{'+CT+'}Default',Extension=ext,ContentType=mime)
    output['[Content_Types].xml']=serialize(types)
    for i,spec in enumerate(manifest['links']):
        nv=page.xpath('//p:cNvPr[@name=$n]',namespaces=NS,n=spec['name'])[0]
        rid='rIdFdmLink'+str(i)
        E.SubElement(rels,'{'+PKG+'}Relationship',Id=rid,Type=R+'/slide',Target=posixpath.relpath(paths[spec['target']-1],posixpath.dirname(target)))
        for node in [nv]+nv.getparent().getparent().xpath('.//a:rPr',namespaces=NS):
            h=E.Element('{'+A+'}hlinkClick',{'{'+R+'}id':rid,'action':'ppaction://hlinksldjump'})
            ext=node.find('a:extLst',NS)
            if ext is None:node.append(h)
            else:node.insert(list(node).index(ext),h)
    old_notes=next(r for r in rels if r.get('Type')==R+'/notesSlide')
    new_notes=next(r for r in donor_rels.values() if r.get('Type')==R+'/notesSlide')
    old_notes_path=resolve_part(target,old_notes.get('Target'))
    new_notes_path=resolve_part(donor_slide,new_notes.get('Target'))
    note=E.fromstring(output[old_notes_path])
    note.replace(note.find('p:cSld',NS),deepcopy(E.fromstring(donor[new_notes_path]).find('p:cSld',NS)))
    output[old_notes_path]=serialize(note)
    if manifest.get('animation'):
        staged_entrance(page,manifest['animation'])
    output[target],output[relpath(target)]=serialize(page),serialize(rels)
    report=repair_package(output)
    assert slides(output)==paths
    assert all(source[p]==output[p] for i,p in enumerate(paths) if i!=6)
    with ZipFile(output_path,'x',compression=ZIP_DEFLATED) as z:
        for part,payload in output.items():z.writestr(part,payload)
    report['unchangedSlideBodies']=21
    (Path(manifest_path).parent/'repair-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
def verify(source,output,links):
    paths=slides(source)
    changed=[k for k in source if source[k]!=output.get(k)]
    assert set(source)==set(output)
    assert set(changed)=={paths[1],relpath(paths[1])},changed
    assert slides(output)==paths
    slide=E.fromstring(output[paths[1]])
    rels=E.fromstring(output[relpath(paths[1])])
    for spec in links:
        nv=slide.xpath('//p:cNvPr[@name=$n]',namespaces=NS,n=spec['name'])
        assert len(nv)==1,spec
        h=nv[0].find('a:hlinkClick',NS)
        assert h is not None and h.get('action')=='ppaction://hlinksldjump',spec
        rel=next(r for r in rels if r.get('Id')==h.get('{'+R+'}id'))
        target=posixpath.normpath(posixpath.join(posixpath.dirname(paths[1]),rel.get('Target')))
        assert target==paths[spec['target']-1],spec
    assert len(links)==8
    assert not slide.xpath('//a:t[contains(text(),"PAM Eq.")]',namespaces=NS)
    print('PASS: only slide 2 and its relationship part changed; all other package entries byte-identical. Eight internal links verified.')

def append_content(source_path, donor_path, output_path, manifest_path, base_data=None):
    source, donor = base_data if base_data is not None else read(source_path), read(donor_path)
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    output = source.copy()
    original, added = slides(source), slides(donor)
    assert len(original)==3 and len(added)==len(manifest['equations']), 'Requires the three-slide opening and the declared content'
    prefix=manifest.get('partPrefix','t3_')
    CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
    ASVG = 'http://schemas.microsoft.com/office/drawing/2016/SVG/main'
    def xml(node):
        return E.tostring(node, xml_declaration=True, encoding='UTF-8', standalone=True)
    def resolved(owner, target):
        return posixpath.normpath(posixpath.join(posixpath.dirname(owner), target)).lstrip('/')
    def mapped(part):
        if '/_rels/' in part:
            folder, basename = part.split('/_rels/')
            return folder+'/_rels/'+prefix+basename
        return posixpath.join(posixpath.dirname(part), prefix+posixpath.basename(part))
    # Each formula retains a PNG fallback and a vector SVG relationship.
    for index, owner in enumerate(added):
        page = E.fromstring(donor[owner])
        rels = E.fromstring(donor[relpath(owner)])
        pics = page.findall('.//p:pic', NS)
        specs = manifest['equations'][index]
        assert len(pics) == len(specs), (index, len(pics), len(specs))
        for pic, spec in zip(pics, specs):
            asset = 'ppt/media/'+spec['key']+'.svg'
            svg = E.fromstring((Path(manifest_path).parent/spec['file']).read_bytes())
            bounds = [float(v) for v in svg.get('viewBox').split()]
            svg.set('width', str(bounds[2]*32)+'px')
            svg.set('height', str(bounds[3]*32)+'px')
            donor[asset] = xml(svg)
            rid = 'rIdVector'+spec['key']
            E.SubElement(rels, '{'+PKG+'}Relationship', Id=rid, Type=R+'/image',
                         Target=posixpath.relpath(asset, posixpath.dirname(owner)))
            blip = pic.find('p:blipFill/a:blip', NS)
            extlst = E.SubElement(blip, '{'+A+'}extLst')
            ext = E.SubElement(extlst, '{'+A+'}ext', uri='{96DAC541-7B7A-43D3-8B79-37D633B846F1}')
            E.SubElement(ext, '{'+ASVG+'}svgBlip', {'{'+R+'}embed':rid})
            nv = pic.find('p:nvPicPr/p:cNvPr', NS)
            nv.set('name', spec['key'])
            nv.set('descr', spec['tex'])
        donor[owner], donor[relpath(owner)] = xml(page), xml(rels)
        if manifest.get('animations'):
            staged_entrance(page, manifest['animations'][index])
            donor[owner]=xml(page)
    exclude = {'ppt/presentation.xml', 'ppt/_rels/presentation.xml.rels'}
    for part, payload in donor.items():
        if not part.startswith('ppt/') or part in exclude:
            continue
        if part.endswith('.rels'):
            rels = E.fromstring(payload)
            folder, filename = part.split('/_rels/')
            owner = folder+'/'+filename[:-5]
            for rel in rels:
                if rel.get('TargetMode') == 'External':
                    continue
                destination = resolved(owner, rel.get('Target'))
                if destination == 'ppt/presentation.xml':
                    destination_new = destination
                else:
                    destination_new = mapped(destination)
                rel.set('Target', posixpath.relpath(destination_new, posixpath.dirname(mapped(owner))))
            payload = xml(rels)
        output[mapped(part)] = payload
    content_types = E.fromstring(source['[Content_Types].xml'])
    defaults = {e.get('Extension') for e in content_types if e.tag.endswith('Default')}
    for e in E.fromstring(donor['[Content_Types].xml']):
        clone = deepcopy(e)
        if e.tag.endswith('Default'):
            if e.get('Extension') in defaults:
                continue
            defaults.add(e.get('Extension'))
        else:
            part = e.get('PartName').lstrip('/')
            if not part.startswith('ppt/') or part in exclude:
                continue
            clone.set('PartName', '/'+mapped(part))
        content_types.append(clone)
    if 'svg' not in defaults:
        E.SubElement(content_types, '{'+CT+'}Default', Extension='svg', ContentType='image/svg+xml')
    output['[Content_Types].xml'] = xml(content_types)
    pres = E.fromstring(source['ppt/presentation.xml'])
    rels = E.fromstring(source['ppt/_rels/presentation.xml.rels'])
    slide_list = pres.find('p:sldIdLst', NS)
    next_id = max(int(e.get('id')) for e in slide_list)+1
    allpaths = original+[mapped(part) for part in added]
    for i, part in enumerate(allpaths[3:]):
        rid = 'rIdTutorial3Slide'+str(i+1)
        E.SubElement(rels, '{'+PKG+'}Relationship', Id=rid, Type=R+'/slide', Target=posixpath.relpath(part, 'ppt'))
        E.SubElement(slide_list, '{'+P+'}sldId', {'id':str(next_id+i), '{'+R+'}id':rid})
    donor_rels = E.fromstring(donor['ppt/_rels/presentation.xml.rels'])
    for rel in donor_rels:
        kind = rel.get('Type').rsplit('/', 1)[-1]
        if kind not in ('slideMaster', 'notesMaster'):
            continue
        list_name, item_name = ('sldMasterIdLst','sldMasterId') if kind=='slideMaster' else ('notesMasterIdLst','notesMasterId')
        owner_list = pres.find('p:'+list_name, NS)
        if owner_list is None:
            owner_list = E.Element('{'+P+'}'+list_name)
            pres.insert(list(pres).index(slide_list), owner_list)
        rid = 'rIdT3'+kind+rel.get('Id')
        target = mapped(resolved('ppt/presentation.xml', rel.get('Target')))
        E.SubElement(rels, '{'+PKG+'}Relationship', Id=rid, Type=rel.get('Type'), Target=posixpath.relpath(target,'ppt'))
        attrs = {'{'+R+'}id':rid}
        if kind=='slideMaster':
            attrs['id'] = str(max([int(e.get('id')) for e in owner_list]+[2147483647])+1)
        E.SubElement(owner_list, '{'+P+'}'+item_name, attrs)
    output['ppt/presentation.xml'],output['ppt/_rels/presentation.xml.rels']=xml(pres),xml(rels)
    links = [{'slide':3, 'name':'!!detail_tx_AM', 'target':4}]+manifest['links']
    for i, spec in enumerate(links):
        owner = allpaths[spec['slide']-1]
        page, rels = E.fromstring(output[owner]), E.fromstring(output[relpath(owner)])
        found = page.xpath('//p:cNvPr[@name=$n]', namespaces=NS, n=spec['name'])
        assert len(found)==1, spec
        rid = 'rId'+prefix+'Link'+str(i)
        E.SubElement(rels, '{'+PKG+'}Relationship', Id=rid, Type=R+'/slide',
                     Target=posixpath.relpath(allpaths[spec['target']-1],posixpath.dirname(owner)))
        for node in [found[0]]+found[0].getparent().getparent().xpath('.//a:rPr',namespaces=NS):
            for old in node.findall('a:hlinkClick',NS):
                node.remove(old)
            h = E.Element('{'+A+'}hlinkClick', {'{'+R+'}id':rid, 'action':'ppaction://hlinksldjump'})
            ext = node.find('a:extLst', NS)
            if ext is None: node.append(h)
            else: node.insert(list(node).index(ext),h)
        output[owner],output[relpath(owner)]=xml(page),xml(rels)
    # Return to the exact same overview, without another entrance animation.
    closing = allpaths[manifest.get('closingSlide',18)-1]
    page = E.fromstring(output[original[2]])
    for node in list(page):
        if E.QName(node).localname in ('transition','timing','AlternateContent'):
            page.remove(node)
    closing_rels = E.fromstring(output[relpath(closing)])
    closing_notes = [deepcopy(r) for r in closing_rels if r.get('Type')==R+'/notesSlide']
    rels = E.fromstring(output[relpath(original[2])])
    for rel in list(rels):
        if rel.get('Type')==R+'/notesSlide':
            rels.remove(rel)
        elif rel.get('TargetMode')!='External':
            dest=resolved(original[2],rel.get('Target'))
            rel.set('Target',posixpath.relpath(dest,posixpath.dirname(closing)))
    for r in closing_notes:
        r.set('Id','rIdClosingNotes')
        rels.append(r)
    output[closing],output[relpath(closing)] = xml(page),xml(rels)
    for owner in allpaths[manifest.get('hiddenStart',19)-1:]:
        page = E.fromstring(output[owner])
        page.set('show','0')
        output[owner]=xml(page)
    if 'docProps/app.xml' in output:
        app=E.fromstring(output['docProps/app.xml'])
        for item in app:
            if E.QName(item).localname=='Slides': item.text=str(len(allpaths))
        output['docProps/app.xml']=xml(app)
    assert len(slides(output))==len(original)+len(added)
    assert all(source[p]==output[p] for p in original[:2])
    for owner in allpaths:
        rels=E.fromstring(output[relpath(owner)])
        lookup={r.get('Id'):r for r in rels}
        for h in E.fromstring(output[owner]).findall('.//a:hlinkClick',NS):
            r=lookup[h.get('{'+R+'}id')]
            assert resolved(owner,r.get('Target')) in allpaths
    repair_package(output)
    if base_data is not None:
        # Retain only parts reachable from the package root after replacing the lesson.
        reachable={'[Content_Types].xml','_rels/.rels'}
        pending=['']
        while pending:
            owner=pending.pop()
            rp='_rels/.rels' if not owner else relpath(owner)
            if rp not in output:continue
            reachable.add(rp)
            for rel in E.fromstring(output[rp]):
                if rel.get('TargetMode')=='External':continue
                dest=resolved(owner,rel.get('Target'))
                if dest not in reachable:
                    reachable.add(dest);pending.append(dest)
        output={k:v for k,v in output.items() if k in reachable}
        types=E.fromstring(output['[Content_Types].xml'])
        for item in list(types):
            if item.tag.endswith('Override') and item.get('PartName').lstrip('/') not in output:types.remove(item)
        output['[Content_Types].xml']=xml(types)
    with ZipFile(output_path,'x',compression=ZIP_DEFLATED) as z:
        for part,payload in output.items(): z.writestr(part,payload)
    print(f'PASS: {len(allpaths)} slides; first two slide bodies preserved; SVG formulas and internal links verified.')

def rebuild_content(source_path, donor_path, output_path, manifest_path):
    base=read(source_path)
    pres=E.fromstring(base['ppt/presentation.xml'])
    listing=pres.find('p:sldIdLst',NS)
    removed={e.get('{'+R+'}id') for e in list(listing)[3:]}
    for e in list(listing)[3:]:listing.remove(e)
    rels=E.fromstring(base['ppt/_rels/presentation.xml.rels'])
    for r in list(rels):
        if r.get('Id') in removed:rels.remove(r)
    base['ppt/presentation.xml']=serialize(pres)
    base['ppt/_rels/presentation.xml.rels']=serialize(rels)
    third=slides(base)[2]
    page=E.fromstring(base[third]);rels=E.fromstring(base[relpath(third)])
    slide_ids={r.get('Id') for r in rels if r.get('Type')==R+'/slide'}
    for h in page.findall('.//a:hlinkClick',NS):
        if h.get('{'+R+'}id') in slide_ids:h.getparent().remove(h)
    for r in list(rels):
        if r.get('Id') in slide_ids:rels.remove(r)
    base[third],base[relpath(third)]=serialize(page),serialize(rels)
    append_content(source_path,donor_path,output_path,manifest_path,base)

if sys.argv[1]=='rebuild-content':
    rebuild_content(*sys.argv[2:6])
elif sys.argv[1]=='replace-fdm':
    replace_fdm(*sys.argv[2:6])
elif sys.argv[1]=='append-content':
    append_content(*sys.argv[2:6])
elif sys.argv[1]=='check':
    source,output=read(sys.argv[2]),read(sys.argv[3])
    with open(sys.argv[4],encoding='utf-8') as f: links=json.load(f)
    verify(source,output,links)
else:
    source,draft=read(sys.argv[1]),read(sys.argv[2])
    output=source.copy()
    with open(sys.argv[4],encoding='utf-8') as f: links=json.load(f)
    paths=slides(source)
    target=paths[1]
    original=E.fromstring(source[target])
    authored=E.fromstring(draft[slides(draft)[1]])
    cs=original.find('p:cSld',NS)
    oldtree=cs.find('p:spTree',NS)
    tree=deepcopy(authored.find('p:cSld/p:spTree',NS))
    for child in list(tree):
        nv=child.find('.//p:cNvPr',NS)
        if nv is not None and (nv.get('name') or '').startswith('old_connector_'):
            tree.remove(child)
    cs.replace(oldtree,tree)
    rels=E.fromstring(source[relpath(target)])
    for i,spec in enumerate(links):
        rid='rIdSlide2Nav'+str(i+1)
        E.SubElement(rels,'{'+PKG+'}Relationship',Id=rid,Type=R+'/slide',Target=posixpath.relpath(paths[spec['target']-1],posixpath.dirname(target)))
        nv=tree.xpath('.//p:cNvPr[@name=$n]',namespaces=NS,n=spec['name'])[0]
        owners=[nv]+nv.getparent().getparent().xpath('.//a:rPr',namespaces=NS)
        for owner in owners:
            h=E.Element('{'+A+'}hlinkClick',{'{'+R+'}id':rid,'action':'ppaction://hlinksldjump'})
            ext=owner.find('{'+A+'}extLst')
            if ext is None: owner.append(h)
            else: owner.insert(list(owner).index(ext),h)
    output[target]=E.tostring(original,xml_declaration=True,encoding='UTF-8',standalone=True)
    output[relpath(target)]=E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)
    verify(source,output,links)
    with ZipFile(sys.argv[3],'x',compression=ZIP_DEFLATED) as z:
        for name,contents in output.items():z.writestr(name,contents)
