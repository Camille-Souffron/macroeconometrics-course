"""Eight original teaching scenes; render with render.py, no LaTeX needed."""
import numpy as np
from scipy.stats import norm
from manim import (
    Scene, Text, VGroup, VMobject, Line, DashedLine, Dot, Arrow, Polygon,
    Axes, NumberPlane, Ellipse, ValueTracker, Create, FadeIn, FadeOut,
    Transform, ReplacementTransform, Write, always_redraw, config,
    UP, DOWN, LEFT, RIGHT, ORIGIN, PI, linear,
)
from statanim.distributions.normal3d import NormalCurve3D
from models import nonlinear, JACOBIAN, allocation, sampling_density

PAPER, INK, MUTED = "#f8f6f0", "#203442", "#66767d"
TEAL, GOLD, RED, GRID = "#087f82", "#b57b23", "#bf5b49", "#d9dfdc"
config.background_color = PAPER


def label(text, size=24, color=INK):
    return Text(text, font="DejaVu Sans", font_size=size, color=color)


def path(points, color=TEAL, width=3):
    return VMobject().set_points_as_corners(points).set_stroke(color, width)


class Lesson(Scene):
    def heading(self, number, title, subtitle):
        self.add(label(number, 14, TEAL).to_corner(UP+LEFT, buff=.25))
        heading = label(title, 32)
        if heading.width > 12.6:
            heading.scale_to_fit_width(12.6)
        self.add(heading.move_to([0, 3.12, 0]))
        sub = label(subtitle, 20, MUTED)
        if sub.width > 12.6:
            sub.scale_to_fit_width(12.6)
        self.add(sub.move_to([0, 2.57, 0]))

    def note(self, text):
        note = label(text, 22).move_to([0, -3.3, 0])
        if note.width > 12.8:
            note.scale_to_fit_width(12.8)
        self.add(note)
        return note

    def axes(self, xr, yr, width=10, height=4, center=(0, -.2, 0)):
        ax = Axes(x_range=xr, y_range=yr, x_length=width, y_length=height,
                  tips=False, axis_config={"color": MUTED, "stroke_width": 1.3,
                                           "include_ticks": True})
        ax.move_to(center)
        # Text ticks avoid a LaTeX runtime and stay crisp in the video.
        for val in np.arange(xr[0], xr[1]+xr[2]/2, xr[2]):
            if not np.isclose(val, 0):
                ax.add(label(f"{val:g}", 16, MUTED).next_to(ax.c2p(val, 0), DOWN, buff=.12))
        for val in np.arange(yr[0], yr[1]+yr[2]/2, yr[2]):
            if not np.isclose(val, 0):
                ax.add(label(f"{val:g}", 16, MUTED).next_to(ax.c2p(0, val), LEFT, buff=.1))
        self.add(ax)
        return ax


class LinearMap(Lesson):
    def construct(self):
        self.heading("01 / ALGEBRA", "Following two independent directions",
                     "A = [[1.15, 0.65], [0.25, 0.65]]")
        plane = NumberPlane(x_range=[-3,3,1], y_range=[-2,2,1],
                            x_length=7.5, y_length=4.5,
                            background_line_style={"stroke_color": GRID, "stroke_width": 1},
                            axis_config={"stroke_color": MUTED, "stroke_width": 1.4})
        plane.shift(DOWN*.3)
        # Use equal data units: transform in world coordinates about this origin.
        origin = plane.c2p(0,0)
        matrix = np.array([[1.15,.65],[.25,.65]])
        sx = np.linalg.norm(plane.c2p(1,0)-origin)
        sy = np.linalg.norm(plane.c2p(0,1)-origin)
        def mapped(p):
            q = matrix @ ((p-origin)[:2]/[sx,sy])
            return origin+np.array([q[0]*sx,q[1]*sy,0])
        square = Polygon(*[plane.c2p(*p) for p in [(0,0),(1,0),(1,1),(0,1)]],
                         fill_color=TEAL, fill_opacity=.12, stroke_color=TEAL, stroke_width=1.5)
        arrows = VGroup(Arrow(origin,plane.c2p(1,0),buff=0,color=TEAL),
                        Arrow(origin,plane.c2p(0,1),buff=0,color=GOLD))
        self.play(Create(plane), FadeIn(square), Create(arrows), run_time=2)
        self.note("The columns of A are the images of the two basis vectors.")
        self.wait(2)
        objects = VGroup(plane,square,arrows)
        transformed = objects.copy().apply_function(mapped)
        self.play(Transform(objects,transformed),run_time=4)
        self.wait(4)


