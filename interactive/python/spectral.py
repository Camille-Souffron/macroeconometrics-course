"""Spectra, cross-spectra and textbook filters."""
import numpy as np
from core import series, result, require, ols


def estimate(frame,s):
    from scipy import signal
    y,names=series(frame,s,['GDPC1']); a=y[:,0]
    method=s['method']; n=len(a)
    if method in ('spectrum','cross_spectrum'):
        window=int(s.get('window',64)); require(16<=window<=n,'Spectral window must lie between 16 and the sample size.')
        f,p=signal.welch(a,fs=1,nperseg=window,detrend='linear')
        if method=='spectrum':
            rawf,raw=signal.periodogram(a,detrend='linear')
            return result('Welch spectrum',{'Spectral density':p[1:]},{'Segment length':window,'Frequency resolution':1/window},
                {'Raw periodogram frequencies':rawf[1:],'Raw periodogram':raw[1:]},
                'Frequency is measured in cycles per quarter. A period of 32 quarters corresponds to frequency 1/32. Welch averaging trades frequency resolution for lower variance; this is descriptive, not a structural test.',x=f[1:],xlabel='Cycles per quarter',ylabel='Density')
        require(y.shape[1]==2,'Select two variables for cross-spectral analysis.')
        _,cross=signal.csd(a,y[:,1],nperseg=window,detrend='linear')
        _,coh=signal.coherence(a,y[:,1],nperseg=window,detrend='linear')
        return result('Coherence by frequency',{'Squared coherence':coh[1:]},{'Segment length':window},
              {'Phase (radians; SciPy conj(X)Y convention)':np.angle(cross[1:]),'Spectral regression real part':(cross[1:]/p[1:]).real,
               'Spectral regression imaginary part':(cross[1:]/p[1:]).imag},
              'Coherence is a frequency-specific association. Phase follows conj(X)Y; a delayed second variable has negative phase. Spectral regression divides the cross-spectrum by the first series spectrum. Very low-frequency estimates are imprecise.',x=f[1:],xlabel='Cycles per quarter',ylabel='Squared coherence')
    filter_name=s.get('filter','hp'); low=float(s.get('low',6)); high=float(s.get('high',32))
    if filter_name in ('bk','cf'):
        require(2<low<high<n,'Period bounds must satisfy 2 < lower < upper < sample size.')
    w=np.linspace(0,np.pi,200)
    tables={}
    if filter_name=='hp':
        from statsmodels.tsa.filters.hp_filter import hpfilter
        lam=float(s.get('smoothing',1600)); require(lam>0,'HP λ must be positive.')
        cycle,trend=hpfilter(a,lamb=lam)
        gain=lam*(2-2*np.cos(w))**2/(1+lam*(2-2*np.cos(w))**2)
        half=n-20; old,_=hpfilter(a[:half],lamb=lam)
        tables['Endpoint revision (last 12 pre-truncation dates)']=cycle[half-12:half]-old[-12:]
    elif filter_name=='bk':
        from statsmodels.tsa.filters.bk_filter import bkfilter
        k=int(s.get('truncation',12)); require(2*k+20<n,'BK truncation leaves too few observations.')
        cycle=bkfilter(a,low=low,high=high,K=k)
        a=a[k:-k]; trend=a-cycle
        jj=np.arange(-k,k+1); weights=np.zeros(2*k+1); nz=jj!=0
        weights[nz]=(np.sin(2*np.pi/low*jj[nz])-np.sin(2*np.pi/high*jj[nz]))/(np.pi*jj[nz])
        weights[k]=2/low-2/high; weights-=weights.mean()
        gain=np.abs(np.exp(-1j*np.outer(w,jj))@weights)
    elif filter_name=='cf':
        from statsmodels.tsa.filters.cf_filter import cffilter
        cycle,trend=cffilter(a,low=low,high=high,drift=True)
        gain=None
    elif filter_name=='hamilton':
        h=int(s.get('horizon',8)); p=int(s.get('lags',4)); require(n>h+p+20,'Too few observations for the Hamilton regression.')
        idx=np.arange(p-1,n-h)
        x=np.column_stack([np.ones(len(idx))]+[a[idx-j] for j in range(p)])
        b,cycle=ols(a[idx+h],x); trend=x@b; a=a[idx+h]; gain=None
        tables['Projection coefficients']=b
    elif filter_name=='difference':
        cycle=np.diff(a); trend=a[1:]-cycle; a=a[1:]; gain=np.abs(1-np.exp(-1j*w))
    else:
        raise ValueError('Unknown filter.')
    if gain is not None:
        tables['Transfer frequency (cycles/quarter)']=w/(2*np.pi); tables['Cycle amplitude gain']=gain
    return result(f'{filter_name.upper()} extracted cycle',{'Cycle':cycle},{'Retained observations':len(cycle),'Cycle standard deviation':np.std(cycle)},
        tables|{'Trend':trend},'Two-sided filters use future observations and are unsuitable as real-time predictors. BK loses endpoints; CF has date-dependent weights and no single transfer function. Hamilton residuals are horizon projections, not a band-pass filter.',ylabel=names[0])
