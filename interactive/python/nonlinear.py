"""Threshold, smooth-transition, hidden-regime and time-varying systems."""
import numpy as np
from core import series, result, require, design, ols


def kalman(y,x,q,r):
    """Random-walk coefficients, fixed observation variance; Joseph covariance update."""
    d=x.shape[1];b=np.zeros(d);p=np.eye(d)*10;means=[];covs=[]
    for row,obs in zip(x,y):
        pred=p+q*np.eye(d);v=obs-row@b;f=row@pred@row+r;gain=pred@row/f
        b=b+gain*v; a=np.eye(d)-np.outer(gain,row)
        p=a@pred@a.T+r*np.outer(gain,gain)
        means.append(b.copy());covs.append(p.copy())
    return np.array(means),np.array(covs)


def markov_em(y,x,regimes,iterations):
    """Gaussian MS-VAR with current-state coefficients; scaled forward/backward EM."""
    from scipy.special import logsumexp
    n,k=y.shape;d=x.shape[1]
    state=np.argsort(np.argsort(y[:,0]))*regimes//n
    weights=np.eye(regimes)[state]*.9+.1/regimes
    transition=np.full((regimes,regimes),.1/(regimes-1));np.fill_diagonal(transition,.9)
    previous=-np.inf
    for iteration in range(iterations):
        bs=[];cs=[];logpdf=[]
        for j in range(regimes):
            w=weights[:,j];require(w.sum()>d+2,'A regime has too few effective observations. Reduce regimes or lags.')
            b,_=ols(y*np.sqrt(w[:,None]),x*np.sqrt(w[:,None]));e=y-x@b
            c=(e*w[:,None]).T@e/w.sum()+np.eye(k)*1e-8
            bs.append(b);cs.append(c)
            logpdf.append(-.5*(k*np.log(2*np.pi)+np.linalg.slogdet(c)[1]+np.einsum('ij,ji->i',e,np.linalg.solve(c,e.T))))
        emissions=np.array(logpdf).T;shift=emissions.max(axis=1);density=np.exp(emissions-shift[:,None])
        filtered=np.zeros_like(weights);scales=np.zeros(n);prob=np.full(regimes,1/regimes)
        for t in range(n):
            a=prob*density[t];scales[t]=a.sum();filtered[t]=a/scales[t];prob=filtered[t]@transition
        backward=np.ones_like(weights)
        for t in range(n-2,-1,-1):backward[t]=transition@(density[t+1]*backward[t+1])/scales[t+1]
        weights=filtered*backward;weights/=weights.sum(axis=1)[:,None]
        counts=np.zeros_like(transition)
        for t in range(n-1):
            pair=filtered[t,:,None]*transition*(density[t+1]*backward[t+1])[None,:];counts+=pair/pair.sum()
        transition=counts/counts.sum(axis=1)[:,None]
        ll=np.sum(np.log(scales)+shift)
        if abs(ll-previous)<1e-6:break
        previous=ll
    return weights,filtered,transition,np.array(bs),np.array(cs),ll,iteration+1


