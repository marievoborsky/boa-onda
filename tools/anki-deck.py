#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut die Anki-Decks von Boa Onda (.apkg) im App-Look.

  python3 tools/anki-deck.py          → anki/boa-onda-woche-1-2.apkg (gratis) und
                                        anki/boa-onda-komplett.apkg (Premium)

Quellen: lektionen/index.json (Vokabeln aller Lektionen), data.js (Grundwortschatz),
LESSONS/WOCHEN aus index.html (Reihenfolge, Titel), audio/*.m4a (Wort-Audios).
Jede Vokabel hat zwei Karten: „Verstehen“ (PT → DE, Audio spielt automatisch) und
„Sagen“ (DE → PT, Antwort tippen). Nach neuen Wochen einfach neu laufen lassen –
die Karten-IDs sind stabil, Lernstand in Anki bleibt erhalten.
Voraussetzung: pip install genanki
"""
import json, os, re, hashlib, html, shutil
import genanki
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
OUT = os.path.join(BASE, 'anki'); os.makedirs(OUT, exist_ok=True)

def nid(name):  # stabile numerische ID aus einem Namen
    return int(hashlib.sha1(name.encode()).hexdigest()[:10], 16)

# ---- Lektionen und Wochen aus index.html lesen
src = open(os.path.join(BASE, 'index.html'), encoding='utf-8').read()
m = re.search(r"const WOCHEN = \[(.*?)\];", src, re.S)
WOCHEN = re.findall(r"'([^']+)'", m.group(1))
LESSONS = [{'id': a, 'label': b, 'w': int(c), 'bonus': 'bonus: true' in d}
           for a, b, c, d in re.findall(r"\{ id: '(tag\d\d|sagres)', label: '([^']+)', sub: '[^']*', w: (\d+)(.*?)\}", src)]
IDX = json.load(open(os.path.join(BASE, 'lektionen', 'index.json'), encoding='utf-8'))['lektionen']
djs = open(os.path.join(BASE, 'data.js'), encoding='utf-8').read()
VOCAB = json.loads(djs[djs.index('['):djs.rindex(']') + 1])

def block_name(b):
    t = b.split('-', 1)[-1].replace('-', ' ').replace('woerter', 'wörter').replace('ae', 'ä').replace('oe', 'ö').replace('ue', 'ü')
    return t[:1].upper() + t[1:]

def staffel(w): return 1 if w < 4 else 2 if w < 8 else 3
def woche_name(w): return re.sub(r'^Staffel \d · ', '', WOCHEN[w])

# ---- Logo als PNG fürs Deck
logo_png = os.path.join(OUT, '_boa-onda-logo.png')
Image.open(os.path.join(BASE, 'logo.webp')).convert('RGBA').resize((360, 110), Image.LANCZOS).save(logo_png)

FONTS = ['spacegrotesk-a57c9413.woff2', 'spacegrotesk-e911c2d9.woff2', 'robotomono-af121f2f.woff2', 'robotomono-fe832705.woff2']
FONT_CSS = """
@font-face { font-family: "Space Grotesk"; font-weight: 400 700; src: url("_spacegrotesk-a57c9413.woff2") format("woff2"); unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2212; }
@font-face { font-family: "Space Grotesk"; font-weight: 400 700; src: url("_spacegrotesk-e911c2d9.woff2") format("woff2"); unicode-range: U+0100-02BA, U+1E00-1EFF; }
@font-face { font-family: "Roboto Mono"; font-weight: 300 700; src: url("_robotomono-af121f2f.woff2") format("woff2"); unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2212; }
@font-face { font-family: "Roboto Mono"; font-weight: 300 700; src: url("_robotomono-fe832705.woff2") format("woff2"); unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F; }
"""
CSS = FONT_CSS + """
.card { font-family: "Space Grotesk", "Avenir Next", "Helvetica Neue", Arial, sans-serif; font-size: 22px; line-height: 1.45;
  color: #33294a; background: #f4eee2; text-align: center; padding: 28px 18px; }
.nightMode.card, .night_mode .card { background: #2a2238; color: #f4eee2; }
.logo { width: 150px; margin: 0 auto 18px; display: block; opacity: .95; }
.kicker { font-family: "Roboto Mono", Menlo, monospace; font-size: 12px; letter-spacing: .18em; text-transform: uppercase; color: #6a6180; margin-bottom: 14px; }
.nightMode .kicker, .night_mode .kicker { color: #b9afc9; }
.pt { font-family: "Roboto Mono", Menlo, monospace; font-weight: 300; font-size: 38px; line-height: 1.15; letter-spacing: -.01em; margin: 6px 0 10px; }
.ipa { font-family: "Roboto Mono", Menlo, monospace; font-size: 17px; color: #6a6180; margin-bottom: 6px; }
.nightMode .ipa, .night_mode .ipa { color: #b9afc9; }
.de { font-size: 26px; font-weight: 700; color: #7f6ec2; margin-top: 10px; }
.karte { background: #fffdf6; border-radius: 26px; padding: 26px 22px; margin: 10px auto; max-width: 520px; box-shadow: 0 10px 30px rgba(51,41,74,.12); transform: rotate(-.4deg); }
.nightMode .karte, .night_mode .karte { background: #352c47; box-shadow: none; }
hr#answer { border: none; border-top: 1px dashed #c9bfd9; margin: 18px auto; max-width: 520px; }
.fuss { font-family: "Roboto Mono", Menlo, monospace; font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: #6a6180; margin-top: 22px; }
.nightMode .fuss, .night_mode .fuss { color: #b9afc9; }
.typeGood { background: #cdeae4; color: #0b6c5f; } .typeBad { background: #f3cdb9; color: #8a3a1e; } .typeMissed { background: #e6dff5; color: #4a3d7a; }
input#typeans { font-family: "Roboto Mono", Menlo, monospace; font-size: 22px; border: 1.5px solid #c9bfd9; border-radius: 12px; padding: 10px 14px; background: #fffdf6; color: #33294a; }
"""
KOPF = '<img class="logo" src="_boa-onda-logo.png"><div class="kicker">{{Lição}}</div>'
MODEL = genanki.Model(
    nid('boa-onda-vokabel-v1'), 'Boa Onda · Vokabel',
    fields=[{'name': 'Palavra'}, {'name': 'Significado'}, {'name': 'IPA'}, {'name': 'Áudio'}, {'name': 'Lição'}, {'name': 'Tema'}],
    templates=[
        {'name': 'Verstehen (PT → DE)',
         'qfmt': KOPF + '<div class="karte"><div class="pt">{{Palavra}}</div><div class="ipa">{{IPA}}</div>{{Áudio}}</div><div class="fuss">Was heißt das?</div>',
         'afmt': KOPF + '<div class="karte"><div class="pt">{{Palavra}}</div><div class="ipa">{{IPA}}</div>{{Áudio}}<hr id="answer"><div class="de">{{Significado}}</div></div><div class="fuss">{{Tema}}</div>'},
        {'name': 'Sagen (DE → PT)',
         'qfmt': KOPF + '<div class="karte"><div class="de">{{Significado}}</div><div style="margin-top:16px">{{type:Palavra}}</div></div><div class="fuss">Auf Portugiesisch – wie in Portugal</div>',
         'afmt': KOPF + '<div class="karte"><div class="de">{{Significado}}</div><hr id="answer"><div class="pt">{{Palavra}}</div><div class="ipa">{{IPA}}</div>{{Áudio}}<div style="margin-top:12px">{{type:Palavra}}</div></div><div class="fuss">{{Tema}}</div>'},
    ],
    css=CSS)

def note(pt, de, ipa, audio_id, licao, tema, guid_key, media):
    snd = ''
    if audio_id:
        f = os.path.join(BASE, 'audio', audio_id + '.m4a')
        if os.path.exists(f): media.append(f); snd = f'[sound:{audio_id}.m4a]'
    n = genanki.Note(model=MODEL, fields=[html.escape(pt), html.escape(de), html.escape(ipa or ''), snd, html.escape(licao), html.escape(tema)],
                     guid=genanki.guid_for('boa-onda', guid_key))
    return n

def bauen(name, wochen, datei):
    decks, media = [], []
    root = 'Boa Onda'
    # Grundwortschatz (Kernwörter aus data.js) – gehört zur freien Fassung dazu
    gd = genanki.Deck(nid(name + '::grund'), f'{root}::Grundwortschatz (A1)')
    for w in VOCAB:
        gd.add_note(note(w['pt'], w['de'], w.get('ipa', ''), w['id'], 'Grundwortschatz', block_name(w.get('block', '')), 'kern:' + w['id'], media))
    decks.append(gd)
    for l in LESSONS:
        if l['w'] not in wochen: continue
        vocab = IDX.get(l['id'], {}).get('vocab', [])
        if not vocab: continue
        dname = f"{root}::Staffel {staffel(l['w'])}::{woche_name(l['w'])}::{l['label']}"
        d = genanki.Deck(nid(name + '::' + l['id']), dname)
        for it in vocab:
            d.add_note(note(it['pt'], it['de'], it.get('ipa', ''), it.get('audio'), l['label'], woche_name(l['w']), l['id'] + ':' + (it.get('audio') or it['pt']), media))
        decks.append(d)
    media.append(logo_png)
    for f in FONTS:
        dst = os.path.join(OUT, '_' + f)
        if not os.path.exists(dst): shutil.copy(os.path.join(BASE, 'fonts', f), dst)
        media.append(dst)
    pkg = genanki.Package(decks); pkg.media_files = sorted(set(media))
    pkg.write_to_file(os.path.join(OUT, datei))
    n = sum(len(d.notes) for d in decks)
    print(f'{datei}: {len(decks)} Decks, {n} Vokabeln, {os.path.getsize(os.path.join(OUT, datei)) / 1048576:.1f} MB')

bauen('frei', {0, 1}, 'boa-onda-woche-1-2.apkg')
bauen('komplett', set(range(len(WOCHEN))), 'boa-onda-komplett.apkg')
os.remove(logo_png)
for f in FONTS: os.remove(os.path.join(OUT, '_' + f))
