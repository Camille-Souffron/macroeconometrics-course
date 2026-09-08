"""Quantile and distribution regression with chronological evaluation."""
import numpy as np
from core import result, require


def quantile_fit(x,y,tau):
    from scipy.optimize import linprog
    from scipy.sparse import eye, hstack, csr_matrix
    n,d=x.shape
    fit=linprog(np.r_[np.zeros(d),np.full(n,tau),np.full(n,1-tau)],
        A_eq=hstack([csr_matrix(x),eye(n),-eye(n)]).tocsr(),b_eq=y,
        bounds=[(None,None)]*d+[(0,None)]*(2*n),method='highs')
    require(fit.success,'Quantile optimisation failed. Check collinearity and sample size.')
    return fit.x[:d]


def cdf_scores(cuts,cdfs,observations):
    """Exact CRPS for a piecewise-linear bounded CDF, plus its PIT values."""
    scores=[];pits=[]
    for cdf,obs in zip(cdfs,observations):
        knots=np.unique(np.r_[cuts,np.clip(obs,cuts[0],cuts[-1])])
        left,right=knots[:-1],knots[1:];middle=(left+right)/2
        indicator=(middle>=obs).astype(float)
        values=[(np.interp(points,cuts,cdf)-indicator)**2 for points in (left,middle,right)]
        integral=np.sum((right-left)*(values[0]+4*values[1]+values[2])/6)
        scores.append(integral+max(cuts[0]-obs,0)+max(obs-cuts[-1],0))
        pits.append(np.interp(obs,cuts,cdf))
    return np.array(scores),np.array(pits)


