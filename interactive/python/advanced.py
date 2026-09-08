"""Optional desktop implementations for capabilities outside the browser budget.

These never run during Quarto rendering. See scope.json for qualifications.
Example: python advanced.py bayesian --csv ../../data/us_ml_time_series_fred.csv
"""
import argparse
import numpy as np
import pandas as pd


def full_tvp_sv(frame, variables, lags=1, draws=1000, tune=1000, seed=2026,
                time_coefficients=True, time_covariance=True, outliers=False,
                stochastic_volatility=True, sampler='nuts', build_only=False):
    """Triangular full-covariance TVP-SV, learned state scales, optional outlier mixture.

    A_t u_t = diag(exp(h_t/2)) e_t, diag(A_t)=1. State increments
    are independent Normal with learned HalfNormal scales. This is a specified
    pedagogical TVP-SV posterior, not a claim to reproduce Primiceri's priors.
    """
    import pymc as pm
    import pytensor.tensor as pt
    values=frame[variables].dropna().to_numpy(float)
    scale=values.std(axis=0);values=(values-values.mean(axis=0))/scale
    n0,k=values.shape;n=n0-lags
    if n<=k*lags+20:raise ValueError('Insufficient observations for TVP-SV.')
    x=np.column_stack([np.ones(n)]+[values[lags-j:n0-j] for j in range(1,lags+1)])
    y=values[lags:];d=x.shape[1]
    with pm.Model() as model:
        beta0=pm.Normal('beta0',0,.5,shape=(d,k))
        if time_coefficients:
            q=pm.HalfNormal('coefficient_state_sd',.03,shape=(d,k))
            increments=pm.Normal('coefficient_increments',0,1,shape=(n-1,d,k))*q
            beta=pt.concatenate([beta0[None,:,:],beta0[None,:,:]+pt.cumsum(increments,axis=0)],axis=0)
            mu=pt.sum(x[:,:,None]*beta,axis=1)
        else:mu=pt.dot(x,beta0)
        h0=pm.Normal('log_variance0',-1,1,shape=k)
        if stochastic_volatility:
            state_sd=pm.HalfNormal('log_variance_state_sd',.15,shape=k)
            innovation=pm.Normal('log_variance_increments',0,1,shape=(n-1,k))*state_sd
            logvar=pt.concatenate([h0[None,:],h0[None,:]+pt.cumsum(innovation,axis=0)],axis=0)
        else:logvar=pt.broadcast_to(h0,(n,k))
        residual=y-mu;structural=[]
        for equation in range(k):
            if equation==0:structural.append(residual[:,0]);continue
            a0=pm.Normal(f'impact_row_{equation}',0,.5,shape=equation)
            if time_covariance:
                sd=pm.HalfNormal(f'impact_state_sd_{equation}',.03,shape=equation)
                innovation=pm.Normal(f'impact_increments_{equation}',0,1,shape=(n-1,equation))*sd
                path=pt.concatenate([a0[None,:],a0[None,:]+pt.cumsum(innovation,axis=0)],axis=0)
            else:path=pt.broadcast_to(a0,(n,equation))
            structural.append(residual[:,equation]+pt.sum(path*residual[:,:equation],axis=1))
        transformed=pt.stack(structural,axis=1);sd=pt.exp(logvar/2)
        normal_logp=pm.logp(pm.Normal.dist(0,sd),transformed)
        if outliers:
            probability=pm.Beta('outlier_probability',1,19)
            multiplier=1+pm.HalfNormal('outlier_scale_increment',5)
            outlier_logp=pm.logp(pm.Normal.dist(0,sd*multiplier),transformed)
            likelihood=pt.logaddexp(pt.log1p(-probability)+normal_logp,pt.log(probability)+outlier_logp)
        else:likelihood=normal_logp
        # Unit determinant of the triangular transformation needs no Jacobian correction.
        pm.Potential('conditional_likelihood',pt.sum(likelihood))
        pm.Deterministic('innovation_sd',sd)
        if build_only:return model
        if sampler=='variational':return pm.fit(n=20000,method='advi',random_seed=seed).sample(draws=draws)
        step=pm.HamiltonianMC() if sampler=='hmc' else None
        return pm.sample(draws=draws,tune=tune,chains=4,cores=1,step=step,random_seed=seed,
                         **({'target_accept':.95} if step is None else {}))


