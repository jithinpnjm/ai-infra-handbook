// Parse every ```mermaid block under docs/ with mermaid.parse; report failures.
import fs from 'fs'; import path from 'path';
import { JSDOM } from 'jsdom';
const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window; globalThis.document = dom.window.document;
globalThis.DOMPurify = undefined;
const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false });
function* walk(d){ for (const f of fs.readdirSync(d,{withFileTypes:true})) { const p=path.join(d,f.name); if (f.isDirectory()) yield* walk(p); else if (p.endsWith('.md')) yield p; } }
let bad=0, n=0;
const only = process.argv[2];
for (const f of walk('docs')) {
  if (only && !f.includes(only)) continue;
  const s = fs.readFileSync(f,'utf8'); const re=/```mermaid\n([\s\S]*?)```/g; let m;
  while ((m=re.exec(s))) { n++; try { await mermaid.parse(m[1]); } catch(e){ bad++; console.log('FAIL',f,'\n',String(e.message||e).split('\n').slice(0,4).join('\n')); } }
}
console.log(`checked ${n} diagrams, ${bad} failed`);
