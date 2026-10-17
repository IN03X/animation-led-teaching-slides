import fs from 'node:fs/promises';
import path from 'node:path';

export function prepareFlights(flights,equations){
 const marked=(tex,term)=>{
  const at=tex.indexOf(term);
  if(at<0)throw Error('Missing mathematical source term: '+term+' in '+tex);
  return tex.slice(0,at)+'\\color[HTML]{D04E12}'+term+'\\color[HTML]{202020}'+tex.slice(at+term.length);
 };
 return flights.map((f,i)=>{
  const find=name=>equations.find(e=>e.slide===f.slide&&e.name===name&&!e.fixedPart);
  const source=find(f.fromName),target=find(f.toName);
  if(!source||!target)throw Error('Missing term-flight equation');
  return {...f,name:'math-flight-'+i,source,target,
   sourceTex:marked(source.tex,f.fromTex),targetTex:marked(target.tex,f.toTex)};
 });
}

export async function installFlights({flights,equations,animation,geometry,lineage,p,sharp,run}){
 const crop=async(file,e)=>{
  const svg=await fs.readFile(path.join(run,file));
  const {data,info}=await sharp(svg,{density:288}).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  let left=info.width,top=info.height,right=-1,bottom=-1;
  for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]>8){
   left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);
  }
  if(right<left)throw Error('Empty term-flight mask: '+file);
  const w=right-left+1,h=bottom-top+1;
  return {x:e.actualLeft+left/info.width*e.actualWidth,y:e.actualTop+top/info.height*e.actualHeight,
   w:w/info.width*e.actualWidth,h:h/info.height*e.actualHeight,
   image:await sharp(data,{raw:info}).extract({left,top,width:w,height:h}).png().toBuffer(),
   crop:{left,top,width:w,height:h},full:info,svg};
 };
 for(const f of flights){
  const source=await crop(f.sourceMask,f.source),target=await crop(f.targetMask,f.target);
  const incoming=animation.find(e=>e.slide===f.slide&&e.name===f.toName&&!e.exitOnly);
  const start=animation.find(e=>e.slide===f.slide&&e.name===f.fromName&&!e.exitOnly);
  if(start&&start.stage>=incoming.stage)throw Error('Mathematical source must already exist: '+f.fromName);
  const anchor=f.name+'-origin',slide=p.slides.items[f.slide-1];
  slide.shapes.add({name:anchor,geometry:'rect',position:{left:source.x,top:source.y,width:source.w,height:source.h},fill:'none',line:{fill:'none',width:0}});
  geometry.push({slide:f.slide,name:anchor,x:source.x,y:source.y,w:source.w,h:source.h,kind:'rect',stage:0,mathAnchor:true});
  // The visible copy is one complete term, not a collection of flying glyphs.
  slide.images.add({blob:target.image,contentType:'image/png',alt:f.name,position:{left:target.x,top:target.y,width:target.w,height:target.h},fit:'contain'});
  const vb=target.svg.toString().match(/viewBox=['"]([^'"]+)/)[1].split(/\s+/).map(Number),c=target.crop;
  const view=[vb[0]+c.left/target.full.width*vb[2],vb[1]+c.top/target.full.height*vb[3],c.width/target.full.width*vb[2],c.height/target.full.height*vb[3]];
  const file=f.name+'.svg';
  await fs.writeFile(path.join(run,file),target.svg.toString().replace(/viewBox=['"][^'"]+['"]/,`viewBox="${view.join(' ')}"`));
  equations.push({slide:f.slide,name:f.name,tex:f.toTex,file,x:target.x,y:target.y,w:target.w,h:target.h,size:f.target.actualFontSize,
   actualLeft:target.x,actualTop:target.y,actualWidth:target.w,actualHeight:target.h,actualFontSize:f.target.actualFontSize,termFlight:true});
  geometry.push({slide:f.slide,name:f.name,x:target.x,y:target.y,w:target.w,h:target.h,kind:'formula',stage:incoming.stage});
  const via=f.via??(f.viaY==null?null:[[source.x+source.w/2,f.viaY],[target.x+target.w/2,f.viaY]]);
  animation.push({slide:f.slide,name:f.name,stage:incoming.stage,delayMs:0,instantEntrance:true,mathTerm:true,motion:{fromName:anchor,matchSourceShape:true,...(via?{via}:{})}});
  animation.push({slide:f.slide,name:f.name,stage:incoming.stage,moveOnly:true,exitOnly:true,exitAfterMs:700});
  lineage.push({slide:f.slide,target:f.toName,source:f.fromName,term:f.fromTex,destinationTerm:f.toTex,kind:'semantic-term-copy',stage:incoming.stage,flight:f.name});
 }
}
