"""
Jednorazowe utworzenie pustych zakładek w arkuszu Google (z nagłówkami).
Zwykle NIE jest potrzebne — wystarczy zaimportować Liga_Debel_DANE.xlsx
(ma już wszystkie zakładki i dane). Przydatne, gdy budujesz arkusz od zera.

Użycie (po skonfigurowaniu .streamlit/secrets.toml):
    python seed_sheets.py
"""

from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import config

SECRETS = Path(__file__).parent / ".streamlit" / "secrets.toml"


def main():
    if not SECRETS.exists():
        raise SystemExit("Brak .streamlit/secrets.toml – najpierw skonfiguruj sekrety (README).")
    with open(SECRETS, "rb") as f:
        sek = tomllib.load(f)
    creds = Credentials.from_service_account_info(
        sek["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
    arkusz = gspread.authorize(creds).open_by_key(sek["google_sheets"]["spreadsheet_id"])

    zakladki = {
        config.WS_MECZE: config.KOL_MECZE,
        config.WS_ZGLOSZENIA: config.KOL_ZGLOSZENIA,
        config.WS_FAIRPLAY: config.KOL_FAIRPLAY,
        config.WS_FAIRPLAY_OCENY: config.KOL_FAIRPLAY_OCENY,
        config.WS_USTAWIENIA: config.KOL_USTAWIENIA,
    }
    for nazwa, naglowki in zakladki.items():
        try:
            ws = arkusz.worksheet(nazwa)
        except gspread.WorksheetNotFound:
            ws = arkusz.add_worksheet(title=nazwa, rows=200, cols=max(10, len(naglowki)))
        if ws.row_values(1) != naglowki:
            ws.update([naglowki], "A1", value_input_option="RAW")
        print("OK:", nazwa)
    print("Gotowe.")


if __name__ == "__main__":
    main()
