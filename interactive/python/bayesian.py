"""Transparent conjugate and Gibbs BVAR posterior simulation."""
import numpy as np
from core import series, result, require, design, ols


def bvar_draws(y,p,prior,tightness,decay,own,draws,burn,seed,cross_tightness=1):
    from scipy.stats import invwishart
    target,x=design(y,p);n,k=target.shape;d=x.shape[1];rng=np.random.default_rng(seed)
    bhat,e=ols(target,x);sigma=e.T@e/(n-d)
    # Original Minnesota scale estimates are univariate autoregression residual variances.
    scales=[]
    for j in range(k):
        univariate=np.column_stack([np.ones(n)]+[y[p-lenlag:len(y)-lenlag,j] for lenlag in range(1,p+1)])
        _,univariate_error=ols(target[:,j],univariate)
        scales.append(univariate_error@univariate_error/(n-p-1))
    scales=np.array(scales);require(np.all(scales>0),'Residual variance must be positive.')
    if prior=='minnesota':sigma=np.diag(scales)
    mean=np.zeros((d,k))
    for j in range(k):mean[1+j,j]=own
    var=np.r_[100., np.concatenate([tightness**2/(lag**(2*decay)*scales) for lag in range(1,p+1)])]
    v0=np.diag(var);prec=np.diag(1/var);vn=np.linalg.inv(x.T@x+prec);bn=vn@(x.T@target+prec@mean)
    nu0=k+2;s0=np.diag(scales)*(nu0-k-1)
    sn=s0+target.T@target+mean.T@prec@mean-bn.T@np.linalg.solve(vn,bn)
    output=[];sigmas=[];b=bhat
    if prior=='normal_diffuse':
        # Proper Normal coefficient prior and improper p(Sigma) ∝ |Sigma|^{-(k+1)/2}.
        nu0=0;s0=np.zeros((k,k))
    for it in range(draws+burn):
        if prior=='normal_wishart':
            sigma=invwishart.rvs(df=nu0+n,scale=sn,random_state=rng)
            b=bn+np.linalg.cholesky(vn)@rng.normal(size=(d,k))@np.linalg.cholesky(sigma).T
        else:
            if prior!='minnesota':
                residual=target-x@b
                sigma=invwishart.rvs(df=nu0+n,scale=s0+residual.T@residual,random_state=rng)
            # Independent Normal prior, equation-specific Minnesota variances.
            equation_variances=np.outer(var,scales)
            for equation in range(k):
                for lag in range(p):
                    for variable in range(k):
                        if variable!=equation:equation_variances[1+lag*k+variable,equation]*=cross_tightness**2
            prior_variances=equation_variances.reshape(-1,order='F')
            precision=np.kron(np.linalg.inv(sigma),x.T@x)+np.diag(1/prior_variances)
            rhs=(x.T@target@np.linalg.inv(sigma)).reshape(-1,order='F')+mean.reshape(-1,order='F')/prior_variances
            chol=np.linalg.cholesky(precision)
            loc=np.linalg.solve(chol.T,np.linalg.solve(chol,rhs))
            b=(loc+np.linalg.solve(chol.T,rng.normal(size=d*k))).reshape((d,k),order='F')
        if it>=burn:output.append(b.copy());sigmas.append(sigma.copy())
    return np.array(output),np.array(sigmas)


def ffbs(y,x,vol,q,rng):
    """Draw random-walk regression coefficients using forward filtering/backward sampling."""
    n,d=x.shape;b=np.zeros(d);p=np.eye(d)*10;means=[];covs=[]
    for t in range(n):
        pred=p+q*np.eye(d);g=pred@x[t]/(x[t]@pred@x[t]+np.exp(vol[t]))
        b=b+g*(y[t]-x[t]@b);p=pred-np.outer(g,x[t]@pred);p=(p+p.T)/2
        means.append(b.copy());covs.append(p.copy())
    path=np.empty((n,d));path[-1]=rng.multivariate_normal(means[-1],covs[-1])
    for t in range(n-2,-1,-1):
        c=covs[t];gain=np.linalg.solve(c+q*np.eye(d),c).T
        loc=means[t]+gain@(path[t+1]-means[t]);v=c-gain@c
        path[t]=rng.multivariate_normal(loc,(v+v.T)/2)
    return path


