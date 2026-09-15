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

// The progress parameter interpolates maps, not powers or elapsed model time.
export function matrixState(a, progress=1) {
  if(a.length!==4 || !a.every(Number.isFinite) || !Number.isFinite(progress))
    throw new TypeError("Four finite coefficients and a finite progress value are required.");
  const [a11,a12,a21,a22]=a;
  const m=[1+progress*(a11-1),progress*a12,progress*a21,1+progress*(a22-1)];
  const apply=([x,y])=>[m[0]*x+m[1]*y,m[2]*x+m[3]*y];
  return {matrix:m,determinant:m[0]*m[3]-m[1]*m[2],
    targetDeterminant:a11*a22-a12*a21,
    firstColumn:apply([1,0]),secondColumn:apply([0,1]),vector:apply([1,1]),
    square:[[0,0],[1,0],[1,1],[0,1]].map(apply)};
}
