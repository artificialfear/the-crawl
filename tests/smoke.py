#!/usr/bin/env python3
"""Pre-deploy test run for The Crawl.

Run from the repo root before every push:   python3 tests/smoke.py
Builds index.html, serves a test copy on a free local port, and drives it in headless Chromium
(Playwright; PLAYWRIGHT_BROWSERS_PATH is preset in Claude's workspace). Exits 1 if anything fails.

Covers: the script parses; boot with a test player; the save path through the real fbDb wrapper over a
fake Firestore (cache vs server snapshots, compare-and-set revisions, held saves); finishing a quest from
low on the board (stage, report, glide back); combat numbers; every tab at phone and desktop width with no
errors and no sideways scrolling; the changelog's newest entry.
Add a check here whenever a bug gets through, so it can't come back.
"""
import os, re, sys, json, shutil, socket, subprocess, tempfile, time, threading, http.server, functools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS, PASSES = [], []

def check(name, ok, detail=""):
    (PASSES if ok else FAILS).append(name)
    print(("  ok   " if ok else "  FAIL ") + name + (f"  ({detail})" if detail and not ok else ""))

# The test player: a mid-game crawler with gear, a pet, potions and eight quests (one overdue, one with no date).
SETUP = r"""()=>{const E=__ev;document.querySelectorAll('.signin').forEach(n=>n.remove());
 E("store={kind:'local',savePlayer:()=>Promise.resolve(),saveTask:()=>Promise.resolve(),deleteTask:()=>Promise.resolve()}");
 const td=E("today()"),add=E("addDays");
 window.__P={name:"Mat",xp:4000,gold:900,hp:70,potions:3,bag:{focus:2,scroll:1},owned:["w1","a1","bt3","h4","c11"],pets:{salamander:{name:"Cinder",bond:30,at:1}},pet:"salamander",look:{},quarters:{at:1,up:{bed:1,craft:1},guests:[]},doneCount:40};
 E("player=normPlayer(window.__P);playerExists=true;loadedP=true;loadedT=true;");
 const T=[["Write the quarterly report",3,45,"INT",-1],["Water the plants",1,5,"CON",0],["Call the dentist",1,10,"CHA",0],["Practice scales 30m",2,30,"DEX",1],["Clean the garage",4,120,"STR",2],["Grade 7th grade quizzes",3,60,"INT",1],["Email the band boosters",2,15,"CHA",3],["Fix the bike tire",2,30,"STR",null]];
 window.__T=T.map((t,i)=>({id:'t'+i,title:t[0],effort:t[1],est:t[2],stat:t[3],due:t[4]==null?null:add(td,t[4]),done:false,created:Date.now()-i*1000}));
 E("tasks=window.__T");E("initPanelFolds()");E("render()");}"""

FAKE_FS = r"""window.F={cbs:{},opts:{},writes:[]};window.firebase=window.firebase||{};firebase.firestore=firebase.firestore||{};
 firebase.firestore.FieldValue={serverTimestamp:()=>'TS'};
 window.fakeFs={doc:path=>({id:path.split('/').pop(),onSnapshot:(a,b,c)=>{if(typeof a==='function'){F.opts[path]=null;F.cbs[path]=a;}else{F.opts[path]=a;F.cbs[path]=b;}},
   set:d=>{F.writes.push(d);return Promise.resolve();},get:()=>Promise.resolve({exists:false,data:()=>undefined}),delete:()=>Promise.resolve()}),
   collection:path=>({onSnapshot:(a,b)=>{F.cbs[path]=typeof a==='function'?a:b;},doc:id=>fakeFs.doc(path+'/'+id),
     orderBy:()=>({limit:()=>({get:()=>Promise.resolve({docs:[]})})}),get:()=>Promise.resolve({docs:[]})})};
 window.fire=(path,d,fromCache)=>F.cbs[path]({id:'player',exists:!!d,data:()=>d?{_rev:d._rev,j:JSON.stringify(d)}:undefined,metadata:{fromCache,hasPendingWrites:false}});"""

