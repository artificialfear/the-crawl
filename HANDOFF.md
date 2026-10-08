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
- Saves: Firestore via `remoteStore`; `_rev` guards plus a stale-device guard (no saves until the server copy loads).
  Since v3.0.3 the player doc is compare-and-set: each save carries `b` (the `_rev` it was built on) and `firestore.rules`
  rejects it unless `b` equals the server's `_rev`. A rejected save calls `onStaleSave`, which adopts the server copy
  (`adopt`, waits for a clean snapshot if needed) and warns the player. Any hand-written REST repair of a player doc must
  set `b` to the current `_rev` and `_rev` to `b+1`, or it will be rejected.
- Belt hotbar (v3.1.0): belts are gear with `slot:"belt"` and `belt:N` slots; `bestBelt`/`beltSlots` (best owned counts, 1 with none), `player.belt` = slot order, `renderHotbar`, `hbUse`, `openBelt`, `pickQuest`. New consumables must be added to `BELT_KEYS`/`consN`. Avatar belt: `avatarBelt` (under/over layers).
- Close-ups: `zoomCard({...})`. Mobs: `MOB_KINDS`, `pokeMob`, bestiary (`renderBestiary`). Party: `renderParty`, `ptSec`. Crafting: `openBench`. Quarters/hall: `openQt`, `enterHall`.
