"""Chronological forecasting with fold-specific standardisation and label embargo."""
import numpy as np
from core import series, result, require


def estimator(s,seed,alpha):
    from sklearn.linear_model import Ridge,Lasso,ElasticNet
    from sklearn.ensemble import RandomForestRegressor,GradientBoostingRegressor
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.neural_network import MLPRegressor
    method=s.get('learner','ridge');depth=int(s.get('depth',3));trees=int(s.get('trees',40))
    require(1<=depth<=8 and 5<=trees<=150,'Limit trees to 5–150 and depth to 1–8.')
    if method=='ridge':return Ridge(alpha=alpha)
    if method=='lasso':return Lasso(alpha=alpha,max_iter=4000)
    if method=='elastic_net':return ElasticNet(alpha=alpha,l1_ratio=float(s.get('l1_ratio',.5)),max_iter=4000)
    if method=='tree':return DecisionTreeRegressor(max_depth=depth,min_samples_leaf=8,random_state=seed)
    if method=='forest':return RandomForestRegressor(n_estimators=trees,max_depth=depth,min_samples_leaf=5,random_state=seed,n_jobs=1)
    if method in ('boosting','quantile_boosting'):
        return GradientBoostingRegressor(n_estimators=trees,max_depth=depth,learning_rate=float(s.get('learning_rate',.05)),random_state=seed,
            loss='quantile' if method=='quantile_boosting' else 'squared_error',alpha=float(s.get('quantile',.1)))
    if method=='mlp':return MLPRegressor(hidden_layer_sizes=(int(s.get('hidden',8)),),alpha=alpha,solver='lbfgs',max_iter=200,random_state=seed)
    raise ValueError('Unknown learner.')


def estimate(frame,s):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from scipy.stats import norm
    y,names=series(frame,s,['gdp_growth','inflation','policy_rate','baa_treasury_spread'])
    p=int(s.get('lags',4));h=int(s.get('horizon',1));seed=int(s.get('seed',2026));alpha=float(s.get('penalty',1))
    require(1<=p<=12 and 1<=h<=12 and alpha>=0,'Use 1–12 lags/horizons and a nonnegative penalty.')
    origins=np.arange(p-1,len(y)-h);x=np.column_stack([y[origins-j] for j in range(p)]);target=y[origins+h,0]
    start=max(80,int(len(x)*float(s.get('train_fraction',.75))));require(len(x)-start>=10,'At least ten evaluation origins are needed.')
    # Limit expensive fits; every reported origin is actually refitted.
    step=int(s.get('evaluation_step',4));require(1<=step<=8,'Evaluation spacing must be 1–8 quarters.')
    forecasts=[];truth=[];benchmark=[];chosen=[];dates=[]
    for t in range(start,len(x),step):
        stop=t-h+1;begin=max(0,stop-int(s.get('rolling_window',100))) if s.get('window_type','expanding')=='rolling' else 0
        require(stop-begin>40,'Training window is too short after the horizon embargo.')
        penalty=alpha
        if s.get('validation','fixed')=='chronological':
            scores=[];candidates=[alpha*.1,alpha,alpha*10] if alpha>0 else [0,.1,1]
            for candidate in candidates:
                errors=[]
                for v in np.linspace(begin+40,stop-1,3,dtype=int):
                    model=make_pipeline(StandardScaler(),estimator(s,seed,candidate))
                    model.fit(x[begin:v-h+1],target[begin:v-h+1]);errors.append((target[v]-model.predict(x[v:v+1])[0])**2)
                scores.append(np.mean(errors))
            penalty=candidates[int(np.argmin(scores))]
        model=make_pipeline(StandardScaler(),estimator(s,seed,penalty));model.fit(x[begin:stop],target[begin:stop])
        forecasts.append(model.predict(x[t:t+1])[0]);truth.append(target[t]);benchmark.append(y[origins[t],0]);chosen.append(penalty);dates.append(int(origins[t]))
    forecasts=np.array(forecasts);truth=np.array(truth);benchmark=np.array(benchmark);e=truth-forecasts;eb=truth-benchmark
    diff=e**2-eb**2;centered=diff-diff.mean();band=max(1,int(np.ceil(h/step)))
    lrv=centered@centered/len(diff)
    for lag in range(1,min(band+1,len(diff))):lrv+=2*(1-lag/(band+1))*(centered[lag:]@centered[:-lag])/len(diff)
    dm=np.sqrt(len(diff))*diff.mean()/np.sqrt(max(lrv,1e-12))
    diag={'RMSE':np.sqrt(np.mean(e**2)),'MAE':np.mean(np.abs(e)),'Persistence RMSE':np.sqrt(np.mean(eb**2)),
          'DM statistic (squared loss)':dm,'DM asymptotic p-value':2*norm.sf(abs(dm)),'Evaluated origins':len(e)}
    if s.get('learner')=='quantile_boosting':
        tau=float(s.get('quantile',.1));diag['Check loss']=np.mean(e*(tau-(e<0)));diag['Violation rate']=np.mean(e<0)
    return result('Chronological forecast evaluation',{'Observed':truth,'Model forecast':forecasts,'Persistence benchmark':benchmark},diag,
        {'Selected penalty at each origin':chosen,'Forecast errors':e},
        'Each forecast uses a new fit and training-window standardisation. Inner chronological validation uses only labels available at that origin. Evaluation spacing limits browser cost. Revised observations make this a pseudo-real-time experiment. DM inference is asymptotic and unreliable with few origins; forecast accuracy does not establish causality.',x=dates,xlabel='Forecast origin (sample index)',ylabel=names[0])
