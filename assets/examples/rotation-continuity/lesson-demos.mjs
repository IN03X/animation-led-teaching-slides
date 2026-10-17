import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const W=1120,H=300,B='#202020',G='#9B9B9B',L='#D0D0D0';
const text=(s,x,y,size=25,col=B)=>`<text x="${x}" y="${y}" font-family="Times New Roman" font-size="${size}" fill="${col}">${s}</text>`;
const line=(a,b,col=B,w=2,dash='')=>`<path d="M${a[0]} ${a[1]}L${b[0]} ${b[1]}" stroke="${col}" stroke-width="${w}" fill="none" ${dash?`stroke-dasharray="${dash}"`:''}/>`;
const dot=(p,col=B,open=false)=>`<circle cx="${p[0]}" cy="${p[1]}" r="5" fill="${open?'white':col}" stroke="${col}" stroke-width="2"/>`;
const add=(p,q)=>p.map((v,i)=>v+q[i]);
const mul=(p,k)=>p.map(v=>v*k);
const rot=(p,t)=>[p[0]*Math.cos(t)-p[1]*Math.sin(t),p[0]*Math.sin(t)+p[1]*Math.cos(t)];
const norm=p=>Math.hypot(...p);
const close=(a,b)=>assert(Math.abs(a-b)<1e-10);
const map=([x,y])=>[460+58*x,235-58*y];
const arrow=(p,q,col=B)=>{const a=map(p),b=map(q),d=[b[0]-a[0],b[1]-a[1]],n=Math.hypot(...d)||1,t=[d[0]/n,d[1]/n];return line(a,b,col,2.7)+line(b,[b[0]-9*t[0]+4*t[1],b[1]-9*t[1]-4*t[0]],col)+line(b,[b[0]-9*t[0]-4*t[1],b[1]-9*t[1]+4*t[0]],col);};
function axes(){let s=line(map([-2.8,0]),map([5,0]),G,1)+line(map([0,-.65]),map([0,3.7]),G,1)+text('x',map([5,0])[0]+10,242,23)+text('y',449,17,23);for(const x of [-2,-1,0,1,2,3,4])s+=text(x,map([x,0])[0]-6,268,21,G);for(const y of [1,2,3])s+=line(map([-2.8,y]),map([5,y]),'#EEEEEE',.7)+text(y,770,map([0,y])[1]+7,21,G);return s;}
function pathArc(c,p,t,col=G){const q=add(p,mul(c,-1));return `<path d="${Array.from({length:50},(_,i)=>{const a=map(add(c,rot(q,t*i/49)));return `${i?'L':'M'}${a[0]} ${a[1]}`;}).join(' ')}" fill="none" stroke="${col}" stroke-width="1.4"/>`;}
function frame(id,q){
  const P=[4,2],C=[2,1],Q=[2,1],T=Math.PI/2;
  let b=axes(),state={id,q};
  const label=(s,p,dx=13,dy=-14,col=B)=>text(s,map(p)[0]+dx,map(p)[1]+dy,25,col);
  if(id==='process'){
    const phase=Math.min(2,Math.floor(q*3)),local=q===1?1:q*3-phase;
    let c,p;
    if(phase===0){c=mul(C,1-local);p=add(Q,c);}
    else if(phase===1){c=[0,0];p=rot(Q,local*T);}
    else {c=mul(C,local);p=add(rot(Q,T),c);}
    b+=arrow(C,P,L)+dot(map(C),G,true)+dot(map(P),G,true)+label('C=(2,1)',C,13,40,G)+label('P=(4,2)',P,13,-14,G);
    b+=arrow(c,p)+dot(map(c))+dot(map(p));
    b+=text(['Subtract C','Turn 90 degrees CCW','Add the same C back'][phase],30,35,27)+text('Follow the same offset arrow.',30,80,25);
    if(q===1)b+=label("P'=(1,3)",p,18,-14);
    state={...state,phase,local,c,p};close(norm(add(p,mul(c,-1))),Math.sqrt(5));
  }else if(id==='focus'){
    if(q===1)return {body:frame('horizontal',0).body,state:{...state,sourceQ:Q,focusComplete:true}};
    const h=[2*Math.min(1,q*2),0],v=[2,Math.max(0,q*2-1)];
    b+=`<g opacity="${1-q}">`+arrow(C,P,G)+dot(map(C),G,true)+dot(map(P),G,true)+label('C',C,13,30,G)+label('P',P,13,-14,G)+'</g>';
    b+=arrow([0,0],Q,G)+dot(map(Q),G,true)+label('Same Q=(2,1)',Q,80,35,G)+line([656,203],map(Q),G,1);
    if(q>0)b+=arrow([0,0],h)+dot(map(h));
    if(q>.5)b+=arrow([2,0],v,G);
    b+=text('Select the offset Q.',30,35,27)+text('Split: right u, then up v.',30,80,25);
    state={...state,sourceQ:Q,h,v,worldOpacity:1-q};
  }else if(id==='return'){
    if(q===0)return {body:frame('vertical',1).body,state:{...state,c:[0,0],p:rot(Q,35*Math.PI/180)}};
    const theta=35*Math.PI/180,h=rot([2,0],theta),v=rot([0,1],theta),c=mul(C,q),p=add(c,add(h,v));
    b+=arrow([0,0],Q,L)+dot(map(Q),G,true);
    b+=`<g opacity="${q}">`+arrow(C,P,L)+dot(map(C),G,true)+dot(map(P),G,true)+label('C=(2,1)',C,13,40,G)+label('P=(4,2)',P,13,-14,G)+'</g>';
    b+=arrow(c,add(c,h),G)+arrow(add(c,h),p,G)+arrow(c,p)+dot(map(c))+dot(map(p));
    const mid=map(add(add(c,h),mul(v,.5)));
    b+=text('K',720,175,25,G)+line([713,170],mid,G,1);
    if(q===1)b+=label("P'",p,18,-14);
    b+=text('Return the turned offset to C.',30,35,27)+text('Same scene, now with the result.',30,80,25);
    if(q===1)b+=text("P' = C + Q'",790,160,27)+text('90-degree check: (1,3)',790,215,24);
    state={...state,c,p,h,v,theta};close(norm(add(p,mul(c,-1))),Math.sqrt(5));
  }else if(id==='subtract'){
    const c=add(C,mul(C,-q)),p=add(P,mul(C,-q));
    b+=arrow(C,P,L)+dot(map(C),G,true)+dot(map(P),G,true);
    if(q>0)b+=label('old C',C,13,40,G)+label('old P',P,13,-14,G);
    b+=arrow(c,p)+dot(map(c))+dot(map(p));
    if(q===0)b+=label('C',c,-35,-15)+label('P',p,14,-16);
    if(q===1)b+=label('C moved to 0',c,-175,-15)+label('Q=(2,1)',p,14,-35);
    b+=text('Translate both by (-2,-1)',30,35,27)+text('Same offset; no turn yet.',30,80,25);
    state={...state,c,p,displacement:add(p,mul(c,-1))};close(norm(add(p,mul(c,-1))),Math.sqrt(5));
  }else if(id==='quarter'){
    const t=T*q,h=rot([2,0],t),v=rot([0,1],t),p=add(h,v);
    b+=arrow([0,0],Q,L)+label('Q=(2,1)',Q,15,-14,G)+pathArc([0,0],Q,t);
    b+=arrow([0,0],h,G)+arrow(h,p,G)+arrow([0,0],p)+dot(map(p));
    if(q===1)b+=label("Q'=(-1,2)",p,-190,-15);
    b+=text('2 right becomes 2 up.',30,35,27)+text('1 up becomes 1 left.',30,80,27);
    b+=text(`Counterclockwise: ${Math.round(q*90)} degrees`,790,125,24);
    state={...state,t,h,v,p};close(norm(p),Math.sqrt(5));
  }else if(id==='add'){
    const c=mul(C,q),p=add([-1,2],c);
    b+=arrow([0,0],[-1,2],L)+label("Q'=(-1,2)",[-1,2],-190,-12,G);
    b+=dot(map(C),G,true)+label('C=(2,1)',C,12,30,G)+arrow(c,p)+dot(map(c))+dot(map(p));
    b+=label(q===1?"P'=(1,3)":'Same turned offset',p,12,-14);
    b+=text('Add C=(2,1) to the arrow.',30,35,27);
    state={...state,c,p};close(norm(add(p,mul(c,-1))),Math.sqrt(5));
  }else if(id==='horizontal'||id==='vertical'){
    const theta=35*Math.PI/180,t=id==='horizontal'?theta*q:theta;
    const h=rot([2,0],t),v=rot([0,1],id==='horizontal'?0:theta*Math.min(1,q*2));
    b+=arrow([0,0],[2,0],L)+arrow([2,0],[2,1],L)+dot(map(Q),G,true)+label('Q=(u,v)',Q,30,-30,G);
    b+=arrow([0,0],h)+dot(map(h));
    b+=line(map(h),map([h[0],0]),G,1.3,'4 4')+line(map(h),map([0,h[1]]),G,1.3,'4 4');
    b+=label('H',h,-38,-12);
    b+=pathArc([0,0],[.7,0],t);
    if(q===1)b+=text('theta',map([1,.15])[0],map([1,.15])[1],21);
    b+=text('Illustration: u=2, v=1, theta=35 degrees',30,25,25);
    if(id==='horizontal'){
      b+=text('Turn the horizontal leg (u,0).',30,65,27);
      if(q===1)b+=text('Length = u',790,115,24)+text('Horizontal: u cos(theta)',790,155,24)+text('Vertical: u sin(theta)',790,195,24);
    }else{
      const join=Math.max(0,(q-.5)*2),base=mul(h,join),tip=add(base,v);
      if(q>0)b+=arrow(base,tip,G)+dot(map(tip),G)+text('K',720,175,25,G)+line([713,170],map(add(base,mul(v,.5))),G,1);
      b+=text(q<.5?'Turn the remaining vertical leg.':'The turned legs are perpendicular.',30,65,27);
      if(q>.5)b+=text('Join the turned legs head to tail.',30,105,26);
      if(q===1){const p=add(h,v);b+=arrow([0,0],p)+dot(map(p))+label("Q'=H+K",p,-70,-22);b+=text('Left v sin(theta)',790,155,24)+text('Up v cos(theta)',790,195,24);}
      state.v=v;state.join=join;state.p=add(h,v);
    }
    state={...state,theta,t,h};close(norm(h),2);
  }else if(id==='thirty'){
    const t=q*Math.PI/6,p=add(C,rot(Q,t));
    b+=arrow(C,P,L)+dot(map(P),G,true)+label('P=(4,2)',P,14,-26,G)+dot(map(C))+label('C=(2,1)',C,12,30);
    b+=pathArc(C,P,t)+arrow(C,p)+dot(map(p));
    if(q===1)b+=label("P' approx (3.232,2.866)",p,18,-22);
    b+=text(`Angle: ${Math.round(q*30)} degrees counterclockwise`,30,35,27);
    state={...state,t,p};close(norm(add(p,mul(C,-1))),Math.sqrt(5));
  }
  return {body:b,state};
}
export async function generateDemos({run,sharp}){
  const assets={},checks=[],codeHash=createHash('sha256').update(await fs.readFile(new URL(import.meta.url))).digest('hex');
  for(const id of ['process','subtract','quarter','add','focus','horizontal','vertical','return','thirty']){
    const dir=path.join(run,'demos',id);await fs.mkdir(dir,{recursive:true});
    const frames=[],durations=[],states=[];
    const N=id==='process'?85:29;
    for(let i=0;i<N;i++){
      const {body,state}=frame(id,i/(N-1));assert(!/NaN|Infinity/.test(body));
      const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" fill="white"/>${body}</svg>`;
      const file=`frame-${String(i).padStart(3,'0')}.png`;
      await fs.writeFile(path.join(dir,file.replace('.png','.svg')),svg);
      await sharp(Buffer.from(svg)).resize(W*2,H*2).png().toFile(path.join(dir,file));
      frames.push(file);durations.push(i===0?500:i===N-1?1100:120);states.push(state);
    }
    await fs.copyFile(path.join(dir,frames[0]),path.join(dir,'first.png'));
    await fs.copyFile(path.join(dir,frames.at(-1)),path.join(dir,'last.png'));
    await fs.writeFile(path.join(dir,'frames.json'),JSON.stringify({frames,durations,states,codeHash},null,2));
    const rel=f=>`demos/${id}/${f}`;
    assets[id]={file:rel('first.png'),first:rel('first.png'),poster:rel('last.png'),width:W,height:H,durationMs:durations.reduce((a,b)=>a+b,0),description:`Rotate-point lesson: ${id}; static entry, one click, held result.`,parameters:{P:[4,2],C:[2,1],thetaDegrees:id==='thirty'?30:id==='horizontal'||id==='vertical'?35:90}};
    checks.push({id,frames:N,first:states[0],last:states.at(-1),finite:true});
  }
  await fs.writeFile(path.join(run,'demos-check.json'),JSON.stringify({checks,assets,nativeFrameBackend:true,singlePlay:true,nativePlaybackTested:false},null,2));
  return assets;
}
