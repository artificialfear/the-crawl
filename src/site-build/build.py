#!/usr/bin/env python3
"""Build the GitHub Pages site from crawl.html (the single source).
Usage: build.py OUTDIR [--emu]   --emu points the app at local Firebase emulators (tests only)."""
import sys,os,shutil,json,hashlib
SRC=os.environ.get("CRAWL_SRC") or os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","crawl.html")
HERE=os.path.dirname(os.path.abspath(__file__))
FBV=os.environ.get("CRAWL_FBV","")  # firebase npm package dir; if missing, the vendor/ copies already in the output are kept
out=sys.argv[1];emu="--emu" in sys.argv
os.makedirs(out+"/vendor",exist_ok=True)
for f in ["firebase-app-compat.js","firebase-auth-compat.js","firebase-firestore-compat.js"]:
    if FBV and os.path.exists(f"{FBV}/{f}"):shutil.copy(f"{FBV}/{f}",f"{out}/vendor/{f}")
for f in ["manifest.webmanifest","icon-192.png","icon-512.png","sw.js","firestore.rules","README.md"]:
    if os.path.exists(f"{HERE}/{f}"):shutil.copy(f"{HERE}/{f}",f"{out}/{f}")
if os.path.isdir(f"{HERE}/sfx"):
    os.makedirs(f"{out}/sfx",exist_ok=True)
    for f in os.listdir(f"{HERE}/sfx"):shutil.copy(f"{HERE}/sfx/{f}",f"{out}/sfx/{f}")
if os.path.isdir(f"{HERE}/vo"):
    os.makedirs(f"{out}/vo",exist_ok=True)
    for f in os.listdir(f"{HERE}/vo"):
        if not f.startswith("."):shutil.copy(f"{HERE}/vo/{f}",f"{out}/vo/{f}")
if not os.path.exists(f"{out}/firebase-config.js"):
    shutil.copy(f"{HERE}/firebase-config.js",f"{out}/firebase-config.js")
app=open(SRC).read()
ver=hashlib.sha1(app.encode()).hexdigest()[:10]
import re
m=re.search(r'const CHANGELOG=\[\s*\{v:"([^"]+)",d:"([^"]+)",t:"([^"]+)"',app)
sfx=sorted(f for f in os.listdir(f"{out}/sfx") if f.endswith(".mp3")) if os.path.isdir(f"{out}/sfx") else []
json.dump({"build":ver,"v":m.group(1) if m else None,"t":m.group(3) if m else None,"sfx":sfx},open(f"{out}/version.json","w"))
emu_js='<script>window.CRAWL_EMU={auth:"http://127.0.0.1:9099",host:"127.0.0.1",port:8080};</script>' if emu else ""
head=f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0713">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="The Crawl">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="icon-192.png">
<link rel="apple-touch-icon" href="icon-192.png">
<style>body{{margin:0}}</style>
<script src="vendor/firebase-app-compat.js"></script>
<script src="vendor/firebase-auth-compat.js"></script>
<script src="vendor/firebase-firestore-compat.js"></script>
<script src="firebase-config.js?v={ver}"></script>
<script>window.CRAWL_BUILD="{ver}";</script>
{emu_js}
<script>if("serviceWorker" in navigator&&location.protocol==="https:")addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{{}}));</script>
</head><body>
'''
open(f"{out}/index.html","w").write(head+app+"\n</body></html>\n")
print("built",out,ver)
