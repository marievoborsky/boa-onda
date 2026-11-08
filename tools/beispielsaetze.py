#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut lektionen/beispiele.json: zu jeder Vokabel ein Beispielsatz mit Ton und deutscher Übersetzung.

Quelle ist tools/beispiele-texte.json (von Hand gepflegt, Schlüssel wie alleWorte() in der App):
  { "<schluessel>": { "a": "<Audio-ID>", "pt": "<Satz>", "de": "<Übersetzung>", "h": "<Wortform im Satz>" } }
Audio-IDs mit d… sind Dialogzeilen aus den Lektionen (Ton in der Stimme der Figur), b… sind eigens
geschriebene Sätze (tts-eleven.py vertont sie mit der Erzählstimme, tts-tok-google.py nimmt ihre Wörter mit auf).

Wörter ohne Eintrag dort (neue Lektionen) bekommen automatisch eine passende Dialogzeile, aber noch keine
Übersetzung. Das Skript listet sie auf: Satz gegenlesen, übersetzen und in die Textdatei eintragen.

Format der App-Datei: { "<Wort-ID>": { "pt", "a", "h": [<Wortnummern zum Hervorheben>], "de" } }
Die Wortnummern zählen wie in der App: am Leerraum getrennt, ab 0.

Automatische Auswahl: zuerst die Lektion, in der das Wort neu ist; dann die zeitlich nächste Lektion.
Innerhalb einer Lektion gewinnen Zeilen aus einem einzigen Satz, dann selten benutzte, dann kurze.
Falsche Treffer (Wort in anderer Bedeutung) kommen in KEIN_SATZ oder FEST.

