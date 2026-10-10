// The Crawl's push notifications, sent while the app is closed.
// Run every 15 minutes by .github/workflows/push.yml with one secret, FIREBASE_SA (a Firebase service-account key).
//
// Each device that turns notifications on stores data/users/<uid>/push/<deviceId>:
//   { sub: "<PushSubscription JSON>", tz, hour (evening reminder, local), evening: bool, party: bool, partyCode, active (ms), lastEvening ("YYYY-MM-DD"), lastParty (ms) }
// Two kinds of message:
//   - Evening reminder, once a day at the chosen hour: overdue quests, a rival who'll hit you overnight, a streak about to end.
//     Nothing is sent on a day with nothing to warn about.
//   - Party: new chat messages and feed posts aimed at you (help requests, gifts) since you last had the app open.
// The VAPID key pair (which signs the pushes) is derived from the service-account key, so there's no second secret;
// its public half is published to config/push for the app to subscribe with.
import crypto from "node:crypto";
import { pathToFileURL } from "node:url";

const b64u = buf => Buffer.from(buf).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

export function deriveVapid(secret) {
  const ecdh = crypto.createECDH("prime256v1");
  for (let i = 0; ; i++) {  // the rare hash that isn't a valid P-256 key just moves on to the next counter
    const priv = crypto.createHash("sha256").update(`crawl-vapid|${i}|${secret}`).digest();
    try { ecdh.setPrivateKey(priv); return { publicKey: b64u(ecdh.getPublicKey()), privateKey: b64u(priv) }; } catch (e) { }
  }
}

