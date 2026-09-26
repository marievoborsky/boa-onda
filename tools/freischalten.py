#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schaltet vorbereitete Wochen frei: trägt LESSONS/TEXTOS-Einträge in index.html ein,
erhöht den Precache im sw.js und erzeugt die Arbeitsblätter.

Voraussetzung: die Lektions-JSONs liegen in lektionen/ UND die Audios existieren
(vorher `python3 tools/tts-eleven.py` und `python3 tools/tts-tok-google.py`).

  python3 tools/freischalten.py 7      # Woche 7 (tag43–49)
  python3 tools/freischalten.py 8      # Woche 8 (tag50–56)
  python3 tools/freischalten.py 7 8    # beide
  python3 tools/freischalten.py 9      # Staffel 3, Woche 9 (tag57–63)
"""
import json, os, re, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
WOCHEN = {
    7: {'w': 6, 'tage': range(43, 50), 'labels': {
        43: ('A carrinha', 'Abfahrt · comigo, contigo'),
        44: ('O Alentejo', 'Superlativ · o mais …, -íssimo'),
        45: ('Avaria', 'Panne · pude, consegui, tive de'),
        46: ('Na oficina', 'se-Passiv · Zahlen bis 1000'),
        47: ('À volta da fogueira', 'Erzählen · primeiro, depois, no fim'),
        48: ('Espero que cheguem bem', 'Konjunktiv · Hörverstehen'),
        49: ('Revisão VI', 'Wochentest · 50 Punkte')},
        'textos': {43: 'Quilómetro zero', 44: 'A estrada mais bonita', 45: 'Quarenta graus', 46: 'Uma noite em Odemira',
                   47: 'A lenda da praia', 48: 'A última etapa', 49: 'Seis da manhã'}},
    8: {'w': 7, 'tage': range(50, 57), 'labels': {
        50: ('A primeira aula', 'Imperativ · du, Sie, ihr'),
        51: ('Clientes do mundo inteiro', 'Nationalitäten · Siezen'),
        52: ('Socorro!', 'Erste Hilfe · Plusquamperfekt'),
        53: ('A competição do Tomás', 'se fizer, quando chegares'),
        54: ('A história do Vasco', 'Alle Zeiten · Hörverstehen'),
        55: ('A decisão', 'Zeiten-Übersicht · Angebote'),
        56: ('Exame final A2', 'Abschlusstest · 60 Punkte')},
        'textos': {50: 'Vinte vezes', 51: 'Obrigado, cerveja, bom dia', 52: 'O penso', 53: 'A onda do Tomás',
                   54: 'O domingo à noite', 55: 'A resposta da Marie', 56: 'Junho'}},
    9: {'w': 8, 'tage': range(57, 64), 'labels': {
        57: ('O sofá do João', 'tenho dormido · perfeito composto'),
        58: ('Senha B 247', 'é preciso que · Konjunktiv'),
        59: ('A padaria às quatro', 'infinitivo pessoal'),
        60: ('Primeiro dia de aulas', 'quero que · não acho que'),
        61: ('Há greve', 'se houver, quando chegares'),
        62: ('Saudades de Sagres', 'embora, para que · Hörverstehen'),
        63: ('Revisão VII', 'Wochentest · 50 Punkte')},
        'textos': {57: 'O quarto andar', 58: 'Falta um papel', 59: 'O pão não espera', 60: 'A professora Teresa',
                   61: 'Sete colinas', 62: 'Chuva em Lisboa', 63: 'O primeiro ordenado'}},
}

def audio_fehlt(tage):
    fehlt = []
    for n in tage:
        L = json.load(open(os.path.join(BASE, 'lektionen', f'tag{n:02d}.json'), encoding='utf-8'))
        for s in L['sections']:
            ids = []
            if s['type'] == 'reading': ids = [l['audio'] for l in s['lines'] if l.get('audio')]
            elif s['type'] == 'vocab': ids = [i['audio'] for i in s['items'] if i.get('audio')]
            elif s['type'] == 'story' and s.get('audio'): ids = [s['audio']]
            fehlt += [a for a in ids if not os.path.exists(os.path.join(BASE, 'audio', a + '.m4a'))]
    return fehlt

def main():
    wochen = [int(x) for x in sys.argv[1:]] or sys.exit(__doc__)
    p = os.path.join(BASE, 'index.html'); s = open(p, encoding='utf-8').read()
    for wk in wochen:
        cfg = WOCHEN[wk]
        fehlt = audio_fehlt(cfg['tage'])
        if fehlt: sys.exit(f'Woche {wk}: {len(fehlt)} Audios fehlen (z. B. {fehlt[:5]}) – erst tts-eleven.py laufen lassen.')
        if f"id: 'tag{cfg['tage'][0]:02d}'" in s: print(f'Woche {wk} ist schon registriert.'); continue
        les = ''.join(f"  {{ id: 'tag{n:02d}', label: 'Tag {n} · {cfg['labels'][n][0]}', sub: '{cfg['labels'][n][1]}', w: {cfg['w']} }},\n" for n in cfg['tage'])
        tex = ''.join(f"  {{ tag: 'tag{n:02d}', num: {n}, title: '{cfg['textos'][n]}', nivel: 5, story: true }},\n" for n in cfg['tage'])
        prev = cfg['tage'][0] - 1
        m = re.search(rf"  \{{ id: 'tag{prev:02d}'.*?\}},\n", s); assert m, 'LESSONS-Anker fehlt'
        s = s[:m.end()] + les + s[m.end():]
        m = re.search(rf"  \{{ tag: 'tag{prev:02d}'.*?\}},\n", s); assert m, 'TEXTOS-Anker fehlt'
        s = s[:m.end()] + tex + s[m.end():]
        print(f'Woche {wk} registriert (tag{cfg["tage"][0]:02d}–tag{cfg["tage"][-1]:02d}).')
    open(p, 'w', encoding='utf-8').write(s)
    # Service Worker: Precache-Länge + Version
    sw = os.path.join(BASE, 'sw.js'); w = open(sw, encoding='utf-8').read()
    maxtag = max(WOCHEN[wk]['tage'][-1] for wk in wochen)
    w = re.sub(r"Array\.from\(\{ length: \d+ \}", f"Array.from({{ length: {maxtag} }}", w)
    w = re.sub(r"boa-onda-shell-v(\d+)", lambda m: f"boa-onda-shell-v{int(m.group(1)) + 1}", w)
    open(sw, 'w', encoding='utf-8').write(w)
    subprocess.run([sys.executable, os.path.join(BASE, '..', 'arbeitsblaetter', 'generieren.py')], check=True)
    print('sw.js gebumpt, Arbeitsblätter erzeugt. Jetzt: Smoke-Test, commit, push.')

if __name__ == '__main__':
    main()
