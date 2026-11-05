#!/usr/bin/env python3
"""Generiert ALLE App-Audios (Dialoge, Vokabeln, Geschichten) mit Google Cloud TTS in
europäischem Portugiesisch. Standard-Werkzeug seit 05.11.2026.

Warum nicht mehr ElevenLabs: Die vier ElevenLabs-Stimmen sprechen das s am Wort-
ende meist als [s] (brasilianisch) statt [ʃ] (europäisch) – gemessen am 05.11.2026
nach der Rückmeldung einer Nutzerin. Google pt-PT spricht durchgehend europäisch.

Stimmen: Google hat für pt-PT nur zwei (Wavenet-E weiblich, Wavenet-F männlich).
Die vier Figuren unterscheiden sich über Tonhöhe und Tempo (FIGUREN unten).

Aufruf:
  python3 tts-google.py            # nur Neues und Geändertes (Textvergleich über audio/manifest.json)
  python3 tts-google.py --alle     # alles neu
  python3 tts-google.py --nach DIR # in einen anderen Ordner schreiben (Probe)
Die antippbaren Einzelwörter (audio/tok/) macht weiterhin tts-tok-google.py.
Danach: sw.js (SHELL und bei ersetzten Audios auch AUDIO) hochzählen und pushen.
"""
import json, os, re, sys, base64, subprocess, tempfile, time, hashlib, importlib.util, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 01_APP/
OUT = os.path.join(BASE, 'audio')
KEY = os.environ.get('GOOGLE_TTS_API_KEY')
# Figur → (Stimme, Tonhöhe in Halbtönen, Tempo). Marie ist auch die Erzählstimme.
FIGUREN = {
    'marie': ('pt-PT-Wavenet-E', 0.0, 0.92),
    'ana':   ('pt-PT-Wavenet-E', -1.6, 0.96),
    'joao':  ('pt-PT-Wavenet-F', 1.2, 0.92),
    'vasco': ('pt-PT-Wavenet-F', -1.6, 0.95),
}
VERSION = 'google-1'   # hochzählen, wenn sich FIGUREN ändert – dann wird alles neu erzeugt

# Texte und Rollen kommen aus derselben Sammlung wie früher (tts-eleven.py: collect, WHO2FIG)
_spec = importlib.util.spec_from_file_location('alt', os.path.join(BASE, 'tools', 'tts-eleven.py'))
_alt = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_alt)

def fingerabdruck(item):
    return hashlib.sha1((VERSION + '|' + item['fig'] + '|' + item['text']).encode()).hexdigest()[:16]

def stuecke(text, grenze=1500):
    """Google nimmt höchstens 5000 Bytes pro Anfrage – lange Geschichten satzweise teilen."""
    teile, akt = [], ''
    for satz in re.split(r'(?<=[.!?…])\s+', text.strip()):
        if akt and len((akt + ' ' + satz).encode()) > grenze:
            teile.append(akt); akt = satz
        else:
            akt = (akt + ' ' + satz).strip()
    if akt: teile.append(akt)
    return teile

def anfrage(text, fig):
    stimme, hoehe, tempo = FIGUREN[fig]
    body = json.dumps({
        'input': {'text': text},
        'voice': {'languageCode': 'pt-PT', 'name': stimme},
        'audioConfig': {'audioEncoding': 'LINEAR16', 'sampleRateHertz': 24000, 'speakingRate': tempo, 'pitch': hoehe},
    }).encode()
    for versuch in range(5):
        try:
            r = urllib.request.Request('https://texttospeech.googleapis.com/v1/text:synthesize?key=' + KEY,
                                       data=body, headers={'Content-Type': 'application/json'})
            wav = base64.b64decode(json.loads(urllib.request.urlopen(r, timeout=60).read())['audioContent'])
            k = wav.index(b'data'); n = int.from_bytes(wav[k + 4:k + 8], 'little')
            return wav[k + 8:k + 8 + n]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and versuch < 4: time.sleep(3 + 4 * versuch); continue
            raise RuntimeError(f'HTTP {e.code}: {e.read().decode()[:200]}')
        except Exception:
            if versuch == 4: raise
            time.sleep(2 + 2 * versuch)

def wav_kopf(n, sr=24000):
    return (b'RIFF' + (36 + n).to_bytes(4, 'little') + b'WAVEfmt ' + (16).to_bytes(4, 'little') + (1).to_bytes(2, 'little')
            + (1).to_bytes(2, 'little') + sr.to_bytes(4, 'little') + (sr * 2).to_bytes(4, 'little') + (2).to_bytes(2, 'little')
            + (16).to_bytes(2, 'little') + b'data' + n.to_bytes(4, 'little'))

def synth(item, dest):
    pause = b'\x00\x00' * int(24000 * 0.35)
    pcm = pause.join(anfrage(t, item['fig']) for t in stuecke(item['text']))
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
        tf.write(wav_kopf(len(pcm)) + pcm); tmp = tf.name
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(['afconvert', tmp, dest, '-f', 'm4af', '-d', 'aac', '-b', '48000'], check=True, capture_output=True)
    os.unlink(tmp)

if __name__ == '__main__':
    if not KEY: sys.exit('GOOGLE_TTS_API_KEY fehlt')
    if '--nach' in sys.argv: OUT = os.path.abspath(sys.argv[sys.argv.index('--nach') + 1])
    items = _alt.collect()
    mpfad = os.path.join(OUT, 'manifest.json')
    manifest = json.load(open(mpfad)) if os.path.exists(mpfad) else {}
    alle = '--alle' in sys.argv
    offen = {a: it for a, it in items.items()
             if alle or manifest.get(a) != fingerabdruck(it) or not os.path.exists(os.path.join(OUT, a + '.m4a'))}
    zeichen = sum(len(it['text']) for it in offen.values())
    print(f'{len(items)} Audios gesamt, {len(offen)} zu erzeugen ({zeichen} Zeichen) → {OUT}', flush=True)
    fehler = []
    def eins(paar):
        aid, it = paar
        try:
            synth(it, os.path.join(OUT, aid + '.m4a')); return aid, None
        except Exception as e:
            return aid, str(e)[:200]
    with ThreadPoolExecutor(6) as pool:
        for i, (aid, err) in enumerate(pool.map(eins, offen.items()), 1):
            if err: fehler.append((aid, err))
            else: manifest[aid] = fingerabdruck(items[aid])
            if i % 100 == 0:
                print(f'  {i}/{len(offen)}', flush=True)
                json.dump(manifest, open(mpfad, 'w'), indent=0, sort_keys=True)
    # verwaiste Einträge raus, Manifest sichern
    manifest = {a: h for a, h in manifest.items() if a in items}
    os.makedirs(OUT, exist_ok=True)
    json.dump(manifest, open(mpfad, 'w'), indent=0, sort_keys=True)
    print(f'Fertig. Fehler: {len(fehler)}', flush=True)
    for aid, err in fehler: print('  FEHLER', aid, err, flush=True)
