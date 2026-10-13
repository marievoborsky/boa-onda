#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lesewörterbuch für den Reader (Textos): Wörter, die in den Geschichten und Dialogen
vorkommen, aber keine Lektionsvokabeln sind. Schreibt lektionen/leseworte.json.
Die App hängt diese Einträge als unterste Stufe ans Reader-Wörterbuch (ohne „Lernen“-Knopf).
Nomen mit Artikel (dann bildet die App Plural), Verben im Infinitiv (dann bildet die App
die regelmäßigen Formen); unregelmäßige Formen stehen extra. Nur europäisches Portugiesisch.

  python3 tools/leseworte.py
"""
import json, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W = {
 # Zeit, Ordnung, Menge
 'depois': 'danach, dann', 'antes': 'vorher, früher', 'então': 'dann, also', 'só': 'nur; allein', 'quase': 'fast', 'ainda': 'noch', 'já': 'schon',
 'sempre': 'immer', 'nunca': 'nie', 'logo': 'gleich, bald', 'cedo': 'früh', 'tarde': 'spät', 'agora': 'jetzt', 'hoje': 'heute', 'ontem': 'gestern', 'amanhã': 'morgen',
 'duas': 'zwei (weiblich)', 'dois': 'zwei', 'três': 'drei', 'cento': 'hundert (in Zusammensetzungen: cento e um)', 'duzentos': 'zweihundert', 'trezentos': 'dreihundert',
 'metade': 'die Hälfte', 'segundo': 'zweiter; die Sekunde', 'os segundos': 'die Sekunden', 'terceiro': 'dritter', 'terceira': 'dritte', 'quinta': 'fünfte; Donnerstag (quinta-feira)',
 'segunda': 'zweite; Montag (segunda-feira)', 'terça': 'Dienstag (terça-feira)', 'quarta': 'vierte; Mittwoch (quarta-feira)', 'sexta': 'sechste; Freitag (sexta-feira)',
 'cada': 'jeder, jede, jedes', 'todo': 'ganz, jeder', 'toda': 'ganz, jede', 'todos': 'alle', 'todas': 'alle (weiblich)', 'outro': 'anderer', 'outra': 'andere', 'outros': 'andere (Plural)',
 'mesmo': 'selbst; sogar; derselbe', 'mesma': 'dieselbe', 'tanto': 'so viel', 'demais': 'zu viel, zu sehr', 'qualquer': 'irgendein, beliebig', 'nenhuma': 'keine', 'nenhum': 'keiner',
 'alguém': 'jemand', 'ninguém': 'niemand', 'nada': 'nichts', 'tudo': 'alles', 'nem': 'nicht einmal; auch nicht', 'assim': 'so, auf diese Weise', 'quê': 'was (betont, am Satzende)',
 'junho': 'Juni', 'julho': 'Juli', 'agosto': 'August', 'setembro': 'September', 'outubro': 'Oktober', 'maio': 'Mai', 'as férias': 'die Ferien', 'o passado': 'die Vergangenheit',
 # Pronomen, Partikel
 'me': 'mich, mir', 'te': 'dich, dir', 'lhe': 'ihm, ihr', 'lhes': 'ihnen', 'nos': 'uns', 'vos': 'euch', 'mim': 'mir, mich (nach Präposition)', 'ti': 'dir, dich (nach Präposition)', 'si': 'sich; Ihnen',
 'connosco': 'mit uns', 'dele': 'von ihm, sein', 'dela': 'von ihr, ihr', 'deles': 'von ihnen, ihr', 'delas': 'von ihnen, ihr (weiblich)', 'desta': 'von dieser', 'deste': 'von diesem', 'nesta': 'in dieser', 'neste': 'in diesem',
 'aí': 'da (bei dir)', 'cá': 'hier', 'lá': 'dort', 'fora': 'draußen', 'dentro': 'drinnen', 'trás': 'hinten (para trás = zurück)', 'junto': 'zusammen, nahe', 'o lado': 'die Seite (ao lado = daneben)', 'o meio': 'die Mitte (no meio = mittendrin)',
 'o fundo': 'der Hintergrund, der Grund (ao fundo = hinten)', 'o canto': 'die Ecke', 'o resto': 'der Rest', 'o princípio': 'der Anfang', 'o ponto': 'der Punkt', 'a causa': 'die Ursache (por causa de = wegen)',
 'claro': 'klar, natürlich; hell', 'escuro': 'dunkel', 'escuras': 'dunkel (Plural, weiblich)', 'a verdade': 'die Wahrheit', 'sério': 'ernst (a sério = im Ernst)', 'normal': 'normal', 'raro': 'selten', 'estranho': 'seltsam', 'perigoso': 'gefährlich',
 'importante': 'wichtig', 'perfeito': 'perfekt', 'perfeita': 'perfekt (weiblich)', 'perfeitas': 'perfekt (Plural, weiblich)', 'fantástico': 'fantastisch', 'fantástica': 'fantastisch (weiblich)', 'famoso': 'berühmt', 'oficial': 'offiziell',
 'rápido': 'schnell', 'forte': 'stark', 'fraco': 'schwach', 'fina': 'dünn, fein', 'largo': 'breit', 'liso': 'glatt', 'molhado': 'nass', 'molhada': 'nass (weiblich)', 'quieta': 'still, ruhig', 'magra': 'dünn, schlank', 'torto': 'schief',
 'sozinha': 'allein (weiblich)', 'sozinho': 'allein', 'sentado': 'sitzend', 'sentada': 'sitzend (weiblich)', 'caído': 'gefallen, umgefallen', 'escrito': 'geschrieben', 'ligado': 'an, eingeschaltet', 'correta': 'richtig, korrekt', 'único': 'einzig',
 'próxima': 'nächste', 'própria': 'eigene', 'honesta': 'ehrlich', 'exatamente': 'genau', 'baixinho': 'ganz leise', 'um bocadinho': 'ein bisschen', 'bem-vinda': 'willkommen (zu einer Frau)', 'bem-vindos': 'willkommen (zu mehreren)',
 'grátis': 'gratis, umsonst', 'útil': 'nützlich (dias úteis = Werktage)', 'úteis': 'nützlich (Plural)', 'breve': 'kurz (até breve = bis bald)', 'direito': 'gerade; rechts; das Recht',
 # Farben
 'azul': 'blau', 'branco': 'weiß', 'branca': 'weiß (weiblich)', 'brancas': 'weiß (Plural, weiblich)', 'preto': 'schwarz', 'verde': 'grün', 'amarelo': 'gelb', 'vermelho': 'rot', 'vermelhos': 'rot (Plural)', 'cinzenta': 'grau (weiblich)',
 'dourada': 'golden (weiblich)', 'cor-de-rosa': 'rosa', 'a cor': 'die Farbe',
 # Menschen, Körper
 'a pessoa': 'die Person', 'a gente': 'die Leute; wir (umgangssprachlich)', 'o senhor': 'der Herr; Sie', 'a senhora': 'die Dame; Sie', 'a dona': 'Frau … (vor Vornamen älterer Frauen)', 'a menina': 'das Mädchen', 'o miúdo': 'der Junge, das Kind',
 'a malta': 'die Leute, die Clique (umgangssprachlich)', 'o bebé': 'das Baby', 'a doutora': 'die Ärztin; Frau Doktor', 'a enfermeira': 'die Krankenschwester', 'o pescador': 'der Fischer', 'o vendedor': 'der Verkäufer', 'o chefe': 'der Chef',
 'o surfista': 'der Surfer', 'o cidadão': 'der Bürger (Loja do Cidadão = Bürgerladen)', 'os alemães': 'die Deutschen', 'o animal': 'das Tier', 'o gato': 'die Katze',
 'o olho': 'das Auge', 'a boca': 'der Mund', 'o nariz': 'die Nase', 'a mão': 'die Hand', 'as mãos': 'die Hände', 'o dedo': 'der Finger', 'o polegar': 'der Daumen', 'o ombro': 'die Schulter', 'o joelho': 'das Knie', 'o colo': 'der Schoß',
 'o corpo': 'der Körper', 'o sorriso': 'das Lächeln', 'a voz': 'die Stimme', 'o gesto': 'die Geste', 'as palmas': 'das Klatschen (bater palmas)', 'o talento': 'das Talent', 'a paciência': 'die Geduld', 'a pressa': 'die Eile',
 'a saudade': 'die Sehnsucht', 'o segredo': 'das Geheimnis', 'o milagre': 'das Wunder', 'a lógica': 'die Logik', 'o problema': 'das Problem', 'a disposição': 'die Laune (à disposição = zur Verfügung)', 'o movimento': 'die Bewegung',
 # Dinge, Orte
 'a carrinha': 'der Van, der Kleinbus', 'o telemóvel': 'das Handy', 'o caderno': 'das Heft', 'o sofá': 'das Sofa', 'a cama': 'das Bett', 'o armário': 'der Schrank', 'a gaveta': 'die Schublade', 'a cadeira': 'der Stuhl', 'o teto': 'die Decke (Zimmer)',
 'o corredor': 'der Flur', 'a varanda': 'der Balkon', 'o prédio': 'das Gebäude, das Wohnhaus', 'o muro': 'die Mauer', 'a ponte': 'die Brücke', 'a avenida': 'die Allee, die Avenida', 'o caminho': 'der Weg', 'a vila': 'die Kleinstadt',
 'o campo': 'das Feld; das Land', 'o rio': 'der Fluss', 'o sul': 'der Süden', 'o norte': 'der Norden', 'o sítio': 'der Ort, die Stelle', 'o banco': 'die Bank (zum Sitzen; Geld)', 'o hospital': 'das Krankenhaus', 'o hostel': 'das Hostel',
 'a piscina': 'das Schwimmbad', 'o duche': 'die Dusche', 'a luz': 'das Licht', 'o ar': 'die Luft', 'o fogo': 'das Feuer', 'o sal': 'das Salz', 'o cheiro': 'der Geruch', 'a maré': 'die Gezeiten, die Flut', 'a falésia': 'die Klippe', 'o tronco': 'der Stamm',
 'o navio': 'das Schiff', 'o camião': 'der Lastwagen', 'o motor': 'der Motor', 'o quilómetro': 'der Kilometer', 'o metro': 'der Meter; die Metro', 'o litro': 'der Liter', 'o grupo': 'die Gruppe', 'a lista': 'die Liste', 'a caixa': 'die Kiste, die Kasse',
 'o envelope': 'der Umschlag', 'o selo': 'die Briefmarke', 'o papel': 'das Papier', 'a página': 'die Seite (Buch)', 'a letra': 'der Buchstabe; der Liedtext', 'a palavra': 'das Wort', 'a frase': 'der Satz', 'a conversa': 'das Gespräch', 'a mensagem': 'die Nachricht',
 'o telefone': 'das Telefon', 'o número': 'die Nummer', 'o vídeo': 'das Video', 'o projeto': 'das Projekt', 'a calculadora': 'der Taschenrechner', 'o lápis': 'der Bleistift', 'o despertador': 'der Wecker',
 'a roupa': 'die Kleidung', 'o casaco': 'die Jacke', 'o vestido': 'das Kleid', 'o pijama': 'der Schlafanzug', 'a t-shirt': 'das T-Shirt', 'o boné': 'die Kappe', 'a toalha': 'das Handtuch', 'a mochila': 'der Rucksack', 'a bata': 'der Kittel',
 'o plástico': 'das Plastik', 'o esqueleto': 'das Skelett', 'a chávena': 'die Tasse', 'a fatia': 'die Scheibe', 'a manteiga': 'die Butter', 'o pão': 'das Brot', 'os pães': 'die Brote', 'o pastel': 'das Törtchen, die Pastete', 'os pastéis': 'die Törtchen',
 'as flores': 'die Blumen', 'o bico': 'der Schnabel; die Spitze', 'o quadrado': 'das Quadrat', 'a venda': 'der Verkauf; die Augenbinde', 'o campeonato': 'die Meisterschaft', 'o fado': 'der Fado', 'o marquês': 'der Marquis (Marquês de Pombal)',
 # Verben (Infinitiv → die App bildet die regelmäßigen Formen)
 'olhar': 'schauen', 'pensar': 'denken', 'fechar': 'schließen', 'esperar': 'warten; hoffen', 'responder': 'antworten', 'gritar': 'schreien', 'perguntar': 'fragen', 'tocar': 'klingeln; berühren; spielen (Instrument)', 'sorrir': 'lächeln',
 'subir': 'hinaufgehen, steigen', 'descer': 'hinuntergehen', 'sair': 'hinausgehen, weggehen', 'entrar': 'hineingehen', 'buscar': 'holen', 'levantar': 'heben (levantar-se = aufstehen)', 'sentar': 'setzen (sentar-se = sich setzen)', 'deitar': 'legen (deitar-se = sich hinlegen)',
 'ligar': 'anrufen; einschalten', 'mandar': 'schicken; befehlen', 'receber': 'bekommen', 'mostrar': 'zeigen', 'apontar': 'zeigen auf; notieren', 'tirar': 'nehmen, herausnehmen; machen (Foto)', 'deixar': 'lassen', 'parar': 'anhalten, aufhören',
 'passar': 'vorbeigehen; verbringen', 'continuar': 'weitermachen', 'tentar': 'versuchen', 'acabar': 'beenden; enden (acabar de = gerade … haben)', 'começar': 'anfangen', 'durar': 'dauern', 'aparecer': 'auftauchen, erscheinen', 'parecer': 'scheinen, aussehen wie',
 'acreditar': 'glauben', 'achar': 'finden, meinen', 'compreender': 'verstehen', 'ler': 'lesen', 'escrever': 'schreiben', 'cantar': 'singen', 'bater': 'klopfen, schlagen', 'apitar': 'pfeifen, hupen', 'pigarrear': 'sich räuspern', 'tossir': 'husten',
 'cheirar': 'riechen', 'provar': 'probieren', 'nascer': 'geboren werden; aufgehen (Sonne)', 'defender': 'verteidigen', 'odiar': 'hassen', 'irritar': 'ärgern', 'mentir': 'lügen', 'existir': 'existieren', 'caber': 'hineinpassen',
 'arranjar': 'besorgen; reparieren', 'acampar': 'zelten', 'surfar': 'surfen', 'piscar': 'blinzeln, zwinkern', 'desistir': 'aufgeben', 'precisar': 'brauchen', 'gostar': 'mögen', 'esquecer': 'vergessen',
 # unregelmäßige / besondere Formen
 'olha': 'schau; er/sie schaut (olhar)', 'olhou': 'schaute (olhar)', 'olham': 'sie schauen (olhar)', 'pensa': 'er/sie denkt (pensar)', 'pensou': 'dachte (pensar)', 'fecha': 'er/sie schließt (fechar)', 'fechou': 'schloss (fechar)',
 'sorri': 'er/sie lächelt (sorrir)', 'ri': 'er/sie lacht (rir)', 'riu-se': 'lachte (rir-se)', 'ri-se': 'er/sie lacht (rir-se)', 'sobe': 'er/sie steigt hinauf (subir)', 'desce': 'er/sie geht hinunter (descer)', 'sai': 'er/sie geht hinaus (sair)', 'saiu': 'ging hinaus (sair)',
 'lê': 'er/sie liest (ler)', 'vê-se': 'man sieht (ver-se)', 'ouve-se': 'man hört (ouvir-se)', 'pôs': 'stellte, legte (pôr)', 'põe': 'er/sie stellt, legt (pôr)', 'havia': 'es gab (haver)', 'há': 'es gibt; seit (haver)', 'houver': 'wenn es gibt (haver, futuro do conjuntivo)',
 'fosse': 'wäre (ser/ir, imperfeito do conjuntivo)', 'tivesse': 'hätte (ter, imperfeito do conjuntivo)', 'for': 'wenn … ist/geht (ser/ir, futuro do conjuntivo)', 'mantiver': 'wenn … hält (manter)', 'cabem': 'sie passen hinein (caber)',
 'disse-me': 'sagte mir (dizer)', 'diz-lhe': 'sagt ihm/ihr (dizer)', 'dá-lhe': 'gibt ihm/ihr (dar)', 'põe-na': 'stellt sie hin (pôr)', 'leva-se': 'man nimmt mit (levar)', 'encontra-o': 'findet ihn (encontrar)', 'abriu-o': 'öffnete ihn (abrir)',
 'doíam-lhe': 'taten ihm/ihr weh (doer)', 'doíam': 'taten weh (doer)', 'irrita-me': 'ärgert mich (irritar)', 'mudava-lhe': 'veränderte ihm/ihr (mudar)', 'pôs-lhe': 'legte ihm/ihr hin (pôr)', 'tragam': 'bringt (trazer, Konjunktiv/Imperativ Plural)',
 'acho': 'ich finde, ich glaube (achar)', 'preciso': 'ich brauche (precisar); nötig', 'precisa': 'er/sie braucht (precisar)', 'precisamos': 'wir brauchen (precisar)', 'gosta': 'er/sie mag (gostar)', 'gostas': 'du magst (gostar)', 'parece': 'es scheint (parecer)',
 'a coisa': 'die Sache, das Ding', 'a aula': 'der Unterricht, die Stunde', 'a previsão': 'die Vorhersage (previsão do tempo = Wetterbericht)', 'a vez': 'das Mal', 'o favor': 'der Gefallen', 'a posição': 'die Position, die Haltung',
 'procurar': 'suchen', 'odiar': 'hassen', 'odeia': 'er/sie hasst (odiar)', 'odeio': 'ich hasse (odiar)', 'pigarreia': 'er/sie räuspert sich (pigarrear)', 'o fã': 'der Fan', 'as notícias': 'die Nachrichten', 'doido': 'verrückt', 'doidos': 'verrückt (Plural)',
 'escolher': 'auswählen', 'a campeã': 'die Meisterin', 'saltar': 'springen', 'a bola': 'der Ball', 'o humor': 'der Humor; die Laune', 'interessante': 'interessant', 'empurrar': 'schieben, stoßen', 'o futebol': 'der Fußball', 'a baleeira': 'das Walfangboot', 'a pesca': 'der Fischfang',
 'as batatas fritas': 'die Pommes', 'o bife': 'das Steak', 'a fome': 'der Hunger', 'cansar': 'müde machen', 'discutir': 'streiten, diskutieren', 'desculpem': 'entschuldigt (desculpar)', 'a pedra': 'der Stein', 'seguinte': 'folgend, nächste', 'atrasado': 'verspätet',
 'acender': 'anzünden, einschalten', 'acende-se': 'geht an (acender-se)', 'riem': 'sie lachen (rir)', 'o postal': 'die Postkarte', 'chiar': 'quietschen', 'soar': 'klingen', 'a parede': 'die Wand', 'satisfeito': 'zufrieden', 'furiosa': 'wütend (weiblich)', 'casar': 'heiraten',
 'certo': 'richtig, sicher', 'explodir': 'explodieren', 'o ouro': 'das Gold', 'fotografar': 'fotografieren', 'a esquina': 'die Straßenecke', 'milhares': 'Tausende', 'a martelada': 'der Hammerschlag', 'desaparecer': 'verschwinden', 'guardar': 'aufbewahren, behalten', 'o texto': 'der Text',
 'hum': 'hm', 'ah': 'ah', 'oh': 'oh', 'ohhh': 'ohhh', 'pling': 'pling (Nachrichtenton)',
 # ---- Ergänzung 2026-10-13 (QA-Regression: Reader-Abdeckung der Textos) ----
 # Monate, Zeit, Ordnungszahlen
 'janeiro': 'Januar', 'fevereiro': 'Februar', 'março': 'März', 'abril': 'April', 'novembro': 'November', 'dezembro': 'Dezember', 'junho–setembro': 'Juni bis September',
 'os meses': 'die Monate', 'o momento': 'der Moment, der Augenblick', 'o intervalo': 'die Pause', 'a data': 'das Datum', 'a antecedência': 'der Vorlauf (com antecedência = im Voraus)', 'anterior': 'vorherig, vorige',
 'prévio': 'vorherig (aviso prévio = Kündigungsfrist)', 'mensalmente': 'monatlich', 'sétimo': 'siebter', 'oitavo': 'achter', 'nono': 'neunter', 'décimo': 'zehnter', 'trigésimo': 'dreißigster',
 # Pronomen, Präpositionen, Adverbien
 'comigo': 'mit mir', 'consigo': 'mit sich; mit Ihnen; ich schaffe es (conseguir)', 'contra': 'gegen', 'daqui': 'von hier (daqui a = in … Zeit)', 'abaixo': 'unten, darunter', 'àquele': 'zu jenem (a + aquele)', 'àquela': 'zu jener (a + aquela)',
 'desse': 'von diesem, von dem (de + esse)', 'dessa': 'von dieser (de + essa)', 'desses': 'von diesen (de + esses)', 'nesse': 'in diesem, in dem (em + esse)', 'nessa': 'in dieser (em + essa)', 'nesses': 'in diesen (em + esses)', 'nessas': 'in diesen (em + essas)',
 'nele': 'in ihm, darin (em + ele)', 'nela': 'in ihr (em + ela)', 'neles': 'in ihnen (em + eles)', 'nelas': 'in ihnen (em + elas)', 'nisso': 'darin, daran (em + isso)', 'noutro': 'in einem anderen (em + outro)', 'noutra': 'in einer anderen (em + outra)',
 'cujo': 'dessen, deren', 'demasiado': 'zu, zu sehr; zu viel', 'claramente': 'deutlich, klar', 'nitidamente': 'deutlich, ganz klar', 'estranhamente': 'seltsamerweise', 'igualmente': 'ebenfalls, gleichfalls', 'devagarinho': 'ganz langsam',
 # Adjektive
 'comprido': 'lang', 'longo': 'lang', 'curto': 'kurz', 'estreito': 'eng, schmal', 'plano': 'flach, eben; der Plan', 'redondo': 'rund', 'enorme': 'riesig', 'pesado': 'schwer', 'lento': 'langsam', 'tranquilo': 'ruhig', 'silencioso': 'still, leise',
 'simples': 'einfach', 'livre': 'frei', 'rico': 'reich', 'moderno': 'modern', 'excelente': 'ausgezeichnet', 'ótimo': 'bestens, großartig', 'horrível': 'schrecklich', 'péssimo': 'sehr schlecht, miserabel', 'brilhante': 'glänzend, strahlend',
 'necessário': 'nötig, notwendig', 'desnecessário': 'unnötig', 'suficiente': 'genug, ausreichend', 'máximo': 'höchster; das Maximum (no máximo = höchstens)', 'verdadeiro': 'wahr, echt', 'errado': 'falsch', 'próprio': 'eigener; selbst (ele próprio = er selbst)',
 'ocupado': 'beschäftigt, besetzt', 'ofendido': 'beleidigt', 'surpreendido': 'überrascht', 'atrevido': 'frech, dreist', 'teimoso': 'stur', 'paciente': 'geduldig; der Patient', 'assustador': 'beängstigend, erschreckend', 'caríssimo': 'sehr teuer; liebster',
 'cinzento': 'grau', 'dourado': 'golden', 'aceso': 'an, eingeschaltet; angezündet', 'encostado': 'angelehnt', 'pendurado': 'aufgehängt', 'dobrado': 'gefaltet; verdoppelt', 'cruzado': 'verschränkt, gekreuzt', 'alinhado': 'ausgerichtet, in einer Reihe',
 'colado': 'geklebt, angeklebt', 'destruído': 'zerstört', 'despenteado': 'zerzaust', 'cozido': 'gekocht', 'frito': 'frittiert, gebraten', 'culpado': 'schuldig; der Schuldige', 'morto': 'tot', 'vivo': 'lebendig, lebend', 'nu': 'nackt, kahl', 'limpo': 'sauber',
 'nasal': 'nasal (Nasallaut: ão, em, im …)', 'alentejano': 'aus dem Alentejo', 'bávaro': 'bayerisch; der Bayer', 'presente': 'vorliegend; anwesend; das Geschenk; das Präsens', 'calculado': 'berechnet', 'emprestado': 'geliehen',
 # Grammatik-Metawörter
 'o verbo': 'das Verb', 'o conjuntivo': 'der Konjunktiv (Grammatik)', 'o imperfeito': 'das Imperfekt (Vergangenheit für Zustände und Gewohnheiten)', 'o condicional': 'das Konditional (würde-Form)', 'a concordância': 'die Übereinstimmung, die Kongruenz (Grammatik)',
 'o artigo': 'der Artikel', 'a exclamação': 'der Ausruf (ponto de exclamação = Ausrufezeichen)', 'o algarismo': 'die Ziffer', 'o teste': 'der Test', 'o verso': 'die Rückseite; der Vers', 'a forma': 'die Form', 'o termo': 'die Frist; der Begriff (contrato a termo = befristeter Vertrag)',
 'o tipo': 'die Art, die Sorte; der Typ', 'a diferença': 'der Unterschied', 'o sinal': 'das Zeichen, das Signal; das Verkehrsschild', 'o valor': 'der Wert; der Betrag', 'o exemplo': 'das Beispiel', 'B1': 'B1 – Sprachniveau (Europäischer Referenzrahmen)',
 'Exmo.': 'Excelentíssimo – Sehr geehrter (förmliche Briefanrede: Exmo. Senhor)', 'o PDF': 'das PDF', 'querido': 'lieber, liebe (Briefanrede: Querido …; auch Partizip von querer)', 'o mail': 'die Mail, die E-Mail', 'o e-mail': 'die E-Mail', 'a internet': 'das Internet', 'o site': 'die Website',
 'Herr': 'Herr (deutsch, im Text)', 'Nein': 'nein (deutsch, im Text)', 'paddeln': 'paddeln (deutsch, im Text)', 'Staffel': 'Staffel (deutsch: Teil des Kurses)',
 'entãomarieegostasdoportoéumacidadelindanãoé': 'Avó-Schnellsprech: Então, Marie, e gostas do Porto? É uma cidade linda, não é? – Also, Marie, magst du Porto? Eine schöne Stadt, oder?',
 # Nomen: Alltag, Dinge
 'o relógio': 'die Uhr', 'o computador': 'der Computer', 'o portátil': 'der Laptop', 'o ecrã': 'der Bildschirm', 'a impressora': 'der Drucker', 'a televisão': 'der Fernseher, das Fernsehen', 'a máquina': 'die Maschine, der Apparat',
 'a caneta': 'der Stift, der Kugelschreiber', 'a folha': 'das Blatt', 'o quadro': 'die Tafel; das Bild', 'a coluna': 'die Spalte; die Säule', 'a carta': 'der Brief; die Spielkarte', 'o cartaz': 'das Plakat', 'o carimbo': 'der Stempel',
 'o passaporte': 'der Reisepass', 'o recibo': 'die Quittung', 'a declaração': 'die Erklärung', 'a fotografia': 'das Foto', 'os telemóveis': 'die Handys', 'a lâmpada': 'die Glühbirne, die Lampe', 'a vela': 'die Kerze; das Segel',
 'o espelho': 'der Spiegel', 'o vidro': 'das Glas (Material); die Scheibe', 'a lata': 'die Dose', 'o balde': 'der Eimer', 'a panela': 'der Kochtopf', 'a cafeteira': 'die Kaffeekanne', 'o óleo': 'das Öl', 'o sabão': 'die Seife',
 'a madeira': 'das Holz; Madeira (die Insel)', 'o pau': 'der Stock, das Holzstück', 'o caco': 'die Scherbe (bolo do caco = Fladenbrot aus Madeira)', 'a placa': 'das Schild', 'o semáforo': 'die Ampel', 'o volante': 'das Lenkrad',
 'o táxi': 'das Taxi', 'o capacete': 'der Helm', 'a escada': 'die Treppe', 'o andar': 'das Stockwerk', 'os andares': 'die Stockwerke', 'a ombreira': 'der Türpfosten, der Türrahmen', 'o armazém': 'das Lager, das Lagerhaus',
 'a cafetaria': 'die Cafeteria', 'a papelaria': 'das Schreibwarengeschäft', 'o negócio': 'das Geschäft', 'o centro': 'das Zentrum', 'a câmara': 'die Kamera; das Rathaus (Câmara Municipal)', 'a estátua': 'die Statue', 'o palácio': 'der Palast',
 'o quartel': 'die Kaserne', 'a gare': 'die Bahnhofshalle', 'as instalações': 'die Räumlichkeiten, die Anlagen', 'as finanças': 'das Finanzamt; die Finanzen', 'a manifestação': 'die Demonstration', 'a eletricidade': 'der Strom, die Elektrizität',
 'o quilowatt': 'das Kilowatt', 'o quilo': 'das Kilo', 'o bónus': 'der Bonus', 'a gorjeta': 'das Trinkgeld', 'o ordenado': 'das Gehalt, der Lohn', 'a lotaria': 'die Lotterie', 'o vale': 'der Gutschein; vale = ist wert, gilt (valer)', 'o bocado': 'das Stück; die Weile (um bocado = ein bisschen)',
 'o pedacinho': 'das Stückchen', 'o par': 'das Paar (sem par = ohnegleichen)', 'o buraco': 'das Loch', 'o cimo': 'das obere Ende, die Spitze (no cimo de = oben auf)', 'a reta': 'die Gerade (reta final = Zielgerade)', 'a risca': 'der Streifen',
 'a roda': 'der Kreis; das Rad', 'o raio': 'der Umkreis, der Radius; der Blitz', 'o eco': 'das Echo', 'a melodia': 'die Melodie', 'o acordeão': 'das Akkordeon', 'a badalada': 'der Glockenschlag',
 # Kleidung, Körper, Essen
 'a camisola': 'der Pullover', 'o gorro': 'die Mütze', 'as meias': 'die Socken, die Strümpfe', 'a manga': 'der Ärmel; die Mango', 'o bolso': 'die Hosentasche, die Tasche (Kleidung)', 'o salto': 'der Sprung; der Absatz (Schuh)',
 'o pescoço': 'der Hals', 'o peito': 'die Brust', 'a testa': 'die Stirn', 'o queixo': 'das Kinn', 'a orelha': 'das Ohr', 'o bigode': 'der Schnurrbart', 'a cicatriz': 'die Narbe', 'o bafo': 'der Atem, der Hauch', 'o riso': 'das Lachen',
 'o sono': 'der Schlaf (ter sono = müde sein)', 'a saúde': 'die Gesundheit (centro de saúde = Gesundheitszentrum)', 'a medicina': 'die Medizin', 'o acidente': 'der Unfall', 'a gravidade': 'die Schwere, der Ernst (sem gravidade = nichts Ernstes)', 'a reação': 'die Reaktion',
 'o alho': 'der Knoblauch', 'a batata': 'die Kartoffel', 'o ovo': 'das Ei', 'o milho': 'der Mais', 'a canela': 'der Zimt; das Schienbein', 'a uva': 'die Traube', 'o rei': 'der König (bolo-rei = Königskuchen zu Weihnachten)',
 # Menschen, Tiere, Natur
 'o menino': 'der Junge', 'o adulto': 'der Erwachsene', 'a neta': 'die Enkelin', 'o sobrinho': 'der Neffe', 'o padre': 'der Pfarrer, der Priester', 'o condutor': 'der Fahrer', 'o turista': 'der Tourist', 'o freguês': 'der Kunde, der Stammkunde',
 'a funcionária': 'die Angestellte, die Beamtin', 'o ajudante': 'der Helfer, die Helferin', 'o instrutor': 'der Lehrer, der Trainer (Surfschule)', 'a instrutora': 'die Lehrerin, die Trainerin', 'a candidata': 'die Bewerberin', 'o candidato': 'der Bewerber',
 'a personalidade': 'die Persönlichkeit', 'o respeito': 'der Respekt', 'a convicção': 'die Überzeugung', 'a alma': 'die Seele', 'o amor': 'die Liebe', 'a felicidade': 'das Glück', 'a emoção': 'die Emotion, die Rührung', 'o elogio': 'das Lob, das Kompliment',
 'a desculpa': 'die Entschuldigung; die Ausrede', 'a ameaça': 'die Drohung', 'o defeito': 'der Fehler, der Defekt', 'a tentativa': 'der Versuch', 'a queda': 'der Sturz', 'a aventura': 'das Abenteuer', 'a vitória': 'der Sieg', 'o empate': 'das Unentschieden',
 'a guerra': 'der Krieg', 'o discurso': 'die Rede', 'o pormenor': 'das Detail, die Einzelheit', 'a estimação': 'die Wertschätzung (animal de estimação = das Haustier)', 'o friozinho': 'die leichte Kälte, das Frösteln', 'a saída': 'der Ausgang; die Abfahrt',
 'a cabra': 'die Ziege', 'a vaca': 'die Kuh', 'o leão': 'der Löwe', 'a alforreca': 'die Qualle', 'a árvore': 'der Baum', 'o pinheiro': 'die Kiefer, die Pinie', 'a relva': 'der Rasen', 'a terra': 'die Erde; das Land; der Heimatort',
 'a costa': 'die Küste', 'a baía': 'die Bucht', 'a tempestade': 'der Sturm', 'o beijo': 'der Kuss',
 # Verben (Infinitiv → die App bildet die regelmäßigen Formen; Sonderformen stehen in IRREG in index.html)
 'haver': 'geben (há = es gibt); Hilfsverb (hei de = ich werde)', 'pôr': 'stellen, legen, setzen', 'os fregueses': 'die Kunden, die Stammkunden', 'rir': 'lachen', 'fugir': 'fliehen, weglaufen', 'propor': 'vorschlagen', 'sugerir': 'vorschlagen', 'convir': 'passen, ratsam sein (convém = es ist besser)', 'reler': 'noch einmal lesen', 'agradecer': 'danken', 'doer': 'wehtun',
 'acelerar': 'beschleunigen, Gas geben', 'travar': 'bremsen', 'acertar': 'richtig treffen, richtig raten', 'admirar': 'bewundern (admira-me = es wundert mich)', 'admitir': 'zugeben; einstellen', 'afastar': 'wegschieben, entfernen (afastar-se = sich entfernen)',
 'afinar': 'stimmen (Instrument); feinabstimmen', 'agarrar': 'packen, festhalten (agarrar-se = sich festhalten)', 'apertar': 'drücken, festziehen (apertar a mão = die Hand schütteln)', 'apresentar': 'vorstellen, präsentieren', 'arrastar': 'schleppen, schleifen (arrastar-se = sich dahinschleppen)',
 'assentir': 'zustimmen, nicken', 'assustar': 'erschrecken (jemanden)', 'atrasar': 'verspäten (atrasar-se = sich verspäten)', 'baixar': 'sinken; senken; herunterladen', 'brilhar': 'glänzen, scheinen', 'calcular': 'berechnen', 'candidatar': 'sich bewerben (candidatar-se a = sich bewerben um)',
 'carregar': 'tragen, laden; drücken (carregar em = drücken auf)', 'cobrar': 'verlangen, kassieren', 'colar': 'kleben (colar-se a = sich drücken an)', 'comentar': 'kommentieren, bemerken', 'concluir': 'abschließen, schlussfolgern', 'concordar': 'zustimmen', 'discordar': 'nicht zustimmen, anderer Meinung sein',
 'considerar': 'betrachten, halten für', 'conversar': 'sich unterhalten', 'convidar': 'einladen', 'copiar': 'kopieren, abschreiben', 'descobrir': 'entdecken, herausfinden', 'desenhar': 'zeichnen', 'despedir': 'verabschieden (despedir-se = sich verabschieden); entlassen',
 'duvidar': 'zweifeln', 'emprestar': 'leihen, ausleihen', 'encostar': 'anlehnen', 'engasgar': 'sich verschlucken (engasgar-se)', 'esconder': 'verstecken', 'escorregar': 'ausrutschen', 'estender': 'ausstrecken, reichen', 'festejar': 'feiern', 'filmar': 'filmen',
 'fingir': 'so tun als ob', 'funcionar': 'funktionieren', 'inventar': 'erfinden', 'lembrar': 'erinnern (lembrar-se de = sich erinnern an)', 'limpar': 'putzen, abwischen', 'meter': 'stecken, legen (meter a terceira = den dritten Gang einlegen)', 'montar': 'aufbauen, montieren; reiten',
 'morrer': 'sterben', 'obrigar': 'zwingen', 'perdoar': 'verzeihen', 'pesar': 'wiegen; lasten', 'pescar': 'angeln, fischen', 'pousar': 'abstellen, hinlegen', 'prender': 'festhalten, festnehmen; befestigen', 'protestar': 'protestieren', 'queixar': 'sich beschweren (queixar-se de)',
 'rasgar': 'zerreißen', 'recuperar': 'sich erholen; zurückgewinnen', 'reparar': 'bemerken (reparar em); reparieren', 'a reparação': 'die Reparatur', 'riscar': 'durchstreichen', 'segurar': 'festhalten', 'servir': 'dienen; servieren; passen', 'sobreviver': 'überleben',
 'sonhar': 'träumen', 'suspirar': 'seufzen', 'terminar': 'beenden, enden', 'tremer': 'zittern', 'usar': 'benutzen; tragen', 'valer': 'wert sein; gelten', 'vender': 'verkaufen', 'vestir': 'anziehen (vestir-se = sich anziehen)', 'viajar': 'reisen', 'vibrar': 'vibrieren', 'votar': 'wählen, abstimmen',
 # Formen, die die Regeln nicht bilden: infinitivo pessoal, imperfeito do conjuntivo, Konditional, Sonstiges
 'chegares': 'du ankommst (chegar, infinitivo pessoal)', 'chegarem': 'sie ankommen (chegar, infinitivo pessoal)', 'começares': 'du anfängst (começar, infinitivo pessoal)', 'comerem': 'sie essen (comer, infinitivo pessoal)', 'escorregares': 'du ausrutschst (escorregar, infinitivo pessoal)',
 'falares': 'du sprichst (falar, infinitivo pessoal)', 'levantares': 'du aufstehst (levantar-se, infinitivo pessoal)', 'saberes': 'du weißt (saber, infinitivo pessoal)', 'voltares': 'du zurückkommst (voltar, infinitivo pessoal)',
 'acontecesse': 'geschähe, passierte (acontecer, imperfeito do conjuntivo)', 'atrasasse': 'sich verspätete (atrasar-se, imperfeito do conjuntivo)', 'baixassem': 'sie senkten (baixar, imperfeito do conjuntivo)', 'chegasse': 'ankäme (chegar, imperfeito do conjuntivo)',
 'contassem': 'sie zählten, erzählten (contar, imperfeito do conjuntivo)', 'continuasse': 'weitermachte (continuar, imperfeito do conjuntivo)', 'deixássemos': 'wir ließen (deixar, imperfeito do conjuntivo)', 'encontrasse': 'fände, träfe (encontrar, imperfeito do conjuntivo)',
 'esperasse': 'wartete (esperar, imperfeito do conjuntivo)', 'ligasse': 'anriefe (ligar, imperfeito do conjuntivo)', 'voltasse': 'zurückkäme (voltar, imperfeito do conjuntivo)',
 'gostaria': 'ich/er/sie würde gern, möchte (gostar, condicional)', 'dera': 'quem me dera = wenn ich doch nur … (dar, mais-que-perfeito)', 'esqueças': 'du vergisst (esquecer, conjuntivo: não te esqueças = vergiss nicht)',
 'doem': 'sie tun weh (doer)', 'convém': 'es passt, es ist ratsam (convir)', 'proponho': 'ich schlage vor (propor)', 'sugiro': 'ich schlage vor (sugerir)', 'foge': 'er/sie flieht, läuft weg (fugir)', 'sobem': 'sie steigen hinauf (subir)',
 'pigarreiam': 'sie räuspern sich (pigarrear)', 'comecei': 'ich fing an (começar)', 'agradeço': 'ich danke (agradecer)', 'agradeças': 'du dankst (agradecer, conjuntivo)', 'releu': 'las noch einmal (reler)', 'riu': 'lachte (rir)', 'riram': 'sie lachten (rir)',
}

out = [{'pt': k, 'de': v} for k, v in W.items()]
p = os.path.join(BASE, 'lektionen', 'leseworte.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out), 'Einträge →', os.path.relpath(p, BASE))
