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

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
OUT = os.path.join(BASE, 'audio-neu')
VOICE_W = 'pt-PT-Wavenet-E'   # weiblich: Ana, Marie, Vokabeln, Geschichten, Einzelwörter
VOICE_M = 'pt-PT-Wavenet-F'   # männlich: João, Vasco
MAENNER = {'joão', 'joao', 'vasco', 'tiago'}
KEY = os.environ.get('GOOGLE_TTS_API_KEY')

def collect():
    """Sammelt alle (audio-id, {text, voice})-Paare der App."""
    items = {}
    def add(aid, text, voice=None):
        items[aid] = {'text': text, 'voice': voice or VOICE_W}
    # 1) Vokabeln aus data.js (Feld say oder pt)
    s = open(os.path.join(BASE, 'data.js')).read()
    for w in json.loads(s[s.index('['):s.rindex(']')+1]):
        add(w['id'], w.get('say') or w['pt'])
    # 2) Lektionen: Dialoge (Stimme nach Sprecher!), Lektions-Vokabeln, Geschichten
    for f in sorted(glob.glob(os.path.join(BASE, 'lektionen', 'tag*.json'))):
        L = json.load(open(f))
        for sec in L['sections']:
            if sec['type'] == 'reading':
                for ln in sec['lines']:
                    if ln.get('audio'):
                        v = VOICE_M if ln['who'].strip().lower() in MAENNER else VOICE_W
                        add(ln['audio'], ln['pt'], v)
            elif sec['type'] == 'vocab':
                for it in sec['items']:
                    if it.get('audio'): add(it['audio'], it['pt'].replace(' / ', ', '))
            elif sec['type'] == 'story' and sec.get('audio'):
                t = re.sub(r'<br\s*/?>', ' ', sec['text'])
                add(sec['audio'], re.sub(r'<[^>]+>', '', t))
    # 3) Einzelwörter für die Textos (tok/)
    for f in glob.glob(os.path.join(BASE, 'audio', 'tok', '*.m4a')):
        w = os.path.splitext(os.path.basename(f))[0]
        add('tok/' + w, w)
    return items

def synth(text, dest, voice=None):
    req = json.dumps({
        'input': {'text': text},
        'voice': {'languageCode': 'pt-PT', 'name': voice or VOICE_W},
        'audioConfig': {'audioEncoding': 'LINEAR16', 'speakingRate': 0.92},
    }).encode()
    r = urllib.request.Request(
        'https://texttospeech.googleapis.com/v1/text:synthesize?key=' + KEY,
        data=req, headers={'Content-Type': 'application/json'})
    for versuch in range(3):
        try:
            wav = base64.b64decode(json.loads(urllib.request.urlopen(r, timeout=30).read())['audioContent'])
            break
        except Exception as e:
            if versuch == 2: raise
            import time; time.sleep(2)
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
    print(f'{len(todo)} von {len(items)} Audios → {OUT} ({VOICE_W} + {VOICE_M})')
    for i, (aid, it) in enumerate(todo.items(), 1):
        dest = os.path.join(OUT, aid + '.m4a')
        if os.path.exists(dest): continue
        synth(it['text'], dest, it['voice'])
        if i % 25 == 0 or probe: print(f'  {i}/{len(todo)}: {aid} – {it["text"][:40]}', flush=True)
    print('Fertig. Anhören, dann: mv audio audio-alt && mv audio-neu audio')
