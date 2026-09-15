import {matrixState} from './formulas.js';

const NS='http://www.w3.org/2000/svg';
const C={ink:'#203442',teal:'#087f82',gold:'#a66d16',red:'#b35040',grid:'#dce2dc',muted:'#607177'};
const presets={
  shear:{name:'Shear: add the vertical coordinate',a:[1,1,0,1]},
  identity:{name:'Identity: leave every vector unchanged',a:[1,0,0,1]},
  stretch:{name:'Stretch: double the horizontal coordinate',a:[2,0,0,1]},
  rotation:{name:'Rotation: one quarter-turn anticlockwise',a:[0,-1,1,0]},
  reflection:{name:'Reflection: reverse the horizontal coordinate',a:[-1,0,0,1]},
  singular:{name:'Projection: collapse onto the horizontal axis',a:[1,0,0,0]},
  zero:{name:'Zero map: collapse to the origin',a:[0,0,0,0]}
};
function node(tag,attrs={},text='') {
  const n=document.createElement(tag);
  for(const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v));
  n.textContent=text;return n;
}
function svgNode(tag,attrs={},text='') {
  const n=document.createElementNS(NS,tag);
  for(const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v));
  n.textContent=text;return n;
}
const fmt=x=>(Math.abs(x)<1e-9?0:x).toFixed(2);
const pair=v=>'('+v.map(fmt).join(', ')+')';

