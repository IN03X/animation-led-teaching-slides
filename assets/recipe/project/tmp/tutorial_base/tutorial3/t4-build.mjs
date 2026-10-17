import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {content as fullContent} from './t4-mainline-story.mjs';
import {classroomContent} from './t4-classroom.mjs';
import {generateReceiverDemos} from './t4-receiver-demos.mjs';
import {generateDemos} from './t4-lecture-demos.mjs';
import {prepareIncremental} from './t4-incremental.mjs';
import {prepareFlights,installFlights} from './t4-math-flights.mjs';

const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(dir,'../../..');
const deps='C:/Users/10486/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const req=createRequire(deps+'/node/node_modules/package.json');process.env.RUNTIME_NODE_MODULES=deps+'/node/node_modules';
const {Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')));
const sharp=req('sharp'),python=deps+'/python/python.exe',tex=process.env.TEX_BIN||'E:/texlive/2024/bin/windows';
const classroom=process.env.T4_EDITION!=='full';
const tutorialNumber=Number(process.env.TUTORIAL_NUMBER||4),isT5=tutorialNumber===5;
const run=path.join(dir,'methods-work',process.env.BUILD_ID||(classroom?'t4-classroom-r1':'t4-feedback-r1'));await fs.mkdir(run,{recursive:true});
const hash=b=>createHash('sha256').update(b).digest('hex');
const sourceHashes={};for(const file of ['output/tutorial3/ELEG2310B_Tutorial3.pptx','output/tutorial4/ELEG2310B_Tutorial4.pptx','output/tutorial5/ELEG2310B_Tutorial5.pptx'])sourceHashes[file]=hash(await fs.readFile(path.join(root,file)));
const demos=isT5?await (await import('./t5-demos.mjs')).generateDemos({run,sharp,python}):await generateDemos({run,sharp,python});
if(!isT5)Object.assign(demos,await generateReceiverDemos({run,sharp,python}));
const p=Presentation.create({slideSize:{width:1280,height:720}});
const pages=[],equations=[],animation=[],geometry=[],links=[],gifs=[],formulaGroups=[],lineage=[],mathFlights=[];let s,num=0,stage=0,terms=new Map();
const black='#202020',gray='#9B9B9B',R=String.raw;
const formulaPositions={
 'pm-offset':585,pm:555,fm:536,phase:536,conversion:266,
 'integration-response':260,'integrator-rule':525,envelope:258,'band-map':520,
 'pm-narrow':525,'pm-orders':535,'pm-real-terms':264,'pm-product':522,'pm-lines':532,'pm-sum':264,'pm-wide':535,
 'pm-convolution':520,'pm-convolution-cube':520,'pm-general-sum':264,tone:562,'fm-narrow':300,'fm-narrow-spectrum':264,'fm-wide':535,'fm-series':280,
 'fm-coefficients':270,'fm-weights':270,'pm-fm-spectrum':264,'fm-range':548,carson:548,general:520,'recover-map':538,
 'envelope-recovery':530,normalize:550,'derivative-response':520,pll:550,noise:520,'pm-recovery':270
};
function layoutY(y){
 if(isT5)return y;
 const id=pages[num-1]?.id,base=formulaPositions[id]??585;
 if(id==='pm-offset')return y;
 const offsets={536:-49,585:0,631:52,676:104,678:106,589:4,531:-54,539:-46,639:54};
 return Object.hasOwn(offsets,y)?base+offsets[y]:y;
}
function record(name,x,y,w,h,kind){geometry.push({slide:num,name,x,y,w,h,kind,stage});if(stage)animation.push({slide:num,name,stage});}
function shape(name,kind,x,y,w,h,fill=black,stroke='none',lw=0){y=layoutY(y);record(name,x,y,w,h,kind);return s.shapes.add({name,geometry:kind,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:lw}});}
function text(name,value,x,y,w,h=34,size=27,bold=false,align='left',color=black){const a=shape(name,'textbox',x,y,w,h,'none');a.text=value;a.text.style={typeface:'Times New Roman',fontSize:size,color,bold,italic:false,alignment:align,verticalAlignment:'middle',wrap:'none',autoFit:'none',insets:{left:0,right:0,top:0,bottom:0}};return name;}
function eq(name,value,x,y,w=1140,h=42,size=27,align='left'){y=layoutY(y);equations.push({slide:num,name,tex:value,x,y,w,h,size,align});record(name,x,y,w,h,'formula');return name;}
function comparisonTable(name,values,x,y,w,h,opts={}){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:opts.columnWidths??[200,...Array(values[0].length-1).fill((w-200)/(values[0].length-1))]});
 t.styleOptions={headerRow:false,bandedRows:false};t.borders.assign({fill:'#B0B0B0',width:1});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0&&opts.header!==false?'#EEEEEE':'#FFFFFF';cell.text.style={typeface:'Times New Roman',fontSize:opts.fontSize??26,bold:r===0||c===0,color:black,alignment:'center',verticalAlignment:'middle'};
 }
 const tableSpec={name,x,y,w,h,stage,index:(pages[num-1].nativeTables??[]).length};
 (pages[num-1].nativeTables??=[]).push(tableSpec);record(name,x,y,w,h,'native-table');
 pages[num-1].nativeTable=true;return t;
}
function statement(...args){const name=eq(...args);geometry.at(-1).role='equation';const item=animation.findLast(v=>v.slide===num&&v.name===name);if(item)item.role='equation';return name;}
function line(name,x,y,w,color=black,lw=1.7){return shape(name,'rect',x,y,w,lw,color);}
function curve(name,pts,color=black,lw=2,fill='none'){
 const x=Math.min(...pts.map(a=>a[0])),y=Math.min(...pts.map(a=>a[1])),w=Math.max(...pts.map(a=>a[0]))-x||.01,h=Math.max(...pts.map(a=>a[1]))-y||.01;
 const commands=pts.map(([a,b],i)=>({[i?'lineTo':'moveTo']:{x:a-x,y:b-y}}));if(fill!=='none')commands.push({close:{}});
 record(name,x,y,w,h,'custom');return s.shapes.add({name,geometry:'custom',position:{left:x,top:y,width:w,height:h},fill,line:{fill:color,width:lw},customPaths:[{width:w,height:h,commands}]});
}
function arrow(name,x,y,w,color=black){line(name+'-shaft',x,y,w-9,color);const q=shape(name+'-head','triangle',x+w-11,y-4.5,11,11,color);q.position.rotation=90;}
function reveal(k,draw){const old=stage;stage=k;draw();stage=old;}
function motion(name,from){const a=animation.findLast(v=>v.slide===num&&v.name===name);if(!a)throw Error('No reveal '+name);a.motion={fromName:from,matchSourceShape:true};}
function route(focus='tx'){
 const xs=[100,575,1060],labels=['m(t)','s(t)',R`\widehat m(t)`];
 labels.forEach((v,i)=>{const active=focus==='tx'?i<=1:focus==='band'?i===1:i>=1;eq('route-'+i,(active?'':R`\color[HTML]{C3C3C3}`)+v,xs[i],124,120,60,42,'center');links.push({slide:num,name:'route-'+i,target:['overview','band-map','recover-map'][i]});});
 [230,705].forEach((x,i)=>arrow('route-arrow-'+i,x,145,335,focus===['tx','rx'][i]?black:'#C3C3C3'));
 if(focus==='band'){
  for(let x=636;x<751;x+=14)line('analysis-dash-'+x,x,182,7,'#777777',1.4);
  for(let y=169;y<183;y+=8)shape('analysis-down-'+y,'rect',635,y,1.4,4,'#777777');
  text('analysis-spectrum','Bandwidth of s(t)',765,166,310,31,24,true);
  links.push({slide:num,name:'analysis-spectrum',target:'band-map'});
 }
}
function page(id,title,subtitle,focus,note,opts={}){
 num++;stage=0;terms=new Map();s=p.slides.add();s.background.fill='#FFFFFF';pages.push({id,title,subtitle,focus,note,parent:opts.parent??'overview',purpose:opts.purpose??subtitle});
 text('title',title,70,25,1110,44,33,true);links.push({slide:num,name:'title',target:num>5?'lesson-map':'overview'});
 if(subtitle)text('subtitle',subtitle,70,66,1135,40,31,true);
 if(!opts.bare)route(focus);
 if(!opts.bare){
  text('route-tx-label','Modulation',265,106,230,25,20,false,'center',focus==='tx'?black:'#969696');
  text('route-rx-label','Demodulation',755,106,250,25,20,false,'center',focus==='rx'?black:'#969696');
 }
 s.speakerNotes.textFrame.setText(note);
 return num;
}
function question(v){text('question',v,64,209,1150,38,28,true);}
function row(i,tex,k=0,plain=null,opts={}){
 tex=Array.isArray(tex)?tex.join(''):tex;
 const prose=typeof tex==='string'?tex.match(/^\\text\{([^{}]*)\}$/):null;
 if(plain||prose){reveal(k,()=>{text('equation-'+i,plain||prose[1],64,502+i*44,1150,40,24,false);geometry.at(-1).role='equation';if(k)animation.at(-1).role='equation';});return;}
 const possibleSources=formulaGroups.filter(g=>g.slide===num&&g.stage<k);
 const requested=Object.values(opts.substitute??{});
 const previous=possibleSources.findLast(g=>requested.includes(g.tex))??possibleSources.findLast(g=>requested.some(v=>g.tex.includes(v)))??possibleSources.at(-1),name='equation-'+i;
 const group={slide:num,row:i,stage:k,tex,x:opts.x??64,y:opts.y??502+i*44,w:opts.w??1150,h:40,size:opts.size??26,parts:[name],delayEnd:0};
 reveal(k,()=>statement(name,tex,group.x,group.y,group.w,group.h,group.size));
 if(k&&opts.substitute&&previous&&previous.stage<k){
  lineage.push({slide:num,target:name,source:previous.parts[0],kind:'direct-substitution',stage:k});
 }
 formulaGroups.push(group);
}
function copy(name,from,match=false,via=null){const target=animation.findLast(v=>v.slide===num&&v.name===name);if(!target)throw Error('No staged target '+name);target.motion={fromName:from,matchSourceShape:match,...(via?{via}:{} )};lineage.push({slide:num,target:name,source:from,kind:'copy-object',stage:target.stage});}
function exit(name,k,delay=750,merge=null){
 const spec={slide:num,name,stage:k,moveOnly:true,exitOnly:true,exitAfterMs:delay};
 if(merge){const src=geometry.find(g=>g.slide===num&&g.name===name),dst=geometry.find(g=>g.slide===num&&g.name===merge);spec.motion={from:{dx:0,dy:0},to:{dx:(dst.x+dst.w/2-src.x-src.w/2)/1280,dy:(dst.y+dst.h/2-src.y-src.h/2)/720}};}
 animation.push(spec);
}
function relocate(name,k,dx,dy,delayMs=250){
 animation.push({slide:num,name,stage:k,moveOnly:true,delayMs,motion:{from:{dx:0,dy:0},to:{dx:dx/1280,dy:dy/720}}});
}
function replace(from,name,tex,k,opts={}){
 reveal(k,()=>statement(name,tex,opts.x??64,opts.y??585,opts.w??1150,opts.h??40,opts.size??27,opts.align??'left'));
 if(opts.fixedPrefix||opts.contractLastRhs)Object.assign(equations.at(-1),{incrementalPrefix:opts.fixedPrefix,contractLastRhs:!!opts.contractLastRhs});
 if(opts.splitMatchedRuns)equations.at(-1).splitMatchedRuns=true;
 if(opts.retainMatchedInk)equations.at(-1).retainMatchedInk=true;
 const target=animation.at(-1);target.delayMs=opts.delayMs??30;target.replacementOf=from;
 if(opts.localTransition){target.localTransition=true;target.delayMs=opts.delayMs??0;target.entranceDurationMs=220;}
 if(opts.instantSubstitution){target.instantSubstitution=true;target.instantEntrance=true;target.delayMs=opts.exitAfterMs??0;}
 const spec={slide:num,name:from,stage:k,moveOnly:true,exitOnly:true,instantExit:true,exitAfterMs:opts.exitAfterMs??0,replacedBy:name};
 if(opts.localTransition){spec.instantExit=false;spec.exitAfterMs=target.delayMs;}
 animation.push(spec);
 if(opts.move){target.motion={fromName:from,matchSourceShape:false};target.delayMs=0;}
 if(opts.rhsFrom){
  target.rhsFrom=opts.rhsFrom;
  animation.push({slide:num,name:opts.rhsFrom,stage:k,moveOnly:true,exitOnly:true,instantExit:true,exitAfterMs:0});
 }
 return name;
}
function flyTerm(fromName,fromTex,toName,toTex=fromTex,options={}){
 const direct=new Set(['fm-series','fm-coefficients','fm-weights','pm-fm-spectrum','carson','general','recover-map','envelope-recovery','pm-recovery','noise']).has(pages[num-1].id);
 const entry=animation.findLast(e=>e.slide===num&&e.name===toName&&!e.exitOnly);
 if(!entry)throw Error('Term flight requires a staged destination: '+toName);
 // Local rewrites already animate only changed ink; a second traveling copy obscures it.
 if(direct&&entry.localTransition&&entry.replacementOf===fromName)return;
 mathFlights.push({slide:num,fromName,fromTex,toName,toTex,...options,...(direct?{via:undefined,viaY:undefined}:{})});
 entry.delayMs=700;
 for(const gone of animation.filter(e=>e.slide===num&&e.replacedBy===toName))gone.exitAfterMs=700;
}
function delay(name,ms){const item=animation.findLast(v=>v.slide===num&&v.name===name&&!v.exitOnly);if(!item)throw Error('Missing delayed object '+name);item.delayMs=ms;}
function arrowBetween(name,label,x=405,y=337,w=60,k=1){reveal(k,()=>{
 if(y===353)y=337;
 label=({'Scale + add':'Scale\n+ add','Integrate\nthen cosine':'Integrate\nCosine','Offset + gain':'Offset\n+ gain','Read phase':'Read\nphase','Divide by kp':'Divide\nby kp','Limit\nthen BPF':'Limit\nBPF'})[label]??label;
 arrow(name,x,y,w);
 if(label==='Add carrier\nphase + cosine'){
  eq(name+'-phase',R`+2\pi f_ct`,x-12,y-78,w+24,28,22,'center');
  text(name+'-label','Cosine',x-18,y-43,w+36,29,22,true,'center');
 }else if(label)text(name+'-label',label,x-25,y-(label.includes('\n')?76:60),w+50,label.includes('\n')?57:33,21,true,'center');
});}
function axis(name,x,y,w,lo,hi,ticks=[],domain='f',label='',unitY=y+45){
 arrow(name+'-axis',x,y,w,'#777777');
 const units=domain.includes('mathrm');if(domain)eq(name+'-domain',domain,units?x+w-84:x+w+3,units?unitY:y-28,units?84:28,26,units?18:20,units?'right':'left');
 if(label)eq(name+'-label',label,x,y-106,w,34,26);
 for(let i=0;i<ticks.length;i++){const [v,t]=ticks[i],xx=x+(v-lo)/(hi-lo)*w;shape(name+'-tick-'+i,'rect',xx,y,1,6,'#777777');eq(name+'-ticklabel-'+i,t,xx-55,y+11,110,28,20,'center');}
}
function wave(name,label,fn,col=0,opts={}){
 const firstObject=geometry.length;
 const x=opts.x??[60,480,900][col],w=opts.w??292,y=opts.y??337;
 const offset=opts.baseline>2?opts.baseline:0,scale=offset?(opts.devScale??38):(opts.scale??50);
 let lower=0;
 for(let i=0;i<=900;i++){const t=i/900;lower=Math.max(lower,(offset-fn(t))*scale,opts.reference?(offset-opts.reference(t))*scale:0,opts.env?opts.env(t)*scale:0);}
 const old=stage;stage=0;axis(name,x,y,w,0,1,opts.ticks??[[0,'0'],[1,'1']],opts.units===false?'':opts.domain??R`t\ (\mathrm{ms})`,'',y+Math.max(45,lower+12));stage=old;if(label)eq(name+'-label',label,x,opts.labelY??235,w,32,24);
 if(opts.reference)curve(name+'-reference',Array.from({length:901},(_,i)=>[x+i*w/900,y-(opts.reference(i/900)-offset)*scale]),'#B5B5B5',1.8);
 curve(name+'-wave',Array.from({length:901},(_,i)=>[x+i*w/900,y-(fn(i/900)-offset)*scale]),opts.color??black,2);
 if(opts.env)for(const sign of [-1,1])curve(name+'-envelope-'+sign,Array.from({length:251},(_,i)=>[x+i*w/250,y-sign*opts.env(i/250)*scale]),'#777777',1.3);
 if(opts.baseline!==undefined){const yy=y-(opts.baseline-offset)*scale;line(name+'-baseline',x,yy,w,'#AAAAAA',1);eq(name+'-baselineLabel',opts.baseLabel??'f_c',offset?x+w/2-20:x+8,yy+(offset?-27:5),40,25,20);}
 for(const g of geometry.slice(firstObject))g.signalGroup=name;
 return name+'-wave';
}
function jn(n,b){if(n<0)return (Math.abs(n)%2?-1:1)*jn(-n,b);let v=1;for(let i=1;i<=n;i++)v*=b/(2*i);let sum=v;for(let k=1;k<80;k++){v*=-(b*b/4)/(k*(n+k));sum+=v;if(Math.abs(v)<1e-17)break;}return sum;}
function spectrum(name,beta,col=0,opts={}){
 const firstObject=geometry.length;
 const x=opts.x??[60,480,900][col],w=opts.w??292,y=opts.y??370,lo=opts.lo??-23,hi=opts.hi??23,fc=12.25,N=opts.N??9;
 const old=stage;stage=0;axis(name,x,y,w,lo,hi,opts.ticks??[[-fc,'-f_c'],[0,'0'],[fc,'f_c']],R`f\ (\mathrm{kHz})`,'');stage=old;eq(name+'-label',opts.label??R`|S(f)|`,x,235,w,32,24);
 const pts=[];
 for(let n=-N;n<=N;n++)for(const sign of [-1,1]){
  const f=sign*(fc+n);if(f<lo||f>hi)continue;const a=(opts.coeff?opts.coeff(n):jn(n,beta))/2,xx=x+(f-lo)/(hi-lo)*w;
  curve(name+'-stem-'+n+'-'+sign,[[xx,y],[xx,y-(opts.signed?a:Math.abs(a))*170]],opts.color??black,1.8);pts.push({f,a});
 }
 if(opts.band!==undefined)for(const sign of [-1,1]){const a=x+(sign*fc-opts.band-lo)/(hi-lo)*w,ww=2*opts.band/(hi-lo)*w;shape(name+'-pass-'+sign,'rect',a,y-86,ww,95,'none','#777777',1.3);}
 for(const g of geometry.slice(firstObject))g.signalGroup=name;
 return pts;
}
function band(name,x,y,w,lo,hi,a,b,h=60,fill='#BBBBBB'){
 const xx=x+(a-lo)/(hi-lo)*w,ww=(b-a)/(hi-lo)*w;return shape(name,'rect',xx,y-h,ww,h,fill,black,1.4);
}
function bracket(name,x,y,w,label){line(name,x,y,w);shape(name+'-l','rect',x,y-5,1.3,10);shape(name+'-r','rect',x+w,y-5,1.3,10);eq(name+'-label',label,x-35,y+8,w+70,31,23,'center');}
function block(name,label,x,y,w=180,h=65){shape(name+'-box','rect',x,y,w,h,'none',black,1.5);text(name+'-text',label,x+8,y+8,w-16,h-16,25,true,'center');}
function link(name,target){links.push({slide:num,name,target});}
async function sweep(){
 const frames=60,W=1120,H=235,frameDir=path.join(run,'sweep-frames');await fs.mkdir(frameDir,{recursive:true});
 const signature=hash(Buffer.from(sweep.toString())),cache=path.join(run,'sweep-signature.txt');
 let reusable=false;try{reusable=(await fs.readFile(cache,'utf8'))===signature;await fs.access(path.join(run,'exact-fm-sweep.gif'));await fs.access(path.join(frameDir,'059.png'));}catch{reusable=false;}
 if(!reusable){const old=path.join(dir,'methods-work/t4-t3-style-r1');try{await fs.copyFile(path.join(old,'exact-fm-sweep.gif'),path.join(run,'exact-fm-sweep.gif'));await fs.copyFile(path.join(old,'sweep-frames/059.png'),path.join(frameDir,'059.png'));reusable=true;await fs.writeFile(cache,signature);}catch{}}
 if(!reusable){
 const svgText=(v,x,y,size=23)=>`<text x="${x}" y="${y}" font-family="Times New Roman" font-size="${size}" fill="#202020">${v}</text>`;
 for(let k=0;k<frames;k++){
  const q=Math.min(1,Math.max(0,(k-8)/42)),b=.2+4.8*q,tau=2*Math.PI;
  const wavePath=Array.from({length:1401},(_,i)=>`${i?'L':'M'}${20+i*490/1400},${128-61*Math.cos(tau*12.25*i/1400+b*Math.sin(tau*i/1400))}`).join(' ');
  let body=`<rect width="${W}" height="${H}" fill="white"/>`+svgText('s(t)',20,30,27)+svgText('|S(f)|',620,30,27)+svgText(`beta = ${b.toFixed(2)}     Delta f = ${b.toFixed(2)} kHz`,190,30,25);
  body+='<path d="M20 128H525 M620 185H1095" stroke="#777" stroke-width="1.5" fill="none"/>';
  body+=`<path d="${wavePath}" stroke="#202020" stroke-width="1.7" fill="none"/>`;
  body+=svgText('0',20,215,20)+svgText('1',500,215,20)+svgText('t (ms)',490,235,19);
  for(let n=-10;n<=10;n++)for(const sign of [-1,1]){const f=sign*(12.25+n),x=620+(f+23)/46*475;body+=`<path d="M${x} 185V${185-Math.abs(jn(n,b))*.5*230}" stroke="#202020" stroke-width="1.6"/>`;}
  for(const [f,v] of [[-12.25,'-12.25'],[0,'0'],[12.25,'12.25']])body+=svgText(v,620+(f+23)/46*475-22,214,19);
  body+=svgText('f (kHz)',1040,235,19);
  await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${body}</svg>`)).resize(W*2,H*2).png().toFile(path.join(frameDir,`${String(k).padStart(3,'0')}.png`));
 }
 execFileSync(python,['-X','utf8',path.join(dir,'t4-package.py'),'gif',run],{stdio:'pipe'});
 await fs.writeFile(cache,signature);
 }
 const png=await fs.readFile(path.join(frameDir,'059.png'));
 s.images.add({blob:png,contentType:'image/png',alt:'exact-fm-sweep',position:{left:70,top:240,width:1120,height:235},fit:'contain'});
 gifs.push({slide:num,name:'exact-fm-sweep',file:'exact-fm-sweep.gif',poster:'sweep-frames/059.png'});
}
async function demo(id,opts={}){
 const g=demos[id];if(!g)throw Error('Missing signal demonstration '+id);
 const initialPoster=`demos/${id}/first.png`,png=await fs.readFile(path.join(run,initialPoster));
 s.images.add({blob:png,contentType:'image/png',alt:id,position:{left:opts.x??70,top:opts.y??256,width:opts.w??1120,height:opts.h??235},fit:'contain'});
 gifs.push({slide:num,name:id,...g,initialPoster,playOnClick:true,hiddenUntilPlay:!!opts.continuation});
 geometry.push({slide:num,name:id,x:opts.x??70,y:opts.y??256,w:opts.w??1120,h:opts.h??235,kind:'media',stage:opts.stage??1});
 if(opts.revealOnClick)animation.push({slide:num,name:id,stage:opts.revealOnClick,revealMedia:true,instantEntrance:true});
 animation.push({slide:num,name:id,stage:opts.stage??1,playMedia:true});
}
const authoring={page,question,text,eq,statement,row,reveal,shape,line,curve,arrow,arrowBetween,wave,spectrum,axis,band,bracket,block,comparisonTable,link,motion,copy,exit,relocate,replace,flyTerm,delay,jn,sweep,demo,R};
await (isT5?(await import('./t5-story.mjs')).content:classroom?classroomContent:fullContent)(authoring);
const navigationAliases=authoring.navigationAliases??{normalize:'envelope-recovery'};
for(const v of links){
 if(classroom&&pages[v.slide-1].id==='end'&&v.name==='title')v.target='course';
 v.target=navigationAliases[v.target]??v.target;
}
const incrementalGroups=prepareIncremental(equations,geometry,animation);
for(const gone of [...animation].filter(e=>(classroom||e.slide>=30)&&e.exitOnly&&!e.replacedBy)){
 const formula=equations.find(e=>e.slide===gone.slide&&e.name===gone.name);
 if(formula?.fixedPrefixName&&!animation.some(e=>e.slide===gone.slide&&e.name===formula.fixedPrefixName&&e.exitOnly&&e.stage===gone.stage))
  animation.push({...gone,name:formula.fixedPrefixName});
}
for(const event of animation.filter(v=>v.rhsFrom)){
 const formula=equations.find(e=>e.slide===event.slide&&e.name===event.name);
 delete formula.previousName;
 event.motion={fromName:event.rhsFrom,matchSourceShape:false};
 event.mathRelocation=true;event.instantEntrance=true;event.delayMs=0;
}
// Preserve authored cognitive steps, including an atomic formula replacement.
// Only remove gaps in click numbering; do not force graphs before equations.
for(let slide=1;slide<=pages.length;slide++){
 const objects=animation.filter(v=>v.slide===slide),originalStage=new Map(objects.map(v=>[v,v.stage])),oldStages=[...new Set(objects.map(v=>v.stage))].sort((a,b)=>a-b);
 let click=0;
 for(const oldStage of oldStages){
  const members=objects.filter(v=>originalStage.get(v)===oldStage);
  const batches=[members];
  for(const batch of batches){click++;for(const item of batch){item.stage=click;if(item.exitOnly||(slide>=30&&item.moveOnly))continue;const g=geometry.find(v=>v.slide===slide&&v.name===item.name);if(g)g.stage=click;const group=formulaGroups.find(v=>v.slide===slide&&v.parts.includes(item.name));if(group)group.stage=click;const origin=lineage.find(v=>v.slide===slide&&v.target===item.name);if(origin)origin.stage=click;}}
 }
}
for(let pass=0;pass<animation.length;pass++){
 let changed=false;
 for(const item of animation){if(!item.motion?.fromName)continue;const source=animation.find(v=>v.slide===item.slide&&v.name===item.motion.fromName&&!v.exitOnly);if(source?.stage!==item.stage)continue;const ready=(source.delayMs??0)+(source.motion?700:400)+120;if((item.delayMs??0)<ready){item.delayMs=ready;changed=true;}}
 if(!changed)break;if(pass===animation.length-1)throw Error('Cyclic same-click animation origins');
}
console.log('Prepared',pages.length,'pages');
const flights=prepareFlights(mathFlights,equations);
const assets=[...new Set([...equations.map(e=>e.renderTex??e.tex),...flights.flatMap(f=>[f.sourceTex,f.targetTex])])];
await fs.writeFile(path.join(run,'formulas.tex'),['\\documentclass[10pt,multi=eqn,border=1pt]{standalone}','\\usepackage{amsmath,upgreek,xcolor}','\\SetMathAlphabet{\\mathrm}{bold}{OT1}{cmr}{bx}{n}','\\newenvironment{eqn}{}{}','\\begin{document}','\\boldmath\\bfseries','\\let\\pi\\uppi\\let\\theta\\uptheta\\let\\beta\\upbeta\\let\\tau\\uptau\\let\\phi\\upphi\\let\\delta\\updelta\\let\\Delta\\Updelta',...assets.map(v=>'\\begin{eqn}\\color[HTML]{202020}$\\mathrm{\\textstyle '+v+'}$\\end{eqn}'),'\\end{document}'].join('\n'));
execFileSync(tex+'/latex.exe',['-interaction=nonstopmode','-halt-on-error','formulas.tex'],{cwd:run,stdio:'pipe'});
execFileSync(tex+'/dvisvgm.exe',['--no-fonts','--page=1-','--bbox=min','--output=formula-%p.svg','formulas.dvi'],{cwd:run,stdio:'pipe'});
const cached=new Map();
const fragments=[];
const mathFile=tex=>`formula-${String(assets.indexOf(tex)+1).padStart(String(assets.length).length,'0')}.svg`;
for(const f of flights)for(const side of ['source','target']){
 f[side+'Mask']=f.name+'-'+side+'.svg';
 fragments.push({source:mathFile(f[side+'Tex']),target:f[side+'Mask'],part:'term'});
}
for(const e of equations){
 e.file=`formula-${String(assets.indexOf(e.renderTex??e.tex)+1).padStart(String(assets.length).length,'0')}.svg`;
 if(e.fragment){const target=e.file.replace('.svg','-'+e.fragment+'.svg');fragments.push({source:e.file,target,part:e.fragment});e.file=target;}
}
for(const e of equations.filter(e=>e.previousName&&!e.fixedPart)){
 const previous=equations.find(p=>p.slide===e.slide&&p.name===e.previousName);
 fragments.find(f=>f.target===e.file).previous=previous.file;
 if(e.contractLastRhs)fragments.find(f=>f.target===e.file).contractLastRhs=true;
 if(e.splitMatchedRuns)fragments.find(f=>f.target===e.file).splitMatchedRuns=true;
}
const uniqueFragments=new Map();
for(const f of fragments){const old=uniqueFragments.get(f.target);if(old?.previous&&f.previous&&old.previous!==f.previous)throw Error('Conflicting formula predecessor');uniqueFragments.set(f.target,{...old,...f,...(old?.previous?{previous:old.previous}:{})});}
await fs.writeFile(path.join(run,'math-fragments.json'),JSON.stringify([...uniqueFragments.values()]));
execFileSync(python,['-X','utf8',path.join(dir,'t4-split-math.py'),run],{stdio:'pipe'});
const fragmentMetrics=JSON.parse(await fs.readFile(path.join(run,'math-fragment-metrics.json'),'utf8'));
const deltaParts=JSON.parse(await fs.readFile(path.join(run,'math-delta-parts.json'),'utf8'));
for(const e of [...equations].filter(e=>e.previousName&&!e.fixedPart)){
 const incoming=animation.find(v=>v.slide===e.slide&&v.name===e.name&&!v.exitOnly);
 const outgoing=animation.find(v=>v.slide===e.slide&&v.name===e.name&&v.exitOnly);
 const g=geometry.find(v=>v.slide===e.slide&&v.name===e.name);
 for(const part of deltaParts.filter(p=>p.source===e.file)){
  if(part.part==='change')continue;
  const name=e.name+'-'+part.part,extra={...e,name,file:part.file,fixedPart:true,deltaPart:part.part};
  equations.push(extra);geometry.push({...g,name,fixedPart:true});
  const sourceExit=animation.find(v=>v.slide===e.slide&&v.name===incoming.replacementOf&&v.exitOnly);
  const event={slide:e.slide,name,stage:incoming.stage,delayMs:sourceExit?.exitAfterMs??0,instantEntrance:true,role:'equation'};
  if(part.part.startsWith('moving')&&!incoming.instantSubstitution&&!incoming.localTransition){extra.deltaUnits=part.delta;event.mathDelta=true;}
  animation.push(event);
  if(outgoing)animation.push({...outgoing,name});
 }
 if(!incoming.instantSubstitution&&!incoming.localTransition&&deltaParts.some(p=>p.source===e.file&&p.part.startsWith('moving'))){const gone=animation.find(v=>v.slide===e.slide&&v.name===incoming.replacementOf&&v.exitOnly);incoming.delayMs=Math.max(incoming.delayMs??0,(gone?.exitAfterMs??0)+730);}
 e.file=deltaParts.find(p=>p.source===e.file&&p.part==='change').file;
}
for(const e of equations){
 if(!cached.has(e.file)){const svg=await fs.readFile(path.join(run,e.file)),md=await sharp(svg).metadata(),png=await sharp(svg,{density:288}).resize({width:Math.max(320,Math.round(md.width*16))}).png().toBuffer();const pm=await sharp(png).metadata();cached.set(e.file,{png,width:md.width,height:md.width*pm.height/pm.width});}
}
const familyMetrics=new Map();
for(const e of equations.filter(e=>e.mathFamily)){
 const a=cached.get(e.file),m=fragmentMetrics[e.file],unit=a.width/m.viewBox[2];
 const above=(m.baseline-m.viewBox[1])*unit,below=a.height-above;
 const boxHeight=classroom||(e.slide>=30&&e.slide<=43)?e.h:40;
 const f=familyMetrics.get(e.mathFamily)??{scale:e.size/10,above:0,below:0,boxHeight};
 f.boxHeight=Math.min(f.boxHeight,boxHeight);
 f.scale=Math.min(f.scale,e.size/10,e.w/a.width);f.above=Math.max(f.above,above);f.below=Math.max(f.below,below);
 familyMetrics.set(e.mathFamily,f);e.baselineAbove=above;
}
for(const f of familyMetrics.values())f.scale=Math.min(f.scale,f.boxHeight/(f.above+f.below));
for(const group of formulaGroups){
 const items=group.parts.map(name=>equations.find(e=>e.slide===group.slide&&e.name===name));
 const total=items.reduce((sum,e)=>sum+cached.get(e.file).width,0),height=Math.max(...items.map(e=>cached.get(e.file).height));
 const scale=Math.min(group.size/10,(group.w-4*(items.length-1))/total,group.h/height);let x=group.x;
 for(const e of items){e.x=x;e.w=cached.get(e.file).width*scale;e.size=scale*10;e.align='left';x+=e.w+4;const g=geometry.find(v=>v.slide===e.slide&&v.name===e.name);Object.assign(g,{x:e.x,y:e.y,w:e.w,h:e.h});}
}
for(const e of equations.filter(v=>v.rewriteTarget)){const target=equations.find(v=>v.slide===e.slide&&v.name===e.rewriteTarget);Object.assign(e,{x:target.x,y:target.y,h:target.h});const g=geometry.find(v=>v.slide===e.slide&&v.name===e.name);Object.assign(g,{x:e.x,y:e.y,w:e.w,h:e.h});}
for(const e of equations){
 const a=cached.get(e.file),scale=Math.min(e.size/10,e.w/a.width,e.h/a.height);e.actualWidth=a.width*scale;e.actualHeight=a.height*scale;e.actualLeft=e.x+(e.align==='center'?(e.w-e.actualWidth)/2:e.align==='right'?e.w-e.actualWidth:0);e.actualTop=e.y+(e.h-e.actualHeight)/2;e.actualFontSize=scale*10;
 if(e.mathFamily){const f=familyMetrics.get(e.mathFamily),q=f.scale;e.actualWidth=a.width*q;e.actualHeight=a.height*q;e.actualLeft=e.slide>=30&&e.slide<=43&&e.align==='center'?e.x+(e.w-e.actualWidth)/2:e.x;e.actualTop=e.y+(f.boxHeight-(f.above+f.below)*q)/2+(f.above-e.baselineAbove)*q;e.actualFontSize=q*10;}
 if(e.deltaUnits){const unit=a.width/fragmentMetrics[e.file].viewBox[2],q=familyMetrics.get(e.mathFamily).scale;animation.find(v=>v.slide===e.slide&&v.name===e.name&&!v.exitOnly).motion={from:{dx:e.deltaUnits[0]*unit*q/1280,dy:e.deltaUnits[1]*unit*q/720},to:{dx:0,dy:0}};}
 p.slides.items[e.slide-1].images.add({blob:a.png,contentType:'image/png',alt:e.name,position:{left:e.actualLeft,top:e.actualTop,width:e.actualWidth,height:e.actualHeight},fit:'contain'});
}
await installFlights({flights,equations,animation,geometry,lineage,p,sharp,run});
const manifest={pages,equations,animation,geometry,links,gifs,formulaGroups,lineage,sourceHashes,incrementalGroups,incrementalMath:true,continuityRevision:true,progressiveRevision:true,connectedRevision:true,pmTermsRevision:true,groupedRevision:true,spectrumRecoveryRevision:true,finalFocusRevision:true,redTeamRevision:true,derivationRevision:true,naturalRevision:true,focusRepairRevision:true,feedbackRevision:true,classroomEdition:classroom,navigationAliases,formulaPositions,signalAnchorLayout:true,preservePrefixT4:5,sourceManifestT4:process.env.SOURCE_MANIFEST_T4||'tmp/tutorial_base/tutorial3/methods-work/t4-recap-sole-r1/compact/manifest.json',total:pages.length,destinations:Object.fromEntries(pages.map((v,i)=>[v.id,i+1]))};
if(isT5)Object.assign(manifest,{tutorialNumber:5,topic:'Pulse Modulation',preservePrefixT4:0,takeawayFirst:true,note7Aligned:true,sourceNote:'Fall2026/Note7_PAM.pdf'});
await fs.writeFile(path.join(run,'manifest.json'),JSON.stringify(manifest,null,2));
await(await PresentationFile.exportPptx(p)).save(path.join(run,'donor.pptx'));
console.log(execFileSync(python,['-X','utf8',path.join(dir,'t4-package.py'),'package',run],{encoding:'utf8'}));
const {finalizeRun}=await import('./t4-finalize.mjs');
await finalizeRun({run,root,python});
