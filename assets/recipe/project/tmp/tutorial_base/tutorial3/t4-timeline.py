"""Sample generated T4 click animations as static, modeled playback frames."""
import argparse
import ast
import hashlib
import json
import math
import posixpath
import re
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E


HERE=Path(__file__).resolve().parent
HELPER=HERE.parent/'slide2_revision/merge.py'
helper_tree=ast.parse(HELPER.read_text(encoding='utf-8'))
lib={}
exec(compile(ast.Module(body=[n for n in helper_tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))],type_ignores=[]),str(HELPER),'exec'),lib)
P,A,R,PKG,NS=[lib[k] for k in ('P','A','R','PKG','NS')]
read,slides,relpath,serialize=[lib[k] for k in ('read','slides','relpath','serialize')]
MC='http://schemas.openxmlformats.org/markup-compatibility/2006'
DEFAULT_PAGES=(6,7,8,9,13,20,21,37)
DEFAULT_TIMES=(0,350,700,950,1250,1450)


def timing_number(value, default=0):
    if value is None:return default
    if value=='indefinite':return math.inf
    return float(value)


def progress(elapsed, start, duration):
    if elapsed<start:return 0
    if duration<=0:return 1
    return min(1,(elapsed-start)/duration)


def linear_path(value):
    number=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
    if not re.fullmatch(r'\s*M\s*'+number+r'\s+'+number+r'(?:\s+L\s*'+number+r'\s+'+number+r')+\s+E\s*',value):raise ValueError('Unsupported motion path: '+value)
    numbers=list(map(float,re.findall(number,value)))
    return list(zip(numbers[::2],numbers[1::2]))

def path_position(points,q):
    lengths=[math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(points,points[1:])]
    left=q*sum(lengths)
    for a,b,length in zip(points,points[1:],lengths):
        if left<=length:
            f=left/length if length else 1
            return a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f
        left-=length
    return points[-1]


def click_effects(page, stage_numbers):
    clicks=page.xpath('//p:cTn[@nodeType="mainSeq"]/p:childTnLst/p:par',namespaces=NS)
    if len(clicks)!=len(stage_numbers):raise ValueError('Manifest stages do not match native click groups')
    effects=[]
    for stage,click in zip(stage_numbers,clicks):
        for node in click.xpath('.//p:cTn[@presetClass]',namespaces=NS):
            start=node.find('p:stCondLst/p:cond',NS)
            delay=timing_number(start.get('delay') if start is not None else None)
            actions=[]
            children=node.find('p:childTnLst',NS)
            if children is None:continue
            for child in children:
                kind=E.QName(child).localname
                if kind not in ('set','animEffect','animMotion','animScale'):
                    raise ValueError('Unsupported modeled animation: '+kind)
                behavior=child.find('p:cBhvr',NS)
                if behavior is None:raise ValueError('Missing animation behavior')
                timing=behavior.find('p:cTn',NS)
                cond=timing.find('p:stCondLst/p:cond',NS)
                target=behavior.find('p:tgtEl/p:spTgt',NS)
                action={'kind':kind,'id':target.get('spid'),'start':delay+timing_number(cond.get('delay') if cond is not None else None),'duration':timing_number(timing.get('dur'))}
                if kind=='set':
                    attrs=behavior.xpath('p:attrNameLst/p:attrName/text()',namespaces=NS)
                    if attrs!=['style.visibility']:raise ValueError('Unsupported set property: '+repr(attrs))
                    action['value']=child.find('p:to/p:strVal',NS).get('val')
                elif kind=='animEffect':
                    if child.get('filter')!='fade':raise ValueError('Only fade effects are modeled')
                    action['transition']=child.get('transition')
                elif kind=='animMotion':action['path']=linear_path(child.get('path'))
                else:
                    action['from']=tuple(float(child.find('p:from',NS).get(k))/100000 for k in ('x','y'))
                    action['to']=tuple(float(child.find('p:to',NS).get(k))/100000 for k in ('x','y'))
                actions.append(action)
            effects.append({'stage':stage,'entrance':node.get('presetClass')=='entr','actions':actions})
    return effects


