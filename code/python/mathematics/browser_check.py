"""Check the actual rendered chapter, controls, formula fixtures and video files.

Run with the book served on 127.0.0.1:8765. MATH_BASE_URL can target publication.
"""
import json
import math
import os
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright

BASE=os.environ.get("MATH_BASE_URL","http://127.0.0.1:8765/").rstrip("/")+"/"
PATH="chapters/00-mathematical-foundations.html"


def main():
    with sync_playwright() as p:
        proxy=os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        proxy_config=None
        if proxy:
            u=urlsplit(proxy)
            proxy_config={"server":str(u.scheme)+"://"+str(u.hostname)+":"+str(u.port or 80),
                          "bypass":"127.0.0.1,localhost"}
            if u.username:proxy_config.update(username=unquote(u.username),password=unquote(u.password or ""))
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"],proxy=proxy_config)
        context=browser.new_context(viewport={"width":1440,"height":1000},
                                   ignore_https_errors=bool(os.environ.get("LAB_TEST_INTERCEPTED_TLS")))
        page=context.new_page()
        errors=[];failed=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("response",lambda r:failed.append((r.url,r.status)) if r.status>=400 else None)
        page.goto(BASE+PATH)
        page.wait_for_function("document.querySelectorAll('.math-explorer svg').length === 5")
        page.wait_for_function("typeof MathJax !== 'undefined' && typeof MathJax.whenReady === 'function'")
        page.evaluate("async () => { await MathJax.whenReady(() => {}); await document.fonts.ready; }")
        assert page.locator("mjx-container").count()>350
        assert page.locator("mjx-merror, [data-mjx-error]").count()==0
        assert ":::" not in page.locator("main").inner_text()
        assert page.locator("main video").count()==9
        assert page.locator("main .math-film").count()==9
        assert page.locator("main .math-explorer").count()==5
        assert page.evaluate("MathJax.version.startsWith('4.')")
        for suffix in ["1","2","3","4a","4b","5"]:
            section=page.locator("#sec-ols-assumption-"+suffix)
            assert "If relaxed." in section.inner_text()
        assert page.locator("#sec-ols-scalar").count()==1
        assert page.locator("#sec-vector-spaces").count()==1
        assert page.locator("#sec-vector-families").count()==1
        assert "—" not in page.locator("main").inner_text()
        print('Chapter structure, mathematical rendering and OLS assumptions checked.',flush=True)
        for picture in page.locator("main img:not(.math-print-poster)").all():
            picture.scroll_into_view_if_needed()
            picture.evaluate("async img => { await img.decode(); }")
            assert picture.evaluate("img=>img.naturalWidth>0")
        # All relative chapter links and anchors, including neighbouring chapters.
        invalid=page.evaluate("""async () => {
          const bad=[];
          for(const a of document.querySelectorAll('main a[href]')) {
            const u=new URL(a.href);
            if(u.origin!==location.origin) continue;
            const response=await fetch(u.href);
            if(!response.ok) {bad.push([u.href,response.status]);continue;}
            if(u.hash && u.pathname.endsWith('.html')) {
              const doc=new DOMParser().parseFromString(await response.text(),'text/html');
              if(!doc.getElementById(decodeURIComponent(u.hash.slice(1)))) bad.push([u.href,'anchor']);
            }
          }
          return bad;
        }""")
        assert not invalid,invalid
        print('Images, links and anchors checked.',flush=True)
        # Loading is deliberate, and every video must decode as H.264 in Chromium.
        for video in page.locator("main video").all():
            video.scroll_into_view_if_needed()
            assert video.get_attribute("autoplay") is None
            video.evaluate("async v => { v.preload='metadata'; v.load(); await new Promise((ok,no)=>{v.onloadedmetadata=ok;v.onerror=()=>no(Error('video decode failed'));}); }")
            info=video.evaluate("v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight})")
            assert 8<info["duration"]<35,info
            assert (info["width"],info["height"])==(1280,720)
            video.evaluate("async v=>{v.muted=true;await v.play();}")
            page.wait_for_timeout(150)
            assert video.evaluate("v=>v.currentTime")>0
            video.evaluate("v=>v.pause()")
        print('Nine videos decoded and played.',flush=True)
        # Independent analytic values, evaluated through the shipped JS module.
        results=page.evaluate("""async () => {
          const m=await import('../interactive/math/formulas.js');
          return {t:m.taylor(-.1),cap:m.cap(.25),edge:m.cap(1),bayes:m.posterior(4),
                  stable:m.descent(.2).at(-1),boundary:m.descent(.5).at(-1),
                  unstable:m.descent(.65).at(-1)};
        }""")
        assert math.isclose(results["t"]["exact"],math.log(.9),abs_tol=1e-14)
        assert abs(results["t"]["exact"]-results["t"]["quadratic"])<results["t"]["bound"]
        assert results["cap"]=={"x":.25,"mu":.75,"value":.28125}
        assert results["edge"]=={"x":1,"mu":0,"value":0}
        assert results["bayes"]["mean"]==.5 and results["bayes"]["variance"]==.5
        assert math.isclose(results["stable"][0],1.5*.8**12)
        assert math.isclose(results["stable"][1],.2**12)
        assert results["boundary"][1]==1 and abs(results["unstable"][1])>100
        # Matrix explorer: endpoints, column images, singular maps and progression.
        matrix=page.locator('[data-math="matrix"]')
        preset=matrix.locator('select');progress=matrix.locator('input[type="range"]')
        for name,det in [("identity",1),("shear",1),("stretch",2),("rotation",1),
                         ("reflection",-1),("singular",0),("zero",0)]:
            preset.select_option(name)
            assert float(matrix.locator('svg').get_attribute('data-determinant'))==det
            progress.fill('0');progress.dispatch_event('input')
            assert float(matrix.locator('svg').get_attribute('data-determinant'))==1
        preset.select_option('reflection');progress.fill('0.5');progress.dispatch_event('input')
        assert float(matrix.locator('svg').get_attribute('data-determinant'))==0
        for input,value in zip(matrix.locator('input[type="number"]').all(),['1','2','-1','1']):
            input.fill(value);input.dispatch_event('input')
        progress.fill('1');progress.dispatch_event('input')
        assert float(matrix.locator('svg').get_attribute('data-determinant'))==3
        assert '(3.00, 0.00)' in matrix.locator('.math-explanation').inner_text()
        prior_svg=matrix.locator('svg').inner_html()
        matrix.locator('input[type="number"]').first.fill('')
        assert 'last valid figure' in matrix.locator('.math-explanation').inner_text()
        assert matrix.locator('svg').inner_html()==prior_svg
        matrix.get_by_role('button',name='Reset',exact=True).click()
        progress.focus();progress.press('ArrowLeft');assert progress.input_value()=='0.99'
        with page.expect_download() as download:
            matrix.get_by_role('button',name='Download figure (SVG)').click()
        assert download.value.suggested_filename=='mathematics-matrix.svg'
        download.value.save_as('/tmp/mathematics-matrix.svg')
        fixtures=page.evaluate("""async()=>{
          const {matrixState}=await import('../interactive/math/formulas.js');
          return [matrixState([1,1,0,1]),matrixState([2,1,0,1]),
                  matrixState([1,0,0,0]),matrixState([0,-1,1,0],.5)];
        }""")
        assert fixtures[0]['firstColumn']==[1,0] and fixtures[0]['secondColumn']==[1,1]
        assert fixtures[1]['vector']==[3,1]
        assert fixtures[2]['determinant']==0
        assert fixtures[3]['determinant']==.5  # Interpolation is not a pure rotation.
        matrix.get_by_role('button',name='Reset',exact=True).click()
        for kind in ["taylor","kkt","descent","bayes"]:
            box=page.locator('[data-math="'+kind+'"]')
            slider=box.locator('input[type="range"]')
            for attr in ["min","max"]:
                slider.fill(slider.get_attribute(attr))
                slider.dispatch_event("input")
                assert "NaN" not in box.inner_text() and "Infinity" not in box.inner_text()
                assert "NaN" not in box.locator("svg").inner_html()
            box.get_by_role("button",name="Reset",exact=True).click()
            before=slider.input_value();slider.focus();slider.press("ArrowRight")
            assert slider.input_value()!=before
            with page.expect_download() as download:
                box.get_by_role("button",name="Download figure (SVG)").click()
            assert download.value.suggested_filename=="mathematics-"+kind+".svg"
            download.value.save_as("/tmp/mathematics-"+kind+".svg")
            box.get_by_role("button",name="Reset",exact=True).click()
        print('All five explorers, numerical fixtures and keyboard controls checked.',flush=True)
        # Prevent smooth anchor scrolling from moving a very tall capture target.
        page.add_style_tag(content='html { scroll-behavior: auto !important; }')
        page.evaluate("window.scrollTo(0,0)")
        page.screenshot(path="/tmp/mathematics-desktop.png")
        page.locator('[data-math="taylor"]').screenshot(path="/tmp/mathematics-taylor.png")
        page.locator("#fig-kkt-film").screenshot(path="/tmp/mathematics-kkt.png")
        matrix.evaluate("e=>e.scrollIntoView({behavior:'instant',block:'start'})")
        # Capture this taller-than-viewport panel in reading-sized portions.
        page.screenshot(path="/tmp/mathematics-matrix-desktop.png")
        matrix.locator('svg').evaluate("e=>e.scrollIntoView({behavior:'instant',block:'center'})")
        page.screenshot(path="/tmp/mathematics-matrix-desktop-geometry.png")
        for width in [390,768]:
            page.set_viewport_size({"width":width,"height":844})
            page.wait_for_timeout(500)
            page.evaluate("async()=>{await MathJax.whenReady(()=>{}); await document.fonts.ready;}")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),("overflow",width)
            for box in page.locator(".math-explorer").all():
                box.evaluate("e=>e.scrollIntoView({behavior:'instant',block:'start'})")
                assert box.evaluate("e=>e.scrollWidth<=e.clientWidth+1")
            page.locator('[data-math="kkt"]').screenshot(path="/tmp/mathematics-mobile-"+str(width)+".png")
            matrix.evaluate("e=>e.scrollIntoView({behavior:'instant',block:'start'})")
            page.screenshot(path="/tmp/mathematics-matrix-"+str(width)+".png")
            matrix.locator('svg').evaluate("e=>e.scrollIntoView({behavior:'instant',block:'center'})")
            page.screenshot(path="/tmp/mathematics-matrix-"+str(width)+"-geometry.png")
            # Equations are readable, not horizontal scrolling widgets.
            scrollers=page.evaluate("""()=>[...document.querySelectorAll('main .math, main mjx-container')]
              .filter(e=>['auto','scroll'].includes(getComputedStyle(e).overflowX))
              .map(e=>e.tagName+': '+e.textContent.slice(0,60))""")
            assert not scrollers,scrollers
            wide=page.evaluate("""()=>[...document.querySelectorAll('main .math.display')]
              .filter(e=>e.scrollWidth>e.clientWidth+2)
              .map(e=>({width:e.clientWidth,content:e.scrollWidth,
                formula:MathJax.startup.document.getMathItemsWithin([e])[0]?.math}))""")
            assert not wide,(width,wide)
        page.emulate_media(reduced_motion="reduce")
        page.reload();page.wait_for_selector(".math-explorer svg")
        assert page.evaluate("[...document.querySelectorAll('video')].every(v=>v.paused)")
        page.emulate_media(media="print")
        assert page.locator(".math-print-poster:visible").count()==9
        assert page.locator(".math-film video:visible").count()==0
        # No-script reading retains figures, formulas as source, prose and posters.
        nojs=browser.new_context(java_script_enabled=False,
                                 ignore_https_errors=bool(os.environ.get("LAB_TEST_INTERCEPTED_TLS")))
        fallback=nojs.new_page();fallback.goto(BASE+PATH)
        fallback_text=fallback.locator("main").inner_text()
        assert "Karush" in fallback_text, (len(fallback_text), fallback_text[:200], fallback_text[-200:])
        assert fallback.locator("video[poster]").count()==9
        assert fallback.locator("main img").count()>=15
        assert not errors,errors
        assert not failed,failed
        browser.close()
    print("Math chapter verified: fixed/reflowing formulas, OLS assumptions, 9 videos, 5 explorers, matrix presets, keyboard controls, downloads, desktop/mobile and print.")


if __name__=="__main__":
    main()
