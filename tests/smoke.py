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
            b = p.chromium.launch(channel="chromium")  # the full browser in headless mode (the bare headless shell refuses notifications)
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

            # ---- save status: a write the server hasn't acknowledged shows "Saving…" ----
            pg, errs = page()
            E(pg, FAKE_FS)
            E(pg, "fakeFs.doc=(orig=>path=>{const d=orig(path);d.set=x=>{F.writes.push(x);return new Promise(r=>{(window.__acks=window.__acks||[]).push(r);});};return d;})(fakeFs.doc)")
            E(pg, "remoteStore(fbDb(fakeFs),'u2').then(s=>{store=s;const t=F.cbs['data/users/u2/player/tasks'];if(t)t({docs:[],size:0,empty:true});})"); pg.wait_for_timeout(200)
            E(pg, "fire('data/users/u2/player',{name:'Mat',_rev:3,gold:10,xp:10},false)"); pg.wait_for_timeout(200)
            E(pg, "setSync('ok','Synced to your account');player.gold=11;store.savePlayer(player)"); pg.wait_for_timeout(1800)
            check("unacknowledged save shows Saving…", "saving" in E(pg, "$('sync').className"), E(pg, "$('sync').className"))
            E(pg, "__acks.forEach(r=>r())"); pg.wait_for_timeout(200)
            check("acknowledged save shows synced", "ok" in E(pg, "$('sync').className"))
            pg.close()

            # ---- restore points: made, listed, restored, and the restore itself undoable ----
            pg, errs = page()
            pg.evaluate(SETUP)
            E(pg, "player.gold=1234;player.name='Point Mat';rpSave(false)"); pg.wait_for_timeout(400)
            E(pg, "player.gold=5;player.name='Later Mat';RP.list=null;rpLoad()"); pg.wait_for_timeout(400)
            n = E(pg, "(RP.list||[]).length")
            check("restore point listed", n >= 1, str(n))
            E(pg, "rpPick(RP.list[0].id)"); pg.wait_for_timeout(300)
            check("restore point opens the replace check", E(pg, "!!(ui.restore&&ui.restore.point)") and E(pg, "!!document.getElementById('bkApply')"))
            E(pg, "applyRestore()"); pg.wait_for_timeout(500)
            check("restore point restores the save", E(pg, "player.name") == "Point Mat", E(pg, "player.name"))
            E(pg, "RP.list=null;rpLoad()"); pg.wait_for_timeout(400)
            check("restoring keeps a 'before restore' point", E(pg, "RP.list.some(x=>x.pre&&x.gold===5)"))
            check("restore points: no page errors", not errs, "; ".join(errs[:2]))
            pg.close()

            # ---- service worker: sounds stored on the device and served as byte ranges ----
            pg, errs = page()
            E(pg, "navigator.serviceWorker.register('sw.js')"); pg.wait_for_timeout(1500)
            pg.reload(); pg.wait_for_timeout(1500)
            ctl = pg.evaluate("!!navigator.serviceWorker.controller")
            check("service worker controls the page", ctl)
            if ctl:
                r1 = pg.evaluate("fetch('sfx/gold.mp3',{headers:{Range:'bytes=0-99'}}).then(r=>r.arrayBuffer().then(b=>[r.status,b.byteLength]))")
                r2 = pg.evaluate("fetch('sfx/gold.mp3',{headers:{Range:'bytes=0-99'}}).then(r=>r.arrayBuffer().then(b=>[r.status,b.byteLength,r.headers.get('content-range')]))")
                check("sound served as a byte range from the device", r2[0] == 206 and r2[1] == 100, str((r1, r2)))
                n = len(json.load(open(os.path.join(ROOT, "version.json"))).get("sfx", []))
                pg.evaluate("fetch('version.json').then(r=>r.json()).then(j=>navigator.serviceWorker.controller.postMessage({precache:j.sfx.map(f=>'sfx/'+f)}))")
                pg.wait_for_timeout(4000)
                got = pg.evaluate("caches.open('crawl-media-v1').then(c=>c.keys()).then(k=>k.length)")
                check("every sound stored for offline", n > 0 and got >= n, f"{got} of {n}")
                pg.context.set_offline(True)
                off = pg.evaluate("fetch('sfx/boss-kill.mp3').then(r=>r.status).catch(e=>'failed')")
                check("sounds play offline", off == 200, str(off))
                pg.context.set_offline(False)
                # a push from the sender shows a notification (delivered through Chrome DevTools)
                pg.context.grant_permissions(["notifications"])
                cdp = pg.context.new_cdp_session(pg)
                regs = []
                cdp.on("ServiceWorker.workerRegistrationUpdated", lambda e: regs.extend(e["registrations"]))
                cdp.send("ServiceWorker.enable"); pg.wait_for_timeout(500)
                rid = next((r["registrationId"] for r in regs if not r.get("isDeleted")), None)
                if rid:
                    cdp.send("ServiceWorker.deliverPushMessage", {"origin": f"http://127.0.0.1:{port}", "registrationId": rid,
                        "data": json.dumps({"title": "The Crawl", "body": "Pip hits you overnight", "open": "quests", "tag": "crawl-evening"})})
                    pg.wait_for_timeout(800)
                    shown = pg.evaluate("navigator.serviceWorker.ready.then(r=>r.getNotifications()).then(n=>n.map(x=>x.body).join('|'))")
                    check("push message shows a notification", "Pip hits you overnight" in shown, shown)
                else:
                    check("push message shows a notification", False, "no registration id")
            check("service worker: no page errors", not errs, "; ".join(errs[:2]))
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

            # ---- an ordinary quest in the default mode: no glide, slim card, folds popups in, tucks itself away ----
            pg, errs = page()
            pg.evaluate(SETUP)
            E(pg, "ensureBoss();player.boss.maxHp=99999;player.mobs=[];player.rival=null;player.hp=80;setTab('quests');render()")
            E(pg, "document.querySelectorAll('#board .quest')[document.querySelectorAll('#board .quest').length-1].scrollIntoView({block:'center'})")
            pg.wait_for_timeout(300); y0 = E(pg, "scrollY")
            pg.wait_for_timeout(500); E(pg, "document.querySelectorAll('#toasts .toast').forEach(n=>n.remove())")  # the floor note from loading
            pg.locator("#board .quest [data-done]").last.click()
            try:
                pg.wait_for_selector("#repWrap.mini", timeout=4000); ok = True
            except Exception:
                ok = False
            why = E(pg, "JSON.stringify(ui.lastShow)")
            big = E(pg, "Object.values(ui.lastShow).some(Boolean)")  # the map can still roll a mob or a rival: that's a big moment
            if big:
                check("quest with a random big moment: full show", E(pg, "!!REP.el&&!REP.mini"), why)
            else:
                check("ordinary quest: slim summary, no glide or cam", ok and not E(pg, "!!$('crawlCam')") and not E(pg, "STAGE.to!=null"), why)
            stray = E(pg, "[...document.querySelectorAll('#toasts .toast:not(.ach)')].map(t=>t.textContent.slice(0,60)).join(' / ')")
            check("ordinary quest: no stray popups over the board", not stray, stray)
            if not big:
                pg.wait_for_timeout(7000)
                check("ordinary quest: summary tucks itself away", not E(pg, "!!REP.el"))
            check("ordinary quest: no page errors", not errs, "; ".join(errs[:2]))
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

            # ---- phone: the hotbar never sits over a quest's Complete or ⋯ button ----
            pg, errs = page(360, 740)
            pg.evaluate(SETUP)
            E(pg, "setTab('quests');render()")
            under = pg.evaluate("""()=>{const hb=document.getElementById('hotbar');if(!hb||hb.hidden)return 'no hotbar';const h=hb.getBoundingClientRect(),bad=[];
              document.querySelectorAll('#board .quest [data-done],#board .quest [data-menu]').forEach(b=>{const r=b.getBoundingClientRect(),x=r.left+r.width/2;if(x>h.left&&x<h.right)bad.push(b.getAttribute('aria-label'));});return bad.join(', ');}""")
            check("360px: hotbar clear of quest buttons", not under, under)
            pg.close()

            # ---- field guide: a new crawler gets a card for a mob, once ----
            pg, errs = page()
            pg.evaluate(SETUP)
            E(pg, "prefs.guide={};prefs.guideInit=1;guideAt=0;player.doneCount=2;document.querySelectorAll('#toasts .toast').forEach(n=>n.remove());render()")
            pg.wait_for_timeout(2200)
            first = E(pg, "[...document.querySelectorAll('#toasts .toast')].map(t=>t.textContent).join('|')")
            check("field guide: first card shows", "Quests" in first or "Bosses" in first, first[:80])
            E(pg, "GUIDE.forEach(g=>prefs.guide[g.id]=1);delete prefs.guide.mob;guideAt=0;document.querySelectorAll('#toasts .toast').forEach(n=>n.remove());player.mobs=[{id:'m9',n:'Rat Swarm',k:'rat',a:'A',pack:false,hp:30,max:30}];render()")
            pg.wait_for_timeout(300); E(pg, "document.querySelectorAll('#toasts .toast').forEach(n=>n.remove())")
            pg.wait_for_timeout(8000)
            t = E(pg, "[...document.querySelectorAll('#toasts .toast')].map(t=>t.textContent).join('|')")
            check("field guide: mob card", "Mobs" in t, t[:80])
            E(pg, "openGear();ui.guideQ='poison';renderGuide()")
            check("field guide: search finds poison", E(pg, "document.querySelectorAll('#guideList .guide-it').length") >= 1 and "Poison" in E(pg, "$('guideList').textContent"))
            check("field guide: no page errors", not errs, "; ".join(errs[:2]))
            pg.close()

            # ---- Settings → Notifications renders in each state ----
            pg, errs = page()
            pg.evaluate(SETUP)
            E(pg, "openGear()")
            t1 = E(pg, "$('pushCtl').textContent")
            E(pg, "fb={user:{uid:'u1'},fs:{doc:p=>({get:()=>Promise.resolve({exists:false}),set:()=>Promise.resolve(),delete:()=>Promise.resolve()})}};renderPushCtl()")
            t2 = E(pg, "$('pushCtl').textContent")
            E(pg, "prefs.push={evening:true,party:true,hour:20};renderPushCtl()")
            t3 = E(pg, "$('pushCtl').textContent")
            check("notifications panel: signed out / off / on", "Sign in" in t1 and "Turn on" in t2 and "8 pm" in t3, f"{t1[:40]} | {t2[:40]} | {t3[:60]}")
            E(pg, "fb=null;prefs.push=null")
            check("notifications panel: no page errors", not errs, "; ".join(errs[:2]))
            pg.close()

            # ---- map walk: a step is replayed when the map comes on screen; spare steps bank and spend ----
            pg, errs = page()
            pg.evaluate(SETUP)
            E(pg, "$('toasts').style.display='none';player.mobs=[];player.rival=null;ensureMap();player.map.rooms.forEach((r,i)=>{if(i>=1&&i<=2){r.t='empty';r.guard=0;}});render()")
            E(pg, "mapStep({effort:1,stat:'DEX',title:''});mapStep({effort:1,stat:'DEX',title:''},true);render()")
            trail = E(pg, "MWALK.w&&MWALK.w.pts.join(',')")
            E(pg, "$('mapBox').scrollIntoView({block:'center'})"); pg.wait_for_timeout(900)
            started = E(pg, "!!(MWALK.w&&MWALK.w.at)&&document.getAnimations().some(a=>a.effect&&a.effect.target&&a.effect.target.id==='mapTok')")
            check("map walk: trail recorded and plays on screen", trail == "0,1,2" and started, f"{trail} {started}")
            pg.wait_for_timeout(2600)
            check("map walk: clears after playing", E(pg, "MWALK.w===null"))
            E(pg, "player.spare={a1:2};player.map.tgt=player.map.pos;player.spSteps=0;mapStep({effort:1});mapStep({effort:1});mapGo(0)")
            sp = E(pg, "player.spSteps")
            check("spare steps leave spare gear copies alone", E(pg, "JSON.stringify(player.spare)") == '{"a1":2}', E(pg, "JSON.stringify(player.spare)"))
            E(pg, "$('spareGo').click()")
            check("spare steps: bank 2, spend them walking back", sp == 2 and E(pg, "player.map.pos===0&&player.spSteps===0"), f"{sp} pos {E(pg,'player.map.pos')}")
            E(pg, "player.map.tgt=null;player.spSteps=0;player.map.pos=farOf(player.map);mapStep({effort:1,stat:'DEX',title:''})")
            check("spare steps: never spent exploring", E(pg, "spareNeed(player.map)===0"))
            # a save wiped by the v3.17.0 bug gets its spare gear back from a restore point
            E(pg, "rpTx('readwrite',st=>st.put({id:'x|old',uid:RP.uid||null,at:Date.now()-864e5,day:'old',pre:false,j:JSON.stringify({player:Object.assign({},player,{spare:{a1:3,w1:1}}),tasks:[]})}))")
            pg.wait_for_timeout(200)
            E(pg, "player=normPlayer(Object.assign({},player,{spare:'[object Object]1'}));RP.fixing=false;rpTick()")
            pg.wait_for_timeout(600)
            check("wiped spare gear restored from a restore point", E(pg, "JSON.stringify(player.spare)") == '{"a1":3,"w1":1}' and E(pg, "!player.spareFix"), E(pg, "JSON.stringify(player.spare)"))
            check("map walk / spare steps: no page errors", not errs, "; ".join(errs[:2]))
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
