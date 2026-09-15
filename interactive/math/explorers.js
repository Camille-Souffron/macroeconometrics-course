import {taylor,cap,descent,posterior,normal} from "./formulas.js";
import {mountMatrixExplorer} from "./matrix.js";

for(const box of document.querySelectorAll('[data-math="matrix"]')) mountMatrixExplorer(box);

const NS="http://www.w3.org/2000/svg";
const C={ink:"#203442",teal:"#087f82",gold:"#a66d16",red:"#b35040",grid:"#dce2dc",muted:"#607177"};
function el(tag,attrs={},text="") {
  const n=document.createElementNS(NS,tag);
  for(const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v));
  if(text) n.textContent=text;
  return n;
}
function graph(kind,title,xlim,ylim,xlabel,ylabel) {
  const svg=el("svg",{viewBox:"0 0 720 370",role:"img","aria-labelledby":kind+"-title"});
  svg.append(el("title",{id:kind+"-title"},title));
  const x=v=>62+(v-xlim[0])/(xlim[1]-xlim[0])*624;
  const y=v=>310-(v-ylim[0])/(ylim[1]-ylim[0])*280;
  const defs=el("defs"),clip=el("clipPath",{id:"clip-"+kind});
  clip.append(el("rect",{x:62,y:30,width:624,height:280})); defs.append(clip); svg.append(defs);
  for(let i=0;i<=4;i++) {
    const xv=xlim[0]+i*(xlim[1]-xlim[0])/4, yv=ylim[0]+i*(ylim[1]-ylim[0])/4;
    svg.append(el("line",{x1:x(xv),x2:x(xv),y1:30,y2:310,stroke:C.grid}));
    svg.append(el("line",{x1:62,x2:686,y1:y(yv),y2:y(yv),stroke:C.grid}));
    svg.append(el("text",{x:x(xv),y:337,"text-anchor":"middle",fill:C.muted},Number(xv.toFixed(2)).toString()));
    svg.append(el("text",{x:51,y:y(yv)+6,"text-anchor":"end",fill:C.muted},Number(yv.toFixed(2)).toString()));
  }
  svg.append(el("text",{x:374,y:365,"text-anchor":"middle",fill:C.ink},xlabel));
  svg.append(el("text",{x:62,y:20,fill:C.ink},ylabel));
  const data=el("g",{"clip-path":"url(#clip-"+kind+")"}); svg.append(data);
  return {
    svg,x,y,
    line(points,color,width=3,dash="") {
      data.append(el("path",{d:points.map((p,i)=>(i?"L":"M")+x(p[0]).toFixed(3)+","+y(p[1]).toFixed(3)).join(" "),
        fill:"none",stroke:color,"stroke-width":width,"stroke-dasharray":dash,"stroke-linejoin":"round"}));
    },
    curve(f,color,range=xlim,dash="") {
      this.line(Array.from({length:241},(_,i)=>{const v=range[0]+(range[1]-range[0])*i/240;return [v,f(v)];}),color,3,dash);
    },
    dot(a,b,color,r=6) { data.append(el("circle",{cx:x(a),cy:y(b),r,fill:color,stroke:"#fff","stroke-width":1.5})); },
    text(a,b,t,color=C.ink) { svg.append(el("text",{x:x(a),y:y(b),fill:color,"text-anchor":"middle"},t)); }
  };
}
const specs={
  taylor:{label:"Proportional growth g",min:-.7,max:.7,step:.01,value:.1,
    legend:[["Exact log",C.teal],["Tangent",C.gold],["Quadratic",C.red]],
    draw(g) {
      const p=graph("taylor","Log growth and its Taylor approximations",[-.75,.75],[-1.5,1],"proportional growth g","log change");
      p.curve(Math.log1p,C.teal); p.curve(x=>x,C.gold,undefined,"8 5");p.curve(x=>x-x*x/2,C.red,undefined,"3 4");
      const r=taylor(g);
      p.line([[g,-1.5],[g,1]],C.muted,1,"4 4");
      p.dot(g,r.exact,C.teal);p.dot(g,r.linear,C.gold,4);p.dot(g,r.quadratic,C.red,4);
      return [p,"Exact: "+r.exact.toFixed(6)+". Tangent: "+r.linear.toFixed(6)+". Quadratic: "+r.quadratic.toFixed(6)+
        ". Absolute quadratic error: "+Math.abs(r.exact-r.quadratic).toExponential(3)+
        "; remainder bound with r = |g|: "+r.bound.toExponential(3)+"."];
    }},
  kkt:{label:"Upper bound b",min:-.5,max:2,step:.025,value:.5,
    legend:[["Loss ½(x − 1)²",C.teal],["Cap b",C.gold],["Optimum",C.red]],
    draw(b) {
      const p=graph("kkt","A constrained quadratic minimum",[-1,2],[0,2],"choice x","loss");
      p.curve(x=>.5*(x-1)**2,C.teal);
      p.line([[b,0],[b,2]],C.gold,2,"7 4");
      const r=cap(b);p.dot(r.x,r.value,C.red);
      p.text(-.48,1.8,"feasible: x ≤ b",C.muted);
      return [p,"x* = "+r.x.toFixed(3)+", μ = "+r.mu.toFixed(3)+", v(b) = "+r.value.toFixed(4)+". "+
        (b<1?"The cap binds; relaxing it lowers the loss.":b===1?"The cap binds with multiplier zero.":"The cap is slack and its multiplier is zero.")+
        " Stationarity: x* − 1 + μ = "+(r.x-1+r.mu).toFixed(2)+
        ". Value derivative: v′(b) = "+(r.mu===0?0:-r.mu).toFixed(3)+"."];
    }},
  descent:{label:"Step size η",min:.05,max:.65,step:.025,value:.2,
    legend:[["Iterates",C.teal],["Start",C.gold]],
    draw(eta) {
      const points=descent(eta);
      const p=graph("descent","Gradient descent on an anisotropic quadratic",[-2,2],[-2,2],"x","y");
      for(const level of [.1,.5,1,2,4]) p.line(Array.from({length:121},(_,i)=>{const t=2*Math.PI*i/120;return [Math.sqrt(2*level)*Math.cos(t),Math.sqrt(level/2)*Math.sin(t)];}),C.grid,1.5);
      p.line(points,C.teal,2); points.forEach(([x,y],i)=>p.dot(x,y,i?C.teal:C.gold,i?3:6));
      const last=points.at(-1); const f=.5*(last[0]**2+4*last[1]**2);
      return [p,"After 12 steps: loss = "+f.toPrecision(4)+" (initial loss 3.125). "+
        (eta<.5?"Both coordinate multipliers have modulus below one; the iterates converge.":Math.abs(eta-.5)<1e-9?
          "The y coordinate alternates between +1 and −1 without decay.":
          "The y coordinate grows in magnitude. The fixed viewing window clips the escaping iterates; it does not rescale to hide divergence.")];
    }},
  bayes:{label:"Number of observations n",min:0,max:40,step:1,value:4,
    legend:[["Prior N(0,1)",C.gold],["Posterior",C.teal]],
    draw(n) {
      const r=posterior(n),p=graph("bayes","Normal prior and conjugate posterior",[-3,3],[0,1.5],"parameter θ","density");
      p.curve(x=>normal(x,0,1),C.gold,undefined,"7 4");
      p.curve(x=>normal(x,r.mean,r.sd),C.teal);
      p.line([[1,0],[1,1.5]],C.muted,1,"3 4");
      return [p,"Posterior mean: "+r.mean.toFixed(3)+". Variance: "+r.variance.toFixed(4)+
        ". Standard deviation: "+r.sd.toFixed(3)+". "+
        (n===0?"With no observations, the posterior equals the prior.":
          "The dashed vertical line is the fixed sample mean, one. More observations increase its precision relative to the prior.")+
        " Both densities integrate to one over the real line; the graph shows a finite window."];
    }}
};

