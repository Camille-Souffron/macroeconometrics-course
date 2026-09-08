"""Native-frequency state-space validation; no invented empirical observations."""
import numpy as np
import pandas as pd
from advanced import mixed_frequency


def test_mixed_frequency_em_on_simulated_common_factor():
    rng=np.random.default_rng(12);n=120;factor=np.zeros(n)
    for t in range(1,n):factor[t]=.7*factor[t-1]+rng.normal()
    monthly=pd.DataFrame(np.column_stack([factor+rng.normal(size=n)*.4,2*factor+rng.normal(size=n)*.5]),
                         index=pd.period_range('2000-01',periods=n,freq='M'),columns=['indicator1','indicator2'])
    quarterly=pd.DataFrame({'growth':factor.reshape(-1,3).mean(axis=1)+rng.normal(size=n//3)*.2},
                           index=pd.period_range('2000Q1',periods=n//3,freq='Q'))
    monthly.iloc[-2:,1]=np.nan
    fit=mixed_frequency(monthly,quarterly)
    assert np.isfinite(fit.llf)
    assert np.isfinite(fit.forecast(3).to_numpy()).all()
