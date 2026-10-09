#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut lektionen/index.json aus allen lektionen/*.json.

Die App liest beim Start nur noch diese eine Datei (statt 64 Lektionen):
  - Vokabeln jeder Lektion (pt, ipa, de, audio) für Heft, Wiederholung und Reader-Wörterbuch
  - die Grammatik-Dicas (Vasco, João, Professora) für die Grammatik-Karte auf Hoje:
    Abschnitts-Index, Titel und die ersten 300 Zeichen als Klartext
Die vollständige Lektion wird erst beim Öffnen geladen.

Aufruf (aus app/ oder von überall):  python3 tools/vokabel-index.py
Nach jeder Änderung an einer Lektionsdatei neu ausführen – freischalten.py ruft es selbst auf.
"""
import glob, html, json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
LEK = os.path.join(BASE, 'lektionen')
DICA_RE = re.compile(r'Dica d[oa] (Vasco|João|Professora)')
MAX_TEXT = 300

def klartext(h):
    t = re.sub(r'<br\s*/?>', ' ', h or '', flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    return re.sub(r'\s+', ' ', t).strip()

def main():
    out = {}
    for pfad in sorted(glob.glob(os.path.join(LEK, '*.json'))):
        name = os.path.basename(pfad)
        if name == 'index.json':
            continue
        with open(pfad, encoding='utf-8') as f:
            L = json.load(f)
        if not isinstance(L, dict) or 'sections' not in L: continue   # index.json / leseworte.json überspringen
        lid = L.get('id') or name[:-5]
        vocab, dicas = [], []
        for i, sec in enumerate(L.get('sections', [])):
            if sec.get('type') == 'vocab':
                for it in sec.get('items', []):
                    e = {'pt': it.get('pt', ''), 'ipa': it.get('ipa', ''), 'de': it.get('de', '')}
                    if it.get('audio'):
                        e['audio'] = it['audio']
                    vocab.append(e)
            elif sec.get('type') == 'note' and DICA_RE.search(sec.get('title') or ''):
                dicas.append({'i': i, 'title': sec.get('title', ''), 'text': klartext(sec.get('html'))[:MAX_TEXT]})
        out[lid] = {'vocab': vocab, 'dicas': dicas}
    ziel = os.path.join(LEK, 'index.json')
    with open(ziel, 'w', encoding='utf-8') as f:
        json.dump({'v': 1, 'lektionen': out}, f, ensure_ascii=False, separators=(',', ':'))
    n_v = sum(len(x['vocab']) for x in out.values())
    n_d = sum(len(x['dicas']) for x in out.values())
    print(f'lektionen/index.json: {len(out)} Lektionen, {n_v} Vokabeln, {n_d} Dicas, {os.path.getsize(ziel) // 1024} KB')

if __name__ == '__main__':
    main()