for(const box of document.querySelectorAll("[data-math]")) {
  const kind=box.dataset.math,spec=specs[kind];
  if(!spec) continue;
  const controls=document.createElement("div");controls.className="math-controls";
  const lab=document.createElement("label");lab.htmlFor="math-"+kind;lab.textContent=spec.label;
  const input=document.createElement("input");input.type="range";input.id=lab.htmlFor;
  for(const k of ["min","max","step","value"]) input[k]=spec[k];
  const out=document.createElement("output");out.htmlFor=input.id;
  controls.append(lab,out,input);
  const plot=document.createElement("div"),legend=document.createElement("div");
  legend.className="math-legend";
  for(const [name,color] of spec.legend) {
    const item=document.createElement("span");item.textContent=name;item.style.setProperty("--series",color);legend.append(item);
  }
  const explanation=document.createElement("p");explanation.className="math-explanation";
  explanation.id="math-"+kind+"-explanation";explanation.setAttribute("aria-live","polite");
  input.setAttribute("aria-describedby",explanation.id);
  const actions=document.createElement("div");actions.className="math-actions";
  const reset=document.createElement("button");reset.type="button";reset.textContent="Reset";
  const download=document.createElement("button");download.type="button";download.textContent="Download figure (SVG)";
  actions.append(reset,download); box.append(controls,plot,legend,explanation,actions);
  function update() {
    const value=Number(input.value);out.value=kind==="bayes"?String(value):value.toFixed(3);
    const [p,text]=spec.draw(value);plot.replaceChildren(p.svg);explanation.textContent=text;
  }
  input.addEventListener("input",update);
  reset.addEventListener("click",()=>{input.value=spec.value;update();});
  download.addEventListener("click",()=>{
    const svg=plot.querySelector("svg").cloneNode(true);svg.setAttribute("xmlns",NS);
    svg.setAttribute("style","font:17px sans-serif;background:#f8f6f0");
    const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:"image/svg+xml"}));
    const a=document.createElement("a");a.href=url;a.download="mathematics-"+kind+".svg";a.click();
    setTimeout(()=>URL.revokeObjectURL(url),5000);
  });
  update();
}
// Never start motion automatically. Pause videos that leave the reading area.
const observer=new IntersectionObserver(entries=>{
  for(const entry of entries) if(!entry.isIntersecting) entry.target.pause();
});
for(const video of document.querySelectorAll(".math-film video")) {
  observer.observe(video);
  const still=document.createElement("img");still.src=video.poster;still.alt=video.getAttribute("aria-label");
  still.className="math-print-poster";still.loading="lazy";video.after(still);
}