class Stability(Lesson):
    def construct(self):
        self.heading("02 / DYNAMICS", "The same rotation, two different futures",
                     "One dot per date · same initial condition")
        axes=[]
        for center,r in [((-3.45,-.1,0),.88),((3.45,-.1,0),1.06)]:
            ax=self.axes([-3,3,1],[-3,3,1],5.1,4.7,center)
            self.add(label(f"Modulus = {r:.2f}",24,TEAL if r<1 else RED).move_to([center[0],2.12,0]))
            axes.append(ax)
        note=self.note("Inside the unit circle: eventual decay. Outside: amplification.")
        angle=.45
        points=[np.array([.75,0.]),np.array([.75,0.])]
        dots=[Dot(ax.c2p(*p),color=c) for ax,p,c in zip(axes,points,[TEAL,RED])]
        self.add(*dots)
        for t in range(1,23):
            animations=[]
            for i,(ax,r,c) in enumerate(zip(axes,[.88,1.06],[TEAL,RED])):
                nxt=r*np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])@points[i]
                self.add(Line(ax.c2p(*points[i]),ax.c2p(*nxt),color=c,stroke_width=2))
                self.add(Dot(ax.c2p(*points[i]),radius=.025,color=c))
                animations.append(dots[i].animate.move_to(ax.c2p(*nxt)))
                points[i]=nxt
            self.play(*animations,run_time=.27,rate_func=linear)
        self.wait(4)


class Taylor(Lesson):
    def construct(self):
        self.heading("03 / ANALYSIS", "From a finite change to a tangent",
                     "Log growth around g = 0")
        ax=self.axes([-.75,1,.25],[-1.5,1,.5],10,4.3)
        f=lambda x:np.log1p(x)
        exact=ax.plot(f,x_range=[-.72,.98],color=TEAL)
        self.play(Create(exact),run_time=2)
        h=ValueTracker(.85)
        sec=always_redraw(lambda:Line(ax.c2p(-.65,-.65*f(h.get_value())/h.get_value()),
                                      ax.c2p(.95,.95*f(h.get_value())/h.get_value()),
                                      color=GOLD,stroke_width=2.5))
        point=always_redraw(lambda:Dot(ax.c2p(h.get_value(),f(h.get_value())),color=GOLD))
        self.add(sec,point,Dot(ax.c2p(0,0),color=INK))
        note=self.note("A secant measures the average slope over a finite change.")
        self.wait(2)
        self.play(h.animate.set_value(.015),run_time=4)
        self.remove(sec,point)
        tangent=ax.plot(lambda x:x,x_range=[-.72,.98],color=GOLD)
        self.add(tangent)
        self.play(Transform(note,label("At zero the limiting slope is one: log(1 + g) ≈ g.",22).move_to(note)),run_time=1)
        self.wait(2)
        quadratic=ax.plot(lambda x:x-x*x/2,x_range=[-.72,.98],color=RED)
        self.play(Create(quadratic),run_time=2)
        self.play(Transform(note,label("The quadratic adds curvature: g − g²/2. Compare the errors away from zero.",22).move_to(note).scale_to_fit_width(12.7)),run_time=1)
        self.add(label("exact",18,TEAL).next_to(ax.c2p(.98,f(.98)),RIGHT,buff=.15),
                 label("tangent",18,GOLD).next_to(ax.c2p(.98,.98),RIGHT,buff=.15),
                 label("quadratic",18,RED).next_to(ax.c2p(.98,.98-.98**2/2),RIGHT,buff=.15))
        self.wait(4)


