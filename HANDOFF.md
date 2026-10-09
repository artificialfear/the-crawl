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
