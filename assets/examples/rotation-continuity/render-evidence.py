"""Additional contact sheets and SVG text bounds; no source images are changed."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from lxml import etree as E
ROOT=Path(__file__).resolve().parent
run=ROOT/'tmp/tutorial_base/tutorial3/methods-work'/sys.argv[1]
out=run/'full-frame-review';out.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/times.ttf',20)
def sheet(paths,labels,target,cols=3,thumb=(560,150)):
    w,h=thumb;im=Image.new('RGB',(cols*w,((len(paths)+cols-1)//cols)*(h+28)),'#eeeeee');dr=ImageDraw.Draw(im)
    for i,(p,label) in enumerate(zip(paths,labels)):
        x=(i%cols)*w;y=(i//cols)*(h+28)
        dr.text((x+8,y+3),label,font=font,fill='#202020')
        pic=Image.open(p).convert('RGB');pic.thumbnail((w,h));im.paste(pic,(x,y+28))
    im.save(target)
issues=[];total=0
for d in sorted((run/'demos').iterdir()):
    spec=json.loads((d/'frames.json').read_text())
    files=[d/f for f in spec['frames']]
    for start in range(0,len(files),12):sheet(files[start:start+12],[f'{d.name}: frame {i}' for i in range(start,min(start+12,len(files)))],out/f'{d.name}-{start:02d}.png')
    for f in spec['frames']:
        total+=1;root=E.parse(str(d/f.replace('.png','.svg')));boxes=[]
        for e in root.xpath('//*[local-name()="text"]'):
            t=''.join(e.itertext());size=int(e.get('font-size'));ft=ImageFont.truetype('C:/Windows/Fonts/times.ttf',size)
            x,y=float(e.get('x')),float(e.get('y'));bb=ft.getbbox(t,anchor='ls');box=(x+bb[0],y+bb[1],x+bb[2],y+bb[3])
            if box[0]<0 or box[1]<-1 or box[2]>1120 or box[3]>300:issues.append(dict(demo=d.name,frame=f,kind='out-of-bounds',text=t,box=box))
            for ot,ob in boxes:
                w=min(box[2],ob[2])-max(box[0],ob[0]);h=min(box[3],ob[3])-max(box[1],ob[1])
                if w>1 and h>1:issues.append(dict(demo=d.name,frame=f,kind='text-overlap',texts=[ot,t],overlap=[w,h]))
            boxes.append((t,box))
(out/'svg-text-bounds.json').write_text(json.dumps(dict(frames=total,findings=issues,boundary='Text boxes only; visual review must inspect curves, labels and packaged states.'),indent=2),encoding='utf-8')
print(json.dumps(dict(frames=total,textBoundsFindings=len(issues),output=str(out))))
