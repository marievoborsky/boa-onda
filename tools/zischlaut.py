#!/usr/bin/env python3
"""Misst, ob das s am Ende einer Aufnahme europäisch [ʃ] („sch“) oder brasilianisch [s] klingt.

Verfahren (05./06.11.2026): Aufnahme in 32 kHz mono umwandeln, in 20-ms-Fenster zerlegen,
Reibelaut-Blöcke suchen (viel Energie über 2,5 kHz, wenig darunter) und vom letzten Block
am Ende den spektralen Schwerpunkt bestimmen. [s] liegt hoch, [ʃ] deutlich tiefer.
Weil jede Stimme anders klingt, wird der Wert auf die eigene [s]- und [ʃ]-Lage der Stimme
bezogen (stimmen.json: „s“ und „sch“ in Hz):

    lage = (schwerpunkt − sch) / (s − sch)      0 ≈ „sch“ (richtig), 1 ≈ „s“ (brasilianisch)

Achtung: Vor einem Vokal ist ein summendes s richtig (seis e meia = „sej-si-meia“). Darum
nur das allerletzte s einer Aufnahme prüfen, vor der Pause.

  python3 zischlaut.py datei.m4a [s_hz sch_hz]
"""
import os, subprocess, sys, tempfile
import numpy as np

SR = 32000

def lade(pfad):
    tmp = tempfile.mktemp(suffix='.wav')
    subprocess.run(['afconvert', '-f', 'WAVE', '-d', f'LEI16@{SR}', '-c', '1', pfad, tmp], check=True, capture_output=True)
    b = open(tmp, 'rb').read(); os.unlink(tmp)
    k = b.index(b'data'); n = int.from_bytes(b[k + 4:k + 8], 'little')   # afconvert schreibt WAVE_FORMAT_EXTENSIBLE
    return np.frombuffer(b[k + 8:k + 8 + n - n % 2], dtype='<i2').astype(float) / 32768

def _frames(x, n=640, hop=320):
    if len(x) < n: x = np.pad(x, (0, n - len(x)))
    k = 1 + (len(x) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(k)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * np.hanning(n), axis=1)) ** 2
    return S, np.fft.rfftfreq(n, 1 / SR)

def bloecke(x):
    """Reibelaut-Blöcke (Start-, Endfenster, Schwerpunkt Hz) plus erstes und letztes lautes Fenster."""
    S, f = _frames(x); e = S.sum(1)
    if e.max() <= 0: return [], 0, 0
    db = 10 * np.log10(e / e.max() + 1e-12)
    hi = S[:, f >= 2500].sum(1); lo = S[:, f < 1500].sum(1) + 1e-12
    fr = (hi / lo > 1.5) & (db > -50)
    band = (f >= 2000) & (f <= 11000)
    out = []; i = 0; n = len(fr)
    while i < n:
        if fr[i]:
            j = i
            while j + 1 < n and fr[j + 1]: j += 1
            if j - i + 1 >= 3:
                P = S[i:j + 1][:, band].mean(0)
                out.append((i, j, float((P * f[band]).sum() / P.sum())))
            i = j + 1
        else: i += 1
    laut = np.where(db > -35)[0]
    return out, (laut[0] if len(laut) else 0), (laut[-1] if len(laut) else 0)

def anfang(pfad):
    """Schwerpunkt des Reibelauts ganz am Anfang (zum Einmessen einer Stimme mit „Sim.“ / „Chá.“)."""
    b, a, z = bloecke(lade(pfad))
    for i, j, c in b:
        if i <= a + 6: return c
    return None

def _band(S, f, i, j):
    """Zweites Merkmal (06.11.2026, für tiefe, raue Stimmen wie Vicente, bei denen auch das [s] unter
    4 kHz liegt und der Schwerpunkt kaum trennt): Energie 4–5,5 kHz minus 2–3 kHz in dB.
    [s] hat oben mehr, [ʃ] unten mehr – bei Vicente liegen die beiden 25 dB auseinander."""
    P = S[i:j + 1].mean(0)
    return float(10 * np.log10(P[(f >= 4000) & (f < 5500)].mean() / (P[(f >= 2000) & (f < 3000)].mean() + 1e-20) + 1e-20))

def _wert(x, i, j, c, merkmal):
    if merkmal != 'band': return c
    S, f = _frames(x)
    return _band(S, f, i, j)

def ende(pfad, x=None, merkmal='schwerpunkt'):
    """Schwerpunkt (oder Band-Merkmal) des Reibelauts ganz am Ende, sonst None (kein klarer Zischlaut)."""
    x = lade(pfad) if x is None else x
    b, a, z = bloecke(x)
    for i, j, c in reversed(b):
        if j >= z - 8: return _wert(x, i, j, c, merkmal)
    return None

