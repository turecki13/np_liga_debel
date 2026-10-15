"""Warstwa dostępu do Google Sheets (gspread + konto serwisowe)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

import config

# Plik do lokalnego podglądu (gdy brak Google Sheets) — tylko do odczytu.
_LOCAL = Path(__file__).parent / "Liga_Debel_DANE.xlsx"


def dane_lokalne() -> bool:
    """True gdy nie ma Google Sheets, ale jest lokalny plik z danymi (podgląd)."""
    return (not skonfigurowane()) and _LOCAL.exists()


def _wczytaj_lokalne(zakladka: str) -> list[dict]:
    import openpyxl
    try:
        wb = openpyxl.load_workbook(_LOCAL, read_only=True, data_only=True)
        ws = wb[zakladka]
        wiersze = list(ws.iter_rows(values_only=True))
        if not wiersze:
            return []
        head = [str(h) for h in wiersze[0]]
        out = []
        for r in wiersze[1:]:
            if all(c is None for c in r):
                continue
            out.append({head[i]: ("" if r[i] is None else r[i]) for i in range(len(head))})
        return out
    except Exception:
        return []


def _lok_otworz():
    import openpyxl
    return openpyxl.load_workbook(_LOCAL)


def _lok_znajdz(ws, kol_id: str, wartosc):
    head = [c.value for c in ws[1]]
    if kol_id not in head:
        return None, head
    idx = head.index(kol_id)
    for r in range(2, ws.max_row + 1):
        if str(ws.cell(row=r, column=idx + 1).value).strip() == str(wartosc).strip():
            return r, head
    return None, head


def _lok_append(zakladka: str, naglowki: list[str], rowdict: dict) -> None:
    wb = _lok_otworz()
    ws = wb[zakladka]
    ws.append([str(rowdict.get(k, "")) for k in naglowki])
    wb.save(_LOCAL)
    wyczysc_cache()


def _lok_update(zakladka: str, kol_id: str, idval, zmiany: dict) -> None:
    wb = _lok_otworz()
    ws = wb[zakladka]
    r, head = _lok_znajdz(ws, kol_id, idval)
    if r is None:
        raise ValueError(f"Nie znaleziono {kol_id}={idval} w {zakladka}.")
    for k, v in zmiany.items():
        if k in head:
            ws.cell(row=r, column=head.index(k) + 1, value=str(v))
    wb.save(_LOCAL)
    wyczysc_cache()


def _lok_delete(zakladka: str, kol_id: str, idval) -> None:
    wb = _lok_otworz()
    ws = wb[zakladka]
    r, _ = _lok_znajdz(ws, kol_id, idval)
    if r:
        ws.delete_rows(r)
    wb.save(_LOCAL)
    wyczysc_cache()


def skonfigurowane() -> bool:
    try:
        return (
            "gcp_service_account" in st.secrets
            and "google_sheets" in st.secrets
            and st.secrets["google_sheets"].get("spreadsheet_id")
        )
    except Exception:
        return False


def haslo_admina() -> str | None:
    try:
        return st.secrets["admin"]["password"]
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def _klient():
    import gspread
    from google.oauth2.service_account import Credentials

    zakresy = ["https://www.googleapis.com/auth/spreadsheets"]
    dane = dict(st.secrets["gcp_service_account"])
    poswiadczenia = Credentials.from_service_account_info(dane, scopes=zakresy)
    return gspread.authorize(poswiadczenia)


@st.cache_resource(show_spinner=False)
def _arkusz():
    return _klient().open_by_key(st.secrets["google_sheets"]["spreadsheet_id"])


def _ws(nazwa: str):
    return _arkusz().worksheet(nazwa)


# --- Odczyt (krótki cache) -------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def pobierz_mecze() -> list[dict]:
    if skonfigurowane():
        return _ws(config.WS_MECZE).get_all_records()
    if dane_lokalne():
        return _wczytaj_lokalne(config.WS_MECZE)
    return []


@st.cache_data(ttl=30, show_spinner=False)
def pobierz_zgloszenia() -> list[dict]:
    if skonfigurowane():
        return _ws(config.WS_ZGLOSZENIA).get_all_records()
    if dane_lokalne():
        return _wczytaj_lokalne(config.WS_ZGLOSZENIA)
    return []


@st.cache_data(ttl=30, show_spinner=False)
def pobierz_fairplay() -> list[dict]:
    try:
        if skonfigurowane():
            return _ws(config.WS_FAIRPLAY).get_all_records()
        if dane_lokalne():
            return _wczytaj_lokalne(config.WS_FAIRPLAY)
    except Exception:
        pass
    return []


@st.cache_data(ttl=30, show_spinner=False)
def pobierz_oceny() -> list[dict]:
    try:
        if skonfigurowane():
            return _ws(config.WS_FAIRPLAY_OCENY).get_all_records()
        if dane_lokalne():
            return _wczytaj_lokalne(config.WS_FAIRPLAY_OCENY)
    except Exception:
        pass
    return []


@st.cache_data(ttl=30, show_spinner=False)
def pobierz_ustawienia() -> dict:
    try:
        if skonfigurowane():
            rows = _ws(config.WS_USTAWIENIA).get_all_records()
        elif dane_lokalne():
            rows = _wczytaj_lokalne(config.WS_USTAWIENIA)
        else:
            rows = []
        return {str(r.get("Klucz", "")).strip(): str(r.get("Wartosc", "")).strip() for r in rows}
    except Exception:
        return {}


def wyczysc_cache() -> None:
    pobierz_mecze.clear()
    pobierz_zgloszenia.clear()
    pobierz_fairplay.clear()
    pobierz_oceny.clear()
    pobierz_ustawienia.clear()


def _ws_lub_utworz(nazwa: str, naglowki: list[str]):
    ar = _arkusz()
    try:
        return ar.worksheet(nazwa)
    except Exception:
        ws = ar.add_worksheet(title=nazwa, rows=200, cols=max(10, len(naglowki)))
        ws.update([naglowki], "A1", value_input_option="RAW")
        return ws


# --- Zapis -----------------------------------------------------------------
def _indeks_kolumny(naglowki: list[str], nazwa: str) -> int:
    return naglowki.index(nazwa) + 1


def _znajdz_wiersz(ws, kolumna_id: str, wartosc: str) -> int | None:
    wartosci = ws.get_all_values()
    if not wartosci:
        return None
    naglowki = wartosci[0]
    if kolumna_id not in naglowki:
        return None
    idx = naglowki.index(kolumna_id)
    for nr, wiersz in enumerate(wartosci[1:], start=2):
        if idx < len(wiersz) and str(wiersz[idx]).strip() == str(wartosc).strip():
            return nr
    return None


def dodaj_zgloszenie(z: dict) -> None:
    if dane_lokalne():
        _lok_append(config.WS_ZGLOSZENIA, config.KOL_ZGLOSZENIA, z)
        return
    ws = _ws(config.WS_ZGLOSZENIA)
    wiersz = [str(z.get(kol, "")) for kol in config.KOL_ZGLOSZENIA]
    ws.append_row(wiersz, value_input_option="RAW")
    wyczysc_cache()


def dodaj_ocene(o: dict) -> None:
    if dane_lokalne():
        _lok_append(config.WS_FAIRPLAY_OCENY, config.KOL_FAIRPLAY_OCENY, o)
        return
    ws = _ws_lub_utworz(config.WS_FAIRPLAY_OCENY, config.KOL_FAIRPLAY_OCENY)
    wiersz = [str(o.get(kol, "")) for kol in config.KOL_FAIRPLAY_OCENY]
    ws.append_row(wiersz, value_input_option="RAW")
    wyczysc_cache()


def usun_ocene(ocena_id: str) -> None:
    if dane_lokalne():
        _lok_delete(config.WS_FAIRPLAY_OCENY, "ID", ocena_id)
        return
    ws = _ws(config.WS_FAIRPLAY_OCENY)
    nr = _znajdz_wiersz(ws, "ID", ocena_id)
    if nr is None:
        raise ValueError("Nie znaleziono oceny do usunięcia.")
    ws.delete_rows(nr)
    wyczysc_cache()


def zapisz_wynik(mecz_id: str, set1: str = "", set2: str = "",
                 super_tb: str = "", wynik: str = "") -> None:
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M")
    zmiany = {"Set1": set1, "Set2": set2, "SuperTB": super_tb,
              "Wynik": wynik, "Zatwierdzono": teraz}
    if dane_lokalne():
        _lok_update(config.WS_MECZE, "ID", mecz_id, zmiany)
        return
    ws_m = _ws(config.WS_MECZE)
    nr = _znajdz_wiersz(ws_m, "ID", mecz_id)
    if nr is None:
        raise ValueError(f"Nie znaleziono meczu o ID {mecz_id}.")
    _aktualizuj(ws_m, config.KOL_MECZE, nr, zmiany)
    wyczysc_cache()


def wyczysc_wynik(mecz_id: str) -> None:
    puste = {"Set1": "", "Set2": "", "SuperTB": "", "Wynik": "", "Zatwierdzono": ""}
    if dane_lokalne():
        _lok_update(config.WS_MECZE, "ID", mecz_id, puste)
        return
    ws_m = _ws(config.WS_MECZE)
    nr = _znajdz_wiersz(ws_m, "ID", mecz_id)
    if nr is None:
        raise ValueError(f"Nie znaleziono meczu o ID {mecz_id}.")
    _aktualizuj(ws_m, config.KOL_MECZE, nr, puste)
    wyczysc_cache()


def ustaw_ustawienie(klucz: str, wartosc) -> None:
    if dane_lokalne():
        wb = _lok_otworz()
        ws = wb[config.WS_USTAWIENIA]
        r, head = _lok_znajdz(ws, "Klucz", klucz)
        if r is not None:
            ws.cell(row=r, column=head.index("Wartosc") + 1, value=str(wartosc))
        else:
            ws.append([str(klucz), str(wartosc)])
        wb.save(_LOCAL)
        wyczysc_cache()
        return
    ws = _ws_lub_utworz(config.WS_USTAWIENIA, config.KOL_USTAWIENIA)
    nr = _znajdz_wiersz(ws, "Klucz", klucz)
    if nr is not None:
        _aktualizuj(ws, config.KOL_USTAWIENIA, nr, {"Wartosc": str(wartosc)})
    else:
        ws.append_row([str(klucz), str(wartosc)], value_input_option="RAW")
    wyczysc_cache()


def _aktualizuj(ws, naglowki: list[str], nr_wiersza: int, zmiany: dict) -> None:
    import gspread

    komorki = [
        gspread.Cell(nr_wiersza, _indeks_kolumny(naglowki, kol), str(wartosc))
        for kol, wartosc in zmiany.items()
    ]
    ws.update_cells(komorki, value_input_option="RAW")


def akceptuj_zgloszenie(zgloszenie: dict) -> None:
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M")
    if dane_lokalne():
        _lok_update(config.WS_MECZE, "ID", zgloszenie["MeczID"], {
            "Set1": zgloszenie.get("Set1", ""),
            "Set2": zgloszenie.get("Set2", ""),
            "SuperTB": zgloszenie.get("SuperTB", ""),
            "Wynik": zgloszenie.get("Wynik", ""),
            "Zatwierdzono": teraz,
        })
        try:
            _lok_update(config.WS_ZGLOSZENIA, "ID", zgloszenie["ID"], {
                "Status": config.STATUS_ZAAKCEPTOWANE, "Rozpatrzono": teraz,
            })
        except ValueError:
            pass
        return
    ws_m = _ws(config.WS_MECZE)
    nr_m = _znajdz_wiersz(ws_m, "ID", zgloszenie["MeczID"])
    if nr_m is None:
        raise ValueError(f"Nie znaleziono meczu o ID {zgloszenie['MeczID']}.")
    _aktualizuj(ws_m, config.KOL_MECZE, nr_m, {
        "Set1": zgloszenie.get("Set1", ""),
        "Set2": zgloszenie.get("Set2", ""),
        "SuperTB": zgloszenie.get("SuperTB", ""),
        "Wynik": zgloszenie.get("Wynik", ""),
        "Zatwierdzono": teraz,
    })
    ws_z = _ws(config.WS_ZGLOSZENIA)
    nr_z = _znajdz_wiersz(ws_z, "ID", zgloszenie["ID"])
    if nr_z is not None:
        _aktualizuj(ws_z, config.KOL_ZGLOSZENIA, nr_z, {
            "Status": config.STATUS_ZAAKCEPTOWANE, "Rozpatrzono": teraz,
        })
    wyczysc_cache()


def odrzuc_zgloszenie(zgloszenie: dict) -> None:
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M")
    if dane_lokalne():
        _lok_update(config.WS_ZGLOSZENIA, "ID", zgloszenie["ID"], {
            "Status": config.STATUS_ODRZUCONE, "Rozpatrzono": teraz,
        })
        return
    ws_z = _ws(config.WS_ZGLOSZENIA)
    nr_z = _znajdz_wiersz(ws_z, "ID", zgloszenie["ID"])
    if nr_z is None:
        raise ValueError("Nie znaleziono zgłoszenia.")
    _aktualizuj(ws_z, config.KOL_ZGLOSZENIA, nr_z, {
        "Status": config.STATUS_ODRZUCONE, "Rozpatrzono": teraz,
    })
    wyczysc_cache()
