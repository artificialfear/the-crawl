import json,re
p='crawl.html';s=open(p).read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(s.count(a),a[:90]);s=s.replace(a,b)
ALT={
"{name} finishes a quest. The crowd briefly looks up from their phones.":"Our crawler finishes a quest. The crowd briefly looks up from their phones.",
"{name} did the thing. Somebody check whether they're feeling okay.":"The crawler did the thing. Somebody check whether they're feeling okay.",
"One more off the board. Only {open} left between you and the sweet release of an empty list.":"One more off the board. Just the rest of them left between you and the sweet release of an empty list.",
"{name} finally finishes an overdue quest. Late, sweaty and technically a win.":"Our crawler finally finishes an overdue quest. Late, sweaty, and technically a win.",
"{name} gives up on a quest. The audience respects honesty. They're still booing.":"The crawler gives up on a quest. The audience respects honesty. They're still booing.",
"Level {L}! The audience is shocked. Frankly, so are we.":"Level up! The audience is shocked. Frankly, so are we.",
"{name} hits Level {L}. Somebody get this crawler a participation trophy.":"Our crawler levels up. Somebody get this crawler a participation trophy.",
"{boss} is down! The crowd goes wild. Some of them had money on the other guy.":"The boss is down! The crowd goes wild. Some of them had money on the other guy.",
"{boss} has been defeated. Producers are pretending they always believed in you.":"The boss has been defeated. Producers are pretending they always believed in you.",
"The stairwell closed and {boss} walks away untouched. {name} was nowhere near the stairs.":"The stairwell closed, and the boss walks away untouched. Our crawler was nowhere near the stairs.",
"Welcome to Floor {floor}: {theme}. Management apologizes for nothing.":"Welcome to the new floor. Check this week's theme. Management apologizes for nothing.",
"Floor {floor} is {theme} this week. The producers insist it's for your growth.":"There's a new theme on this floor this week. The producers insist it's for your growth.",
"{theme}, Floor {floor}. Please keep your hands, feet and dignity inside the dungeon.":"New floor, new theme. Please keep your hands, feet, and dignity inside the dungeon.",
"{name} is sheltering in the safe room today. No cameras allowed. The producers are furious.":"Our crawler is sheltering in the safe room today. No cameras allowed. The producers are furious.",
"No cameras in the safe room, and {name} knows it. Ratings are in free fall.":"No cameras in the safe room, and our crawler knows it. Ratings are in free fall.",
"{name} has gone into hiding. Chat is speculating wildly.":"The crawler has gone into hiding. Chat is speculating wildly.",
"Ladies and gentlemen, {name} is now a {race} {cls}. The betting markets are in chaos.":"Ladies and gentlemen, our crawler has picked a race and a class. The betting markets are in chaos.",
"{name} has chosen: {race}, {cls}. Somewhere, a focus group is screaming.":"The crawler has chosen. Somewhere, a focus group is screaming.",
"A {race} {cls}. Bold. Questionable. Extremely watchable.":"That race. That class. Bold. Questionable. Extremely watchable.",
"{name} rerolls. Nobody liked those options anyway.":"A reroll. Nobody liked those options anyway.",
"{name} climbs to #{rank}. {rival} just felt a chill and doesn't know why.":"Our crawler climbs the rankings. Somebody just above them felt a chill and doesn't know why.",
"New rank for {name}: #{rank}. The producers pretend they saw it coming.":"A new rank for our crawler. The producers pretend they saw it coming.",
"#{rank}! {name} is moving up. {rival} has asked to speak to a manager.":"Moving up the board! The crawler they just passed has asked to speak to a manager.",
"{name} signs with {brand}. Integrity: sold. Price: one box.":"Our crawler signs a sponsor deal. Integrity: sold. Price: one box.",
"{brand} welcomes {name} to the family. The family has a very strict contract.":"Our newest sponsor welcomes the crawler to the family. The family has a very strict contract.",
"Brought to you by {brand}, as of about four seconds ago.":"This crawler is now brought to you by a sponsor, as of about four seconds ago.",
"{name} turns down {brand}. Bold. Broke, but bold.":"Our crawler turns down a sponsor. Bold. Broke, but bold.",
"{brand} has been rejected. They're taking it about as well as you'd expect.":"The sponsor has been rejected. They're taking it about as well as you'd expect.",
"No deal for {brand}. {name} remains independent and slightly poorer.":"No deal. The crawler remains independent, and slightly poorer.",
"{pet} joins the show. The audience immediately likes it more than you.":"A new pet joins the show. The audience immediately likes it more than you.",
"Say hello to {pet}. Ratings just went up, and it wasn't because of you.":"Say hello to the new pet. Ratings just went up, and it wasn't because of you.",
"{pet} has hatched! Chat is already arguing about its name. You've been overruled.":"The egg has hatched! Chat is already arguing about its name. You've been overruled.",
"It's alive! {pet} enters the dungeon and immediately bites a producer.":"It's alive! The new pet enters the dungeon and immediately bites a producer.",
"Next up: {boss}, the {tier}. They've heard about you.":"Next up: a new boss. They've heard about you.",
"{boss} steps out of the shadows. {tier}. The crowd leans in.":"The next boss steps out of the shadows. The crowd leans in.",
"Here comes {boss}, the {tier}. Try not to embarrass us.":"Here comes the next boss. Try not to embarrass us.",
"{name} has been knocked out by their own to-do list. A first for the show. Well, not a first.":"Our crawler has been knocked out by their own to-do list. A first for the show. Well, not a first.",
"{name} drinks a Potion of Focus. Eyes wide. Jaw clenched. Next quest is getting destroyed.":"The crawler drinks a Potion of Focus. Eyes wide. Jaw clenched. The next quest is getting destroyed.",
"{name} reads a Scroll of Extension. Procrastination, but make it magic.":"A Scroll of Extension. Procrastination, but make it magic.",
"Smoke bomb! {name} vanishes. The chore will be back. Chores always come back.":"Smoke bomb! The crawler vanishes. The chore will be back. Chores always come back.",
"{name} throws a smoke bomb and skips a chore. The crowd boos. The crowd also respects it.":"Our crawler throws a smoke bomb and skips a chore. The crowd boos. The crowd also respects it.",
"{name} has pledged themselves to {god}. The sponsor's stock is up two percent.":"Our crawler has pledged themselves to a god. The sponsor's stock is up two percent.",
"{god} has a new worshipper: {name}. Terms and conditions were not read.":"A god has a new worshipper. Terms and conditions were not read.",
"Breaking: {name} kneels before {god}. Somewhere, a marketing team high-fives.":"Breaking: our crawler kneels before a god. Somewhere, a marketing team high-fives.",
"Final day on Floor {floor}. The stairwell closes at midnight. {boss} is still standing.":"Final day on this floor. The stairwell closes at midnight, and the boss is still standing.",
"Tick tock. The Floor {floor} stairwell shuts tonight and {boss} knows it.":"Tick tock. The stairwell shuts tonight, and the boss knows it.",
"It's {time} and you've finished nothing today. Bold strategy. Let's see if it pays off.":"It's getting late, and you've finished nothing today. Bold strategy. Let's see if it pays off.",
"{name} cashes in for a real-world prize. Treat yourself. Allegedly, you earned it.":"Our crawler cashes in for a real-world prize. Treat yourself. Allegedly, you earned it.",
'"{title}". Gripping. Truly the stuff of legend.':"That quest name. Gripping. Truly the stuff of legend.",
'"{title}" has been added. The bards are already struggling to rhyme it.':"Your new quest has been added. The bards are already struggling to rhyme it.",
'"{title}"? The dungeon has seen worse. Not much worse, but worse.':"That quest? The dungeon has seen worse. Not much worse, but worse.",
'"{title}". Our writers couldn\'t have come up with that. They tried.':"That quest. Our writers couldn't have come up with it. They tried.",
'Breaking: {name} vows to "{title}". Experts are cautiously unimpressed.':"Breaking: our crawler has made a vow. Experts are cautiously unimpressed.",
'"{title}" is on the board. It\'s staring at you. Stare back. Then do it.':"It's on the board now. It's staring at you. Stare back. Then do it.",
"{open} open quests. At this point the board is a lifestyle.":"That many open quests? At this point, the board is a lifestyle.",
"Quest number {open}. The board is applying for its own zip code.":"Another quest. The board is applying for its own zip code.",
"That's {adds} quests added today. Adding them is not the same as doing them. We checked.":"That's a lot of quests added today. Adding them is not the same as doing them. We checked.",
"Folks, you know them, you tolerate them, it's {name}!":"Folks, you know them, you tolerate them, it's our next crawler!",
"Please welcome a crawler who is, legally, still alive: {name}!":"Please welcome a crawler who is, legally, still alive!",
"Our next guest has done several things. Some on purpose. {name}!":"Our next guest has done several things. Some on purpose. Welcome, crawler!",
"So here's my challenge, and I say this with love and a contract: {goal} by {due}. On live TV. Yes?":"So here's my challenge, and I say this with love and a contract. The goal's on your screen, and so is the deadline. On live TV. Yes?",
"Good morning! Today's tea is piping hot and it is {name}!":"Good morning! Today's tea is piping hot, and it is our crawler!",
"Dex, look who finally said yes to us! {name}, everybody!":"Dex, look who finally said yes to us! Our crawler, everybody!",
"Grab your coffee, we've got {name} on the couch!":"Grab your coffee, we've got a crawler on the couch!",
"Okay, okay, before we let you go: {goal} by {due}. Pinky promise, on air. Deal?":"Okay, okay, before we let you go. That goal, by that date. Pinky promise, on air. Deal?",
"Welcome to Crawl Center. I've got the tape, I've got the numbers, and I've got {name}.":"Welcome to Crawl Center. I've got the tape, I've got the numbers, and I've got a crawler.",
"Let's break down the film with the crawler herself or himself or themselves: {name}!":"Let's break down the film with the crawler herself, or himself, or themselves!",
"Here's a crawler with stats. Some of them good. {name}, welcome.":"Here's a crawler with stats. Some of them good. Welcome.",
"Here's what I want to see this week: {goal} by {due}. I'll be watching the tape. Commit?":"Here's what I want to see this week. That goal, by that date. I'll be watching the tape. Commit?",
}
QV=["That one quest has been overdue for a while now. Walk us through that.",
"So many overdue quests on your board. Is that a strategy, or a cry for help?",
"Look at that streak! How do you stay so consistent?",
"Be honest. Is your pet the real star of your show?",
"You and your pet are getting close. Are you two... exclusive?",
"Let's talk fashion. That weapon: statement piece, or cry for help?",
"Who dressed you? That armor is getting a lot of chatter.",
None,
"That many quests in a single day? Walk me through that game plan.",
"Look at your rank this floor. What's the gap between you and number one?",
"Your biggest hit this week. Was that the plan all along?",
None,
"Your best stat is way ahead of your worst one. Is that a weakness?",
"Another level, and still going. What keeps you crawling?",
"There's a boss waiting for you right now. Any message for them?",
"You've been knocked out before. Do you think about it?",
"You've abandoned a few quests. Commitment issues?",
"Look at all those finished quests! What's the secret?",
"That race and class combo! The fans have opinions. Any regrets?",
"All those achievements. Do you even look at them anymore?",
"You're sitting on a pile of gold. Any big purchases planned?",
"Look at all those quests on the board right now! How do you decide what to do first?",
"All those viewers tuned in. Does the pressure get to you?",
"Look how deep you've crawled. Where do you see yourself in five floors?"]
# SHOW_Q: add v before each q:
a=s.index("const SHOW_Q=[");b=s.index("\n];",a)
blk=s[a:b];parts=blk.split("q:");assert len(parts)==25,len(parts)
out=parts[0]
for i,pt in enumerate(parts[1:]):
    out+=(f'v:{json.dumps(QV[i])},' if QV[i] else "")+"q:"+pt
