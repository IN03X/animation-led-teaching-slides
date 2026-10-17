import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const deps='C:/Users/10486/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const req=createRequire(deps+'/node/node_modules/package.json');
process.env.RUNTIME_NODE_MODULES=deps+'/node/node_modules';
const {PresentationFile,FileBlob}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')));
const skill=process.env.PRESENTATION_SKILL_DIR||'C:/Users/10486/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const hash=b=>createHash('sha256').update(b).digest('hex');

export async function finalizeRun({run,root,python=deps+'/python/python.exe'}){
 const m=JSON.parse(await fs.readFile(path.join(run,'manifest.json'),'utf8'));
 const candidate=path.join(run,'candidate.pptx'),sha=hash(await fs.readFile(candidate));
 const finalPath=path.join(run,'validated','T'+(m.tutorialNumber??4)+'-'+sha.slice(0,12)+'.pptx');
 await fs.mkdir(path.dirname(finalPath),{recursive:true});
 const tables=m.pages.flatMap((v,i)=>v.nativeTable?[i+1]:[]);
 await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,pythonExecutable:python,
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],
  explicitTotalSlideCount:m.total,fontPolicy:{basis:'user_request',families:['Times New Roman']},
  requiredNativeTableOwnerSlides:tables,verifyArtifactToolImport:true,
  receiptPath:path.join(run,'validation-'+sha.slice(0,12)+'.json')});
 const deck=await PresentationFile.importPptx(await FileBlob.load(path.join(run,'static-preview.pptx')));
 const renderOnly=process.env.RENDER_PAGES?new Set(process.env.RENDER_PAGES.split(',').map(Number)):null;
 for(let i=0;i<deck.slides.items.length;i++){
  if(renderOnly&&!renderOnly.has(i+1))continue;
  const png=await deck.export({slide:deck.slides.items[i],format:'png',scale:1.25});
  await fs.writeFile(path.join(run,`slide-${String(i+1).padStart(3,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
  console.log('Rendered',i+1);
 }
 const receipt={finalPath,sha256:hash(await fs.readFile(finalPath)),sourceHashes:m.sourceHashes,slides:m.total,nativePlaybackTested:false};
 await fs.writeFile(path.join(run,'latest.json'),JSON.stringify(receipt,null,2));
 console.log(JSON.stringify({run,finalPath,slides:m.total}));return receipt;
}

if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){
 const run=path.resolve(process.argv[2]);
 await finalizeRun({run,root:path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..')});
}
