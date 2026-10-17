"""Reconcile duplicate notes masters without changing any slide or animation."""
import hashlib
import json
import posixpath
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS={'p':P,'a':A,'r':R}
MASTER_TYPE='application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml'

def relpath(owner):
    return posixpath.dirname(owner)+'/_rels/'+posixpath.basename(owner)+'.rels'

def resolve(owner,target):
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner),target)).lstrip('/')

def serialize(node):
    return E.tostring(node,xml_declaration=True,encoding='UTF-8',standalone=True)

def normalize(data):
    pres=E.fromstring(data['ppt/presentation.xml'])
    relationships=E.fromstring(data[relpath('ppt/presentation.xml')])
    lookup={r.get('Id'):r for r in relationships}
    entries=pres.findall('p:notesMasterIdLst/p:notesMasterId',NS)
    assert len(entries)==1,'Expected one registered notes master'
    registered=resolve('ppt/presentation.xml',lookup[entries[0].get('{'+R+'}id')].get('Target'))
    types=E.fromstring(data['[Content_Types].xml'])
    master_parts=[e.get('PartName').lstrip('/') for e in types if e.get('ContentType')==MASTER_TYPE]
    report={'canonicalMaster':registered,'mergedMasters':[],'notesUpdated':[]}
    for duplicate in master_parts:
        if duplicate==registered:continue
        assert E.tostring(E.fromstring(data[duplicate]),method='c14n')==E.tostring(E.fromstring(data[registered]),method='c14n'),'Different notes master requires manual reconciliation'
        theme_rel=next(r for r in E.fromstring(data[relpath(duplicate)]) if r.get('Type')==R+'/theme')
        theme=E.fromstring(data[resolve(duplicate,theme_rel.get('Target'))])
        fonts={kind:{script:theme.find('a:themeElements/a:fontScheme/a:'+kind+'Font/a:'+script,NS).get('typeface') for script in ('latin','ea','cs')} for kind in ('major','minor')}
        for part in list(data):
            if not part.startswith('ppt/notesSlides/_rels/') or not part.endswith('.rels'):continue
            owner='ppt/notesSlides/'+posixpath.basename(part)[:-5]
            rels=E.fromstring(data[part]);changed=False
            for rel in rels:
                if rel.get('Type')==R+'/notesMaster' and resolve(owner,rel.get('Target'))==duplicate:
                    rel.set('Target',posixpath.relpath(registered,posixpath.dirname(owner)));changed=True
            if not changed:continue
            # The two equivalent masters use different themes. Preserve the old
            # notes-body font explicitly before reconnecting to the sole master.
            notes=E.fromstring(data[owner])
            original_text=notes.xpath('//a:t/text()',namespaces=NS)
            for run in notes.findall('.//a:r',NS):
                props=run.find('a:rPr',NS)
                if props is None:props=E.Element('{'+A+'}rPr');run.insert(0,props)
                for script in ('latin','ea','cs'):
                    font=props.find('a:'+script,NS)
                    typeface=font.get('typeface') if font is not None else '+mn-lt'
                    if typeface and not typeface.startswith('+'):continue
                    family=fonts['major' if typeface.startswith('+mj') else 'minor'][script]
                    if not family:continue
                    if font is None:
                        font=E.Element('{'+A+'}'+script)
                        successor={'latin':('ea','cs','sym','hlinkClick','hlinkMouseOver','extLst'),'ea':('cs','sym','hlinkClick','hlinkMouseOver','extLst'),'cs':('sym','hlinkClick','hlinkMouseOver','extLst')}[script]
                        before=next((c for c in props if E.QName(c).localname in successor),None)
                        if before is None:props.append(font)
                        else:props.insert(list(props).index(before),font)
                    font.set('typeface',family)
            assert notes.xpath('//a:t/text()',namespaces=NS)==original_text
            data[owner]=serialize(notes);data[part]=serialize(rels)
            report['notesUpdated'].append(owner)
        # Omit only the superseded internal master from the new ZIP package.
        data.pop(duplicate);data.pop(relpath(duplicate))
        for entry in list(types):
            if entry.get('PartName')=='/'+duplicate:types.remove(entry)
        report['mergedMasters'].append(duplicate)
    if report['mergedMasters']:data['[Content_Types].xml']=serialize(types)
    validate(data)
    return report

def validate(data):
    types=E.fromstring(data['[Content_Types].xml'])
    masters=[e.get('PartName').lstrip('/') for e in types if e.get('ContentType')==MASTER_TYPE]
    assert len(masters)==1,'Package must contain exactly one notes master'
    pres=E.fromstring(data['ppt/presentation.xml'])
    rels=E.fromstring(data[relpath('ppt/presentation.xml')]);lookup={r.get('Id'):r for r in rels}
    entries=pres.findall('p:notesMasterIdLst/p:notesMasterId',NS)
    assert len(entries)==1
    assert resolve('ppt/presentation.xml',lookup[entries[0].get('{'+R+'}id')].get('Target'))==masters[0]
    for part,payload in data.items():
        if not part.endswith('.rels') or '/_rels/' not in part:continue
        owner=part.replace('/_rels/','/')[:-5]
        for rel in E.fromstring(payload):
            if rel.get('TargetMode')=='External':continue
            target=resolve(owner,rel.get('Target'))
            assert target in data,(part,target)
            if rel.get('Type')==R+'/notesMaster':assert target==masters[0],(part,target)

if __name__=='__main__':
    source,run=map(Path,sys.argv[1:3]);run.mkdir(parents=True,exist_ok=True)
    with ZipFile(source) as z:original={n:z.read(n) for n in z.namelist()}
    data=original.copy();report=normalize(data)
    changed=[n for n in data if data[n]!=original.get(n)]
    assert all(n.startswith('ppt/notesSlides/') or n=='[Content_Types].xml' for n in changed),changed
    assert all(data[n]==b for n,b in original.items() if n.startswith(('ppt/slides/','ppt/slideLayouts/','ppt/slideMasters/','ppt/media/')))
    schema=E.XMLSchema(E.parse('C:/Users/10486/.codex/skills/pptx/scripts/office/schemas/ISO-IEC29500-4_2016/pml.xsd'))
    for n in report['notesUpdated']:assert schema.validate(E.fromstring(data[n])),str(schema.error_log)
    candidate=run/'candidate.pptx'
    with ZipFile(candidate,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in data.items():z.writestr(n,b)
    with ZipFile(candidate) as z:assert z.testzip() is None
    report.update(sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),candidateSha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),changedParts=changed,slideAndAnimationPartsByteIdentical=True,nativePlaybackTested=False)
    (run/'compatibility-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
