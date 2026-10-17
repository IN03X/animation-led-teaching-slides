import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';

const W=1120,H=250,B='#202020',G='#999999',L='#CCCCCC',tau=2*Math.PI;
const clamp=x=>Math.max(0,Math.min(1,x));
const sinc=x=>Math.abs(x)<1e-10?1:Math.sin(Math.PI*x)/(Math.PI*x);
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const typeset=s=>esc(s).replaceAll('m delta','m<tspan baseline-shift="sub" font-size="75%">&#x3B4;</tspan>')
 .replaceAll('M delta','M<tspan baseline-shift="sub" font-size="75%">&#x3B4;</tspan>')
 .replaceAll('H LP','H<tspan baseline-shift="sub" font-size="75%">LP</tspan>')
 .replaceAll('h LP','h<tspan baseline-shift="sub" font-size="75%">LP</tspan>')
 .replace(/m([123])/g,'m<tspan baseline-shift="sub" font-size="75%">$1</tspan>')
 .replaceAll('Ts','T<tspan baseline-shift="sub" font-size="75%">s</tspan>')
 .replaceAll('fs','f<tspan baseline-shift="sub" font-size="75%">s</tspan>');
const text=(s,x,y,size=25,anchor='start',color=B)=>`<text x="${x}" y="${y}" font-family="Times New Roman" font-size="${size}" text-anchor="${anchor}" fill="${color}">${typeset(s)}</text>`;
const line=(x,y,u,v,color=G,width=1.4,dash='')=>`<path d="M${x} ${y}L${u} ${v}" fill="none" stroke="${color}" stroke-width="${width}"${dash?` stroke-dasharray="${dash}"`:''}/>`;
const curve=(points,color=B,width=2,dash='')=>`<path d="${points.map(([x,y],i)=>`${i?'L':'M'}${x.toFixed(3)} ${y.toFixed(3)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linejoin="round"${dash?` stroke-dasharray="${dash}"`:''}/>`;
function pointer(x,y,label,where='above',offsetX=0,labelHeight=null){
 const d=where==='above'?-1:1;
 const labelY=labelHeight??(d<0?Math.max(61,y-48):Math.min(222,y+58));
 const margin=label.length*6+8,labelX=Math.max(margin,Math.min(W-margin,x+offsetX));
 return line(labelX,labelY+(d<0?7:-23),x,y+7*d,B,1.8)+curve([[x-5,y+14*d],[x,y+7*d],[x+5,y+14*d]],B,1.8)+text(label,labelX,labelY,24,'middle');
}
function plot(i,count,title,{lo=0,hi=4,ylo=-1.25,yhi=1.25,xticks=[[0,'0'],[1,'1'],[2,'2'],[3,'3'],[4,'4']],unit='t / Ts',yticks=true}={}){
 const slot=W/count,x0=i*slot+45,x1=(i+1)*slot-26,y0=74,y1=190;
 const X=x=>x0+(x-lo)/(hi-lo)*(x1-x0),Y=y=>y1-(y-ylo)/(yhi-ylo)*(y1-y0);
 let body=text(title,i*slot+slot/2,27,27,'middle')+line(x0,Y(0),x1,Y(0))+line(x0,y0,x0,y1);
 for(const [value,label] of xticks)body+=line(X(value),y1,X(value),y1+4)+text(label,X(value),216,23,'middle');
 if(yticks)for(const v of [-1,1])if(v>=ylo&&v<=yhi)body+=text(v,x0-8,Y(v)+6,22,'end');
 body+=text(unit,(x0+x1)/2,246,23,'middle');
 return {body,X,Y,x0,x1,y0,y1,lo,hi};
}
function trace(p,fn,q=1,color=B,width=2){
 const length=Math.max(2,Math.ceil(500*q));
 return curve(Array.from({length},(_,i)=>{
  const x=p.lo+(p.hi-p.lo)*q*i/(length-1);return [p.X(x),p.Y(fn(x))];
 }),color,width);
}
function stem(p,x,y,color=B,width=2.2){
 return line(p.X(x),p.Y(0),p.X(x),p.Y(y),color,width)+curve([[p.X(x)-3,p.Y(y)+(y<0?-6:6)],[p.X(x),p.Y(y)],[p.X(x)+3,p.Y(y)+(y<0?-6:6)]],color,width);
}
function pulse(p,x,y,width=.27,color=B){return curve([[p.X(x),p.Y(0)],[p.X(x),p.Y(y)],[p.X(x+width),p.Y(y)],[p.X(x+width),p.Y(0)]],color,2.2);}
const msg=x=>.78*Math.cos(tau*.22*x)+.15*Math.sin(tau*.43*x);
const tri=x=>Math.max(0,1-Math.abs(x));
function spectrum(p,fs=3,count=2,q=1,product=false,T=.25){
 let body='';
 for(let k=-count;k<=count;k++){
  const center=k*fs;
  if(center+1<p.lo||center-1>p.hi)continue;
  const col=k===0?B:G;
  body+=curve(Array.from({length:101},(_,i)=>{const f=center-1+2*i/100;return[p.X(f),p.Y(tri(f-center)*(product?Math.abs(sinc(f*T)):1)*q)];}),col,k===0?2.7:2);
 }
 return body;
}
const spec={lo:-7,hi:7,ylo:-.18,yhi:1.25,xticks:[[-6,'-2fs'],[-3,'-fs'],[0,'0'],[3,'fs'],[6,'2fs']],unit:'f',yticks:false};
const states=(N=28)=>Array.from({length:N},(_,i)=>i/(N-1));
function pulseTypes(q){
 let b='';const amp=.35+.6*q;
 for(let i=0;i<3;i++){
  const p=plot(i,3,['PAM: height','PDM: width','PPM: position'][i],{lo:0,hi:3,xticks:[[0,'0'],[1,'Ts'],[2,'2Ts']],unit:'t',yticks:false});b+=p.body;
  for(let n=0;n<3;n++){
   const active=n===1,q1=active?q:0;
   const x=n+.08+(i===2?.43*q1:0),width=i===1?.15+.5*q1:.25;
   if(active)b+=curve([[p.X(n+.08),p.Y(0)],[p.X(n+.08),p.Y(i===0?.35:.85)],[p.X(n+.08+(i===1?.15:.25)),p.Y(i===0?.35:.85)],[p.X(n+.08+(i===1?.15:.25)),p.Y(0)]],L,1.5,'4 4');
   b+=pulse(p,x,i===0?(active?amp:.35):.85,width);
   if(n===1)b+=pointer(p.X(x+width/2),p.Y(i===0?amp:.85),'Changed '+['height','width','position'][i]);
  }
 }
 return b;
}
function formation(q){
 const ps=[plot(0,3,'m(t)'),plot(1,3,'m delta(t)'),plot(2,3,'s(t)')];
 let b=ps.map(p=>p.body).join('')+trace(ps[0],msg,1,G,1.7);
 const progress=q*5;
 for(let n=0;n<=4;n++){
  const a=clamp(progress-n);if(a===0)continue;
  const y=msg(n);b+=stem(ps[1],n,y)+pulse(ps[2],n,y,.27);
  b+=`<circle cx="${ps[0].X(n)}" cy="${ps[0].Y(y)}" r="4" fill="${B}"/>`;
 }
 const n=Math.min(4,Math.floor(progress));
 if(q>0)b+=pointer(ps[0].X(n),ps[0].Y(msg(n)),'Sample '+n)+pointer(ps[2].X(n+.13),ps[2].Y(msg(n)),'Same height');
 return b;
}
function replicas(q){
 const p=plot(0,1,'M delta(f)',spec);let b=p.body+spectrum(p,3,0);
 for(const k of [-2,-1,1,2]){
  const a=clamp(q*2-(Math.abs(k)-1));if(a===0)continue;
  const center=k*3*a;
  b+=curve(Array.from({length:101},(_,j)=>{const f=center-1+2*j/100;return[p.X(f),p.Y(tri(f-center))];}),k===1?B:G,k===1?2.7:2);
 }
 if(q>0)b+=pointer(p.X(3),p.Y(1),'Copy at fs');
 return b;
}
function rate(q){
 const fs=q<.38?3-1.5*q/.38:q<.65?1.5:1.5+1.5*(q-.65)/.35;
 const p=plot(0,1,`Copies of M(f); fs / W = ${fs.toFixed(2)}`,{...spec,xticks:[[-6,'-6W'],[-3,'-3W'],[-1,'-W'],[0,'0'],[1,'W'],[3,'3W'],[6,'6W']]});
 let b=p.body+spectrum(p,fs,4);
 for(const edge of [-1,1])b+=line(p.X(edge),p.Y(0),p.X(edge),p.Y(1.1),L,1.2,'4 4');
 if(fs>=2.7){
  const y=p.Y(0)+10,x1=p.X(1),x2=p.X(fs-1);
  b+=line(x1,y,x2,y,B,1.3)+line(x1,y-5,x1,y+5,B,1.3)+line(x2,y-5,x2,y+5,B,1.3);
  b+=text('fs-W',x2,216,23,'middle');
 }
 if(fs<2){
  const center=(fs-1+1)/2;
  b+=pointer(p.X(center),p.Y(.55),'Overlap');
 }else b+=pointer(p.X((1+fs-1)/2),p.Y(.2),'Separated');
 return b;
}
function pulseResponse(q){
 const a=plot(0,2,'h(t)',{lo:-.3,hi:1,ylo:-.15,yhi:1.25,xticks:[[0,'0'],[.5,'T']],unit:'t',yticks:false});
 const b=plot(1,2,'|H(f)| / T',{lo:-3,hi:3,ylo:-.15,yhi:1.25,xticks:[[-1,'-1/T'],[0,'0'],[1,'1/T']],unit:'f',yticks:false});
 let body=a.body+b.body+pulse(a,0,1,.5)+trace(b,x=>Math.abs(sinc(x)),q);
 if(q===1)body+=pointer(b.X(1),b.Y(0),'First zero','above',65,64);
 return body;
}
function pamSpectrum(q){
 const opts={...spec,lo:-6.7,hi:6.7,xticks:[[-3,'-fs'],[0,'0'],[3,'fs']]};
 const p=[plot(0,3,'|M delta(f)|',opts),plot(1,3,'|H(f)| / T',opts),plot(2,3,'|S(f)| / (T/Ts)',opts)];
 let b=p.map(v=>v.body).join('')+spectrum(p[0],3,2)+trace(p[1],f=>Math.abs(sinc(f/4)),1,G);
 b+=spectrum(p[2],3,2,q,true,.25);
 if(q>0)b+=pointer(p[1].X(4),p[1].Y(0),'1/T')+pointer(p[2].X(6),p[2].Y(Math.abs(sinc(1.5))),'Nonzero tails');
 return b;
}
function readSamples(q){
 const a=plot(0,2,'s(t)'),b=plot(1,2,'m delta(t)');let body=a.body+b.body;
 for(let n=0;n<=4;n++)body+=pulse(a,n,msg(n),.27);
 const progress=q*5;
 for(let n=0;n<=4;n++)if(progress>n)body+=stem(b,n,msg(n));
 if(q>0){const n=Math.min(4,Math.floor(progress));body+=pointer(a.X(n+.135),a.Y(msg(n)),'Read inside pulse')+pointer(b.X(n),b.Y(msg(n)),'Same sample');}
 return body;
}
function lpf(q){
 const p=[plot(0,3,'M delta(f)',spec),plot(1,3,'H LP(f)',{...spec,xticks:[[-1.5,'-fs/2'],[0,'0'],[1.5,'fs/2']]}),plot(2,3,'M delta(f) H LP(f)',spec)];
 let b=p.map(v=>v.body).join('')+spectrum(p[0],3,2);
 b+=curve([[p[1].X(-1.5),p[1].Y(0)],[p[1].X(-1.5),p[1].Y(1)],[p[1].X(1.5),p[1].Y(1)],[p[1].X(1.5),p[1].Y(0)]],B,2.2);
 b+=curve(Array.from({length:201},(_,i)=>{const f=-7+14*i/200;return[p[2].X(f),p[2].Y(tri(f)*q)];}),B,2.7);
 if(q>0)b+=pointer(p[2].X(0),p[2].Y(q),'Keep k = 0');
 return b;
}
function kernel(q){
 const a=plot(0,2,'H LP(f)',{lo:-2,hi:2,ylo:-.2,yhi:1.3,xticks:[[-.5,'-fs/2'],[0,'0'],[.5,'fs/2']],unit:'f',yticks:false});
 const b=plot(1,2,'h LP(t) / fs',{lo:-3,hi:3,ylo:-.4,yhi:1.3,xticks:[[-2,'-2Ts'],[-1,'-Ts'],[0,'0'],[1,'Ts'],[2,'2Ts']],unit:'t',yticks:false});
 return a.body+b.body+curve([[a.X(-.5),a.Y(0)],[a.X(-.5),a.Y(1)],[a.X(.5),a.Y(1)],[a.X(.5),a.Y(0)]])+trace(b,sinc,q)+(q===1?pointer(b.X(1),b.Y(0),'Zero at Ts','above',65,64):'');
}
const coefficients=[.5,1,-.5,.8,-.3];
const interp=x=>coefficients.reduce((v,c,i)=>v+c*sinc(x-(i-2)),0);
function interpolation(q){
 const p=plot(0,1,'Add shifted sinc pulses',{lo:-3.5,hi:3.5,ylo:-1.15,yhi:1.7,xticks:[[-2,'-2Ts'],[-1,'-Ts'],[0,'0'],[1,'Ts'],[2,'2Ts']],unit:'t',yticks:false});
 let b=p.body+trace(p,interp,1,L,1.6);
 const u=q*5,n=Math.min(4,Math.floor(u)),partial=clamp(u-n);
 for(let k=0;k<=n;k++){
  if(k===n&&partial===0&&q<1)continue;
  b+=trace(p,x=>coefficients[k]*sinc(x-(k-2))*(k===n&&q<1?partial:1),1,G,1.4);
 }
 const sum=x=>coefficients.reduce((v,c,i)=>v+(i<n?1:i===n?(q===1?1:partial):0)*c*sinc(x-(i-2)),0);
 if(q>0)b+=trace(p,sum,1,B,2.8)+pointer(p.X(n-2),p.Y(coefficients[n]),`Sample n = ${n-2}`);
 for(let k=0;k<5;k++)b+=`<circle cx="${p.X(k-2)}" cy="${p.Y(coefficients[k])}" r="3.5" fill="${B}"/>`;
 return b;
}
const tdmValue=(channel,t)=>[.65*Math.cos(tau*.18*t),.75*Math.sin(tau*.15*t+.5),-.5+.3*Math.cos(tau*.22*t)][channel];
function tdm(q,receive){
 const left={x:95,w:380},right={x:665,w:425},base=130,scale=42;
 const X=(x,group)=>group.x+x/3*group.w;
 let b=text(receive?'s(t): interleaved pulses':'Three bandlimited messages',270,27,26,'middle')+text(receive?'One sample stream per message':'s(t): interleaved pulses',865,27,26,'middle');
 function slots(group,show){
  let out=line(group.x,base,group.x+group.w,base);
  for(let n=0;n<3;n++){
   out+=text(n===0?'0':n===1?'Ts':'2Ts',X(n,group),233,23,'middle');
   for(let c=0;c<3;c++){
    const j=n*3+c,t=n+c/3;
    if(j>=show)continue;
    const x=X(t,group),y=base-scale*tdmValue(c,t);
    out+=curve([[x,base],[x,y],[x+group.w/3*.18,y],[x+group.w/3*.18,base]],B,2)+text(c+1,x+9,204,23,'middle');
   }
  }
  return out+text('t',group.x+group.w+10,base+8,23);
 }
 function channels(group,show,continuous){
  let out='';
  for(let c=0;c<3;c++){
   const y=74+c*61;out+=line(group.x,y,group.x+group.w,y)+text(receive?String(c+1):`m${c+1}(t)`,group.x-12,y+7,24,'end');
   if(continuous)out+=curve(Array.from({length:301},(_,i)=>{const t=3*i/300;return[X(t,group),y-tdmValue(c,t)*23];}),L,1.4);
   for(let n=0;n<3;n++){
    const j=n*3+c,t=n+c/3;if(j>=show)continue;
    out+=line(X(t,group),y,X(t,group),y-tdmValue(c,t)*23,B,2.4);
   }
  }
  return out+text('t',group.x+group.w+10,204,23);
 }
 const shown=Math.ceil(q*9);
 b+=receive?slots(left,9)+channels(right,shown,false):channels(left,9,true)+slots(right,shown);
 if(q>0){
  const j=Math.min(8,Math.max(0,shown-1)),c=j%3,t=Math.floor(j/3)+c/3;
  const src=receive?[X(t,left),base-tdmValue(c,t)*scale]:[X(t,left),74+c*61-tdmValue(c,t)*23];
  const dst=receive?[X(t,right),74+c*61-tdmValue(c,t)*23]:[X(t,right),base-tdmValue(c,t)*scale];
  const lx=left.x+left.w+12,rx=right.x-(receive?35:12),dx=rx-lx,dy=dst[1]-src[1],length=Math.hypot(dx,dy),ux=dx/length,uy=dy/length;
  b+=line(src[0],src[1],lx,src[1],G,1,'4 4')+line(rx,dst[1],dst[0],dst[1],G,1,'4 4');
  b+=line(lx,src[1],rx,dst[1],B,1.8)+curve([[rx-8*ux+4*uy,dst[1]-8*uy-4*ux],[rx,dst[1]],[rx-8*ux-4*uy,dst[1]-8*uy+4*ux]],B,1.8);
  b+=`<circle cx="${src[0]}" cy="${src[1]}" r="6" fill="white" stroke="${B}" stroke-width="2"/><circle cx="${dst[0]}" cy="${dst[1]}" r="6" fill="white" stroke="${B}" stroke-width="2"/>`;
  b+=text(`Channel ${c+1}`,(lx+rx)/2,(src[1]+dst[1])/2-23,23,'middle');
 }
 return b;
}

export async function generateDemos({run,sharp}){
 const definitions=[['pulse-types',pulseTypes],['pam-formation',formation],['sampling-replicas',replicas],['sampling-rate',q=>rate(q*.5)],['sampling-rate-up',q=>rate(.5+q*.5)],
  ['pulse-response',pulseResponse],['pam-spectrum',pamSpectrum],['read-samples',readSamples],['sampling-lpf',lpf],
  ['sinc-kernel',kernel],['interpolation',interpolation],['tdm-send',q=>tdm(q,false)],['tdm-receive',q=>tdm(q,true)]];
 const assets={};
 const source=await fs.readFile(new URL(import.meta.url));
 const codeHash=createHash('sha256').update(source).digest('hex');
 const shared=[sinc,esc,typeset,text,line,curve,pointer,plot,trace,stem,pulse,msg,tri,spectrum,interp,tdmValue].map(f=>f.toString()).join('\n')+JSON.stringify({W,H,B,G,L,tau,coefficients,spec});
 for(const [id,render] of definitions){
  const dir=path.join(run,'demos',id);await fs.mkdir(dir,{recursive:true});
  const N=id.startsWith('tdm')?37:id==='interpolation'?36:29;
  let cache;try{cache=JSON.parse(await fs.readFile(path.join(dir,'cache.json'),'utf8'));}catch{}
  const frames=states(N).map((_,i)=>`frame-${String(i).padStart(3,'0')}.png`);
  const durations=frames.map((_,i)=>i===0?500:i===N-1?1100:160);
  const renderHash=createHash('sha256').update(shared+render.toString()+(id.startsWith('tdm')?tdm.toString():'')+(id.startsWith('sampling-rate')?rate.toString():'')+JSON.stringify({N,durations})).digest('hex');
  if(cache?.renderHash!==renderHash){
   for(const [i,q] of states(N).entries()){
    const body=render(q);
    if(/NaN|Infinity/.test(body))throw Error('Nonfinite animation: '+id+':'+i);
    const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" fill="white"/>${body}</svg>`;
    await fs.writeFile(path.join(dir,frames[i].replace('.png','.svg')),svg);
    await sharp(Buffer.from(svg)).resize(W*2,H*2).flatten({background:'#FFFFFF'}).png({compressionLevel:9}).toFile(path.join(dir,frames[i]));
   }
   await fs.copyFile(path.join(dir,frames[0]),path.join(dir,'first.png'));
   await fs.copyFile(path.join(dir,frames.at(-1)),path.join(dir,'last.png'));
   await fs.writeFile(path.join(dir,'frames.json'),JSON.stringify({frames,durations,states:states(N),codeHash},null,2));
   await fs.writeFile(path.join(dir,'cache.json'),JSON.stringify({codeHash,renderHash}));
  }
  const rel=file=>`demos/${id}/${file}`;
  assets[id]={file:rel('first.png'),first:rel('first.png'),poster:rel('last.png'),width:W,height:H,
   description:'Note 7: '+id.replaceAll('-',' ')+'. Static entry; click once; final state retained.',durationMs:durations.reduce((a,b)=>a+b,0),parameters:{note7Aligned:true}};
  console.log('Prepared animation',id);
 }
 let sampleError=0;
 for(let n=-2;n<=2;n++)sampleError=Math.max(sampleError,Math.abs(interp(n)-coefficients[n+2]));
 if(sampleError>1e-12)throw Error('Interpolation does not preserve samples');
 await fs.writeFile(path.join(run,'demos-check.json'),JSON.stringify({assets,nativeFrameBackend:true,logicalSize:[W,H],rasterSize:[W*2,H*2],
  sampleInterpolationMaxError:sampleError,singlePlay:true,minimumFontPx:22,nativePlaybackTested:false},null,2));
 return assets;
}
