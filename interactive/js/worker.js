// One runtime per open lab. The UI terminates this worker to cancel CPU-bound work.
const BASE = new URL('../', import.meta.url);
const CDN = 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/';
let runtime;
const loaded = new Set();
const datasets = new Map();
async function fetchText(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Resource unavailable (${response.status}). Please retry.`);
  return response.text();
}
self.onmessage = async ({data: {id, spec, dataset}}) => {
  const status = message => self.postMessage({id, status: message});
  try {
    if (!runtime) {
      status('Loading Python 3.12 / Pyodide 0.27.7…');
      const {loadPyodide} = await import(`${CDN}pyodide.mjs`);
      runtime = await loadPyodide({indexURL: CDN});
    }
    status('Loading the scientific packages needed for this method…');
    const packages = ['numpy','scipy','pandas'];
    if (['linear','spectral','structural','nonlinear','foundations','instruments'].includes(spec.module)) packages.push('statsmodels');
    if (spec.module === 'learning') packages.push('scikit-learn');
    if (spec.module === 'sequence') packages.push('autograd');
    const packageErrors = [];
    await runtime.loadPackage(packages, {errorCallback: message => packageErrors.push(message)});
    if (packageErrors.length) {
      status('Retrying a scientific package download…');
      const retryErrors = [];
      await runtime.loadPackage(packages, {errorCallback: message => retryErrors.push(message)});
      if (retryErrors.length) throw new Error('A scientific package download failed. Retry on a connection that permits the Pyodide CDN.');
    }
    // loadPackage may report download failures through callbacks, not rejection.
    await runtime.runPythonAsync('import numpy, scipy, pandas' + (packages.includes('statsmodels') ? ', statsmodels' : '') + (packages.includes('scikit-learn') ? ', sklearn' : '') + (packages.includes('autograd') ? ', autograd' : ''));
    for (const module of ['core', spec.module]) {
      if (!loaded.has(module)) {
        runtime.FS.writeFile(`/home/pyodide/${module}.py`, await fetchText(new URL(`python/${module}.py`, BASE)));
        loaded.add(module);
      }
    }
    const url = new URL(dataset.path, new URL('../../', import.meta.url)).href;
    if (!datasets.has(url)) datasets.set(url, await fetchText(url));
    runtime.globals.set('csv_text', datasets.get(url));
    let joined = '';
    if (dataset.join) {
      const joinURL = new URL(dataset.join, new URL('../../', import.meta.url)).href;
      if (!datasets.has(joinURL)) datasets.set(joinURL, await fetchText(joinURL));
      joined = datasets.get(joinURL);
    }
    runtime.globals.set('join_text', joined);
    runtime.globals.set('spec_text', JSON.stringify(spec));
    status('Estimating in Python…');
    const payload = await runtime.runPythonAsync(`
import io, json, pandas as pd
from core import run_json
frame = pd.read_csv(io.StringIO(csv_text))
if join_text:
    frame = frame.merge(pd.read_csv(io.StringIO(join_text)), on='date', how='inner', validate='one_to_one')
run_json(frame, json.loads(spec_text))
`);
    self.postMessage({id, ...JSON.parse(payload)});
  } catch (error) {
    self.postMessage({id, error: 'Python or a required resource could not be loaded. Check your connection and retry. ' + String(error.message).split('\n')[0]});
  }
};
