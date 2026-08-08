"""Figures and data for the Growth-at-Risk chapter.

The script downloads three public FRED series, aggregates the weekly NFCI to the
quarter, and estimates the chapter's deliberately small quantile-regression
model.  Quantile regressions are solved as linear programmes here rather than
through a high-level econometrics wrapper, so the check-loss problem remains
visible.  This code and the choice of figures were written for this course.
"""

from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from scipy.optimize import linprog


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "us_growth_at_risk_fred.csv"
FIGURES = ROOT / "figures" / "growth-at-risk"
FIGURES.mkdir(parents=True, exist_ok=True)

BLUE, RED, GOLD, PURPLE, GREY = "#2166ac", "#b2182b", "#d6604d", "#542788", "#4d4d4d"
QUANTILES = np.array([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
SAMPLE_START = "1973-01-01"
SAMPLE_END = "2024-09-30"
HORIZON = 4

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"figure.dpi": 140, "savefig.dpi": 180, "font.size": 10})


def fred(series_id):
    """Download one FRED series without requiring an API key."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    with urlopen(url, timeout=30) as response:
        raw = response.read()
    frame = pd.read_csv(BytesIO(raw), parse_dates=["observation_date"])
    return frame.rename(columns={"observation_date": "date", series_id: series_id})


def prepare_data():
    """Construct data known at each quarterly forecast origin."""
    gdp = fred("GDPC1").set_index("date")
    deflator = fred("GDPDEF").set_index("date")
    nfci = fred("NFCI").set_index("date").resample("QS").mean()
    frame = gdp.join(deflator, how="inner").join(nfci, how="left")
    frame = frame.rename(columns={"GDPC1": "real_gdp", "GDPDEF": "deflator", "NFCI": "nfci"})
    frame["log_gdp"] = np.log(frame["real_gdp"])
    frame["growth_now"] = 100 * frame["log_gdp"].diff(4)
    frame["inflation"] = 100 * np.log(frame["deflator"]).diff(4)
    frame["growth_4q_ahead"] = 100 * (frame["log_gdp"].shift(-HORIZON) - frame["log_gdp"])
    frame = frame.loc[SAMPLE_START:SAMPLE_END].dropna().reset_index()
    frame.to_csv(DATA, index=False)
    return frame


def design(frame, target="growth_4q_ahead"):
    """Return the regression target and conditioning variables at date t."""
    y = frame[target].to_numpy(dtype=float)
    x = np.column_stack(
        [
            np.ones(len(frame)),
            frame["growth_now"].to_numpy(dtype=float),
            frame["inflation"].to_numpy(dtype=float),
            frame["nfci"].to_numpy(dtype=float),
        ]
    )
    return y, x


def quantile_fit(x, y, tau):
    """Solve min sum rho_tau(y - X beta) through its linear-programme form."""
    n, k = x.shape
    objective = np.r_[np.zeros(k), tau * np.ones(n), (1 - tau) * np.ones(n)]
    equality = np.c_[x, np.eye(n), -np.eye(n)]
    bounds = [(None, None)] * k + [(0, None)] * (2 * n)
    result = linprog(objective, A_eq=equality, b_eq=y, bounds=bounds, method="highs")
    if not result.success:
        raise RuntimeError(result.message)
    return result.x[:k]


def fit_grid(frame, quantiles=QUANTILES, target="growth_4q_ahead"):
    y, x = design(frame, target)
    return np.vstack([quantile_fit(x, y, tau) for tau in quantiles])


def moving_block_indices(n, length, rng):
    """Resample adjacent observations together, preserving short-run dependence."""
    starts = rng.integers(0, n - length + 1, size=int(np.ceil(n / length)))
    return np.concatenate([np.arange(s, s + length) for s in starts])[:n]


def bootstrap_coefficients(frame, quantiles, target, draws=120, block=8, seed=20260808):
    """Moving-block bootstrap intervals for time-series quantile coefficients."""
    y, x = design(frame, target)
    rng = np.random.default_rng(seed)
    out = np.empty((draws, len(quantiles), x.shape[1]))
    for draw in range(draws):
        idx = moving_block_indices(len(y), block, rng)
        for j, tau in enumerate(quantiles):
            out[draw, j] = quantile_fit(x[idx], y[idx], tau)
    return np.quantile(out, [0.05, 0.95], axis=0)


def check_loss_figure():
    residual = np.linspace(-3, 3, 400)
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    for tau, colour in [(0.05, RED), (0.50, BLUE), (0.95, GOLD)]:
        loss = np.maximum(tau * residual, (tau - 1) * residual)
        ax.plot(residual, loss, lw=2.3, color=colour, label=rf"$\tau={tau:.2f}$")
    ax.axvline(0, color="black", lw=.8)
    ax.set(
        xlabel="residual $u=y-x'\\beta$",
        ylabel=r"check loss $\rho_\tau(u)$",
        title="The target quantile determines which errors are costly",
    )
    ax.legend(title="target quantile", frameon=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "quantile-check-loss.png", bbox_inches="tight")
    plt.close(fig)


def coefficient_figure(frame, betas, intervals):
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), sharex=True)
    names = [(1, "current four-quarter growth"), (3, "financial conditions (NFCI)")]
    for ax, (column, title) in zip(axes, names):
        estimate = betas[:, column]
        lower, upper = intervals[0, :, column], intervals[1, :, column]
        ax.fill_between(QUANTILES, lower, upper, color=BLUE if column == 1 else RED, alpha=.20, label="90% moving-block bootstrap interval")
        ax.plot(QUANTILES, estimate, "o-", color=BLUE if column == 1 else RED, lw=2, ms=5, label="quantile coefficient")
        ax.axhline(0, color="black", lw=.8)
        ax.set(title=title, xlabel=r"conditional quantile $\tau$", ylabel="coefficient")
        ax.set_xticks(QUANTILES)
        ax.set_xticklabels(["5", "10", "25", "50", "75", "90", "95"])
        ax.legend(fontsize=8, frameon=True)
    axes[0].text(.5, -.26, "percentile", ha="center", transform=axes[0].transAxes)
    axes[1].text(.5, -.26, "percentile", ha="center", transform=axes[1].transAxes)
    fig.suptitle("The same predictor can move different parts of future-growth distribution", y=1.03, fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES / "gar-coefficients-by-quantile.png", bbox_inches="tight")
    plt.close(fig)


def rearrange(values):
    """Monotone rearrangement at a fixed forecast origin."""
    return np.maximum.accumulate(values, axis=-1)


def quantile_curve_figure(frame, betas):
    dates = [pd.Timestamp("2006-10-01"), pd.Timestamp("2008-10-01")]
    fig, ax = plt.subplots(figsize=(8.8, 5.1))
    colours = [BLUE, RED]
    for date, colour in zip(dates, colours):
        row = frame.loc[frame.date == date]
        if row.empty:
            continue
        _, x = design(row)
        fitted = rearrange((x @ betas.T).ravel())
        ax.plot(fitted, QUANTILES, "o-", color=colour, lw=2, label=date.strftime("%YQ4"))
    ax.axvline(0, color="black", lw=.8)
    ax.axhline(.05, color=GREY, lw=.8, ls=":")
    ax.axhline(.50, color=GREY, lw=.8, ls=":")
    ax.set(
        xlabel="predicted four-quarter GDP growth (percent)",
        ylabel="conditional probability",
        title="Changing financial information moves the lower tail more than the upper tail",
        ylim=(0, 1),
    )
    ax.legend(title="information available at", frameon=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "gar-conditional-quantile-curves.png", bbox_inches="tight")
    plt.close(fig)


def fan_chart_figure(frame, betas):
    _, x = design(frame)
    fitted = rearrange(x @ betas.T)
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    date = frame.date
    ax.fill_between(date, fitted[:, 0], fitted[:, -1], color=BLUE, alpha=.10, label="5–95% fitted interval")
    ax.fill_between(date, fitted[:, 1], fitted[:, -2], color=BLUE, alpha=.18, label="10–90% fitted interval")
    ax.fill_between(date, fitted[:, 2], fitted[:, -3], color=BLUE, alpha=.31, label="25–75% fitted interval")
    ax.plot(date, fitted[:, 3], color=BLUE, lw=1.8, label="conditional median")
    ax.plot(date, frame.growth_4q_ahead, color=GREY, lw=.9, alpha=.85, label="realised four-quarter growth")
    ax.axhline(0, color="black", lw=.7)
    ax.set(
        ylabel="percent",
        title="Fitted distribution of U.S. four-quarter-ahead GDP growth",
    )
    ax.legend(ncol=3, fontsize=8.3, frameon=True, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIGURES / "gar-in-sample-fan-chart.png", bbox_inches="tight")
    plt.close(fig)


def horizon_target(frame, horizon):
    copy = frame.copy()
    copy["growth_h"] = 400 / horizon * (copy.log_gdp.shift(-horizon) - copy.log_gdp)
    return copy.dropna(subset=["growth_h", "growth_now", "inflation", "nfci"])


def term_structure_figure(frame):
    horizons = np.arange(1, 13)
    taus = np.array([.05, .50])
    coefficient = np.empty((len(taus), len(horizons)))
    lower = np.empty_like(coefficient)
    upper = np.empty_like(coefficient)
    for h_i, h in enumerate(horizons):
        sample = horizon_target(frame, h)
        beta = fit_grid(sample, taus, target="growth_h")
        interval = bootstrap_coefficients(sample, taus, "growth_h", draws=80, block=8, seed=20260808 + h)
        coefficient[:, h_i] = beta[:, 3]
        lower[:, h_i] = interval[0, :, 3]
        upper[:, h_i] = interval[1, :, 3]
    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    for i, (tau, colour) in enumerate(zip(taus, [RED, BLUE])):
        ax.fill_between(horizons, lower[i], upper[i], color=colour, alpha=.18)
        ax.plot(horizons, coefficient[i], "o-", color=colour, lw=2, ms=5, label=rf"$\tau={tau:.2f}$")
    ax.axhline(0, color="black", lw=.8)
    ax.set(
        xticks=horizons,
        xlabel="forecast horizon (quarters)",
        ylabel="NFCI coefficient",
        title="A term structure of conditional growth: financial conditions at several horizons",
    )
    ax.legend(title="forecast quantile", frameon=True)
    ax.text(.01, -.22, "Shaded areas are 90% moving-block bootstrap intervals. NFCI > 0 denotes tighter-than-average financial conditions.", transform=ax.transAxes, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(FIGURES / "gar-term-structure.png", bbox_inches="tight")
    plt.close(fig)


def backtest_figure(frame):
    """Recursive 5% forecast: only previously observed outcomes enter estimation."""
    tau, initial = .05, 80
    predictions, actual, dates = [], [], []
    for position in range(initial + HORIZON, len(frame)):
        train = frame.iloc[: position - HORIZON]
        beta = fit_grid(train, np.array([tau]))[0]
        _, x_test = design(frame.iloc[[position]])
        predictions.append((x_test @ beta).item())
        actual.append(frame.iloc[position].growth_4q_ahead)
        dates.append(frame.iloc[position].date)
    out = pd.DataFrame({"date": dates, "forecast": predictions, "actual": actual})
    out["hit"] = (out.actual <= out.forecast).astype(float)
    out["rolling_coverage"] = out.hit.rolling(20, min_periods=8).mean()
    fig, axes = plt.subplots(2, 1, figsize=(11.4, 6.6), sharex=True, gridspec_kw={"height_ratios": [1.35, 1]})
    axes[0].plot(out.date, out.actual, color=GREY, lw=1, label="realised four-quarter growth")
    axes[0].plot(out.date, out.forecast, color=RED, lw=1.8, label="recursive 5% quantile forecast")
    breach = out.hit == 1
    axes[0].scatter(out.date[breach], out.actual[breach], color=RED, s=22, zorder=3, label="realisation below forecast")
    axes[0].axhline(0, color="black", lw=.7)
    axes[0].set(ylabel="percent", title="Out-of-sample tail forecasts must be judged by their failures")
    axes[0].legend(ncol=3, fontsize=8.3, frameon=True, loc="lower left")
    axes[1].plot(out.date, out.rolling_coverage, color=PURPLE, lw=1.8, label="20-origin rolling breach frequency")
    axes[1].axhline(tau, color=RED, ls=":", lw=1.8, label="nominal 5% frequency")
    axes[1].axhline(out.hit.mean(), color=GREY, ls="--", lw=1.2, label=f"overall frequency: {out.hit.mean():.1%}")
    axes[1].set(ylim=(0, max(.25, out.rolling_coverage.max() + .03)), ylabel="share of breaches", xlabel="forecast origin")
    axes[1].legend(ncol=3, fontsize=8.3, frameon=True, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES / "gar-recursive-backtest.png", bbox_inches="tight")
    plt.close(fig)


def distributional_var_diagram():
    """A course-native map from marginal distribution models to a DIRF."""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.35), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    ax.set(xlim=(0, 10), ylim=(0, 6.2)); ax.axis("off")

    def box(x, y, text, colour):
        patch = FancyBboxPatch((x, y), 2.5, .85, boxstyle="round,pad=.08", facecolor=colour, edgecolor="#333333", linewidth=1)
        ax.add_patch(patch)
        ax.text(x + 1.25, y + .425, text, ha="center", va="center", fontsize=9)

    box(.3, 4.55, r"lags $Z_t$", "#e5e5e5")
    box(3.6, 4.55, r"$F_{Y_1\mid Z}$", "#d1e5f0")
    box(3.6, 2.3, r"$F_{Y_2\mid Y_1,Z}$", "#fddbc7")
    box(7.0, 3.42, r"joint $F_{Y\mid Z}$", "#d9f0d3")
    for start, end in [((2.85, 4.98), (3.55, 4.98)), ((6.15, 4.85), (6.95, 3.95)), ((6.15, 2.72), (6.95, 3.82)), ((4.85, 4.48), (4.85, 3.2))]:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#333333"})
    ax.text(4.85, 3.75, r"sample $Y_1$", ha="center", va="center", fontsize=8.2)
    ax.text(5, .75, "Factorise the joint distribution, then simulate coherent joint draws.", ha="center", fontsize=9.2)
    ax.set_title("From marginal conditional CDFs to a joint forecast", fontsize=11)

    ax = axes[1]
    grid = np.linspace(-3.2, 3.2, 400)
    baseline = 1 / (1 + np.exp(-1.25 * grid))
    counterfactual = 1 / (1 + np.exp(-1.25 * (grid + .8)))
    ax.plot(grid, baseline, color=BLUE, lw=2.3, label=r"baseline $F_{t+h\mid Z_t}$")
    ax.plot(grid, counterfactual, color=RED, lw=2.3, label=r"counterfactual $F^*_{t+h\mid Z_t}$")
    ax.fill_between(grid, baseline, counterfactual, where=counterfactual >= baseline, color=PURPLE, alpha=.16, label=r"difference: DIR$_h$")
    ax.axhline(.05, color=GREY, lw=.8, ls=":")
    ax.set(xlabel="future outcome", ylabel="conditional CDF", ylim=(0, 1), title="A distributional response is a difference between CDFs")
    ax.legend(frameon=True, fontsize=8.1, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES / "distributional-var-factorization.png", bbox_inches="tight")
    plt.close(fig)


def main():
    frame = prepare_data()
    beta = fit_grid(frame)
    intervals = bootstrap_coefficients(frame, QUANTILES, "growth_4q_ahead")
    check_loss_figure()
    coefficient_figure(frame, beta, intervals)
    quantile_curve_figure(frame, beta)
    fan_chart_figure(frame, beta)
    term_structure_figure(frame)
    backtest_figure(frame)
    distributional_var_diagram()
    print(f"saved {len(frame)} observations to {DATA}")


if __name__ == "__main__":
    main()
