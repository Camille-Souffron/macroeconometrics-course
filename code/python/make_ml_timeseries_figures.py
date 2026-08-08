"""Data and figures for the machine-learning time-series chapter.

The empirical illustration uses public FRED data and deliberately modest
methods: an autoregression, a small linear model, and ridge regularisation.
It is designed to make the forecasting protocol inspectable, not to crown a
universal winner.  The other figures are diagrams constructed from the
mathematical objects introduced in the chapter.
"""

from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "us_ml_time_series_fred.csv"
FIGURES = ROOT / "figures" / "machine-learning"
FIGURES.mkdir(parents=True, exist_ok=True)

BLUE, RED, GOLD, PURPLE, GREY, GREEN = (
    "#2166ac", "#b2182b", "#d6604d", "#542788", "#4d4d4d", "#1b7837"
)
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"figure.dpi": 140, "savefig.dpi": 180, "font.size": 10})


def fred(series_id):
    """Download a FRED series without an API key."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    with urlopen(url, timeout=30) as response:
        raw = response.read()
    out = pd.read_csv(BytesIO(raw), parse_dates=["observation_date"])
    return out.rename(columns={"observation_date": "date", series_id: series_id})


def prepare_data():
    """Make a quarterly, date-t information set and a one-quarter target."""
    gdp = fred("GDPC1").set_index("date").resample("QS").last()
    cpi = fred("CPIAUCSL").set_index("date").resample("QS").mean()
    rate = fred("FEDFUNDS").set_index("date").resample("QS").mean()
    spread = fred("BAA10YM").set_index("date").resample("QS").mean()
    frame = gdp.join(cpi, how="inner").join(rate, how="left").join(spread, how="left")
    frame.columns = ["real_gdp", "cpi", "policy_rate", "baa_treasury_spread"]
    frame["gdp_growth"] = 400 * np.log(frame.real_gdp).diff()
    frame["inflation"] = 400 * np.log(frame.cpi).diff()
    frame["target_next_growth"] = frame.gdp_growth.shift(-1)
    frame = frame.loc["1961-01-01":"2024-10-01"].dropna().reset_index()
    frame.to_csv(DATA, index=False)
    return frame


def standardise(train_x, test_x):
    """Scale using training data alone, preserving the forecasting boundary."""
    mean = train_x.mean(axis=0)
    scale = train_x.std(axis=0, ddof=0)
    scale[scale < 1e-10] = 1.0
    return (train_x - mean) / scale, (test_x - mean) / scale


def ridge_forecast(train_x, train_y, x_new, penalty):
    """Ridge fit with an unpenalised intercept, using only a historical sample."""
    x_train, x_new = standardise(train_x, x_new[None, :])
    design = np.column_stack((np.ones(len(x_train)), x_train))
    penalty_matrix = np.diag(np.r_[0.0, np.repeat(penalty, design.shape[1] - 1)])
    beta = np.linalg.solve(design.T @ design + penalty_matrix, design.T @ train_y)
    return float(np.r_[1.0, x_new[0]] @ beta)


def choose_penalty(train_x, train_y, candidates=(0.1, 1.0, 10.0, 100.0)):
    """Select lambda on several past forecast origins inside the training sample."""
    first = max(40, len(train_y) - 28)
    origins = range(first, len(train_y), 4)
    losses = []
    for lam in candidates:
        errors = []
        for origin in origins:
            pred = ridge_forecast(train_x[:origin], train_y[:origin], train_x[origin], lam)
            errors.append((train_y[origin] - pred) ** 2)
        losses.append(np.mean(errors))
    return candidates[int(np.argmin(losses))]


def build_design(frame, lags=4):
    """Turn dated observations into rows of lagged predictors without shuffling."""
    columns = ["gdp_growth", "inflation", "policy_rate", "baa_treasury_spread"]
    pieces = []
    for lag in range(lags):
        part = frame[columns].shift(lag).copy()
        part.columns = [f"{name}_lag{lag}" for name in columns]
        pieces.append(part)
    out = pd.concat([frame[["date", "target_next_growth"]]] + pieces, axis=1).dropna()
    return out.reset_index(drop=True)


def empirical_figure(frame):
    """Expanding-origin forecasts of quarterly U.S. GDP growth, 1990 onward."""
    design = build_design(frame)
    feature_columns = [name for name in design.columns if name not in {"date", "target_next_growth"}]
    x = design[feature_columns].to_numpy(float)
    y = design.target_next_growth.to_numpy(float)
    start = int(np.flatnonzero(design.date >= pd.Timestamp("1990-01-01"))[0])
    predictions = {"Historical mean": [], "OLS": [], "Ridge": []}
    realised, dates = [], []
    for origin in range(start, len(design)):
        train_x, train_y = x[:origin], y[:origin]
        x_new = x[origin]
        predictions["Historical mean"].append(float(train_y.mean()))
        predictions["OLS"].append(ridge_forecast(train_x, train_y, x_new, 0.0))
        lam = choose_penalty(train_x, train_y)
        predictions["Ridge"].append(ridge_forecast(train_x, train_y, x_new, lam))
        realised.append(y[origin])
        dates.append(design.date.iloc[origin])
    realised = np.asarray(realised)
    dates = pd.DatetimeIndex(dates)
    scores = {name: np.sqrt(np.mean((realised - np.asarray(values)) ** 2)) for name, values in predictions.items()}

    fig, axes = plt.subplots(2, 1, figsize=(10.7, 7.0), height_ratios=(1.55, 1), sharex=False)
    display = dates >= pd.Timestamp("2000-01-01")
    axes[0].plot(dates[display], realised[display], color="black", lw=1.9, label="realised growth")
    for name, colour in [("OLS", BLUE), ("Ridge", RED), ("Historical mean", GREY)]:
        axes[0].plot(dates[display], np.asarray(predictions[name])[display], color=colour, lw=1.35, label=name)
    axes[0].axhline(0, color="black", lw=.7)
    axes[0].set(title="One-quarter-ahead U.S. GDP-growth forecasts", ylabel="annualised percent")
    axes[0].legend(ncol=2, fontsize=8, frameon=True, loc="upper right")
    names = ["Historical mean", "OLS", "Ridge"]
    values = [scores[name] for name in names]
    bars = axes[1].bar(names, values, color=[GREY, BLUE, RED], width=.58)
    axes[1].bar_label(bars, labels=[f"{value:.2f}" for value in values], padding=3, fontsize=9)
    axes[1].set(title="Pseudo-out-of-sample RMSE, expanding estimation window", ylabel="annualised percentage points")
    axes[1].set_ylim(0, max(values) * 1.24)
    fig.suptitle("Regularisation is assessed only on forecasts made from the past", y=.99, fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES / "fred-expanding-ridge-forecast.png", bbox_inches="tight")
    plt.close(fig)


def origins_figure():
    """Visualise the chronological split and the nesting of validation."""
    fig, ax = plt.subplots(figsize=(10.8, 3.9))
    ax.set_xlim(0, 100)
    ax.set_ylim(-.35, 3.35)
    ax.axis("off")
    colours = {"estimation": BLUE, "validation": GOLD, "test": RED, "future": "#d9d9d9"}
    labels = [(0, 45, 2.55, "estimation", "fit parameters"), (45, 65, 2.55, "validation", "choose architecture / tuning"), (65, 85, 2.55, "test", "reported forecast errors"), (85, 100, 2.55, "future", "not observed")]
    for left, right, height, key, note in labels:
        ax.barh(height, right-left, left=left, height=.54, color=colours[key], edgecolor="white")
        ax.text((left+right)/2, height, key, ha="center", va="center", fontsize=9, color="white" if key != "future" else "black")
        ax.text((left+right)/2, height-.5, note, ha="center", va="center", fontsize=8)
    for row, origin in zip([1.15, .63], [72, 84]):
        ax.barh(row, origin, left=0, height=.34, color=BLUE, alpha=.87)
        ax.barh(row, 1.6, left=origin, height=.34, color=RED, alpha=.87)
        ax.axvline(origin, ymin=.11, ymax=.42, color="black", lw=.8)
    ax.text(0, 1.68, "At each origin: refit on history, then forecast the next unavailable observation", fontsize=10, weight="bold")
    ax.annotate("time", xy=(97, -.04), xytext=(4, -.04), arrowprops=dict(arrowstyle="->", lw=1.1), va="center")
    ax.set_title("A time-series validation set moves forward; it is never a random hold-out", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES / "rolling-origin-validation.png", bbox_inches="tight")
    plt.close(fig)


def parameter_figure():
    """Show how a dense VAR becomes difficult as the cross-section grows."""
    k = np.arange(2, 51)
    p = 4
    parameters = k * k * p + k
    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    ax.plot(k, parameters, color=PURPLE, lw=2.5)
    ax.scatter([8, 20, 50], [8*8*p+8, 20*20*p+20, 50*50*p+50], color=RED, zorder=3)
    for variables in [8, 20, 50]:
        number = variables * variables * p + variables
        ax.annotate(f"{variables} series: {number:,} slopes", (variables, number), xytext=(5, 8), textcoords="offset points", fontsize=9)
    ax.axhline(120, color=GREY, linestyle=(0, (4, 3)), lw=1)
    ax.text(50.1, 120, "120 quarterly observations", va="center", ha="right", fontsize=8, color=GREY)
    ax.set(xlabel="number of variables $k$", ylabel="intercepts and lag coefficients in a VAR(4)", title="A dense lag system consumes observations quadratically")
    fig.tight_layout()
    fig.savefig(FIGURES / "var-parameter-growth.png", bbox_inches="tight")
    plt.close(fig)


def receptive_field_figure():
    """Contrast a causal convolution with an attention pattern that adapts by date."""
    fig, axes = plt.subplots(2, 1, figsize=(10.6, 5.9), gridspec_kw={"height_ratios": [1, 1.25]})
    ax = axes[0]
    times = np.arange(1, 17)
    ax.scatter(times, np.zeros_like(times), s=58, color=BLUE, zorder=3)
    ax.scatter([16], [0], s=100, color=RED, zorder=4)
    for source in [15, 14, 12, 8]:
        ax.annotate("", xy=(16, .03), xytext=(source, .03), arrowprops=dict(arrowstyle="->", color=PURPLE, lw=1.5))
    ax.text(16, -.32, "$t$", ha="center", color=RED)
    ax.text(1, -.32, "$t-15$", ha="center")
    ax.text(8, .42, "causal dilated convolution: a fixed, sparse set of past lags", ha="center", fontsize=10)
    ax.set_xlim(.4, 16.8); ax.set_ylim(-.5, .68); ax.axis("off")
    ax = axes[1]
    weights = np.array([[.04,.04,.05,.05,.06,.07,.08,.09,.10,.10,.08,.06,.05,.04,.03,.02], [.01,.01,.01,.01,.02,.02,.03,.03,.04,.05,.06,.08,.12,.18,.22,.11]])
    im = ax.imshow(weights, aspect="auto", cmap="Blues", vmin=0, vmax=.23)
    ax.set(yticks=[0,1], yticklabels=["normal state", "financial-stress state"], xticks=np.arange(0,16,2), xticklabels=["$t-15$", "$t-13$", "$t-11$", "$t-9$", "$t-7$", "$t-5$", "$t-3$", "$t-1$"])
    ax.set_xlabel("available past positions")
    ax.set_title("masked attention: weights can be recomputed from the observed window")
    colourbar = fig.colorbar(im, ax=ax, fraction=.03, pad=.02)
    colourbar.set_label("illustrative attention weight")
    fig.suptitle("Both architectures respect time order; neither yields a structural impulse response", y=.98, fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES / "causal-convolution-and-attention.png", bbox_inches="tight")
    plt.close(fig)


def main():
    frame = prepare_data()
    origins_figure()
    parameter_figure()
    receptive_field_figure()
    empirical_figure(frame)


if __name__ == "__main__":
    main()
