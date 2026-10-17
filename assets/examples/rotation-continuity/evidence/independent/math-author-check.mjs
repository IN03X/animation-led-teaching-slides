import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const [workspace,run,tag='first']=process.argv.slice(2),output=path.dirname(fileURLToPath(import.meta.url));
const source=await fs.readFile(path.join(workspace,'lesson-demos.mjs'),'utf8');
const hash=createHash('sha256').update(source).digest('hex');
// Expose original lexical functions in memory; do not change the author file.
const instrumented=source+'\nexport {rot as authoredRotate,frame as authoredFrame,map as authoredMap};\n';
const model=await import('data:text/javascript;base64,'+Buffer.from(instrumented).toString('base64'));
const oracle=JSON.parse(await fs.readFile(path.join(output,'math-oracle.json'),'utf8'));
let comparisons=0,maxError=0,states=0,metadata=0;
function close(actual,expected){
 assert(actual.length===expected.length);
 for(let i=0;i<actual.length;i++){const e=Math.abs(actual[i]-expected[i]);maxError=Math.max(maxError,e);assert(e<1e-10,JSON.stringify({actual,expected,error:e}));}
 comparisons++;
}
for(const c of oracle.cases){
 const local=c.point.map((v,i)=>v-c.centre[i]);
 const actual=model.authoredRotate(local,c.degrees*Math.PI/180).map((v,i)=>v+c.centre[i]);
 close(actual,c.expected);
}
const original=[4,2],centre=[2,1],relative=[2,1];
const expectedRotation=(point,degrees)=>{
 const a=degrees*Math.PI/180;
 return [point[0]*Math.cos(a)-point[1]*Math.sin(a),point[0]*Math.sin(a)+point[1]*Math.cos(a)];
};
const demoIds=await fs.readdir(path.join(run,'demos'));
assert.deepEqual([...demoIds].sort(),['process','subtract','quarter','add','focus','horizontal','vertical','return','thirty'].sort());
for(const id of demoIds){
 const meta=JSON.parse(await fs.readFile(path.join(run,'demos',id,'frames.json'),'utf8'));
 assert.equal(meta.codeHash,hash,'Cached frame source version differs from actual tested model');
 assert.equal(meta.frames.length,meta.states.length);
 for(let i=0;i<meta.states.length;i++){
  const q=i/(meta.states.length-1),{state,body}=model.authoredFrame(id,q);states++;
  assert(!/NaN|Infinity/.test(body));assert.deepEqual(meta.states[i],state);metadata++;
  if(id==='subtract'){close(state.c,centre.map(v=>v*(1-q)));close(state.p,original.map((v,i)=>v-centre[i]*q));}
  if(id==='quarter')close(state.p,expectedRotation(relative,90*q));
  if(id==='add'){close(state.c,centre.map(v=>v*q));close(state.p,[-1+2*q,2+q]);}
  if(id==='horizontal')close(state.h,expectedRotation([2,0],35*q));
  if(id==='vertical'){close(state.h,expectedRotation([2,0],35));close(state.v,expectedRotation([0,1],35*Math.min(1,2*q)));}
  if(id==='thirty')close(state.p,expectedRotation(relative,30*q).map((v,i)=>v+centre[i]));
  if(id==='process'){
   const phase=Math.min(2,Math.floor(q*3)),local=q===1?1:q*3-phase;
   assert.equal(state.phase,phase);assert.equal(state.local,local);
   const c=phase===0?centre.map(v=>v*(1-local)):phase===1?[0,0]:centre.map(v=>v*local);
   const offset=expectedRotation(relative,phase===0?0:phase===1?90*local:90);
   close(state.c,c);close(state.p,offset.map((v,i)=>v+c[i]));
  }
  if(id==='focus'){
   close(state.sourceQ,relative);
   if(q===1)assert.equal(body,model.authoredFrame('horizontal',0).body);
   else {close(state.h,[2*Math.min(1,q*2),0]);close(state.v,[2,Math.max(0,2*q-1)]);}
  }
  if(id==='return'){
   close(state.c,centre.map(v=>v*q));
   close(state.p,expectedRotation(relative,35).map((v,i)=>v+centre[i]*q));
   if(q===0)assert.equal(body,model.authoredFrame('vertical',1).body);
  }
 }
}
for(const [from,to] of [['focus','horizontal'],['vertical','return']]){
 const [a,b]=await Promise.all([fs.readFile(path.join(run,'demos',from,'last.png')),fs.readFile(path.join(run,'demos',to,'first.png'))]);
 assert(a.equals(b),'Visual boundary must retain the same actual diagram: '+from+' -> '+to);
}
const zero=model.authoredMap([0,0]),right=model.authoredMap([1,0]),up=model.authoredMap([0,1]);
assert(right[0]>zero[0]&&up[1]<zero[1]);close([right[0]-zero[0]],[zero[1]-up[1]]);
const report={passed:true,authorDemoSourceSha256:hash,independentComplexOracleCases:oracle.cases.length,
 actualDemoStatesChecked:states,generatedMetadataComparedToActualSource:metadata,numericComparisons:comparisons,
 demoIds,maxNumericError:maxError,equalAxisScaleAndUpwardY:true,exampleExpected:[1,3],exactSourceImageBoundaries:['focus -> horizontal','vertical -> return'],
 claimBoundary:'Tests the actual author numerical functions and generated state metadata; does not independently certify every drawn pixel or native playback.'};
await fs.writeFile(path.join(output,'math-author-'+tag+'.json'),JSON.stringify(report,null,2),{flag:'wx'});
console.log(JSON.stringify(report));
