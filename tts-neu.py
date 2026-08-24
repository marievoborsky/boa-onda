#!/usr/bin/env python3
"""Generiert ALLE App-Audios neu mit Google Cloud Text-to-Speech (pt-PT).

Warum: Die bisherigen Audios stammen von der macOS-Stimme „Joana" – deren
Lizenz erlaubt keine Weitergabe in einer veröffentlichten App. Google Cloud
TTS ist dafür lizenziert (und die pt-PT-Stimmen sind sehr gut).

Vorbereitung (einmalig):
  1. https://console.cloud.google.com → Projekt anlegen (kostenlos)
  2. „Cloud Text-to-Speech API" aktivieren
  3. API-Schlüssel erstellen (APIs & Dienste → Anmeldedaten)
  4. Free Tier: 1 Mio. Zeichen/Monat gratis – unsere ~500 Audios sind winzig.

Aufruf:
  export GOOGLE_TTS_API_KEY="dein-key"
  python3 tts-neu.py --probe        # nur 3 Testdateien nach audio-neu/
  python3 tts-neu.py                # alles nach audio-neu/
  # anhören, wenn gut: audio/ sichern und audio-neu/ -> audio/
"""
import json, os, re, sys, base64, subprocess, tempfile, urllib.request, glob

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'audio-neu')
VOICE = 'pt-PT-Wavenet-A'   # weiblich; Alternativen: -B/-C (m), -D (w), pt-PT-Standard-*
KEY = os.environ.get('GOOGLE_TTS_API_KEY')

def collect():
    """Sammelt alle (audio-id, text)-Paare der App."""
    items = {}
    # 1) Vokabeln aus data.js (Feld say oder pt)
    s = open(os.path.join(BASE, 'data.js')).read()
    for w in json.loads(s[s.index('['):s.rindex(']')+1]):
        items[w['id']] = w.get('say') or w['pt']
    # 2) Lektionen: Dialoge, Lektions-Vokabeln, Geschichten
    for f in sorted(glob.glob(os.path.join(BASE, 'lektionen', 'tag*.json'))):
        L = json.load(open(f))
        for sec in L['sections']:
            if sec['type'] == 'reading':
                for ln in sec['lines']:
                    if ln.get('audio'): items[ln['audio']] = ln['pt']
            elif sec['type'] == 'vocab':
                for it in sec['items']:
                    if it.get('audio'): items[it['audio']] = it['pt'].replace(' / ', ', ')
            elif sec['type'] == 'story' and sec.get('audio'):
                t = re.sub(r'<br\s*/?>', ' ', sec['text'])
                items[sec['audio']] = re.sub(r'<[^>]+>', '', t)
    # 3) Einzelwörter für die Textos (tok/)
    for f in glob.glob(os.path.join(BASE, 'audio', 'tok', '*.m4a')):
        w = os.path.splitext(os.path.basename(f))[0]
        items['tok/' + w] = w
    return items

def synth(text, dest):
    req = json.dumps({
        'input': {'text': text},
        'voice': {'languageCode': 'pt-PT', 'name': VOICE},
        'audioConfig': {'audioEncoding': 'LINEAR16', 'speakingRate': 0.92},
    }).encode()
    r = urllib.request.Request(
        'https://texttospeech.googleapis.com/v1/text:synthesize?key=' + KEY,
        data=req, headers={'Content-Type': 'application/json'})
    wav = base64.b64decode(json.loads(urllib.request.urlopen(r).read())['audioContent'])
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
        tf.write(wav); tmp = tf.name
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(['afconvert', tmp, dest, '-f', 'm4af', '-d', 'aac', '-b', '48000'],
                   check=True, capture_output=True)
    os.unlink(tmp)

if __name__ == '__main__':
    if not KEY:
        sys.exit('Fehlt: export GOOGLE_TTS_API_KEY=…  (siehe Kommentar oben)')
    items = collect()
    probe = '--probe' in sys.argv
    todo = dict(list(items.items())[:3]) if probe else items
    print(f'{len(todo)} von {len(items)} Audios → {OUT} (Stimme: {VOICE})')
    for i, (aid, text) in enumerate(todo.items(), 1):
        dest = os.path.join(OUT, aid + '.m4a')
        if os.path.exists(dest): continue
        synth(text, dest)
        if i % 25 == 0 or probe: print(f'  {i}/{len(todo)}: {aid} – {text[:40]}')
    print('Fertig. Anhören, dann: mv audio audio-alt && mv audio-neu audio')
