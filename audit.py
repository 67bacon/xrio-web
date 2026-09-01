"""Exercise every control and interaction in the panel and report what breaks.

Written because the UI defects this session were all found by the user in play:
each one cost a round trip and several of my guesses. A harness that clicks
everything finds them before he does.
"""
from playwright.sync_api import sync_playwright
import os, json

FAIL, PASS = [], []
def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(("  ok   " if ok else "  FAIL ") + name + (("  -- " + str(detail)) if detail and not ok else ""))

SCHEMA_JS = """() => {
  schema = [
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Enable Aimbot', flag:'AimbotToggle', desc:'自动瞄准总开关'},
    {type:'dropdown',tab:'Combat', section:'AIMBOT', name:'Aim Mode', flag:'AimModeDropdown', options:['Silent Aim','Right Click Lock']},
    {type:'dropdown',tab:'Combat', section:'AIMBOT', name:'Wallbang', flag:'WallbangModeDropdown', options:['Off','Normal','Dangerous'], desc:'三选一'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Rapid Fire', flag:'RapidFireToggle', risk:true, desc:'服务器会校验'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Wallbang (RCL)', flag:'WallbangRCLToggle'},
    {type:'slider',  tab:'Combat', section:'AIMBOT', name:'FOV Radius', flag:'FOVSlider', min:50, max:500, suffix:'px'},
    {type:'keybind', tab:'Settings', section:'UI CONTROL', name:'Panic Key', flag:'PanicKey', default:'END'},
    {type:'toggle',  tab:'Movement', section:'MOVEMENT', name:'Bunny Hop', flag:'BhopToggle', desc:'自动连跳'},
  ];
  for (let i=0;i<20;i++) schema.push({type:'dropdown',tab:'Misc',section:'SKIN CHANGER',
      name:'Gun'+i, flag:'Skin'+i, options:['Stock','Vanilla','Howl']});
  flags = {AimbotToggle:false, AimModeDropdown:'Silent Aim', WallbangModeDropdown:'Off',
           RapidFireToggle:false, WallbangRCLToggle:false, FOVSlider:210, PanicKey:'END', BhopToggle:false};
  for (let i=0;i<20;i++) flags['Skin'+i]='Stock';
  luaConnected = true; schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags();
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1600, "height": 1000})
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("file://" + os.getcwd() + "/audit.html")
    p.wait_for_timeout(1200)
    p.evaluate(SCHEMA_JS)
    p.wait_for_timeout(900)
    p.evaluate("() => { document.querySelector('.loader-card')?.remove(); window.__sent=[]; window.send=(x)=>window.__sent.push(x); }")

    print("\n--- panels ---")
    names = p.evaluate("() => [...document.querySelectorAll('.panel-title__name')].map(e=>e.textContent.trim())")
    check("5 panels built", len(names) == 4, names)   # Combat/Movement/Misc/Settings

    print("\n--- toggle ---")
    p.evaluate("""() => {
      window.__log=[]; const row=[...document.querySelectorAll('.toggle')].find(e=>e.textContent.includes('Enable Aimbot'));
      window.__row=row;
      new MutationObserver(()=>window.__log.push(row.classList.contains('on')?'ON':'OFF'))
        .observe(row,{attributes:true,attributeFilter:['class']});
    }""")
    p.evaluate("() => window.__row.click()")
    p.wait_for_timeout(200)
    log = p.evaluate("() => window.__log")
    check("one click = one state change", log == ['ON'], log)
    sent = p.evaluate("() => window.__sent")
    check("click sends set_flag", any(m.get('flag')=='AimbotToggle' for m in sent), sent)

    print("\n--- dropdown ---")
    p.evaluate("""() => {
        schema.push({type:'dropdown', tab:'Visuals', section:'ESP', name:'Chams Color',
          flag:'ChamsColor', options:['Red','Green','Blue','Yellow','Pink','Cyan','White']});
        flags['ChamsColor']='Red'; schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags();
        const row=[...document.querySelectorAll('.dropdown')]
          .find(e=>e.textContent.includes('Chams Color')); window.__dd=row; row.click(); }""")
    p.wait_for_timeout(200)
    open_ = p.evaluate("() => window.__dd.classList.contains('open')")
    check("dropdown opens on click", open_)
    vis = p.evaluate("""() => { const m=window.__dd.parentElement.querySelector('.dropdown__menu');
        return m && getComputedStyle(m).display !== 'none'; }""")
    check("menu is visible when open", vis)
    p.evaluate("""() => { const m=window.__dd.parentElement.querySelector('.dropdown__menu');
        [...m.querySelectorAll('.dropdown__opt')].find(o=>o.dataset.value==='Blue').click(); }""")
    p.wait_for_timeout(200)
    val = p.evaluate("() => window.__dd.querySelector('.dropdown__value').textContent")
    check("selecting sets the displayed value", val == 'Blue', val)
    closed = p.evaluate("() => !window.__dd.classList.contains('open')")
    check("menu closes after选择", closed)
    sent = p.evaluate("() => window.__sent")
    check("dropdown sends set_flag", any(m.get('flag')=='ChamsColor' and m.get('value')=='Blue' for m in sent), sent)

    print("\n--- dropdown echo (Lua returns a LIST) ---")
    p.evaluate("""() => window.__ws_onmessage({data: JSON.stringify(
        {type:'flag', flag:'ChamsColor', value:['Cyan']})})""")
    p.wait_for_timeout(200)
    val = p.evaluate("() => window.__dd.querySelector('.dropdown__value').textContent")
    check("list-shaped echo renders as plain text", val == 'Cyan', repr(val))

    print("\n--- risk / desc ---")
    check("risk tile marked", p.evaluate("""() => {const r=[...document.querySelectorAll('.toggle')]
        .find(e=>e.textContent.includes('Rapid Fire')); return r && r.classList.contains('risk');}"""))
    check("desc rendered", p.evaluate("""() => !![...document.querySelectorAll('.ctrl-row__desc')]
        .find(e=>e.textContent.includes('自动瞄准总开关'))"""))

    print("\n--- visibility map ---")
    p.evaluate("""() => window.__ws_onmessage({data: JSON.stringify({type:'flag', flag:'_visibility',
        value:{WallbangRCLToggle:false, FOVSlider:false}})})""")
    p.wait_for_timeout(300)
    check("mapped rows hide", p.evaluate("() => rowRefs.get('WallbangRCLToggle').hidden"))
    check("collapse note appears", p.evaluate("() => !!document.querySelector('.inactive-note')"))
    note = p.evaluate("() => {const n=document.querySelector('.inactive-note'); return n && n.textContent;}")
    check("note counts the hidden rows", note and '2' in note, note)
    p.evaluate("() => document.querySelector('.inactive-note').click()")
    p.wait_for_timeout(200)
    check("note expands them again", p.evaluate("() => !rowRefs.get('WallbangRCLToggle').hidden"))

    print("\n--- search filter ---")
    has = p.evaluate("() => !!document.querySelector('.sec-filter')")
    check("large section gets a search box", has)
    if has:
        p.evaluate("""() => { const i=document.querySelector('.sec-filter__input');
            i.value='Gun1'; i.dispatchEvent(new Event('input',{bubbles:true})); }""")
        p.wait_for_timeout(200)
        n = p.evaluate("""() => [...document.querySelectorAll('.dropdown-wrap')]
            .filter(e=>!e.hidden && e.closest('.section-body').querySelector('.sec-filter')).length""")
        check("filter narrows the list", 0 < n < 20, n)

    print("\n--- slider ---")
    sl = p.evaluate("""() => {const s=[...document.querySelectorAll('.slider')]
        .find(e=>e.textContent.includes('FOV Radius'));
        if(!s) return null; const t=s.querySelector('.slider__track'); const r=t.getBoundingClientRect();
        return {x:r.x+r.width*0.75, y:r.y+r.height/2};}""")
    if sl:
        p.mouse.move(sl['x'], sl['y']); p.mouse.down(); p.mouse.move(sl['x'], sl['y']); p.mouse.up()
        p.wait_for_timeout(200)
        v = p.evaluate("() => flags['FOVSlider']")
        check("slider drag changes value", v != 210, v)
    else:
        check("slider present", False, "not found")

    print("\n--- layout ---")
    boxes = p.evaluate("""() => [...document.querySelectorAll('.panel')].map(e=>{
        const r=e.getBoundingClientRect();
        return {n:e.querySelector('.panel-title__name').textContent.trim(),
                x:r.x,y:r.y,w:r.width,h:r.height};})""")
    over = []
    for i in range(len(boxes)):
        for j in range(i+1, len(boxes)):
            a, c = boxes[i], boxes[j]
            if a['x'] < c['x']+c['w'] and c['x'] < a['x']+a['w'] and a['y'] < c['y']+c['h'] and c['y'] < a['y']+a['h']:
                over.append(f"{a['n']}×{c['n']}")
    check("no overlapping panels", not over, over)
    off = [b['n'] for b in boxes if b['x'] < 0 or b['y'] < 0 or b['x'] > 1600 or b['y'] > 1000]
    check("no panel off-screen", not off, off)

    print("\n--- segmented (few short options) ---")
    p.evaluate("""() => {
        schema.push({type:'dropdown', tab:'Movement', section:'MOVEMENT', name:'Strafe Mode',
          flag:'StrafeModeDropdown', segmented:true,
          options:['Auto','Pure Sideways','Keep Forward']});
        flags['StrafeModeDropdown']='Auto';
        schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags(); }""")
    check("a control that opts in renders inline", p.evaluate("""() =>
        !![...document.querySelectorAll('.segmented')].find(e=>e.textContent.includes('Strafe Mode'))"""))
    check("a control that does NOT opt in stays a popup", p.evaluate("""() =>
        !![...document.querySelectorAll('.dropdown')].find(e=>e.textContent.includes('Wallbang'))"""))
    check("many-option list stays a popup", p.evaluate("""() =>
        !![...document.querySelectorAll('.dropdown')].find(e=>e.textContent.includes('Chams Color'))"""))

    print("\n--- showWhen (value-dependent visibility) ---")
    p.evaluate("""() => {
      schema.push({type:'slider', tab:'Combat', section:'AIMBOT', name:'Dep Slider',
                   flag:'DepSlider', min:0, max:1,
                   showWhen:{flag:'WallbangModeDropdown', equals:'Normal'}});
      flags['DepSlider']=0.5;
      flags['WallbangModeDropdown']=['Off'];      // Lua sends dropdowns as a LIST
      schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags();
    }""")
    p.wait_for_timeout(500)
    check("hidden when rule unmet (list-shaped flag)", p.evaluate("() => rowRefs.get('DepSlider').hidden"))
    p.evaluate("() => { flags['WallbangModeDropdown']=['Normal']; applyShowWhen(); }")
    check("shown when rule met (list-shaped)", p.evaluate("() => !rowRefs.get('DepSlider').hidden"))
    p.evaluate("() => { flags['WallbangModeDropdown']='Normal'; applyShowWhen(); }")
    check("shown when rule met (string-shaped)", p.evaluate("() => !rowRefs.get('DepSlider').hidden"))
    p.evaluate("() => { flags['WallbangModeDropdown']='Dangerous'; applyShowWhen(); }")
    check("hidden again on switch away", p.evaluate("() => rowRefs.get('DepSlider').hidden"))
    p.evaluate("""() => window.__ws_onmessage({data: JSON.stringify(
        {type:'flag', flag:'WallbangModeDropdown', value:['Normal']})})""")
    p.wait_for_timeout(200)
    check("echo of the gating flag re-shows it",
          p.evaluate("() => !rowRefs.get('DepSlider').hidden"))
    p.evaluate("() => { flags['WallbangModeDropdown']='Off'; applyShowWhen();\
        window.__ws_onmessage({data: JSON.stringify({type:'flag', flag:'_visibility',\
        value:{WallbangRCLToggle:false}})}); }")
    p.wait_for_timeout(200)
    check("visibility map does not resurrect a showWhen-hidden row",
          p.evaluate("() => rowRefs.get('DepSlider').hidden"))

    print("\n--- console ---")
    check("no page errors", not errs, errs)

    p.screenshot(path="audit.png")
    b.close()

print(f"\n===== {len(PASS)} passed, {len(FAIL)} failed =====")
for f in FAIL: print("  FAILED:", f)