def ende_genau(pfad, x=None):
    """Wie ende(), aber robuster (06.11.2026): sucht in den letzten 400 ms vor Sprechende auch leise
    Zischlaute und übergeht kurze Geräusche danach (Klicken, Atmen). Gibt (schwerpunkt, status):
    status 'ok' = Zischlaut gefunden, 'fehlt' = am Ende gar kein Zischlaut (KI hat das s verschluckt)."""
    x = lade(pfad) if x is None else x
    S, f = _frames(x); e = S.sum(1)
    if e.max() <= 0: return None, 'fehlt'
    db = 10 * np.log10(e / e.max() + 1e-12)
    hi = S[:, f >= 2500].sum(1); lo = S[:, f < 1500].sum(1) + 1e-12
    sprache = np.where(db > -45)[0]
    if not len(sprache): return None, 'fehlt'
    z = sprache[-1]; a = max(0, z - 40)
    kand = [i for i in range(a, len(db)) if hi[i] / lo[i] > 1.0 and db[i] > -62]
    if not kand: return None, 'fehlt'
    # letzten zusammenhängenden Lauf nehmen (Lücken bis 2 Fenster erlaubt)
    lauf = [kand[-1]]
    for i in reversed(kand[:-1]):
        if lauf[-1] - i <= 3: lauf.append(i)
        else: break
    if len(lauf) < 2: return None, 'fehlt'
    band = (f >= 2000) & (f <= 11000)
    P = S[sorted(lauf)][:, band].mean(0)
    return float((P * f[band]).sum() / P.sum()), 'ok'

def nach_vokal(x, ab=0, bis=None, merkmal='schwerpunkt'):
    """Zischlaut direkt nach dem letzten Vokal (im Bereich ab..bis, in Fenstern zu 10 ms) suchen.
    Robust gegen Atem oder Klicken danach, weil nur die 160 ms nach dem Vokal zählen.
    Gibt (schwerpunkt oder Band-Merkmal, lautstaerke_db) oder (None, None), wenn dort kein Zischlaut ist."""
    S, f = _frames(x); e = S.sum(1) + 1e-14
    db = 10 * np.log10(e / e.max())
    lo = S[:, f < 1500].sum(1) + 1e-14; hi = S[:, f >= 2500].sum(1)
    bis = len(db) if bis is None else min(bis, len(db))
    lodb = 10 * np.log10(lo / lo[ab:bis].max())
    vok = [i for i in range(ab, bis) if lodb[i] > -25]
    if not vok: return None, None
    v = vok[-1]
    fr = [hi[i] / lo[i] > 1.0 and db[i] > -60 for i in range(len(db))]
    def lauf(s):
        j = s
        while j + 1 < len(db) and (fr[j + 1] or (j + 2 < len(db) and fr[j + 2])): j += 1
        return j
    # erster Reibelaut von mindestens 3 Fenstern im 160-ms-Fenster nach dem Vokal
    # (ein einzelnes Geräusch-Fenster direkt nach dem Vokal darf das echte s nicht verdecken – Fix 06.11.)
    start = j = None; s = v + 1
    while s < min(len(db), v + 17):
        if fr[s]:
            e_ = lauf(s)
            if e_ - s + 1 >= 3: start, j = s, e_; break
            s = e_ + 1
        else: s += 1
    if start is None: return None, None
    if merkmal == 'band': wert = _band(S, f, start, j)
    else:
        band = (f >= 2000) & (f <= 11000)
        P = S[start:j + 1][:, band].mean(0)
        wert = float((P * f[band]).sum() / P.sum())
    return wert, float(db[start:j + 1].max())

def bewerte(pfad, s_hz, sch_hz, x=None, merkmal='schwerpunkt'):
    """Gesamturteil über das End-s einer Aufnahme: ('sch' | 's' | 'fehlt', lage).
    'sch' nur, wenn ein deutlicher Zischlaut in [ʃ]-Lage gemessen wird – sonst neu erzeugen.
    merkmal 'band' (stimmen.json) für Stimmen, bei denen der Schwerpunkt kaum trennt; s_hz/sch_hz sind
    dann die Band-Werte in dB."""
    x = lade(pfad) if x is None else x
    c = ende(pfad, x, merkmal)
    if c is None:
        c, staerke = nach_vokal(x, merkmal=merkmal)
        if c is None or staerke < -50: return 'fehlt', None
    l = lage(c, s_hz, sch_hz)
    return ('sch' if l < 0.5 else 's'), l

def lage(schwerpunkt, s_hz, sch_hz):
    if schwerpunkt is None or s_hz == sch_hz: return None
    return round((schwerpunkt - sch_hz) / (s_hz - sch_hz), 2)

if __name__ == '__main__':
    c = ende(sys.argv[1])
    print('Schwerpunkt am Ende:', round(c) if c else 'kein Zischlaut')
    if c and len(sys.argv) == 4: print('Lage (0 = sch, 1 = s):', lage(c, float(sys.argv[2]), float(sys.argv[3])))
