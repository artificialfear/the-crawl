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
