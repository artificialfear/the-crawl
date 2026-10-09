# The Crawl: notes for the next Claude session

Read this first. Everything needed to keep building lives in this repo.

## Layout
- `src/crawl.html`: the single source for the whole app (HTML, CSS, JS in one file). **Edit this, never `index.html`.**
- `src/site-build/build.py`: builds the site into the repo root (`index.html`, `version.json`, copies assets).
  `python3 src/site-build/build.py .` from the repo root. Firebase SDK files are already in `vendor/` (set `CRAWL_FBV` to an npm `firebase` dir to refresh them).
- `sfx/`: recorded sound effects, played with `clip(name, gain)`. New sounds go here (trim/normalise with ffmpeg first).
- `vo/`: recorded announcer and talk-show voice clips + `index.json`. Built by `tools/vo/` (see below).
- `firestore.rules`: Mat pastes these into the Firebase console by hand (project `the-crawl-4a1d6`).

## Deploy
Edit `src/crawl.html`, then from the repo root:
`python3 src/site-build/build.py . && git add -A && git commit -m "..." && git push origin HEAD:main`
GitHub Pages serves https://artificialfear.github.io/the-crawl/ . Open clients see an "update ready" bar via `version.json`.

## Voice clips (Kokoro TTS, free, offline)
- `pip install kokoro-onnx soundfile`; download `kokoro-v1.0.onnx` and `voices-v1.0.bin` from
  github.com/thewh1teagle/kokoro-onnx/releases (tag model-files-v1.0) into `tools/vo/kokoro/` (not committed, 350 MB).
- Export the line list from the running app: `voScript()` (see `tools/vo/voexport.js`, a Playwright script) → `tools/vo/script.json`.
- `python3 tools/vo/gen_vo.py [voice ...]` regenerates only changed clips into `vo/`.
- Voices: System announcer = `am_fenrir` + heavy PA filter; Chet = `am_michael`, Marla = `af_bella`, Dex = `am_puck`, Coach Brick = `am_onyx` (TV filter).
- Lines with fill-ins ({name}, {boss}…) need a spoken version in `VO_ALT` in crawl.html. The announcer always says "crawler", never the player's name.

