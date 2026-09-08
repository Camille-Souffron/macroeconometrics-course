"""Print inspectable new snapshots; never required for ordinary site use."""
import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

if sys.argv[1]=='macro':
    from statsmodels.datasets import macrodata
    data=macrodata.load_pandas().data
    data.insert(0,'date',[f'{int(y)}-{int(q)*3-2:02d}-01' for y,q in zip(data.year,data.quarter)])
    print(data[['date','realgdp','realcons','realdpi','tbilrate','unemp']].to_csv(index=False),end='')
elif sys.argv[1]=='panel':
    from statsmodels.datasets import grunfeld
    data=grunfeld.load_pandas().data
    frame=pd.DataFrame({'unit':data.firm,'year':data.year,
                        'log_invest':np.log(data.invest),'log_capital':np.log(data.capital)})
    print(frame.to_csv(index=False),end='')
elif sys.argv[1]=='macro-policy':
    data=pd.read_csv(ROOT/'data/us_ml_time_series_fred.csv')
    print(data[['date','real_gdp','gdp_growth','inflation','policy_rate']].to_csv(index=False),end='')
else:
    raise SystemExit('Choose macro, panel or macro-policy. The author shock archive is documented in metadata.json.')
