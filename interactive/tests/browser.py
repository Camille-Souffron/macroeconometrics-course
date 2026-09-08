"""Real Chromium + actual WebAssembly runtime. Serve _book on port 8765 first."""
import json
import os
import hashlib
import subprocess
import sys
from urllib.parse import urlsplit,unquote
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
BASE='http://127.0.0.1:8765/'
with sync_playwright() as playwright:
    proxy=os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    proxy_config=None
    if proxy:
        parsed=urlsplit(proxy if '://' in proxy else 'http://'+proxy)
        proxy_config={'server':f'{parsed.scheme}://{parsed.hostname}:{parsed.port or 80}','bypass':'127.0.0.1,localhost'}
        if parsed.username:proxy_config.update(username=unquote(parsed.username),password=unquote(parsed.password or ''))
    browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'],proxy=proxy_config)
    page=browser.new_page(viewport={'width':1440,'height':1000},ignore_https_errors=bool(os.environ.get('LAB_TEST_INTERCEPTED_TLS')))
    # Optional transport workaround for TLS-inspecting proxies that corrupt a
    # Brotli-encoded wheel. This serves the original hash-verified package bytes;
    # it does not mock Python or any numerical result. CI uses the CDN directly.
    mirror=os.environ.get('LAB_TEST_STATSMODELS_WHEEL')
    if mirror:
        wheel=Path(mirror).read_bytes()
        assert hashlib.sha256(wheel).hexdigest()=='4c89f4c9146b142216126042af0eb3927d5912485a50bfd333def06c5ad5fd8d'
        page.context.route('**/statsmodels-0.14.4-cp312-cp312-pyodide_2024_0_wasm32.whl',lambda route:route.fulfill(status=200,body=wheel,headers={'Content-Type':'application/octet-stream','Access-Control-Allow-Origin':'*'}))
    errors=[];console_errors=[];requests=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('requestfailed',lambda request:print('Failed request:',request.url,request.failure,flush=True))
    page.on('console',lambda message:console_errors.append(message.text) if message.type=='error' else None)
    page.on('request',lambda request:requests.append(request.url))
    page.goto(BASE+'chapters/03-var.html');page.wait_for_timeout(800)
    assert not any('pyodide' in url or '/interactive/js/' in url for url in requests)
    page.goto(BASE+'interactive-lab.html?method=var&spec=%7B%22lags%22%3A1%7D')
    page.wait_for_function("document.querySelector('#lab-status').textContent.startsWith('Ready')")
    assert page.locator('#spec-lags').input_value()=='1'
    assert not any('pyodide' in url for url in requests)
    page.screenshot(path='/tmp/macro-lab-desktop.png',full_page=True)
    page.locator('#lab-run').click()
    page.wait_for_function("/complete|could not|stopped/.test(document.querySelector('#lab-status').textContent)",timeout=240000)
    print('First browser estimation:',page.locator('#lab-status').inner_text(),page.locator('#lab-error').inner_text(),flush=True)
    assert page.locator('#lab-error').is_hidden()
    assert page.locator('#lab-plot svg').count()==1
    with page.expect_download() as download:
        page.locator('#lab-download-code').click()
    download.value.save_as('/tmp/macro-lab-reproduce.py')
    subprocess.run([sys.executable,'/tmp/macro-lab-reproduce.py'],check=True,stdout=subprocess.DEVNULL)
    page.locator('#lab-pin').click()
    page.locator('#spec-lags').fill('2');page.locator('#spec-lags').dispatch_event('change');page.locator('#lab-run').click()
    page.wait_for_function("document.querySelector('#lab-status').textContent.startsWith('Estimation complete')",timeout=120000)
    assert 'Specification comparison' in page.locator('#lab-comparison').inner_text()
    page.evaluate('window.scrollTo(0,0)');page.screenshot(path='/tmp/macro-lab-result.png',full_page=True)
    catalog=json.loads((ROOT/'interactive/catalog.json').read_text())
    for experiment in catalog['experiments']:
        page.select_option('#lab-chapter',experiment['chapter']);page.select_option('#lab-method',experiment['id'])
        assert page.locator('#lab-controls').evaluate('(form) => form.checkValidity()'),experiment['id']
    for identifier in ['stationarity','filters','svar','vecm','dfm','panel','markov','lp','gar','dvar','distribution-regression','bvar','tvp-sv','samplers','sequence','ml','proxy']:
        experiment=next(e for e in catalog['experiments'] if e['id']==identifier)
        page.select_option('#lab-chapter',experiment['chapter']);page.select_option('#lab-method',identifier)
        if identifier=='distribution-regression':
            page.locator('#lab-spec-controls > details').evaluate('(element) => element.open = true')
            page.locator('#spec-evaluate').check()
        print('Browser model running:',identifier,flush=True)
        page.locator('#lab-run').click()
        page.wait_for_function("/complete|could not|stopped/.test(document.querySelector('#lab-status').textContent)",timeout=180000)
        assert page.locator('#lab-error').is_hidden(),(identifier,page.locator('#lab-error').inner_text())
        print('Browser model passed:',identifier,flush=True)
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path='/tmp/macro-lab-mobile.png',full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
    # Error handling must return an econometric explanation, not a raw traceback.
    page.select_option('#lab-chapter','06-nonlinear.qmd');page.select_option('#lab-method','tar')
    page.locator('#spec-threshold').fill('-5');page.locator('#lab-run').click()
    page.wait_for_function("/complete|could not/.test(document.querySelector('#lab-status').textContent)",timeout=120000)
    assert page.locator('#lab-error').is_visible()
    assert 'regime' in page.locator('#lab-error').inner_text()
    # Cancellation is a real worker termination, not just a hidden result.
    page.locator('#lab-reset').click()
    page.evaluate("() => { document.querySelector('#lab-run').click(); document.querySelector('#lab-cancel').click(); }")
    assert 'cancelled' in page.locator('#lab-status').inner_text()
    print('Browser page errors:',errors,flush=True)
    print('Browser console errors:',console_errors,flush=True)
    assert not errors and not console_errors
    browser.close()