def tvp_sv(y,x,s):
    rng=np.random.default_rng(int(s.get('seed',2026)));draws=int(s.get('draws',80));burn=int(s.get('burn',40))
    require(20<=draws<=300 and 0<=burn<=300,'Use 20–300 retained draws and at most 300 burn-in draws.')
    q=float(s.get('state_variance',.001));v=float(s.get('vol_variance',.02));require(q>0 and v>0,'State variances must be positive.')
    b,e=ols(y,x);r=max(np.var(e),1e-6);vol=np.full(len(y),np.log(r));kept=[];coefs=[];accept=0
    persistence=float(s.get('vol_persistence',1));prob=float(s.get('outlier_probability',0));multiplier=float(s.get('outlier_scale',5))
    require(0<=persistence<=1 and 0<=prob<.5 and multiplier>=1,'Invalid volatility persistence or outlier-mixture specification.')
    outlier=np.zeros(len(y));location=np.log(r)
    for it in range(draws+burn):
        effective_vol=vol+2*outlier*np.log(multiplier)
        if s.get('time_coefficients',True):path=ffbs(y,x,effective_vol,q,rng)
        else:
            weight=np.exp(-effective_vol);precision=(x*weight[:,None]).T@x+np.eye(x.shape[1])/.5**2
            covariance=np.linalg.inv(precision);coefficient=rng.multivariate_normal(covariance@(x.T@(weight*y)),covariance)
            path=np.tile(coefficient,(len(y),1))
        res=y-np.sum(x*path,axis=1)
        if prob:
            from scipy.special import expit
            logodds=np.log(prob/(1-prob))-np.log(multiplier)+.5*res**2*np.exp(-vol)*(1-1/multiplier**2)
            outlier=(rng.uniform(size=len(y))<expit(logodds)).astype(float)
        def log_target(t,z):
            ans=-.5*(z+res[t]**2*np.exp(-z)/multiplier**(2*outlier[t]))
            prior_mean=location+persistence*(vol[t-1]-location) if t else location
            prior_variance=v if t else (v/(1-persistence**2) if persistence<1 else 1.)
            ans-=.5*(z-prior_mean)**2/prior_variance
            if t<len(y)-1:ans-=.5*(vol[t+1]-location-persistence*(z-location))**2/v
            return ans
        for t in range(len(y)):
            candidate=vol[t]+rng.normal(scale=.2)
            if np.log(rng.uniform())<log_target(t,candidate)-log_target(t,vol[t]):vol[t]=candidate;accept+=1
        if it>=burn:kept.append(np.exp(vol/2));coefs.append(path[:,1])
    return np.array(kept),np.array(coefs),accept/((draws+burn)*len(y))


