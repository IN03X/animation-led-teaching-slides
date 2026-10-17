"""Extract fixed and changing TeX ink without changing its typeset coordinates."""
import json
import sys
from copy import deepcopy
from difflib import SequenceMatcher, Match
from pathlib import Path
from lxml import etree as E

run=Path(sys.argv[1])
specs=json.loads((run/'math-fragments.json').read_text(encoding='utf-8'))
ns={'s':'http://www.w3.org/2000/svg'}
metadata={}
for spec in specs:
    original=E.parse(str(run/spec['source'])).getroot()
    uses=original.xpath('s:g//s:use',namespaces=ns)
    assert uses, spec
    box=list(map(float,original.get('viewBox').split()))
    metadata[spec['target']]={'viewBox':box,'baseline':float(uses[0].get('y'))}
    result=deepcopy(original)
    prefix_part=spec['part']=='prefix'
    def filter_ink(node, fill='#000000', definitions=False):
        definitions=definitions or E.QName(node).localname=='defs'
        if definitions:return
        fill=node.get('fill',fill).lower()
        for child in list(node):
            kind=E.QName(child).localname
            if kind in ('use','rect','path','polygon','circle','ellipse','line','polyline'):
                ink=child.get('fill',fill).lower()
                is_prefix=ink=='#13579b'
                keep=ink=='#d04e12' if spec['part']=='term' else is_prefix==prefix_part
                if not keep:node.remove(child)
                else:child.set('fill','#202020' if is_prefix or spec['part']=='term' else ink)
            else:filter_ink(child,fill)
        if node.get('fill') is not None:node.set('fill','#202020')
    filter_ink(result)
    (run/spec['target']).write_bytes(E.tostring(result,xml_declaration=True,encoding='UTF-8'))
parts=[]
def leaves(root):
    return root.xpath('s:g//*[self::s:use or self::s:rect or self::s:path]',namespaces=ns)
def identity(node):
    kind=E.QName(node).localname
    if kind=='use':return kind,node.get('{http://www.w3.org/1999/xlink}href')
    if kind=='rect':return kind,node.get('width'),node.get('height')
    return kind,node.get('d')
for spec in specs:
    if not spec.get('previous'):continue
    current=E.parse(str(run/spec['target'])).getroot()
    previous=E.parse(str(run/spec['previous'])).getroot()
    a,b=leaves(previous),leaves(current)
    base_a=metadata[spec['previous']]['baseline'];base_b=metadata[spec['target']]['baseline']
    stable=set();moving=[]
    if spec.get('contractLastRhs'):
        assert len(a)>=len(b) and [identity(n) for n in a[-len(b):]]==[identity(n) for n in b], ('Last RHS is not the retained expression', spec)
        matches=[Match(len(a)-len(b),0,len(b))]
    else:
        matches=SequenceMatcher(a=[identity(n) for n in a],b=[identity(n) for n in b],autojunk=False).get_matching_blocks()
    for match in matches:
        pairs=[(match.a+i,match.b+i) for i in range(match.size)]
        if not pairs:continue
        shifts=[(float(a[i].get('x','0'))-float(b[j].get('x','0')),
                 float(a[i].get('y','0'))-base_a-float(b[j].get('y','0'))+base_b) for i,j in pairs]
        starts=[0]
        if spec.get('splitMatchedRuns') and not spec.get('contractLastRhs'):
            # Compare against each run's first shift to avoid tolerance drift.
            for index,(x,y) in enumerate(shifts[1:],1):
                dx,dy=shifts[starts[-1]]
                if not (abs(x-dx)<.0001 and abs(y-dy)<.0001):starts.append(index)
        starts.append(len(pairs))
        for start,end in zip(starts,starts[1:]):
            dx,dy=shifts[start]
            if not all(abs(x-dx)<.0001 and abs(y-dy)<.0001 for x,y in shifts[start:end]):
                assert not spec.get('contractLastRhs'), ('Retained RHS cannot move as one unit', spec)
                continue
            ids={j for i,j in pairs[start:end]}
            if abs(dx)<.0001 and abs(dy)<.0001:stable|=ids
            elif len(ids)>=3:moving.append((ids,[dx,dy]))
    moved=set().union(*(ids for ids,delta in moving)) if moving else set()
    groups={'change':set(range(len(b)))-stable-moved,'stable':stable}
    groups.update({'moving'+str(i):ids for i,(ids,delta) in enumerate(moving)})
    for label,keep in groups.items():
        if not keep and label!='change':continue
        output=deepcopy(current)
        for i,node in enumerate(leaves(output)):
            if i not in keep:node.getparent().remove(node)
        target=spec['target'].replace('.svg','-'+label+'.svg')
        (run/target).write_bytes(E.tostring(output,xml_declaration=True,encoding='UTF-8'))
        metadata[target]=metadata[spec['target']]
        parts.append({'source':spec['target'],'file':target,'part':label,'delta':moving[int(label[6:])][1] if label.startswith('moving') else None})
(run/'math-delta-parts.json').write_text(json.dumps(parts),encoding='utf-8')
(run/'math-fragment-metrics.json').write_text(json.dumps(metadata),encoding='utf-8')