s=s[:a]+out+s[b:]
# voice core, inserted before announce
alt_js="const VO_ALT="+json.dumps(ALT,ensure_ascii=False,indent=0).replace('\n','')+";"
core='''/* ---------- Recorded voice ----------
   Announcer and talk-show lines are pre-recorded (Kokoro TTS + a dungeon PA filter; vo-tools/ builds them from voScript()).
   A clip is keyed by its line's template, before {name} and friends are filled in. Templates with fill-ins are recorded
   from a spoken version in VO_ALT that leaves the changing part out; the ticker still shows the real text.
   Clips live at vo/<voice>-<id>.mp3 and vo/index.json lists them. Anything without a clip falls back to the browser voice. */
'''+alt_js+'''
const VO_KINDS=["complete","late","abandon","level","boss","escaped","theme","shelter","chosen","reroll","rankup","signed","declined","pet","hatch","next","knocked","focus","scroll","smoke","god","stairwell","welcome","idle","reward"];
const VO_LIVE="The announcer is live. Try not to embarrass yourself.";
const voSrc=new Map();
function voNote(text,key){if(!text||text===key)return;voSrc.set(text,key);if(voSrc.size>80)voSrc.delete(voSrc.keys().next().value);}
function voHash(t){let h=2166136261;for(let i=0;i<t.length;i++){h^=t.charCodeAt(i);h=Math.imul(h,16777619);}return (h>>>0).toString(36);}
const voSpoken=k=>/\\{\\w+\\}/.test(k)?VO_ALT[k]||null:k;
const vo={idx:null,cur:null,loading:false};
function voLoad(){if(vo.idx||vo.loading||!window.CRAWL_FB||typeof fetch!=="function")return;vo.loading=true;
  fetch("vo/index.json").then(r=>r.ok?r.json():[]).then(a=>{vo.idx=new Set(a);}).catch(()=>{vo.idx=new Set();});}
voLoad();
function voStop(){if(vo.cur){try{vo.cur.pause();}catch(e){}vo.cur=null;}}
/* Plays the recorded clip for this line in this voice; false when there isn't one (the caller falls back). */
function voPlay(voice,text){
  if(!vo.idx||typeof Audio!=="function")return false;
  const key=voSrc.get(text)||text,id=voice+"-"+voHash(key);if(!vo.idx.has(id))return false;
  try{voStop();if(tts.ok)speechSynthesis.cancel();const a=new Audio(`vo/${id}.mp3`);a.volume=Math.max(.2,Math.min(1,prefs.vol==null?.6:+prefs.vol));vo.cur=a;
    const pr=a.play();if(pr&&pr.catch)pr.catch(()=>{});return true;}catch(e){return false;}
}
/* Who says a Morning Spill line: lines that name Dex are Marla's, lines that name Marla are Dex's, the rest alternate. */
function spillVoice(key){return /\\bMarla\\b/.test(key)?"dex":/\\bDex\\b/.test(key)?"marla":(hostTurn++%2?"dex":"marla");}
/* Every recordable line: [{voice, key, text}] for the clip builder. */
function voScript(){
  const out=[],add=(voice,key)=>{if(!key)return;const text=voSpoken(key);if(text)out.push({voice,key,text,id:voice+"-"+voHash(key)});else out.push({voice,key,text:null,missing:true});};
  VO_KINDS.forEach(k=>(QUIPS[k]||[]).forEach(l=>add("sys",l)));
  Object.values(ADD_QUIPS).forEach(a=>a.forEach(l=>add("sys",l)));add("sys",VO_LIVE);
  const hostVoices=k=>k==="spill"?["marla","dex"]:[k];
  const lineVoices=(k,l)=>k!=="spill"?[k]:/\\bMarla\\b/.test(l)?["dex"]:/\\bDex\\b/.test(l)?["marla"]:["marla","dex"];
  for(const k of HOST_KEYS){const H=HOSTS[k];[...H.hi,H.pledge,...H.good,...H.bad].forEach(l=>lineVoices(k,l).forEach(v=>add(v,l)));
    SHOW_Q.forEach(q=>{const key=q.v||(q.q.length===0?q.q():null);if(key)hostVoices(k).forEach(v=>add(v,key));});}
  return out;
}
'''
rep("function announce(text,force,how){",core+"function announce(text,force,how){")
# announce: try clip first for the system voice
rep('''  if(!tts.ok||(!force&&(prefs.tts!==true||prefs.sound===false||document.visibilityState!=="visible")))return;
  try{speechSynthesis.cancel();''','''  if(!force&&(prefs.tts!==true||prefs.sound===false||document.visibilityState!=="visible"))return;
  if(voPlay(how&&how.vo||"sys",text))return;
  if(!tts.ok)return;
  try{voStop();speechSynthesis.cancel();''')
