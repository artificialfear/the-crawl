// Network first, falling back to the last copy, so the app opens with no signal
// and always picks up a new version when online. Saves sync through Firestore's own offline cache.
const CACHE="crawl-shell-v1";
self.addEventListener("install",e=>self.skipWaiting());
self.addEventListener("activate",e=>e.waitUntil(self.clients.claim()));
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);if(u.origin!==location.origin)return;
  e.respondWith(fetch(r).then(res=>{if(res.ok){const c=res.clone();caches.open(CACHE).then(k=>k.put(r,c));}return res;})
    .catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match("index.html"))));
});
// Tapping a party notification brings The Crawl forward on the chat (or opens it if it was closed).
self.addEventListener("notificationclick",e=>{
  e.notification.close();const open=(e.notification.data&&e.notification.data.open)||"party";
  e.waitUntil(self.clients.matchAll({type:"window",includeUncontrolled:true}).then(list=>{
    for(const c of list){if("focus" in c){c.postMessage({open});return c.focus();}}
    return self.clients.openWindow("./?open="+open);
  }));
});
