"""Mathematical examples shared by figures, scenes and independent checks."""
import numpy as np
from scipy.stats import gamma, norm


def nonlinear(x):
    x = np.asarray(x)
    return np.array([x[0] + .4*x[1] + .12*x[0]**2,
                     -.2*x[0] + .8*x[1] + .08*x[1]**2])


JACOBIAN = np.array([[1., .4], [-.2, .8]])


def allocation(b):
    """x, y, resource multiplier, lower-x multiplier, lower-y multiplier."""
    if b <= 0:
        raise ValueError("The worked example assumes b > 0.")
    if b < .5:
        return np.array([0., b, 4*(1-b), 2-4*b, 0.])
    if b < 2:
        return np.array([(2*b-1)/3, (b+1)/3, 4*(2-b)/3, 0., 0.])
    return np.array([1., 1., 0., 0., 0.])


def loss(x, y):
    return (x-1)**2 + 2*(y-1)**2


def sampling_density(z, n):
    """Exact density of sqrt(n) * (mean Exp(1) - 1)."""
    return np.sqrt(n) * gamma.pdf(n + np.sqrt(n)*np.asarray(z), a=n)


def normal_density(z):
    return norm.pdf(z)


def posterior(n):
    variance = 1 / (1 + n/4)
    return n/4 * variance, variance