def estimate(frame,s):
    y,names=series(frame,s,['gdp_growth','inflation','policy_rate']);p=int(s.get('lags',2));h=int(s.get('horizon',12))
    if s['method']=='samplers':return samplers(y[:,0],s)
    draws=int(s.get('draws',150));burn=int(s.get('burn',50));confidence=float(s.get('confidence',.9));tail=(1-confidence)/2
    require(1<=h<=32 and 20<=draws<=1000 and 0<=burn<=1000,'Use 1–32 horizons, 20–1000 draws and at most 1000 burn-in draws.')
    if s['method']=='tvp_sv':
        target,x=design(y,p);sc=x[:,1:].std(axis=0);x[:,1:]=(x[:,1:]-x[:,1:].mean(axis=0))/sc
        vols=[];coefficients=[];acceptance=[]
        for j in range(y.shape[1]):
            vv,bb,acc=tvp_sv(target[:,j],x,s);vols.append(vv);coefficients.append(bb);acceptance.append(acc)
        return result('Time-varying innovation volatility',{names[j]:np.median(vols[j],axis=0) for j in range(len(names))},
            {'MH acceptance rates':acceptance,'Retained draws':draws},
            {'First equation volatility lower':np.quantile(vols[0],tail,axis=0),'First equation volatility upper':np.quantile(vols[0],1-tail,axis=0),
             'First lag coefficient posterior medians':[np.median(bb,axis=0) for bb in coefficients]},
            'VAR with diagonal stochastic volatility: coefficient paths follow random walks when enabled; otherwise coefficients are constant. Log variances follow the selected AR(1), with persistence one giving a random walk. Q and V are fixed. FFBS or Gaussian coefficient draws alternate with Metropolis log-volatility updates and, when enabled, Bernoulli outlier-mixture draws. Mixture probability and scale are imposed. Cross-equation contemporaneous covariance is zero; short teaching chains are not convergence evidence.')
    tight=float(s.get('tightness',.2));require(tight>0,'Prior tightness must be positive.')
    require(y.shape[1]*p<=16,'Browser posterior simulation is limited to 16 lag regressors per equation.')
    prior=s.get('prior','normal_wishart')
    cross=float(s.get('cross_tightness',.5));require(cross>0,'Cross-variable tightness must be positive.')
    bs,ss=bvar_draws(y,p,prior,tight,float(s.get('decay',1)),float(s.get('own_mean',0)),draws,burn,int(s.get('seed',2026)),cross)
    paths=[];stabilities=[];k=len(names);rng=np.random.default_rng(int(s.get('seed',2026))+1)
    for b,cov in zip(bs,ss):
        a=b[1:].T.reshape(k,p,k).transpose(1,0,2)
        companion=np.zeros((k*p,k*p));companion[:k]=np.concatenate(list(a),axis=1)
        if p>1:companion[k:,:-k]=np.eye(k*(p-1))
        stabilities.append(np.max(np.abs(np.linalg.eigvals(companion)))<1)
        if s.get('output','forecast')=='irf':
            j=int(s.get('shock',k-1));require(0<=j<k,'Invalid shock index.')
            psi=[np.eye(k)];path=[np.linalg.cholesky(cov)[:,j]]
            for hh in range(1,h+1):
                value=sum(a[lag-1]@psi[hh-lag] for lag in range(1,min(p,hh)+1));psi.append(value);path.append(value@np.linalg.cholesky(cov)[:,j])
        else:
            history=list(y[-p:].copy());path=[]
            for _ in range(h):
                z=np.r_[1,np.concatenate(history[-p:][::-1])]
                pred=z@b+rng.multivariate_normal(np.zeros(k),cov);path.append(pred);history.append(pred)
        paths.append(path)
    paths=np.array(paths);med=np.median(paths,axis=0)
    first=bs[:,1,0];lagcorr=np.corrcoef(first[:-1],first[1:])[0,1]
    from scipy.special import logsumexp,multigammaln
    target,x=design(y,p);n,k=target.shape;log_likelihood=[]
    def loglik(beta,covariance):
        residual=target-x@beta
        return -.5*(k*np.log(2*np.pi)+np.linalg.slogdet(covariance)[1]+np.einsum('ij,ji->i',residual,np.linalg.solve(covariance,residual.T)))
    for beta,covariance in zip(bs,ss):log_likelihood.append(loglik(beta,covariance))
    ll=np.array(log_likelihood);waic=-2*(np.sum(logsumexp(ll,axis=0)-np.log(draws))-np.sum(ll.var(axis=0,ddof=1)))
    dic=-4*ll.sum(axis=1).mean()+2*loglik(bs.mean(axis=0),ss.mean(axis=0)).sum()
    diagnostics={'Stable posterior draw fraction':np.mean(stabilities),'Retained draws':draws,'First lag draw autocorrelation':lagcorr,'Conditional WAIC':waic,'DIC':dic}
    if prior=='normal_wishart':
        scales=[]
        for j in range(k):
            xx=np.column_stack([np.ones(n)]+[y[p-lag:len(y)-lag,j] for lag in range(1,p+1)])
            _,ee=ols(target[:,j],xx);scales.append(ee@ee/(n-p-1))
        scales=np.array(scales);decay=float(s.get('decay',1))
        variance=np.r_[100.,np.concatenate([tight**2/(lag**(2*decay)*scales) for lag in range(1,p+1)])]
        precision=np.diag(1/variance);vn=np.linalg.inv(x.T@x+precision);m0=np.zeros((len(variance),k))
        for j in range(k):m0[1+j,j]=float(s.get('own_mean',0))
        mn=vn@(x.T@target+precision@m0);nu0=k+2;s0=np.diag(scales);sn=s0+target.T@target+m0.T@precision@m0-mn.T@np.linalg.solve(vn,mn)
        diagnostics['Conditional log marginal likelihood']=(-n*k/2*np.log(np.pi)+k/2*(np.linalg.slogdet(vn)[1]-np.log(variance).sum())+
            nu0/2*np.linalg.slogdet(s0)[1]-(nu0+n)/2*np.linalg.slogdet(sn)[1]+multigammaln((nu0+n)/2,k)-multigammaln(nu0/2,k))
    return result('BVAR posterior responses' if s.get('output')=='irf' else 'BVAR posterior predictive forecast',
        {names[j]:med[:,j] for j in range(k)}, diagnostics,
        {'Lower':np.quantile(paths,tail,axis=0),'Upper':np.quantile(paths,1-tail,axis=0),'Posterior coefficient means':bs.mean(axis=0)},
        'Equal-tail posterior intervals. Forecasts include future innovations and parameter uncertainty; IRFs impose recursive identification for every draw. Unstable draws are reported and retained. Minnesota fixes a diagonal covariance using univariate AR residual variances; Normal–Wishart is conjugate and cannot impose equation-specific cross-lag tightness; independent Normal–Wishart and Normal–diffuse use Gibbs sampling. Lag standard deviations decay with exponent λ₃. A short single chain is pedagogical, not a convergence assessment.',xlabel='Quarters ahead' if s.get('output','forecast')=='forecast' else 'Quarters after shock')


