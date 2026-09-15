// Pure calculations: checked in a real browser against independent fixtures.
export function taylor(g) {
  return { exact: Math.log1p(g), linear: g, quadratic: g-g*g/2,
    bound: Math.abs(g)**3/(3*(1-Math.abs(g))**3) };
}
export function cap(b) {
  const x = Math.min(1,b);
  return { x, mu: Math.max(1-b,0), value: .5*(x-1)**2 };
}
export function descent(eta, steps=12) {
  let x=1.5, y=1;
  const points=[[x,y]];
  for (let k=0;k<steps;k++) { x*=1-eta; y*=1-4*eta; points.push([x,y]); }
  return points;
}
export function posterior(n) {
  const variance=1/(1+n/4);
  return { mean: n/4*variance, variance, sd: Math.sqrt(variance) };
}
export function normal(x,mean,sd) {
  return Math.exp(-.5*((x-mean)/sd)**2)/(sd*Math.sqrt(2*Math.PI));
}