rep('''function hostSpeak(host,text){const vs=HOST_VOICE[host]||HOST_VOICE.chet;announce(text,false,vs[(hostTurn++)%vs.length]);}''',
'''function hostSpeak(host,text){
  const key=voSrc.get(text)||text,v=host==="spill"?spillVoice(key):host;
  const vs=HOST_VOICE[host]||HOST_VOICE.chet;announce(text,false,Object.assign({vo:v},vs[host==="spill"&&v==="dex"?1:0]));}''')
# fill notes its template
rep('''function fill(t,v){v=Object.assign({name:player.name,open:tasks.filter(x=>!x.done).length},v||{});return t.replace(/\\{(\\w+)\\}/g,(m,k)=>v[k]!=null?v[k]:m);}''',
'''function fill(t,v){v=Object.assign({name:player.name,open:tasks.filter(x=>!x.done).length},v||{});const out=t.replace(/\\{(\\w+)\\}/g,(m,k)=>v[k]!=null?v[k]:m);voNote(out,t);return out;}''')
# talk show questions note their spoken key
rep('''<div class="bubble tq">${esc(q.q(ctx))}</div>''','''<div class="bubble tq">${esc((()=>{const t=q.q(ctx);voNote(t,q.v||t);return t;})())}</div>''')
# announcer-live uses constant
rep('''if(prefs.tts)announce("The announcer is live. Try not to embarrass yourself.",true);''','''if(prefs.tts)announce(VO_LIVE,true);''')
rep('''announce(ui.news&&ui.news[0]||"The announcer is live. Try not to embarrass yourself.",true);''','''announce(ui.news&&ui.news[0]||VO_LIVE,true);''')
open(p,'w').write(s)
print("ok")