def state_at(effects, stage, time_ms):
    ids={a['id'] for effect in effects for a in effect['actions']}
    states={spid:{'visible':True,'opacity':1.0,'offset':(0,0),'scale':(1,1)} for spid in ids}
    for effect in effects:
        if effect['entrance']:
            for action in effect['actions']:states[action['id']]['visible']=False
    for effect in effects:
        if effect['stage']>stage:continue
        elapsed=math.inf if effect['stage']<stage else time_ms
        for action in effect['actions']:
            if elapsed<action['start']:continue
            state=states[action['id']];kind=action['kind'];q=progress(elapsed,action['start'],action['duration'])
            if kind=='set':state['visible']=action['value']=='visible'
            elif kind=='animEffect':state['opacity']=q if action['transition']=='in' else 1-q
            elif kind=='animMotion':
                state['offset']=path_position(action['path'],q)
            else:state['scale']=tuple(a+(b-a)*q for a,b in zip(action['from'],action['to']))
    return states


def set_opacity(obj, opacity):
    if obj.tag=='{'+P+'}pic':
        blip=obj.find('p:blipFill/a:blip',NS)
        alpha=blip.find('a:alphaModFix',NS)
        if alpha is None:
            alpha=E.Element('{'+A+'}alphaModFix',amt='100000')
            extensions=blip.find('a:extLst',NS)
            if extensions is None:blip.append(alpha)
            else:blip.insert(list(blip).index(extensions),alpha)
        alpha.set('amt',str(round(int(alpha.get('amt','100000'))*opacity)))
    else:
        for color in obj.xpath('.//a:srgbClr|.//a:schemeClr|.//a:sysClr|.//a:prstClr|.//a:hslClr|.//a:scrgbClr',namespaces=NS):
            alpha=color.find('a:alpha',NS)
            if alpha is None:alpha=E.SubElement(color,'{'+A+'}alpha',val='100000')
            alpha.set('val',str(round(int(alpha.get('val','100000'))*opacity)))


def snapshot(page, effects, stage, time_ms, slide_size):
    result=deepcopy(page);states=state_at(effects,stage,time_ms)
    selected={a['id'] for effect in effects if effect['stage']==stage for a in effect['actions']}
    objects=[];tree=result.find('p:cSld/p:spTree',NS)
    for obj in list(tree):
        nv=obj.find('.//p:cNvPr',NS)
        if nv is None or nv.get('id') not in states:continue
        state=states[nv.get('id')];visible=state['visible'] and state['opacity']>0
        transform=obj.find('.//a:xfrm',NS)
        if transform is None:transform=obj.find('p:xfrm',NS)
        if transform is None:raise ValueError('Animated object has no transform: '+nv.get('name',''))
        off=transform.find('a:off',NS);ext=transform.find('a:ext',NS)
        x,y=[int(off.get(k)) for k in ('x','y')];w,h=[int(ext.get(k)) for k in ('cx','cy')]
        width,height=w*state['scale'][0],h*state['scale'][1]
        left=x+w/2+state['offset'][0]*slide_size[0]-width/2
        top=y+h/2+state['offset'][1]*slide_size[1]-height/2
        for key,value in [('x',left),('y',top)]:off.set(key,str(round(value)))
        for key,value in [('cx',width),('cy',height)]:ext.set(key,str(max(1,round(value))))
        if nv.get('id') in selected:
            objects.append({'name':nv.get('name'),'visible':visible,'opacity':state['opacity'] if visible else 0,'boundsEmu':[left,top,width,height],'scale':list(state['scale'])})
        if not visible:tree.remove(obj)
        elif state['opacity']<1:set_opacity(obj,state['opacity'])
    for node in list(result):
        if node.tag=='{'+P+'}timing' or node.tag=='{'+P+'}transition' or node.tag=='{'+MC+'}AlternateContent':result.remove(node)
    return result,objects


