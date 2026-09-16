"""Independent mathematical checks for the worked examples and visual data."""
import numpy as np
import pytest
import sympy as sp
from scipy.integrate import quad
from scipy.optimize import minimize
from scipy.stats import chi2, f as fisher_f, norm, t as student_t
from models import JACOBIAN, nonlinear, allocation, loss, sampling_density, posterior


def test_span_coordinates_and_dependent_family():
    basis=sp.Matrix([[1,sp.Rational(-1,5)],[sp.Rational(1,2),1]])
    r,s=sp.symbols('r s')
    coefficients=sp.Matrix([(r+s/5)/sp.Rational(11,10),(s-r/2)/sp.Rational(11,10)])
    assert sp.simplify(basis*coefficients)==sp.Matrix([r,s])
    family=sp.Matrix([[1,0,1],[0,1,1]])
    assert family.rank()==2
    assert family*sp.Matrix([1,1,-1])==sp.zeros(2,1)


def test_norm_comparison_and_reference_law_exercises():
    rng=np.random.default_rng(271)
    for n in [1,2,5,20]:
        for _ in range(20):
            x=rng.normal(size=n)
            one=np.linalg.norm(x,1);two=np.linalg.norm(x,2);infinity=np.linalg.norm(x,np.inf)
            assert infinity<=two+1e-14
            assert two<=one+1e-14
            assert one<=np.sqrt(n)*two+1e-14
    coordinate=np.array([3.,0.,0.])
    assert np.linalg.norm(coordinate,np.inf)==np.linalg.norm(coordinate,2)==np.linalg.norm(coordinate,1)
    equal=np.ones(4)
    assert np.linalg.norm(equal,1)==pytest.approx(2*np.linalg.norm(equal,2))

    assert np.exp(-2)==pytest.approx(.1353352832366127)
    assert chi2.mean(9)==9 and chi2.var(9)==18
    tcrit=student_t.ppf(.975,9)
    assert fisher_f.cdf(tcrit*tcrit,1,9)==pytest.approx(.95)


def test_matrix_vector_and_composition_examples():
    M=sp.Matrix([[1,2,-1],[0,1,3]])
    x=sp.Matrix([2,1,-1])
    assert M*x==sp.Matrix([5,-2])
    assert sum((x[j]*M[:,j] for j in range(3)),sp.zeros(2,1))==M*x
    A=sp.Matrix([[1,1],[0,1]]);B=sp.diag(2,1);v=sp.ones(2,1)
    assert A*B==sp.Matrix([[2,1],[0,1]])
    assert B*A==sp.Matrix([[2,2],[0,1]])
    assert A*(B*v)==sp.Matrix([3,1])
    assert B*(A*v)==sp.Matrix([4,1])


def test_scalar_ols_matches_matrix_and_completed_squares():
    x=sp.Matrix([0,1,2,3]);y=sp.Matrix([1,2,2,4]);ones=sp.ones(4,1)
    X=ones.row_join(x)
    beta=(X.T*X).inv()*X.T*y
    assert beta==sp.Matrix([sp.Rational(9,10),sp.Rational(9,10)])
    residual=y-X*beta
    assert residual==sp.Matrix([sp.Rational(1,10),sp.Rational(2,10),sp.Rational(-7,10),sp.Rational(4,10)])
    assert (residual.T*residual)[0]==sp.Rational(7,10)
    assert X.T*residual==sp.zeros(2,1)
    assert (X.T*X).det()==4*5
    a,b=sp.symbols('a b')
    errors=y-X*sp.Matrix([a,b])
    expected=sp.Rational(7,10)+5*(b-sp.Rational(9,10))**2+4*(sp.Rational(9,4)-a-sp.Rational(3,2)*b)**2
    assert sp.expand((errors.T*errors)[0]-expected)==0


def test_ols_covariance_relaxations_and_gauss_markov():
    X=np.column_stack([np.ones(4),np.arange(4)])
    inverse=np.linalg.inv(X.T@X);L=inverse@X.T
    np.testing.assert_allclose(L@X,np.eye(2),atol=1e-14)
    for omega in [np.diag([1.,2.,3.,4.]),.5**np.abs(np.arange(4)[:,None]-np.arange(4))]:
        assert np.linalg.eigvalsh(omega).min()>0
        covariance=L@omega@L.T
        np.testing.assert_allclose(covariance,inverse@X.T@omega@X@inverse)
        weights=(X[:,1]-1.5)/5
        assert covariance[1,1]==pytest.approx(weights@omega@weights)
    D=np.array([[1.,-2.,1.,0.],[0.,1.,-2.,1.]])
    np.testing.assert_allclose(D@X,0,atol=1e-14)
    np.testing.assert_allclose((L+D)@(L+D).T-L@L.T,D@D.T,atol=1e-14)


def test_omitted_variable_slope_identity():
    # Exact sample counterpart: choose the remaining error orthogonal to x.
    x=np.arange(5,dtype=float);z=x*x
    X=np.column_stack([np.ones(5),x])
    epsilon=np.array([1.,-2.,1.,0.,0.])
    beta,gamma=.7,1.2
    y=2+beta*x+gamma*z+epsilon
    fitted=np.linalg.lstsq(X,y,rcond=None)[0][1]
    xc=x-x.mean();zc=z-z.mean()
    assert fitted==pytest.approx(beta+gamma*(xc@zc)/(xc@xc))


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
