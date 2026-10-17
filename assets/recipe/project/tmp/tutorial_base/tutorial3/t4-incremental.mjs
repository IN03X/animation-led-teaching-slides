// Separate a formula's unchanged prefix from its changing remainder.
export function prepareIncremental(equations, geometry, animation) {
 const originals=[...equations], groups=[], seen=new Set();
 const key=e=>e.slide+':'+e.name;
 const incoming=new Map(animation.filter(a=>a.replacementOf).map(a=>[a.slide+':'+a.name,a]));
 const token=s=>s.match(/\\[A-Za-z]+|\\.|./gs)||[];
 const common=items=>{
  const ts=items.map(e=>token(e.tex));let n=0;
  while(ts.every(t=>n<t.length&&t[n]===ts[0][n]))n++;
  let depth=0,safe=0;
  for(let i=0;i<n;i++){
   const t=ts[0][i];if(t==='{')depth++;if(t==='}')depth--;
   if(depth===0&&!['_','^','\\','\\frac','\\color','\\text','\\mathrm','\\operatorname'].includes(t))safe=i+1;
  }
  return ts[0].slice(0,safe).join('');
 };
 for(const root of originals){
  if(incoming.has(key(root))||seen.has(key(root)))continue;
  const chain=[root];let last=root;
  while(true){
   const next=originals.find(e=>incoming.get(key(e))?.replacementOf===last.name&&e.slide===last.slide);
   if(!next)break;chain.push(next);last=next;
  }
  if(chain.length<2)continue;
  chain.forEach(e=>seen.add(key(e)));
  const prefix=chain.find(e=>e.incrementalPrefix)?.incrementalPrefix??common(chain);
  if(prefix.length<4&&!chain.some(e=>e.retainMatchedInk))continue;
  if(!chain.every(e=>e.tex.startsWith(prefix)))throw Error('Invalid fixed formula prefix: '+key(root));
  const family=key(root),members=[];let fixed=null;
  for(const e of chain){
   const entry=animation.find(a=>a.slide===e.slide&&a.name===e.name&&!a.exitOnly);
   const source=incoming.get(key(e));
   e.mathFamily=family;e.fragment='body';e.fixedText=prefix;
   if(source&&!source.motion)e.previousName=source.replacementOf;
   e.renderTex='\\color[HTML]{13579B}'+prefix+'\\color[HTML]{202020}'+e.tex.slice(prefix.length);
   if(!fixed||source?.motion){
    const name='fixed-'+e.name,copy={...e,name,fragment:'prefix',fixedPart:true};
    const g=geometry.find(g=>g.slide===e.slide&&g.name===e.name);
    equations.push(copy);geometry.push({...g,name,fixedPart:true});
    if(entry){
     const a={...entry,name};delete a.replacementOf;
     if(fixed&&source?.motion){
      a.motion={...source.motion,fromName:fixed.name};
      a.instantEntrance=true;entry.instantEntrance=true;
      const gone=animation.find(v=>v.slide===e.slide&&v.name===source.replacementOf&&v.exitOnly);
      animation.push({...gone,name:fixed.name,replacedBy:name});
     }else if(!entry.motion)delete a.motion;
     animation.push(a);
    }
    fixed=copy;
   }
   e.fixedPrefixName=fixed.name;members.push(e.name);
  }
  groups.push({slide:root.slide,family,prefix,members});
 }
 return groups;
}
