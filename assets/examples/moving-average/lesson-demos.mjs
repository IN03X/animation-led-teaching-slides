import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

const W=1120, H=250, B='#202020', G='#9B9B9B', L='#C4C4C4';
const input=[0,2,4,2,0], previous=0;
const sample=n=>n===-1?previous:input[n];
const output=input.map((v,n)=>(v+sample(n-1))/2);
const esc=v=>String(v).replaceAll('&','&amp;').replaceAll('<','&lt;');
const text=(v,x,y,size=24,anchor='start',color=B,bold=false)=>`<text x="${x}" y="${y}" font-family="Times New Roman" font-size="${size}" text-anchor="${anchor}" fill="${color}" font-weight="${bold?'bold':'normal'}">${esc(v)}</text>`;
const line=(x1,y1,x2,y2,color=G,width=1.5,dash='')=>`<path d="M${x1} ${y1}L${x2} ${y2}" fill="none" stroke="${color}" stroke-width="${width}"${dash?` stroke-dasharray="${dash}"`:''}/>`;
const dot=(x,y,r=4.5,color=B,fill=color)=>`<circle cx="${x}" cy="${y}" r="${r}" stroke="${color}" stroke-width="2" fill="${fill}"/>`;
const rect=(x,y,w,h,color=B,dash='')=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="none" stroke="${color}" stroke-width="1.6"${dash?` stroke-dasharray="${dash}"`:''}/>`;
const X=n=>60+(n+1)*70, Y=v=>200-22*v, O=n=>740+n*80;
const clamp=v=>Math.max(0,Math.min(1,v));
const lerp=(a,b,q)=>a+(b-a)*q;

function axes() {
  let b=text('Input x[n]',235,27,27,'middle',B,true)+text('Output y[n]',900,27,27,'middle',B,true);
  b+=line(35,200,450,200)+line(700,200,1085,200);
  b+=text('n',469,237,23)+text('n',1098,237,23);
  for(let n=-1;n<=4;n++)b+=line(X(n),200,X(n),206)+text(n,X(n),237,23,'middle');
  for(let n=0;n<=4;n++)b+=line(O(n),200,O(n),206)+text(n,O(n),237,23,'middle');
  b+=text('value',12,62,22)+text('value',675,62,22);
  b+=line(35,200,35,85)+line(700,200,700,85);
  for(const v of [0,2,4])b+=text(v,27,Y(v)+7,22,'end',G)+text(v,692,Y(v)+7,22,'end',G);
  return b;
}
function inputStems(selected=[]) {
  let b='';
  for(let n=-1;n<=4;n++){
    const v=sample(n),color=selected.includes(n)?B:G;
    b+=line(X(n),200,X(n),Y(v),color,2.3)+dot(X(n),Y(v),3.5,color);
    if(selected.includes(n))b+=dot(X(n),Y(v),7,B,'white')+text(v,X(n),Y(v)-16,24,'middle',B,true);
  }
  return b;
}
function outputStem(n) {
  return line(O(n),200,O(n),Y(output[n]),B,2.5)+dot(O(n),Y(output[n]),4,B)+text(output[n],O(n),Y(output[n])-15,25,'middle',B,true);
}
function pairFrame(q) {
  let b=axes()+inputStems([1,2]);
  b+=rect(X(1)-21,72,112,141,B);
  b+=text('Previous: 2     Current: 4',236,59,23,'middle');
  const travel=clamp(q/.48), collapse=clamp((q-.48)/.42);
  const p1={x:lerp(X(1),O(2)-12,travel),y:Y(lerp(2,3,collapse))};
  const p2={x:lerp(X(2),O(2)+12,travel),y:Y(lerp(4,3,collapse))};
  if(q>0&&q<1){
    const shrink=clamp((q-.90)/.10);
    p1.x=lerp(p1.x,O(2),shrink);p2.x=lerp(p2.x,O(2),shrink);
    b+=dot(p1.x,p1.y,6,B,'white')+dot(p2.x,p2.y,6,B,'white');
  }
  if(q>=.48){
    b+=line(O(2)-60,Y(2),O(2)+60,Y(2),L,1.2,'4 4');
    b+=line(O(2)-60,Y(4),O(2)+60,Y(4),L,1.2,'4 4');
    b+=text(q<1?'Halfway between 2 and 4':'Average = 3',895,59,24,'middle',B,true);
  }
  if(q===1)b+=outputStem(2)+line(O(2)+28,Y(3)-30,O(2)+6,Y(3)-7,B,1.5);
  return {body:b, state:{q,selectedIndices:[1,2],selectedValues:[2,4],travel,collapse,movingHeights:[lerp(2,3,collapse),lerp(4,3,collapse)],outputVisible:q===1,outputIndex:2,outputValue:3}};
}
function movingFrame(i) {
  const segment=Math.min(4,Math.floor(i/8)),local=i===40?1:(i%8)/7;
  const moving=segment>0&&local<.35;
  const n=moving?segment-1:segment;
  const windowN=moving?lerp(segment-1,segment,local/.35):segment;
  const newOutput=local>=.65||i===40;
  const count=segment+(newOutput?1:0);
  let b=axes()+inputStems(moving?[]:[n-1,n]);
  if(segment>0)b+=rect(X(segment-2)-20,72,110,141,L,'4 4');
  b+=rect(X(windowN-1)-20,72,110,141,B);
  b+=text(moving?'Next adjacent pair':`n = ${n}:  (${sample(n)} + ${sample(n-1)}) / 2`,242,59,24,'middle',B,true);
  for(let k=0;k<count;k++)b+=outputStem(k);
  if(newOutput)b+=line(O(segment)+22,Y(output[segment])-30,O(segment)+4,Y(output[segment])-6,B,1.5);
  b+=text(count===5?'All five outputs retained':count?`Outputs through n = ${count-1}`:'No output yet',899,59,24,'middle');
  return {body:b,state:{frame:i,segment,local,moving,selectedIndices:moving?[]:[n-1,n],selectedValues:moving?[]:[sample(n-1),sample(n)],outputs:output.slice(0,count),computedIndices:Array.from({length:count},(_,k)=>k)}};
}

export async function generateDemos({run,sharp}) {
  assert.deepEqual(output,[0,1,3,3,1]);
  const assets={}, numerical={input,previous,indices:[0,1,2,3,4],output,rows:input.map((v,n)=>({n,previous:sample(n-1),current:v,sum:v+sample(n-1),mean:output[n]}))};
  const codeHash=createHash('sha256').update(await fs.readFile(new URL(import.meta.url))).digest('hex');
  const definitions=[{id:'pair-to-output',N:29,render:i=>pairFrame(i/28),ms:160},{id:'moving-window',N:41,render:movingFrame,ms:240}];
  for(const {id,N,render,ms} of definitions){
    const folder=path.join(run,'demos',id);await fs.mkdir(folder,{recursive:true});
    const frames=[],states=[],durations=[];
    for(let i=0;i<N;i++){
      const {body,state}=render(i);
      assert(!/NaN|Infinity/.test(body));
      if(id==='pair-to-output')assert(Math.abs(state.movingHeights.reduce((a,b)=>a+b,0)-6)<1e-12);
      if(id==='moving-window'&&!state.moving)assert.equal(state.selectedValues.reduce((a,b)=>a+b,0)/2,output[state.segment]);
      const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" fill="white"/>${body}</svg>`;
      const frame=`frame-${String(i).padStart(3,'0')}.png`;
      await fs.writeFile(path.join(folder,frame.replace('.png','.svg')),svg);
      await sharp(Buffer.from(svg)).resize(W*2,H*2).flatten({background:'#FFFFFF'}).png({compressionLevel:9}).toFile(path.join(folder,frame));
      frames.push(frame);states.push(state);durations.push(i===0?500:i===N-1?1100:ms);
    }
    await fs.copyFile(path.join(folder,frames[0]),path.join(folder,'first.png'));
    await fs.copyFile(path.join(folder,frames.at(-1)),path.join(folder,'last.png'));
    await fs.writeFile(path.join(folder,'frames.json'),JSON.stringify({frames,durations,states,codeHash},null,2));
    const rel=f=>`demos/${id}/${f}`;
    assets[id]={file:rel('first.png'),first:rel('first.png'),poster:rel('last.png'),width:W,height:H,durationMs:durations.reduce((a,b)=>a+b,0),description:id==='pair-to-output'?'Copy the same heights 2 and 4 to output index 2, then meet at average 3.':'Move the pair from indices (-1,0) through (3,4), retaining every output.',parameters:{input,previous,output,scope:'n=0..4'}};
  }
  await fs.writeFile(path.join(run,'demos-check.json'),JSON.stringify({assets,numerical,nativeFrameBackend:true,logicalSize:[W,H],rasterSize:[W*2,H*2],finiteFrames:true,pairHeightSumInvariant:6,singlePlay:true,nativePlaybackTested:false},null,2));
  return assets;
}
