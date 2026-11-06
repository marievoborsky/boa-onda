#!/usr/bin/env python3
"""Vertont alle App-Audios (Dialoge, Vokabeln, Geschichten) mit ElevenLabs. Standard seit 06.11.2026.

Stimmen (stimmen.json): Bibliotheksstimmen von Sprecherinnen und Sprechern aus Portugal, von Marie
am 06.11.2026 per Hörprobe ausgewählt: Marie = Benedita, Ana = Mariza, João = Dinis,
Vasco = „Vasco – Grounded and natural“. Marie ist auch die Erzählstimme (Vokabeln, Geschichten).
Wiederkehrende Nebenfiguren haben eigene Stimmen (Tio Tó = Vicente, Professora Teresa = Daniela,
Avó Carolina = Marta, Martim = Adrião, Tiago = Francisco, Inês = Inês), kleine Rollen teilen sich
Luis (Männer) und Beatriz (Frauen); Zuordnung in WHO2FIG. Es sind KI-Stimmen: nicht als „echte“
oder „eingesprochene“ Stimmen bewerben.

Geschichte: Bis 05.11.2026 liefen hier selbst entworfene ElevenLabs-Stimmen; die sprachen das End-s
oft brasilianisch ([s] statt [ʃ]). Am 05.11. kurz Google pt-PT (tts-google.py, bleibt als Notlösung).
Alte Fassungen liegen in 09_AUDIO-BACKUPS/.

Schutz gegen Brasilianisch und verschluckte s: Endet ein Text auf s oder z, wird das End-s nachgemessen
(zischlaut.bewerte). Klingt es wie [s] oder fehlt es ganz (die KI verschluckt es manchmal; die erste
João-Stimme Rodrigo tat es so oft, dass sie ersetzt wurde), wird die Datei neu erzeugt, bis zu VERSUCHE-mal, abwechselnd mit und ohne
Kontext. Kurze Einträge (Vokabeln) bekommen PREV immer (wird nicht mitgesprochen).
Auffällige Längen (abgeschnitten, Störgeräusche) werden einmal neu erzeugt.
Protokoll jeder Prüfung: <Ausgabeordner>/pruefung.json.

Aufruf (ELEVENLABS_API_KEY steht in ~/.zshrc):
  python3 tts-eleven.py                 # nur Neues und Geändertes (Vergleich über audio/manifest.json)
  python3 tts-eleven.py --alle          # alles neu
  python3 tts-eleven.py --nur d0101 w107
  python3 tts-eleven.py --probe         # ein Dutzend typische Dateien
  python3 tts-eleven.py --nach DIR      # in einen anderen Ordner (erst prüfen, dann übernehmen)
  python3 tts-eleven.py --nachpruefen --versuche 8   # vorhandene Dateien streng nachmessen, schlechte neu
  python3 tts-eleven.py --nur s36 d3110 --saetze      # Satz für Satz erzeugen (gegen verschluckte s mitten im Text)
  python3 tts-eleven.py --tok           # die antippbaren Einzelwörter (audio/tok/, Stimme Benedita,
                                        # Wortliste aus tts-tok-google.py, eigenes tok/manifest.json)
Danach: sw.js – SHELL hochzählen, bei ersetzten Audios auch AUDIO – und pushen.
"""
import json, os, re, sys, glob, subprocess, tempfile, time, random, hashlib, threading, importlib.util, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 01_APP/
OUT = os.path.join(BASE, 'audio')
KEY = os.environ.get('ELEVENLABS_API_KEY')
VOICES = json.load(open(os.path.join(BASE, 'tools', 'stimmen.json')))
MODEL = 'eleven_multilingual_v2'
EINSTELLUNG = {'stability': 0.5, 'similarity_boost': 0.75, 'speed': 0.95}
VERSION = 'eleven-pt-1'   # hochzählen, wenn sich EINSTELLUNG oder MODEL ändern: dann wird alles neu erzeugt
# Sprecher (who, klein geschrieben) → Stimme aus stimmen.json. Unbekannte Sprecher: Marie.
WHO2FIG = {'ana': 'ana', 'marie': 'marie', 'joão': 'joao', 'joao': 'joao', 'vasco': 'vasco',
           'tomás': 'ana', 'tomas': 'ana',   # Tomás (13): Ana-Stimme – Kinderstimmen sind bei ElevenLabs zu Recht gesperrt
           'tio tó': 'tio', 'tio to': 'tio', 'tio': 'tio', 'professora': 'professora', 'avó': 'avo', 'avo': 'avo',
           'martim': 'martim', 'tiago': 'tiago', 'inês': 'ines', 'ines': 'ines',
           # kleine Rollen: eine Männer- und eine Frauenstimme für alle
           'empregado': 'neben_m', 'vendedor': 'neben_m', 'senhor': 'neben_m', 'motorista': 'neben_m', 'pai': 'neben_m',
           'senhorio': 'neben_m', 'operador': 'neben_m', 'mecânico': 'neben_m', 'mecanico': 'neben_m', 'weber': 'neben_m',
           'tio zé': 'neben_m', 'tio ze': 'neben_m',
           'empregada': 'neben_w', 'vendedora': 'neben_w', 'senhora': 'neben_w', 'senhoria': 'neben_w',
           'funcionária': 'neben_w', 'funcionaria': 'neben_w', 'mãe': 'neben_w', 'mae': 'neben_w'}
