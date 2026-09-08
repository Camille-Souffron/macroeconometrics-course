"""Shared numerical and serialisation helpers; no browser dependencies."""
import importlib
import json
import warnings
import numpy as np


class EconometricError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EconometricError(message)


def design(y, p, deterministic='c'):
    y = np.asarray(y, float)
    if y.ndim == 1:
        y = y[:, None]
    require(1 <= p <= 12, 'Choose between 1 and 12 lags.')
    n, k = y.shape
    require(n - p > k * p + 12, 'Too few observations for this lag order and dimension.')
    x = np.column_stack([y[p-j:n-j] for j in range(1, p+1)])
    if deterministic == 'c':
        x = np.column_stack([np.ones(n-p), x])
    elif deterministic == 'ct':
        x = np.column_stack([np.ones(n-p), np.arange(p,n), x])
    return y[p:], x


def ols(y, x):
    require(np.linalg.matrix_rank(x) == x.shape[1], 'Regressors are collinear. Reduce lags or change variables.')
    b = np.linalg.lstsq(x, y, rcond=None)[0]
    return b, y-x@b


def series(frame, spec, default):
    columns = spec.get('variables', default)
    if isinstance(columns, str):
        columns = [x.strip() for x in columns.split(',')]
    require(all(x in frame for x in columns), 'A selected variable is not available in this dataset.')
    a = frame[columns].to_numpy(float)
    t = spec.get('transform', 'level')
    if t in ('log', 'growth'):
        require(np.all(a > 0), 'Logarithms require strictly positive levels; use differences for rates or spreads.')
        a = np.log(a)
    if t in ('difference', 'growth'):
        a = np.diff(a, axis=0) * (400 if t == 'growth' else 1)
    if t == 'demean':
        a = a - a.mean(axis=0)
    if t == 'detrend':
        from scipy.signal import detrend
        a = detrend(a, axis=0)
    require(np.isfinite(a).all(), 'The sample contains missing or nonfinite values. Use a complete common sample.')
    require(len(a) >= 40, 'At least 40 complete observations are required.')
    return a, columns


def result(title, curves=None, diagnostics=None, tables=None, note='', x=None, xlabel='Observation', ylabel=''):
    curves = curves or {}
    return dict(title=title, curves=curves, diagnostics=diagnostics or {}, tables=tables or {}, note=note,
                x=list(range(len(next(iter(curves.values()))))) if x is None and curves else x,
                xlabel=xlabel, ylabel=ylabel)


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k,v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    return value


def run(frame, spec):
    """Run precisely the selected module and return JSON-safe output."""
    modules = {'linear', 'spectral', 'structural', 'nonlinear', 'panel', 'bayesian', 'distribution', 'learning', 'sequence', 'foundations', 'instruments'}
    require(spec.get('module') in modules, 'Unknown method family.')
    frame = frame.copy()
    date_column = next((name for name in ('date','observation_date','year') if name in frame), None)
    if date_column:
        import pandas as pd
        dates = pd.to_datetime(frame[date_column].astype(int).astype(str)+'-01-01') if date_column=='year' else pd.to_datetime(frame[date_column])
        mask = np.ones(len(frame), dtype=bool)
        if spec.get('sample_start'):mask &= dates >= pd.Timestamp(spec['sample_start'])
        if spec.get('sample_end'):mask &= dates <= pd.Timestamp(spec['sample_end'])
        frame = frame.loc[mask]
    if 'start' in spec:
        frame = frame.iloc[int(spec['start']):]
    if spec.get('end'):
        frame = frame.iloc[:int(spec['end'])]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        output = importlib.import_module(spec['module']).estimate(frame, spec)
    output['warnings'] = list(dict.fromkeys(str(w.message) for w in caught))[:6]
    output['specification'] = spec
    return clean(output)


def run_json(frame, spec):
    try:
        return json.dumps({'result': run(frame,spec)}, allow_nan=False)
    except (ValueError, np.linalg.LinAlgError) as exc:
        return json.dumps({'error': str(exc)})
    except ImportError as exc:
        return json.dumps({'error': 'A required scientific package is unavailable. Retry loading Python. ' + str(exc).split('\n')[0]})
    except Exception as exc:
        return json.dumps({'error': 'Estimation failed for this specification: ' + type(exc).__name__ + ': ' + str(exc).split('\n')[0] + '. Reduce dimension or lags, inspect the data, and report this specification if the problem persists.'})
