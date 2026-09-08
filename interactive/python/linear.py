"""Classical time-series estimation using statsmodels."""
import numpy as np
from core import series, result, require, design, ols


def estimate(frame, s):
    from statsmodels.tsa.stattools import acf, pacf, adfuller, kpss, zivot_andrews
    from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
    from statsmodels.stats.stattools import jarque_bera
    method = s['method']
    y, names = series(frame, s, ['GDPC1'] if method=='simulation' else ['gdp_growth'])
    p, h = int(s.get('lags', 2)), int(s.get('horizon', 12))
    alpha = 1-float(s.get('confidence', .9))
    require(1 <= h <= 40, 'Forecast horizon must be between 1 and 40.')
    if method == 'foundations':
        a = y[:,0]
        det = s.get('deterministic', 'c')
        adf = adfuller(a, maxlag=p, regression=det, autolag=None)
        kp = kpss(a, regression='ct' if det=='ct' else 'c', nlags='auto')
        za = zivot_andrews(a, maxlag=p, regression='ct' if det=='ct' else 'c')
        curves = {'ACF': acf(a, nlags=h), 'PACF': pacf(a, nlags=h, method='ywm')}
        return result('Dependence and stationarity', curves,
            {'ADF statistic': adf[0], 'ADF p-value': adf[1], 'KPSS statistic':kp[0], 'KPSS p-value (tabulated bounds)':kp[1],
             'Zivot–Andrews statistic':za[0], 'Zivot–Andrews p-value':za[1], 'Estimated break observation':int(za[4]),
             'Observations':len(a), 'Mean':a.mean(), 'Variance':a.var(ddof=1)},
            note='ADF tests a unit root; KPSS tests stationarity. Zivot–Andrews allows one endogenous break under its alternative. Small p-values answer different null hypotheses. ACF reference bands ±1.96/√T are only a white-noise approximation.', xlabel='Lag')
    if method == 'simulation':
        from statsmodels.tsa.arima_process import ArmaProcess
        rho, theta = float(s.get('root',.8)), float(s.get('ma',.3))
        n, seed = int(s.get('observations',300)), int(s.get('seed',2026))
        require(abs(rho)<1, 'The stationary AR experiment requires |ρ| < 1.')
        process = ArmaProcess([1,-rho],[1,theta])
        a = process.generate_sample(nsample=n, burnin=500, distrvs=np.random.default_rng(seed).standard_normal)
        return result('ARMA(1,1): population and sample dependence', {'Theoretical ACF': process.acf(h+1), 'Sample ACF':acf(a,nlags=h)},
                      {'AR coefficient':rho,'MA coefficient':theta,'Stationary':process.isstationary,'Invertible':process.isinvertible,'Sample variance':a.var()},
                      note='Simulated data, with Gaussian innovations of variance one. The seed fixes the innovations as persistence changes.', xlabel='Lag')
    if method == 'arma':
        from statsmodels.tsa.arima.model import ARIMA
        q,d = int(s.get('ma_order',1)), int(s.get('difference_order',0))
        require(0<=p<=8 and 0<=q<=5 and 0<=d<=2, 'Use p ≤ 8, q ≤ 5 and d ≤ 2.')
        a = y[:,0]
        estimator=s.get('estimator','statespace')
        fit = ARIMA(a,order=(p,d,q),trend=s.get('deterministic','c')).fit(method=estimator)
        forecast = fit.get_forecast(h)
        ci = np.asarray(forecast.conf_int(alpha=alpha))
        residual = fit.resid[max(p,q)+d:]
        lb_lag = max(p+q+3, min(16,len(residual)//5))
        lb = acorr_ljungbox(residual,lags=[lb_lag],model_df=p+q,return_df=True)
        return result('ARIMA forecast', {'Forecast':forecast.predicted_mean,'Lower':ci[:,0],'Upper':ci[:,1]},
             {'AIC':fit.aic,'BIC':fit.bic,'Ljung–Box p-value':lb.lb_pvalue.iloc[0], 'ARCH LM p-value':het_arch(residual,nlags=4)[1],
              'Jarque–Bera p-value':jarque_bera(residual)[1], 'Converged':getattr(fit,'mle_retvals',{}).get('converged',True)},
             {'Coefficients':dict(zip(fit.param_names,fit.params))},
             'Gaussian prediction intervals conditional on estimated parameters; parameter uncertainty is omitted. Diagnostics use post-initialisation residuals.', x=np.arange(1,h+1),xlabel='Quarters ahead',ylabel=names[0])
    if method == 'vecm':
        from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen
        require(y.shape[1]>=2, 'Cointegration requires at least two level series.')
        rank = int(s.get('rank',1)); require(0<=rank<y.shape[1], 'Rank must be between zero and k−1.')
        det = s.get('deterministic','co')
        require(det in ('n','co'), 'This experiment supports no deterministic term or an unrestricted constant.')
        fit = VECM(y,k_ar_diff=p,coint_rank=rank,deterministic=det).fit()
        joh = coint_johansen(y, -1 if det=='n' else 0, p)
        pred,lo,hi = fit.predict(h,alpha=alpha)
        return result('VECM level forecasts', {names[j]:pred[:,j] for j in range(y.shape[1])},
            {'Rank imposed':rank,'Difference lags':p,'Whiteness p-value':fit.test_whiteness(nlags=p+5).pvalue},
            {'Adjustment α':fit.alpha,'Cointegration β':fit.beta,'Johansen trace statistics':joh.lr1,'Trace 95% critical values':joh.cvt[:,1],
             'Maximum eigenvalue statistics':joh.lr2,'Max-eigen 95% critical values':joh.cvm[:,1], 'Forecast lower':lo,'Forecast upper':hi},
            'Rank is imposed, not selected automatically. Johansen critical values use the corresponding standard deterministic case; assess integration and breaks first. Forecast intervals condition on rank and estimated parameters.',x=np.arange(1,h+1),xlabel='Quarters ahead')
    if method in ('pca','dfm','favar'):
        from statsmodels.tsa.api import VAR
        f = int(s.get('factors',1)); require(1<=f<y.shape[1], 'Use fewer factors than observed series.')
        scale=y.std(axis=0,ddof=1); require(np.all(scale>0),'Constant series cannot be standardised.')
        z=(y-y.mean(axis=0))/scale
        u,d,v=np.linalg.svd(z,full_matrices=False); factors=u[:,:f]*d[:f]
        estimates={'PCA loadings':v[:f].T}
        if method=='dfm':
            from statsmodels.tsa.statespace.dynamic_factor import DynamicFactor
            fit=DynamicFactor(z,k_factors=f,factor_order=p).fit(maxiter=150,disp=False)
            factors=fit.factors.smoothed.T
            diagnostics={'AIC':fit.aic,'Converged':fit.mle_retvals['converged']}
            estimates={'State-space parameter estimates':dict(zip(fit.param_names,fit.params))}
        else:
            diagnostics={'Variance explained':float(np.sum(d[:f]**2)/np.sum(d**2))}
        if method=='favar':
            # Last column is the policy rate; remove it from factor extraction.
            u,d,v=np.linalg.svd(z[:,:-1],full_matrices=False)
            require(f<y.shape[1]-1,'FAVAR needs more non-policy series than factors.')
            factors=u[:,:f]*d[:f]
            fit=VAR(np.column_stack([factors,y[:,-1]])).fit(p)
            responses=fit.irf(h).orth_irfs[:,:,-1]
            return result('FAVAR: policy innovation responses', {f'Factor {j+1}' :responses[:,j] for j in range(f)} | {names[-1]:responses[:,-1]},
                {'Stable':fit.is_stable(),'Factors':f},note='Two-step PCA FAVAR. The last observable is ordered last and its one-standard-deviation shock has no contemporaneous effect on the factors. This small panel is not the Bernanke–Boivin–Eliasz replication.',xlabel='Quarters after shock')
        return result('Common factors', {f'Factor {j+1}':factors[:,j] for j in range(f)},diagnostics,
            estimates,'Factors are identified only up to rotation and sign. PCA is static; DFM estimates a Gaussian state-space model by numerical maximum likelihood and reports smoothed factors.')
    from statsmodels.tsa.api import VAR
    require(y.shape[1]>=2,'VAR estimation requires at least two variables.')
    fit=VAR(y).fit(p,trend=s.get('deterministic','c'))
    output=s.get('output','irf'); j=int(s.get('shock',y.shape[1]-1)); require(0<=j<y.shape[1],'Invalid shock index.')
    diag={'AIC':fit.aic,'BIC':fit.bic,'Stable':fit.is_stable(),'Portmanteau p-value':fit.test_whiteness(p+5,adjusted=True).pvalue,
          'Normality p-value':fit.test_normality().pvalue,'Granger p-value (last → first)':fit.test_causality(0,[y.shape[1]-1]).pvalue}
    if output=='forecast':
        pred,lo,hi=fit.forecast_interval(y[-p:],h,alpha=alpha)
        return result('VAR forecast', {names[i]:pred[:,i] for i in range(y.shape[1])},diag,{'Lower':lo,'Upper':hi},
                      'Gaussian prediction intervals condition on estimated parameters. No structural identification is needed for a reduced-form forecast.',x=np.arange(1,h+1),xlabel='Quarters ahead')
    irf=fit.irf(h)
    if output=='fevd':
        fevd=fit.fevd(h).decomp[0]
        return result(f'Forecast variance shares: {names[0]}',{names[i]:fevd[:,i] for i in range(y.shape[1])},diag,
            note='Cholesky identification in displayed variable order. Shares describe orthogonal shocks, not correlated reduced-form residuals.',x=np.arange(1,h+1),xlabel='Forecast horizon',ylabel='Share')
    orth=s.get('identification','reduced')=='recursive'
    a=irf.orth_irfs if orth else irf.irfs
    from scipy.stats import norm
    standard_error=irf.stderr(orth=orth)[:,:,j];critical=norm.ppf(1-alpha/2)
    return result('VAR impulse responses',{names[i]:a[:,i,j] for i in range(y.shape[1])},diag,
        {'Pointwise lower':a[:,:,j]-critical*standard_error,'Pointwise upper':a[:,:,j]+critical*standard_error},
        note=('Recursive identification in displayed variable order; one-standard-deviation orthogonal shock.' if orth else 'Reduced-form unit innovation. Other residuals are held at zero; this is not an identified structural intervention.')+' Tabulated pointwise normal bands use the statsmodels asymptotic IRF covariance and are unreliable near unit roots.',xlabel='Quarters after innovation')
