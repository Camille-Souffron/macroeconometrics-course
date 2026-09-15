"""Independent mathematical checks for the worked examples and visual data."""
import numpy as np
import pytest
import sympy as sp
from scipy.integrate import quad
from scipy.optimize import minimize
from scipy.stats import norm
from models import JACOBIAN, nonlinear, allocation, loss, sampling_density, posterior


def test_jacobian_and_taylor_identity():
    x,y=sp.symbols("x y")
    G=sp.Matrix([x+sp.Rational(2,5)*y+sp.Rational(3,25)*x*x,
                 -x/5+sp.Rational(4,5)*y+sp.Rational(2,25)*y*y])
    J=G.jacobian([x,y]).subs({x:0,y:0})
    np.testing.assert_allclose(np.array(J).astype(float),JACOBIAN)
    assert G-J*sp.Matrix([x,y]) == sp.Matrix([sp.Rational(3,25)*x*x,sp.Rational(2,25)*y*y])
    rng=np.random.default_rng(13)
    for _ in range(30):
        h=rng.normal(size=2)
        np.testing.assert_allclose(nonlinear(h/2)-JACOBIAN@(h/2),
                                   (nonlinear(h)-JACOBIAN@h)/4,atol=1e-14)


@pytest.mark.parametrize("b",[.05,.25,.49,.5,.51,1,1.99,2,2.01,3])
def test_kkt_against_independent_constrained_solver(b):
    x,y,mu,nu_x,nu_y=allocation(b)
    np.testing.assert_allclose([2*(x-1)+mu-nu_x,4*(y-1)+mu-nu_y],0,atol=1e-12)
    g=np.array([x+y-b,-x,-y]);multipliers=np.array([mu,nu_x,nu_y])
    assert np.max(g)<=1e-12 and np.min(multipliers)>=0
    np.testing.assert_allclose(g*multipliers,0,atol=1e-12)
    result=minimize(lambda z:loss(*z),[b/3,b/3],bounds=[(0,None),(0,None)],
                    constraints={"type":"ineq","fun":lambda z:b-z.sum()},
                    method="SLSQP",options={"ftol":1e-12})
    assert result.success
    np.testing.assert_allclose(result.x,[x,y],atol=2e-6)
    eps=1e-5
    derivative=(loss(*allocation(b+eps)[:2])-loss(*allocation(b-eps)[:2]))/(2*eps)
    assert derivative == pytest.approx(-mu,abs=2e-5)


def test_household_and_constrained_hessian():
    c,w,beta,R=sp.symbols("c w beta R",positive=True)
    u=sp.log(c)+beta*sp.log(R*(w-c))
    assert sp.simplify(sp.diff(u,c).subs(c,w/(1+beta)))==0
    x,y=sp.symbols("x y")
    lag=y+(x*x-y)
    assert sp.hessian(lag,[x,y])==sp.diag(2,0)


def test_log_remainder_bound_and_exercise():
    g=sp.symbols("g")
    assert sp.series(sp.log(1+g),g,0,3).removeO()==g-g*g/2
    for z in np.linspace(-.7,.7,281):
        error=abs(np.log1p(z)-(z-z*z/2))
        bound=abs(z)**3/(3*(1-abs(z))**3)
        assert error<=bound+1e-15
    assert abs(np.log(.9)+.105)==pytest.approx(.0003605156578263)


@pytest.mark.parametrize("n",[2,4,8,16,64])
def test_exact_sampling_density_moments(n):
    lo=-np.sqrt(n)
    assert quad(lambda z:sampling_density(z,n),lo,np.inf)[0]==pytest.approx(1,abs=1e-9)
    assert quad(lambda z:z*sampling_density(z,n),lo,np.inf)[0]==pytest.approx(0,abs=1e-9)
    assert quad(lambda z:z*z*sampling_density(z,n),lo,np.inf)[0]==pytest.approx(1,abs=1e-9)


def test_projection_and_spectral_examples():
    v=np.array([1,2,3]);y=np.array([1,2,4])
    fitted=v*(17/14)
    assert v@(y-fitted)==pytest.approx(0,abs=1e-14)
    A=sp.Matrix([[sp.Rational(7,10),sp.Rational(2,10)],[sp.Rational(1,10),sp.Rational(8,10)]])
    assert set(A.eigenvals())=={sp.Rational(9,10),sp.Rational(6,10)}
    t=np.arange(48);signal=np.cos(2*np.pi*t/12)+.55*np.cos(2*np.pi*t/4)
    transform=np.fft.fft(signal)
    np.testing.assert_allclose(np.fft.ifft(transform).real,signal,atol=1e-14)
    assert np.sum(signal**2)==pytest.approx(np.sum(abs(transform)**2)/48)
    assert set(np.where(abs(transform)>1e-8)[0])=={4,12,36,44}


def test_normal_quantile_bayes_and_markov():
    c=norm.ppf(.975)
    assert 2*norm.sf(c)==pytest.approx(.05)
    for n in [0,1,4,40]:
        mean,var=posterior(n)
        assert mean==pytest.approx(n/(n+4))
        assert var==pytest.approx(4/(n+4))
    p=np.array([[.92,.08],[.35,.65]])
    pi=np.array([35/43,8/43])
    np.testing.assert_allclose(pi@p,pi)
    assert .8*.05/(.8*.05+.1*.95)==pytest.approx(8/27)


def test_statanim_geometry_when_installed(tmp_path):
    # Rendering environment only; CI does not need native Manim dependencies.
    pytest.importorskip("manim")
    from manim import config
    config.media_dir=str(tmp_path)
    from scenes import Lesson, statanim_normal
    scene=Lesson()
    axes=scene.axes([-4,4,1],[0,.5,.1],10,4)
    stroke=statanim_normal(axes)
    origin=axes.c2p(0,0)
    vertical_unit=np.linalg.norm(axes.c2p(0,1)-origin)
    # Peak must represent a true density, not a library-normalised unit peak.
    assert (stroke.get_top()[1]-origin[1])/vertical_unit==pytest.approx(norm.pdf(0),abs=1e-7)
