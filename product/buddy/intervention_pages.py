"""Actionable intervention detail pages (Dutch, coaching, no medical claims)."""

from __future__ import annotations

from typing import Any

# Theme keys match intervention "theme" in the persona fixtures.

MOVEMENT_GRONINGEN: dict[str, Any] = {
    "theme": "sport",
    "kicker": "Beweging · Groningen",
    "title": "Rondje plantsoen, grachten en Martinitoren",
    "coach": (
        "Geen schema voor atleten — een rondje dat je kunt onthouden. "
        "Groen, water, en de toren als herkenningspunt. Trek je jas aan en begin klein."
    ),
    "why": "Wandelen hoort bij je gewicht en taille. Geen schema, geen recept.",
    "when": "Het liefst na een maaltijd, drie keer deze week — dezelfde schoenen, hetzelfde startpunt.",
    "duration": "30–45 minuten (ongeveer 3,5 km). Liever 25 minuten volhouden dan 60 minuten uitstellen.",
    "intensity": "Stevig wandeltempo: je kunt nog praten, je hoeft niet te hijgen. Bankjes onderweg zijn oké.",
    "route_name": "Plantsoen, gracht, Martinitoren",
    "route_steps": [
        "Start bij de hoofdingang van het Noorderplantsoen (Kruissingel / Oranjesingel).",
        "Loop het park rond: blijf bij de vijver en de grote bomen, met de klok mee.",
        "Verlaat het plantsoen richting de Noorderhaven en volg het water de stad in.",
        "Houd de Diepenring aan tot je de Martinitoren goed ziet (Vismarkt / Grote Markt-kant).",
        "Keer terug via de Nieuwe Ebbingestraat of Boteringestraat naar het plantsoen — rondje afmaken.",
    ],
    "tip": "Regendag? Doe alleen het plantsoenrondje (15–20 min) en streep de week niet weg.",
}

FOOD_PAGE: dict[str, Any] = {
    "theme": "food",
    "kicker": "Voeding · één vaste wissel",
    "title": "Eén suikerdrank minder, dezelfde koffieafspraak",
    "coach": (
        "Niet een heel dieet omgooien. Kies één vast moment — bijvoorbeeld de middag op het Forum "
        "of thuis na het eten — en wissel het suikerdrankje in voor water of thee zonder suiker."
    ),
    "why": "Minder suikerdrank en rustig eten horen bij gewicht en taille. Geen dieet.",
    "when": "Kies één vast moment per dag, zeven dagen achter elkaar.",
    "duration": "De wissel zelf duurt geen extra tijd — alleen de keuze.",
    "intensity": "Klein en saai is beter dan streng en kort.",
    "route_name": "Zo pak je de week",
    "route_steps": [
        "Schrijf op welk drankje je meestal neemt (frisdrank, sap, zoete koffie).",
        "Zet het alternatief al klaar: fles water of thee zonder suiker.",
        "Kies het moment dat het vaakst misgaat — middagdip of ná het eten.",
        "Vink zeven dagen af. Pas daarna mag je een tweede wissel bedenken.",
        "Eet in rust: bord op tafel, niet staand bij de koelkast.",
    ],
    "tip": "Uit eten? Zelfde regel: één drankje zonder suiker, de rest van de afspraak blijft hetzelfde.",
}

SLEEP_PAGE: dict[str, Any] = {
    "theme": "sleep",
    "kicker": "Slaap · vast ritueel",
    "title": "Telefoon de kamer uit, dezelfde bedtijd",
    "coach": (
        "Slaap is geen prestatie. Een vast avondritueel maakt de dag kleiner, "
        "niet perfecter."
    ),
    "why": "Een rustiger avond hoort bij je slaap. Geen slaaprecept.",
    "when": "Dertig minuten voor je gekozen bedtijd, vijf avonden deze week.",
    "duration": "30 minuten schermvrij — niet meer.",
    "intensity": "Licht dimmen, geen extra oefeningen verplicht.",
    "route_name": "Avondritueel",
    "route_steps": [
        "Kies een bedtijd die je twee avonden achter elkaar kunt herhalen.",
        "Leg de telefoon in een andere kamer, niet op het nachtkastje.",
        "Zet een wekker in die andere kamer — ochtend telt ook.",
        "Doe één rustig ding: thee, boek, of alleen het licht lager.",
        "Late avond gehad? Volgende nacht dezelfde tijd, niet uitslapen tot de middag.",
    ],
    "tip": "Lukt vijf avonden niet? Begin met woensdag tot en met vrijdag. Weekend mag later.",
}

