import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const deps='C:/Users/10486/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const req=createRequire(deps+'/node/node_modules/package.json');
process.env.RUNTIME_NODE_MODULES=deps+'/node/node_modules';
const {PresentationFile,FileBlob}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')));
const sharp=req('sharp'),run=path.resolve(process.argv[2]);
const m=JSON.parse(await fs.readFile(path.join(run,'manifest.json'),'utf8'));
const pack=JSON.parse(await fs.readFile(path.join(run,'package-check.json'),'utf8'));
const sha=buffer=>createHash('sha256').update(buffer).digest('hex');
assert.equal(m.total,23);assert.equal(m.tutorialNumber,5);
assert.equal(m.pages.length,23);assert.equal(new Set(m.pages.map(p=>p.id)).size,23);
assert.equal(pack.template.slides.filter(p=>p.entireSlideCopied).length,3);
assert.equal(pack.template.slides.filter(p=>p.coverOrEndCopied).length,2);
assert.equal(pack.clickMedia.backend,'native-png-frames');
for(const link of m.links)assert(m.destinations[link.target],`Broken navigation: ${link.target}`);
for(const event of m.animation)assert(m.geometry.some(g=>g.slide===event.slide&&g.name===event.name),`Missing animation: ${event.name}`);
for(const item of m.geometry){
 assert(Number.isFinite(item.x)&&Number.isFinite(item.y)&&item.w>=0&&item.h>=0);
 assert(item.x>=-1&&item.y>=-1&&item.x+item.w<=1281&&item.y+item.h<=721,`Out of slide: ${item.slide}:${item.name}`);
}
for(const e of m.equations){
 assert(!e.tex.includes('p(t)'),`Old pulse symbol on ${e.slide}`);
 assert(e.actualFontSize>=20,`Small mathematical content: ${e.slide}:${e.name}:${e.actualFontSize}`);
}
for(const g of m.gifs){
 assert(g.playOnClick);
 assert.equal(!!g.hiddenUntilPlay,g.name==='sampling-rate-up');
 const frames=JSON.parse(await fs.readFile(path.join(run,path.dirname(g.file),'frames.json'),'utf8'));
 assert(frames.frames.length>=25&&frames.durations.length===frames.frames.length);
 assert.equal(g.durationMs,frames.durations.reduce((a,b)=>a+b,0));
}
const expected={
 'pam-derivation':['s(t)=(m_\\delta*h)(t)','\\delta(\\tau-nT_s)','h(t-nT_s)'],
 'sampling-coefficients':['a_k=','\\delta(t)','\\frac1{T_s}'],
 'sampling-spectrum':['\\mathcal F','M(f-kf_s)'],
 'pulse-transform':['\\int_0^T','e^{-j\\pi fT}','\\operatorname{sinc}(fT)'],
 'read-samples':['s(nT_s+T/2)=m(nT_s)'],
 'lpf':['G(f)=T_s'],
 'reconstruction-kernel':['\\int_{-f_s/2}^{f_s/2}','f_s\\operatorname{sinc}(f_st)'],
 'interpolation-derivation':['\\delta(t-\\tau-nT_s)','h_{\\mathrm{LP}}(t-nT_s)','f_s(t-nT_s)'],
 'tdm-send':['T<T_s/3'],
 'tdm-receive':['T<T_s/3']
};
for(const [id,terms] of Object.entries(expected)){
 const tex=m.equations.filter(e=>e.slide===m.destinations[id]).map(e=>e.tex).join('\n');
 for(const term of terms)assert(tex.includes(term),`Missing derivation step: ${id}:${term}`);
}
const stages=JSON.parse(await fs.readFile(path.join(run,'stages.json'),'utf8'));
const deck=await PresentationFile.importPptx(await FileBlob.load(path.join(run,'stage-preview.pptx')));
assert.equal(deck.slides.items.length,stages.length);
for(let slide=5;slide<=22;slide++){
 const max=pack.clicks[String(slide)];
 for(let stage=0;stage<=max;stage++)assert.equal(stages.filter(s=>s.slide===slide&&s.stage===stage).length,1);
}
const stageDir=path.join(run,'review-stages');await fs.mkdir(stageDir,{recursive:true});
for(const [i,item] of stages.entries()){
 const b=Buffer.from(await (await deck.export({slide:deck.slides.items[i],format:'png',scale:1})).arrayBuffer());
 const stats=await sharp(b).stats();assert(stats.channels.some(c=>c.stdev>5));
 await fs.writeFile(path.join(stageDir,`slide-${String(item.slide).padStart(2,'0')}-stage-${item.stage}.png`),b);
}
const montage=async(files,target,columns=4)=>{
 const width=400,height=250,rows=Math.ceil(files.length/columns),items=[];
 for(const [i,file] of files.entries()){
  const label=`<svg width="400" height="25"><rect width="400" height="25" fill="#EEEEEE"/><text x="8" y="19" font-family="Times New Roman" font-size="19">${file.label}</text></svg>`;
  items.push({input:Buffer.from(label),left:(i%columns)*width,top:Math.floor(i/columns)*height});
  items.push({input:await sharp(file.path).resize(400,225).png().toBuffer(),left:(i%columns)*width,top:Math.floor(i/columns)*height+25});
 }
 await sharp({create:{width:columns*width,height:rows*height,channels:3,background:'#DDDDDD'}}).composite(items).png().toFile(target);
};
await montage(m.pages.map((p,i)=>({path:path.join(run,`slide-${String(i+1).padStart(3,'0')}.png`),label:`${i+1}: ${p.id}`})),path.join(run,'overview.png'));
for(const slide of [7,8,9,11,15,16]){
 const frames=stages.filter(s=>s.slide===slide);
 await montage(frames.map(s=>({path:path.join(stageDir,`slide-${String(slide).padStart(2,'0')}-stage-${s.stage}.png`),label:`${slide}, click ${s.stage}`})),path.join(run,`sequence-${slide}.png`),2);
}
let timelineFrames=0;
try{
 const timing=JSON.parse(await fs.readFile(path.join(run,'timeline-stages.json'),'utf8'));
 assert.equal(timing.sourceSha256,sha(await fs.readFile(path.join(run,'candidate.pptx'))));
 const modeled=await PresentationFile.importPptx(await FileBlob.load(path.join(run,'timeline-preview.pptx')));
 assert.equal(modeled.slides.items.length,timing.frames.length);
 for(const [i,frame] of timing.frames.entries()){
  const b=Buffer.from(await (await modeled.export({slide:modeled.slides.items[i],format:'png',scale:1})).arrayBuffer());
  await fs.writeFile(path.join(stageDir,frame.png),b);timelineFrames++;
 }
 for(const slide of [7,16]){
  const selected=timing.frames.filter(f=>f.slide===slide&&f.stage===3);
  await montage(selected.map(f=>({path:path.join(stageDir,f.png),label:`Slide ${slide}, ${f.timeMs} ms`})),path.join(run,`motion-${slide}.png`),2);
 }
}catch(error){if(error.code!=='ENOENT')throw error;}
const report={candidateHash:sha(await fs.readFile(path.join(run,'candidate.pptx'))),pages:23,
 nativeClickAnimations:m.gifs.length,clickEndpoints:stages.length,totalClicks:Object.values(pack.clicks).reduce((a,b)=>a+b,0),
 note7DerivationStepsVerified:true,templateCopiesVerified:true,navigationTargetsVerified:true,nonblankEndpoints:true,
 modeledMotionFrames:timelineFrames,nativePlaybackTested:false,classroomTimingTested:false};
await fs.writeFile(path.join(run,'review-checks.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report));
