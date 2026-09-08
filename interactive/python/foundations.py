"""Dependence-robust unit-root statistics, breaks and elementary inference."""
import numpy as np
from core import series,result,require,ols


def adf_t(y,p,z=None):
    import statsmodels.api as sm
    dy=np.diff(y);t=np.arange(p,len(dy))
    x=np.column_stack([y[t]]+[dy[t-j] for j in range(1,p+1)])
    if z is not None:x=np.column_stack([x,z[t+1]])
    fit=sm.OLS(dy[t],x).fit()
    return fit.tvalues[0]


def dfgls(y,p,trend):
    n=len(y);z=np.ones((n,1)) if trend=='c' else np.column_stack([np.ones(n),np.arange(1,n+1)])
    a=1+(-7 if trend=='c' else -13.5)/n
    yz=np.r_[y[0],y[1:]-a*y[:-1]];zz=np.vstack([z[0],z[1:]-a*z[:-1]])
    beta,_=ols(yz,zz)
    return adf_t(y-z@beta,p)


def estimate(frame,s):
    import statsmodels.api as sm
    from scipy.stats import f as f_distribution,norm
    from statsmodels.tsa.adfvalues import mackinnonp
    y,names=series(frame,s,['GDPC1']);a=y[:,0];n=len(a);p=int(s.get('lags',2));method=s['method'];rng=np.random.default_rng(int(s.get('seed',2026)))
    if method=='sampling':
        size=int(s.get('observations',80));draws=int(s.get('draws',500));block=int(s.get('block',4))
        require(10<=size<=500 and 100<=draws<=2000 and 1<=block<=min(n,32),'Use sample size 10–500, 100–2000 resamples and block length 1–32.')
        means=[];population=s.get('population','empirical');df=float(s.get('degrees_freedom',8));prob=float(s.get('probability',.3));rate=float(s.get('rate',2))
        require(df>4 and 0<prob<1 and rate>0,'Use degrees of freedom above four, a probability in (0,1), and a positive rate.')
        if population=='empirical':
            for _ in range(draws):
                starts=rng.integers(0,n,size=int(np.ceil(size/block)));idx=np.concatenate([(np.arange(start,start+block)%n) for start in starts])[:size]
                means.append(a[idx].mean())
            population_mean=a.mean()
        else:
            generators={'normal':lambda:rng.normal(size=(draws,size)),'student':lambda:rng.standard_t(df,size=(draws,size)),
                'bernoulli':lambda:rng.binomial(1,prob,size=(draws,size)),'poisson':lambda:rng.poisson(rate,size=(draws,size)),
                'exponential':lambda:rng.exponential(1/rate,size=(draws,size)),'chi_square':lambda:rng.chisquare(df,size=(draws,size)),
                'fisher':lambda:rng.f(df,df,size=(draws,size))}
            require(population in generators,'Unknown population distribution.')
            means=generators[population]().mean(axis=1)
            population_mean={'normal':0,'student':0,'bernoulli':prob,'poisson':rate,'exponential':1/rate,'chi_square':df,'fisher':df/(df-2)}[population]
        means=np.array(means);z=(means-means.mean())/means.std(ddof=1)
        from scipy.stats import gaussian_kde
        grid=np.linspace(-4,4,100)
        return result('Sampling distribution of the mean',{'Standardised resampling density':gaussian_kde(z)(grid),'Standard Normal density':norm.pdf(grid)},
            {'Population mean':population_mean,'Mean across samples':means.mean(),'Sampling standard error':means.std(ddof=1),'Sample size':size},
            {'Sample mean draws':means},'The empirical option uses circular block resampling of real observations: block length one imposes independence; longer blocks retain short-run dependence. Other options simulate independent draws from the stated population law. Increasing sample size illustrates concentration and a CLT approximation, not proof that the underlying macro series is stationary.',x=grid,xlabel='Standardised sample mean',ylabel='Density')
    if method=='unit_roots':
        trend=s.get('deterministic','c');require(trend in ('c','ct'),'Choose a constant or constant and trend.')
        z=np.ones((n-1,1)) if trend=='c' else np.column_stack([np.ones(n-1),np.arange(1,n)])
        x=np.column_stack([a[:-1],z]);fit=sm.OLS(a[1:],x).fit();e=fit.resid;t=len(e)
        gamma=e@e/t;lrv=gamma;band=int(s.get('bandwidth',8));require(0<=band<t,'Invalid long-run variance bandwidth.')
        for lag in range(1,band+1):lrv+=2*(1-lag/(band+1))*(e[lag:]@e[:-lag])/t
        require(lrv>0,'Estimated long-run variance is nonpositive.')
        se=fit.bse[0];resvar=fit.scale;rho=fit.params[0]
        pp=np.sqrt(gamma/lrv)*(rho-1)/se-.5*(lrv-gamma)/np.sqrt(lrv)*(t*se/np.sqrt(resvar))
        gls=dfgls(a,p,trend);draws=int(s.get('draws',199));require(99<=draws<=999,'Use 99–999 null simulations.')
        stats=np.array([dfgls(np.cumsum(rng.normal(size=n)),p,trend) for _ in range(draws)])
        return result('DF–GLS finite-sample null distribution',{'Sorted null statistics':np.sort(stats)},
            {'Phillips–Perron τ':pp,'PP asymptotic p-value':mackinnonp(pp,regression=trend),'DF–GLS statistic':gls,
             'DF–GLS Monte Carlo p-value':(1+np.sum(stats<=gls))/(draws+1),'Simulated 5% critical value':np.quantile(stats,.05)},
            note='PP uses Bartlett long-run variance correction. DF–GLS applies ERS local-to-unity GLS detrending before an unaugmented-deterministic ADF regression. Its displayed critical value is simulated for an i.i.d. Gaussian random-walk null at this sample size and lag order, not taken from the published ERS tables.',xlabel='Null simulation order statistic')
    if method=='seasonality':
        period=int(s.get('period',4));require(2<=period<=12,'Use seasonal period 2–12.')
        if s.get('seasonal_method','dummies')=='difference':res=a[period:]-a[:-period]
        else:
            z=np.eye(period)[np.arange(n)%period];b,res=ols(a,z)
        return result('Seasonal transformation',{'Transformed series':res},{'Seasonal period':period},
            note='Seasonal dummies remove a stable periodic mean; seasonal differences impose roots at seasonal frequencies. The bundled GDP data are already seasonally adjusted, so this illustrates the transformation rather than discovering an untreated seasonal component.',ylabel=names[0])
    if method=='breaks':
        fraction=float(s.get('split',.5));trim=int(n*float(s.get('trim',.15)));breaks=int(s.get('breaks',1));require(1<=breaks<=3 and trim>=8,'Use 1–3 breaks and segments of at least eight observations.')
        x=np.column_stack([np.ones(n),np.linspace(0,1,n)]);b,e=ols(a,x);split=int(n*fraction)
        require(min(split,n-split)>4,'The known break must leave observations on each side.')
        b1,e1=ols(a[:split],x[:split]);b2,e2=ols(a[split:],x[split:]);ssr=e1@e1+e2@e2
        chow=((e@e-ssr)/2)/(ssr/(n-4))
        # Global least-squares partition, all intercepts and trend slopes allowed to break.
        require((breaks+1)*trim<=n,'Too many breaks for the selected minimum segment length.')
        costs=np.full((n+1,n+1),np.inf)
        for i in range(n-trim+1):
            for j in range(i+trim,n+1):
                _,r=ols(a[i:j],x[i:j]);costs[i,j]=r@r
        dp=np.full((breaks+2,n+1),np.inf);dp[0,0]=0;back=np.zeros_like(dp,dtype=int)
        for count in range(1,breaks+2):
            for j in range(count*trim,n+1):
                ids=np.arange((count-1)*trim,j-trim+1);v=dp[count-1,ids]+costs[ids,j];best=np.argmin(v);dp[count,j]=v[best];back[count,j]=ids[best]
        boundaries=[n];end=n
        for count in range(breaks+1,0,-1):end=int(back[count,end]);boundaries.append(end)
        boundaries=sorted(boundaries);fitted=np.zeros(n)
        for i,j in zip(boundaries[:-1],boundaries[1:]):bb,_=ols(a[i:j],x[i:j]);fitted[i:j]=x[i:j]@bb
        return result('Broken deterministic trends',{'Observed':a,'Estimated segmented trend':fitted},
            {'Known-break Chow F':chow,'Chow classical p-value':f_distribution.sf(chow,2,n-4),'Chosen unknown breaks':boundaries[1:-1],
             'Segmented SSR':dp[breaks+1,n]},
            note='Chow’s classical F reference requires homoskedastic, serially independent regression errors and a pre-specified break. Global dynamic programming estimates multiple unknown trend breaks subject to trimming (Bai–Perron least-squares partition). This display does not attach ordinary F p-values to searched break dates.',ylabel=names[0])
    if method=='perron':
        split=int(n*float(s.get('split',.5)));t=np.arange(n);z=np.column_stack([np.ones(n),t,(t>=split).astype(float),np.maximum(t-split,0),(t==split).astype(float)])
        stat=adf_t(a,p,z);draws=int(s.get('draws',199));require(99<=draws<=999,'Use 99–999 null simulations.')
        null=np.array([adf_t(np.cumsum(rng.normal(size=n)),p,z) for _ in range(draws)])
        return result('Known-break augmented unit-root regression',{'Sorted Gaussian null statistics':np.sort(null)},
            {'Known break index':split,'Lagged-level t statistic':stat,'Monte Carlo p-value':(1+np.sum(null<=stat))/(draws+1),'5% simulated critical value':np.quantile(null,.05)},
            note='Known-date regression includes intercept, trend, level shift, slope shift and a break pulse. Reference distribution is simulated under a Gaussian random walk with zero break magnitude, conditional on the chosen break and lags. It is a Perron-style exercise; it does not substitute ordinary ADF critical values or claim the exact Perron (1989) innovation-outlier design.',xlabel='Null simulation order statistic')
    # Elementary Gaussian regression and repeated-sample inference on actual observations.
    require(y.shape[1]>=2,'Select an outcome and a predictor.')
    x=sm.add_constant(y[:,1:]);fit=sm.OLS(a,x).fit(cov_type='HAC',cov_kwds={'maxlags':p})
    return result('Linear projection and inference',{'Observed':a,'Linear projection':fit.fittedvalues},
        {'R²':fit.rsquared,'Design rank':np.linalg.matrix_rank(x),'Condition number':np.linalg.cond(x),'Slope Wald p-value':fit.pvalues[1]},
        {'Coefficients':fit.params,'HAC confidence intervals':fit.conf_int(alpha=1-float(s.get('confidence',.95))),
         'Covariance eigenvalues':np.linalg.eigvalsh(np.cov(y.T))},
        'OLS projects the outcome onto the regressor span. HAC uncertainty allows weak residual dependence, conditional on exogeneity and a suitable bandwidth. Statistical association is not a structural coefficient.',ylabel=names[0])
