from playwright.sync_api import sync_playwright
import os
with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1500, "height": 1050})
    errs=[]; p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("file://" + os.getcwd() + "/audit.html"); p.wait_for_timeout(1000)
    p.evaluate(open("audit_schema.js").read())
    p.evaluate("""() => {
      schema.push({type:'dropdown', tab:'Movement', section:'MOVEMENT', name:'Strafe Mode',
        flag:'StrafeModeDropdown', segmented:true, options:['Auto','Pure Sideways','Keep Forward'],
        desc:'Auto=按A/D时才松W(推荐)；纯横向=一律松W最快但会侧飘；保留前进=永不松W最慢'});
      flags['StrafeModeDropdown']='Auto';
      schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags();
      document.querySelector('.loader-card')?.remove(); packPanels();
    }"""); p.wait_for_timeout(1600)
    seg = p.evaluate("() => !!document.querySelector('.segmented')")
    print(("  ok   " if seg else "  FAIL ") + "3 short options render inline, no popup")
    h0 = p.evaluate("""() => [...document.querySelectorAll('.panel')]
        .find(e=>e.querySelector('.panel-title__name').textContent.trim()==='Movement').offsetHeight""")
    p.evaluate("""() => [...document.querySelectorAll('.segmented__opt')]
        .find(e=>e.dataset.value==='Keep Forward').click()"""); p.wait_for_timeout(400)
    h1 = p.evaluate("""() => [...document.querySelectorAll('.panel')]
        .find(e=>e.querySelector('.panel-title__name').textContent.trim()==='Movement').offsetHeight""")
    print(("  ok   " if h0 == h1 else "  FAIL ") + f"choosing does not resize the panel ({h0} -> {h1})")
    v = p.evaluate("() => flags['StrafeModeDropdown']")
    print(("  ok   " if v == 'Keep Forward' else "  FAIL ") + f"selection updates the flag ({v})")
    on = p.evaluate("""() => { const r=[...document.querySelectorAll('.segmented')]
        .find(e=>e.textContent.includes('Strafe Mode'));
        return [...r.querySelectorAll('.segmented__opt')].filter(e=>e.classList.contains('on'))
          .map(e=>e.dataset.value); }""")
    print(("  ok   " if on == ['Keep Forward'] else "  FAIL ") + f"exactly one segment highlighted {on}")
    # long lists must still use the popup
    dd = p.evaluate("""() => { const r=[...document.querySelectorAll('.dropdown')]
        .find(e=>e.textContent.includes('Aim Mode')); return !!r; }""")
    print(("  ok   " if not dd else "  note ") + "Aim Mode (2 short options) also inline")
    skins = p.evaluate("() => document.querySelectorAll('#panels-root .dropdown').length")
    print(f"  info  popup dropdowns remaining: {skins} (the 20 skins, 3 options each are short → check)")
    print("errors:", errs or "none")
    p.screenshot(path="seg.png")
    b.close()
