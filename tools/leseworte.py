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
}

out = [{'pt': k, 'de': v} for k, v in W.items()]
p = os.path.join(BASE, 'lektionen', 'leseworte.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out), 'Einträge →', os.path.relpath(p, BASE))
