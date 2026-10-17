import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
const dir=path.dirname(fileURLToPath(import.meta.url));
const deps='C:/Users/10486/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const req=createRequire(deps+'/node/node_modules/package.json');
process.env.RUNTIME_NODE_MODULES=deps+'/node/node_modules';
const {PresentationFile,FileBlob}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')));
const run=process.env.PDF_RUN||path.join(dir,'methods-work/pdf-export-r1'),script=path.join(dir,'export-pdf.py');
console.log(execFileSync(deps+'/python/python.exe',['-X','utf8',script,'prepare'],{encoding:'utf8'}));
const deck=await PresentationFile.importPptx(await FileBlob.load(path.join(run,'static.pptx')));
for(let i=0;i<deck.slides.items.length;i++) {
  const png=await deck.export({slide:deck.slides.items[i],format:'png',scale:2.5});
  await fs.writeFile(path.join(run,`slide-${String(i+1).padStart(3,'0')}.png`),Buffer.from(await png.arrayBuffer()));
  if((i+1)%15===0)console.log('Rendered '+(i+1));
}
console.log(execFileSync(deps+'/python/python.exe',['-X','utf8',script,'assemble'],{encoding:'utf8'}));