def estimate(frame,s):
    from scipy.special import expit
    from scipy.optimize import minimize
    method=s['method'];h=int(s.get('horizon',4));tau=float(s.get('quantile',.05))
    require(1<=h<=12 and .02<=tau<=.98,'Use 1–12 quarters and quantiles between .02 and .98.')
    if method=='dvar':
        return dvar(frame,s)
    g=np.log(frame.real_gdp.to_numpy(float));target=400/h*(g[h:]-g[:-h])
    cols=['growth_now','inflation','nfci'];x=np.column_stack([np.ones(len(target)),frame[cols].to_numpy(float)[:-h]])
    require(len(target)*min(tau,1-tau)>=5,'Fewer than five effective tail observations; widen the quantile or sample.')
    grid=np.array([.05,.1,.25,.5,.75,.9,.95]);rng=np.random.default_rng(int(s.get('seed',2026)))
    condition=np.r_[1,frame[cols].iloc[-1].to_numpy(float)];condition[-1]=float(s.get('financial_conditions',1))
    if method=='distribution_regression':
        thresholds=np.linspace(np.quantile(target,.03),np.quantile(target,.97),25)
        mu=x[:,1:].mean(axis=0);sd=x[:,1:].std(axis=0);z=np.column_stack([x[:,0],(x[:,1:]-mu)/sd])
        xx=np.r_[1,(condition[1:]-mu)/sd];baseline=xx.copy();baseline[-1]=(float(s.get('baseline_conditions',0))-mu[-1])/sd[-1]
        cdf=[];base=[]
        for cut in thresholds:
            binary=(target<=cut).astype(float)
            def objective(b):
                eta=z@b
                return np.sum(np.logaddexp(0,eta)-binary*eta),z.T@(expit(eta)-binary)
            fit=minimize(objective,np.zeros(z.shape[1]),jac=True,method='BFGS')
            require(np.linalg.norm(fit.jac)<.01,'Logit separation or convergence failure at a distribution threshold.')
            cdf.append(expit(xx@fit.x));base.append(expit(baseline@fit.x))
        crossings=int(np.sum(np.diff(cdf)<0));cdf=np.maximum.accumulate(cdf);base=np.maximum.accumulate(base)
        diagnostics={'Raw CDF crossings':crossings};tables={}
        if s.get('evaluate',False):
            origin=max(80,int(.7*len(target)));end=origin-h+1
            require(len(target)-origin>=10,'Evaluation requires at least ten held-out observations.')
            mu=x[:end,1:].mean(axis=0);sd=x[:end,1:].std(axis=0)
            train=np.column_stack([x[:end,0],(x[:end,1:]-mu)/sd])
            test=np.column_stack([x[origin:,0],(x[origin:,1:]-mu)/sd])
            cuts=np.linspace(target[:end].min(),target[:end].max(),31);predictions=[]
            for cut in cuts[1:-1]:
                binary=(target[:end]<=cut).astype(float)
                def objective(b):
                    eta=train@b
                    return np.sum(np.logaddexp(0,eta)-binary*eta),train.T@(expit(eta)-binary)
                fit=minimize(objective,np.zeros(train.shape[1]),jac=True,method='BFGS')
                require(np.linalg.norm(fit.jac)<.01,'Evaluation logit separated or failed to converge. Widen the estimation sample.')
                predictions.append(expit(test@fit.x))
            forecasts=np.column_stack([np.zeros(len(test)),np.maximum.accumulate(np.array(predictions).T,axis=1),np.ones(len(test))])
            scores,pits=cdf_scores(cuts,forecasts,target[origin:])
            diagnostics.update({'Held-out mean CRPS':scores.mean(),'Held-out PIT mean':pits.mean(),'Held-out observations':len(test)})
            tables={'Held-out PIT values':pits,'Held-out CRPS':scores,'Evaluation support endpoints':cuts[[0,-1]]}
        return result('Conditional growth CDF',{'Selected financial conditions':cdf,'Baseline financial conditions':base},diagnostics,tables,
            note='Separate unpenalised logistic regressions estimate P(growth ≤ threshold | current information), followed by monotone envelope repair. These are conditional scenarios, not structural responses. Optional evaluation freezes a model trained on the first 70% with an h-quarter label embargo and training-only scaling. Its CDF is linearly interpolated and bounded at the training extrema; CRPS scores that explicitly bounded law, including penalties for observations outside support. PIT values at zero or one reveal support failures. Revised data and overlapping targets preclude a real-time or independent-PIT interpretation.',x=thresholds,xlabel='Annualised future growth (%)',ylabel='Cumulative probability')
    beta=quantile_fit(x,target,tau);fitted=x@beta;res=target-fitted
    grid_beta=np.array([quantile_fit(x,target,q) for q in grid]);raw=grid_beta@condition;ordered=np.sort(raw)
    draws=int(s.get('draws',40));block=int(s.get('block',8));require(0<=draws<=200 and h<=block<=32,'Use 0–200 bootstrap draws and block length between h and 32.')
    coefficients=[]
    for _ in range(draws):
        starts=rng.integers(0,len(x)-block+1,size=int(np.ceil(len(x)/block)))
        ids=np.concatenate([np.arange(a,a+block) for a in starts])[:len(x)]
        coefficients.append(quantile_fit(x[ids],target[ids],tau))
    loss=np.mean(res*(tau-(res<0)));tables={'Coefficients':dict(zip(['Intercept']+cols,beta)),'Raw conditional quantiles':raw}
    if draws:
        tail=(1-float(s.get('confidence',.9)))/2
        tables['Moving-block percentile coefficient lower']=np.quantile(coefficients,tail,axis=0)
        tables['Moving-block percentile coefficient upper']=np.quantile(coefficients,1-tail,axis=0)
    diagnostics={'Selected conditional quantile':condition@beta,'In-sample check loss':loss,'Raw quantile crossings':int(np.sum(np.diff(raw)<0)), 'Observations':len(target)}
    if s.get('evaluate',False):
        errors=[]
        for t in range(max(100,int(.7*len(x))),len(x)):
            # Labels for origin i are known at t only if i+h <= t.
            last=t-h+1;bt=quantile_fit(x[:last],target[:last],tau);errors.append(target[t]-x[t]@bt)
        errors=np.array(errors);diagnostics['Out-of-sample violation rate']=np.mean(errors<0);diagnostics['Out-of-sample check loss']=np.mean(errors*(tau-(errors<0)))
        tables['Out-of-sample forecast errors']=errors
    return result('Conditional growth quantiles',{'Rearranged quantile curve':ordered},diagnostics,tables,
        'Target is 400/h × log(GDP[t+h]/GDP[t]). NFCI conditions the distribution; it is not an exogenous policy shock. Moving-block bootstrap intervals preserve adjacent rows. Rearrangement prevents crossing but does not identify extreme tails. Evaluation uses revised data and an h-quarter label embargo.',x=grid,xlabel='Quantile probability',ylabel='Annualised future growth (%)')


