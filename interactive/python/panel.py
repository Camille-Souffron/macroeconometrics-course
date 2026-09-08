"""Panel VAR pooling, collapsed moment estimators and hierarchical Gibbs sampling."""
import numpy as np
from core import result, require, design, ols


def estimate(frame,s):
    from scipy.stats import invgamma
    variables=s.get('variables',['log_invest','log_capital'])
    if isinstance(variables,str):variables=variables.split(',')
    units=[];names=[];p=int(s.get('lags',1));method=s.get('estimator','within')
    require(1<=p<=3,'The panel experiment supports 1–3 lags.')
    for name,group in frame.groupby('unit',sort=True):
        group=group.sort_values('year');require(np.all(np.diff(group.year)==1),'Panel data must have consecutive annual observations within each unit.')
        units.append(group[variables].to_numpy(float));names.append(name)
    require(len(units)>=3,'At least three panel units are needed.')
    k=len(variables);blocks=[design(a,p) for a in units];diag={'Units':len(units),'Smallest T':min(map(len,units))}
    if method=='mean_group':
        coefficients=np.array([ols(y,x)[0][1:] for y,x in blocks]);b=coefficients.mean(axis=0)
        tables={'Unit coefficients':coefficients,'Mean-group standard errors':coefficients.std(axis=0,ddof=1)/np.sqrt(len(units))}
        note='Separate unit VAR slopes are averaged without observation-count weights. Mean Group allows slope heterogeneity; small T biases and cross-unit dependence remain relevant. These observations are firms, not countries.'
    elif method=='hierarchical':
        rng=np.random.default_rng(int(s.get('seed',2026)));draws=int(s.get('draws',150));burn=int(s.get('burn',50));tau=float(s.get('pooling_variance',.1))
        require(20<=draws<=500 and tau>0,'Use 20–500 draws and a positive between-unit prior variance.')
        centred=[(y-y.mean(axis=0),x[:,1:]-x[:,1:].mean(axis=0)) for y,x in blocks]
        d=k*p;mu=np.zeros((d,k));slopes=np.zeros((len(units),d,k));sigma=np.ones((len(units),k));kept=[]
        for it in range(draws+burn):
            for i,(y,x) in enumerate(centred):
                for j in range(k):
                    precision=x.T@x/sigma[i,j]+np.eye(d)/tau;v=np.linalg.inv(precision)
                    loc=v@(x.T@y[:,j]/sigma[i,j]+mu[:,j]/tau)
                    slopes[i,:,j]=rng.multivariate_normal(loc,v)
                    e=y[:,j]-x@slopes[i,:,j];sigma[i,j]=invgamma.rvs(2+len(e)/2,scale=1+e@e/2,random_state=rng)
            v=1/(len(units)/tau+.01);mu=rng.normal(v*slopes.sum(axis=0)/tau,np.sqrt(v))
            if it>=burn:kept.append(mu.copy())
        b=np.mean(kept,axis=0);tables={'Group mean 5%':np.quantile(kept,.05,axis=0),'Group mean 95%':np.quantile(kept,.95,axis=0),'Last unit slopes':slopes}
        note='Gaussian hierarchical slopes with fixed between-unit variance, diffuse Normal group mean, and independent inverse-gamma equation variances. Demeaning conditions out intercepts; this does not remove finite-T dynamic-panel bias. Gibbs bands are conditional on the pooling variance.'
    elif method in ('difference_gmm','system_gmm'):
        depth=int(s.get('instrument_depth',2));require(2<=depth<=5,'Instrument depth must be 2–5.')
        xx=[];yy=[];zz=[];unit_blocks=[]
        for a in units:
            ids=np.arange(max(p+1,depth),len(a));require(len(ids)>15,'Too few dates after lag and instrument trimming.')
            x=np.column_stack([a[ids-l]-a[ids-l-1] for l in range(1,p+1)]);y=a[ids]-a[ids-1]
            z=np.column_stack([a[ids-l] for l in range(2,depth+1)])
            if method=='system_gmm':
                # Separate moment blocks for differences and levels; common slopes.
                xl=np.column_stack([a[ids-l] for l in range(1,p+1)]);yl=a[ids]
                zl=a[ids-1]-a[ids-2]
                z=np.block([[z,np.zeros((len(ids),k))],[np.zeros((len(ids),z.shape[1])),zl]])
                x=np.vstack([x,xl]);y=np.vstack([y,yl])
            xx.append(x);yy.append(y);zz.append(z)
        x=np.vstack(xx);y=np.vstack(yy);z=np.vstack(zz)
        require(np.linalg.matrix_rank(z)==z.shape[1] and np.linalg.matrix_rank(z.T@x)==x.shape[1],'Instruments do not identify all lag coefficients. Increase instrument depth or reduce lags.')
        w=np.linalg.inv(z.T@z);a=x.T@z@w@z.T@x;b=np.linalg.solve(a,x.T@z@w@z.T@y)
        tables={'Collapsed instrument count':z.shape[1],'Moment means':z.T@(y-x@b)/len(y)}
        diag['Instrument relevance condition number']=np.linalg.cond(a)
        note='One-step GMM with collapsed instruments and W=(Z′Z)⁻¹. Difference moments use levels dated t−2 or earlier. System moments add lagged differences as instruments for levels and require mean-stationarity restrictions. Eleven firms are too few for reliable large-N Hansen/Arellano–Bond test p-values; moment residuals and relevance are reported without such claims.'
    elif method=='gvar':
        require(len(set(map(len,units)))==1,'GVAR requires a balanced common sample.')
        array=np.array(units);slopes=[];foreign=[]
        for i,a in enumerate(units):
            star=(array.sum(axis=0)-a)/(len(units)-1)
            y,x=design(a,p);_,xs=design(star,p)
            coefficient,_=ols(y,np.column_stack([x,xs[:,1:]]));slopes.append(coefficient[1:1+k*p]);foreign.append(coefficient[1+k*p:])
        b=np.mean(slopes,axis=0);tables={'Domestic slopes':slopes,'Lagged foreign slopes':foreign}
        note='Unit VARX models use equally weighted lagged other-unit aggregates, not trade weights. With no contemporaneous other-unit terms, stacking these coefficients directly gives the global transition system. This illustrates the GVAR construction on firms rather than countries; equal weights are imposed.'
    else:
        ys=[];xs=[]
        for y,x in blocks:ys.append(y-y.mean(axis=0));xs.append(x[:,1:]-x[:,1:].mean(axis=0))
        b,e=ols(np.vstack(ys),np.vstack(xs));tables={'Residual covariance':np.cov(e.T)}
        note='Within estimator with common slopes and unit intercepts. It is biased in short dynamic panels (Nickell bias); increasing the number of units alone does not remove that bias. The teaching snapshot contains firms, not national economies.'
    return result('Panel VAR lag coefficients',{variables[j]:b[:,j] for j in range(k)},diag,tables,note,xlabel='Lag regressor index',ylabel='Coefficient')