def build():
    r = subprocess.run([sys.executable, "src/site-build/build.py", "."], cwd=ROOT, capture_output=True, text=True)
    check("build", r.returncode == 0, r.stderr[-300:])
    html = open(os.path.join(ROOT, "index.html")).read()
    js = max(re.findall(r"<script>(.*?)</script>", html, re.S), key=len)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(js)
    r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
    check("script parses", r.returncode == 0, r.stderr[-400:])
    os.unlink(f.name)
    return html

def serve(html):
    d = tempfile.mkdtemp(prefix="crawl-smoke-")
    open(os.path.join(d, "index.html"), "w").write(html.replace("boot().catch(", "window.__ev=s=>eval(s);boot().catch(", 1))
    for n in os.listdir(ROOT):
        if n not in ("index.html", ".git", "site", "tests") and not os.path.exists(os.path.join(d, n)):
            os.symlink(os.path.join(ROOT, n), os.path.join(d, n))
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Quiet, directory=d)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, d, port

def main():
    from playwright.sync_api import sync_playwright
    html = build()
    if FAILS: return finish()
    m = re.search(r'const CHANGELOG=\[\s*\{v:"([\d.]+)"', html)
    check("changelog has a newest entry", bool(m))
    srv, d, port = serve(html)
    url = f"http://127.0.0.1:{port}/index.html"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            def page(w=390, h=844, **kw):
                errs = []
                pg = b.new_page(viewport={"width": w, "height": h}, **kw)
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(url); pg.wait_for_timeout(2000)
                return pg, errs
            E = lambda pg, js: pg.evaluate("s=>__ev(s)", js)

            # ---- saving, through the real fbDb wrapper over a fake Firestore ----
            pg, errs = page()
            E(pg, FAKE_FS)
            E(pg, "remoteStore(fbDb(fakeFs),'u1').then(s=>{store=s;const t=F.cbs['data/users/u1/player/tasks'];if(t)t({docs:[],size:0,empty:true,docChanges:()=>[]});})")
            pg.wait_for_timeout(300)
            check("player listener asks for metadata changes", E(pg, "!!(F.opts['data/users/u1/player']&&F.opts['data/users/u1/player'].includeMetadataChanges)"))
            E(pg, "fire('data/users/u1/player',{name:'Mat',_rev:41,gold:4321,xp:99999},true)"); pg.wait_for_timeout(150)
            E(pg, "player.gold+=1;store.savePlayer(player)"); pg.wait_for_timeout(150)
            check("no save while only the cached copy has loaded", E(pg, "F.writes.length") == 0)
            E(pg, "fire('data/users/u1/player',{name:'Mat',_rev:41,gold:4321,xp:99999},false)"); pg.wait_for_timeout(250)
            check("server copy loads", E(pg, "player.gold") in (4321, 4322) and E(pg, "playerExists"))
            E(pg, "player.gold=5000;store.savePlayer(player)"); pg.wait_for_timeout(250)
            w = E(pg, "JSON.stringify(F.writes.map(w=>({b:w.b,r:w._rev,g:JSON.parse(w.j).gold})))")
            ws = json.loads(w)
            chain = bool(ws) and ws[0]["b"] == 41 and all(ws[i]["b"] == ws[i-1]["r"] for i in range(1, len(ws)))
            check("each save names the revision it was built on", chain and any(x["g"] >= 5000 for x in ws), w)
            check("save loop: no page errors", not errs, "; ".join(errs[:2]))
            pg.close()

            # ---- finishing a quest from low on the board ----
            pg, errs = page()
            pg.evaluate(SETUP)
            E(pg, "ensureBoss();player.mobs=[{id:'m1',n:'Rat Swarm',k:'rat',a:'A',pack:false,hp:40,max:40}];player.hp=80;setTab('quests');render()")
            E(pg, "document.querySelectorAll('#board .quest')[document.querySelectorAll('#board .quest').length-1].scrollIntoView({block:'center'})")
            pg.wait_for_timeout(300); y0 = E(pg, "scrollY")
            n0 = E(pg, "tasks.filter(t=>!t.done).length")
            pg.locator("#board .quest [data-done]").last.click()
            pg.wait_for_timeout(1300)
            check("quest: page glides up to the fight", E(pg, "scrollY") < y0 - 200, f"y {y0} -> {E(pg, 'scrollY')}")
            try:
                pg.wait_for_selector(".fxnum", timeout=3000); fx = True
            except Exception:
                fx = False
            check("quest: hit numbers show", fx)
            try:
                pg.wait_for_selector("#repWrap", timeout=4000); rep = True
            except Exception:
                rep = False
            check("quest: report opens", rep)
            check("quest: marked done", E(pg, "tasks.filter(t=>!t.done&&!t.rec).length") <= n0 - 1 or E(pg, "tasks.some(t=>t.done)"))
            check("quest: cards unfrozen", not E(pg, "staged()"))
            for _ in range(40):
                if not E(pg, "SHOWQ.busy"): break
                if E(pg, "!!document.querySelector('.victory')"): pg.keyboard.press("Escape")
                pg.wait_for_timeout(500)
            E(pg, "closeReport()"); pg.wait_for_timeout(800)
            for _ in range(20):  # entrances for anything new play before the glide back
                if not E(pg, "ENTR.going||ENTR.wait.size>0"): break
                pg.wait_for_timeout(500)
            pg.wait_for_timeout(1200)
            check("quest: glides back to the board", abs(E(pg, "scrollY") - y0) < 80, f"{E(pg, 'scrollY')} vs {y0}")
            check("quest: no page errors", not errs, "; ".join(errs[:2]))
            pg.close()

            # ---- combat numbers ----
            pg, errs = page()
            pg.evaluate(SETUP)
            E(pg, "ensureBoss();player.mobs=[{id:'m1',n:'Rat Swarm',k:'rat',a:'A',pack:false,hp:30,max:30}];player.rival=spawnRival({})||player.rival;player.hp=80;setTab('quests');render()")
            E(pg, "dealDamage(7);player.mobs[0].hp=12;player.rival.hp-=9;render()"); pg.wait_for_timeout(200)
            kinds = E(pg, "[...document.querySelectorAll('.fxnum')].map(d=>d.className).join(' ')")
            check("combat: boss, mob and rival numbers", all(k in kinds for k in ("fx-boss", "fx-mob", "fx-rv")), kinds)
            pg.close()

            # ---- every tab, phone and desktop ----
            for w, h in ((390, 844), (1280, 800)):
                pg, errs = page(w, h)
                pg.evaluate(SETUP)
                for tab in ("quests", "hero", "loot", "show", "safe", "party"):
                    E(pg, f"setTab('{tab}')"); pg.wait_for_timeout(250)
                    over = E(pg, "document.documentElement.scrollWidth-innerWidth")
                    check(f"{w}px {tab}: no sideways scroll", over <= 1, f"{over}px too wide")
                check(f"{w}px tabs: no page errors", not errs, "; ".join(errs[:2]))
                pg.close()

            # ---- reduced motion still completes a quest ----
            pg, errs = page(reduced_motion="reduce")
            pg.evaluate(SETUP)
            E(pg, "setTab('quests');render()")
            pg.locator("#board .quest [data-done]").last.click()
            try:
                pg.wait_for_selector("#repWrap", timeout=4000); rep = True
            except Exception:
                rep = False
            check("reduced motion: report opens", rep and not errs, "; ".join(errs[:2]))
            pg.close()
            b.close()
    finally:
        srv.shutdown(); shutil.rmtree(d, ignore_errors=True)
    finish()

def finish():
    print(f"\n{len(PASSES)} passed, {len(FAILS)} failed")
    if FAILS:
        print("FAILED: " + ", ".join(FAILS)); sys.exit(1)

if __name__ == "__main__":
    main()