# Für die Notlösung tts-google.py (hat nur die vier Hauptstimmen): Nebenfiguren dorthin zurückführen
HAUPTSTIMME = {'tio': 'vasco', 'professora': 'ana', 'avo': 'ana', 'martim': 'joao', 'tiago': 'joao', 'ines': 'ana',
               'neben_m': 'vasco', 'neben_w': 'ana'}

# Kontext-Anker, damit kurze Einträge sicher europäisch klingen (wird nicht mitgesprochen).
# Test 05.11.2026, Einzelwörter seis/dois/três: mit diesem Satz 47 von 48 mit „sch“,
# ohne Kontext gut die Hälfte.
PREV = 'Em Lisboa, a professora diz devagar: '
PREV_DIALOG = 'Em Lisboa, um amigo diz: '   # Kontext für Wiederholungen bei Dialogzeilen
GRENZE = 0.5     # Lage des End-s (0 = „sch“, 1 = „s“) ab der neu erzeugt wird
VERSUCHE = 4
PROBE_TOK = ['seis', 'dois', 'três', 'adeus', 'obrigada', 'o', 'de', 'que', 'não', 'pão', 'estás', 'mas', 'à', 'chama-se']
PROBE = ['d0101', 'd0204', 'd0302', 'd0504', 'd1302', 'd1305', 'd1307', 'w107', 'w103', 'v0411', 's03', 'db06']

