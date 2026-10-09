// Zwei getrennte Caches: die Shell wird bei jedem Update ersetzt, die Audios
// bleiben liegen – ein Versionssprung darf keine 15 MB Neudownload auslösen.
const SHELL = 'boa-onda-shell-v41';
const AUDIO = 'boa-onda-audio-v1';
// Vorab nur der Vokabel-Index und die erste Woche; jede weitere Lektion landet beim
// ersten Öffnen im Cache (siehe fetch: Netz zuerst, Antwort wird gespeichert).
const LEKTIONEN = ['./lektionen/index.json', './lektionen/leseworte.json'].concat(Array.from({ length: 7 }, (_, i) => `./lektionen/tag${String(i + 1).padStart(2, '0')}.json`));
const CORE = [
  './index.html', './data.js', './manifest.webmanifest', './descobrir.json',
  './logo.webp', './karte.webp', './karte-lisboa.webp', './boa-onda-welle.webp', './datenschutz.html', './druck.html',
  './vendor/supabase.js',   // Konto/Sync (supabase-js, MIT) – lokal, damit die App offline startet
  './fonts/fonts.css',
  './fonts/robotomono-af121f2f.woff2',
  './fonts/robotomono-fe832705.woff2',
  './fonts/spacegrotesk-a57c9413.woff2',
  './fonts/spacegrotesk-e911c2d9.woff2',
  './avatare/marie.webp', './avatare/ana.webp', './avatare/joao.webp', './avatare/vasco.webp', './avatare/martim.webp', './avatare/tiago.webp', './avatare/ines.webp', './avatare/carolina.webp', './avatare/tio.webp', './avatare/professora.webp',
  './etappen/porto.webp', './etappen/lisboa.webp', './etappen/milfontes.webp', './etappen/sagres.webp', './etappen/coimbra.webp', './etappen/alentejo.webp',
  './fotos/sagres-mareta.webp', './fotos/sagres-baia.webp', './fotos/sagres-vale.webp', './fotos/sagres-praia.webp', './fotos/sagres-falesia.webp', './fotos/sagres-estrada.webp',
  ...LEKTIONEN,
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(SHELL)
      // einzeln laden: eine fehlende Datei darf die Installation nicht kippen
      .then(c => Promise.all(CORE.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== SHELL && k !== AUDIO).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

// Nur vollständige 200er-Antworten cachen. Ohne diese Prüfung landete eine 404
// dauerhaft im Cache, und Safaris Range-Requests (206) ließen c.put werfen.
function cachebar(res) {
  return res && res.ok && res.status === 200 && res.type !== 'opaque';
}
// Netz mit Zeitlimit – bei schlechtem Netz nach 2,5 s auf den Cache fallen
function netzMitTimeout(req, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('timeout')), ms);
    fetch(req).then(res => { clearTimeout(t); resolve(res); },
                    err => { clearTimeout(t); reject(err); });
  });
}

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  // Nur eigene Dateien cachen. Alles Fremde – vor allem die Supabase-API (Konto, Sync, Auth) –
  // geht unangetastet ans Netz; eine gecachte Antwort wäre dort ein veralteter Lernstand.
  if (url.origin !== location.origin) return;

  if (url.pathname.includes('/audio/')) {
    // Audio ändert sich nie: Cache zuerst
    e.respondWith(caches.open(AUDIO).then(c =>
      c.match(e.request).then(hit => hit || fetch(e.request).then(res => {
        if (cachebar(res)) c.put(e.request, res.clone());
        return res;
      }))
    ));
  } else {
    // Rest: Netz zuerst (damit Updates ankommen), sonst Cache. Jede erfolgreiche Antwort
    // wird gespeichert – so sind einmal geöffnete Lektionen und Texte auch offline da.
    const istDaten = /\.json$/.test(url.pathname);
    e.respondWith(
      netzMitTimeout(e.request, 2500).then(res => {
        if (cachebar(res)) {
          const kopie = res.clone();
          caches.open(SHELL).then(c => c.put(e.request, kopie)).catch(() => {});
        }
        return res;
      }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(hit => hit ||
        // Daten, die nie geladen wurden, bekommen kein index.html untergeschoben (die App
        // zeigt dann „Bist du offline?" mit Nochmal-Knopf); Navigationen fallen auf die Shell
        (istDaten ? Response.error() : caches.match('./index.html'))))
    );
  }
});
