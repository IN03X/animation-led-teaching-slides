"""Create a static handout without opening or altering PowerPoint."""
import ast
import hashlib
import json
import os
import posixpath
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUN=Path(os.environ.get('PDF_RUN',str(HERE/'methods-work/pdf-export-r1')))
SOURCE=Path(os.environ.get('PDF_SOURCE',str(ROOT/'output/tutorial3/ELEG2310B_Tutorial3.pptx')))
TARGET=Path(os.environ.get('PDF_OUTPUT',str(ROOT/'output/tutorial3/ELEG2310B_Tutorial3.pdf')))
EXPECTED_SLIDES=int(os.environ.get('PDF_EXPECTED_SLIDES','63'))
TITLE=os.environ.get('PDF_TITLE','ELEG2310B Tutorial 3')
helper=HERE.parent/'slide2_revision/merge.py'
tree=ast.parse(helper.read_text(encoding='utf-8'));lib={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))],type_ignores=[]),str(helper),'exec'),lib)
read,slides,serialize,resolve,relpath,NS=[lib[k] for k in ('read','slides','serialize','resolve_part','relpath','NS')]
P,A,R,PKG=[lib[k] for k in ('P','A','R','PKG')]
sha=lambda b:hashlib.sha256(b).hexdigest()

if sys.argv[1]=='prepare':
    RUN.mkdir(exist_ok=False)
    data=read(SOURCE);out=data.copy();owners=slides(data)
    assert len(owners)==EXPECTED_SLIDES
    manifest={'sourceHash':sha(SOURCE.read_bytes()),'slides':len(owners),'links':[],'gifFinalFrames':[],'motionEndpoints':[]}
    t4_manifest=None
    if os.environ.get('PDF_T4_MANIFEST'):
        import importlib.util
        t4_manifest=json.loads(Path(os.environ['PDF_T4_MANIFEST']).read_text(encoding='utf-8'))
        package=json.loads(Path(os.environ['PDF_T4_PACKAGE']).read_text(encoding='utf-8'))
        spec=importlib.util.spec_from_file_location('pdf_click_media',HERE/'t4-click-media.py')
        click_media=importlib.util.module_from_spec(spec);spec.loader.exec_module(click_media)
        assert t4_manifest['total']==len(owners)
        manifest['nativeFrameFinals']=sum(len(v) for v in package['clickMedia']['mediaIndex'].values())
    types=E.fromstring(data['[Content_Types].xml'])
    assert any(el.get('Extension')=='png' for el in types)
    for number,owner in enumerate(owners,1):
        page=E.fromstring(data[owner]);rels=E.fromstring(data[relpath(owner)])
        if t4_manifest is not None:
            page=click_media.snapshot_page(page,package['clickMedia']['mediaIndex'],number)
            shapes=page.find('p:cSld/p:spTree',NS)
            specs=[s for s in t4_manifest['animation'] if s['slide']==number]
            aliases=package['aliases'][str(number)]
            exits={aliases.get(s['name'],s['name']) for s in specs if s.get('exitOnly')}
            for obj in list(shapes):
                nv=obj.find('.//p:cNvPr',NS)
                if nv is not None and (nv.get('name','').endswith('-rewrite-source') or nv.get('name') in exits):
                    shapes.remove(obj)
            for event in specs:
                if not event.get('moveOnly') or event.get('exitOnly'):continue
                end=event.get('motion',{}).get('to')
                if end is None:continue
                nv=page.xpath('//p:cNvPr[@name=$n]',namespaces=NS,n=aliases.get(event['name'],event['name']))
                if not nv:continue
                off=nv[0].getparent().getparent().find('.//a:xfrm/a:off',NS)
                off.set('x',str(round(int(off.get('x'))+end['dx']*12192000)))
                off.set('y',str(round(int(off.get('y'))+end['dy']*6858000)))
                manifest['motionEndpoints'].append({'slide':number,'shape':nv[0].get('id')})
            for node in page.findall('{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent'):
                page.remove(node)
        rr={r.get('Id'):r for r in rels}
        shapes=page.find('p:cSld/p:spTree',NS)
        byid={s.find('.//p:cNvPr',NS).get('id'):s for s in shapes if s.find('.//p:cNvPr',NS) is not None}
        endpoints={}
        for motion in page.findall('.//p:animMotion',NS):
            target=motion.find('.//p:spTgt',NS).get('spid')
            tokens=motion.get('path').split();last=tokens.index('L')
            endpoints[target]=(float(tokens[last+1]),float(tokens[last+2]))
        for sid,(dx,dy) in endpoints.items():
            if dx==dy==0:continue
            off=byid[sid].find('.//a:xfrm/a:off',NS)
            off.set('x',str(int(off.get('x'))+round(dx*12192000)))
            off.set('y',str(int(off.get('y'))+round(dy*6858000)))
            manifest['motionEndpoints'].append({'slide':number,'shape':sid})
        for pic in page.findall('.//p:pic',NS):
            blip=pic.find('.//a:blip',NS)
            if blip is None:continue
            rid=blip.get('{'+R+'}embed');rel=rr[rid]
            target=resolve(owner,rel.get('Target'))
            if not target.endswith('.gif'):continue
            dest=target[:-4]+'-pdf-final.png'
            if dest not in out:
                im=Image.open(BytesIO(data[target]));im.seek(im.n_frames-1)
                buffer=BytesIO();im.convert('RGBA').save(buffer,format='PNG');out[dest]=buffer.getvalue()
            rel.set('Target',posixpath.relpath(dest,posixpath.dirname(owner)))
            manifest['gifFinalFrames'].append(number)
        for shape in shapes:
            links=shape.findall('.//a:hlinkClick',NS)
            off=shape.find('.//a:xfrm/a:off',NS);ext=shape.find('.//a:xfrm/a:ext',NS)
            if off is None or ext is None:continue
            seen=set()
            for link in links:
                rid=link.get('{'+R+'}id')
                if not rid or rid in seen:continue
                seen.add(rid);rel=rr[rid]
                target=resolve(owner,rel.get('Target'))
                if target not in owners:continue
                manifest['links'].append({'from':number,'to':owners.index(target)+1,'rect':[int(off.get('x'))/12700,int(off.get('y'))/12700,int(ext.get('cx'))/12700,int(ext.get('cy'))/12700]})
        for tag in ('timing','transition'):
            for node in page.findall('p:'+tag,NS):page.remove(node)
        out[owner]=serialize(page);out[relpath(owner)]=serialize(rels)
    with ZipFile(RUN/'static.pptx','x',ZIP_DEFLATED) as z:
        for name,payload in out.items():z.writestr(name,payload)
    (RUN/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'slides':len(owners),'gifFinalFrames':len(manifest['gifFinalFrames'])}))
