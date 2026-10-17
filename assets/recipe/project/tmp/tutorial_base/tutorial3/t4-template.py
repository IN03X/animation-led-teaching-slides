"""Copy the actual T3 framing, heading objects, routes and layout ancestry."""
import hashlib
import importlib.util
import posixpath
from copy import deepcopy
from pathlib import Path
from lxml import etree as E


def inherit(data, types, manifest, root, lib):
    P,A,R,PKG,NS=[lib[k] for k in ('P','A','R','PKG','NS')]
    read,slides,relpath,resolve,serialize=[lib[k] for k in ('read','slides','relpath','resolve_part','serialize')]
    source=read(root/'output/tutorial3/ELEG2310B_Tutorial3.pptx')
    reference_slides=slides(source)
    source_types=E.fromstring(source['[Content_Types].xml'])
    CT=E.QName(types).namespace
    type_lookup={e.get('PartName','').lstrip('/'):e.get('ContentType') for e in source_types if e.tag.endswith('Override')}
    for entry in source_types:
        if entry.tag.endswith('Default') and not any(e.get('Extension')==entry.get('Extension') for e in types):types.append(deepcopy(entry))
    imported={}

    def import_part(part, destination=None):
        if part in imported and destination is None:return imported[part]
        folder=posixpath.dirname(part)
        dest=destination or folder+'/t3_reference_'+posixpath.basename(part)
        if '/media/' in part:
            dest='ppt/media/t3_reference_'+hashlib.sha256(source[part]).hexdigest()[:24]+posixpath.splitext(part)[1]
        imported[part]=dest
        data[dest]=source[part]
        if part in type_lookup and not any(e.get('PartName')=='/'+dest for e in types):
            E.SubElement(types,'{'+CT+'}Override',PartName='/'+dest,ContentType=type_lookup[part])
        if relpath(part) in source:
            rr=E.fromstring(source[relpath(part)])
            for relationship in rr:
                if relationship.get('TargetMode')=='External':continue
                target=import_part(resolve(part,relationship.get('Target')))
                relationship.set('Target',posixpath.relpath(target,posixpath.dirname(dest)))
            data[relpath(dest)]=serialize(rr)
        return dest

    def cloned_slide(ref, owner):
        page=E.fromstring(source[ref])
        for link in page.findall('.//a:hlinkClick',NS)+page.findall('.//a:hlinkMouseOver',NS):link.getparent().remove(link)
        rels=E.fromstring(source[relpath(ref)])
        # Notes point back to this copied slide, including a second router copy.
        imported[ref]=owner
        for relationship in list(rels):
            if relationship.get('Type')==R+'/slide':
                rels.remove(relationship);continue
            if relationship.get('TargetMode')=='External':continue
            part=resolve(ref,relationship.get('Target'))
            destination=None
            if relationship.get('Type')==R+'/notesSlide':
                destination='ppt/notesSlides/t3_reference_for_'+posixpath.basename(owner)
            target=import_part(part,destination)
            relationship.set('Target',posixpath.relpath(target,posixpath.dirname(owner)))
        return page,rels

    def course_navigation(page, slide):
        for node in page.findall('.//p:cNvPr',NS):
            text=' '.join(''.join(node.getparent().getparent().xpath('.//a:t/text()',namespaces=NS)).split())
            target=({'AM':'review','AM schemes':'review','PAM':'overview','PM':'review','FM':'review'} if manifest.get('tutorialNumber')==5 else {'AM':'course','AM schemes':'course','PAM':'course','PM':'pm-offset','FM':'fm'}).get(text)
            name=node.get('name','')
            if name.lstrip('!')=='signal' or name.endswith('-route-s') or text=='s(t)':target='overview'
            if manifest.get('tutorialNumber')==5 and name.endswith('pulse_formula'):target='overview'
            if target is not None:
                link={'slide':slide,'name':name,'target':target}
                manifest.setdefault('links',[]).append(link);course_links.append(link.copy())

    def cloned_object(ref, obj, owner, rels, name, obj_id):
        clone=deepcopy(obj)
        nv=clone.find('.//p:cNvPr',NS);nv.set('name',name);nv.set('id',str(obj_id))
        for link in clone.findall('.//a:hlinkClick',NS)+clone.findall('.//a:hlinkMouseOver',NS):link.getparent().remove(link)
        rr={e.get('Id'):e for e in E.fromstring(source[relpath(ref)])}
        for node in clone.iter():
            for attr in ['{'+R+'}embed','{'+R+'}link','{'+R+'}id']:
                old=node.get(attr)
                if old is None:continue
                relationship=deepcopy(rr[old]);new='rIdT3Object'+str(len(rels)+1)
                relationship.set('Id',new)
                if relationship.get('TargetMode')!='External':
                    target=import_part(resolve(ref,relationship.get('Target')))
                    relationship.set('Target',posixpath.relpath(target,posixpath.dirname(owner)))
                rels.append(relationship);node.set(attr,new)
        return clone

    def named(ref, suffix):
        page=E.fromstring(source[ref])
        return next((o for o in page.find('p:cSld/p:spTree',NS) if o.find('.//p:cNvPr',NS) is not None and o.find('.//p:cNvPr',NS).get('name','').endswith(suffix)),None)

    def set_text(obj,value):
        texts=obj.findall('.//a:t',NS)
        assert texts
        texts[0].text=value
        for text in texts[1:]:text.text=''

    title_ref=reference_slides[9]
    course_ref=reference_slides[3]
    opening_refs={'system':reference_slides[1],'ideal':reference_slides[2],'course':course_ref,'course-return':course_ref}
    ending_ref=reference_slides[39]
    audit=[];course_links=[]
    for i,owner in enumerate(slides(data)):
        page=E.fromstring(data[owner]);tree=page.find('p:cSld/p:spTree',NS)
        rels=E.fromstring(data[relpath(owner)]);info=manifest['pages'][i]
        is_course=info['id'] in ['course','course-return']
        if info['id'] in opening_refs:
            ref=opening_refs[info['id']]
            replacement=next((deepcopy(o) for o in tree if o.find('.//p:cNvPr',NS) is not None and o.find('.//p:cNvPr',NS).get('name')=='course-pulse'),None)
            donor_rels={r.get('Id'):deepcopy(r) for r in rels}
            page,rels=cloned_slide(ref,owner)
            if is_course and manifest.get('tutorialNumber')==5 and replacement is not None:
                old=next(o for o in page.find('p:cSld/p:spTree',NS) if o.find('.//p:cNvPr',NS) is not None and o.find('.//p:cNvPr',NS).get('name','').endswith('pulse_formula'))
                original_nv=old.find('.//p:cNvPr',NS);new_nv=replacement.find('.//p:cNvPr',NS)
                new_nv.set('id',original_nv.get('id'));new_nv.set('name',original_nv.get('name'))
                transform=replacement.find('p:spPr/a:xfrm',NS)
                donor_size=transform.find('a:ext',NS)
                ratio=int(donor_size.get('cy'))/int(donor_size.get('cx'))
                target_transform=deepcopy(old.find('p:spPr/a:xfrm',NS))
                target_size=target_transform.find('a:ext',NS);target_pos=target_transform.find('a:off',NS)
                previous_height=int(target_size.get('cy'));height=round(int(target_size.get('cx'))*ratio)
                target_size.set('cy',str(height));target_pos.set('y',str(int(target_pos.get('y'))+(previous_height-height)//2))
                transform.getparent().replace(transform,target_transform)
                for node in replacement.iter():
                    for attr in ('{'+R+'}embed','{'+R+'}link','{'+R+'}id'):
                        rid=node.get(attr)
                        if rid not in donor_rels:continue
                        relationship=deepcopy(donor_rels[rid]);new='rIdNote7Pulse'+str(len(rels)+1)
                        relationship.set('Id',new);rels.append(relationship);node.set(attr,new)
                old.getparent().replace(old,replacement)
            if info['id']=='course-return':
                for child in list(page):
                    if E.QName(child).localname in ('transition','AlternateContent'):page.remove(child)
            if manifest.get('tutorialNumber')==5:
                note_part=next((resolve(owner,r.get('Target')) for r in rels if r.get('Type')==R+'/notesSlide'),None)
                if note_part is not None:
                    notes=E.fromstring(data[note_part])
                    bodies=notes.xpath('//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=NS)
                    if bodies:
                        body=bodies[0]
                        for node in list(body):
                            if node.tag=='{'+A+'}p':body.remove(node)
                        paragraph=E.SubElement(body,'{'+A+'}p');run=E.SubElement(paragraph,'{'+A+'}r')
                        E.SubElement(run,'{'+A+'}t').text=info.get('note','')
                        data[note_part]=serialize(notes)
            # Generated objects and animation metadata cannot address the source tree.
            for key in ('links','animation','equations','geometry','formulaGroups','lineage','gifs'):
                if key in manifest:manifest[key][:]=[item for item in manifest[key] if item['slide']!=i+1]
            if is_course:course_navigation(page,i+1)
            data[owner]=serialize(page);data[relpath(owner)]=serialize(rels)
            audit.append({'slide':i+1,'referenceSlide':reference_slides.index(ref)+1,'coverOrEndCopied':False,'courseRouterCopied':is_course,'entireSlideCopied':True,'sourceTimingPreserved':True,'sourceTransitionPreserved':info['id']!='course-return'})
            continue
        ref=reference_slides[0] if info['id']=='cover' else ending_ref if info['id']=='end' else course_ref if is_course else title_ref
        layout_rel=next(r for r in E.fromstring(source[relpath(ref)]) if r.get('Type')==R+'/slideLayout')
        layout=import_part(resolve(ref,layout_rel.get('Target')))
        next(r for r in rels if r.get('Type')==R+'/slideLayout').set('Target',posixpath.relpath(layout,posixpath.dirname(owner)))
        if info['id'] in ['cover','end']:
            original_tree=E.fromstring(source[ref]).find('p:cSld/p:spTree',NS)
            fresh=deepcopy(original_tree)
            for child in list(fresh)[2:]:fresh.remove(child)
            for index,obj in enumerate(list(original_tree)[2:],2):
                nv=obj.find('.//p:cNvPr',NS)
                if nv is None:
                    fresh.append(deepcopy(obj));continue
                clone=cloned_object(ref,obj,owner,rels,nv.get('name'),index)
                number=manifest.get('tutorialNumber',4)
                if nv.get('name')=='title':set_text(clone,f'Tutorial {number}' if info['id']=='cover' else f'End of Tutorial {number}')
                if nv.get('name')=='topic':set_text(clone,manifest.get('topic','Phase and Frequency Modulation'))
                if nv.get('name')=='assistants':set_text(clone,'Teaching Assistants: WANG, Runbang; TIAN, Feng')
                fresh.append(clone)
            tree.getparent().replace(tree,fresh)
        else:
            for name, suffix, value in [('title','-title',info.get('title')),('subtitle','-subtitle',info.get('subtitle'))]:
                if not value:continue
                obj=next((o for o in tree if o.find('.//p:cNvPr',NS) is not None and o.find('.//p:cNvPr',NS).get('name')==name),None)
                original=named(ref,suffix)
                if obj is None or original is None:continue
                clone=cloned_object(ref,original,owner,rels,name,obj.find('.//p:cNvPr',NS).get('id'))
                set_text(clone,value);tree.replace(obj,clone)
            # Keep the parent's three-node geometry and active/inactive math styling.
        data[owner]=serialize(page);data[relpath(owner)]=serialize(rels)
        audit.append({'slide':i+1,'referenceSlide':reference_slides.index(ref)+1,'coverOrEndCopied':info['id'] in ['cover','end'],'courseRouterCopied':is_course})

    # Register imported masters so the inherited layout/theme is fully connected.
    pres=E.fromstring(data['ppt/presentation.xml'])
    rels=E.fromstring(data['ppt/_rels/presentation.xml.rels'])
    masters=pres.find('p:sldMasterIdLst',NS)
    for old,new in imported.items():
        if type_lookup.get(old)!='application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml':continue
        rid='rIdT3Master'+str(len(rels)+1)
        E.SubElement(rels,'{'+PKG+'}Relationship',Id=rid,Type=R+'/slideMaster',Target=posixpath.relpath(new,'ppt'))
        E.SubElement(masters,'{'+P+'}sldMasterId',{'id':str(2147490000+len(masters)),'{'+R+'}id':rid})
    data['ppt/presentation.xml']=serialize(pres);data['ppt/_rels/presentation.xml.rels']=serialize(rels)
    spec=importlib.util.spec_from_file_location('t4_notes_integrity',Path(__file__).with_name('t4-notes-integrity.py'))
    notes_integrity=importlib.util.module_from_spec(spec);spec.loader.exec_module(notes_integrity)
    data['[Content_Types].xml']=serialize(types)
    notes_report=notes_integrity.normalize(data)
    # normalize may update the content-types part; retain this caller-owned tree.
    normalized_types=E.fromstring(data['[Content_Types].xml'])
    types[:]=list(normalized_types)
    return {'referenceSha256':manifest['sourceHashes']['output/tutorial3/ELEG2310B_Tutorial3.pptx'],'slides':audit,'importedParts':len(imported),'courseLinks':course_links,'notesIntegrity':notes_report}
