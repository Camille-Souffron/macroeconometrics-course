"""Reproducible figures for the frequency-domain chapter.

The empirical series is U.S. real GDP (GDPC1), downloaded from FRED.  The
script deliberately implements the filters in a few lines rather than hiding
their mechanics behind a package API.
"""

from pathlib import Path
from urllib.request import urlopen

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal


ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "figures" / "frequency"
DATA = ROOT / "data" / "us_real_gdp_fred.csv"
HOURS_SPREAD_DATA = ROOT / "data" / "us_hours_baa_spread_fred.csv"
FIGURES.mkdir(parents=True, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
BLUE, RED, GOLD, GREY = "#2166ac", "#b2182b", "#d6604d", "#4d4d4d"


def hp_cycle(y, lam=1600.0):
    """HP cycle: (I - (I + lambda D'D)^-1)y, including end observations."""
    n = len(y)
    d = np.zeros((n - 2, n))
    rows = np.arange(n - 2)
    d[rows, rows] = 1.0
    d[rows, rows + 1] = -2.0
    d[rows, rows + 2] = 1.0
    trend = np.linalg.solve(np.eye(n) + lam * d.T @ d, y)
    return y - trend, trend


def hamilton_cycle(y, h=8, p=4):
    """Hamilton's (2018) h-step-ahead regression filter for quarterly data."""
    n = len(y)
    # y[t+h] on a constant and y[t],...,y[t-p+1], t = p-1,...,n-h-1
    t = np.arange(p - 1, n - h)
    x = np.column_stack([np.ones(len(t))] + [y[t - j] for j in range(p)])
    beta = np.linalg.lstsq(x, y[t + h], rcond=None)[0]
    cycle = np.full(n, np.nan)
    cycle[t + h] = y[t + h] - x @ beta
    return cycle


def periodogram(x):
    """One-sided periodogram with frequency in cycles per quarter."""
    freq, power = signal.periodogram(x - np.mean(x), scaling="density")
    return freq[1:], power[1:]


def smoothed_cross_spectrum(x, y, nfft=1024, width=13):
    """Hamming-smoothed auto- and cross-spectra, as in the supplied appendix."""
    x, y = np.asarray(x) - np.mean(x), np.asarray(y) - np.mean(y)
    x_fft, y_fft = np.fft.rfft(x, n=nfft), np.fft.rfft(y, n=nfft)
    scale = 2 * np.pi * len(x)
    kernel = np.hamming(width)
    kernel /= kernel.sum()
    smooth = lambda z: np.convolve(z, kernel, mode="same")
    s_xx = smooth(np.abs(x_fft) ** 2 / scale)
    s_yy = smooth(np.abs(y_fft) ** 2 / scale)
    s_yx = smooth(y_fft * np.conj(x_fft) / scale)
    frequency = np.fft.rfftfreq(nfft, d=1)
    coherence = np.clip(np.abs(s_yx) ** 2 / (s_xx * s_yy), 0, 1)
    beta = s_yx / s_xx
    return frequency[1:], s_xx[1:], s_yy[1:], s_yx[1:], coherence[1:], beta[1:]


def make_spectrum_and_gain():
    rng = np.random.default_rng(20260308)
    n = 240
    t = np.arange(n)
    # A stochastic low-frequency AR component plus a medium-frequency cycle.
    ar = np.zeros(n)
    innovations = rng.normal(size=n)
    for i in range(1, n):
        ar[i] = 0.92 * ar[i - 1] + innovations[i]
    cyc = 1.5 * np.sin(2 * np.pi * t / 28) + 0.4 * rng.normal(size=n)
    mixture = ar + cyc
    f_ar, p_ar = periodogram(ar)
    f_cyc, p_cyc = periodogram(cyc)
    f_mix, p_mix = periodogram(mixture)

    omega = np.linspace(0, np.pi, 1000)
    hp_gain = (16 * 1600 * np.sin(omega / 2) ** 4) / (
        1 + 16 * 1600 * np.sin(omega / 2) ** 4
    )
    diff_gain = 4 * np.sin(omega / 2) ** 2
    period = np.divide(2 * np.pi, omega, out=np.full_like(omega, np.inf), where=omega > 0)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(f_ar, p_ar, color=BLUE, lw=1.3, label="AR(1), $\\phi=0.92$")
    axes[0].plot(f_cyc, p_cyc, color=GOLD, lw=1.3, label="cycle around 28 quarters")
    axes[0].plot(f_mix, p_mix, color=GREY, lw=1.7, label="sum")
    axes[0].set(xlim=(0, 0.5), xlabel="Frequency (cycles per quarter)", ylabel="Periodogram")
    axes[0].set_title("Different sources of variance occupy different frequencies")
    axes[0].legend(frameon=True, fontsize=9)

    axes[1].plot(period, hp_gain, color=RED, lw=2, label="HP cycle, $\\lambda=1600$")
    axes[1].plot(period, diff_gain, color=BLUE, lw=2, label="first difference")
    axes[1].axvspan(6, 32, color="#fddbc7", alpha=0.55, label="conventional cycle band")
    axes[1].set(xlim=(2, 80), ylim=(0, 4.1), xlabel="Period (quarters; long periods to the right)", ylabel="Squared gain")
    axes[1].set_title("A filter is a frequency-dependent weighting rule")
    axes[1].legend(frameon=True, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES / "spectrum-and-filter-gain.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def make_gdp_filters():
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1"
    with urlopen(url, timeout=30) as response:
        DATA.write_bytes(response.read())
    gdp = pd.read_csv(DATA, parse_dates=["observation_date"]).dropna()
    gdp = gdp.rename(columns={"observation_date": "date", "GDPC1": "gdp"})
    gdp = gdp[gdp.date >= "1984-01-01"].reset_index(drop=True)
    y = 100 * np.log(gdp.gdp.to_numpy())
    hp, trend = hp_cycle(y)
    ham = hamilton_cycle(y)
    # A practical zero-phase band-pass approximation, retained only where its
    # 6-quarter padding is available. It makes the edge loss visible.
    bp = signal.sosfiltfilt(signal.butter(4, [1 / 32, 1 / 6], btype="bandpass", fs=1, output="sos"), y)
    bp[:6], bp[-6:] = np.nan, np.nan

    fig, axes = plt.subplots(2, 1, figsize=(11, 6.4), sharex=True, gridspec_kw={"height_ratios": [1, 1.25]})
    axes[0].plot(gdp.date, y, color=GREY, lw=1.4, label="log real GDP (×100)")
    axes[0].plot(gdp.date, trend, color=RED, lw=2, label="HP trend, $\\lambda=1600$")
    axes[0].set(ylabel="log points", title="U.S. real GDP and an HP trend")
    axes[0].legend(ncol=2, frameon=True, fontsize=9)
    axes[1].axhline(0, color="black", lw=0.7)
    axes[1].plot(gdp.date, hp, color=RED, lw=1.8, label="HP cycle")
    axes[1].plot(gdp.date, ham, color=BLUE, lw=1.5, label="Hamilton cycle (h=8, p=4)")
    axes[1].plot(gdp.date, bp, color=GOLD, lw=1.4, label="6–32-quarter band-pass")
    axes[1].set(ylabel="deviation / residual (log points)", title="The estimated cycle depends on the extraction rule")
    axes[1].legend(ncol=3, frameon=True, fontsize=9, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIGURES / "us-gdp-filter-comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def make_endpoint_revisions():
    gdp = pd.read_csv(DATA, parse_dates=["observation_date"]).dropna()
    gdp = gdp.rename(columns={"observation_date": "date", "GDPC1": "gdp"})
    gdp = gdp[gdp.date >= "2000-01-01"].reset_index(drop=True)
    y = 100 * np.log(gdp.gdp.to_numpy())
    full_cycle, _ = hp_cycle(y)
    cutoff = np.where(gdp.date.to_numpy() == np.datetime64("2019-10-01"))[0][0]
    vintage_cycle, _ = hp_cycle(y[: cutoff + 1])
    fig, ax = plt.subplots(figsize=(11, 4.3))
    ax.axhline(0, color="black", lw=0.7)
    ax.plot(gdp.date, full_cycle, color=RED, lw=2, label="HP cycle with full sample")
    ax.plot(gdp.date[: cutoff + 1], vintage_cycle, color=BLUE, lw=2, ls="--", label="same HP filter, data ending 2019Q4")
    ax.axvline(gdp.date.iloc[cutoff], color=GREY, lw=1, ls=":")
    ax.text(gdp.date.iloc[cutoff], ax.get_ylim()[1] * .84, "2019Q4", ha="right", color=GREY)
    ax.set(title="Two-sided filters revise history when the future arrives", ylabel="HP cycle (log points)")
    ax.legend(frameon=True, fontsize=9, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIGURES / "hp-endpoint-revisions.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def make_hours_spread_cross_spectrum():
    """Empirical cross-spectrum: hours and the Baa minus Treasury spread."""
    ids = ["HOANBS", "BAA10YM"]
    frames = []
    for series_id in ids:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        with urlopen(url, timeout=30) as response:
            frame = pd.read_csv(response, parse_dates=["observation_date"])
        frames.append(frame.rename(columns={"observation_date": "date", series_id: series_id}))
    hours, spread = frames
    # The credit spread is monthly. Averaging it within each quarter matches the
    # quarterly hours observation without inventing intra-quarter precision.
    spread = spread.set_index("date").resample("QS").mean().reset_index()
    data = hours.merge(spread, on="date", how="inner").dropna()
    data = data[data.date >= "1954-01-01"].reset_index(drop=True)
    data.to_csv(HOURS_SPREAD_DATA, index=False)
    time = np.arange(len(data))
    log_hours = 100 * np.log(data.HOANBS.to_numpy())
    # A linear trend is removed only to estimate a stationary second-order object;
    # the chapter contrasts this choice with the paper's high-pass robustness checks.
    hours_residual = log_hours - np.polyval(np.polyfit(time, log_hours, 1), time)
    spread_residual = data.BAA10YM.to_numpy() - data.BAA10YM.mean()
    frequency, s_h, s_s, s_sh, coherence, beta = smoothed_cross_spectrum(hours_residual, spread_residual)
    period = 1 / frequency
    keep = (period >= 4) & (period <= 80)
    order = np.argsort(period[keep])
    p = period[keep][order]
    s_h, s_s = s_h[keep][order], s_s[keep][order]
    coherence, beta = coherence[keep][order], beta[keep][order]
    # Unit-area spectra make their *shape* comparable despite different units.
    s_h /= np.trapezoid(s_h, p)
    s_s /= np.trapezoid(s_s, p)

    fig, axes = plt.subplots(2, 1, figsize=(11, 6.6), sharex=True)
    for ax in axes:
        ax.axvspan(32, 50, color="#d9d9d9", alpha=0.65, zorder=0)
        ax.set_xlim(4, 80)
    axes[0].plot(p, s_h, color=BLUE, lw=2, label="detrended business-sector hours")
    axes[0].plot(p, s_s, color=RED, lw=2, label="Baa minus 10-year Treasury spread")
    axes[0].set(title="Frequency content: labour utilisation and financial stress", ylabel="Normalised spectral density")
    axes[0].legend(frameon=True, fontsize=9)
    axes[1].plot(p, coherence, color="#542788", lw=2, label="squared coherence")
    beta_abs = np.abs(beta)
    beta_abs[coherence < .20] = np.nan
    axes[1].plot(p, beta_abs / np.nanmax(beta_abs), color=GOLD, lw=1.7, label="spectral-regression gain (scaled; coherence ≥ 0.20)")
    axes[1].set(ylim=(0, 1.05), xlabel="Period (quarters)", ylabel="Coherence / scaled gain")
    axes[1].legend(frameon=True, fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIGURES / "hours-spread-cross-spectrum.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    make_spectrum_and_gain()
    make_gdp_filters()
    make_endpoint_revisions()
    make_hours_spread_cross_spectrum()
