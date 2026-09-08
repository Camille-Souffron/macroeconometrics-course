const $ = id => document.getElementById(`lab-${id}`);
const root = new URL('../../', import.meta.url);
const asset = path => new URL(path, root);
const colors = ['#1d4e89','#a34b35','#427665','#8a6c33','#785a88','#5c666e'];
let catalog, metadata, exercise, worker, runId = 0, busy = false, last, pinned, lastSpec, lastDataset;
const text = (tag, content, cls) => { const e=document.createElement(tag);e.textContent=content;if(cls)e.className=cls;return e; };
async function resource(path) { const r=await fetch(asset(path));if(!r.ok)throw Error(`Cannot load ${path}`);return r; }
function option(select,value,label) { const e=text('option',label);e.value=value;select.append(e); }
function status(message) { $('status').textContent=message; }
function specification() {
  const spec={module:exercise.module,method:exercise.method,...exercise.defaults};
  for(const c of exercise.controls) {
    const e=document.getElementById(`spec-${c.key}`);
    spec[c.key]=c.type==='checkbox'?e.checked:c.type==='number'||typeof c.default==='number'?Number(e.value):e.value;
  }
  return spec;
}
function codeFor(spec) {
  const url=asset(metadata[$('dataset').value].path).href;
  const join=metadata[$('dataset').value].join;
  const merge=join?`\nframe = frame.merge(pd.read_csv(${JSON.stringify(asset(join).href)}), on='date', how='inner', validate='one_to_one')`:'';
  return `import json\nimport pandas as pd\nfrom core import run\n\nframe = pd.read_csv(${JSON.stringify(url)})${merge}\nspec = json.loads(r'''${JSON.stringify(spec,null,2)}''')\nresult = run(frame, spec)\nprint(json.dumps(result, indent=2))`;
}
function updateSpec() {
  if(busy)cancel('Specification changed; previous computation cancelled.');
  const spec=specification();$('code').textContent=codeFor(spec);
  for(const c of exercise.controls) {
    const wrapper=document.getElementById(`spec-${c.key}`).closest('.lab-control');
    wrapper.hidden=Boolean(c.when)&&!Object.entries(c.when).every(([key,values])=>values.includes(spec[key]));
    document.getElementById(`spec-${c.key}`).disabled=wrapper.hidden;
  }
  const url=new URL(location);url.searchParams.set('method',exercise.id);url.searchParams.set('dataset',$('dataset').value);
  const changes={};for(const [k,v] of Object.entries(spec))if(v!==exercise.defaults[k]&&!['module','method'].includes(k))changes[k]=v;
  if(Object.keys(changes).length)url.searchParams.set('spec',JSON.stringify(changes));else url.searchParams.delete('spec');
  history.replaceState(null,'',url);
  if(last)status('Specification changed. Run to update the displayed result.');
  $('stale').hidden=!last || (lastDataset===$('dataset').value&&JSON.stringify(lastSpec)===JSON.stringify(spec));
}
function describeData() {
  const d=metadata[$('dataset').value];const container=$('provenance');container.replaceChildren();
  container.append(text('p',`${d.title}. ${d.frequency}. Sample: ${d.sample}. ${d.vintage}`));
  container.append(text('p',d.provenance));container.append(text('p',d.license));
  const a=text('a','Download the versioned CSV');a.href=asset(d.path);a.download='';container.append(a);
  if(d.join){const p=text('p','');const a=text('a','Download the accompanying shock series');a.href=asset(d.join);a.download='';p.append(a);container.append(p);}
  for(const v of d.series) {
    const p=text('p',`${v.column}: ${v.definition} (${v.id}). ${v.transformation} `);
    const a=text('a','Source');a.href=v.url;a.target='_blank';a.rel='noopener';p.append(a);container.append(p);
  }
}
function selectExercise(id, restore=false) {
  if(busy)cancel();exercise=catalog.experiments.find(e=>e.id===id)||catalog.experiments[0];
  $('method').value=exercise.id;$('title').textContent=exercise.title;$('description').textContent=exercise.description;
  $('reference').replaceChildren(text('span',`${exercise.preset.label}. `));
  const ref=text('a',exercise.citation||exercise.reference);ref.href=asset(`references.html#ref-${exercise.reference}`);$('reference').append(ref,text('span',` — ${exercise.preset.changed}`));
  $('notes').href=asset(`chapters/${exercise.chapter.replace('.qmd','.html')}`);
  $('dataset').replaceChildren();exercise.datasets.forEach(id=>option($('dataset'),id,metadata[id].title));
  const params=new URL(location).searchParams;
  if(restore&&exercise.datasets.includes(params.get('dataset')))$('dataset').value=params.get('dataset');
  let overrides={};if(restore)try{overrides=JSON.parse(params.get('spec')||'{}');}catch{status('Invalid deep-link specification; defaults restored.');}
  const controls=$('spec-controls');controls.replaceChildren();const advanced=text('details','');advanced.append(text('summary','Additional specification choices'));
  exercise.controls.forEach((c,i)=>{
    const wrapper=text('div','','lab-control');const label=text('label',c.label);label.htmlFor=`spec-${c.key}`;
    const input=document.createElement(c.type==='select'?'select':'input');input.id=`spec-${c.key}`;
    if(c.type==='select')c.options.forEach(value=>option(input,value,String(value)));
    else {input.type=c.type; if(c.type==='number'){input.min=c.min;input.max=c.max;input.step=c.step;input.required=true;}}
    let value=overrides[c.key]??exercise.defaults[c.key]??c.default;
    if(c.type==='select'&&!c.options.some(v=>String(v)===String(value)))value=c.default;
    if(c.type==='number'&&(!Number.isFinite(Number(value))||value<c.min||value>c.max))value=c.default;
    if(c.type==='checkbox')input.checked=Boolean(value);else input.value=value;
    input.addEventListener('change',updateSpec);wrapper.append(label,input);
    if(c.help){const help=text('small',c.help);help.id=`help-${c.key}`;input.setAttribute('aria-describedby',help.id);wrapper.append(help);}
    (i<5?controls:advanced).append(wrapper);
  });if(exercise.controls.length>5)controls.append(advanced);
  $('output').hidden=true;$('empty').hidden=false;$('error').hidden=true;last=null;
  describeData();updateSpec();status('Ready. Python loads on the first run.');
}
function selectChapter(chapter,id,restore=false) {
  $('chapter').value=chapter;$('method').replaceChildren();catalog.experiments.filter(e=>e.chapter===chapter).forEach(e=>option($('method'),e.id,e.title));
  selectExercise(id||$('method').value,restore);
}
function cancel(message='Computation cancelled. Packages remain in the browser HTTP cache.') {
  worker?.terminate();worker=null;runId++;busy=false;$('cancel').hidden=true;$('run').textContent='Run specification';status(message);
}
function format(value) {return value===null?'Not available':typeof value==='number'?Number(value.toPrecision(5)).toLocaleString('en-US',{maximumSignificantDigits:5}):typeof value==='object'?JSON.stringify(value):String(value);}
function table(values) {
  const t=document.createElement('table');const body=document.createElement('tbody');
  for(const [key,value] of Object.entries(values)){const row=document.createElement('tr');const th=text('th',key);th.scope='row';row.append(th,text('td',format(value)));body.append(row);}t.append(body);return t;
}
function plot(result) {
  const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 800 380');svg.setAttribute('role','img');svg.setAttribute('aria-label',result.title);
  const title=document.createElementNS(ns,'title');title.textContent=result.title;svg.append(title);
  const entries=Object.entries(result.curves);const xs=result.x||entries[0][1].map((_,i)=>i);const all=entries.flatMap(([,a])=>a).filter(v=>v!==null&&Number.isFinite(v));
  if(!all.length)return;
  let min=Math.min(...all),max=Math.max(...all);const pad=(max-min||1)*.08;min-=pad;max+=pad;
  const xmin=Math.min(...xs),xmax=Math.max(...xs);const X=v=>70+(v-xmin)/(xmax-xmin||1)*700;const Y=v=>320-(v-min)/(max-min)*290;
  function el(tag,attributes,content){const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attributes))e.setAttribute(k,v);if(content!==undefined)e.textContent=content;svg.append(e);return e;}
  for(let i=0;i<=4;i++){const v=min+(max-min)*i/4;el('line',{x1:70,x2:770,y1:Y(v),y2:Y(v),stroke:'#e0e3e5'});el('text',{x:60,y:Y(v)+4,'text-anchor':'end'},format(v));const x=xmin+(xmax-xmin)*i/4;el('text',{x:X(x),y:345,'text-anchor':'middle'},format(x));}
  if(min<0&&max>0)el('line',{x1:70,x2:770,y1:Y(0),y2:Y(0),stroke:'#88939c','stroke-dasharray':'4 4'});
  $('legend').replaceChildren();entries.forEach(([name,ys],i)=>{
    let path='',gap=true;ys.forEach((v,j)=>{if(v===null||!Number.isFinite(v)){gap=true;return;}path+=`${gap?'M':'L'}${X(xs[j])},${Y(v)} `;gap=false;});
    el('path',{d:path,fill:'none',stroke:colors[i%colors.length],'stroke-width':2,'stroke-dasharray':/Lower|Upper/.test(name)?'4 4':''});
    const label=text('span',name);label.style.borderColor=colors[i%colors.length];$('legend').append(label);
  });el('text',{x:420,y:374,'text-anchor':'middle'},result.xlabel||'Observation');
  if(result.ylabel)el('text',{x:70,y:16},result.ylabel);
  $('plot').replaceChildren(svg);
}
function show(result,spec,code) {
  last=result;lastSpec=spec;lastDataset=$('dataset').value;last.dataset=lastDataset;$('output').hidden=false;$('empty').hidden=true;$('error').hidden=true;
  $('stale').hidden=true;
  $('figure-title').textContent=result.title;plot(result);$('interpretation').textContent=result.note;
  $('diagnostics').replaceChildren(table(result.diagnostics));$('warnings').replaceChildren(...result.warnings.map(w=>text('p',w,'lab-warning')));
  $('tables').replaceChildren();for(const [name,values]of Object.entries(result.tables)){
    const detail=document.createElement('details');detail.append(text('summary',name));
    detail.append(Array.isArray(values)?text('pre',JSON.stringify(values,null,2)):table(values));$('tables').append(detail);
  }
  compare();status('Estimation complete. Results were recomputed in browser Python.');
}
function compare() {
  $('comparison').replaceChildren();if(!pinned||!last)return;
  $('comparison').append(text('h3','Specification comparison'),text('p',`Saved: ${pinned.title}. Current: ${last.title}. Compare numerical diagnostics only when the sample, target and likelihood definition agree.`));
  const values={};for(const key of Object.keys(last.diagnostics))if(key in pinned.diagnostics)values[key]=`${format(pinned.diagnostics[key])} → ${format(last.diagnostics[key])}`;
  $('comparison').append(table(values));const d=text('details','');d.append(text('summary','Saved specification'),text('pre',JSON.stringify(pinned.specification,null,2)));$('comparison').append(d);
}
function download(name,content,type='text/plain') {const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('controls').addEventListener('submit',event=>{
  event.preventDefault();if(busy)cancel();busy=true;const id=++runId;const spec=specification();const code=codeFor(spec);
  $('error').hidden=true;$('cancel').hidden=false;$('run').textContent='Rerun';
  if(!worker)worker=new Worker(new URL('./worker.js',import.meta.url),{type:'module'});
  worker.onmessage=({data})=>{if(data.id!==runId)return;if(data.status){status(data.status);return;}busy=false;$('cancel').hidden=true;$('run').textContent='Run specification';
    if(data.error){$('error').textContent=data.error;$('error').hidden=false;status('Estimation could not be completed.');return;}show(data.result,spec,code);};
  worker.onerror=()=>{cancel('The Python worker stopped. Retry to reload it.');$('error').hidden=false;$('error').textContent='A worker resource failed. Check the network connection and retry.';};
  worker.postMessage({id,spec,dataset:metadata[$('dataset').value]});
});
$('cancel').onclick=()=>cancel();$('reset').onclick=()=>selectExercise(exercise.id);
$('chapter').onchange=()=>selectChapter($('chapter').value);$('method').onchange=()=>selectExercise($('method').value);
$('dataset').onchange=()=>{describeData();updateSpec();};$('pin').onclick=()=>{pinned=structuredClone(last);compare();status('Current result retained for comparison.');};
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText($('code').textContent);status('Python specification copied.');}catch{status('Clipboard unavailable; select and copy the displayed code.');}};
$('download-result').onclick=()=>download('macroeconometrics-result.json',JSON.stringify(last,null,2),'application/json');
$('download-code').onclick=async()=>{
  try {
    const spec=specification();const sources=await Promise.all(['core',spec.module].map(async m=>[m,await(await resource(`interactive/python/${m}.py`)).text()]));
    let script='# Interactive Macroeconometrics Lab — generated reproducible implementation\n# Python 3.12; pip install numpy==2.0.2 scipy==1.14.1 pandas==2.2.3 statsmodels==0.14.4 scikit-learn==1.6.1 autograd==1.7.0\nimport sys, types\n';
    for(const [name,source]of sources)script+=`\nmodule = types.ModuleType(${JSON.stringify(name)})\nsys.modules[${JSON.stringify(name)}] = module\nexec(${JSON.stringify(source)}, module.__dict__)\n`;
    script+='\n'+codeFor(spec);download(`${exercise.id}.py`,script);status('Complete Python script downloaded.');
  }catch(error){status(error.message);}
};
try {
  [catalog,metadata]=await Promise.all(['interactive/catalog.json','interactive/data/metadata.json'].map(async path=>(await resource(path)).json()));
  const chapters=[...new Set(catalog.experiments.map(e=>e.chapter))].sort();chapters.forEach(ch=>option($('chapter'),ch,catalog.chapters[ch]));
  const id=new URL(location).searchParams.get('method');const chosen=catalog.experiments.find(e=>e.id===id)||catalog.experiments.find(e=>e.id==='var');
  selectChapter(chosen.chapter,chosen.id,true);
  $('coverage').append(text('p',`${catalog.experiments.length} registered experiments. The catalog records methods, controls, implementation and references. Numerical limits are enforced by Python as well as the interface.`));
  const a=text('a','Inspect the method catalog');a.href=asset('interactive/catalog.json');$('coverage').append(a);
  const b=text('a','Coverage qualifications and advanced implementations');b.href=asset('interactive/scope.html');$('coverage').append(text('p',''),b);
}catch(error){status(error.message);$('error').textContent='The experiment catalog could not be loaded. Reload the page to retry.';$('error').hidden=false;}
