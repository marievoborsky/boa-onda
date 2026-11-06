#!/usr/bin/env node
/* Handy-Testlauf (06.11.2026): spielt alle Lektionen in iPhone-Größe durch und tippt dabei wie ein
   Finger: Touch genau dort, wo der Knopf auf dem Bildschirm zu sehen ist. Vor jedem Tipp wird
   geprüft, ob an dieser Stelle wirklich der Knopf liegt. So fallen unsichtbare Schichten auf, die
   das Antippen abfangen (Fehler vom 06.11.: ausgeblendete Meldung lag über „Stunde abschließen“).

   Pro Lektion: jede Übung richtig lösen (ein Teil absichtlich ohne Akzent, einige erst falsch),
   je ein Vokabel-, Dialog- und Geschichten-Audio antippen, Test-Punkte selbst vergeben, dann
   „Stunde abschließen“ antippen und prüfen, dass das Abschluss-Fenster kommt und die Stunde
   gespeichert ist. Weiter über „… jetzt starten“, jede zehnte Lektion über die Kursliste.
   Danach: alle Lesetexte (Wörter antippen, Wort-Fenster), Tab-Leiste, eine Wiederholungsrunde.

   Voraussetzung: lokaler Server auf 8124 (Launch-Konfiguration „vokabel-app“).
     ~/.local/node/bin/node tools/handytest.js              # alles
     ~/.local/node/bin/node tools/handytest.js tag07 tag14  # nur diese Lektionen (ohne Texte/Tabs)
     NUR_TEXTE=1 …                                          # nur Lesetexte, Tabs, Wiederholung
     AB=tag21 / BIS=tag25 …                                 # Teilstrecke der Lektionen
     GEGENPROBE=1 … tag07                                   # baut den alten Meldungs-Fehler wieder ein:
                                                            # der Test muss dann „verdeckt“ melden
   Ergebnis in OUT (Standard: Temp-Ordner): befunde.json, Bildschirmfotos zu Befunden. */
const puppeteer = require('../../03_STORE/tools/node_modules/puppeteer-core');
const fs = require('fs'), path = require('path'), os = require('os');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BASE = process.env.BASE || 'http://localhost:8124/';
const OUT = process.env.OUT || path.join(os.tmpdir(), 'boa-onda-handytest');
const NUR = process.argv.slice(2);
const AB = process.env.AB || '';   // erst ab dieser Lektion (z. B. AB=tag21), sonst wie der volle Lauf
let bereit = false;
const sleep = ms => new Promise(r => setTimeout(r, ms));
fs.mkdirSync(OUT, { recursive: true });

const befunde = []; let aktuell = 'start', fotoNr = 0, page, letzterTipp = '', navigiert = false;
const z = { tipps: 0, verdeckt: 0, typed: 0, opts: 0, satz: 0, reveal: 0, selbst: 0, falschZuerst: 0,
  ohneAkzent: 0, perEnter: 0, audio: 0, worte: 0, lektionen: 0, abgeschlossen: 0, texte: 0 };
async function foto(name) {
  const f = path.join(OUT, `${String(++fotoNr).padStart(3, '0')}-${name}`.replace(/[^\w.\-]/g, '_') + '.png');
  try { await page.screenshot({ path: f }); } catch (e) {}
  return path.basename(f);
}
async function befund(art, wo, detail, mitFoto = true) {
  const b = { art, lektion: aktuell, wo, detail: detail || '' };
  if (mitFoto && befunde.filter(x => x.art === art).length < 6) b.foto = await foto(aktuell + '-' + art);
  befunde.push(b);
  console.log('BEFUND', art, '|', aktuell, '|', wo, '|', detail || '');
}
async function warte(fn, ms = 3000, arg) {
  try { await page.waitForFunction(fn, { timeout: ms, polling: 50 }, arg); return true; } catch (e) { return false; }
}
/* Wo liegt das Element, und trifft ein Finger in seiner Mitte wirklich das Element? */
async function lage(h, scrollen) {
  return h.evaluate((el, scrollen) => {
    if (scrollen) el.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
    const r = el.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
    const imBild = x >= 0 && y >= 0 && x < innerWidth && y < innerHeight;
    const oben = imBild ? document.elementFromPoint(x, y) : null;
    const b = e => e ? e.tagName.toLowerCase() + (e.id ? '#' + e.id : '')
      + (typeof e.className === 'string' && e.className.trim() ? '.' + e.className.trim().split(/\s+/).slice(0, 3).join('.') : '') : 'nichts';
    return { x, y, sichtbar: r.width > 0 && r.height > 0 && imBild, frei: !!oben && (oben === el || el.contains(oben)),
      oben: b(oben), text: (el.textContent || el.placeholder || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 40) };
  }, scrollen);
}
async function tippe(h, wo, scrollen = true) {
  if (!h) { await befund('Knopf fehlt', wo); return false; }
  if (scrollen) { await lage(h, true); await sleep(30); }
  const l = await lage(h, false);
  if (!l.sichtbar) { await befund('nicht sichtbar', wo, l.text); return false; }
  z.tipps++; letzterTipp = `${wo} „${l.text}“`;
  if (!l.frei) { z.verdeckt++; await befund('verdeckt', wo, `„${l.text}“ – darüber liegt ${l.oben}`); }
  await page.touchscreen.tap(l.x, l.y);
  await sleep(70);
  return l.frei;
}
async function tippeText(sel, text, wo) {
  const h = await page.evaluateHandle((sel, text) => [...document.querySelectorAll(sel)].find(b => b.textContent.trim().startsWith(text)) || null, sel, text);
  return tippe(h.asElement(), wo);
}
const ohneAkzent = t => t.normalize('NFD').replace(/[̀-ͯ]/g, '');

