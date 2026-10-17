"""Read-only, project-independent checks of the later archived teaching case."""
import hashlib
import io
import json
import posixpath
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as E
from PIL import Image

SKILL=Path(__file__).resolve().parents[1];CASE=SKILL/'assets/continuity'
P='http://schemas.openxmlformats.org/presentationml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
N={'p':P,'r':R}
sha=lambda file:hashlib.sha256(file.read_bytes()).hexdigest()
provenance=json.loads((CASE/'provenance.json').read_text(encoding='utf-8'))
deck=CASE/provenance['sourceDeck'];assert sha(deck)==provenance['sourceSha256']
for item in provenance['images']:assert sha(CASE/item['file'])==item['sha256']
with ZipFile(deck) as z:
    assert z.testzip() is None
    rels={x.get('Id'):x for x in E.fromstring(z.read('ppt/_rels/presentation.xml.rels'))}
    pres=E.fromstring(z.read('ppt/presentation.xml'))
    targets=[rels[x.get('{'+R+'}id')].get('Target') for x in pres.find('p:sldIdLst',N)]
    parts=[posixpath.normpath(t.lstrip('/') if t.startswith('/') else 'ppt/'+t) for t in targets]
    assert len(parts)==116
    zooms=0;pages={}
    for part in parts:
        root=E.fromstring(z.read(part));pages[parts.index(part)+1]=root
        groups=root.findall('.//p:cTn[@nodeType="mainSeq"]/p:childTnLst/p:par',N)
        clips={}
        for cn in root.findall('.//p:cNvPr',N):
            name=cn.get('name','')
            if 'zoom' in name and '--t4-click-frame-001' in name:clips[name]=cn.get('id')
        for name,sid in clips.items():
            matching=[g for g in groups if sid in [v.get('spid') for v in g.findall('.//p:spTgt',N)]]
            assert len(matching)==1,(part,name)
            gate=matching[0].find('p:cTn/p:stCondLst/p:cond',N)
            assert gate is not None and gate.get('delay')=='indefinite',(part,name,'zoom no longer click-start')
            zooms+=1
    assert zooms==62,zooms
    def frame(page,clip,last):
        owner=parts[page-1];rp=posixpath.join(posixpath.dirname(owner),'_rels',posixpath.basename(owner)+'.rels')
        rr={x.get('Id'):x for x in E.fromstring(z.read(rp))};frames=[]
        for pic in pages[page].findall('.//p:pic',N):
            cn=pic.find('p:nvPicPr/p:cNvPr',N);name=cn.get('name','')
            if name==clip or name.startswith(clip+'--t4-click-frame-'):
                frames.append((0 if name==clip else int(name.rsplit('-',1)[1]),pic))
        frames.sort(key=lambda x:x[0]);assert frames,(page,clip)
        pic=frames[-1 if last else 0][1]
        blip=next(x for x in pic.iter() if x.tag.endswith('}blip'))
        target=rr[blip.get('{'+R+'}embed')].get('Target')
        part=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.dirname(owner)+'/'+target)
        with Image.open(io.BytesIO(z.read(part))) as image:
            image=image.convert('RGBA');return image.size,hashlib.sha256(image.tobytes()).hexdigest()
    pairs=[((10,'pam-factors-flow-2',True),(11,'pam-factors-zoom-0-in',False)),
           ((11,'pam-factors-zoom-0-in',True),(17,'pam-factors-zoom-0-out',False)),
           ((17,'pam-factors-zoom-0-out',True),(18,'pam-factors-zoom-1-in',False)),
           ((18,'pam-factors-zoom-1-in',True),(21,'pam-factors-zoom-1-out',False)),
           ((21,'pam-factors-zoom-1-out',True),(10,'pam-factors-flow-2',True)),
           ((23,'pam-receiver-flow-1',True),(24,'pam-receiver-zoom-0-in',False))]
    for start,end in pairs:assert frame(*start)==frame(*end),('Discontinuous case frame',start,end)
print(json.dumps({'passed':True,'deckSha256':sha(deck),'slides':116,'referenceImages':len(provenance['images']),
                  'clickStartZooms':zooms,'requiresOriginalProject':False,'readOnly':True,
                  'pixelIdenticalSceneBoundaryPairs':len(pairs),'nativePowerPointTested':False,
                  'claimBoundary':'Archived identity, six scene boundaries and declared click gates only; not native navigation or teaching approval.'}))