def mixed_frequency(monthly,quarterly,factors=1,factor_order=1):
    """Native-frequency Gaussian DFM with EM and quarterly aggregation restrictions.

    Pass stationary monthly indicators and quarterly growth, indexed by PeriodIndex
    with M and Q frequencies. Missing observations remain NaN; do not interpolate.
    A vintage-specific monthly panel is intentionally a required input.
    """
    from statsmodels.tsa.statespace.dynamic_factor_mq import DynamicFactorMQ
    if not isinstance(monthly.index,pd.PeriodIndex) or monthly.index.freqstr!='M':
        raise ValueError('Monthly indicators require a monthly PeriodIndex.')
    if not isinstance(quarterly.index,pd.PeriodIndex) or not quarterly.index.freqstr.startswith('Q'):
        raise ValueError('Quarterly growth requires a quarterly PeriodIndex.')
    model=DynamicFactorMQ(monthly,endog_quarterly=quarterly,factors=factors,factor_orders=factor_order,standardize=True)
    return model.fit_em(maxiter=500,disp=False)


def pretrained_forecast(series,revision,horizon=8,seed=2026):
    """Real pretrained Chronos inference; explicitly pinned model revision required.

    pip install chronos-forecasting torch
    PyTorch and the model checkpoint are not part of the Pyodide distribution.
    """
    import torch
    from chronos import ChronosPipeline
    if not revision:raise ValueError('Provide a model commit revision for reproducibility.')
    torch.manual_seed(seed)
    model=ChronosPipeline.from_pretrained('amazon/chronos-t5-tiny',revision=revision,device_map='cpu',torch_dtype=torch.float32)
    draws=model.predict(torch.tensor(np.asarray(series),dtype=torch.float32),prediction_length=horizon,num_samples=100)
    return np.quantile(draws[0].numpy(),[.05,.5,.95],axis=0)


def climate_quantiles(frame,outcome,physical,transition,controls,unit,time,tau=.05):
    """Observed climate covariates with unit effects; no fabricated climate proxy.

    This is a pooled quantile regression with unit dummies, not a claim of causal
    climate identification. Short panels entail incidental-parameter concerns.
    """
    from statsmodels.regression.quantile_regression import QuantReg
    selected=frame.sort_values([unit,time]).dropna(subset=[outcome,physical,transition]+controls)
    regressors=pd.concat([selected[[physical,transition]+controls],pd.get_dummies(selected[unit],drop_first=True,dtype=float)],axis=1)
    x=np.column_stack([np.ones(len(selected)),regressors.to_numpy(float)])
    if len(selected)*min(tau,1-tau)<10:raise ValueError('Too few effective tail observations.')
    return QuantReg(selected[outcome].to_numpy(float),x).fit(q=tau,max_iter=10000)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('method',choices=['bayesian','foundation'])
    parser.add_argument('--csv',required=True)
    parser.add_argument('--variables',default='gdp_growth,inflation,policy_rate')
    parser.add_argument('--draws',type=int,default=1000)
    parser.add_argument('--tune',type=int,default=1000)
    parser.add_argument('--revision',help='Required model commit revision for pretrained inference')
    parser.add_argument('--outliers',action='store_true')
    parser.add_argument('--output',default='posterior.nc')
    args=parser.parse_args();frame=pd.read_csv(args.csv);variables=args.variables.split(',')
    if args.method=='bayesian':full_tvp_sv(frame,variables,draws=args.draws,tune=args.tune,outliers=args.outliers).to_netcdf(args.output)
    else:print(pretrained_forecast(frame[variables[0]].dropna(),args.revision))