def estimate(frame,s):
    import statsmodels.api as sm
    from scipy.special import expit
    from scipy.stats import norm
    y,names=series(frame,s,['gdp_growth']);p=int(s.get('lags',2));h=int(s.get('horizon',12));method=s['method']
    target,x=design(y,p);n,k=target.shape;d=x.shape[1]
    require(1<=h<=32,'Use a response horizon between 1 and 32.')
    confidence=float(s.get('confidence',.9));crit=norm.ppf((1+confidence)/2)
    if method=='tvp':
        q=float(s.get('state_variance',.001));require(0<q<=.2,'State innovation variance must be in (0,.2].')
        # Scale predictors to make a common state variance interpretable.
        scale=x[:,1:].std(axis=0);require(np.all(scale>0),'Constant lag regressors.')
        x[:,1:]=(x[:,1:]-x[:,1:].mean(axis=0))/scale
        _,e=ols(target,x);r=np.var(e,axis=0,ddof=d)
        paths=[];bands=[]
        for j in range(k):
            b,cov=kalman(target[:,j],x,q,r[j]);paths.append(b);bands.append(np.sqrt(cov[:,1,1]))
        return result('Filtered time-varying lag coefficient',{names[j]:paths[j][:,1] for j in range(k)},
            {'State innovation variance':q}, {'Lower (first equation)':paths[0][:,1]-crit*bands[0], 'Upper (first equation)':paths[0][:,1]+crit*bands[0], 'All coefficient paths':paths},
            'Gaussian random-walk coefficients with fixed diagonal observation covariance estimated by OLS. Bands are conditional filtering intervals, not a stochastic-volatility posterior. Predictor standardisation uses the estimation sample; this is an in-sample coefficient analysis.')
    if method=='markov':
        regimes=int(s.get('regimes',2));require(regimes in (2,3),'Use two or three regimes.')
        weights,filtered,transition,b,c,ll,it=markov_em(target,x,regimes,int(s.get('iterations',80)))
        return result('Smoothed regime probabilities',{f'Regime {j+1}':weights[:,j] for j in range(regimes)},
            {'Log likelihood':ll,'EM iterations':it,'Converged before limit':it<int(s.get('iterations',80))},
            {'Transition probabilities (row → column)':transition,'Expected durations':1/(1-np.diag(transition)),'Regime coefficients':b,'Filtered probabilities':filtered},
            'Gaussian MS-VAR with coefficients and covariance indexed by the current latent regime. EM is locally optimising; compare alternative specifications. Smoothed probabilities use future observations and are not real-time recession probabilities.',ylabel='Probability')
    if method in ('lp','state_lp','asymmetric_lp'):
        require(k>=2,'Local projections need an outcome and a shock variable.')
        # Cholesky shock placed last: residualise policy on lags and current earlier variables.
        shock_x=np.column_stack([x,target[:,:-1]])
        _,shock=ols(target[:,-1],shock_x);shock/=np.std(shock,ddof=shock_x.shape[1])
        state=y[p-1:-1,0]<=float(s.get('threshold',0));curves={};betas=[];ses=[]
        for hh in range(h+1):
            count=n-hh;z=np.column_stack([x[:count],shock[:count]])
            if method=='state_lp':
                st=state[:count].astype(float);z=np.column_stack([x[:count]*st[:,None],x[:count]*(1-st[:,None]),shock[:count]*st,shock[:count]*(1-st)])
            elif method=='asymmetric_lp':
                z=np.column_stack([x[:count],np.maximum(shock[:count],0),np.minimum(shock[:count],0)])
            require(np.linalg.matrix_rank(z)==z.shape[1] and count>z.shape[1]+10,'Too few observations or collinearity in a projection regime.')
            dep=y[p+hh:,0]
            if s.get('cumulative',False):dep=np.array([y[p+t:p+t+hh+1,0].sum() for t in range(count)])
            fit=sm.OLS(dep,z).fit(cov_type='HAC',cov_kwds={'maxlags':max(hh,p),'use_correction':True})
            m=1 if method=='lp' else 2;betas.append(fit.params[-m:]);ses.append(fit.bse[-m:])
        betas=np.array(betas);ses=np.array(ses)
        labels=['Response'] if method=='lp' else (['Low-growth state','High-growth state'] if method=='state_lp' else ['Positive shock slope','Negative shock slope'])
        curves={label:betas[:,j] for j,label in enumerate(labels)}
        return result('Local projection responses',curves,{'Confidence level':confidence}, {'Lower':betas-crit*ses,'Upper':betas+crit*ses},
            'Shock is a one-standard-deviation policy residual orthogonalised after current earlier variables and all lags. Structural interpretation requires this recursive timing assumption. Pointwise normal HAC bands use max(h,p) Bartlett lags; generated-shock estimation uncertainty is omitted. States use lagged growth.',xlabel='Quarters after shock')
    threshold=float(s.get('threshold',0));delay=int(s.get('delay',1));require(1<=delay<=p,'Threshold delay must lie within the lag window.')
    state=y[p-delay:len(y)-delay,0];speed=float(s.get('speed',2))
    if method=='star':
        require(speed>0,'Transition speed must be positive.')
        w=expit(speed*(state-threshold))
    else:w=(state>threshold).astype(float)
    require(min(w.sum(),(1-w).sum())>d+5,'A regime is empty or too small; change the threshold or reduce lags.')
    z=np.column_stack([x*(1-w[:,None]),x*w[:,None]])
    b,e=ols(target,z);b0,b1=b[:d],b[d:]
    if s.get('output','fit')=='girf':
        draws=int(s.get('draws',200));require(20<=draws<=1000,'Use 20–1000 simulations.')
        rng=np.random.default_rng(int(s.get('seed',2026)));impact=np.linalg.cholesky(np.cov(e.T).reshape(k,k))
        shock=int(s.get('shock',k-1));require(0<=shock<k,'Invalid shock index.')
        histories=np.repeat(y[-p:][None,:,:],draws,axis=0);base=histories.copy();perturbed=histories.copy();paths=[]
        size=float(s.get('shock_size',1))
        def step(hist,eps):
            xx=np.column_stack([np.ones(draws)]+[hist[:,-j,:] for j in range(1,p+1)])
            st=hist[:,-delay,0];ww=expit(speed*(st-threshold)) if method=='star' else (st>threshold)
            pred=(xx@b0)*(1-ww[:,None])+(xx@b1)*ww[:,None]+eps
            return np.concatenate([hist[:,1:],pred[:,None,:]],axis=1)
        for hh in range(h+1):
            eps=e[rng.integers(len(e),size=draws)]
            base=step(base,eps);perturbed=step(perturbed,eps+(size*impact[:,shock] if hh==0 else 0))
            paths.append((perturbed[:,-1]-base[:,-1]).mean(axis=0))
        paths=np.array(paths)
        require(np.isfinite(paths).all() and np.max(np.abs(paths))<1e8,'Simulated paths diverged. Change lags or regime specification.')
        return result('Generalized impulse response',{names[j]:paths[:,j] for j in range(k)}, {'Simulation paths':draws},
            note='Paired residual-bootstrap paths start at the final observed history; only one path receives the initial recursive shock. Regimes subsequently evolve endogenously. The mean difference is history- and shock-size-dependent; no uncertainty band is implied.',xlabel='Quarters after shock')
    return result('Regime-dependent fitted values',{'Observed':target[:,0],'Fitted':(z@b)[:,0]},
        {'Low-state effective observations':float((1-w).sum()),'High-state effective observations':float(w.sum()),'Residual RMSE':np.sqrt(np.mean(e[:,0]**2))},
        {'Low-state coefficients':b0,'High-state coefficients':b1,'Transition weights':w},
        'TAR uses a hard split on lagged growth. STAR uses a logistic transition with fixed, user-chosen threshold and speed, estimating both coefficient blocks by least squares. Changing these controls changes the actual regression, not just its presentation.')
