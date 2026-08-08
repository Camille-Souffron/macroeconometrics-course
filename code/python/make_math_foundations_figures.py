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


def bases_and_span():
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.1), sharex=True, sharey=True)
    limits = dict(xlim=(-2.6, 3.1), ylim=(-2.3, 2.7), aspect="equal")
    # A basis: two independent directions spanning the plane.
    ax = axes[0]
    u, v, x = np.array([1.6, .25]), np.array([.35, 1.35]), np.array([1.95, 1.6])
    _arrow(ax, (0, 0), u, BLUE, "$u$")
    _arrow(ax, (0, 0), v, RED, "$v$")
    _arrow(ax, (0, 0), x, PURPLE, "$x= u+v$")
    ax.set(title="A free family gives unique coordinates", **limits)
    # A linked family: all generated vectors stay on the same line.
    ax = axes[1]
    u, v = np.array([1.4, .7]), np.array([2.1, 1.05])
    line = np.column_stack([np.linspace(-2.5, 3, 100), .5 * np.linspace(-2.5, 3, 100)])
    ax.plot(line[:, 0], line[:, 1], color="#c7c7c7", lw=2)
    _arrow(ax, (0, 0), u, BLUE, "$u$")
    _arrow(ax, (0, 0), v, RED, "$v=1.5u$")
    ax.set(title="A linked family spans only a line", **limits)
    # A subspace: a line through origin, contrasted with a translated affine line.
    ax = axes[2]
    z = np.linspace(-2.5, 3, 100)
    ax.plot(z, -.45 * z, color=PURPLE, lw=2.4, label=r"$\mathrm{Vect}(w)$")
    ax.plot(z, -.45 * z + 1.1, color="#999999", ls=":", lw=2, label="translated line")
    _arrow(ax, (0, 0), np.array([1.5, -.675]), PURPLE, "$w$")
    ax.scatter(0, 0, color="black", s=16)
    ax.set(title="A vector subspace must contain zero", **limits)
    ax.legend(frameon=True, fontsize=9, loc="lower left")
    for ax in axes:
        ax.axhline(0, color="black", lw=.65)
        ax.axvline(0, color="black", lw=.65)
        ax.set_xlabel("first coordinate")
    axes[0].set_ylabel("second coordinate")
    fig.tight_layout()
    fig.savefig(FIGURES / "bases-span-and-subspaces.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def dimensions_and_products():
    fig, ax = plt.subplots(figsize=(10.5, 3.2))
    ax.axis("off")
    boxes = [
        (.05, .35, .23, .34, BLUE, r"$x\in R^n$"),
        (.39, .35, .23, .34, RED, r"$A\in R^{m\times n}$"),
        (.73, .35, .23, .34, PURPLE, r"$Ax\in R^m$"),
    ]
    for left, bottom, width, height, color, text in boxes:
        rect = plt.Rectangle((left, bottom), width, height, facecolor=color, alpha=.16, edgecolor=color, lw=2)
        ax.add_patch(rect)
        ax.text(left + width / 2, bottom + height / 2, text, ha="center", va="center", fontsize=17, color=color)
    ax.annotate("", xy=(.37, .52), xytext=(.29, .52), arrowprops={"arrowstyle": "->", "lw": 2})
    ax.annotate("", xy=(.71, .52), xytext=(.63, .52), arrowprops={"arrowstyle": "->", "lw": 2})
    ax.text(.5, .17, r"The inner dimensions $n$ match; the product has the outer dimension $m$.", ha="center", fontsize=13)
    ax.text(.5, .83, r"For $AB$, the number of columns of $A$ must equal the number of rows of $B$.", ha="center", fontsize=14)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    fig.tight_layout()
    fig.savefig(FIGURES / "matrix-vector-dimensions.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def determinant_and_invertibility():
    transforms = [
        (np.array([[1.35, .35], [.25, .85]]), "non-zero determinant: area survives", BLUE),
        (np.array([[1.0, .55], [.5, .275]]), "zero determinant: the plane collapses", RED),
    ]
    grid = np.linspace(-1.8, 1.8, 11)
    square = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), sharex=True, sharey=True)
    for ax, (matrix, title, color) in zip(axes, transforms):
        for value in grid:
            horizontal = np.column_stack([grid, np.full_like(grid, value)]) @ matrix.T
            vertical = np.column_stack([np.full_like(grid, value), grid]) @ matrix.T
            ax.plot(horizontal[:, 0], horizontal[:, 1], color="#c7c7c7", lw=.8)
            ax.plot(vertical[:, 0], vertical[:, 1], color="#c7c7c7", lw=.8)
        image = square @ matrix.T
        ax.fill(image[:, 0], image[:, 1], color=color, alpha=.22)
        ax.plot(image[:, 0], image[:, 1], color=color, lw=2.2)
        det = np.linalg.det(matrix)
        ax.axhline(0, color="black", lw=.65)
        ax.axvline(0, color="black", lw=.65)
        ax.set(title=title + f"\n$\\det(A)={det:.2f}$", xlim=(-3, 3), ylim=(-2.5, 2.5), aspect="equal", xlabel="$x_1$")
    axes[0].set_ylabel("$x_2$")
    fig.tight_layout()
    fig.savefig(FIGURES / "determinant-invertibility.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def systems_geometry():
    x = np.linspace(-1, 6, 200)
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8), sharex=True, sharey=True)
    cases = [
        ((x, 4 - .65 * x, x, .35 + .55 * x), "one intersection\nunique solution", BLUE),
        ((x, 3.7 - .55 * x, x, 2.4 - .55 * x), "parallel lines\nno solution", RED),
        ((x, 3.2 - .55 * x, x, 3.2 - .55 * x), "same line\ninfinitely many solutions", PURPLE),
    ]
    for ax, ((x1, y1, x2, y2), title, color) in zip(axes, cases):
        ax.plot(x1, y1, color=BLUE, lw=2.2, label="first equation")
        ax.plot(x2, y2, color=color, lw=2.2, ls="--", label="second equation")
        ax.set(title=title, xlim=(-.5, 5.5), ylim=(-.5, 4.5), aspect="equal", xlabel="$x_1$")
        ax.axhline(0, color="black", lw=.65)
        ax.axvline(0, color="black", lw=.65)
    axes[0].set_ylabel("$x_2$")
    axes[0].legend(frameon=True, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIGURES / "linear-systems-geometry.png", dpi=180, bbox_inches="tight")
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


