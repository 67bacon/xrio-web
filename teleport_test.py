"""Two regressions the user hit: panels relocating when a section is toggled,
and a scrollbar inside a colour list that did not need to scroll."""
from playwright.sync_api import sync_playwright
import os
with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1500, "height": 1050})
    p.goto("file://" + os.getcwd() + "/audit.html"); p.wait_for_timeout(1000)
    p.evaluate(open("audit_schema.js").read()); p.wait_for_timeout(900)
    p.evaluate("""() => {
      schema.push({type:'dropdown', tab:'Visuals', section:'ESP', name:'Chams Color',
        flag:'ChamsColor', options:['Red','Green','Blue','Yellow','Pink','Cyan','White']});
      flags['ChamsColor']='Red'; schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags();
      document.querySelector('.loader-card')?.remove(); packPanels();
    }"""); p.wait_for_timeout(2500)   # let the build-time packing timers finish first

    def pos():
        return p.evaluate("""() => Object.fromEntries([...document.querySelectorAll('.panel')]
            .map(e=>[e.querySelector('.panel-title__name').textContent.trim(),
                     e.style.left + ',' + e.style.top]))""")
    before = pos()
    # open and close a section in one panel; nothing else should move
    p.evaluate("""() => { const panel=[...document.querySelectorAll('.panel')]
        .find(x=>x.querySelector('.panel-title__name').textContent.trim()==='Combat');
        const d=[...panel.querySelectorAll('.section-divider')].find(x=>x.textContent.includes('AIMBOT'));
        d.click(); }"""); p.wait_for_timeout(1400)
    after = pos()
    moved = [k for k in before if before[k] != after.get(k)]
    print(("  ok   " if not moved else "  FAIL ") + "no panel moves when a section toggles" +
          ("" if not moved else "  -- moved: " + str(moved)))

    # colour menu should fit without scrolling
    p.evaluate("""() => { const r=[...document.querySelectorAll('.dropdown')]
        .find(e=>e.textContent.includes('Chams Color')); window.__cc=r; r.click(); }""")
    p.wait_for_timeout(300)
    sc = p.evaluate("""() => { const m=window.__cc.parentElement.querySelector('.dropdown__menu');
        return {scroll: m.scrollHeight > m.clientHeight, h: m.scrollHeight, c: m.clientHeight}; }""")
    print(("  ok   " if not sc['scroll'] else "  FAIL ") + f"7-colour menu needs no scrollbar {sc}")
    p.screenshot(path="menu.png")
    b.close()