else:
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from pypdf import PdfReader
    m=json.loads((RUN/'manifest.json').read_text())
    assert sha(SOURCE.read_bytes())==m['sourceHash']
    target=TARGET
    assert not target.exists(),'Existing PDF must not be overwritten silently'
    private=RUN/target.name
    c=canvas.Canvas(str(private),pagesize=(960,540),pageCompression=1)
    c.setTitle(TITLE);c.setAuthor('WANG, Runbang; TIAN, Feng')
    for number in range(1,m['slides']+1):
        c.bookmarkPage('page'+str(number))
        c.drawImage(ImageReader(str(RUN/f'slide-{number:03}.png')),0,0,960,540)
        for link in m['links']:
            if link['from']!=number:continue
            x,y,w,h=link['rect']
            c.linkRect('', 'page'+str(link['to']), (x,540-y-h,x+w,540-y),relative=0,thickness=0)
        c.showPage()
    c.save()
    pdf=PdfReader(private)
    assert len(pdf.pages)==m['slides']==EXPECTED_SLIDES
    assert all(tuple(float(v) for v in p.mediabox)==(0,0,960,540) for p in pdf.pages)
    assert sum(len(p.get('/Annots',[])) for p in pdf.pages)==len(m['links'])
    with target.open('xb') as f:f.write(private.read_bytes())
    print(json.dumps({'pdf':str(target),'pages':len(pdf.pages),'links':len(m['links']),'bytes':target.stat().st_size}))
