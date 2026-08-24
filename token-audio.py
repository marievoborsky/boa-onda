#!/usr/bin/env python3
"""Erzeugt Einzelwort-Audio für die antippbaren Textos-Wörter.
Quelle: dieselben Lektions-Texte, die die App in den Textos zeigt.
Ausgabe: app/audio/tok/<wort>.m4a (Stimme: macOS Joana pt_PT).
Nach neuen Texten einfach neu ausführen – vorhandene Dateien werden übersprungen."""
import json, os, re, subprocess, tempfile, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
TOK = os.path.join(BASE, 'audio', 'tok')
os.makedirs(TOK, exist_ok=True)

TEXTOS = [
 ('tag01', 'Olá, bom dia!', False), ('tag02', 'Este é o João', False),
 ('tag03', 'Uma amiga em Lisboa', True), ('tag04', 'É segredo!', True),
 ('tag05', 'Vinte perguntas', True), ('tag06', 'A irmã do João', True),
 ('tag07', 'Domingo em Lisboa', True),
]

def tokens_of(text):
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    out = set()
    for tok in text.split():
        core = re.sub(r'^[^\w]+|[^\w]+$', '', tok, flags=re.UNICODE)
        if core and re.search(r'\w', core, re.UNICODE):
            out.add(core.lower())
    return out

words = set()
for tag, title, story in TEXTOS:
    L = json.load(open(os.path.join(BASE, 'lektionen', tag + '.json')))
    sec = next((s for s in L['sections'] if s['type'] == 'story' and title in s['title']), None)
    if sec:
        words |= tokens_of(sec['text'])
    else:
        r = next(s for s in L['sections'] if s['type'] == 'reading')
        for ln in r['lines']:
            words |= tokens_of(ln['pt'])

made = skipped = 0
for w in sorted(words):
    dest = os.path.join(TOK, w + '.m4a')
    if os.path.exists(dest):
        skipped += 1
        continue
    with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as tf:
        aiff = tf.name
    subprocess.run(['say', '-v', 'Joana', '-o', aiff, w], check=True)
    subprocess.run(['afconvert', aiff, dest, '-f', 'm4af', '-d', 'aac', '-b', '48000'],
                   check=True, capture_output=True)
    os.unlink(aiff)
    made += 1
print(f'{made} neu, {skipped} übersprungen, gesamt {len(words)} Wörter')