SMOKING_PAGE: dict[str, Any] = {
    "theme": "smoking",
    "kicker": "Rookvrij · twee blokken",
    "title": "Twee rookvrije dagen die je zelf kiest",
    "coach": (
        "Geen stoppen-met-roken-kuur hier. Wel twee blokken die je vooraf kiest. "
        "Hulpmiddelen en ontwenning horen bij je zorgteam."
    ),
    "why": "Twee dagen zonder sigaret. Coaching, geen behandeling.",
    "when": "Twee dagen die je van tevoren in je agenda zet.",
    "duration": "De hele dag rookvrij — of twee vaste blokken van vier uur als een hele dag te groot is.",
    "intensity": "Geen wedstrijd met jezelf. Kies dagen waarop de fietsrit al staat.",
    "route_name": "Zo kies je de blokken",
    "route_steps": [
        "Kies twee dagen (bijvoorbeeld dinsdag en donderdag).",
        "Bescherm de fietsrit of wandeling op die dagen — handen en hoofd hebben iets anders te doen.",
        "Zet kauwgom, water of een korte ommetje klaar voor het gebruikelijke moment.",
        "Vertel één persoon welke dagen het zijn.",
        "Wil je verder stoppen? Dat gesprek is voor je arts of praktijkondersteuner.",
    ],
    "tip": "Een uitglijder is geen reset. De volgende gekozen dag telt gewoon weer.",
}

ALCOHOL_PAGE: dict[str, Any] = {
    "theme": "alcohol",
    "kicker": "Alcohol · twee avonden",
    "title": "Twee doordeweekse avonden zonder alcohol",
    "coach": (
        "Geen verbod. Twee avonden met bruiswater dat je echt lust, "
        "zodat de rest van de week herkenbaar blijft."
    ),
    "why": "Twee avonden zonder alcohol. Geen behandeling.",
    "when": "Twee doordeweekse avonden, vooraf gekozen.",
    "duration": "De avond zelf — vanaf thuiskomen tot slapen.",
    "intensity": "Laag. Weekend mag het oude patroon zijn tot deze twee avonden vanzelfsprekend voelen.",
    "route_name": "Avond zonder glas",
    "route_steps": [
        "Zet woensdag en donderdag (of twee andere avonden) in de agenda.",
        "Zet het alternatief al klaar: bruiswater, thee, of een glas dat je mooi vindt.",
        "Houd de rest van de avond hetzelfde: eten, serie, bedtijd.",
        "Boodschap gedaan? Koop die twee avonden geen extra fles ‘voor het geval dat’.",
        "Vragen over minderen of stoppen horen bij je zorgverlener, niet bij Boris.",
    ],
    "tip": "Eén avond gelukt is winst. Tel niet meteen de hele maand.",
}

GENERIC_STUB: dict[str, Any] = {
    "theme": "generic",
    "kicker": "Kleine stap",
    "title": "Eén kleine herhaalbare stap",
    "coach": "Kies één ding dat je morgen opnieuw kunt doen. Geen schema, geen kuur.",
    "why": "Eén kleine stap die je morgen opnieuw kunt doen.",
    "when": "Morgen, op een vast tijdstip.",
    "duration": "Tien minuten is genoeg om te starten.",
    "intensity": "Laag. Herhalen telt meer dan zwaar.",
    "route_name": "Eerste stap",
    "route_steps": [
        "Kies één gewoonte die al een beetje lukt.",
        "Herhaal die morgen op hetzelfde moment.",
    ],
    "tip": "Geen medisch advies — praat met je zorgverlener over klachten of medicijnen.",
}

PAGES = {
    "sport": MOVEMENT_GRONINGEN,
    "food": FOOD_PAGE,
    "sleep": SLEEP_PAGE,
    "smoking": SMOKING_PAGE,
    "alcohol": ALCOHOL_PAGE,
}


def get_intervention_page(theme: str) -> dict[str, Any]:
    return PAGES.get(theme) or {**GENERIC_STUB, "theme": theme}
