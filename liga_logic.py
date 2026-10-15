"""
Czysta logika ligi deblowej (bez Streamlit i Google Sheets) — łatwa do testów.
"Para" = zespół dwóch zawodników, grający jako całość.

Zasady (jak w lidze singlowej NP):
- Mecz do 2 wygranych setów; przy 1:1 super tie-break do 10 (przewaga min. 2).
- Set: 6:0–6:4, 7:5, 7:6.
- Zwycięstwo = 3 pkt, porażka = 1 pkt. Walkower: zwycięzca 3 pkt, oddający 0.
- Kolejność: punkty → bezpośredni pojedynek (2 pary) → różnica setów → różnica gemów.
"""

from __future__ import annotations

import pandas as pd


class BladWyniku(ValueError):
    """Wyjątek zgłaszany przy niepoprawnym wyniku meczu."""


def parsuj_pare(tekst: str) -> tuple[int, int]:
    if tekst is None:
        raise BladWyniku("Brak wyniku.")
    surowy = str(tekst).strip().replace("-", ":").replace(" ", ":")
    czesci = [c for c in surowy.split(":") if c != ""]
    if len(czesci) != 2:
        raise BladWyniku(f"Niepoprawny format: '{tekst}'. Użyj np. 6:4.")
    try:
        a, b = int(czesci[0]), int(czesci[1])
    except ValueError:
        raise BladWyniku(f"Wynik musi być liczbami: '{tekst}'.")
    if a < 0 or b < 0:
        raise BladWyniku(f"Wynik nie może być ujemny: '{tekst}'.")
    return a, b


def set_poprawny(g: int, o: int) -> bool:
    wyzszy, nizszy = max(g, o), min(g, o)
    if g == o:
        return False
    if wyzszy == 6 and 0 <= nizszy <= 4:
        return True
    if wyzszy == 7 and nizszy in (5, 6):
        return True
    return False


def super_tb_poprawny(g: int, o: int) -> bool:
    return g != o and max(g, o) >= 10 and abs(g - o) >= 2


def oblicz_mecz(set1: str, set2: str, super_tb: str | None = None) -> dict:
    """Liczy wynik meczu z perspektywy GOSPODARZA (pary gospodarzy)."""
    g1, o1 = parsuj_pare(set1)
    g2, o2 = parsuj_pare(set2)
    if not set_poprawny(g1, o1):
        raise BladWyniku(f"Set 1 ({g1}:{o1}) jest niepoprawny. Dozwolone: 6:0–6:4, 7:5, 7:6.")
    if not set_poprawny(g2, o2):
        raise BladWyniku(f"Set 2 ({g2}:{o2}) jest niepoprawny. Dozwolone: 6:0–6:4, 7:5, 7:6.")

    gemy_g, gemy_o = g1 + g2, o1 + o2
    wygral_g_1 = g1 > o1
    wygral_g_2 = g2 > o2
    ma_super_tb = super_tb not in (None, "", " ")

    if wygral_g_1 == wygral_g_2:
        if ma_super_tb:
            raise BladWyniku("Przy wyniku 2:0 nie podaje się super tie-breaka.")
        if wygral_g_1:
            return {"wynik": "2:0", "sety_g": 2, "sety_o": 0,
                    "gemy_g": gemy_g, "gemy_o": gemy_o, "zwyciezca": "gospodarz"}
        return {"wynik": "0:2", "sety_g": 0, "sety_o": 2,
                "gemy_g": gemy_g, "gemy_o": gemy_o, "zwyciezca": "gosc"}

    if not ma_super_tb:
        raise BladWyniku("Przy stanie 1:1 w setach podaj super tie-break do 10 (np. 10:7).")
    gt, ot = parsuj_pare(super_tb)
    if not super_tb_poprawny(gt, ot):
        raise BladWyniku(f"Super tie-break ({gt}:{ot}) jest niepoprawny. Do 10, przewaga min. 2 (np. 10:7).")

    if gt > ot:
        return {"wynik": "2:1", "sety_g": 2, "sety_o": 1,
                "gemy_g": gemy_g, "gemy_o": gemy_o, "zwyciezca": "gospodarz"}
    return {"wynik": "1:2", "sety_g": 1, "sety_o": 2,
            "gemy_g": gemy_g, "gemy_o": gemy_o, "zwyciezca": "gosc"}