def collect():
    items = {}
    def add(aid, text, fig='marie', prev=None):
        items[aid] = {'text': text, 'fig': fig, 'prev': prev}
    s = open(os.path.join(BASE, 'data.js')).read()
    for w in json.loads(s[s.index('['):s.rindex(']')+1]):
        add(w['id'], w.get('say') or w['pt'], 'marie', PREV)
    for f in sorted(glob.glob(os.path.join(BASE, 'lektionen', '*.json'))):
        L = json.load(open(f))
        if not isinstance(L, dict) or 'sections' not in L: continue   # index.json, leseworte.json
        for sec in L['sections']:
            if sec['type'] == 'reading':
                for ln in sec['lines']:
                    if ln.get('audio'):
                        add(ln['audio'], ln['pt'], WHO2FIG.get(ln['who'].strip().lower(), 'marie'))
            elif sec['type'] == 'vocab':
                for it in sec['items']:
                    if it.get('audio'):
                        add(it['audio'], it['pt'].replace(' / ', ', '), 'marie', PREV)
            elif sec['type'] == 'story' and sec.get('audio'):
                t = re.sub(r'<br\s*/?>', ' ', sec['text'])
                add(sec['audio'], re.sub(r'<[^>]+>', '', t), 'marie')
    # tok/-Einzelwörter kommen seit 29.08. NICHT mehr von ElevenLabs:
    # die Marie-Stimme spricht EP-Auslaute bei Einzelwörtern unsauber („adeus"
    # ohne End-[ʃ]). Einzelwörter generiert tts-tok-google.py (Google TTS).
    # Tag-8-Sagres aus dem Arbeitsblatt (Marie & Vasco)
    html = open(os.path.join(BASE, '..', '08_ARBEITSBLAETTER', 'sagres-bonus.html')).read()
    lines = re.findall(r'<span class="who">([^<]+):</span>\s*([^<]+)</p>', html)[:12]
    for i, (who, pt) in enumerate(lines, 1):
        add(f'db{i:02d}', pt.strip(), WHO2FIG.get(who.strip().lower(), 'marie'))
    story = re.search(r'Kleine Geschichte: O fim do mundo.*?<div class="dialog">(.*?)</div>', html, re.S).group(1)
    add('sb', re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', story)).strip(), 'marie')
    return items

def tok_items():
    """Antippbare Einzelwörter: Wortliste wie bisher aus tts-tok-google.py, gesprochen von der Erzählstimme."""
    spec = importlib.util.spec_from_file_location('tokliste', os.path.join(BASE, 'tools', 'tts-tok-google.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return {w: {'text': w, 'fig': 'marie', 'prev': PREV} for w in m.tok_woerter()}

def fingerabdruck(item):
    teile = (VERSION, VOICES[item['fig']]['id'], item['text'], item.get('prev') or '')
    return hashlib.sha1('|'.join(teile).encode()).hexdigest()[:16]

class Guthaben(Exception):
    """ElevenLabs-Guthaben aufgebraucht: sauber anhalten, später mit demselben Aufruf weitermachen."""

def anfrage(text, voice_id, prev=None, seed=None):
    body = {'text': text, 'model_id': MODEL, 'voice_settings': EINSTELLUNG}
    if prev: body['previous_text'] = prev
    if seed is not None: body['seed'] = seed
    daten = json.dumps(body).encode()
    for versuch in range(8):
        req = urllib.request.Request(
            f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128',
            data=daten, headers={'xi-api-key': KEY, 'Content-Type': 'application/json'})
        try:
            return urllib.request.urlopen(req, timeout=180).read()
        except urllib.error.HTTPError as e:
            txt = e.read().decode(errors='replace')[:400]
            if 'quota' in txt.lower(): raise Guthaben(txt)
            if e.code in (409, 429, 500, 502, 503, 504) and versuch < 7:
                time.sleep(4 + 6 * versuch); continue
            raise RuntimeError(f'HTTP {e.code}: {txt}')
        except Exception:
            if versuch == 7: raise
            time.sleep(4 + 6 * versuch)

def nach_m4a(mp3, dest):
    """mp3 von ElevenLabs als m4a speichern – oder verlustfrei als WAV, wenn dest auf .wav endet
    (Zwischenstufe im Satz-für-Satz-Modus, damit nicht zweimal komprimiert wird)."""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tf:
        tf.write(mp3); tmp = tf.name
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if dest.endswith('.wav'):
        subprocess.run(['afconvert', tmp, dest, '-f', 'WAVE', '-d', 'LEI16@44100', '-c', '1'], check=True, capture_output=True)
    else:
        subprocess.run(['afconvert', tmp, dest, '-f', 'm4af', '-d', 'aac', '-b', '48000'], check=True, capture_output=True)
    os.unlink(tmp)

def saetze(text):
    # Satzende auch vor schließendem Anführungszeichen („… prévio.» Aqui …“, Fix 06.11.2026)
    return [t for t in re.split(r'(?<=[.!?…][»”")])\s+|(?<=[.!?…])\s+', text.strip()) if t and re.search(r'\w', t)]

def _wav_lesen(pfad):
    import numpy as np
    b = open(pfad, 'rb').read(); k = b.index(b'data'); n = int.from_bytes(b[k + 4:k + 8], 'little')
    return np.frombuffer(b[k + 8:k + 8 + n - n % 2], dtype='<i2')

def _trimmen(a, sr=44100):
    """Stille am Anfang und Ende kürzen – großzügig, damit ein leises End-s nicht abgeschnitten wird."""
    import numpy as np
    fr = sr // 100; x = a.astype(float)
    e = np.array([(x[i:i + fr] ** 2).mean() for i in range(0, max(1, len(x) - fr), fr)])
    if not len(e) or e.max() <= 0: return a
    laut = np.where(e > e.max() * 1e-6)[0]          # −60 dB
    return a[max(0, (laut[0] - 6) * fr):min(len(a), (laut[-1] + 10) * fr)]

def zusammenfuegen(wavs, dest, pause=0.35, sr=44100):
    import numpy as np
    stille = np.zeros(int(sr * pause), dtype='<i2')
    teile = []
    for i, p in enumerate(wavs):
        if i: teile.append(stille)
        teile.append(_trimmen(_wav_lesen(p), sr))
    pcm = np.concatenate(teile).astype('<i2').tobytes(); n = len(pcm)
    kopf = (b'RIFF' + (36 + n).to_bytes(4, 'little') + b'WAVEfmt ' + (16).to_bytes(4, 'little') + (1).to_bytes(2, 'little')
            + (1).to_bytes(2, 'little') + sr.to_bytes(4, 'little') + (sr * 2).to_bytes(4, 'little') + (2).to_bytes(2, 'little')
            + (16).to_bytes(2, 'little') + b'data' + n.to_bytes(4, 'little'))
    tmp = dest + '.gesamt.wav'; open(tmp, 'wb').write(kopf + pcm)
    subprocess.run(['afconvert', tmp, dest, '-f', 'm4af', '-d', 'aac', '-b', '48000'], check=True, capture_output=True)
    os.unlink(tmp)

def erzeuge_saetze(item, dest, versuche_max=None):
    """Satz für Satz erzeugen und zusammenfügen (0,35 s Pause). Grund (06.11.2026): Mitten im Text
    verschlucken die ElevenLabs-Stimmen das End-s vor einer Pause oft (bei Marie in ~40 % der Fälle),
    am Ende einer Aufnahme kaum. So steht jedes Satzende am Ende einer Aufnahme und wird einzeln geprüft.
    Der vorige Satz geht als previous_text mit, damit die Satzmelodie zusammenpasst."""
    ts = saetze(item['text'])
    if len(ts) < 2: return erzeuge(item, dest, versuche_max)
    wavs, infos = [], []
    for i, t in enumerate(ts):
        kontext = ts[i - 1] if i else item.get('prev')
        w = f'{dest}.satz{i}.wav'
        infos.append(erzeuge({'text': t, 'fig': item['fig'], 'prev': kontext}, w, versuche_max)); wavs.append(w)
    zusammenfuegen(wavs, dest)
    for w in wavs: os.unlink(w)
    geprueft = [s for s in infos if s['pruefen']]
    urteile = [urteil_von(s) for s in geprueft]
    gesamt = 'sch' if all(u == 'sch' for u in urteile) else ('s' if 's' in urteile else 'fehlt')
    lagen = [s['versuche'][s['gewaehlt']]['lage'] for s in geprueft if s['versuche'][s['gewaehlt']]['lage'] is not None]
    from zischlaut import lade, SR
    return {'fig': item['fig'], 'pruefen': bool(geprueft), 'gewaehlt': 0, 'satzweise': True,
            'versuche': [{'urteil': gesamt if geprueft else None, 'lage': max(lagen) if lagen else None,
                          'dauer': round(len(lade(dest)) / SR, 2), 'kontext': True}],
            'saetze': [{'text': t[-40:], 'urteil': urteil_von(s) if s['pruefen'] else None, 'versuche': len(s['versuche'])} for t, s in zip(ts, infos)]}

def endet_auf_s(text):
    return bool(re.search(r'[sSzZ][\s.,;:!?…»«"“”„)\]–-]*$', text))

def plausibel(dauer, text):
    n = len(text)
    return 0.025 * n <= dauer <= 0.2 * n + 2.5

def erzeuge(item, dest, versuche_max=None):
    """Eine Datei erzeugen, End-s und Länge prüfen, bei Bedarf wiederholen. Gibt das Protokoll zurück.
    End-s-Urteil (zischlaut.bewerte): 'sch' = gut; 's' = brasilianisch; 'fehlt' = die KI hat das s
    verschluckt (kam am 06.11. bei der João-Stimme Rodrigo oft vor, z. B. „Levamos doi“)."""
    from zischlaut import lade, bewerte, SR
    stimme = VOICES[item['fig']]
    pruefen = endet_auf_s(item['text'])
    versuche, beste = [], None          # beste = (punkte, pfad, nummer)
    for v in range(versuche_max or VERSUCHE):
        # Kontext ab dem zweiten Versuch abwechselnd an und aus – mal hilft das eine, mal das andere
        prev = item.get('prev') or (PREV_DIALOG if v % 2 == 1 else None)
        seed = None if v == 0 else random.randrange(1, 2 ** 31)
        tmp = f'{dest}.v{v}' + ('.wav' if dest.endswith('.wav') else '.m4a')
        nach_m4a(anfrage(item['text'], stimme['id'], prev, seed), tmp)
        x = lade(tmp); dauer = round(len(x) / SR, 2)
        urteil, l = bewerte(tmp, stimme['s'], stimme['sch'], x, stimme.get('merkmal', 'schwerpunkt')) if pruefen else (None, None)
        laenge_ok = plausibel(dauer, item['text'])
        versuche.append({'urteil': urteil, 'lage': l, 'dauer': dauer, 'kontext': bool(prev)})
        punkte = (0 if laenge_ok else 10) + ({'sch': l, 'fehlt': 1.2, 's': 1.0 + (l or 0)}[urteil] if pruefen else 0)
        if beste is None or punkte < beste[0]:
            if beste: os.unlink(beste[1])
            beste = (punkte, tmp, v)
        else:
            os.unlink(tmp)
        if laenge_ok and (not pruefen or urteil == 'sch'): break
        if not pruefen and v >= 1: break      # nur ein Längenproblem: höchstens zwei Versuche
    os.replace(beste[1], dest)
    return {'fig': item['fig'], 'pruefen': pruefen, 'gewaehlt': beste[2], 'versuche': versuche}

def urteil_von(p):
    g = p['versuche'][p['gewaehlt']]
    if 'urteil' in g: return g['urteil']
    return None if g['lage'] is None else ('sch' if g['lage'] < GRENZE else 's')   # Protokolle vor 06.11. mittags

def zusammenfassung(pruefung, ids):
    stat = {}
    for a in ids:
        p = pruefung.get(a)
        if not p: continue
        s = stat.setdefault(VOICES[p['fig']]['name'], {'Dateien': 0, 'mit End-s': 0, 'sch sofort': 0, 'sch nach Wiederholung': 0, 'unklar': [], 'bleibt s-artig': []})
        s['Dateien'] += 1
        if p['pruefen']:
            s['mit End-s'] += 1
            u = urteil_von(p)
            if u in (None, 'fehlt'): s['unklar'].append(a)
            elif u == 's': s['bleibt s-artig'].append(a)
            elif p['gewaehlt'] == 0: s['sch sofort'] += 1
            else: s['sch nach Wiederholung'] += 1
    return stat

def argumente_nach(schalter):
    i = sys.argv.index(schalter) + 1; out = []
    while i < len(sys.argv) and not sys.argv[i].startswith('--'): out.append(sys.argv[i]); i += 1
    return out

if __name__ == '__main__':
    if not KEY: sys.exit('ELEVENLABS_API_KEY fehlt (vorher: source ~/.zshrc)')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    tok = '--tok' in sys.argv
    ziel = os.path.abspath(argumente_nach('--nach')[0]) if '--nach' in sys.argv else (os.path.join(OUT, 'tok') if tok else OUT)
    os.makedirs(ziel, exist_ok=True)
    items = tok_items() if tok else collect()
    mpfad, ppfad = os.path.join(ziel, 'manifest.json'), os.path.join(ziel, 'pruefung.json')
    manifest = json.load(open(mpfad)) if os.path.exists(mpfad) else {}
    pruefung = json.load(open(ppfad)) if os.path.exists(ppfad) else {}
    versuche_max = int(argumente_nach('--versuche')[0]) if '--versuche' in sys.argv else None
    if '--probe' in sys.argv: auswahl = PROBE_TOK if tok else PROBE
    elif '--nur' in sys.argv: auswahl = argumente_nach('--nur')
    elif '--nachpruefen' in sys.argv:
        # vorhandene Dateien mit End-s streng nachmessen, nur die schlechten neu erzeugen
        from zischlaut import bewerte
        auswahl = [a for a, it in items.items() if endet_auf_s(it['text']) and os.path.exists(os.path.join(ziel, a + '.m4a'))
                   and bewerte(os.path.join(ziel, a + '.m4a'), VOICES[it['fig']]['s'], VOICES[it['fig']]['sch'],
                               merkmal=VOICES[it['fig']].get('merkmal', 'schwerpunkt'))[0] != 'sch']
    elif '--alle' in sys.argv: auswahl = list(items)
    else: auswahl = [a for a, it in items.items()
                     if manifest.get(a) != fingerabdruck(it) or not os.path.exists(os.path.join(ziel, a + '.m4a'))]
    unbekannt = [a for a in auswahl if a not in items]
    if unbekannt: sys.exit(f'Unbekannte Audio-IDs: {unbekannt}')
    zeichen = sum(len(items[a]['text']) for a in auswahl)
    print(f'{len(items)} Audios gesamt, {len(auswahl)} zu erzeugen ({zeichen} Zeichen) → {ziel}', flush=True)
    halt, sperre, fehler, fertig = threading.Event(), threading.Lock(), [], [0]
    def speichern():
        json.dump(manifest, open(mpfad, 'w'), indent=0, sort_keys=True)
        json.dump(pruefung, open(ppfad, 'w'), indent=0, sort_keys=True, ensure_ascii=False)
    def eins(aid):
        if halt.is_set(): return
        it = items[aid]
        try:
            f = erzeuge_saetze if '--saetze' in sys.argv else erzeuge
            info = f(it, os.path.join(ziel, aid + '.m4a'), versuche_max)
        except Guthaben as e:
            halt.set(); fehler.append((aid, 'GUTHABEN AUFGEBRAUCHT: ' + str(e)[:300])); return
        except Exception as e:
            fehler.append((aid, str(e)[:300])); return
        with sperre:
            manifest[aid] = fingerabdruck(it); pruefung[aid] = info; fertig[0] += 1
            if fertig[0] % 50 == 0:
                speichern(); print(f'  {fertig[0]}/{len(auswahl)}', flush=True)
    with ThreadPoolExecutor(3) as pool:
        list(pool.map(eins, auswahl))
    if not ('--probe' in sys.argv or '--nur' in sys.argv or '--nachpruefen' in sys.argv):
        manifest = {a: h for a, h in manifest.items() if a in items}
    speichern()
    print(f'Fertig: {fertig[0]} erzeugt, {len(fehler)} Fehler.' + (' ANGEHALTEN: Guthaben aufgebraucht, später gleichen Aufruf wiederholen.' if halt.is_set() else ''), flush=True)
    for aid, err in fehler[:20]: print('  FEHLER', aid, err, flush=True)
    for name, s in zusammenfassung(pruefung, auswahl).items():
        print(f'  {name}: {s["Dateien"]} Dateien, {s["mit End-s"]} mit End-s → sch sofort {s["sch sofort"]}, nach Wiederholung {s["sch nach Wiederholung"]}, s fehlt/unklar {len(s["unklar"])} {s["unklar"][:12]}, bleibt s-artig {len(s["bleibt s-artig"])} {s["bleibt s-artig"][:12]}', flush=True)
