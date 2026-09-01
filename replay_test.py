"""Two quick picks made the panel walk back through the click history: the echo
of the first choice landed after the second and repainted the control.

Sampled step by step and synchronously. A MutationObserver cannot see this —
its callback is batched and runs once the DOM has already settled, so the
intermediate repaint is invisible and the test passes with the fix removed.
"""
from playwright.sync_api import sync_playwright
import os, sys

DISABLE_GUARD = "--no-guard" in sys.argv

with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1500, "height": 1050})
    errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("file://" + os.getcwd() + "/audit.html"); p.wait_for_timeout(1000)
    p.evaluate(open("audit_schema.js").read())
    p.evaluate("""() => {
      schema.push({type:'dropdown', tab:'Movement', section:'MOVEMENT', name:'Strafe Mode',
        flag:'StrafeModeDropdown', segmented:true, options:['Auto','Pure Sideways','Keep Forward']});
      flags['StrafeModeDropdown']='Auto';
      schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags();
      document.querySelector('.loader-card')?.remove();
      window.__seg=[...document.querySelectorAll('.segmented')].find(e=>e.textContent.includes('Strafe Mode'));
    }"""); p.wait_for_timeout(1200)
    if DISABLE_GUARD:
        p.evaluate("() => { window.isStaleEcho = () => false; }")

    cur = lambda: p.evaluate("""() => { const on=[...window.__seg.querySelectorAll('.segmented__opt')]
        .find(e=>e.classList.contains('on')); return on ? on.dataset.value : 'none'; }""")
    pick = lambda v: p.evaluate("""(v) => [...window.__seg.querySelectorAll('.segmented__opt')]
        .find(e=>e.dataset.value===v).click()""", v)
    echo = lambda v: p.evaluate("""(v) => window.__ws_onmessage({data: JSON.stringify(
        {type:'flag', flag:'StrafeModeDropdown', value:[v]})})""", v)

    steps = []
    pick('Pure Sideways'); steps.append(('after click 1', cur()))
    pick('Keep Forward');  steps.append(('after click 2', cur()))
    echo('Pure Sideways'); steps.append(('after stale echo', cur()))
    echo('Keep Forward');  steps.append(('after final echo', cur()))
    for name, v in steps: print(f"    {name:20} {v}")

    stale = dict(steps)['after stale echo']
    ok = stale == 'Keep Forward' and dict(steps)['after final echo'] == 'Keep Forward'
    print(("  ok   " if ok else "  FAIL ") + "stale echo does not repaint the picker")
    print("errors:", errs or "none")
    b.close()