def oblicz_tabele(mecze: list[dict]) -> pd.DataFrame:
    """Buduje tabelę par z listy zatwierdzonych meczów (Gospodarz/Gość = pary)."""
    stat: dict[str, dict] = {}
    h2h: dict[tuple[str, str], int] = {}

    def para(nazwa: str) -> dict:
        return stat.setdefault(
            nazwa,
            {"Para": nazwa, "Mecze": 0, "Wygrane": 0, "Przegrane": 0,
             "Sety wygrane": 0, "Sety przegrane": 0,
             "Gemy wygrane": 0, "Gemy przegrane": 0, "Punkty": 0},
        )

    for m in mecze:
        gosp = str(m.get("Gospodarz", "")).strip()
        gosc = str(m.get("Gość", "")).strip()
        if not gosp or not gosc:
            continue

        wynik_txt = str(m.get("Wynik", "")).strip().lower()
        if wynik_txt.startswith("walkower"):
            zw = "gosc" if wynik_txt.endswith("gosc") else "gospodarz"
            g, o = para(gosp), para(gosc)
            g["Mecze"] += 1
            o["Mecze"] += 1
            if zw == "gospodarz":
                g["Wygrane"] += 1
                g["Punkty"] += 3
                o["Przegrane"] += 1  # oddający walkower: 0 pkt
                h2h[(gosp, gosc)] = h2h.get((gosp, gosc), 0) + 1
            else:
                o["Wygrane"] += 1
                o["Punkty"] += 3
                g["Przegrane"] += 1
                h2h[(gosc, gosp)] = h2h.get((gosc, gosp), 0) + 1
            continue

        try:
            wynik = oblicz_mecz(m.get("Set1", ""), m.get("Set2", ""), m.get("SuperTB", ""))
        except BladWyniku:
            continue

        g, o = para(gosp), para(gosc)
        g["Mecze"] += 1
        o["Mecze"] += 1
        g["Sety wygrane"] += wynik["sety_g"]
        g["Sety przegrane"] += wynik["sety_o"]
        o["Sety wygrane"] += wynik["sety_o"]
        o["Sety przegrane"] += wynik["sety_g"]
        g["Gemy wygrane"] += wynik["gemy_g"]
        g["Gemy przegrane"] += wynik["gemy_o"]
        o["Gemy wygrane"] += wynik["gemy_o"]
        o["Gemy przegrane"] += wynik["gemy_g"]
        if wynik["zwyciezca"] == "gospodarz":
            g["Wygrane"] += 1
            g["Punkty"] += 3
            o["Przegrane"] += 1
            o["Punkty"] += 1
            h2h[(gosp, gosc)] = h2h.get((gosp, gosc), 0) + 1
        else:
            o["Wygrane"] += 1
            o["Punkty"] += 3
            g["Przegrane"] += 1
            g["Punkty"] += 1
            h2h[(gosc, gosp)] = h2h.get((gosc, gosp), 0) + 1

    kolumny = ["Para", "Mecze", "Wygrane", "Przegrane",
               "Sety wygrane", "Sety przegrane",
               "Gemy wygrane", "Gemy przegrane", "Punkty"]
    if not stat:
        return pd.DataFrame(columns=kolumny)

    for p in stat.values():
        p["_sety"] = p["Sety wygrane"] - p["Sety przegrane"]
        p["_gemy"] = p["Gemy wygrane"] - p["Gemy przegrane"]

    def klucz_roznic(p):
        return (p["_sety"], p["_gemy"])

    pary = sorted(stat.values(), key=lambda p: p["Punkty"], reverse=True)
    uporzadkowane: list[dict] = []
    i = 0
    while i < len(pary):
        j = i
        while j < len(pary) and pary[j]["Punkty"] == pary[i]["Punkty"]:
            j += 1
        grupa = pary[i:j]
        if len(grupa) == 2:
            a, b = grupa
            wa = h2h.get((a["Para"], b["Para"]), 0)
            wb = h2h.get((b["Para"], a["Para"]), 0)
            if wa != wb:
                grupa = [a, b] if wa > wb else [b, a]
            else:
                grupa = sorted(grupa, key=klucz_roznic, reverse=True)
        else:
            grupa = sorted(grupa, key=klucz_roznic, reverse=True)
        uporzadkowane.extend(grupa)
        i = j

    df = pd.DataFrame(uporzadkowane).reset_index(drop=True)
    return df[kolumny]
