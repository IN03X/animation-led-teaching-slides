import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';

const req=createRequire(process.env.RUNTIME_NODE_MODULES+'/package.json');
const sharp=req('sharp');
const {PresentationFile,FileBlob}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')));
const run=path.resolve(process.argv[2]);
const read=async name=>JSON.parse(await fs.readFile(path.join(run,name),'utf8'));
const manifest=await read('manifest.json'),pack=await read('package-check.json');
const sha=b=>createHash('sha256').update(b).digest('hex');
assert.equal(manifest.total,manifest.pages.length);
assert.equal(new Set(manifest.pages.map(p=>p.id)).size,manifest.total);
for(const link of manifest.links)assert(manifest.destinations[link.target],`Broken link ${link.slide}:${link.name}->${link.target}`);
for(const item of manifest.geometry){
 assert([item.x,item.y,item.w,item.h].every(Number.isFinite),'Nonfinite geometry');
 assert(item.w>=0&&item.h>=0&&item.x>=-1&&item.y>=-1&&item.x+item.w<=1281&&item.y+item.h<=721,`Out of bounds ${item.slide}:${item.name}`);
}
const smallMath=manifest.equations.filter(e=>e.actualFontSize<20).map(e=>({slide:e.slide,name:e.name,size:e.actualFontSize}));
assert.equal(smallMath.length,0,'Unreadable small math: '+JSON.stringify(smallMath));
for(const event of manifest.animation)assert(manifest.geometry.some(g=>g.slide===event.slide&&g.name===event.name),`Missing animated object ${event.name}`);
for(const media of manifest.gifs){
 assert(media.playOnClick,'Demonstration must be click-start');
 const frames=await read(path.join(path.dirname(media.file),'frames.json'));
 assert.equal(frames.frames.length,frames.durations.length);
 assert.equal(frames.durations.reduce((a,b)=>a+b,0),media.durationMs);
}
const out=path.join(run,'quality-review');await fs.mkdir(out,{recursive:true});
async function renderDeck(file,entries,name){
 const deck=await PresentationFile.importPptx(await FileBlob.load(path.join(run,file)));
 assert.equal(deck.slides.items.length,entries.length);
 const outputs=[];
 for(const [i,entry] of entries.entries()){
  const png=Buffer.from(await (await deck.export({slide:deck.slides.items[i],format:'png',scale:1})).arrayBuffer());
  const stats=await sharp(png).stats();assert(stats.channels.some(c=>c.stdev>5),`Blank ${file}:${i+1}`);
  const target=path.join(out,`${name}-${String(i+1).padStart(3,'0')}.png`);await fs.writeFile(target,png);
  outputs.push({path:target,label:`${entry.slide??i+1} / ${entry.stage??'final'}${entry.timeMs===undefined?'':' / '+entry.timeMs+'ms'}`});
 }
 return outputs;
}
async function montage(items,file,columns=3){
 if(!items.length)return;
 const width=400,height=250,inputs=[];
 for(const [i,item] of items.entries()){
  const left=i%columns*width,top=Math.floor(i/columns)*height;
  const safe=item.label.replaceAll('&','&amp;').replaceAll('<','&lt;');
  inputs.push({input:Buffer.from(`<svg width="400" height="25"><rect width="400" height="25" fill="#eee"/><text x="8" y="19" font-family="Times New Roman" font-size="18">${safe}</text></svg>`),left,top});
  inputs.push({input:await sharp(item.path).resize(400,225,{fit:'contain',background:'white'}).png().toBuffer(),left,top:top+25});
 }
 await sharp({create:{width:columns*width,height:Math.ceil(items.length/columns)*height,channels:3,background:'#ddd'}}).composite(inputs).png().toFile(file);
}
const finals=await renderDeck('static-preview.pptx',manifest.pages,'final');
await montage(finals,path.join(out,'overview.png'));
const stages=await read('stages.json'),endpoints=await renderDeck('stage-preview.pptx',stages,'click');
for(let i=1;i<=manifest.total;i++){
 const items=endpoints.filter((_,n)=>stages[n].slide===i);
 await montage(items,path.join(out,`sequence-${i}.png`),2);
}
const timeline=await read('timeline-stages.json');
assert.equal(timeline.sourceSha256,sha(await fs.readFile(path.join(run,'candidate.pptx'))));
const motions=await renderDeck('timeline-preview.pptx',timeline.frames,'motion');
for(const i of [...new Set(timeline.frames.map(f=>f.slide))]){
 await montage(motions.filter((_,n)=>timeline.frames[n].slide===i),path.join(out,`motion-${i}.png`),3);
}
for(const g of manifest.gifs){
 const directory=path.dirname(g.file),frames=await read(path.join(directory,'frames.json'));
 const chosen=[0,Math.floor(frames.frames.length/2),frames.frames.length-1];
 await montage(chosen.map(i=>({path:path.join(run,directory,frames.frames[i]),label:`${g.name} frame ${i}`})),path.join(out,`demo-${g.slide}-${g.name}.png`),3);
}
const result={candidateHash:sha(await fs.readFile(path.join(run,'candidate.pptx'))),slides:manifest.total,
 finalRenders:finals.length,clickEndpoints:endpoints.length,modeledMotionFrames:motions.length,nativeClickAnimations:manifest.gifs.length,
 structuralChecks:true,nonblankEndpoints:true,formulaMinimumLogicalSize:20,
 humanReviewRequired:['source-specific math','mainline continuity and each new symbol','visual hierarchy','all endpoints and relevant intermediates','local pointer targets and plotted axes','navigation meaning'],
 teachingApproved:false,nativePlaybackTested:false,classroomTimingTested:false};
await fs.writeFile(path.join(run,'quality-review.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result));