def distribution_moments():
    x = np.linspace(-5, 7, 800)
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2))
    axes[0, 0].plot(x, stats.norm.pdf(x, 0, 1), color=BLUE, lw=2, label=r"$\mu=0$")
    axes[0, 0].plot(x, stats.norm.pdf(x, 1.5, 1), color=RED, lw=2, label=r"$\mu=1.5$")
    axes[0, 0].set(title="First moment: location", xlabel="$x$", ylabel="density")
    axes[0, 0].legend(frameon=True)
    axes[0, 1].plot(x, stats.norm.pdf(x, 0, .55), color=BLUE, lw=2, label=r"$\sigma=0.55$")
    axes[0, 1].plot(x, stats.norm.pdf(x, 0, 1.5), color=RED, lw=2, label=r"$\sigma=1.5$")
    axes[0, 1].set(title="Second moment: dispersion", xlabel="$x$", ylabel="density")
    axes[0, 1].legend(frameon=True)
    gamma_x = np.linspace(0, 8, 800)
    gamma_pdf = stats.gamma.pdf(gamma_x, a=2, scale=1)
    # Standardise the Gamma variable to make asymmetry visible independently of location and scale.
    axes[1, 0].plot(x, stats.norm.pdf(x), color=BLUE, lw=2, label="symmetric Normal")
    axes[1, 0].plot((gamma_x - 2) / np.sqrt(2), gamma_pdf * np.sqrt(2), color=GOLD, lw=2, label="standardised Gamma")
    axes[1, 0].set(title="Third moment: skewness", xlabel="standardised value", ylabel="density")
    axes[1, 0].legend(frameon=True)
    axes[1, 1].plot(x, stats.norm.pdf(x), color=BLUE, lw=2, label="Normal")
    axes[1, 1].plot(x, stats.t.pdf(x * np.sqrt(3 / 5), 5) * np.sqrt(3 / 5), color=PURPLE, lw=2, label=r"variance-one $t_5$")
    axes[1, 1].set(title="Fourth moment: tail weight", xlabel="standardised value", ylabel="density")
    axes[1, 1].legend(frameon=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "distribution-four-moments.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def basic_distributions():
    k = np.arange(0, 13)
    x = np.linspace(0, 5, 700)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    axes[0].bar([0, 1], [0.7, .3], color=["#92c5de", BLUE], width=.55, alpha=.85, label="Bernoulli, $p=.3$")
    axes[0].plot(k, stats.binom.pmf(k, 10, .3), color=RED, marker="o", ms=3.5, lw=1.8, label="Binomial, $n=10, p=.3$")
    axes[0].plot(k, stats.poisson.pmf(k, 3), color=PURPLE, marker="s", ms=3.5, lw=1.6, label=r"Poisson, $\lambda=3$")
    axes[0].set(title="Discrete laws count possible outcomes", xlabel="outcome or count", ylabel="probability", xlim=(-.6, 12.4), ylim=(0, .78))
    axes[0].legend(frameon=True, fontsize=8.4)
    rate = .7
    axes[1].plot(x, stats.expon.pdf(x, scale=1 / rate), color=GOLD, lw=2.2, label="density, rate 0.7")
    axes[1].plot(x, stats.expon.sf(x, scale=1 / rate), color=RED, lw=2, label="survival probability")
    axes[1].fill_between(x, 0, stats.expon.pdf(x, scale=1 / rate), color=GOLD, alpha=.14)
    axes[1].set(title="The Exponential law measures waiting time", xlabel="waiting time", ylabel="density or probability")
    axes[1].legend(frameon=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "basic-distributions.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def ols_geometry():
    rng = np.random.default_rng(11)
    x = rng.uniform(-2.4, 2.4, 40)
    y = 1.0 + 1.35 * x + rng.normal(scale=.8, size=len(x))
    beta = np.polyfit(x, y, 1)
    grid = np.linspace(-2.6, 2.6, 100)
    i = np.argmax(np.abs(y - np.polyval(beta, x)))
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.35))
    axes[0].scatter(x, y, color=BLUE, s=28, alpha=.85, label="observations")
    axes[0].plot(grid, np.polyval(beta, grid), color=RED, lw=2.2, label="OLS fitted line")
    axes[0].plot([x[i], x[i]], [np.polyval(beta, x[i]), y[i]], color=PURPLE, lw=2)
    axes[0].text(x[i] + .06, (y[i] + np.polyval(beta, x[i])) / 2, "residual", color=PURPLE)
    axes[0].set(title="OLS minimises squared vertical residuals", xlabel="$x_i$", ylabel="$y_i$")
    axes[0].legend(frameon=True)
    ax = axes[1]
    ax.set(xlim=(-.15, 3.2), ylim=(-.15, 2.8), aspect="equal", title="In vector form, fitted values are a projection")
    ax.axhline(0, color="black", lw=.7)
    ax.axvline(0, color="black", lw=.7)
    _arrow(ax, (0, 0), (2.55, 0), RED, r"$\hat y=X\hat\beta$")
    _arrow(ax, (2.55, 0), (2.55, 1.65), PURPLE, r"$e=y-\hat y$")
    _arrow(ax, (0, 0), (2.55, 1.65), BLUE, "$y$")
    ax.plot([2.35, 2.35, 2.55], [0, .2, .2], color="black", lw=1)
    ax.text(.3, 2.25, r"$e$ is orthogonal to the column space of $X$", fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(FIGURES / "ols-geometry-projection.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def hypothesis_testing():
    x = np.linspace(-4, 5, 1000)
    h0 = stats.norm.pdf(x)
    h1 = stats.norm.pdf(x, loc=1.35)
    critical = stats.norm.ppf(.95)
    fig, ax = plt.subplots(figsize=(9.2, 4.3))
    ax.plot(x, h0, color=BLUE, lw=2.2, label=r"sampling distribution under $H_0$")
    ax.plot(x, h1, color=RED, lw=2.2, label=r"sampling distribution under $H_1$")
    ax.fill_between(x[x >= critical], 0, h0[x >= critical], color=BLUE, alpha=.25, label=r"Type I error $\alpha$")
    ax.fill_between(x[x < critical], 0, h1[x < critical], color=RED, alpha=.20, label=r"Type II error $\beta$")
    ax.axvline(critical, color="black", ls=":", lw=1.5)
    ax.text(critical + .05, ax.get_ylim()[1] * .89, "critical value", rotation=90, va="top")
    ax.set(title="A test trades false alarms against missed effects", xlabel="test statistic", ylabel="density", xlim=(-3.5, 4.5))
    ax.legend(frameon=True, ncol=2, fontsize=8.7)
    fig.tight_layout()
    fig.savefig(FIGURES / "hypothesis-testing-errors.png", dpi=180, bbox_inches="tight")
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
    bases_and_span()
    dimensions_and_products()
    determinant_and_invertibility()
    systems_geometry()
    stability_portraits()
    llm_and_clt()
    sampling_distributions()
    distribution_moments()
    basic_distributions()
    ols_geometry()
    hypothesis_testing()
    stochastic_processes()
    bayesian_update()
    fourier_signal()
