#!/usr/bin/env python3
"""Generiert alle App-Audios mit dem ElevenLabs-Ensemble (BoaOnda-Stimmen).

Rollen: Dialogzeilen spricht die jeweilige Figur (who-Feld); Vokabeln,
Geschichten und Einzelwörter spricht Marie (Erzählstimme). Tag-8-Sagres
(noch ohne App-Lektion) kommt aus dem Arbeitsblatt: Marie + Vasco.

Voraussetzung: ELEVENLABS_API_KEY in der Umgebung, Voice-IDs in stimmen.json.
  python3 tts-eleven.py --probe   # 4 Beispieldateien
  python3 tts-eleven.py           # alles nach audio-11/ (inkrementell)
"""
import json, os, re, sys, glob, subprocess, tempfile, time, urllib.request, urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
OUT = os.path.join(BASE, 'audio')
KEY = os.environ.get('ELEVENLABS_API_KEY')
VOICES = json.load(open(os.path.join(BASE, 'tools', 'stimmen.json')))
MODEL = 'eleven_multilingual_v2'
WHO2FIG = {'ana': 'ana', 'marie': 'marie', 'joão': 'joao', 'joao': 'joao', 'vasco': 'vasco', 'tomás': 'ana', 'tomas': 'ana', 'empregado': 'vasco', 'empregada': 'marie', 'vendedora': 'marie', 'vendedor': 'vasco', 'senhor': 'vasco', 'motorista': 'vasco', 'senhora': 'ana'}  # Tomás (12): Ana-Stimme – Kinderstimmen-Design ist bei ElevenLabs zu Recht gesperrt
# Kontext-Anker, damit kurze Einzelwörter sicher als EP gesprochen werden (wird nicht mitgesprochen)
PREV = 'Em português europeu: '

def collect():
    items = {}
    def add(aid, text, fig='marie', prev=None):
        items[aid] = {'text': text, 'fig': fig, 'prev': prev}
    s = open(os.path.join(BASE, 'data.js')).read()
    for w in json.loads(s[s.index('['):s.rindex(']')+1]):
        add(w['id'], w.get('say') or w['pt'], 'marie', PREV)
    for f in sorted(glob.glob(os.path.join(BASE, 'lektionen', 'tag*.json'))):
        L = json.load(open(f))
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
    html = open(os.path.join(BASE, '..', 'arbeitsblaetter', 'tag-08-sagres.html')).read()
    lines = re.findall(r'<span class="who">([^<]+):</span>\s*([^<]+)</p>', html)[:12]
    for i, (who, pt) in enumerate(lines, 1):
        add(f'd08{i:02d}', pt.strip(), WHO2FIG.get(who.strip().lower(), 'marie'))
    story = re.search(r'Kleine Geschichte: O fim do mundo.*?<div class="dialog">(.*?)</div>', html, re.S).group(1)
    add('s08', re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', story)).strip(), 'marie')
    return items

def synth(item, dest):
    body = {'text': item['text'], 'model_id': MODEL,
            'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75, 'speed': 0.95}}
    if item.get('prev'): body['previous_text'] = item['prev']
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICES[item['fig']]}?output_format=mp3_44100_128",
        data=json.dumps(body).encode(),
        headers={'xi-api-key': KEY, 'Content-Type': 'application/json'})
    for versuch in range(3):
        try:
            mp3 = urllib.request.urlopen(req, timeout=60).read()
            break
        except urllib.error.HTTPError as e:
            raise SystemExit(f'HTTP {e.code}: {e.read().decode()[:200]}')
        except Exception:
            if versuch == 2: raise
            time.sleep(3)
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tf:
        tf.write(mp3); tmp = tf.name
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(['afconvert', tmp, dest, '-f', 'm4af', '-d', 'aac', '-b', '48000'],
                   check=True, capture_output=True)
    os.unlink(tmp)

if __name__ == '__main__':
    if not KEY: sys.exit('ELEVENLABS_API_KEY fehlt')
    items = collect()
    probe = '--probe' in sys.argv
    if probe:
        keys = ['d0101', 'd0107', 'w001', 's03']
        items = {k: items[k] for k in keys}
    print(f'{len(items)} Audios → {OUT}', flush=True)
    for i, (aid, item) in enumerate(items.items(), 1):
        dest = os.path.join(OUT, aid + '.m4a')
        if os.path.exists(dest): continue
        synth(item, dest)
        if i % 25 == 0 or probe: print(f'  {i}/{len(items)}: {aid} ({item["fig"]})', flush=True)
    print('Fertig.', flush=True)
