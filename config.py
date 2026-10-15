"""Wspólna konfiguracja ligi deblowej/mikstowej."""

# W tej rundzie tworzymy wyłącznie ligę mikstową, podzieloną na 2 grupy.
LIGI: dict[str, str] = {
    "1": "Liga 1",
    "2": "Liga 2",
}

# Informacje o rundzie (osobne zapisy na każdą rundę).
RUNDA = "Runda 1"
RUNDA_TERMIN = "16.10.2026 – 15.01.2027"
RUNDA2_TERMIN = "01.02.2027 – 30.04.2027"
SEZON = "Sezon deblowo-mikstowy 2026/2027"

# Zakładki (worksheety) w arkuszu Google.
WS_MECZE = "mecze"
WS_ZGLOSZENIA = "zgloszenia"
WS_FAIRPLAY = "fairplay"
WS_FAIRPLAY_OCENY = "fairplay_oceny"
WS_USTAWIENIA = "ustawienia"

# Kolumny. UWAGA: brak kolejek i dat meczów — umawiacie się sami w oknie rundy.
# "Gospodarz" i "Gość" to PARY (np. "Jan Kowalski / Anna Nowak").
KOL_MECZE = [
    "ID", "Liga", "Gospodarz", "Gość", "Set1", "Set2", "SuperTB", "Wynik", "Zatwierdzono",
]
KOL_ZGLOSZENIA = [
    "ID", "Czas", "MeczID", "Liga", "Gospodarz", "Gość",
    "Set1", "Set2", "SuperTB", "Wynik", "Status", "Rozpatrzono",
]
KOL_FAIRPLAY = ["Para", "Liga", "Punkty Fair Play"]
KOL_FAIRPLAY_OCENY = [
    "ID", "Czas", "MeczID", "Liga", "Oceniający", "Oceniany", "Ocena", "Komentarz",
]
KOL_USTAWIENIA = ["Klucz", "Wartosc"]

# Oznaczenia walkowera w kolumnie "Wynik" (zwycięzca: gospodarz / gość)
WALKOWER_G = "walkower:gosp"
WALKOWER_S = "walkower:gosc"

# Statusy zgłoszeń
STATUS_OCZEKUJE = "oczekuje"
STATUS_ZAAKCEPTOWANE = "zaakceptowane"
STATUS_ODRZUCONE = "odrzucone"
