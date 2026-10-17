"""Independent audit of a NEW generic-topic PPT; never invoke course-specific assertions."""
import argparse
import hashlib
import json
import posixpath
import re
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
N={'p':P,'a':A,'r':R}
def resolve(owner,target):return posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.dirname(owner)+'/'+target)
def relpart(owner):return posixpath.join(posixpath.dirname(owner),'_rels',posixpath.basename(owner)+'.rels')
def inspect(candidate):
    with ZipFile(candidate) as z:
        assert z.testzip() is None
        data={n:z.read(n) for n in z.namelist()}
    pres=E.fromstring(data['ppt/presentation.xml'])
    rr={x.get('Id'):x for x in E.fromstring(data[relpart('ppt/presentation.xml')])}
    parts=[resolve('ppt/presentation.xml',rr[x.get('{'+R+'}id')].get('Target')) for x in pres.find('p:sldIdLst',N)]
    assert len(parts)==len(set(parts)) and len(parts)>1
    slide_numbers={part:n for n,part in enumerate(parts,1)}
    pages=[];links=[];leaks=[];relationships=0
    for number,owner in enumerate(parts,1):
        page=E.fromstring(data[owner]);rels={x.get('Id'):x for x in E.fromstring(data[relpart(owner)])}
        ids=page.xpath('.//p:cNvPr/@id',namespaces=N);tids=page.xpath('.//p:cTn/@id',namespaces=N)
        assert len(ids)==len(set(ids)) and len(tids)==len(set(tids)),owner
        assert set(page.xpath('.//p:spTgt/@spid',namespaces=N))<=set(ids),owner
        assert set(page.xpath('.//p:tn/@val',namespaces=N))<=set(tids),owner
        for node in page.iter():
            for attr,value in node.attrib.items():
                if attr in ['{'+R+'}embed','{'+R+'}link','{'+R+'}id']:assert value in rels,(owner,value)
        visible=' '.join(page.xpath('.//a:t/text()',namespaces=N))
        notes=[]
        for rel in rels.values():
            if rel.get('TargetMode')=='External':continue
            dest=resolve(owner,rel.get('Target'));assert dest in data,(owner,dest);relationships+=1
            if rel.get('Type')==R+'/notesSlide':notes.extend(E.fromstring(data[dest]).xpath('.//a:t/text()',namespaces=N))
        identity=re.findall(r'ELEG2310B|WANG,? Runbang|TIAN,? Feng|runbang@|Note\s*7|Pulse Modulation',' '.join([visible,*notes]),re.I)
        if identity:leaks.append({'page':number,'matches':identity})
        for link in page.xpath('//*[local-name()="hlinkClick" or local-name()="hlinkHover"]'):
            rid=link.get('{'+R+'}id')
            if rid and rels[rid].get('Type')==R+'/slide':
                dest=resolve(owner,rels[rid].get('Target'));assert dest in slide_numbers
                links.append({'page':number,'targetPage':slide_numbers[dest]})
        main=page.find('.//p:cTn[@nodeType="mainSeq"]/p:childTnLst',N)
        pages.append({'page':number,'shapeCount':len(ids),'nativeClickGroups':len(main) if main is not None else 0,
                      'pictureCount':len(page.findall('.//p:pic',N)),'visibleText':visible})
    assert not leaks,leaks
    assert sum(x['nativeClickGroups'] for x in pages)>0,'Not an animated deck'
    schema=E.XMLSchema(E.parse(str(Path.home()/'.codex/skills/animation-led-teaching-slides/assets/vendor/schemas/ISO-IEC29500-4_2016/pml.xsd')))
    for owner in parts:assert schema.validate(E.fromstring(data[owner])),(owner,str(schema.error_log))
    return {'passed':True,'candidate':str(candidate),'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'slides':len(parts),'nativeClickGroups':sum(x['nativeClickGroups'] for x in pages),'links':links,
            'allSchemasAndTimingTargetsValid':True,'courseIdentityLeak':False,'relationshipsChecked':relationships,
            'pages':pages,'nativePowerPointTested':False,
            'claimBoundary':'Actual packaged slide/schema/target/visible-text audit; not mathematics, visual teaching quality or native playback.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('candidate',type=Path);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    report=inspect(args.candidate.resolve())
    with args.report.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ['pages','links']},indent=2))