def make_timeline(run, pages=DEFAULT_PAGES, times=DEFAULT_TIMES, source=None):
    source=Path(source) if source else run/'candidate.pptx'
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    report=json.loads((run/'package-check.json').read_text(encoding='utf-8'))
    data=read(source);ordered=slides(data);assert len(ordered)==manifest['total']
    pres=E.fromstring(data['ppt/presentation.xml']);size=pres.find('p:sldSz',NS);slide_size=tuple(int(size.get(k)) for k in ('cx','cy'))
    rels=E.fromstring(data['ppt/_rels/presentation.xml.rels']);listing=pres.find('p:sldIdLst',NS)
    for child in list(listing):listing.remove(child)
    types=E.fromstring(data['[Content_Types].xml']);CT=E.QName(types).namespace
    inherited=set(report.get('inheritedSlides',[]));frames=[];skipped=[]
    schema_path=Path('C:/Users/10486/.codex/skills/pptx/scripts/office/schemas/ISO-IEC29500-4_2016/pml.xsd')
    schema=E.XMLSchema(E.parse(str(schema_path))) if schema_path.exists() else None
    for number in pages:
        if number<1 or number>len(ordered):raise ValueError('Invalid page: '+str(number))
        if number in inherited:
            skipped.append({'slide':number,'reason':'Actual T3 opening is audited separately'});continue
        owner=ordered[number-1];page=E.fromstring(data[owner])
        specs=[a for a in manifest['animation'] if a['slide']==number]
        stage_numbers=sorted({a['stage'] for a in specs if a['stage']>0})
        effects=click_effects(page,stage_numbers)
        chosen=stage_numbers
        sample_pairs=[(0,0)]+[(stage,time) for stage in chosen for time in times]
        aliases=report.get('aliases',{}).get(str(number),{})
        for stage,time_ms in sample_pairs:
            page_snapshot,objects=snapshot(page,effects,stage,time_ms,slide_size)
            if schema is not None and not schema.validate(page_snapshot):raise ValueError(str(schema.error_log))
            index=len(frames)+1;part='ppt/slides/t4_timeline_'+str(index)+'.xml'
            data[part]=serialize(page_snapshot);data[relpath(part)]=data[relpath(owner)]
            rid='rIdTimeline'+str(index)
            if rid in {rel.get('Id') for rel in rels}:raise ValueError('Timeline relationship already exists')
            E.SubElement(rels,'{'+PKG+'}Relationship',Id=rid,Type=R+'/slide',Target=posixpath.relpath(part,'ppt'))
            E.SubElement(listing,'{'+P+'}sldId',{'id':str(500000+index),'{'+R+'}id':rid})
            E.SubElement(types,'{'+CT+'}Override',PartName='/'+part,ContentType='application/vnd.openxmlformats-officedocument.presentationml.slide+xml')
            origins=[{'target':aliases.get(a['name'],a['name']),'source':aliases.get(a['motion']['fromName'],a['motion']['fromName'])} for a in specs if a['stage']==stage and a.get('motion',{}).get('fromName')]
            frames.append({'index':index,'slide':number,'id':manifest['pages'][number-1]['id'],'stage':stage,'timeMs':time_ms,'part':part,'png':'timeline-'+str(number).zfill(2)+'-'+str(stage)+'-'+str(time_ms).zfill(4)+'.png','origins':origins,'objects':objects})
    if not frames:raise ValueError('No generated pages selected')
    data['ppt/presentation.xml']=serialize(pres);data['ppt/_rels/presentation.xml.rels']=serialize(rels);data['[Content_Types].xml']=serialize(types)
    metadata={'mode':'modeled-click-playback','nativePlaybackTested':False,'source':str(source.resolve()),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'slideSizeEmu':list(slide_size),'timesMs':list(times),'limitations':['Linear position/scale interpolation and fade sampling from OOXML; native easing, frame scheduling and Morph are not reproduced.','Static images can inspect intermediate states but cannot certify native PowerPoint playback.'],'skipped':skipped,'frames':frames}
    return data,metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--pages',type=int,nargs='+',default=list(DEFAULT_PAGES))
    parser.add_argument('--times',type=int,nargs='+',default=list(DEFAULT_TIMES))
    args=parser.parse_args()
    if any(t<0 for t in args.times):parser.error('Sample times must be nonnegative')
    data,metadata=make_timeline(args.run,args.pages,args.times,args.source)
    output=args.run/'timeline-preview.pptx';index=args.run/'timeline-stages.json'
    with ZipFile(output,'w',ZIP_DEFLATED,compresslevel=9) as archive:
        for part,payload in data.items():archive.writestr(part,payload)
    with ZipFile(output) as archive:assert archive.testzip() is None
    index.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps({'preview':str(output.resolve()),'index':str(index.resolve()),'frames':len(metadata['frames']),'mode':metadata['mode'],'nativePlaybackTested':False}))


if __name__=='__main__':main()
