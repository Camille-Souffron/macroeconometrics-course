"""Narrative shock projections and external-instrument VAR identification."""
import numpy as np
from core import series,design,ols,result,require


def estimate(frame,s):
    import statsmodels.api as sm
    from statsmodels.tsa.api import VAR
    from scipy.stats import norm
    y,names=series(frame,s,['gdp_growth','inflation','policy_rate']);p=int(s.get('lags',2));h=int(s.get('horizon',12))
    require('rr_shock' in frame,'The narrative shock snapshot must be joined by date.')
    instrument=frame.rr_shock.to_numpy(float);target,x=design(y,p);z=instrument[p:];require(np.isfinite(z).all(),'Missing instrument observations.')
    magnitude=float(s.get('shock_size',1));require(1<=h<=32,'Use 1–32 response horizons.')
    if s['method']=='proxy':
        fit=VAR(y).fit(p);u=np.asarray(fit.resid)
        # Residualise the instrument on the same predetermined controls.
        _,z=ols(z,x);moment=z@u/len(z);j=y.shape[1]-1
        first=sm.OLS(u[:,j],sm.add_constant(z)).fit(cov_type='HAC',cov_kwds={'maxlags':p})
        require(abs(moment[j])>1e-10,'The instrument is irrelevant for the policy residual; no impact normalisation is available.')
        impact=moment/moment[j]*magnitude;responses=np.einsum('hij,j->hi',fit.ma_rep(h),impact)
        return result('Proxy-VAR policy responses',{names[i]:responses[:,i] for i in range(len(names))},
            {'Instrument relevance HAC t²':first.tvalues[1]**2,'Instrument-policy residual correlation':np.corrcoef(z,u[:,j])[0,1],'Stable':fit.is_stable()},
            {'Identified impact direction':impact},
            'Quarterly Romer–Romer shocks extended by Wieland–Yang instrument the VAR policy residual. Identification requires relevance and orthogonality to every other structural shock. Policy impact is normalised to the selected percentage-point change; structural shock variance and a complete impact matrix are not identified, so no full FEVD is reported. The relevance statistic is descriptive and does not make weak-IV inference valid.',xlabel='Quarters after policy shock')
    coefficient=[];se=[]
    for hh in range(h+1):
        count=len(target)-hh;xx=np.column_stack([x[:count],z[:count]])
        dep=y[p+hh:,0]
        fit=sm.OLS(dep,xx).fit(cov_type='HAC',cov_kwds={'maxlags':max(hh,p),'use_correction':True})
        coefficient.append(fit.params[-1]*magnitude);se.append(fit.bse[-1]*abs(magnitude))
    coefficient=np.array(coefficient);se=np.array(se);critical=norm.ppf((1+float(s.get('confidence',.9)))/2)
    return result('Narrative-shock local projections',{'Response':coefficient,'Lower':coefficient-critical*se,'Upper':coefficient+critical*se},
        {'Shock observations':len(z)},note='Narrative shocks enter directly, with lagged macro controls. Exogeneity requires that the narrative residual isolate an unanticipated policy change after removing the information used in policy setting. Pointwise HAC bands condition on the published shock estimates. Quarterly data, revised GDP and the projection specification differ from the original paper.',xlabel='Quarters after narrative shock',ylabel=names[0])
