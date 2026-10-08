"""Builds the recorded voice clips for The Crawl.
   1. Export the script from the running app: voScript() -> vo-tools/script.json (see voexport.js)
   2. python3 vo-tools/gen_vo.py [voice ...]   (only regenerates clips whose text or voice settings changed)
   Output: site-build/vo/<voice>-<id>.mp3 and site-build/vo/index.json"""
import json,os,sys,hashlib,subprocess,tempfile
import numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.environ.get("VO_OUT") or os.path.join(HERE,"..","..","vo");os.makedirs(OUT,exist_ok=True)
KOK=os.environ.get("KOKORO_DIR") or os.path.join(HERE,"kokoro")  # kokoro-v1.0.onnx + voices-v1.0.bin from github.com/thewh1teagle/kokoro-onnx releases (model-files-v1.0)
PA_HEAVY="highpass=f=320,lowpass=f=4800,acompressor=threshold=-24dB:ratio=6:attack=3:release=60:makeup=4,asoftclip=type=tanh:threshold=0.6,equalizer=f=1800:t=q:w=1.2:g=5,aecho=0.85:0.55:60|140:0.28|0.14"
TV="highpass=f=90,lowpass=f=9500,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,aecho=0.8:0.4:25:0.08"
VOICES={ # kokoro voice (or "a:0.7,b:0.3" blend), speed, lang, filter
  "sys":  dict(v="am_fenrir",speed=1.0,lang="en-us",fx=PA_HEAVY),
  "chet": dict(v="am_michael",speed=1.0,lang="en-us",fx=TV),
  "marla":dict(v="af_bella",speed=1.05,lang="en-us",fx=TV),
  "dex":  dict(v="am_puck",speed=1.05,lang="en-us",fx=TV),
  "coach":dict(v="am_onyx",speed=1.1,lang="en-us",fx=TV),
}
k=Kokoro(os.path.join(KOK,"kokoro-v1.0.onnx"),os.path.join(KOK,"voices-v1.0.bin"))
def style(v):
    if ":" not in v:return v
    return sum(k.get_voice_style(n)*float(w) for n,w in (p.split(":") for p in v.split(",")))
script=json.load(open(os.path.join(HERE,"script.json")))
only=set(sys.argv[1:])
cachef=os.path.join(OUT,".cache.json");cache=json.load(open(cachef)) if os.path.exists(cachef) else {}
made=0
for ln in script:
    if not ln.get("text"):continue
    cfg=VOICES[ln["voice"]];sig=hashlib.md5((ln["text"]+json.dumps(cfg,sort_keys=True)).encode()).hexdigest()
    path=os.path.join(OUT,ln["id"]+".mp3")
    if (only and ln["voice"] not in only) or (cache.get(ln["id"])==sig and os.path.exists(path)):continue
    a,sr=k.create(ln["text"],voice=style(cfg["v"]),speed=cfg["speed"],lang=cfg["lang"])
    with tempfile.NamedTemporaryFile(suffix=".wav") as t:
        sf.write(t.name,np.concatenate([np.zeros(int(sr*.05),np.float32),a]),sr)
        subprocess.run(["ffmpeg","-loglevel","error","-y","-i",t.name,"-af",cfg["fx"]+",apad=pad_dur=0.35,loudnorm=I=-16:TP=-1.5","-ac","1","-ar","24000","-b:a","64k",path],check=True)
    cache[ln["id"]]=sig;made+=1
    if made%20==0:print(made,"clips…",flush=True)
ids=sorted(l["id"] for l in script if l.get("text") and os.path.exists(os.path.join(OUT,l["id"]+".mp3")))
keep=set(ids)
for f in os.listdir(OUT):
    if f.endswith(".mp3") and f[:-4] not in keep:os.remove(os.path.join(OUT,f));cache.pop(f[:-4],None)
json.dump(ids,open(os.path.join(OUT,"index.json"),"w"));json.dump(cache,open(cachef,"w"))
print("made",made,"total",len(ids))