export function localNow(tz, now = new Date()) {
  let parts;
  try { parts = new Intl.DateTimeFormat("en-CA", { timeZone: tz || "UTC", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", hourCycle: "h23" }).formatToParts(now); }
  catch (e) { return localNow("UTC", now); }
  const g = t => parts.find(p => p.type === t).value;
  return { date: `${g("year")}-${g("month")}-${g("day")}`, hour: +g("hour") % 24 };
}

const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;

// What tonight's reminder says, or null when there's nothing worth a buzz.
export function eveningMessage(player, tasks, today) {
  const open = (tasks || []).filter(t => t && !t.done && t.title);
  const overdue = open.filter(t => t.due && t.due < today);
  const dueToday = open.filter(t => t.due === today);
  const bits = [];
  if (player && player.rival && player.rival.n) bits.push(`${player.rival.n} hits you overnight`);
  if (overdue.length) bits.push(`${plural(overdue.length, "overdue quest")} will hit you in the morning`);
  if (dueToday.length) bits.push(`${plural(dueToday.length, "quest")} due today`);
  const streak = player && player.streak || 0;
  if (streak >= 2 && player.lastDoneDate && player.lastDoneDate < today) bits.push(`your ${streak}-day streak ends at midnight`);
  if (!bits.length) return null;
  const first = bits[0][0].toUpperCase() + bits[0].slice(1);
  return { title: "The Crawl", body: [first].concat(bits.slice(1)).join(" · ") + ". One quest fights back.", open: "quests", tag: "crawl-evening" };
}

// A crewmate newly hunted by a rival crawler (one ping per rival), so you can jump in and help.
export function huntedMessage(cards, uid, seen) {
  const fresh = Object.entries(cards || {}).filter(([id, c]) => id !== uid && c && c.rvl && c.rvl.id && !(seen || []).includes(c.rvl.id));
  if (!fresh.length) return null;
  const [, c] = fresh[0];
  return { msg: { title: `${c.name || "A crewmate"} needs backup`, body: `${c.rvl.n || "A rival crawler"} is hunting ${c.name || "them"}. Help from the Party tab before they're knocked out.`, open: "party", tag: "crawl-hunt" },
    ids: fresh.map(([, x]) => x.rvl.id) };
}

// New party chat and feed posts aimed at this crawler since `since`, as one notification.
export function partyMessage(chat, feed, uid, since, partyName) {
  const msgs = (chat || []).filter(m => m.uid !== uid && (m.at || 0) > since).sort((a, b) => a.at - b.at);
  const mine = (feed || []).filter(f => f.to === uid && f.uid !== uid && (f.at || 0) > since).sort((a, b) => a.at - b.at);
  if (mine.length) {
    const f = mine[mine.length - 1];
    return { title: `${f.name || "A crewmate"} · ${partyName || "Your party"}`, body: String(f.text || "").slice(0, 160) + (mine.length > 1 ? ` (+${mine.length - 1} more)` : ""), open: "party", tag: "crawl-party" };
  }
  if (msgs.length) {
    const m = msgs[msgs.length - 1];
    return { title: `${m.name || "Crawler"} · ${partyName || "Party chat"}`, body: String(m.text || "").slice(0, 160) + (msgs.length > 1 ? ` (+${msgs.length - 1} more)` : ""), open: "chat", tag: "crawl-chat" };
  }
  return null;
}

const parseJ = d => { if (!d) return null; if (typeof d.j === "string") { try { return JSON.parse(d.j); } catch (e) { return null; } } return d; };

export async function run({ db, webpush, now = new Date(), log = console.log }) {
  const sent = [], gone = [];
  const devs = await db.collectionGroup("push").get();
  const playerCache = new Map(), partyCache = new Map();
  const loadPlayer = async uid => {
    if (!playerCache.has(uid)) {
      const pRef = db.doc(`data/users/${uid}/player`);
      const [p, ts] = await Promise.all([pRef.get(), pRef.collection("tasks").get()]);
      playerCache.set(uid, { player: p.exists ? parseJ(p.data()) : null, tasks: ts.docs.map(d => parseJ(d.data())).filter(Boolean) });
    }
    return playerCache.get(uid);
  };
  const loadParty = async code => {
    if (!partyCache.has(code)) {
      const base = db.doc(`parties/${code}`);
      const [doc, chat, feed, cards] = await Promise.all([base.get(), base.collection("chat").orderBy("at", "desc").limit(15).get(), base.collection("feed").orderBy("at", "desc").limit(15).get(), base.collection("cards").get()]);
      partyCache.set(code, { name: doc.exists && doc.data().name, members: doc.exists && doc.data().members || [], chat: chat.docs.map(d => d.data()), feed: feed.docs.map(d => d.data()),
        cards: Object.fromEntries(cards.docs.map(d => [d.id, d.data()])) });
    }
    return partyCache.get(code);
  };
  for (const dev of devs.docs) {
    const d = dev.data(), uid = dev.ref.parent.parent.parent.id; // data/users/<uid>/player/push/<dev>
    let sub; try { sub = JSON.parse(d.sub); } catch (e) { continue; }
    const upd = {}, out = [];
    try {
      const { date, hour } = localNow(d.tz, now);
      if (d.evening !== false && hour >= (d.hour ?? 19) && d.lastEvening !== date) {
        upd.lastEvening = date;
        const { player, tasks } = await loadPlayer(uid);
        const m = player && eveningMessage(player, tasks, date);
        if (m) out.push(m);
      }
      if (d.party !== false && d.partyCode) {
        const pt = await loadParty(d.partyCode);
        if (pt.members.includes(uid)) {
          const since = Math.max(d.lastParty || 0, d.active || 0, now.getTime() - 6 * 3600e3); // nothing older than 6 hours
          const m = partyMessage(pt.chat, pt.feed, uid, since, pt.name);
          if (m) out.push(m);
          upd.lastParty = now.getTime();
          const h = huntedMessage(pt.cards, uid, d.hunts);
          if (h) { out.push(h.msg); upd.hunts = (d.hunts || []).concat(h.ids).slice(-30); }
        }
      }
      for (const m of out) {
        try { await webpush.sendNotification(sub, JSON.stringify(m), { TTL: 6 * 3600 }); sent.push([uid, m.tag]); }
        catch (e) { if (e.statusCode === 404 || e.statusCode === 410) { gone.push(dev.ref.path); await dev.ref.delete(); break; } log("push failed", e.statusCode || e.message); }
      }
      if (Object.keys(upd).length && !gone.includes(dev.ref.path)) await dev.ref.set(upd, { merge: true });
    } catch (e) { log("device", dev.ref.path, e.message); }
  }
  log(`devices ${devs.size}, sent ${sent.length}, removed ${gone.length}`);
  return { sent, gone };
}

async function main() {
  const sa = JSON.parse(process.env.FIREBASE_SA || "null");
  if (!sa || !sa.private_key) { console.error("FIREBASE_SA isn't set (or isn't the service-account JSON), so nothing can be sent. See HANDOFF.md → Notifications."); process.exit(1); }
  const { initializeApp, cert } = await import("firebase-admin/app");
  const { getFirestore } = await import("firebase-admin/firestore");
  const webpush = (await import("web-push")).default;
  initializeApp({ credential: cert(sa) });
  const db = getFirestore();
  const keys = deriveVapid(sa.private_key);
  webpush.setVapidDetails("https://artificialfear.github.io/the-crawl/", keys.publicKey, keys.privateKey);
  const cfg = await db.doc("config/push").get();
  if (!cfg.exists || cfg.data().vapid !== keys.publicKey) await db.doc("config/push").set({ vapid: keys.publicKey, at: Date.now() });
  await run({ db, webpush });
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) main().catch(e => { console.error(e); process.exit(1); });
