"""Szybkie testy logiki ligi deblowej (python test_logic.py)."""

from liga_logic import BladWyniku, oblicz_mecz, oblicz_tabele, set_poprawny, super_tb_poprawny

bledy = []


def sprawdz(opis, war):
    print(("OK  " if war else "BLAD") + "  " + opis)
    if not war:
        bledy.append(opis)


def oczekuj_blad(opis, *a):
    try:
        oblicz_mecz(*a)
        sprawdz(opis + " (mial byc blad)", False)
    except BladWyniku:
        sprawdz(opis, True)


sprawdz("6:4 ok", set_poprawny(6, 4))
sprawdz("6:5 zle", not set_poprawny(6, 5))
sprawdz("super 10:7 ok", super_tb_poprawny(10, 7))
sprawdz("super 10:9 zle", not super_tb_poprawny(10, 9))

r = oblicz_mecz("6:4", "6:2")
sprawdz("2:0 gospodarz, gemy 12:6", r["wynik"] == "2:0" and r["gemy_g"] == 12 and r["gemy_o"] == 6)
r = oblicz_mecz("6:4", "3:6", "10:7")
sprawdz("2:1 przez super TB, gemy 9:10", r["wynik"] == "2:1" and r["gemy_g"] == 9 and r["gemy_o"] == 10)
oczekuj_blad("super TB przy 2:0 odrzucony", "6:4", "6:2", "10:5")
oczekuj_blad("brak super TB przy 1:1 odrzucony", "6:4", "3:6", "")

# tabela par: punktacja 3/1
mecze = [
    {"Gospodarz": "A/B", "Gość": "C/D", "Set1": "6:4", "Set2": "6:2", "SuperTB": ""},
    {"Gospodarz": "A/B", "Gość": "E/F", "Set1": "2:6", "Set2": "1:6", "SuperTB": ""},
]
t = oblicz_tabele(mecze)
sprawdz("kolumna 'Para' istnieje", "Para" in t.columns)
ab = t[t.Para == "A/B"].iloc[0]
sprawdz("A/B: 1W+1P = 4 pkt", int(ab["Punkty"]) == 4 and int(ab["Wygrane"]) == 1 and int(ab["Przegrane"]) == 1)
cd = t[t.Para == "C/D"].iloc[0]
sprawdz("C/D: porazka = 1 pkt", int(cd["Punkty"]) == 1)

# walkower: zwyciezca 3, oddajacy 0
tw = oblicz_tabele([
    {"Gospodarz": "X/Y", "Gość": "Z/W", "Wynik": "walkower:gosp", "Set1": "", "Set2": "", "SuperTB": ""},
])
sprawdz("walkower: X/Y 3 pkt", int(tw[tw.Para == "X/Y"].iloc[0]["Punkty"]) == 3)
sprawdz("walkower: Z/W 0 pkt", int(tw[tw.Para == "Z/W"].iloc[0]["Punkty"]) == 0)

print()
if bledy:
    print(f"NIEPOWODZENIA: {len(bledy)}")
    raise SystemExit(1)
print("Wszystkie testy przeszly OK")
