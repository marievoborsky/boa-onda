const CACHE = 'boa-onda-v4';
const CORE = ['./index.html', './data.js', './manifest.webmanifest', './lektionen/tag01.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
// Netz zuerst für Kern-Dateien (damit Updates ankommen), Cache-Fallback offline.
// Audio: Cache zuerst (ändert sich nie), beim ersten Abspielen gespeichert.
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.pathname.includes('/audio/')) {
    e.respondWith(
      caches.open(CACHE).then(c => c.match(e.request).then(hit => hit ||
        fetch(e.request).then(res => { c.put(e.request, res.clone()); return res; })))
    );
  } else if (url.origin === location.origin) {
    e.respondWith(
      fetch(e.request).then(res => {
        caches.open(CACHE).then(c => c.put(e.request, res.clone()));
        return res.clone();
      }).catch(() => caches.match(e.request))
    );
  }
});
