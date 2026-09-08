"""Identification conditional on an estimated reduced-form VAR."""
import numpy as np
from core import series, result, require


def identify(fit,s,rng):
    from scipy.linalg import eigh
    cov=np.asarray(fit.sigma_u); k=len(cov); p=np.linalg.cholesky(cov)
    method=s.get('identification','recursive'); h=int(s.get('horizon',16)); psi=fit.ma_rep(h)
    note=''
    if method=='recursive':
        b=p; note='Recursive zero restrictions in displayed variable order. Later shocks cannot affect earlier variables on impact.'
    elif method=='long_run':
        require(fit.is_stable(),'Long-run identification requires a stable VAR in stationary variables.')
        c=np.linalg.inv(np.eye(k)-fit.coefs.sum(axis=0))
        b=np.linalg.solve(c,np.linalg.cholesky(c@cov@c.T))
        note='The cumulative multiplier C(1)B is lower triangular. Only the first shock permanently affects the first variable. Apply to growth rates when the long-run object is a level.'
    elif method=='heteroskedastic':
        split=int(len(fit.resid)*float(s.get('split',.5)))
        require(min(split,len(fit.resid)-split)>k+10,'Both variance regimes need enough residual observations.')
        c1=np.cov(fit.resid[:split].T); c2=np.cov(fit.resid[split:].T)
        values,v=eigh(c2,c1); b=np.linalg.inv(v.T)
        require(np.min(np.diff(values))>1e-5,'Variance ratios are repeated: shocks are not separately identified.')
        note='Common impact matrix across two known variance regimes; structural covariances diagonal in both. Columns are ordered by variance ratio and normalised to unit shock variance in regime 1, not by economic identity.'
        for j in range(k):
            if b[j,j]<0: b[:,j]*=-1
    elif method=='max_share':
        target=int(s.get('response',0)); require(0<=target<k,'Invalid response index.')
        a=np.einsum('hij,jk->hik',psi,p)[:,target,:]
        _,v=np.linalg.eigh(a.T@a); q=v[:,::-1]
        b=p@q
        if b[target,0]<0:b[:,0]*=-1
        note='The first shock maximises the target variable’s cumulative forecast-error variance over the selected horizon, conditional on the VAR. Statistical importance does not supply an economic label.'
    elif method=='sign':
        draws=int(s.get('draws',500)); r=int(s.get('restriction_horizon',2))
        require(20<=draws<=3000 and 0<=r<=h,'Use 20–3000 rotations and a restriction horizon within the response horizon.')
        require(k==3,'This sign exercise requires output growth, inflation, policy rate in that order.')
        accepted=[]
        for _ in range(draws):
            q,rr=np.linalg.qr(rng.normal(size=(k,k)));q=q@np.diag(np.sign(np.diag(rr)))
            candidate=p@q
            ir=np.einsum('hij,jk->hik',psi[:r+1],candidate)[:,:,2]
            if np.all(ir[:,0]<=0) and np.all(ir[:,1]<=0) and np.all(ir[:,2]>=0):accepted.append(candidate)
        require(len(accepted)>0,'No admissible rotations. Increase draws, shorten the restriction horizon, or reconsider the restrictions.')
        b=accepted[0]
        note=f'Contractionary policy restrictions: output growth ≤ 0, inflation ≤ 0, rate ≥ 0 through horizon {r}. The plotted response uses the first admissible rotation; tabulated quantiles describe rotation uncertainty conditional on fixed reduced-form estimates, not confidence or credible intervals.'
        return b,note,accepted
    elif method=='short_run':
        from scipy.optimize import least_squares
        elasticity=float(s.get('elasticity',.5)); require(k==3,'The short-run elasticity exercise uses three variables.')
        # B[0,1] = elasticity B[1,1], B[0,2]=B[1,2]=0: three restrictions.
        def unpack(x):
            return np.array([[x[0],elasticity*x[2],0],[x[1],x[2],0],[x[3],x[4],x[5]]])
        tri=np.tril_indices(k)
        sol=least_squares(lambda x:(unpack(x)@unpack(x).T-cov)[tri],p[tri],max_nfev=2000)
        b=unpack(sol.x)
        require(np.linalg.norm(b@b.T-cov)<1e-5,'The imposed elasticity is incompatible with the residual covariance.')
        require(np.linalg.matrix_rank(sol.jac)==6,'The short-run system is not locally identified.')
        note='Imposed contemporaneous elasticity B₁₂/B₂₂, with B₁₃=B₂₃=0. Covariance matching estimates the remaining coefficients. This is an elasticity illustration, not a fiscal-policy replication.'
    else:
        raise ValueError('Unknown identification scheme.')
    return b,note,None


