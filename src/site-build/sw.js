// Network first, falling back to the last copy, so the app opens with no signal
// and always picks up a new version when online. Saves sync through Firestore's own offline cache.
// Sounds and voice clips (sfx/, vo/) are served from the cache once stored, so they play instantly and offline;
// each one is re-checked in the background once per service-worker lifetime, so a replaced sound still arrives.
const CACHE="crawl-shell-v1",MEDIA="crawl-media-v1";
self.addEventListener("install",e=>self.skipWaiting());
self.addEventListener("activate",e=>e.waitUntil(self.clients.claim()));
const fresh=new Set();
// Audio elements ask for byte ranges; answer from the stored whole file so iPhone and Android both accept it.
function ranged(req,res){
  const h=req.headers.get("range");if(!h||!res||res.status!==200)return res;
  return res.arrayBuffer().then(buf=>{
    const m=/bytes=(\d*)-(\d*)/.exec(h),n=buf.byteLength;
    let s=m&&m[1]?+m[1]:0,e=m&&m[2]?+m[2]:n-1;if(m&&!m[1]&&m[2]){s=Math.max(0,n-+m[2]);e=n-1;}
    e=Math.min(e,n-1);
    return new Response(buf.slice(s,e+1),{status:206,statusText:"Partial Content",headers:{"Content-Type":res.headers.get("Content-Type")||"audio/mpeg",
      "Content-Range":`bytes ${s}-${e}/${n}`,"Content-Length":String(e-s+1),"Accept-Ranges":"bytes"}});
  });
}
function media(req,url){
  return caches.open(MEDIA).then(c=>c.match(url).then(hit=>{
    const net=()=>fetch(url).then(r=>{if(r.status===200)c.put(url,r.clone()).catch(()=>{});return r;});
    if(hit){if(!fresh.has(url)){fresh.add(url);net().catch(()=>{});}return ranged(req,hit);}
    fresh.add(url);return net().then(r=>ranged(req,r));
  })).catch(()=>fetch(req));
}
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);if(u.origin!==location.origin)return;
  if(/\/(sfx|vo)\/[^/]+\.mp3$/.test(u.pathname)){e.respondWith(media(r,u.origin+u.pathname));return;}
  e.respondWith(fetch(r).then(res=>{if(res.status===200){const c=res.clone();caches.open(CACHE).then(k=>k.put(r,c)).catch(()=>{});}return res;})
    .catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match("index.html"))));
});
// The app sends the sound list once per version: store any that aren't cached yet, a few at a time.
self.addEventListener("message",e=>{
  const d=e.data;if(!d||!Array.isArray(d.precache))return;
  const base=self.registration.scope;
  e.waitUntil(caches.open(MEDIA).then(async c=>{
    const list=d.precache.map(p=>new URL(p,base).href);
    for(let i=0;i<list.length;i+=4)await Promise.all(list.slice(i,i+4).map(u=>c.match(u).then(m=>m||fetch(u).then(r=>{if(r.status===200)return c.put(u,r);}).catch(()=>{}))));
  }));
});
// Tapping a party notification brings The Crawl forward on the chat (or opens it if it was closed).
self.addEventListener("notificationclick",e=>{
  e.notification.close();const open=(e.notification.data&&e.notification.data.open)||"party";
  e.waitUntil(self.clients.matchAll({type:"window",includeUncontrolled:true}).then(list=>{
    for(const c of list){if("focus" in c){c.postMessage({open});return c.focus();}}
    return self.clients.openWindow("./?open="+open);
  }));
});
