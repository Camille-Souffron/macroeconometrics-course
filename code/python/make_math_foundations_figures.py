"""Reproducible figures for the mathematical foundations chapter."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "figures" / "mathematics"
FIGURES.mkdir(parents=True, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
BLUE, RED, GOLD, PURPLE, GREY = "#2166ac", "#b2182b", "#d6604d", "#542788", "#4d4d4d"


def _arrow(ax, start, end, color, label=None):
    ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 2.2, "color": color})
    if label:
        ax.text(end[0], end[1], label, color=color, fontsize=11, ha="left", va="bottom")


def linear_transformation():
    matrix = np.array([[1.15, 0.65], [0.25, 0.65]])
    grid = np.linspace(-2.2, 2.2, 11)
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), sharex=True, sharey=True)
    for ax, transform, title in [
        (axes[0], np.eye(2), "A vector space before the transformation"),
        (axes[1], matrix, "The same space after a linear transformation"),
    ]:
        for value in grid:
            horizontal = np.column_stack([grid, np.full_like(grid, value)]) @ transform.T
            vertical = np.column_stack([np.full_like(grid, value), grid]) @ transform.T
            ax.plot(horizontal[:, 0], horizontal[:, 1], color="#c7c7c7", lw=.75)
            ax.plot(vertical[:, 0], vertical[:, 1], color="#c7c7c7", lw=.75)
        ax.axhline(0, color="black", lw=.7)
        ax.axvline(0, color="black", lw=.7)
        ax.set(title=title, xlim=(-3.2, 3.8), ylim=(-3.2, 3.8), aspect="equal", xlabel="$x_1$")
    axes[0].set_ylabel("$x_2$")
    x = np.array([1.4, .8])
    _arrow(axes[0], (0, 0), x, BLUE, "$x$")
    _arrow(axes[1], (0, 0), matrix @ x, RED, "$Ax$")
    for value, vector in zip(eigenvalues, eigenvectors.T):
        vector = np.real(vector) / np.linalg.norm(vector)
        _arrow(axes[1], (0, 0), 2.5 * vector, PURPLE, rf"$v$, $\lambda={value:.2f}$")
    fig.tight_layout()
    fig.savefig(FIGURES / "linear-transformation-eigenvectors.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def stability_portraits():
    matrices = [
        (np.array([[.78, -.30], [.30, .78]]), "damped oscillation", BLUE),
        (np.array([[1.04, -.30], [.30, 1.04]]), "explosive oscillation", RED),
    ]
    starts = np.array([[1.5, 0], [0, 1.5], [-1.2, .7], [-.8, -1.3], [1.1, -1.0]])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharex=True, sharey=True)
    for ax, (matrix, title, color) in zip(axes, matrices):
        for start in starts:
            path = [start]
            for _ in range(18):
                path.append(matrix @ path[-1])
            path = np.asarray(path)
            ax.plot(path[:, 0], path[:, 1], color=color, alpha=.85, lw=1.5)
            ax.scatter(path[0, 0], path[0, 1], color=color, s=16)
        values = np.linalg.eigvals(matrix)
        ax.axhline(0, color="black", lw=.7)
        ax.axvline(0, color="black", lw=.7)
        ax.set(title=title + f"\n$|\\lambda|={np.abs(values[0]):.2f}$", xlim=(-3, 3), ylim=(-3, 3), aspect="equal", xlabel="$x_{1,t}$")
    axes[0].set_ylabel("$x_{2,t}$")
    fig.tight_layout()
    fig.savefig(FIGURES / "matrix-stability-phase-portraits.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def llm_and_clt():
    rng = np.random.default_rng(20260808)
    population_mean = 1.0
    sample = rng.exponential(scale=1, size=2000)
    running_mean = np.cumsum(sample) / np.arange(1, len(sample) + 1)
    means = rng.exponential(scale=1, size=(10000, 40)).mean(axis=1)
    z = np.linspace(-4, 4, 600)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    axes[0].plot(np.arange(1, len(sample) + 1), running_mean, color=BLUE, lw=1.4)
    axes[0].axhline(population_mean, color=RED, lw=1.8, ls=":", label="population mean")
    axes[0].set(title="Law of large numbers", xlabel="number of observations", ylabel="running sample mean", ylim=(.55, 1.7))
    axes[0].legend(frameon=True)
    axes[1].hist(np.sqrt(40) * (means - 1), bins=45, density=True, color="#92c5de", edgecolor="white", label="10,000 sample means")
    axes[1].plot(z, stats.norm.pdf(z), color=RED, lw=2, label="standard Normal density")
    axes[1].set(title="Central limit theorem", xlabel=r"$\sqrt{n}(\bar X_n-\mu)/\sigma$", ylabel="density")
    axes[1].legend(frameon=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "lln-clt-simulation.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def sampling_distributions():
    x = np.linspace(-4.5, 6.5, 800)
    positive = np.linspace(.001, 12, 800)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    axes[0].plot(x, stats.norm.pdf(x), color=BLUE, lw=2, label="Normal")
    axes[0].plot(x, stats.t.pdf(x, 5), color=RED, lw=2, label="Student $t_5$")
    axes[0].set(title="Unknown scale gives heavier tails", xlabel="standardised statistic", ylabel="density")
    axes[0].legend(frameon=True)
    axes[1].plot(positive, stats.chi2.pdf(positive, 5), color=PURPLE, lw=2, label=r"$\chi^2_5$")
    axes[1].plot(positive, stats.f.pdf(positive, 5, 20), color=GOLD, lw=2, label="$F_{5,20}$")
    axes[1].set(title="Variance and variance ratios", xlabel="statistic", ylabel="density", xlim=(0, 8))
    axes[1].legend(frameon=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "sampling-distributions.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def stochastic_processes():
    rng = np.random.default_rng(42)
    innovation = rng.normal(scale=.8, size=180)
    ar = np.zeros(180)
    rw = np.zeros(180)
    for t in range(1, len(ar)):
        ar[t] = .85 * ar[t - 1] + innovation[t]
        rw[t] = rw[t - 1] + innovation[t]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharex=True)
    axes[0].plot(ar, color=BLUE, lw=1.6)
    axes[0].axhline(0, color="black", lw=.7)
    axes[0].set(title=r"Stationary AR(1): $X_t=.85X_{t-1}+\varepsilon_t$", xlabel="quarter", ylabel="level")
    axes[1].plot(rw, color=RED, lw=1.6)
    axes[1].set(title=r"Unit root: $X_t=X_{t-1}+\varepsilon_t$", xlabel="quarter")
    fig.tight_layout()
    fig.savefig(FIGURES / "stationary-ar-versus-random-walk.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def bayesian_update():
    grid = np.linspace(-1.8, 3.2, 700)
    prior = stats.norm.pdf(grid, 0, 1)
    likelihood = stats.norm.pdf(grid, 1.25, .55)
    posterior = prior * likelihood
    posterior /= np.trapezoid(posterior, grid)
    fig, ax = plt.subplots(figsize=(8.5, 4.1))
    ax.plot(grid, prior, color=BLUE, lw=2, label="prior")
    ax.plot(grid, likelihood / likelihood.max() * prior.max(), color=GOLD, lw=2, label="likelihood, rescaled")
    ax.plot(grid, posterior, color=RED, lw=2.4, label="posterior")
    ax.fill_between(grid, 0, posterior, color=RED, alpha=.12)
    ax.set(title="Bayes' rule combines a prior with the information in the sample", xlabel="unknown parameter $\theta$", ylabel="density, up to scale")
    ax.legend(frameon=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "bayesian-update.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def fourier_signal():
    rng = np.random.default_rng(7)
    t = np.arange(160)
    signal = 1.2 * np.sin(2 * np.pi * t / 24) + .55 * np.sin(2 * np.pi * t / 7) + .25 * rng.normal(size=len(t))
    freq = np.fft.rfftfreq(len(t), d=1)
    power = np.abs(np.fft.rfft(signal - signal.mean())) ** 2 / len(t)
    period = 1 / freq[1:]
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 5.5))
    axes[0].plot(t, signal, color=BLUE, lw=1.3)
    axes[0].set(title="A time series can contain several rhythms at once", xlabel="observation", ylabel="value")
    order = np.argsort(period)
    axes[1].plot(period[order], power[1:][order], color=PURPLE, lw=1.6)
    for value, text in [(7, "7"), (24, "24")]:
        axes[1].axvline(value, color=RED, lw=1, ls=":")
        axes[1].text(value, axes[1].get_ylim()[1] * .83, f"period {text}", color=RED, ha="center")
    axes[1].set(xlim=(2, 50), title="The discrete Fourier transform reveals those rhythms", xlabel="period (observations)", ylabel="periodogram")
    fig.tight_layout()
    fig.savefig(FIGURES / "fourier-time-and-frequency.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    linear_transformation()
    stability_portraits()
    llm_and_clt()
    sampling_distributions()
    stochastic_processes()
    bayesian_update()
    fourier_signal()