def estimate(frame,s):
    from statsmodels.tsa.api import VAR
    y,names=series(frame,s,['gdp_growth','inflation','policy_rate'])
    if s.get('identification')=='sign':
        require(names==['gdp_growth','inflation','policy_rate'],'This sign preset requires the displayed order: gdp_growth, inflation, policy_rate. Other orderings require explicitly remapped restrictions.')
    p=int(s.get('lags',2));h=int(s.get('horizon',16));j=int(s.get('shock',len(names)-1));target=int(s.get('response',0))
    require(1<=p<=8 and 1<=h<=40,'Use 1–8 lags and 1–40 response horizons.')
    require(0<=j<len(names) and 0<=target<len(names),'Invalid shock or response index.')
    fit=VAR(y).fit(p);psi=fit.ma_rep(h)
    b,note,accepted=identify(fit,s,np.random.default_rng(int(s.get('seed',2026))))
    if s.get('identification')=='max_share':j=0
    ir=np.einsum('hij,jk->hik',psi,b)
    if s.get('cumulative',False):ir=ir.cumsum(axis=0)
    tables={'Impact matrix B':b,'Reduced-form covariance Σu':fit.sigma_u}
    diag={'Stable':fit.is_stable(),'Covariance reconstruction error':np.linalg.norm(b@b.T-fit.sigma_u)}
    if accepted is not None:
        samples=np.array([np.einsum('hij,jk->hik',psi,bi)[:,:,j] for bi in accepted])
        if s.get('cumulative',False):samples=samples.cumsum(axis=1)
        tables['Rotation 16% quantiles']=np.quantile(samples,.16,axis=0);tables['Rotation 84% quantiles']=np.quantile(samples,.84,axis=0)
        diag['Admissible rotations']=len(accepted)
    output=s.get('output','irf')
    if output=='historical':
        require(s.get('identification')!='heteroskedastic','Historical variance normalisation for this regime design is not provided; select impulse responses.')
        shocks=np.linalg.solve(b,np.asarray(fit.resid).T).T
        n=len(shocks);fullpsi=fit.ma_rep(n-1);contributions=np.zeros((n,len(names)))
        for t in range(n):
            for lag in range(t+1):contributions[t]+=(fullpsi[lag]@b)[target]*shocks[t-lag]
        initial=y[p:,target]-contributions.sum(axis=1)
        return result(f'Historical decomposition: {names[target]}',{f'Shock {i+1}':contributions[:,i] for i in range(len(names))}|{'Initial conditions and deterministic path':initial},diag,tables,note+' Contributions sum to the observed series after adding initial conditions and the deterministic path.')
    if output=='fevd':
        require(s.get('identification')!='heteroskedastic','Choose a common-variance identification for this FEVD.')
        energy=np.cumsum(np.einsum('hij,jk->hik',psi,b)**2,axis=0)[:,target,:]
        shares=energy/energy.sum(axis=1)[:,None]
        return result(f'FEVD: {names[target]}',{f'Shock {i+1}':shares[:,i] for i in range(len(names))},diag,tables,note,x=np.arange(1,h+2),xlabel='Forecast horizon',ylabel='Share')
    return result('Identified impulse responses',{names[i]:ir[:,i,j] for i in range(len(names))},diag,tables,note,xlabel='Quarters after shock')