async function uebung(row, k) {
  const d = await row.evaluate(r => ({
    art: r.querySelector('[data-ziel]') ? 'satz' : r.querySelector('.exin') ? 'typed' : r.querySelector('.wchip') ? 'opts' : 'reveal',
    sol: r.querySelector('.asol').textContent, satz: r.dataset.satz || '', q: r.querySelector('.q').textContent.trim().slice(0, 50),
    luecken: (r.querySelector('.q').textContent.match(/___/g) || []).length, sichtbar: !!r.offsetParent,
    test: !!r.querySelector('.selfchk'), sec: r.closest('.lsec') ? r.closest('.lsec').id : '' }));
  const wo = `${d.sec} Übung ${k + 1} (${d.art}) „${d.q}“`;
  if (!d.sichtbar) { await befund('Übung nicht sichtbar', wo); return; }
  z[d.art]++;
  if (d.art === 'typed') {
    const inp = await row.$('.exin');
    let text = d.sol.replace(/\(.*?\)/g, ' ').replace(/\s+/g, ' ').trim();
    if (d.luecken <= 1) text = text.split(/ \/ |·| oder /)[0].trim();
    const ohne = ohneAkzent(text);
    const einfach = !/ \/ |·| oder /.test(d.sol);
    const kandidat = einfach && ohne !== text;
    if (kandidat) z.akzentKandidaten = (z.akzentKandidaten || 0) + 1;
    const akzentlos = kandidat && z.akzentKandidaten % 3 === 1;   // wie am Handy oft: ohne Akzent → Meldung unten
    const erstFalsch = z.typed % 9 === 4;
    await tippe(inp, wo + ' Feld');
    if (erstFalsch) {
      z.falschZuerst++;
      await page.keyboard.type('xyz');
      await tippe(await row.$('button.reveal.pruef'), wo + ' Prüfen (falsch)');
      await sleep(60);
      await tippe(inp, wo + ' Feld');
      for (let i = 0; i < 3; i++) await page.keyboard.press('Backspace');
    }
    if (akzentlos) z.ohneAkzent++;
    await page.keyboard.type(akzentlos ? ohne : text);
    if (z.typed % 4 === 1) { z.perEnter++; await page.keyboard.press('Enter'); }
    else await tippe(await row.$('button.reveal.pruef'), wo + ' Prüfen');
    await sleep(60);
    if (!(await row.evaluate(r => r.classList.contains('exok')))) await befund('nicht gelöst', wo, 'getippt: ' + (akzentlos ? ohne : text));
  } else if (d.art === 'opts') {
    const chip = await row.evaluateHandle(r => {
      const n = t => t.toLowerCase().replace(/[.!?,;:«»"]/g, '').replace(/\s+/g, ' ').trim();
      const soll = n(r.querySelector('.asol').textContent);
      return [...r.querySelectorAll('.wchip')].find(b => n(b.textContent) === soll) || null;
    });
    if (!chip.asElement()) { await befund('Auswahl: keine passende Antwort', wo, d.sol); return; }
    await tippe(chip.asElement(), wo + ' Antwort');
    if (!(await row.evaluate(r => r.classList.contains('exok')))) await befund('nicht gelöst', wo, d.sol);
  } else if (d.art === 'satz') {
    for (const w of d.satz.split(/\s+/).filter(Boolean)) {
      const chip = await row.evaluateHandle((r, w) => [...r.querySelectorAll('[data-pool] .wchip')].find(b => b.textContent === w) || null, w);
      if (!chip.asElement()) { await befund('Satzbau: Wort fehlt im Vorrat', wo, w); break; }
      await tippe(chip.asElement(), wo + ' Wort „' + w + '“');
    }
    await tippe(await row.$('button.reveal.pruef'), wo + ' Prüfen');
    if (!(await row.evaluate(r => r.classList.contains('exok')))) await befund('nicht gelöst', wo, d.satz);
  } else {
    await tippe(await row.$('button.reveal'), wo + ' Lösung');
    if (!(await row.evaluate(r => r.classList.contains('open')))) await befund('Lösung geht nicht auf', wo);
    if (d.test && z.reveal % 2 === 0) { z.selbst++; await tippe(await row.$('.selfchk'), wo + ' Hatte ich richtig'); }
  }
}

async function lektionDurchspielen() {
  for (const b of await page.$$('#l-body button.reveal'))
    if ((await b.evaluate(x => x.textContent.trim())) === 'Text anzeigen') await tippe(b, 'Text anzeigen');
  for (const [sel, name] of [['#l-body .vrow .playbtn', 'Vokabel-Audio'], ['#l-body .dline .dpt', 'Dialogzeile'], ['#l-body .lsec > .playbtn', 'Geschichten-Audio']]) {
    const h = await page.$(sel);
    if (h) { z.audio++; await tippe(h, name); await sleep(120); }
  }
  const rows = await page.$$('#l-body .exitem');
  for (let k = 0; k < rows.length; k++) await uebung(rows[k], k);
  for (const chips of await page.$$('#l-body .ptchips')) {
    const alle = await chips.$$('.ptchip');
    if (alle.length) await tippe(alle[alle.length - 1], 'Punkte selbst vergeben');
  }
}

async function abschliessen(L, naechste) {
  // Wie ein Mensch: ganz nach unten wischen und den Knopf dort antippen, wo er dann steht
  await page.evaluate(() => window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' }));
  await sleep(150);
  const knopf = await page.$('#lesson > .mixbtn');
  const frei = await tippe(knopf, 'Stunde abschließen', false);
  const da = await warte(() => { const a = document.getElementById('abschluss'); return a && a.style.display !== 'none'; }, 2500);
  if (!da) {
    await befund('Stunde abschließen ohne Wirkung', 'Stunde abschließen', frei ? 'Knopf frei, trotzdem kein Abschluss' : 'Knopf verdeckt');
    return false;
  }
  const s = await page.evaluate(id => ({ gespeichert: store.lessons[id] || null, titel: (document.querySelector('#abschluss h2') || {}).textContent || '',
    test: store.tests[id] || null }), L.id);
  if (!s.gespeichert) await befund('Stunde nicht gespeichert', 'Abschluss', JSON.stringify(s));
  if (!/geschafft/.test(s.titel)) await befund('Abschluss-Titel falsch', 'Abschluss', s.titel);
  z.abgeschlossen++;
  return true;
}

async function zurKursliste(id) {
  await tippeText('#abschluss button', 'Zum Kurs', 'Abschluss: Zum Kurs');
  if (!(await warte(() => document.getElementById('kurs').style.display === 'block', 2500))) { await befund('Zum Kurs geht nicht', 'Abschluss'); return false; }
  if (!id) return true;
  const zu = await page.evaluate(id => { const t = document.getElementById('lek-' + id); return !t || !t.offsetParent; }, id);
  if (zu) {
    const kopf = await page.evaluateHandle(id => { const t = document.getElementById('lek-' + id); const body = t && t.closest('.woche-body'); return body ? body.previousElementSibling : null; }, id);
    await tippe(kopf.asElement(), 'Woche aufklappen');
    await sleep(150);
  }
  await tippe(await page.$('#lek-' + id), 'Kursliste: Lektion antippen');
  return true;
}

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--no-first-run', '--autoplay-policy=no-user-gesture-required', '--mute-audio'] });
  page = await browser.newPage();
  await page.emulate({ viewport: { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1' });
  if (process.env.GEGENPROBE) await page.evaluateOnNewDocument(() => document.addEventListener('DOMContentLoaded', () => {
    const s = document.createElement('style'); s.textContent = '#toast { pointer-events: auto !important; }'; document.head.appendChild(s); }));
  const cdp = await page.createCDPSession();
  let safeArea;
  try { await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 47, bottom: 34, left: 0, right: 0 } }); safeArea = 'iPhone-Ränder nachgestellt (oben 47, unten 34 px)'; }
  catch (e) { safeArea = 'iPhone-Ränder nicht nachstellbar: ' + e.message.slice(0, 80); }
  console.log('Gerät: 390×844, Touch, iPhone-Kennung;', safeArea);
  const audio = [];
  page.on('domcontentloaded', () => {      // nur echtes Neuladen, nicht Wechsel der Ansicht
    if (!bereit) return;
    navigiert = true;
    befund('Seite neu geladen', letzterTipp, page.url().replace(BASE, '/'), false);
  });
  page.on('pageerror', e => befund('JS-Fehler', '', e.message.slice(0, 300), false));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource|supabase/i.test(m.text())) befund('Konsolenfehler', '', m.text().slice(0, 300), false); });
  page.on('response', r => {
    const u = r.url(); if (!u.startsWith(BASE)) return;
    if (u.includes('/audio/')) audio.push({ u: decodeURIComponent(u.replace(BASE, '')), s: r.status() });
    if (r.status() >= 400) befund('HTTP ' + r.status(), '', decodeURIComponent(u.replace(BASE, '')), false);
  });
  page.on('requestfailed', r => {
    const u = r.url(), f = (r.failure() || {}).errorText || '';
    if (u.startsWith(BASE) && !/ERR_ABORTED/.test(f)) befund('Anfrage fehlgeschlagen', '', decodeURIComponent(u.replace(BASE, '')) + ' ' + f, false);
  });

  await page.goto(BASE, { waitUntil: 'networkidle2' });
  await page.evaluate(() => { store.premium = { seit: '2026-11-06', art: 'code' }; saveStill(); });   // nur im Test-Browser
  await page.goto(BASE, { waitUntil: 'networkidle2' });
  const offen = await page.evaluate(() => [...document.querySelectorAll('body > div')].filter(d => {
    const c = getComputedStyle(d); return c.position === 'fixed' && c.display !== 'none' && +c.zIndex >= 50; }).map(d => d.id || d.className));
  if (offen.length) console.log('Nach dem Start offen:', offen);

  const alle = await page.evaluate(() => LESSONS.map(l => ({ id: l.id, label: l.label, bonus: !!l.bonus })));
  let liste = NUR.length ? alle.filter(l => NUR.includes(l.id)) : AB ? alle.slice(alle.findIndex(l => l.id === AB)) : alle;
  if (process.env.BIS) liste = liste.slice(0, liste.findIndex(l => l.id === process.env.BIS) + 1);   // nur bis zu dieser Lektion, ohne Texte/Tabs
  if (process.env.NUR_TEXTE) liste = [];   // nur Lesetexte, Tabs und Wiederholung
  console.log(liste.length, 'Lektionen');
  let offenUeber = null;   // wie die nächste Lektion schon geöffnet wurde
  bereit = true;
  for (let i = 0; i < liste.length; i++) {
    const L = liste[i], naechste = liste[i + 1];
    aktuell = L.id; z.lektionen++;
    if (!offenUeber) await page.evaluate(id => openLesson(id), L.id);
    offenUeber = null;
    if (!(await warte(id => curLesson === id && document.getElementById('lesson').style.display === 'block'
        && document.querySelectorAll('#l-body .lsec').length > 0, 8000, L.id))) {
      await befund('Lektion öffnet nicht', 'öffnen', await page.evaluate(() => curLesson));
      continue;
    }
    await sleep(150);
    console.log('Lektion', L.id);
    navigiert = false;
    let ok = false;
    try { await lektionDurchspielen(); ok = await abschliessen(L, naechste); }
    catch (e) {
      await befund('Lektion abgebrochen', letzterTipp, (navigiert ? 'nach Neuladen: ' : '') + e.message.slice(0, 160));
      await page.waitForFunction(() => typeof openLesson === 'function', { timeout: 15000 }).catch(() => {});
      await sleep(500);
    }
    if (ok && naechste && !NUR.length) {
      if ((i + 1) % 10 === 0) { if (await zurKursliste(naechste.id)) offenUeber = 'kurs'; }
      else {
        const t = await page.evaluate(() => [...document.querySelectorAll('#abschluss button')].map(b => b.textContent.trim()).find(t => /jetzt starten/.test(t)));
        if (t && await tippeText('#abschluss button', t, 'Abschluss: ' + t)) offenUeber = 'sheet';
        else await befund('Weiter-Knopf fehlt', 'Abschluss', t || '');
      }
    } else if (ok) await page.evaluate(() => schliesseAbschluss());
    if (i % 10 === 9 || i === liste.length - 1) console.log(`  ${i + 1}/${liste.length} Lektionen, ${z.tipps} Tipps, ${befunde.length} Befunde`);
  }

  if (!NUR.length && !process.env.BIS) {
    // Lesetexte: drei Wörter antippen, Wort-Fenster und Aussprache prüfen
    aktuell = 'Texte';
    const texte = await page.evaluate(() => TEXTOS.map(t => t.tag));
    for (const tag of texte) {
      aktuell = 'Text ' + tag; z.texte++;
      await page.evaluate(tag => openTexto(tag), tag);
      if (!(await warte(() => document.getElementById('leitura').style.display === 'block' && document.querySelectorAll('#lt-text .wtok').length > 0, 6000))) {
        await befund('Text öffnet nicht', tag); continue;
      }
      const toks = await page.$$('#lt-text .wtok');
      for (const t of [toks[0], toks[Math.floor(toks.length / 2)], toks[toks.length - 1]]) {
        if (!t) continue;
        z.worte++;
        await tippe(t, 'Wort antippen');
        if (!(await warte(() => getComputedStyle(document.getElementById('wpop')).display !== 'none', 1500))) await befund('Wort-Fenster kommt nicht', 'Wort', await t.evaluate(x => x.textContent));
      }
      // Lässt sich das Wort-Fenster schließen, ohne das Wort zu markieren? (Tipp auf den Titel)
      if (tag === texte[0]) {
        await tippe(await page.$('#lt-title'), 'Tipp neben das Wort-Fenster');
        const nochOffen = await page.evaluate(() => getComputedStyle(document.getElementById('wpop')).display !== 'none');
        if (nochOffen) await befund('Wort-Fenster schließt nicht', 'Tipp daneben', 'nur über „Lernen“/„Kenne ich“ oder Wechsel der Ansicht');
      }
      await page.evaluate(() => hideWpop());
    }
    // Tab-Leiste
    aktuell = 'Tabs';
    await page.evaluate(() => goTab('home')); await sleep(300);
    for (const name of ['Kurs', 'Texte', 'Heft', 'Mehr', 'Heute']) {
      await tippeText('#tabbar button', name, 'Tab ' + name);
      await sleep(250);
    }
    // Wiederholungsrunde: zwölf Wörter heute fällig machen, zehn Karten mit „Kann ich“
    aktuell = 'Wiederholung';
    await page.evaluate(() => { const t = today(); Object.keys(store.words).slice(0, 12).forEach(id => { store.words[id].due = t; }); saveStill(); goTab('home'); });
    await sleep(400);
    const start = await page.evaluateHandle(() => [...document.querySelectorAll('#home button, #home [role=button]')].find(b => /Wörter|Runde|Wiederhol|Lernen/.test(b.textContent)) || null);
    if (start.asElement()) {
      await tippe(start.asElement(), 'Heute: Runde starten');
      if (await warte(() => document.getElementById('learn').style.display === 'block', 3000)) {
        for (let n = 0; n < 10; n++) {
          if (await page.evaluate(() => document.getElementById('learn').style.display !== 'block')) break;
          const ex = await page.evaluate(() => document.getElementById('excard').style.display !== 'none');
          if (ex) { const w = await page.$('#excard .reveal'); if (w) await tippe(w, 'Übungskarte'); const weiter = await page.evaluateHandle(() => [...document.querySelectorAll('#excard button')].find(b => /Weiter/.test(b.textContent)) || null); if (weiter.asElement()) await tippe(weiter.asElement(), 'Weiter'); continue; }
          await tippe(await page.$('#card'), 'Karte umdrehen');
          await tippe(await page.$('#learnactions .good'), 'Kann ich');
          await sleep(120);
        }
      } else await befund('Runde startet nicht', 'Heute');
    } else await befund('Start-Knopf für Runde nicht gefunden', 'Heute', '', false);
  }

  const kaputt = audio.filter(a => a.s >= 400);
  const ergebnis = { datum: new Date().toISOString(), geraet: '390×844 Touch, ' + safeArea, zaehler: z, audioAnfragen: audio.length, audioFehler: kaputt, befunde };
  fs.writeFileSync(path.join(OUT, 'befunde.json'), JSON.stringify(ergebnis, null, 1));
  console.log('FERTIG', JSON.stringify(z));
  console.log('Audio-Anfragen:', audio.length, 'davon fehlerhaft:', kaputt.length);
  const arten = {}; befunde.forEach(b => { arten[b.art] = (arten[b.art] || 0) + 1; });
  console.log('Befunde nach Art:', JSON.stringify(arten));
  await browser.close();
})().catch(e => { console.error('ABBRUCH', e); process.exit(1); });