def dvar(frame,s):
    """Direct multi-step joint distribution regression with triangular factorisation."""
    from scipy.special import expit
    from scipy.optimize import minimize
    y=frame[['nfci','growth_now']].to_numpy(float);p=int(s.get('lags',1));h=int(s.get('horizon',4));draws=int(s.get('draws',300))
    require(1<=p<=3 and 1<=h<=8 and 100<=draws<=1000,'DVAR limits: 1–3 lags, 1–8 horizons, 100–1000 draws.')
    penalty=float(s.get('penalty',1));require(penalty>0,'Positive logit regularisation is required to avoid separation on the threshold grid.')
    shift=float(s.get('financial_conditions',1));rng=np.random.default_rng(int(s.get('seed',2026)));differences=[];baseline_q=[];scenario_q=[];allcross=0;table={}
    for horizon in range(1,h+1):
        ids=np.arange(p-1,len(y)-horizon)
        z=np.column_stack([y[ids-j] for j in range(p)]);future=y[ids+horizon]
        initial=np.concatenate([y[-1-j] for j in range(p)])
        baseline=np.tile(initial,(draws,1));scenario=baseline.copy();scenario[:,0]+=shift
        future_base=np.zeros((draws,2));future_scenario=np.zeros((draws,2))
        for variable in range(2):
            raw=np.column_stack([z,future[:,:variable]])
            mean=raw.mean(axis=0);scale=raw.std(axis=0);x=np.column_stack([np.ones(len(raw)),(raw-mean)/scale])
            xb=np.column_stack([np.ones(draws),(np.column_stack([baseline,future_base[:,:variable]])-mean)/scale])
            xc=np.column_stack([np.ones(draws),(np.column_stack([scenario,future_scenario[:,:variable]])-mean)/scale])
            cuts=np.linspace(future[:,variable].min(),future[:,variable].max(),31);bs=[]
            for cut in cuts[1:-1]:
                binary=(future[:,variable]<=cut).astype(float)
                def objective(b):
                    eta=x@b;reg=np.r_[0,b[1:]]
                    return np.sum(np.logaddexp(0,eta)-binary*eta)+penalty*(b[1:]@b[1:])/2,x.T@(expit(eta)-binary)+penalty*reg
                fit=minimize(objective,np.zeros(x.shape[1]),jac=True,method='BFGS');require(np.linalg.norm(fit.jac)<.01,'Distribution regression did not converge.')
                bs.append(fit.x)
            bs=np.array(bs);fb=expit(xb@bs.T);fc=expit(xc@bs.T);allcross+=int(np.sum(np.diff(fb,axis=1)<0)+np.sum(np.diff(fc,axis=1)<0))
            # Monotone envelope and explicit finite-support boundary convention.
            fb=np.column_stack([np.zeros(draws),np.maximum.accumulate(fb,axis=1),np.ones(draws)])
            fc=np.column_stack([np.zeros(draws),np.maximum.accumulate(fc,axis=1),np.ones(draws)])
            uniforms=rng.uniform(size=draws)
            for i in range(draws):
                future_base[i,variable]=np.interp(uniforms[i],fb[i],cuts);future_scenario[i,variable]=np.interp(uniforms[i],fc[i],cuts)
            if variable==1 and horizon==h:
                table={'Growth grid':cuts,'Baseline growth CDF':fb.mean(axis=0),'Scenario growth CDF':fc.mean(axis=0),'CDF difference':(fc-fb).mean(axis=0)}
        q=np.array([.05,.5,.95]);baseline_q.append(np.quantile(future_base[:,1],q));scenario_q.append(np.quantile(future_scenario[:,1],q));differences.append(scenario_q[-1]-baseline_q[-1])
    differences=np.array(differences)
    return result('Direct distributional forecast response',{'5th percentile change':differences[:,0],'Median change':differences[:,1],'95th percentile change':differences[:,2]},
        {'Raw CDF crossings repaired':allcross,'Simulation draws':draws,'Logit penalty':penalty},table|{'Baseline quantiles':baseline_q,'Scenario quantiles':scenario_q},
        'At each horizon a new joint forecast law factors future NFCI first, then future four-quarter growth conditional on future NFCI and current lagged information. The scenario shifts current NFCI, holding other conditioning values fixed. It is a model-based conditional counterfactual, not an identified policy intervention. Logit slopes are ridge-regularised; monotone CDFs are interpolated on observed support, so extreme extrapolated tails are unavailable. Monte Carlo variation is not parameter uncertainty.',x=np.arange(1,h+1),xlabel='Quarters ahead',ylabel='Growth quantile change (percentage points)')
