"""Independent numerical and package assertions for this rotation topic."""
import hashlib,json,math,random,sys,zipfile
from pathlib import Path
from lxml import etree as E
ROOT=Path(__file__).resolve().parent
run=ROOT/'tmp/tutorial_base/tutorial3/methods-work'/sys.argv[1]
checks=[]
def check(label,condition):
    assert condition,label
    checks.append(label)
def close(a,b,tol=1e-10):return max(abs(x-y) for x,y in zip(a,b))<tol
def transform(p,c,t):
    u,v=(p[i]-c[i] for i in range(2));co,si=math.cos(t),math.sin(t)
    return c[0]+u*co-v*si,c[1]+u*si+v*co
def polar(p,c,t):
    u,v=(p[i]-c[i] for i in range(2));r=math.hypot(u,v)
    phi=math.atan2(v,u)
    return c[0]+r*math.cos(phi+t),c[1]+r*math.sin(phi+t)
P=(4,2);C=(2,1)
check('Requested CCW 90 degree result is (1,3)',close(transform(P,C,math.pi/2),(1,3)))
exact=(1.5+math.sqrt(3),2+math.sqrt(3)/2)
check('Returned rule gives exact 30 degree answer',close(transform(P,C,math.pi/6),exact))
check('Quarter-turn has positive signed area about C',(P[0]-C[0])*(3-C[1])-(P[1]-C[1])*(1-C[0])>0)
rng=random.Random(20261018);errors=[]
for _ in range(2000):
    p=[rng.uniform(-20,20) for _ in range(2)];c=[rng.uniform(-10,10) for _ in range(2)];t=rng.uniform(-8*math.pi,8*math.pi)
    a=transform(p,c,t);b=polar(p,c,t);errors.append(max(abs(x-y) for x,y in zip(a,b)))
    assert close(a,b)
    assert abs(math.dist(a,c)-math.dist(p,c))<1e-10
    assert close(transform(a,c,-t),p)
check('2000 signed-angle/signed-coordinate cases agree with independent polar geometry',max(errors)<1e-10)
check('Centre remains fixed for arbitrary angles',all(close(transform(C,C,t),C) for t in [0,.4,-3,20]))
check('Zero rotation preserves the input',close(transform(P,C,0),P))
check('Clockwise 90 degrees gives (3,-1)',close(transform(P,C,-math.pi/2),(3,-1)))
check('Full revolution preserves the input',close(transform(P,C,2*math.pi),P))
check('Composition agrees with successive turns',close(transform(transform(P,C,.31),C,-.85),transform(P,C,-.54)))
frame_count=0
for d in sorted((run/'demos').iterdir()):
    spec=json.loads((d/'frames.json').read_text())
    assert len(spec['frames'])==len(spec['durations'])==len(spec['states'])==(85 if d.name=='process' else 29)
    for filename,s in zip(spec['frames'],spec['states']):
        frame_count+=1
        assert (d/filename).is_file()
        q=s['q'];id=s['id']
        if id=='process':
            assert abs(math.dist(s['p'],s['c'])-math.sqrt(5))<1e-10
            if s['phase']==1:assert close(s['p'],transform((2,1),(0,0),s['local']*math.pi/2))
        elif id=='focus':assert close(s['sourceQ'],(2,1))
        elif id=='return':assert close(s['p'],transform((2,1),(0,0),35*math.pi/180) if q==0 else [s['c'][i]+transform((2,1),(0,0),35*math.pi/180)[i] for i in range(2)])
        elif id=='subtract':assert close(s['displacement'],(2,1)) and close(s['c'],(2-2*q,1-q))
        elif id=='quarter':
            expected=transform((2,1),(0,0),q*math.pi/2)
            assert close(s['p'],expected)
            assert close(s['p'],[s['h'][i]+s['v'][i] for i in range(2)])
            assert abs(sum(s['h'][i]*s['v'][i] for i in range(2)))<1e-10
        elif id=='add':assert close(s['p'],(-1+2*q,2+q))
        elif id=='horizontal':assert close(s['h'],transform((2,0),(0,0),s['t']))
        elif id=='vertical':
            assert abs(math.hypot(*s['v'])-1)<1e-10
            if q>=.5:assert close(s['p'],transform((2,1),(0,0),s['theta']))
        elif id=='thirty':assert close(s['p'],transform(P,C,q*math.pi/6))
    assert hashlib.sha256((d/spec['frames'][0]).read_bytes()).digest()==hashlib.sha256((d/'first.png').read_bytes()).digest()
    assert hashlib.sha256((d/spec['frames'][-1]).read_bytes()).digest()==hashlib.sha256((d/'last.png').read_bytes()).digest()
check('All 317 actual animation frame states and poster identities verified',frame_count==317)
for f in (run/'demos/thirty').glob('frame-*.svg'):
    t=E.parse(str(f)).xpath('//*[local-name()="text" and text()="C=(2,1)"]')
    assert len(t)==1 and float(t[0].get('x'))==588 and float(t[0].get('y'))==207
check('30-degree centre label stays beside the actual C, clear of the y-axis in every frame',True)
m=json.loads((run/'manifest.json').read_text());p=json.loads((run/'package-check.json').read_text())
check('11 authored generic-topic pages; zero inherited course slides',m['total']==11 and m['genericContent'] and not p['inheritedSlides'])
check('All links target meaningful new-topic IDs',all(v['target'] in m['destinations'] for v in m['links']))
check('Nine demonstrations all click-start',len(m['gifs'])==9 and all(v['playOnClick'] for v in m['gifs']))
check('Focus endpoint is pixel-identical to next detail entry',(run/'demos/focus/last.png').read_bytes()==(run/'demos/horizontal/first.png').read_bytes())
check('Detail endpoint is pixel-identical to return entry',(run/'demos/vertical/last.png').read_bytes()==(run/'demos/return/first.png').read_bytes())
placements=[(v['x'],v['y'],v['w'],v['h']) for v in m['geometry'] if v['kind']=='media' and v['slide'] in [6,7,8,9]]
check('Focus/detail/return media preserve exact on-slide position and scale',placements==[(70,300,1120,260)]*4)
contracts=json.loads((ROOT/'page-contract.json').read_text())['pages']
for i,page in enumerate(contracts,1):assert len(page['clicks'])-1==p['clicks'][str(i)]
check('All 11 page contracts match actual packaged click-group counts',True)
for i in [9,10,11]:
    tex=' '.join(v['tex'] for v in m['equations'] if v['slide']==i)
    assert '\\cos' in tex and '\\sin' in tex
check('Returned rule remains visibly present at return, use and takeaway',True)
with zipfile.ZipFile(run/'candidate.pptx') as z:
    text=' '.join(E.fromstring(z.read(n)).xpath('//*[local-name()="t"]/text()')[0:] and ' '.join(E.fromstring(z.read(n)).xpath('//*[local-name()="t"]/text()')) or '' for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml'))
    check('No authored visible course identity',not any(x in text for x in ['ELEG2310','Runbang','TIAN','PAM','Tutorial 5']))
    media=sum(1 for n in z.namelist() if n.startswith('ppt/media/') and n.endswith('.png'))
report=dict(passed=True,checks=checks,assertionGroups=len(checks),randomCases=2000,maximumPolarDisagreement=max(errors),verifiedNumericalFrames=frame_count,pngMedia=media,scope='New rotation topic only; not old golden replay',nativePlaybackTested=False)
(run/'topic-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