## Mat's standing rules
- **Ask before every change whether it goes in the changelog** (small cosmetic or sound tweaks usually don't). Changelog lives in `CHANGELOG` in crawl.html, versions major.minor.patch, newest first.
- IP: nothing from Dungeon Crawler Carl by name (no named characters, book text or cover art). Original names only.
- Prefers fuller explanations, bullets, honest critique, flagging issues; ask clarifying questions on ambiguous requests; confirm only before big tasks.
- Test changes in a real browser (Playwright, `window.__ev` eval hook injected in test builds) before deploying.

## Systems worth knowing (search crawl.html for these)
- Floors/bosses: `ensureBoss`, `TIERS`; from the week of Oct 12, 2026 floors use **lairs** (`makeLairs`, `engageLair`, `lairPrompt`, `retreatLair`): 3-6 bosses in side rooms, optional, Charge stored while exploring, roaming bosses.
- Quest completion presentation is a queue: `beat(fn,gap)` / `beatHold` / `SHOWQ`. New effects after a quest should be beats, not raw timers.
  Since v3.2.0 the first beat opens the quest report (`openReport`); while it's open, `toast()` calls become report lines (`repLine`), achievements wait in `REP.ach` and then show one at a time (`achToast`/`ACHQ`). Every toast/report/achievement also goes to the 🔔 history (`histAdd`, localStorage `crawl.hist.v1`). `toast()` escapes text for kinds other than lvl/ach/quest; use `toastH()` for markup.
- Saves: Firestore via `remoteStore`; `_rev` guards plus a stale-device guard (no saves until the server copy loads).
  Since v3.0.3 the player doc is compare-and-set: each save carries `b` (the `_rev` it was built on) and `firestore.rules`
  rejects it unless `b` equals the server's `_rev`. A rejected save calls `onStaleSave`, which adopts the server copy
  (`adopt`, waits for a clean snapshot if needed) and warns the player. Any hand-written REST repair of a player doc must
  set `b` to the current `_rev` and `_rev` to `b+1`, or it will be rejected.
- Belt hotbar (v3.1.0): belts are gear with `slot:"belt"` and `belt:N` slots; `bestBelt`/`beltSlots` (best owned counts, 1 with none), `player.belt` = slot order, `renderHotbar`, `hbUse`, `openBelt`, `pickQuest`. New consumables must be added to `BELT_KEYS`/`consN`. Avatar belt: `avatarBelt` (under/over layers).
- Compact layout (v3.3.0): any `main section.panel` whose first child is an `h2` folds via `initPanelFolds` (prefs.fold). Floor theme strip in `renderTheme` (prefs.bannerOpen / bannerHide per week); boss fold `bossFold` (prefs.bossMini); new-quest box gets `.tight` until used (`addCompact`); quest cards are a 2x2 grid (`.qtop`). Avoid class `.cl` (hit animation).
- Body armour (v3.3.1): every armour is a row in `ARMOR_STYLE` (`tee:true` = open garment over the tee; fill "MAIL"/"TEE"), drawn by `armorBase` + `armorDetail(st,u,magic)` on the avatar and by `armorIcon` for loot icons (same drawing, scaled). Magical icons pass through `comicize` twice, so `armorIcon` thins strokes when `magic` is set.
- Gear art (v3.3.2): rings `ringIcon` + `RING_LOOK` (one design per ring id); gloves `gloveIcon`/`gloveFist`; boots `bootIcon`/`bootArt`; head gear `headArt` (+ `headLegacy` for h1/l1/l3/l7, `headDetail` overlays, framing in `HEAD_CENTER`); capes `capeArt`/`capeIcon` (`CAPE_STYLE` covers every cape, `CAPE_MAIN` = cloth colour); trinkets `trinketArt` (pets and icons); belts `beltArt(st,belt,id)`/`avatarBelt`. Icons pass through `comicize` (x1.6 strokes, twice for magical items), so icon code thins strokes where noted.
- Spells (v3.4.0): `SPELLS` table (14), `CLASS_SPELL` (starter per class, granted by `spellTick`), mana `player.mp` (cap `MP_MAX`) from `gainMana(t)` in `completeQuest`; learned `player.spells`, prepared `player.prep` (`spellSlots`: 2/3/4 at levels 1/10/20), unread `player.tomes`. Cast with `castSpell(id)`; effects hook into `mobFight` (opts.charm, player.charm), `rivalStep` (rv.hex), `dailyTick` (player.ward), `completeQuest` (player.haste, player.regrow), `partyTrack` (`chantOn`), party cards (`ch`, `mm`; applied by `spellCrew`). Boss damage spells go through `spellBossHit` (25% of a boss's HP cap via `player.spDmg`). Tomes: `tomeDrop` (boxes, bosses, rivals, secret rooms), shop via `TOME_PRICE`. UI: hotbar spell row, `renderSpellbook` (Hero tab), `spellIcon`/`tomeIcon`, `castFx`. Cast sound: `sfx/spell-cast.mp3` if added, else synth `cast`.
- Close-ups: `zoomCard({...})`. Mobs: `MOB_KINDS`, `pokeMob`, bestiary (`renderBestiary`). Party: `renderParty`, `ptSec`. Crafting: `openBench`. Quarters/hall: `openQt`, `enterHall`.

## Potion sickness (v3.5.0)
- `quaff(hud)` gates every sickness-causing drink (`POTION_KINDS`: potion, mana, focus). `drink/drinkFocus/drinkMana` take `o===true` to mean "from the belt" (the shop/bag pass click events, so the check is strict).
- Belt during sickness: refuses with a countdown. Anything else: drinks and adds a poison stack (`player.poison={n,at}`).
- `sickMins()` = max(10, 30 − 3×(CON lvl − 1)); stored as `player.sickUntil`.
- `poisonTick()` takes 2 HP × stacks per 15 min since `poison.at` (floored at 1 HP); runs on load and in a 30 s interval. Only `drinkAntidote()` clears it.
- New consumables: `mana` (100g, +40 MP, needs a known spell) and `antidote` (60g). Both are in BELT_KEYS, the shop, box drops and the inventory tooltip.

## Theme mob families (v3.6.0)
- `MOB_KINDS` now has 13 families. The 3 base ones (`BASE_MOBS`) spawn anywhere; the other 10 each have `th` (a floor theme id) and spawn 40% of the time (`THEME_MOB`) on that theme's floors (`themeMobKind()`).
- Twist keys live on each family (see the comment above `BASE_MOBS`). `mobFight` reads them: `mobHitMul` (noPhys/stat/offMul/quick), miss, kill rewards (xpMul/viewMul/box/stolen), survivor hooks (flee/regen/split), `mobNip` (nipMul/noNip) and steal.
- Art: `MOB_ART[k](eye,K)`, called from `mobCreature`. Scene colors: `K.col = [glow, dark, eye glint, alert border]`.
- Ghosts: `mb.exp` = next 6 a.m.; `mobUpkeep()` drops expired ones (in mobFight and on load). Firebolt/Chain call `mobFight(0,null,{spell:true,raw:dmg})` when `hasGhost()`. Ward banishes the first ghost. Charm skips ghosts.
- Arrival and poke sounds: `sfx/mob-<kind>.mp3` if present; ghosts fall back to the synth `SFX.wail`, the rest to `hurt`.

## Hotbar layout
- One row by default: spells (`.hb-sp`), a divider, then the belt row (`.hb-bt`). `hbFit()` measures the unclamped width after each render and resize; if it's wider than the screen minus 16px, it adds `.two` to the hotbar (spells stack on top) and `has-sp` to the body (extra bottom padding).
- With spells prepared, the belt button (`.hb-belt.mp`) is also the mana gauge: a conic ring via `--mp`, with the number in `.hb-mp`. The old `.hb-mana` circle is gone (its CSS is unused).

## INT mana refill and CHA haggling (v3.7.0)
- `manaRate(p)` = 1 + INT level, per hour. `manaTick()` accrues from `player.mpAt` (time away counts, nothing banks while full or with no spells). It runs on load and every 60 s. No save per tick: mp and mpAt only change together, so whichever gets saved next is consistent.
- `chaOff(p)` = 1% per CHA level above 1, max 20%, folded into `priceOf()`, so every in-game price uses it and `priceTag` shows the struck-out price. Real-world prizes don't use `priceOf`.

## Save hold (stale-device guard) fix
- The player listener uses `{includeMetadataChanges:true}` (fbDb's `docRef.onSnapshot` accepts an options object first; test save changes through `fbDb(fakeFs)`, not a bare mock, or wrapper bugs slip through). Without it, a cached copy that matched the server never got a confirmed snapshot, so `fresh` stayed false: the red "Loading your latest save…" stuck, and any save in the first 20 s (e.g. tapping Help on the Party tab) was dropped.
- Held saves are now remembered (`held`, `heldRev`) and written once the server copy is confirmed or the 20 s wait ends, but only if no newer revision arrived meanwhile (otherwise the "Another device had newer progress" toast shows).
- Snapshots carrying the revision we already hold are our own echoes and no longer replace the live `player` object (protects unsaved in-memory changes like mana refill).

## Attack spell targeting
- Firebolt/Chain Lightning: `spellTargets(id)` lists the mob on you, your rival and the boss (each with `err` if it can't be hit now). `spellPick` always opens (even with one target) so a stray tap never fires; mana is spent only after the choice. Every other spell goes through `spellConfirm` (Cast / Cancel) first, except Time Warp, which has its own picker. `spellStrike(id,"mob"|"rival")`, `castBoss(id)`.
- Damage `spellDmg(id)` = mobScale().xp × 1 or 1.5 × (1 + INT XP bonus). Mobs: `mobFight(0,null,{spell:true,raw})`. Rivals: capped at `RV_SPELL_CAP` (25%) of max HP per rival per day via `player.rvSp`; a spell can finish them (`rivalDown`). Boss keeps the `spellBossHit` cap (dry-run with its 2nd arg).
- Crewmates' rivals: `spellTargets` also lists each rival in `huntedMates()` as `mate:<uid>`. The caster can't write the crewmate's save, so the hit goes out on their own party card as `asp: {rivalId: {to, n}}` (cumulative), and the hunted player's `rivalCrew()` applies the new part. It shares that rival's daily spell cap (`rvSpellRoom`, published as `rvl.sp`) and never takes the last HP. On the caster's side, `mateSpellRoom` also limits them by what they've already sent today (`player.asSpDay`), so a crewmate who's offline can't be flooded. Spell helpers count as helpers for the thank-you reward (`rv.asp`).

## Pokes (v3.7.1)
- `pokeHit(lead)` runs on every poke: 1 damage, at most `POKE_MAX` (5) per mob (`mb.pk`), never below 1 HP, and a `POKE_NIP` (10%) chance of −1 HP to you. Family reactions: noPhys (ghost) is untouchable, miss (stalker) can dodge, flee+box (loot goblin) bolts and is removed, split (bunny) splits. The result shows in the close-up as `.poke-res` (passed via `ui.pokeNote`); a goblin that bolts shows a toast instead.
- Aim step: picking a target (or the only target) opens `spellAim(id,target,T)`, a preview of exactly what lands (mobs in order with before → after HP, rival/boss caps, fog-hidden HP) with Cast / Back / Cancel. Mana is spent only on Cast.

- Rival spell limit (updated): `RV_SPELL_CASTS` (2) spell hits per rival per day, each up to `RV_SPELL_CAP` (25%) of max HP (`rvHitCap`, `rvCastsLeft`, `rvSpNote`; `player.rvSp` = {id,d,n,c}). Crewmates' hits count toward the same 2: their card `asp[rid]` carries {n,c}, the owner's card publishes `rvl.spc` (hits left), and `mateSpellRoom` also counts the caster's own sends today (`asSpDay.c`).

## Art style (v3.8.0)
- `avatarSVG(eq)` wraps the figure in a filter from `avFx(u,eq)`. The default is cel: a warm multiply tint, a hard shadow band (silhouette offset) and a warm rim on the lit edge. It deliberately avoids blur and lighting primitives, because any animation in the SVG re-runs the filter. The swaying cape sits outside the filter in cel mode. `eq.style:"flat"` = the old look.
- Rival crawlers: `rvAvatar(rv, plate)` → `inkCard(eq,{psy,name,plate})`, built on the boss card template (same smoke filter seeded by name, ink hill with splatter, frame, corners and name banner, but no numeral; a psycho gets darker smoke and dripping ink), with an etched greyscale figure (`eq.style:"ink"`, accent `eq.inkc`: amber, or red for a psycho) on a tarot card. Ink cards are still: the cape is inside the filter and the animations are off. The figure is inlined as a `<g>`, not a nested `<svg>`, so page CSS like `.rv-av svg` can't move it.

## Poses and expressions (v3.9.0)
- `avatarSVG(eq)` takes `eq.pose` (else `look.pose`, default "ready") from `POSES`: ready (the original weapon stances), hips, crossed, victory, hurt. Outside ready, the weapon is drawn before the legs, so it never crosses the body: slung on the back (hilt over the right shoulder). In victory, a one-handed weapon is raised in the right fist; a two-handed one rests on the right shoulder in the right hand while the left fist goes up. Hurt tilts the upper body. The arms for each pose are in the `A` table in the hands section (arm1 + fist + ringOn; shoulder plates via armorDetail).
- `eq.expr` is a key of `EXPRS`, a brow + mouth preset (happy, smug, angry, determined, hurt, unhinged, shout). Unhinged also shrinks the pupils (`PR`). New look options: brow "worried", mouths "ouch" and "wild".
- `myMood()`: victory for 10 min after bossKills/rivalKills/rivalKOs/level go up (in-memory `ui.winAt`, published on the party card as `win`, an expiry timestamp), hurt under 30% HP, no change for mobs or rivals (pose and face kept); `moodNote()` explains an override in the look editor. Used by the hero sheet, `zoomMe` and `myAvatarEq`.
- Rivals: `rvMood(rv)` picks a stance and face from a hash of the name, unhinged for psychos, angry under 50% HP, hurt under 20%.

## Feel pass, batch 1 (changelog entry comes with the last batch)
- `render()` snapshots card positions (`fxSnap`) before drawing, then `fxTick(pre)` compares with the last state (`ui.fxPrev`): boss HP drop → floating number on `#bossPanel .bossart` plus `.fx-shake`; mob HP drop (by mob id, including mobs that died) → number on the mob alert ("Hit!" for hidden HP); rival HP drop → number, and "KO!" after `rivalDown` (`ui.rvLastKO`); your HP down/up → red/green number on the avatar and `#sheet.av-hit`; finished quest → `.av-hop`; level-up → `.av-lvl`. Numbers are `.fxnum` divs on `body`, removed after 1.4 s.
- Idle life: avatarSVG wraps the upper body in `<g class="breathe">` (inside `.upper`, whose transform attribute the hurt pose uses) and the eyes in `<g class="eyes">`. The CSS breathes and blinks them on the Hero tab, `zoomMe` and the look editor only, and only without reduced motion.
- Boss cards crack below 25% HP (`bossSVG` opts.crack), except on fog floors.

## Feel pass, batch 2
- `AV_SCENE[theme]` gives each floor theme its own avatar backdrop (wall, brick, floor, flame colours, torch glow, bokeh, plus an overlay `ov`: water, lanterns, fog, a clock, moss and coins, ghosts, a spotlight, sand, books, paw prints). `avScene()` = the current floor's theme; `eq.scene` overrides it (party avatars pass it so the cache keys per floor). The page-wide theme palette (`THEME_LOOK`) already existed.
- Gear presence: any legendary piece adds a pulsing gold aura behind the figure (`.legaura`) and gold twinkles; epic adds purple twinkles (`.gearglow .twinkle`). Not on ink cards.
- Pets: `.pet-cheer` (victory), `.pet-cower` (hurt) and `.pet-hiss` with a red "!" when `myMood()` returns `threat` (a mob or rival on you), plus a ♪ when cheering.
- Mob deaths: `fxDeath(at, kind)`, with a style per family from `FX_DEATH` (dust, drops, wisps, gears, coins, confetti, pages, fluff), fired from `fxTick` when a mob id disappears (`ui.fxKinds` remembers the kinds).
- Map markers: `headToken(eq,cx,cy,r,ring,id)` = the bare flat avatar cropped to the head in a ring (cached in `headCache`), used for you on the floor map and for everyone on the raid floor.

## Feel pass, batch 3 (v3.10.0 entry covers batches 1–3)
- Per-part shading (cel only, `SHON`): `tube()` adds a `SHADE` band on the lower-left of every limb or sleeve 18 px or wider (offset (−.16w, +.16w), width .42w, so it stays inside the outline, caps included), plus shade over the torso's left side, the face's left side, a chin shadow on the neck and a brim shadow under hats. The cel filter now lights from the right (rim on the right, shadow band on the left), matching the line art's existing left-side hatching.
- Fonts: the Google Fonts link now also loads IM Fell English, the engraved face that bossSVG and inkCard ask for (before this they fell back to Georgia). Headings stay Bungee. Test browsers can't reach Google Fonts; for accurate screenshots, `npm pack @fontsource/<font>` and inject @font-face rules.

## Stage (v3.10.1): quest hits play where you can see them
- `completeQuest` calls `stageOn()`; while `staged()` (max 8 s) `render()` skips `STAGE_FROZEN` (renderBoss, renderMobAlert, renderRivalAlert) and skips `fxTick`, so those cards keep their pre-quest look and `ui.fxPrev` keeps the old numbers.
- Beats after the slice: `stageGo` (smooth-scrolls to the first visible of bossPanel/mobAlert/rivalAlert if any boss/mob/rival art is off screen, below the undo bar; shows `#crawlCam` PiP above the hotbar when `#avatarBox` won't be on screen after the scroll), then `stageEnd` (runs `fxTick(fxSnap())` on the frozen cards so a slain mob still bursts on its own card, `react()`, then unfreezes and renders 600 ms later), then `openReport` (which calls `camOut()`).
- `fxEl("me")` points at the cam while it's in; `meP` pulses both `#sheet` and `#crawlCam` (av-hit/av-hop/av-lvl). `fxTick` now returns whether anything visible fired.
- `closeReport` → `stageBack()` scrolls back to where you were unless you scrolled yourself (>60 px from where the stage left you).

## Entrances (v3.10.2)
- `entrWatch()` runs at the end of every `render()`: when a boss key / mob id / rival id is new while `showBusy()` (report open, staged, or a victory card), its kind goes in `ENTR.wait`; the matching panel (`ENTR_PANEL`) gets `.entr-wait` (opacity 0). Not toggled while staged (the frozen cards are still being hit).
- If a newcomer is waiting, `stageEnd` keeps the cards frozen until the report beat opens (otherwise there'd be a gap on screen).
- `entrRun()` polls every 400 ms until no report, victory, visible `.gearwrap/.hbwrap/#zoomWrap`, or busy beat queue; then `viewTo` glides up, `camIn(dy,{pose:"ready",expr:"determined",threat:true})`, and each card slams in (`.entr-in` + `.entrstamp`) with `entrSound(k)`, one per second; a card below the fold gets its own `viewTo(...,full)` glide first.
- The arrival sounds (mob cry, crawler-appear, bossAppear) are skipped in the report beats and the victory `after()` when that kind is in `ENTR.wait`; `ENTR.snd.mob` carries the mob kind.
- `closeReport` defers achievements + `stageBack()` to `ENTR.after` while entrances are waiting/running.
- Helpers shared with the stage: `viewBand()`, `viewTo(panels,arts,full)`, `camIn(dy,mood)`.
- Achievement toast: `.toast.ach` wraps; text and `.achacts` are each full width.

## Pre-deploy test run (tests/smoke.py)
- **Run `python3 tests/smoke.py` before every push**; it must end "0 failed". It builds, serves a test copy on a free port and drives headless Chromium: script parses, save path through the real `fbDb` over a fake Firestore (metadata listener, no save before the server copy, revision chain), finishing a quest from low on the board (glide up, numbers, report, unfreeze, glide back after entrances), combat numbers, all six tabs at 390px and 1280px (no errors, no sideways scroll), reduced motion.
- When a bug slips through, add a check for it there.

## After-quest modes (v3.11.0)
- `prefs.showMode`: "big" (default) | "full" | "quick"; Settings → After a quest (`renderShowCtl`, `SHOW_MODES`).
- In `completeQuest`, `bigMoment` = level-up, boss loot, rival win, mob death, arrivals (mobSnd0/rvNew/ENTR.wait), lair, ambush, storm. `slim` (no big moment in "big", or "quick") skips stageGo/cam: `stageEnd(hit,true)` unfreezes at once, and `openReport(head,true)` builds `.repwrap.mini` (no backdrop, compact lines, above the hotbar via `--mini-b`, tap to close, `repAuto()` closes 4.5 s after the last beat). Beat gaps cap at 450 ms while mini. A second quest joins whatever report is open.
- Quick mode never queues entrances.
- Skips: a document pointerdown (capture) while staged and before the report sets `SHOWQ.fast` and clears the hold; `beatHold` is a no-op while fast. Clicking the full report's backdrop = the Show all / Continue button.
- `REP.pend`: created by `stageOn`, toasts (not achievements) raised before the report opens are queued and replayed as report lines by `repPend()`; closeReport flushes any leftovers as normal toasts.

## Restore points and save status (v3.12.0)
- `RP` module (above `applyRestore`): `rpSave(pre)` writes `backupData()` to IndexedDB `crawl-restore`/`pts` (id `<uid|local>|<day>[|pre-<ts>]`, with lv/gold/open summary) and, when `store.backups` exists and `RP.cloud`, to `data/users/<uid>/player/backups/<day>[-pre-<ts>]` (needs the backups rule; a permission-denied turns cloud off for the session). Keeps 7 daily + 3 pre-restore per uid. `rpTick()` (end of render) makes the day's first point 3 s after the server copy is confirmed (`prefs["rp:<uid>"]`). `rpLoad()` merges device + account (dedup within 60 s); `rpPick(id)` fills `ui.restore` (with `point:true`) so the existing Replace check shows; `applyRestore` makes a pre-restore point first.
- fbDb: `docRef.trySet/tryDelete` (no error toast), `colRef.list()` (get). `remoteStore` api has `backups:{put,list,del}` and sets `RP.uid`.
- Save status: `fire()` calls `syncTrack(p)`; `SYNCQ.n` counts unacknowledged writes; after 1.5 s pending `syncShow` sets class `saving` (gold pulsing dot, "Saving…"/"Offline…"); only overrides the ok/saving states. `setSync` sets `data-short`, shown as `::after` on phones when not ok. Tapping #sync → `syncInfo()` toast with the last-saved time.
- **Rules:** `firestore.rules` gained `match /backups/{pointId}` under the player doc. Mat must paste the rules into the Firebase console for account copies; device copies work without it.

## Install + sounds on device (v3.13.0)
- `sw.js` (src/site-build): sfx/ and vo/ mp3s are cache-first in `crawl-media-v1`, re-checked in the background once per SW lifetime, and answered as 206 byte ranges (`ranged()`) from the stored whole file (Audio sends Range). Shell stays network-first (`crawl-shell-v1`, only 200s cached). A `{precache:[...]}` message stores missing sounds 4 at a time.
- build.py writes `sfx` (file list) into version.json; `checkForUpdate` (also 15 s after load) calls `sfxPrecache(j)` once per build when there's no update and no Save-Data.
- Install: `beforeinstallprompt` is captured into `installEvt`; Settings → Install the app (`renderInstallCtl`) shows the button, iPhone Share steps, or "installed"; `installNudge()` (45 s after load) toasts once per 14 days, max 3, phones in a browser with ≥3 quests done.

## Phone hotbar placement (v3.13.1)
- Phones: `.hotbar` is left-aligned (`left:max(8px,safe-area)`, no transform) so the right-hand quest buttons stay clear; `hbFit` wraps to `.two` when the one-row width exceeds `innerWidth-110` on phones (16 on desktop).
- tests/smoke.py now also checks that no quest's Complete/⋯ button center sits under the hotbar at any scroll position.

## Field guide (v3.14.0)
- `GUIDE` entries {id,t,when(p),line,more}; `guideTick()` at the end of render shows the first unseen entry whose `when` is true as a `.toast.guide` (More → `openGuide(id)`), one per 20 s, never while a report/show/entrance/victory/zoom/toast/Settings is up (retries in 6 s). Seen state is per device in `prefs.guide`; `prefs.guideInit` marks everything seen for crawlers with 25+ quests. Settings → Field guide (`renderGuide`, search `ui.guideQ`, reset button).
- When adding a system, add a GUIDE entry for it.

## Notifications (v3.15.0)
- Sender: `tools/push/send.mjs`, run by `.github/workflows/push.yml` (cron at :07/:22/:37/:52 + manual "Run workflow"). Needs repo secret **FIREBASE_SA** (service-account key JSON). VAPID keys are derived from the SA private key (`deriveVapid`), and the public half is written to `config/push` each run if it changed. Pure functions (`eveningMessage`, `partyMessage`, `huntedMessage`, `localNow`) are exported for testing; `run({db,webpush,now})` takes injected deps.
- Per device: `data/users/<uid>/player/push/<prefs.devId>` {sub, tz, hour, evening, party, partyCode, active, lastEvening, lastParty, hunts}. Evening: once per local date at/after `hour`, only if there's something to warn about. Party: chat/feed-to-you newer than max(lastParty, active, now−6h); hunted crewmates once per rival id. 404/410 from the push service deletes the device doc.
- App: Settings → Notifications (`renderPushCtl`, `pushOn/pushOff/pushSet`), `pushTouch()` at the end of render updates active/tz/partyCode every 2 min while visible. SW `push` event shows the notification; taps open quests/party/chat (`?open=` too).
- Rules: `push/{deviceId}` (owner) under the player doc, `config/{id}` (get if signed in).
- **Mat's one-time setup:** paste rules; Firebase console → Project settings → Service accounts → Generate new private key; GitHub repo → Settings → Secrets and variables → Actions → New repository secret `FIREBASE_SA` = the whole JSON file's contents; Actions tab → Push notifications → Run workflow (creates config/push). Until then the job logs "FIREBASE_SA isn't set" and the app says notifications aren't switched on yet.
- A stray branch `wf-probe` (a one-step manual-only workflow) was pushed while checking that workflow files can be pushed from this workspace; the proxy blocks deleting branches, so Mat should delete it on GitHub.
- tests/smoke.py now launches `channel="chromium"` (full browser, headless) because the bare headless shell refuses notification permission; it delivers a push over DevTools and checks the notification.