function draw(a,t,stacked) {
  const r=matrixState(a,t),height=stacked?760:380,width=stacked?360:720;
  const svg=svgNode('svg',{viewBox:`0 0 ${width} ${height}`,role:'img','aria-labelledby':'matrix-title matrix-desc'});
  svg.append(svgNode('title',{id:'matrix-title'},'A linear map acting on a grid and three vectors'));
  svg.append(svgNode('desc',{id:'matrix-desc'},
    `The left or upper panel is the input. The other panel applies the displayed map. `+
    `At progress ${Math.round(t*100)} percent, the first basis vector ends at ${pair(r.firstColumn)}, `+
    `the second at ${pair(r.secondColumn)}, and their sum at ${pair(r.vector)}. `+
    `The determinant of the displayed map is ${fmt(r.determinant)}.`));
  svg.setAttribute('data-determinant',String(r.determinant));
  const defs=svgNode('defs');
  for(const name of ['teal','gold','red']) {
    const marker=svgNode('marker',{id:'matrix-arrow-'+name,viewBox:'0 0 10 10',refX:9,refY:5,
      markerWidth:7,markerHeight:7,orient:'auto-start-reverse',markerUnits:'userSpaceOnUse'});
    marker.append(svgNode('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:C[name]}));defs.append(marker);
  }
  svg.append(defs);
  // The two panels share units; the scale does not change when progress moves.
  const extent=Math.max(2.5,2*Math.max(Math.abs(a[0])+Math.abs(a[1]),Math.abs(a[2])+Math.abs(a[3]))+.5);
  const scale=145/extent;
  const m=r.matrix;
  const maps=[v=>v,([x,y])=>[m[0]*x+m[1]*y,m[2]*x+m[3]*y]];
  maps.forEach((map,panel)=>{
    const cx=stacked?180:180+360*panel,cy=stacked?185+390*panel:195;
    const point=([x,y])=>[cx+scale*x,cy-scale*y];
    const path=(points,color,strokeWidth=1,dash='')=>{
      const d=points.map((p,i)=>(i?'L':'M')+point(p).join(',')).join(' ');
      svg.append(svgNode('path',{d,fill:'none',stroke:color,'stroke-width':strokeWidth,'stroke-dasharray':dash}));
    };
    svg.append(svgNode('text',{x:cx,y:cy-164,'text-anchor':'middle',fill:C.ink,'font-size':17},
      panel?'Image under the displayed map':'Input coordinates'));
    for(let v=-2;v<=2.001;v+=.5) {
      path([map([v,-2]),map([v,2])],C.grid);
      path([map([-2,v]),map([2,v])],C.grid);
    }
    // Fixed axes make a collapse visible rather than collapsing the reference too.
    path([[-extent,0],[extent,0]],C.muted,1);
    path([[0,-extent],[0,extent]],C.muted,1);
    for(const k of [-2,-1,1,2]) {
      const [px,py]=point([k,0]);
      svg.append(svgNode('text',{x:px,y:py+17,'text-anchor':'middle',fill:C.muted,'font-size':12},String(k)));
    }
    const square=[[0,0],[1,0],[1,1],[0,1]].map(map);
    svg.append(svgNode('polygon',{points:square.map(p=>point(p).join(',')).join(' '),
      fill:C.teal,'fill-opacity':.12,stroke:C.teal,'stroke-width':1.5}));
    for(const [v,name,dash] of [[[1,1],'red','5 3'],[[1,0],'teal',''],[[0,1],'gold','']]) {
      const end=map(v),[px,py]=point(end);
      if(Math.hypot(...end)<1e-8) svg.append(svgNode('circle',{cx,cy,r:4,fill:C[name]}));
      else svg.append(svgNode('line',{x1:cx,y1:cy,x2:px,y2:py,stroke:C[name],
        'stroke-width':2.7,'stroke-dasharray':dash,'marker-end':'url(#matrix-arrow-'+name+')'}));
    }
    svg.append(svgNode('text',{x:cx,y:cy+167,'text-anchor':'middle',fill:C.muted,'font-size':13},
      panel?'Same coordinate scale as the input':'Shaded square: area 1'));
  });
  return [svg,r];
}

export function mountMatrixExplorer(box) {
  const presetLabel=node('label',{for:'matrix-preset'},'Start with a transformation');
  const select=node('select',{id:'matrix-preset'});
  for(const [key,p] of Object.entries(presets)) select.append(node('option',{value:key},p.name));
  select.append(node('option',{value:'custom'},'Custom matrix'));
  const fieldset=node('fieldset',{class:'matrix-entry'});
  fieldset.append(node('legend',{},'Target matrix A (row first, column second)'));
  const entries=node('div',{class:'matrix-coefficients'}),inputs=[];
  for(let i=0;i<4;i++) {
    const row=Math.floor(i/2)+1,col=i%2+1,id=`matrix-a${row}${col}`;
    const wrap=node('div');
    wrap.append(node('label',{for:id},'a'+['₁','₂'][row-1]+['₁','₂'][col-1]));
    const input=node('input',{id,type:'number',min:-2,max:2,step:.1,
      'aria-label':`Row ${row}, column ${col}`,'aria-describedby':'matrix-input-help'});
    wrap.append(input);entries.append(wrap);inputs.push(input);
  }
  fieldset.append(entries,node('p',{id:'matrix-input-help'},
    'Each coefficient can vary from −2 to 2. Column 1 gives Ae₁; column 2 gives Ae₂.'));
  const controls=node('div',{class:'math-controls'});
  const slider=node('input',{id:'matrix-progress',type:'range',min:0,max:1,step:.01,value:1,
    'aria-describedby':'matrix-progress-help matrix-explanation'});
  const output=node('output',{for:slider.id});
  controls.append(node('label',{for:slider.id},'Apply the transformation'),output,slider);
  const help=node('p',{id:'matrix-progress-help',class:'matrix-help'},
    'At 0% the map is the identity; at 100% it is A. In between, the displayed map is (1 − t)I + tA. '+
    'This is a linear interpolation of matrices, not repeated multiplication. A rotation preset need not remain a rotation in between.');
  const plot=node('div'),legend=node('div',{class:'math-legend'});
  for(const [text,color] of [['First basis vector e₁',C.teal],['Second basis vector e₂',C.gold],['Sum x = e₁ + e₂ (dashed)',C.red]]) {
    const item=node('span',{},text);item.style.setProperty('--series',color);legend.append(item);
  }
  const explanation=node('p',{id:'matrix-explanation',class:'math-explanation','aria-live':'polite'});
  const actions=node('div',{class:'math-actions'});
  const reset=node('button',{type:'button'},'Reset');
  const download=node('button',{type:'button'},'Download figure (SVG)');actions.append(reset,download);
  box.append(presetLabel,select,fieldset,controls,help,plot,legend,explanation,actions);
  const narrow=matchMedia('(max-width: 600px)');
  function update() {
    const a=inputs.map(input=>input.valueAsNumber);
    if(!a.every(Number.isFinite) || !inputs.every(input=>input.checkValidity())) {
      explanation.textContent='Enter four numbers from −2 to 2 in steps of 0.1. The last valid figure is retained.';
      return;
    }
    const t=Number(slider.value),[svg,r]=draw(a,t,narrow.matches);
    plot.replaceChildren(svg);output.value=Math.round(t*100)+'%';
    const singular=Math.abs(r.determinant)<1e-9;
    const zero=r.matrix.every(v=>Math.abs(v)<1e-9);
    explanation.textContent=`Displayed columns: ${pair(r.firstColumn)} and ${pair(r.secondColumn)}. `+
      `Their sum is the image of x: ${pair(r.vector)}. `+
      `det A = ${fmt(r.targetDeterminant)}; determinant at this stage = ${fmt(r.determinant)}. `+
      (zero?'All vectors collapse to zero. No direction can be recovered.':
       singular?'The columns are dependent: the plane collapses onto a line. The map is not invertible.':
       `The columns are independent. Areas are multiplied by ${fmt(Math.abs(r.determinant))}; `+
       (r.determinant<0?'orientation is reversed.':'orientation is preserved.'));
    download.disabled=false;
  }
  function setPreset(key) {
    if(!presets[key]) return;
    presets[key].a.forEach((v,i)=>inputs[i].value=v);select.value=key;slider.value=1;update();
  }
  select.addEventListener('change',()=>setPreset(select.value));
  for(const input of inputs) input.addEventListener('input',()=>{select.value='custom';update();});
  slider.addEventListener('input',update);narrow.addEventListener('change',update);
  reset.addEventListener('click',()=>setPreset('shear'));
  download.addEventListener('click',()=>{
    const svg=plot.querySelector('svg').cloneNode(true);svg.setAttribute('xmlns',NS);
    svg.setAttribute('style','font:17px sans-serif;background:#f8f6f0');
    const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));
    const a=node('a',{href:url,download:'mathematics-matrix.svg'});a.click();
    setTimeout(()=>URL.revokeObjectURL(url),5000);
  });
  setPreset('shear');
}
