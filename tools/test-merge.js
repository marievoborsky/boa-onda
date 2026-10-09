// Aufruf: node app/tools/test-merge.js (Node, ohne Browser)
// Unit-Tests für mergeZustand/streakAusTagen – Code wird aus index.html (SYNC-MERGE-Marker) gezogen
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync('/Users/marievoborsky/KI/BOAONDA/app/index.html', 'utf8');
const m = html.match(/\/\* SYNC-MERGE-START[\s\S]*?\*\/([\s\S]*?)\/\* SYNC-MERGE-END \*\//);
assert(m, 'Marker nicht gefunden');
const ZIEL_KARTEN = 10;
function today(d) { const x = d || new Date(); return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`; }
const { mergeZustand, streakAusTagen } = new Function('ZIEL_KARTEN', 'today', m[1] + '; return { mergeZustand, streakAusTagen };')(ZIEL_KARTEN, today);

const T = today(), G = today(new Date(Date.now() - 864e5)), VG = today(new Date(Date.now() - 2 * 864e5));
let n = 0;
function test(name, fn) { try { fn(); n++; console.log('ok   ', name); } catch (e) { console.log('FEHL ', name, '\n     ', e.message); process.exitCode = 1; } }

const A = { // Gerät A: Tag 1–3
  lessons: { tag01: '2026-10-01', tag02: '2026-10-02', tag03: '2026-10-03' },
  words: { w1: { box: 1, due: '2026-10-05' }, w2: { box: 2, due: '2026-10-06' }, w3: { box: 0, due: '2026-10-04', neu: true }, w9: { box: 3, due: '2026-10-20' } },
  uebungen: { 'tag01:3:0': { lid: 'tag01', sec: 3, i: 0, fehl: 1, box: 1, due: '2026-10-05' } },
  tests: { tag07: { punkte: 30, max: 44, datum: '2026-10-07' } },
  tage: { '2026-10-01': { karten: 5, richtig: 4, lektionen: 1 }, [G]: { karten: 12, richtig: 10 } },
  streak: { last: G, count: 2 },
  fehler: { w1: { n: 2, last: '2026-10-02' } },
  sprechen: { tag02: 'nochmal' },
};
const B = { // Gerät B: Tag 2–5, höhere Boxen
  lessons: { tag02: '2026-10-01', tag03: '2026-10-05', tag04: '2026-10-06', tag05: '2026-10-07' },
  words: { w1: { box: 3, due: '2026-10-15' }, w2: { box: 2, due: '2026-10-09' }, w3: { box: 0, due: '2026-10-03', neu: true }, w4: { box: 1, due: '2026-10-08', neu: true } },
  uebungen: { 'tag01:3:0': { lid: 'tag01', sec: 3, i: 0, fehl: 3, box: 3, due: '2026-10-20', gelernt: '2026-10-06' }, 'tag04:2:1': { lid: 'tag04', sec: 2, i: 1, fehl: 0, box: 0, due: '2026-10-07' } },
  tests: { tag07: { punkte: 38, max: 44, datum: '2026-10-08' } },
  tage: { '2026-10-01': { karten: 2, richtig: 2, geloest: 3 }, [T]: { karten: 3, richtig: 3, lektionen: 1 } },
  streak: { last: T, count: 1 },
  fehler: { w1: { n: 1, last: '2026-10-07' }, w4: { n: 1, last: '2026-10-07' } },
  sprechen: { tag02: 'gut' },
};

test('Vereinigung Gerät A (Tag 1–3) + Gerät B (Tag 2–5)', () => {
  const r = mergeZustand(A, B, true);
  assert.deepStrictEqual(Object.keys(r.lessons).sort(), ['tag01', 'tag02', 'tag03', 'tag04', 'tag05']);
  assert.strictEqual(r.lessons.tag02, '2026-10-01', 'frühestes Datum');
  assert.strictEqual(r.lessons.tag03, '2026-10-03');
  assert.deepStrictEqual(r.words.w1, { box: 3, due: '2026-10-15' }, 'höhere Box gewinnt');
  assert.deepStrictEqual(r.words.w2, { box: 2, due: '2026-10-09' }, 'Gleichstand: späteres due');
  assert.strictEqual(r.words.w3.neu, true, 'neu nur wenn beide neu');
  assert.strictEqual(r.words.w3.due, '2026-10-04');
  assert.deepStrictEqual(r.words.w4, { box: 1, due: '2026-10-08', neu: true }, 'nur remote: übernommen');
  assert.deepStrictEqual(r.words.w9, { box: 3, due: '2026-10-20' }, 'nur lokal: übernommen');
  const u = r.uebungen['tag01:3:0'];
  assert.strictEqual(u.box, 3); assert.strictEqual(u.fehl, 3); assert.strictEqual(u.gelernt, '2026-10-06');
  assert.ok(r.uebungen['tag04:2:1']);
  assert.strictEqual(r.tests.tag07.punkte, 38, 'höhere Punkte');
  assert.deepStrictEqual(r.tage['2026-10-01'], { karten: 5, richtig: 4, lektionen: 1, geloest: 3 }, 'Tage: Max je Feld');
  assert.deepStrictEqual(r.tage[T], { karten: 3, richtig: 3, lektionen: 1 });
  assert.deepStrictEqual(r.fehler.w1, { n: 2, last: '2026-10-07' });
  assert.strictEqual(r.sprechen.tag02, 'gut', 'remote neuer → remote');
  assert.strictEqual(mergeZustand(A, B, false).sprechen.tag02, 'nochmal', 'lokal neuer → lokal');
  // Streak: gestern 12 Karten (A) + heute Lektion (B) → Kette 2, endet heute
  assert.deepStrictEqual(r.streak, { last: T, count: 2 });
});
test('neu-Flag verschwindet, wenn eine Seite das Wort schon geübt hat', () => {
  const r = mergeZustand({ words: { x: { box: 0, due: '2026-10-01', neu: true } } }, { words: { x: { box: 1, due: '2026-10-02' } } });
  assert.deepStrictEqual(r.words.x, { box: 1, due: '2026-10-02' });
  const r2 = mergeZustand({ words: { x: { box: 1, due: '2026-10-03' } } }, { words: { x: { box: 1, due: '2026-10-02', neu: true } } });
  assert.deepStrictEqual(r2.words.x, { box: 1, due: '2026-10-03' });
});
test('leerer Remote → lokal unverändert', () => {
  const r = mergeZustand(A, {}, false);
  assert.deepStrictEqual(r.lessons, A.lessons); assert.deepStrictEqual(r.words, A.words); assert.deepStrictEqual(r.uebungen, A.uebungen);
  assert.deepStrictEqual(r.tests, A.tests); assert.deepStrictEqual(r.tage, A.tage); assert.deepStrictEqual(r.fehler, A.fehler);
  assert.deepStrictEqual(r.sprechen, A.sprechen);
  assert.deepStrictEqual(r.streak, { last: G, count: 2 }, 'Streak bleibt (gespeichert ≥ berechnet)');
  assert.deepStrictEqual(mergeZustand(A, null, false).lessons, A.lessons);
  assert.deepStrictEqual(mergeZustand(A, undefined, false).words, A.words);
});
test('leerer Lokal → remote übernommen', () => {
  const leer = { words: {}, lessons: {}, streak: { last: '', count: 0 }, fehler: {}, tage: {}, uebungen: {}, tests: {}, sprechen: {} };
  const r = mergeZustand(leer, B, true);
  assert.deepStrictEqual(r.lessons, B.lessons); assert.deepStrictEqual(r.words, B.words); assert.deepStrictEqual(r.uebungen, B.uebungen);
  assert.deepStrictEqual(r.tests, B.tests); assert.deepStrictEqual(r.tage, B.tage); assert.deepStrictEqual(r.fehler, B.fehler);
  assert.deepStrictEqual(r.sprechen, B.sprechen); assert.deepStrictEqual(r.streak, { last: T, count: 1 });
});
test('beide leer', () => {
  const r = mergeZustand({}, {}, false);
  for (const f of ['lessons', 'words', 'uebungen', 'tests', 'tage', 'fehler', 'sprechen']) assert.deepStrictEqual(r[f], {});
  assert.deepStrictEqual(r.streak, { last: '', count: 0 });
});
test('kaputte Remote-Daten (Strings, Arrays, null) kippen den Merge nicht', () => {
  const r = mergeZustand(A, { lessons: 'x', words: [1, 2], uebungen: null, tage: { '2026-10-01': 'x' }, fehler: { w1: null }, streak: 'nein', tests: 5, sprechen: 1 }, true);
  assert.deepStrictEqual(r.lessons, A.lessons); assert.deepStrictEqual(r.words, A.words);
  assert.deepStrictEqual(r.tage['2026-10-01'], { karten: 5, richtig: 4, lektionen: 1 });
  assert.deepStrictEqual(r.fehler.w1, { n: 2, last: '2026-10-02' });
  assert.deepStrictEqual(r.streak, { last: G, count: 2 });
});
test('Merge ist idempotent und monoton (nochmal mergen ändert nichts)', () => {
  const r = mergeZustand(A, B, true), r2 = mergeZustand(r, B, true), r3 = mergeZustand(A, r, true);
  assert.deepStrictEqual(r2, r); assert.deepStrictEqual(r3, r);
});
test('streakAusTagen: Kette endet gestern → zählt; Lücke → 0', () => {
  assert.deepStrictEqual(streakAusTagen({ [G]: { lektionen: 1 }, [VG]: { karten: 10 } }), { last: G, count: 2 });
  assert.deepStrictEqual(streakAusTagen({ [VG]: { lektionen: 1 } }), { last: '', count: 0 });
  assert.deepStrictEqual(streakAusTagen({ [T]: { karten: 9 } }), { last: '', count: 0 }, '9 Karten reichen nicht');
  assert.deepStrictEqual(streakAusTagen({ [T]: { geloest: 1 } }), { last: T, count: 1 }, 'eine gelöste Übung reicht');
  assert.deepStrictEqual(streakAusTagen({}), { last: '', count: 0 });
});
test('Streak: gespeicherter Streak mit gleichem Enddatum und höherem Zähler bleibt', () => {
  const r = mergeZustand({ tage: { [T]: { lektionen: 1 } }, streak: { last: T, count: 9 } }, { streak: { last: VG, count: 30 } }, false);
  assert.deepStrictEqual(r.streak, { last: T, count: 9 });
});
console.log(`\n${n} Tests ok`);
