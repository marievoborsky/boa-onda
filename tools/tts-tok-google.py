#!/usr/bin/env python3
"""Regeneriert NUR die tok/-Einzelwörter mit Google Cloud TTS (pt-PT-Wavenet-E).

Warum: Die ElevenLabs-Marie-Stimme spricht bei isolierten Einzelwörtern den
EP-Auslaut nicht zuverlässig (z. B. „adeus" ohne End-[ʃ]). Google TTS macht
das korrekt. Dialoge/Vokabeln/Geschichten bleiben ElevenLabs.

Aufruf:
  python3 tts-tok-google.py           # alle tok-Wörter, überschreibt audio/tok/
  python3 tts-tok-google.py --nur adeus obrigada   # nur einzelne Wörter
Danach: sw.js-Cache bumpen + pushen.
"""
import json, os, re, sys, base64, subprocess, tempfile, time, glob, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
OUT = os.path.join(BASE, 'audio', 'tok')
VOICE = 'pt-PT-Wavenet-E'
KEY = os.environ.get('GOOGLE_TTS_API_KEY')

def tok_woerter():
    """Wortliste wie in tts-eleven.py: aus allen Story-/Dialogtexten der Lektionen."""
    tok = set()
    def toks(text):
        text = re.sub(r'<br\s*/?>', ' ', text)
        text = re.sub(r'<[^>]+>', ' ', text)
        for w in text.split():
            core = re.sub(r'^[^\wÀ-ÿ]+|[^\wÀ-ÿ]+$', '', w)
            if core and re.search(r'[A-Za-zÀ-ÿ]', core):
                tok.add(core.lower())
    for f in sorted(glob.glob(os.path.join(BASE, 'lektionen', 'tag*.json'))):
        L = json.load(open(f))
        for sec in L['sections']:
            if sec['type'] == 'story':
                toks(sec['text'])
            elif sec['type'] == 'reading':
                for ln in sec['lines']: toks(ln['pt'])
    return sorted(tok)

def synth(text, dest):
    req = json.dumps({
        'input': {'text': text},
        'voice': {'languageCode': 'pt-PT', 'name': VOICE},
        'audioConfig': {'audioEncoding': 'LINEAR16', 'speakingRate': 0.92},
    }).encode()
    r = urllib.request.Request(
        'https://texttospeech.googleapis.com/v1/text:synthesize?key=' + KEY,
        data=req, headers={'Content-Type': 'application/json'})
    for versuch in range(3):
        try:
            wav = base64.b64decode(json.loads(urllib.request.urlopen(r, timeout=30).read())['audioContent'])
            break
        except Exception:
            if versuch == 2: raise
            time.sleep(2)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
        tf.write(wav); tmp = tf.name
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(['afconvert', tmp, dest, '-f', 'm4af', '-d', 'aac', '-b', '48000'],
                   check=True, capture_output=True)
    os.unlink(tmp)

if __name__ == '__main__':
    if not KEY: sys.exit('GOOGLE_TTS_API_KEY fehlt')
    woerter = tok_woerter()
    if '--nur' in sys.argv:
        nur = set(sys.argv[sys.argv.index('--nur') + 1:])
        woerter = [w for w in woerter if w in nur]
    print(f'{len(woerter)} tok-Wörter → {OUT} ({VOICE})', flush=True)
    for i, w in enumerate(woerter, 1):
        synth(w, os.path.join(OUT, w + '.m4a'))
        if i % 50 == 0: print(f'  {i}/{len(woerter)}: {w}', flush=True)
    print('Fertig.', flush=True)