def samplers(y,s):
    """Compare genuine MH, HMC, slice NUTS and mean-field VI against conjugacy."""
    from scipy.stats import norm,gaussian_kde
    x=np.column_stack([np.ones(len(y)-1),y[:-1]]);target=y[1:];b,e=ols(target,x);variance=e@e/(len(e)-2)
    prior_sd=float(s.get('prior_sd',1));require(prior_sd>0,'Prior standard deviation must be positive.')
    prior=np.array([0,float(s.get('own_mean',0))]);precision=x.T@x/variance+np.eye(2)/prior_sd**2
    cov=np.linalg.inv(precision);mean=cov@(x.T@target/variance+prior/prior_sd**2)
    # Work in marginal-SD coordinates, preserving posterior correlation.
    scale=np.sqrt(np.diag(cov));P=precision*np.outer(scale,scale)
    logp=lambda z:-.5*z@P@z
    gradient=lambda z:-P@z
    rng=np.random.default_rng(int(s.get('seed',2026)));draws=int(s.get('draws',300));burn=int(s.get('burn',100));eps=float(s.get('step_size',.25))
    require(50<=draws<=2000 and 0<=burn<=1000 and 0<eps<=1,'Use 50–2000 draws, at most 1000 burn-in draws, and step size in (0,1].')
    method=s.get('sampler','hmc');z=np.zeros(2);samples=[];accepted=0;divergences=0
    def leapfrog(z,r,step):
        rr=r+.5*step*gradient(z);zz=z+step*rr;rr=rr+.5*step*gradient(zz);return zz,rr
    def uturn(left,right,rl,rr):return (right-left)@rl>=0 and (right-left)@rr>=0
    def tree(z,r,logu,direction,depth,joint0):
        if depth==0:
            zz,rr=leapfrog(z,r,direction*eps);joint=logp(zz)-rr@rr/2
            return zz,rr,zz,rr,zz,int(logu<=joint),int(logu<joint+1000)
        left,rl,right,rr,candidate,n,valid=tree(z,r,logu,direction,depth-1,joint0)
        if valid:
            if direction<0:l2,r2,_,_,candidate2,n2,valid2=tree(left,rl,logu,direction,depth-1,joint0);left,rl=l2,r2
            else:_,_,r2,rr2,candidate2,n2,valid2=tree(right,rr,logu,direction,depth-1,joint0);right,rr=r2,rr2
            if n+n2 and rng.uniform()<n2/(n+n2):candidate=candidate2
            n+=n2;valid=valid2 and uturn(left,right,rl,rr)
        return left,rl,right,rr,candidate,n,valid
    if method=='variational':
        # Exact reverse-KL optimum within the diagonal Gaussian variational family.
        approximation_variance=1/np.diag(precision)
        posterior=rng.normal(mean,np.sqrt(approximation_variance),size=(draws,2))
    else:
        for iteration in range(draws+burn):
            old=z.copy()
            if method=='mh':
                proposal=z+rng.normal(scale=eps,size=2)
                if np.log(rng.uniform())<logp(proposal)-logp(z):z=proposal
            elif method=='hmc':
                r0=rng.normal(size=2);zz=z.copy();rr=r0.copy()
                for _ in range(int(s.get('leapfrog_steps',8))):zz,rr=leapfrog(zz,rr,eps)
                delta=logp(zz)-rr@rr/2-logp(z)+r0@r0/2
                divergences+=int(abs(delta)>1000)
                if np.log(rng.uniform())<delta:z=zz
            elif method=='nuts':
                r0=rng.normal(size=2);joint0=logp(z)-r0@r0/2;logu=joint0-rng.exponential()
                left=z.copy();right=z.copy();rl=r0.copy();rr=r0.copy();n=1;valid=True
                for depth in range(6):
                    direction=1 if rng.uniform()>.5 else -1
                    if direction<0:left,rl,_,_,candidate,n2,v2=tree(left,rl,logu,direction,depth,joint0)
                    else:_,_,right,rr,candidate,n2,v2=tree(right,rr,logu,direction,depth,joint0)
                    if v2 and rng.uniform()<min(1,n2/n):z=candidate.copy()
                    n+=n2;valid=v2 and uturn(left,right,rl,rr)
                    if not valid:break
            else:raise ValueError('Unknown posterior sampler.')
            accepted+=int(np.any(z!=old))
            if iteration>=burn:samples.append(mean+z*scale)
        posterior=np.array(samples)
    grid=np.linspace(mean[1]-4*np.sqrt(cov[1,1]),mean[1]+4*np.sqrt(cov[1,1]),120)
    require(np.std(posterior[:,1])>1e-12,'Sampler did not move; change its step size.')
    return result('AR coefficient posterior: computation versus conjugacy',{'Exact Gaussian posterior':norm.pdf(grid,mean[1],np.sqrt(cov[1,1])),'Estimated posterior density':gaussian_kde(posterior[:,1])(grid)},
        {'Analytical posterior mean':mean[1],'Computed mean':posterior[:,1].mean(),'Analytical posterior SD':np.sqrt(cov[1,1]),'Computed SD':posterior[:,1].std(),
         'Moved-state fraction':accepted/(draws+burn) if method!='variational' else None,'Large Hamiltonian errors':divergences},
        {'Coefficient draws':posterior,'Exact posterior covariance':cov},
        'Gaussian AR(1) regression with independent Normal coefficient priors, conditional on an OLS plug-in observation variance. MH is random-walk Metropolis; HMC uses fixed leapfrog trajectories; slice NUTS grows a binary tree until a U-turn (depth capped at 6, no step-size adaptation). Mean-field VI uses its analytical reverse-KL optimum and can understate marginal uncertainty when coefficients are correlated.',x=grid,xlabel='AR coefficient',ylabel='Posterior density')
