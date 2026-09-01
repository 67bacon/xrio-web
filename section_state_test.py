"""A section closed to get it out of the way came back open on every
re-injection, because the panel always reset to "first section expanded"."""
from playwright.sync_api import sync_playwright
import os, sys
OLD = "--old" in sys.argv
with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1500, "height": 1050})
    errs=[]; p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("file://" + os.getcwd() + "/audit.html"); p.wait_for_timeout(900)
    p.evaluate(open("audit_schema.js").read()); p.wait_for_timeout(1400)
    if OLD:
        p.evaluate("() => { window.rememberSection = () => {}; window.recallSection = () => null; }")

    state = lambda: p.evaluate("""() => Object.fromEntries(
        [...document.querySelectorAll('.section-divider')]
          .map(d => [d.textContent.replace(/[0-9\\s]+$/,'').trim(), d.classList.contains('open')]))""")
    print("    initial:", state())

    # close AIMBOT, open ANTI-AIM — a layout the user chose
    p.evaluate("""() => {
      const ds=[...document.querySelectorAll('.section-divider')];
      const aim=ds.find(d=>d.textContent.includes('AIMBOT'));
      if (aim.classList.contains('open')) aim.click();
      const mv=ds.find(d=>d.textContent.includes('MOVEMENT'));
      if (mv && mv.classList.contains('open')) mv.click();
    }"""); p.wait_for_timeout(900)
    chosen = state()
    print("    chosen: ", chosen)

    # a re-injection: same schema, full rebuild
    p.evaluate("() => { schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags(); }")
    p.wait_for_timeout(1200)
    after = state()
    print("    after re-inject:", after)

    ok = (after.get('AIMBOT') is False and after.get('MOVEMENT') is False
          and after.get('UI CONTROL') is True)
    print(("  ok   " if ok else "  FAIL ") + "section open/closed state survives a re-inject")
    print("errors:", errs or "none")
    b.close()