Aufruf (von überall):  python3 tools/beispielsaetze.py [--liste]
--liste gibt die automatisch gefundenen Paare zum Gegenlesen aus. freischalten.py ruft das Skript selbst auf.
"""
import glob, json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEK = os.path.join(BASE, 'lektionen')
TEXTE = os.path.join(BASE, 'tools', 'beispiele-texte.json')
MAX_ZEICHEN = 110
MIN_WOERTER = 3

ARTIKEL = re.compile(r'^(o|a|os|as|um|uma)\s+')
ARTIKEL_ALLEIN = {'o', 'a', 'os', 'as'}
# Vor einem Nomen stehen diese Wörter nicht: dort ist die gleiche Schreibung meist ein Verb („Trabalho numa padaria“).
VOR_VERB = set('eu tu ele ela nós eles elas você não me te se lhe lhes já também ainda sempre nunca quem'.split())
# Davor ist die gleiche Schreibung meist ein Nomen („em casa“, „a conta“): kein Treffer für das Verb.
VOR_NOMEN = set('''o a os as um uma uns umas do da dos das no na nos nas ao à aos às pelo pela pelos pelas num numa dum duma de em com
    sem para por meu minha meus minhas teu tua teus tuas seu sua seus suas nosso nossa nossos nossas este esta estes estas esse essa
    esses essas aquele aquela aqueles aquelas'''.split())
# Formen, die fast immer etwas anderes heißen (como = wie, para = für, nada = nichts …): nie als Verbform werten.
KEINE_VERBFORM = set('''como para sobre entre contra cedo nada pena tarde sede fora ante vira
    mesa mesmo mesma cara casa certo certa baixo baixa alto alta fino fina sala sala'''.split())

# Gegengelesen am 08.11.2026 (--liste). Die Suche ist grob, deshalb entscheidet hier ein Mensch:
# Kein Satz, weil jede gefundene Zeile das Wort in einer anderen Bedeutung benutzt als die Karte
# („Vamos de comboio, é mais seguro“ ist nicht „die Versicherung“) oder ohne Dialog unverständlich ist.
KEIN_SATZ = {'a', 'um', 'por', 'partir', 'o trabalho', 'o frio', 'mudar', 'o seguro', 'rir', 'Está?', 'a razão',
             'Socorro!', 'cortar-se', 'melhorar', 'segundo', 'o direito', 'contratar', 'a esposa', 'a cerveja'}
# Wort → (Stück der Zeile, die es sein soll; Wort zum Hervorheben), wenn die Suche eine schlechtere Zeile nimmt.
FEST = {
    'que': ('diz que ainda é de manhã', 'que'),
    'se': ('E se chover?', 'se'),
    'mais': ('Gostas mais do café', 'mais'),
    'a semana': ('daqui a duas semanas', 'semanas'),
    'a tarde': ('E à tarde vamos ao cinema', 'tarde'),
    'a chuva': ('A chuva é esperada', 'chuva'),
    'seguir': ('não sigam em frente', 'sigam'),
    'o fim': ('o fim do mundo', 'fim'),
    'primeiro': ('E uma sopa primeiro', 'primeiro'),
    'a volta': ('Ida e volta', 'volta'),
}
# Eigene Wörter, die ohne Artikel wie ein anderes aussähen; dieselbe Liste steht bei alleWorte() in der App
EIGENE_KARTE = {'o / a estudante', 'o / a principiante', 'o / a cliente', 'um', 'que', 'um pouco', 'tarde', 'jantar', 'o alemão / o português / o inglês'}
# Sieht aus wie Artikel + Nomen, ist aber ein fester Ausdruck
PHRASEN = {'o que': ['o', 'que']}


def lade_vokabeln():
    src = open(os.path.join(BASE, 'data.js'), encoding='utf-8').read()
    return json.loads(src[src.index('['):src.rindex(']') + 1])


def lade_irregulaere(html):
    teil = html[html.index('const IRREG = {'):html.index('function wordClass')]
    return {m.group(1).strip("'"): m.group(2).split()
            for m in re.finditer(r"^\s*('?[\wôáéí]+'?):\s*'([^']+)',?\s*$", teil, re.M)}


def verbformen(wort):
    """Wie derivados() in der App, nur der Verb-Zweig."""
    m = re.match(r'^(.+?)(ar|er|ir)$', wort)
    if not m or len(wort) <= 3:
        return []
    st, k = m.groups()
    endungen = {
        'ar': 'o as a amos am ei aste ou ámos aram ava avas ávamos avam e es emos em ando ado ada ados adas',
        'er': 'o es e emos em i este eu eram ia ias íamos iam a as amos am endo ido ida idos idas',
        'ir': 'o es e imos em i iste iu iram ia ias íamos iam a as amos am indo ido ida idos idas',
    }[k].split()
    out = [st + e for e in endungen]
    if k == 'ar' and re.search('[cg]$', st):  # chegar → cheguei, ficar → fiquei
        st2 = re.sub('g$', 'gu', re.sub('c$', 'qu', st))
        out += [st2 + e for e in ('ei', 'e', 'es', 'emos', 'em')]
    return out


def andere_formen(wort, nomen):
    """Plural und, außer bei Nomen, weibliche Formen. Wie derivados() in der App."""
    out = []
    if wort.endswith('ão'):
        out += [wort[:-2] + 'ões', wort[:-2] + 'ãos', wort[:-2] + 'ã']
    elif wort.endswith('al'):
        out.append(wort[:-2] + 'ais')
    elif wort.endswith('el'):
        out.append(wort[:-2] + 'éis')
    elif wort.endswith('ol'):
        out.append(wort[:-2] + 'óis')
    elif wort.endswith('m'):
        out.append(wort[:-1] + 'ns')
    elif re.search('[rsz]$', wort):
        out.append(wort + 'es')
    else:
        out.append(wort + 's')
    if not nomen and wort.endswith('o'):
        out += [wort[:-1] + 'a', wort[:-1] + 'as']
    if not nomen and re.search('[eê]s$', wort):
        out += [re.sub('ês$', 'esa', wort), re.sub('ês$', 'esas', wort), re.sub('ês$', 'eses', wort)]
    return out


def kern(token):
    return re.sub(r'^[^\w]+|[^\w-]+$', '', token, flags=re.U).strip('-').lower()


class Muster:
    """Alles, was als Treffer für einen Karteneintrag gilt."""

    def __init__(self, pt, irreg):
        self.nomen, self.verb, self.sonst, self.formen, self.phrasen = set(), set(), set(), set(), []
        teile = [re.sub(r'[?!.,…:]', '', re.sub(r'\(.*?\)', '', t)).strip() for t in pt.lower().split('/')]
        teile = [t for t in teile if t]
        nur_artikel = all(t in ARTIKEL_ALLEIN for t in teile)
        for p in teile:
            if p in PHRASEN:
                self.phrasen.append(PHRASEN[p])
                continue
            # „o / a principiante“: das einzelne „o“ ist kein Suchwort, nur bei „o / a / os / as“ selbst
            if p in ARTIKEL_ALLEIN and not nur_artikel:
                continue
            ist_nomen = bool(ARTIKEL.match(p))
            w = ARTIKEL.sub('', p).strip()
            woerter = w.split()
            if len(woerter) > 1:
                self.phrasen.append(woerter)
                continue
            w = re.sub(r'-se$', '', w)
            if ist_nomen:
                self.nomen.add(w)
                self.nomen.update(andere_formen(w, True))
            elif w in irreg or verbformen(w):
                self.sonst.add(w)
                self.verb.update(verbformen(w))
                self.verb.update(irreg.get(w, []))
            else:
                self.sonst.add(w)
                self.formen.update(andere_formen(w, False))

    def passt(self, zeile, irreg, andere):
        """Gibt die Wortnummern des Treffers zurück oder None."""
        toks = zeile.split()
        cores = [kern(t) for t in toks]
        for i, c in enumerate(cores):
            basis = c.split('-')[0]
            davor = cores[i - 1] if i else ''
            satzanfang = i == 0 or re.search(r'[.!?…:—]["»”]?$', toks[i - 1])
            if c in self.sonst or basis in self.sonst:
                return [i]
            # abgeleitete Form, die selbst Vokabel ist: mal → „mais“, você → „vocês“ wären falsche Treffer
            if c in self.formen and c not in andere:
                return [i]
            if c in self.nomen and not satzanfang and davor not in VOR_VERB:
                return [i]
            for form in (c, basis):
                if form in self.verb and form not in KEINE_VERBFORM:
                    if form in andere and davor in VOR_NOMEN:
                        continue
                    return [i]
        for ph in self.phrasen:
            n = len(ph)
            kopf = {ph[0], *verbformen(ph[0]), *irreg.get(ph[0], [])}
            for i in range(len(cores) - n + 1):
                if cores[i] in kopf and cores[i + 1:i + n] == ph[1:]:
                    return list(range(i, i + n))
        return None


def schluessel(pt):
    """Wie alleWorte() in der App: ein Wort mit zwei Einträgen zeigt nur eine Karte."""
    k = str(pt).lower()
    if k in EIGENE_KARTE:
        return '=' + k
    return ARTIKEL.sub('', k.split(' / ')[0].split(' (')[0]).strip()


def wortnummern(satz, wort):
    """Stelle der Wortform im Satz, als Nummern der am Leerraum getrennten Wörter. Leer, wenn nicht gefunden."""
    cores, ziel = [kern(t) for t in satz.split()], [kern(t) for t in wort.split()]
    for i in range(len(cores) - len(ziel) + 1):
        if cores[i:i + len(ziel)] == ziel:
            return list(range(i, i + len(ziel)))
    return []


def lade_daten():
    html = open(os.path.join(BASE, 'index.html'), encoding='utf-8').read()
    vokabeln = lade_vokabeln()
    ids = list(dict.fromkeys(re.findall(r"\{\s*id:\s*'(tag\d+|sagres)'", html)))
    lektionen = {}
    for lid in ids:
        pfad = os.path.join(LEK, lid + '.json')
        if os.path.exists(pfad):
            with open(pfad, encoding='utf-8') as f:
                lektionen[lid] = json.load(f)

    alle_zeilen, zeilen, eintraege, kern_lid = {}, [], [], {}
    pt_zu_kern = {v['pt'].strip().lower(): v['id'] for v in vokabeln}
    for lid, L in lektionen.items():
        for sec in L.get('sections', []):
            for ln in sec.get('lines') or []:
                pt, a = ln.get('pt'), ln.get('audio')
                if pt and a:
                    alle_zeilen[a] = {'lid': lid, 'pt': pt, 'a': a, 'who': ln.get('who', '')}
                    if len(pt) <= MAX_ZEICHEN and len(pt.split()) >= MIN_WOERTER:
                        zeilen.append({'lid': lid, 'pt': pt, 'a': a, 'who': ln.get('who', ''),
                                       'saetze': len(re.findall(r'[.!?…]+(?:\s|$)', pt))})
            if sec.get('type') == 'vocab':
                for it in sec.get('items', []):
                    kid = pt_zu_kern.get(it.get('pt', '').strip().lower())
                    if kid:
                        kern_lid.setdefault(kid, lid)
                    elif it.get('audio'):
                        eintraege.append({'id': it['audio'], 'pt': it['pt'], 'de': it.get('de', ''), 'lid': lid})
    eintraege = [{'id': v['id'], 'pt': v['pt'], 'de': v.get('de', ''), 'lid': kern_lid.get(v['id'])} for v in vokabeln] + eintraege
    return {'html': html, 'ids': ids, 'pos': {lid: i for i, lid in enumerate(ids)}, 'eintraege': eintraege,
            'zeilen': zeilen, 'alle_zeilen': alle_zeilen, 'irreg': lade_irregulaere(html)}


def suche(d):
    """Automatische Auswahl: Wort-ID → (Zeile, Wortnummern)."""
    irreg, pos, zeilen, eintraege = d['irreg'], d['pos'], d['zeilen'], d['eintraege']
    # Schreibungen, die selbst als Vokabel existieren (für die Abgrenzung Nomen/Verb)
    andere = set()
    for e in eintraege:
        for teil in e['pt'].lower().split('/'):
            andere.add(ARTIKEL.sub('', re.sub(r'\(.*?\)', '', teil).strip()).strip())

    genutzt, gefunden = {}, {}
    for e in eintraege:
        if e['pt'] in KEIN_SATZ:
            continue
        if e['pt'] in FEST:
            stueck, wort = FEST[e['pt']]
            z = next(z for z in zeilen if stueck in z['pt'])  # bricht bewusst ab, wenn die Zeile im Dialog geändert wurde
            genutzt[z['a']] = genutzt.get(z['a'], 0) + 1
            gefunden[e['id']] = (z, wortnummern(z['pt'], wort)[:1])
            continue
        m = Muster(e['pt'], irreg)
        p0 = pos.get(e['lid'])
        treffer = []
        for z in zeilen:
            h = m.passt(z['pt'], irreg, andere - {ARTIKEL.sub('', e['pt'].lower()).strip()})
            if h is not None:
                treffer.append((z, h))
        if not treffer:
            continue

        def rang(t):
            z = t[0]
            abstand = abs(pos[z['lid']] - p0) if p0 is not None else pos[z['lid']]
            return (abstand, z['saetze'] > 1, genutzt.get(z['a'], 0), len(z['pt']))

        z, h = min(treffer, key=rang)
        genutzt[z['a']] = genutzt.get(z['a'], 0) + 1
        gefunden[e['id']] = (z, h)
    return gefunden


def lade_texte():
    if not os.path.exists(TEXTE):
        return {}
    with open(TEXTE, encoding='utf-8') as f:
        return json.load(f)


def main():
    d = lade_daten()
    gefunden = suche(d)
    texte = lade_texte()
    out, liste, ohne_text, veraltet, ohne_satz, wartet = {}, [], [], [], [], set()
    for e in d['eintraege']:
        t = texte.get(schluessel(e['pt']))
        if t and t['a'].startswith('b') and not os.path.exists(os.path.join(BASE, 'audio', t['a'] + '.m4a')):
            wartet.add(t['a'])                  # noch nicht vertont: Karte bleibt solange ohne Satz
        elif t:
            a, pt = t['a'], t['pt']
            zeile = d['alle_zeilen'].get(a)
            if zeile and zeile['pt'] != pt:     # Dialog wurde geändert: neuer Text, Übersetzung prüfen
                veraltet.append(a)
                pt = zeile['pt']
            h = wortnummern(pt, t['h'])
            if not h:
                sys.exit(f"beispiele-texte.json: „{t['h']}“ steht nicht im Satz „{pt}“ ({e['pt']})")
            out[e['id']] = {'pt': pt, 'a': a, 'h': h, 'de': t['de']}
        elif e['id'] in gefunden:
            z, h = gefunden[e['id']]
            out[e['id']] = {'pt': z['pt'], 'a': z['a'], 'h': h}
            liste.append((e, z))
            ohne_text.append(e['pt'])
        else:
            ohne_satz.append(e['pt'])
    ziel = os.path.join(LEK, 'beispiele.json')
    with open(ziel, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    if '--liste' in sys.argv:
        for e, z in liste:
            print(f"{e['pt']} | {e['de'][:22]} | {z['lid'][3:] if z['lid'].startswith('tag') else z['lid']} | {z['pt']}")
    print(f"beispiele.json: {len(out)} von {len(d['eintraege'])} Einträgen mit Satz ({os.path.getsize(ziel) // 1024} KB)", file=sys.stderr)
    if ohne_text:
        print(f"  {len(ohne_text)} automatisch gefunden, noch ohne Übersetzung: {', '.join(ohne_text[:12])} …", file=sys.stderr)
    if wartet:
        print(f"  {len(wartet)} geschriebene Sätze warten auf die Vertonung (tts-eleven.py), bis dahin ohne Satz", file=sys.stderr)
    if ohne_satz:
        print(f"  {len(ohne_satz)} ohne Satz: {', '.join(ohne_satz[:12])} …", file=sys.stderr)
    if veraltet:
        print(f"  Dialog geändert, Übersetzung prüfen: {', '.join(veraltet)}", file=sys.stderr)


if __name__ == '__main__':
    main()
