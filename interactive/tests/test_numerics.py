import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'interactive/python'))
from core import run, EconometricError

CATALOG=json.loads((ROOT/'interactive/catalog.json').read_text())

def data(experiment):
    metadata=json.loads((ROOT/'interactive/data/metadata.json').read_text())
    record=metadata[experiment['datasets'][0]]
    frame=pd.read_csv(ROOT/record['path'])
    if record.get('join'):frame=frame.merge(pd.read_csv(ROOT/record['join']),on='date',validate='one_to_one')
    return frame

@pytest.mark.parametrize('experiment',CATALOG['experiments'],ids=lambda e:e['id'])
def test_canonical_specification(experiment):
    spec=dict(module=experiment['module'],method=experiment['method'],**experiment['defaults'])
    output=run(data(experiment),spec)
    assert output['curves']
    assert all(len(v)==len(output['x']) for v in output['curves'].values())
    assert all(np.isfinite(v).all() for v in output['curves'].values())
    json.dumps(output,allow_nan=False)

def test_ols_matches_lstsq():
    from core import ols
    rng=np.random.default_rng(27);x=rng.normal(size=(100,4));y=rng.normal(size=(100,2))
    b,e=ols(y,x)
    np.testing.assert_allclose(x.T@e,0,atol=1e-12)
    np.testing.assert_allclose(b,np.linalg.lstsq(x,y,rcond=None)[0])

def test_quantile_lp_matches_statsmodels():
    from distribution import quantile_fit
    from statsmodels.regression.quantile_regression import QuantReg
    rng=np.random.default_rng(7);x=np.column_stack([np.ones(150),rng.normal(size=150)]);y=x@np.array([1.,2.])+rng.normal(size=150)
    np.testing.assert_allclose(quantile_fit(x,y,.25),QuantReg(y,x).fit(q=.25,max_iter=5000).params,atol=1e-3)

def test_identification_reconstructs_covariance():
    from structural import identify
    from statsmodels.tsa.api import VAR
    rng=np.random.default_rng(2026);y=rng.normal(size=(300,3));fit=VAR(y).fit(2)
    for scheme in ['recursive','long_run','short_run','max_share']:
        b,_,_=identify(fit,{'identification':scheme,'horizon':8},rng)
        np.testing.assert_allclose(b@b.T,fit.sigma_u,atol=1e-6)
        if scheme=='long_run':
            long=np.linalg.solve(np.eye(3)-fit.coefs.sum(axis=0),b)
            np.testing.assert_allclose(long[np.triu_indices(3,1)],0,atol=1e-12)

def test_invalid_log_and_short_sample():
    from core import series,design
    with pytest.raises(EconometricError,match='positive'):series(pd.DataFrame({'x':[-1]*60}),{'transform':'log'},['x'])
    with pytest.raises(EconometricError,match='Too few'):design(np.ones((20,3)),4)

def test_empty_threshold_regime():
    experiment=next(e for e in CATALOG['experiments'] if e['id']=='tar')
    with pytest.raises(EconometricError,match='regime'):run(data(experiment),{'module':'nonlinear','method':'tar',**experiment['defaults'],'threshold':1e9})

def test_bvar_reproducible():
    from bayesian import bvar_draws
    y=np.random.default_rng(11).normal(size=(100,2))
    a=bvar_draws(y,1,'normal_wishart',.2,2,0,30,10,42)
    b=bvar_draws(y,1,'normal_wishart',.2,2,0,30,10,42)
    np.testing.assert_array_equal(a[0],b[0])

@pytest.mark.parametrize('trend,expected_gls,expected_pp',[
    ('c',-1.2910543210073064,-3.0831563767665937),
    ('ct',-1.9073657018086168,-3.3085698560477397),
])
def test_unit_root_statistics_against_arch_720(trend,expected_gls,expected_pp):
    # Independently verified against arch 7.2.0 DFGLS and PhillipsPerron.
    from foundations import dfgls,estimate
    y=np.cumsum(np.random.default_rng(108).normal(size=150))
    np.testing.assert_allclose(dfgls(y,2,trend),expected_gls,rtol=1e-10)
    out=estimate(pd.DataFrame({'GDPC1':y}),{'method':'unit_roots','lags':2,'bandwidth':8,'deterministic':trend,'draws':99})
    np.testing.assert_allclose(out['diagnostics']['Phillips–Perron τ'],expected_pp,rtol=1e-10)

def test_nuts_targets_the_analytical_posterior():
    from bayesian import samplers
    y=np.random.default_rng(123).normal(size=160)
    out=samplers(y,{'sampler':'nuts','draws':2000,'burn':300,'seed':7})
    d=out['diagnostics']
    assert abs(d['Computed mean']-d['Analytical posterior mean'])<.1*d['Analytical posterior SD']
    assert abs(d['Computed SD']/d['Analytical posterior SD']-1)<.1