class Jacobian(Lesson):
    def construct(self):
        self.heading("04 / SEVERAL VARIABLES", "One linear map for every direction",
                     "Nonlinear image / radius   and   Jacobian image / radius")
        ax=self.axes([-1.8,1.8,.6],[-1.4,1.4,.7],8.5,4)
        radius=ValueTracker(1.2)
        def grid(r,exact):
            lines=VGroup()
            for v in np.linspace(-1,1,7):
                for vertical in [False,True]:
                    raw=[np.array([v,t] if vertical else [t,v]) for t in np.linspace(-1,1,41)]
                    vals=[nonlinear(r*p)/r if exact else JACOBIAN@p for p in raw]
                    lines.add(path([ax.c2p(*p) for p in vals],TEAL if exact else GOLD,2 if exact else 1.4))
            return lines
        approx=grid(1,False)
        actual=always_redraw(lambda:grid(radius.get_value(),True))
        self.add(approx,actual)
        counter=always_redraw(lambda:label(f"radius = {radius.get_value():.2f}",23,INK).move_to([4.9,1.9,0]))
        self.add(counter)
        self.note("After dividing by the radius, the remaining discrepancy still tends to zero.")
        self.wait(2)
        self.play(radius.animate.set_value(.05),run_time=7)
        self.wait(4)


class KKT(Lesson):
    def construct(self):
        self.heading("05 / CONSTRAINTS", "A cap changes which choices are possible",
                     "Minimise (x − 1)² + 2(y − 1)²   with   x, y ≥ 0 and x + y ≤ b")
        ax=self.axes([0,3,1],[0,3,1],6,4.3,(-1.4,-.1,0))
        b=ValueTracker(.25)
        triangle=always_redraw(lambda:Polygon(ax.c2p(0,0),ax.c2p(b.get_value(),0),ax.c2p(0,b.get_value()),
                                              fill_color=TEAL,fill_opacity=.14,stroke_color=TEAL,stroke_width=2))
        self.add(triangle)
        # Only draw contour portions in the first quadrant.
        for level in [.08,.3,.7,1.2,2.]:
            theta=np.linspace(0,2*np.pi,401)
            coords=np.column_stack([1+np.sqrt(level)*np.cos(theta),
                                    1+np.sqrt(level/2)*np.sin(theta)])
            segment=[]
            for x,y in coords:
                if 0<=x<=3 and 0<=y<=3:
                    segment.append(ax.c2p(x,y))
                elif segment:
                    if len(segment)>1:self.add(path(segment,GRID,1.5))
                    segment=[]
            if len(segment)>1:self.add(path(segment,GRID,1.5))
        self.add(Dot(ax.c2p(1,1),color=GOLD,radius=.065))
        point=always_redraw(lambda:Dot(ax.c2p(*allocation(b.get_value())[:2]),color=RED,radius=.085))
        info=always_redraw(lambda:VGroup(
            label(f"Resource b = {b.get_value():.2f}",25),
            label(f"x* = {allocation(b.get_value())[0]:.2f}",24,RED),
            label(f"y* = {allocation(b.get_value())[1]:.2f}",24,RED),
            label(f"Multiplier μ = {allocation(b.get_value())[2]:.2f}",24,TEAL),
            label("cap slack" if b.get_value()>2 else ("x = 0 and cap bind" if b.get_value()<.5 else "cap binds"),21,MUTED)
        ).arrange(DOWN,buff=.27).move_to([4.05,-.1,0]))
        self.add(point,info)
        self.note("A binding constraint may have a zero multiplier at a regime transition.")
        self.wait(2)
        for target in [.5,1.,2.,2.8]:
            self.play(b.animate.set_value(target),run_time=2.5,rate_func=linear)
            self.wait(1.3)
        self.wait(2)


def statanim_normal(ax):
    """Keep StatAnim's actual density scale, rather than a fixed peak height.

    Upstream draws in the x-z plane and normalises its sampled peak to z_scale.
    Map that geometry to our x-y axes and set z_scale to the true density peak
    times the vertical data unit. Use its curve layer, with our own axis labels.
    """
    origin=ax.c2p(0,0)
    sx=np.linalg.norm(ax.c2p(1,0)-origin)
    sy=np.linalg.norm(ax.c2p(0,1)-origin)
    bell=NormalCurve3D(mu=0,sigma=1,x_range=(-4,4,.04),
                       z_scale=sy*norm.pdf(0),color=GOLD,
                       glow_opacity=0,fill_opacity=0,smooth_resolution=2)
    return bell.stroke.copy().rotate(-PI/2,axis=RIGHT,about_point=ORIGIN).stretch(sx,0,about_point=ORIGIN).shift(origin)


