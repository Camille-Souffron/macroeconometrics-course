"""Publication-quality SVG stills for the chapter; all data are illustrative."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch
import numpy as np
from scipy import stats

DEST = Path(__file__).resolve().parents[3] / "figures/mathematics/analysis"
PAPER, INK, TEAL, GOLD, RED, GREY = "#f8f6f0", "#203442", "#087f82", "#a66d16", "#b35040", "#dce2dc"
plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": GREY,
    "xtick.color": INK, "ytick.color": INK, "font.family": "DejaVu Sans",
    "font.size": 12, "axes.titlesize": 14, "axes.titleweight": "medium",
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": GREY, "grid.alpha": .65, "axes.grid": True,
    "legend.frameon": False, "svg.fonttype": "none", "svg.hashsalt": "math-foundations",
    "lines.linewidth": 2.4,
})


def save(fig, name):
    DEST.mkdir(parents=True, exist_ok=True)
    import io
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight", metadata={"Date": None})
    (DEST/f"{name}.svg").write_text("\n".join(line.rstrip() for line in buffer.getvalue().splitlines())+"\n")
    plt.close(fig)


def arrow(ax, point, color, text):
    ax.annotate("", xy=point, xytext=(0,0), arrowprops={"arrowstyle":"->","color":color,"lw":2.7})
    ax.annotate(text, xy=point, xytext=(5,8), textcoords="offset points",color=color)


def paths():
    fig, axes=plt.subplots(1,2,figsize=(10.5,4),layout="constrained")
    ax=axes[0]
    for p,c in [((.9,0),TEAL),((0,.9),TEAL),((.75,.75),RED)]:
        ax.annotate("",xy=(.03,.03) if p[0]*p[1] else (0,0),xytext=p,arrowprops={"arrowstyle":"->","color":c,"lw":2.5})
    ax.text(.44,.07,"axes",color=TEAL);ax.text(.43,.55,"y = x",color=RED)
    ax.scatter(0,0,color=INK,s=30);ax.set(xlim=(-.1,1),ylim=(-.1,1),xlabel="x",ylabel="y",title="Approach the same origin",aspect="equal")
    t=np.geomspace(.001,1,200)
    axes[1].semilogx(t,np.zeros_like(t),color=TEAL,label="Along either axis")
    axes[1].semilogx(t,np.full_like(t,.5),color=RED,label="Along y = x")
    axes[1].set(xlabel="distance parameter t → 0 (to the left)",ylabel="xy / (x² + y²)",ylim=(-.1,.7),title="The values do not approach one limit")
    axes[1].legend(loc="center",fontsize=11)
    save(fig,"paths")


def curvature():
    fig,axes=plt.subplots(1,3,figsize=(12,3.6),layout="constrained")
    x=np.linspace(-1.4,1.4,200)
    for ax,sgn,title in [(axes[0],1,"A minimum: x² + y²"),(axes[1],-1,"A saddle: x² − y²")]:
        ax.plot(x,x*x,color=TEAL,label="Along the x axis")
        ax.plot(x,sgn*x*x,color=GOLD,ls="--",label="Along the y axis")
        ax.set(title=title,xlabel="displacement",ylabel="objective change",ylim=(-2,2))
    axes[0].legend(fontsize=10)
    axes[2].plot(x,x**4,color=TEAL,label="x⁴: minimum")
    axes[2].plot(x,-x**4,color=RED,ls="--",label="−x⁴: maximum")
    axes[2].set(title="Zero curvature is inconclusive",xlabel="x",ylim=(-2,2));axes[2].legend(fontsize=10)
    save(fig,"curvature")


def bases():
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),layout="constrained")
    for ax in axes:
        ax.set(xlim=(-.6,2.8),ylim=(-.6,2.5),aspect="equal",xlabel="first coordinate")
        ax.axhline(0,color=GREY);ax.axvline(0,color=GREY)
    arrow(axes[0],(1.6,.2),TEAL,"u");arrow(axes[0],(.4,1.6),GOLD,"v")
    arrow(axes[0],(2,1.8),RED,"u + v")
    axes[0].set_title("Two independent directions")
    axes[1].plot([-.6,2.8],[-.3,1.4],color=GREY)
    arrow(axes[1],(2.4,1.2),GOLD,"2u");arrow(axes[1],(1.2,.6),TEAL,"u")
    axes[1].set_title("Only one independent direction")
    x=np.linspace(-.6,2.8,100)
    axes[2].plot(x,.5*x,color=TEAL,label="subspace")
    axes[2].plot(x,.5*x+1,color=GOLD,ls="--",label="affine translation")
    axes[2].scatter(0,0,color=INK);axes[2].set_title("Passing through zero matters");axes[2].legend(fontsize=10)
    save(fig,"bases")


def determinant():
    fig,axes=plt.subplots(1,2,figsize=(10,4.3),layout="constrained")
    square=np.array([[0,0],[1,0],[1,1],[0,1]])
    for ax,A,title in zip(axes,[np.array([[1.2,.5],[.2,1]]),np.array([[1,.8],[.5,.4]])],
                          ["Nonzero area: invertible","Zero area: one direction is lost"]):
        shape=square@A.T
        ax.add_patch(Polygon(square,fill=False,edgecolor=GREY,linestyle="--"))
        ax.add_patch(Polygon(shape,facecolor=TEAL,alpha=.18,edgecolor=TEAL))
        arrow(ax,A[:,0],TEAL,"Ae₁");arrow(ax,A[:,1],GOLD,"Ae₂")
        ax.set(title=title,xlim=(-.3,2.2),ylim=(-.3,1.6),aspect="equal",xlabel="first output",ylabel="second output")
        ax.text(.03,.93,"det A = "+f"{np.linalg.det(A):.1f}",transform=ax.transAxes)
    save(fig,"determinant")


def projection():
    fig,axes=plt.subplots(1,2,figsize=(10.5,4.2),layout="constrained")
    x=np.array([0,1,2,3,4.]);y=np.array([.5,1.9,1.6,3.3,3.1])
    X=np.column_stack([np.ones(5),x]);beta=np.linalg.lstsq(X,y,rcond=None)[0];yh=X@beta
    axes[0].scatter(x,y,color=INK,zorder=3)
    axes[0].plot(x,yh,color=TEAL)
    axes[0].vlines(x,np.minimum(y,yh),np.maximum(y,yh),color=RED,lw=2)
    axes[0].set(title="Vertical errors in the data plot",xlabel="regressor",ylabel="response")
    ax=axes[1]
    ax.plot([-1,3],[0,0],color=TEAL)
    arrow(ax,(1.7,1.5),INK,"y");arrow(ax,(1.7,0),TEAL,"fitted vector")
    ax.annotate("",xy=(1.7,1.5),xytext=(1.7,0),arrowprops={"arrowstyle":"->","color":RED,"lw":2.5})
    ax.text(1.84,.6,"residual",color=RED)
    ax.plot([1.5,1.5,1.7],[0,.2,.2],color=GREY)
    ax.set(title="Orthogonality in data space",xlim=(-.3,3.3),ylim=(-.5,2),aspect="equal")
    ax.set_xticks([]);ax.set_yticks([]);ax.text(.2,-.35,"regressor subspace",color=TEAL)
    save(fig,"projection")


def moments():
    fig,axes=plt.subplots(2,2,figsize=(10.5,6.5),layout="constrained")
    x=np.linspace(-4,5,500)
    pairs=[(stats.norm.pdf(x),stats.norm.pdf(x,1,1),"Location","same spread, shifted mean"),
           (stats.norm.pdf(x),stats.norm.pdf(x,0,1.7),"Dispersion","same mean, larger variance"),
           (stats.norm.pdf(x),stats.skewnorm.pdf(x,5),"Asymmetry","a skewed distribution"),
           (stats.norm.pdf(x),stats.t.pdf(x/np.sqrt(3/5),5)/np.sqrt(3/5),"Fourth moment","Normal and t₅, both variance one")]
    for ax,(a,b,title,sub) in zip(axes.flat,pairs):
        ax.plot(x,a,color=TEAL,label="Normal reference")
        ax.plot(x,b,color=GOLD,ls="--",label=sub)
        ax.set(title=title,xlabel="value",ylabel="density",ylim=(0,.85));ax.legend(fontsize=9,loc="upper right")
    save(fig,"moments")


def laws():
    fig,axes=plt.subplots(2,2,figsize=(10.5,6.3),layout="constrained")
    for ax,law,x,title in [
        (axes[0,0],stats.bernoulli(.3),np.arange(2),"Default indicator: Bernoulli(0.3)"),
        (axes[0,1],stats.binom(10,.3),np.arange(11),"Ten independent firms: Binomial"),
        (axes[1,0],stats.poisson(3),np.arange(11),"Arrivals: Poisson(3)")]:
        ax.bar(x,law.pmf(x),color=TEAL,width=.5);ax.set(title=title,xlabel="count / outcome",ylabel="probability mass")
        ax.set_xticks(x[::max(1,len(x)//6)])
    ax=axes[1,1];x=np.linspace(0,5,300);density=stats.expon.pdf(x)
    ax.plot(x,density,color=TEAL);ax.fill_between(x,0,density,where=x<=1,color=GOLD,alpha=.3)
    ax.set(title="Waiting time: Exponential(1)",xlabel="duration",ylabel="density")
    ax.text(.44,.76,"P(X ≤ 1) ≈ 0.632",transform=ax.transAxes,color=GOLD)
    save(fig,"laws")


def intervals():
    rng=np.random.default_rng(47)
    means=rng.normal(0,1,size=(40,25)).mean(axis=1)
    half=stats.norm.ppf(.975)/5
    fig,ax=plt.subplots(figsize=(9,5),layout="constrained")
    for i,m in enumerate(means):
        color=TEAL if abs(m)<=half else RED
        ax.plot([m-half,m+half],[i,i],color=color,lw=1.5)
        ax.scatter(m,i,color=color,s=12)
    ax.axvline(0,color=INK,lw=1.4,ls="--")
    ax.set(xlabel="mean estimate and 95% interval (known variance)",ylabel="independent repetition",title="One fixed parameter, forty random intervals")
    save(fig,"intervals")


def timepaths():
    rng=np.random.default_rng(31);e=rng.normal(size=120)
    stable=np.zeros(120);walk=np.cumsum(e)
    # Stationary marginal initial value, independent of future innovations.
    stable[0]=rng.normal(scale=1/np.sqrt(1-.8**2))
    for t in range(1,120):stable[t]=.8*stable[t-1]+e[t]
    fig,ax=plt.subplots(figsize=(10,4.2),layout="constrained")
    ax.plot(stable,color=TEAL,label="AR(1), φ = 0.8")
    ax.plot(walk,color=GOLD,label="Random walk, φ = 1")
    ax.set(xlabel="date",ylabel="level",title="The same subsequent innovations, different persistence")
    ax.legend(ncol=2)
    save(fig,"timepaths")


def filtering():
    fig,ax=plt.subplots(figsize=(10.5,3.6),layout="constrained");ax.axis("off")
    for i in range(4):
        x=.12+i*.25
        for y,text,color in [(.73,"hidden state s"+str(i),TEAL),(.23,"observation y"+str(i),GOLD)]:
            ax.add_patch(FancyBboxPatch((x-.10,y-.09),.2,.18,boxstyle="round,pad=0.015",
                                       facecolor=PAPER,edgecolor=color,lw=1.6))
            ax.text(x,y,text,ha="center",va="center",fontsize=12,color=color)
        ax.annotate("",xy=(x,.34),xytext=(x,.62),arrowprops={"arrowstyle":"->","color":GREY,"lw":2})
        if i<3:ax.annotate("",xy=(x+.13,.73),xytext=(x+.11,.73),arrowprops={"arrowstyle":"->","color":TEAL,"lw":2})
    ax.text(.5,.99,"States propagate through time; observations measure states",ha="center",fontsize=15)
    ax.text(.5,-.08,"At date 2: filtering uses y₀, y₁, y₂. Smoothing may also use y₃.",ha="center",fontsize=12)
    ax.set(xlim=(-.01,1.01),ylim=(-.15,1.08))
    save(fig,"filtering")


def compactness():
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout="constrained")
    x=np.linspace(0,1,201)
    for ax,closed in zip(axes,[False,True]):
        ax.plot(x,(x-2)**2,color=TEAL)
        ax.scatter([0,1],[4,1],s=65,facecolors=TEAL if closed else PAPER,edgecolors=TEAL,lw=2,zorder=4)
        ax.set(xlim=(-.1,1.1),ylim=(.5,4.4),xlabel="x",ylabel="(x − 2)²",
               title="Closed interval [0, 1]" if closed else "Open interval (0, 1)")
        ax.text(.35,3.6,"Minimum = 1\nattained at x = 1" if closed else "Infimum = 1\nnever attained",fontsize=12)
    save(fig,"compactness")


def convexity():
    fig,ax=plt.subplots(figsize=(9,4),layout="constrained")
    x=np.linspace(-1.5,2.3,201);a=.4
    ax.plot(x,.5*x*x,color=TEAL,label="Convex function: x²/2")
    ax.plot(x,a*x-a*a/2,color=GOLD,ls="--",label="Supporting tangent at x = 0.4")
    ax.plot([-1,2],[.5,2],color=RED,ls=":",label="Chord between two points")
    ax.scatter([-1,a,2],[.5,a*a/2,2],color=INK,zorder=4)
    ax.set(xlabel="x",ylabel="function value",ylim=(-.8,3.6),
           title="A convex curve lies above its tangents and below its chords")
    ax.legend(fontsize=11,loc="upper center")
    save(fig,"convexity")


def integration():
    fig,axes=plt.subplots(1,2,figsize=(10.5,3.9),layout="constrained")
    x=np.linspace(0,1,250)
    for ax,n in zip(axes,[4,16]):
        mid=(np.arange(n)+.5)/n
        ax.bar(mid,mid**2,width=1/n,color=TEAL,alpha=.25,edgecolor=TEAL,linewidth=1)
        ax.plot(x,x*x,color=TEAL)
        ax.set(title=str(n)+" midpoint rectangles",xlabel="quantity q",ylabel="marginal cost q²",ylim=(0,1.2))
        ax.text(.05,.94,f"sum = {np.mean(mid**2):.5f}\nintegral = 1/3",transform=ax.transAxes,va="top")
    save(fig,"integration")


if __name__=="__main__":
    for make in [paths,curvature,bases,determinant,projection,moments,laws,intervals,timepaths,filtering,compactness,convexity,integration]:
        make()
    print("Thirteen SVG figures generated.")
