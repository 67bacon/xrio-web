"""Opening a section clipped its last row until the animation finished: the
target max-height was measured before the padding that .open adds had been
applied, so it was short by the padding and the content sat cut off."""
from playwright.sync_api import sync_playwright
import os, sys
OLD = "--old" in sys.argv
with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1500, "height": 1050})
    errs=[]; p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("file://" + os.getcwd() + "/audit.html"); p.wait_for_timeout(1000)
    p.evaluate(open("audit_schema.js").read()); p.wait_for_timeout(1500)
    p.evaluate("() => document.querySelector('.loader-card')?.remove()")

    # close UI CONTROL, then reopen it and inspect the animation target
    p.evaluate("""() => {
      const panel=[...document.querySelectorAll('.panel')]
        .find(e=>e.querySelector('.panel-title__name').textContent.trim()==='Settings');
      window.__d=[...panel.querySelectorAll('.section-divider')].find(e=>e.textContent.includes('UI CONTROL'));
      window.__b=window.__d.nextElementSibling;
      if (window.__d.classList.contains('open')) window.__d.click();
    }"""); p.wait_for_timeout(600)
    if OLD:
        p.evaluate("""() => { window.__patch = true; }""")
    p.evaluate("() => window.__d.click()")
    p.wait_for_timeout(60)
    target = p.evaluate("() => parseFloat(window.__b.style.maxHeight) || 0")
    p.wait_for_timeout(700)
    natural = p.evaluate("() => window.__b.scrollHeight")
    clipped = p.evaluate("() => window.__b.scrollHeight > window.__b.clientHeight + 1")
    print(f"    animation target {target:.0f}px   natural height {natural}px")
    ok = abs(target - natural) <= 2 and not clipped
    print(("  ok   " if ok else "  FAIL ") + "opening animates to the full height (clipped=%s)" % clipped)
    print("errors:", errs or "none")
    b.close()
