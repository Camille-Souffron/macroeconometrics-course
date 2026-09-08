"""Exercise alternative econometric paths, not just default screenshots."""
import numpy as np
import pytest
from test_numerics import CATALOG,data
from core import run,EconometricError

CASES=[
    ('arma',{'lags':0,'ma_order':1}),('arma',{'ma_order':0,'estimator':'yule_walker'}),
    ('arma',{'ma_order':0,'estimator':'burg'}),('arma',{'estimator':'innovations_mle'}),
    ('arma',{'estimator':'hannan_rissanen'}),('arma',{'difference_order':1,'deterministic':'n'}),
    *[('filters',{'filter':name}) for name in ['bk','cf','hamilton','difference']],
    ('var',{'output':'forecast'}),('var',{'output':'fevd'}),('var',{'identification':'recursive'}),
    *[('svar',{'identification':name}) for name in ['short_run','long_run','sign','heteroskedastic','max_share']],
    ('svar',{'output':'historical'}),('svar',{'output':'fevd'}),('svar',{'cumulative':True}),
    ('vecm',{'rank':0}),('vecm',{'deterministic':'n'}),
    *[('panel',{'estimator':name}) for name in ['mean_group','difference_gmm','system_gmm','hierarchical','gvar']],
    ('tar',{'output':'girf','draws':40}),('star',{'output':'girf','draws':40}),
    ('gar',{'evaluate':True,'draws':0,'quantile':.1}),
    ('distribution-regression',{'evaluate':True}),
    *[('ml',{'learner':name,'evaluation_step':8}) for name in ['lasso','elastic_net','tree','forest','boosting','quantile_boosting','mlp']],
    ('ml',{'validation':'chronological','window_type':'rolling','evaluation_step':8}),
    *[('sequence',{'architecture':name,'epochs':10}) for name in ['lstm','tcn','transformer']],
    ('sequence',{'loss':'quantile','epochs':10}),
    *[('bvar',{'prior':name,'draws':40}) for name in ['minnesota','independent','normal_diffuse']],
    ('bvar',{'output':'irf','draws':40}),
    ('tvp-sv',{'time_coefficients':False,'vol_persistence':.95,'outlier_probability':.05,'draws':20,'burn':10}),
    *[('samplers',{'sampler':name,'draws':100,'burn':50}) for name in ['mh','nuts','variational']],
    *[('sampling',{'population':name}) for name in ['normal','student','bernoulli','poisson','exponential','chi_square','fisher']],
]

@pytest.mark.parametrize('identifier,overrides',CASES)
def test_alternative_estimator_paths(identifier,overrides):
    e=next(e for e in CATALOG['experiments'] if e['id']==identifier)
    output=run(data(e),{'module':e['module'],'method':e['method'],**e['defaults'],**overrides})
    assert all(np.isfinite(v).all() for v in output['curves'].values())

def test_fevd_sums_to_one():
    e=next(e for e in CATALOG['experiments'] if e['id']=='svar')
    output=run(data(e),{'module':'structural','method':'svar',**e['defaults'],'output':'fevd'})
    np.testing.assert_allclose(np.sum(list(output['curves'].values()),axis=0),1,atol=1e-12)

def test_invalid_sign_order_is_not_silently_relabelled():
    e=next(e for e in CATALOG['experiments'] if e['id']=='svar')
    with pytest.raises(EconometricError,match='order'):
        run(data(e),{'module':'structural','method':'svar',**e['defaults'],'identification':'sign','variables':'policy_rate,gdp_growth,inflation'})

def test_sample_dates_are_applied_before_lags():
    e=next(e for e in CATALOG['experiments'] if e['id']=='var')
    frame=data(e);spec={'module':'linear','method':'var',**e['defaults']}
    a=run(frame,{**spec,'sample_start':'1980-01-01','sample_end':'2010-01-01'})
    b=run(frame.loc[(frame.date>='1980-01-01')&(frame.date<='2010-01-01')],spec)
    assert a['diagnostics']==b['diagnostics']


def test_crps_against_uniform_distribution():
    from distribution import cdf_scores
    scores,pits=cdf_scores(np.array([0.,1.]),np.array([[0.,1.]]*3),[.5,2.,-.5])
    np.testing.assert_allclose(scores,[1/12,4/3,5/6],atol=1e-12)
    np.testing.assert_allclose(pits,[.5,1,0])