class Sampling(Lesson):
    def construct(self):
        self.heading("06 / SAMPLING", "The observations are skewed; their mean need not be",
                     "Exact densities of Zₙ = √n (X̄ₙ − 1), with Xᵢ independent Exp(1)")
        ax=self.axes([-4,4,1],[0,.65,.2],10,4.1)
        ref=statanim_normal(ax)
        self.play(Create(ref),run_time=2)
        self.add(label("Normal reference",20,GOLD).move_to([4.65,2.1,0]))
        self.note("The horizontal and vertical scales stay fixed as n increases.")
        curve=None
        nlabel=None
        for n in [2,4,8,16,64]:
            lo=max(-3.98,-np.sqrt(n)+.001)
            new=ax.plot(lambda z:sampling_density(z,n),x_range=[lo,4,.025],color=TEAL)
            newlabel=label(f"n = {n}",28,TEAL).move_to([-4.5,2.1,0])
            if curve is None:
                self.play(Create(new),FadeIn(newlabel),run_time=1.5)
            else:
                # Cross-fade exact distributions: no invented intermediate density.
                self.play(FadeOut(curve),FadeIn(new),ReplacementTransform(nlabel,newlabel),run_time=1)
            curve,nlabel=new,newlabel
            self.wait(2)
        self.wait(2)


class NormalArea(Lesson):
    def construct(self):
        self.heading("07 / INFERENCE", "A five-percent test reserves two tails",
                     "Standard Normal null statistic · two-sided rejection rule")
        ax=self.axes([-4,4,1],[0,.5,.1],10,4.1)
        curve=statanim_normal(ax)
        self.play(Create(curve),run_time=2)
        c=norm.ppf(.975)
        def area(lo,hi,color):
            xs=np.linspace(lo,hi,180)
            return Polygon(ax.c2p(lo,0),*[ax.c2p(x,norm.pdf(x)) for x in xs],ax.c2p(hi,0),
                           fill_color=color,fill_opacity=.25,stroke_width=0)
        center=area(-c,c,TEAL)
        tails=VGroup(area(-4,-c,RED),area(c,4,RED))
        self.play(FadeIn(center),run_time=2)
        self.note("The central region contains 95%; the two rejection tails contain 2.5% each.")
        self.add(label("0.95",25,TEAL).move_to(ax.c2p(0,.16)))
        self.wait(2)
        self.play(FadeIn(tails),run_time=2)
        for x in [-c,c]:
            self.add(DashedLine(ax.c2p(x,0),ax.c2p(x,.28),color=RED,stroke_width=1.5),
                     label(f"{x:.2f}",20,RED).move_to(ax.c2p(x,.32)))
        self.add(label("0.025",22,RED).move_to(ax.c2p(-3,.12)),
                 label("0.025",22,RED).move_to(ax.c2p(3,.12)))
        self.wait(4)


class Fourier(Lesson):
    def construct(self):
        self.heading("08 / FREQUENCY", "Two rhythms inside one observed signal",
                     "48 observations · periods 12 and 4 · no measurement noise")
        top=self.axes([0,48,12],[-2,2,1],7.6,3.9,(-2,-.1,0))
        right=self.axes([0,.5,.125],[0,2,1],3.6,3.9,(4.45,-.1,0))
        t=np.arange(48)
        a=np.cos(2*np.pi*t/12)
        b=.55*np.cos(2*np.pi*t/4)
        pa=path([top.c2p(x,y) for x,y in zip(t,a)],TEAL)
        pb=path([top.c2p(x,y) for x,y in zip(t,b)],GOLD)
        self.play(Create(pa),Create(pb),run_time=2)
        note=self.note("Teal: period 12. Ochre: period 4.")
        self.wait(2)
        total=path([top.c2p(x,y) for x,y in zip(t,a+b)],INK)
        self.play(FadeOut(pa),FadeOut(pb),Create(total),run_time=2)
        self.play(Transform(note,label("Their sum has two Fourier peaks, at 1/12 and 1/4 cycles per observation.",22).move_to(note).scale_to_fit_width(12.8)),run_time=1)
        freq=np.fft.rfftfreq(48)
        power=np.abs(np.fft.rfft(a+b))**2/(2*np.pi*48)
        bars=VGroup(*[Line(right.c2p(f,0),right.c2p(f,p),color=TEAL if f<.2 else GOLD,stroke_width=5)
                      for f,p in zip(freq,power) if p>1e-8])
        self.play(Create(bars),run_time=2)
        self.add(label("cycles / observation",17,MUTED).move_to([4.45,-2.65,0]))
        self.wait(4)
