"""
Liga Deblowo-Mikstowa NP Tennis Academy – strona (Streamlit) z samodzielnym
zgłaszaniem wyników, trybem akceptacji, tabelami par i klasyfikacją Fair Play.

BEZ kalendarza kolejek – pary umawiają się same w oknie całej rundy.
"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

import config
import liga_logic
import sheets

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGO_DIR = BASE_DIR / "logo"
LOGO_POZIOME = LOGO_DIR / "logo 2.png"
LOGO_PIONOWE = LOGO_DIR / "logo 1.png"

LIGI_MENU = {f"🎾 {nazwa}": nazwa for nazwa in config.LIGI.values()}

st.set_page_config(
    page_title="Liga Deblowa NP Tennis Academy",
    page_icon=str(LOGO_PIONOWE) if LOGO_PIONOWE.exists() else "🎾",
    layout="wide",
)

if LOGO_POZIOME.exists():
    st.logo(str(LOGO_POZIOME), icon_image=str(LOGO_PIONOWE), size="large")

OCENY_FP = {
    1: "🟢 +1 — bardzo sportowo",
    0: "⚪ 0 — normalnie",
    -1: "🔴 -1 — niesportowo",
}


# =============================================================================
#  Pomocnicze
# =============================================================================
def _tabela_z_pozycjami(df: pd.DataFrame, kol_sort: str | None = None) -> pd.DataFrame:
    if kol_sort and kol_sort in df.columns:
        df = df.sort_values(kol_sort, ascending=False, kind="stable").reset_index(drop=True)
    df = df.copy()
    df.index = range(1, len(df) + 1)
    df.index.name = "Poz."
    return df


def _tabela_statyczna(df: pd.DataFrame) -> None:
    """Statyczna tabela – nie da się przesuwać ani sortować kolumn."""
    df = df.copy()
    df.index = [""] * len(df)
    st.table(df)


def _int0(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _dane_sa() -> bool:
    """Czy mamy dane do pokazania (Google Sheets albo lokalny plik podglądu)."""
    return sheets.skonfigurowane() or sheets.dane_lokalne()


def _lista_par(df: pd.DataFrame) -> list[str]:
    nazwy = set()
    for kol in ("Gospodarz", "Gość"):
        if kol in df.columns:
            nazwy |= {str(x).strip() for x in df[kol] if str(x).strip()}
    return sorted(nazwy)


def _wynik_opis(r: dict) -> str:
    w = str(r.get("Wynik", "")).strip()
    if not w:
        return ""
    if w.lower().startswith("walkower"):
        zw = r.get("Gość", "") if w.lower().endswith("gosc") else r.get("Gospodarz", "")
        return f"walkower (wygrana: {zw})"
    sety = [str(r.get(k, "")).strip() for k in ("Set1", "Set2", "SuperTB")]
    sety = [s for s in sety if s]
    return f"{w} ({', '.join(sety)})" if sety else w


# =============================================================================
#  Strony lig
# =============================================================================
def strona_ligi(etykieta_menu: str, nazwa_ligi: str) -> None:
    st.header(f"🎾 {nazwa_ligi} — {config.RUNDA}")
    tab_tabela, tab_mecze = st.tabs(["📊 Tabela", "📋 Mecze"])

    if _dane_sa():
        mecze = [m for m in sheets.pobierz_mecze() if str(m.get("Liga", "")).strip() == nazwa_ligi]
        oczekujace_id = {
            str(z.get("MeczID", "")).strip()
            for z in sheets.pobierz_zgloszenia()
            if str(z.get("Status", "")).strip() == config.STATUS_OCZEKUJE
        }
        with tab_tabela:
            _tabela_sheets(mecze)
        with tab_mecze:
            _mecze_sheets(mecze, oczekujace_id, nazwa_ligi)
    else:
        st.info("Sekcja dostępna po włączeniu Google Sheets (patrz README).")


def _tabela_sheets(mecze: list[dict]) -> None:
    zatwierdzone = [m for m in mecze if str(m.get("Zatwierdzono", "")).strip()]
    tabela = liga_logic.oblicz_tabele(zatwierdzone)
    if tabela.empty:
        st.info("Brak zatwierdzonych wyników – tabela pojawi się po akceptacji pierwszych meczów.")
        return
    st.table(_tabela_z_pozycjami(tabela))
    st.caption("Tabela liczona automatycznie z zatwierdzonych wyników "
               "(3 pkt zwycięstwo, 1 pkt porażka, walkower 3:0).")


def _mecze_sheets(mecze: list[dict], oczekujace_id: set[str], klucz: str) -> None:
    if not mecze:
        st.info("Brak meczów w arkuszu dla tej ligi.")
        return
    df = pd.DataFrame(mecze)

    def status(r):
        opis = _wynik_opis(r)
        if opis:
            return opis
        if str(r.get("ID", "")).strip() in oczekujace_id:
            return "⏳ oczekuje na akceptację"
        return "— nierozegrany"

    df["Wynik"] = df.apply(status, axis=1)

    WSZYSCY = "— wszystkie pary —"
    wybor = st.selectbox("Pokaż mecze pary:", [WSZYSCY] + _lista_par(df), key=f"filtr_m_{klucz}")
    if wybor != WSZYSCY:
        df = df[(df["Gospodarz"] == wybor) | (df["Gość"] == wybor)]
        if df.empty:
            st.info("Brak meczów tej pary.")
            return

    kolumny = [k for k in ["Gospodarz", "Gość", "Wynik"] if k in df.columns]
    st.caption("Gospodarz = para odpowiedzialna za zorganizowanie meczu.")
    _tabela_statyczna(df[kolumny].reset_index(drop=True))


# =============================================================================
#  Strona główna
# =============================================================================
def strona_glowna() -> None:
    if LOGO_PIONOWE.exists():
        kol_logo, kol_tytul = st.columns([1, 3], vertical_alignment="center")
        kol_logo.image(str(LOGO_PIONOWE), width=170)
        kol_tytul.title("Liga Deblowo-Mikstowa NP Tennis Academy")
    else:
        st.title("🎾 Liga Deblowo-Mikstowa NP Tennis Academy")

    st.markdown(
        f"""
        Witamy w **Lidze Deblowo-Mikstowej NP Tennis Academy**!

        **{config.RUNDA}: {config.RUNDA_TERMIN}** — w tej rundzie gramy wyłącznie
        **miksty**, podzielone na dwie grupy. Wybierz ligę z menu po lewej stronie.
        """
    )

    if _dane_sa():
        st.success("✅ Wyniki zgłaszacie w zakładce **➕ Zgłoś wynik** "
                   "(każdy wynik trafia do akceptacji organizatora).")
        st.success("🤝 Po meczu oceńcie przeciwników w zakładce **🤝 Zgłoś fair play** "
                   "— budujmy razem dobrą, sportową atmosferę!")
        if sheets.dane_lokalne():
            st.info("🔎 **Wersja lokalna (testowa)** — dane zapisują się w pliku "
                    "`Liga_Debel_DANE.xlsx`. Docelowo liga działa na Google Sheets.")
    else:
        st.warning("ℹ️ Brak danych. Aby włączyć ligę, skonfiguruj Google Sheets – patrz README.")

    tab_nier, tab_reg = st.tabs(["📋 Nierozegrane mecze", "📜 Regulamin"])
    with tab_nier:
        _nierozegrane_mecze()
    with tab_reg:
        st.subheader("ℹ️ Informacje")
        st.markdown(
            f"""
            - **Runda:** {config.RUNDA} ({config.RUNDA_TERMIN})
            - **Format:** debel/mikst, każda para gra z każdą w swojej lidze
            - **Bez kolejek** — mecze umawiacie sami w oknie całej rundy
            - **Mecz:** do 2 wygranych setów; przy 1:1 super tie-break do 10
            - **Punktacja:** 3 pkt zwycięstwo, 1 pkt porażka, walkower 3:0
            - **Awanse/spadki:** 2 najlepsze pary Ligi 2 → Liga 1, 2 ostatnie Ligi 1 → Liga 2 (w kolejnej rundzie)
            """
        )
        st.subheader("📜 Regulamin")
        regulamin = DATA_DIR / "regulamin.md"
        if regulamin.exists():
            st.markdown(regulamin.read_text(encoding="utf-8"))
        else:
            st.info("Treść regulaminu znajdziesz w pliku `data/regulamin.md`.")

    st.markdown("---")
    st.caption("© 2026 Liga Deblowa NP Tennis Academy · aplikację stworzył **Tomek Turek** 🎾")


def _nierozegrane_mecze() -> None:
    if not _dane_sa():
        st.info("Sekcja dostępna po włączeniu Google Sheets.")
        return
    mecze = sheets.pobierz_mecze()
    if not mecze:
        st.info("Brak meczów w arkuszu.")
        return

    oczek = {
        str(z.get("MeczID", "")).strip()
        for z in sheets.pobierz_zgloszenia()
        if str(z.get("Status", "")).strip() == config.STATUS_OCZEKUJE
    }

    WYBIERZ = "— wybierz ligę —"
    liga = st.selectbox("Wybierz ligę", [WYBIERZ] + list(config.LIGI.values()), key="nier_liga")
    if liga == WYBIERZ:
        st.info("Wybierz ligę, aby zobaczyć nierozegrane mecze.")
        return

    nier = []
    for m in mecze:
        if str(m.get("Liga", "")).strip() != liga:
            continue
        if str(m.get("Wynik", "")).strip() or str(m.get("Zatwierdzono", "")).strip():
            continue
        oczekuje = str(m.get("ID", "")).strip() in oczek
        nier.append({
            "Gospodarz": m.get("Gospodarz"),
            "Gość": m.get("Gość"),
            "Status": "⏳ oczekuje na akceptację" if oczekuje else "❗ nierozegrany",
        })

    if not nier:
        st.success("🎉 Wszystkie mecze w tej lidze rozegrane!")
        return
    st.caption(f"Nierozegrane mecze: {len(nier)}")
    _tabela_statyczna(pd.DataFrame(nier))


# =============================================================================
#  Zgłoś fair play
# =============================================================================
def strona_zglos_fairplay() -> None:
    st.header("🤝 Zgłoś ocenę fair play")
    st.caption("Po rozegranym meczu oceńcie przeciwną parę. Oceny trafiają do organizatora. "
               "Przy ocenie -1 komentarz jest obowiązkowy.")
    _formularz_oceny_fp()


def _formularz_oceny_fp() -> None:
    mecze = sheets.pobierz_mecze()
    liga = st.selectbox("Liga", list(config.LIGI.values()), key="oc_liga")
    pary = [p for p in _lista_par(pd.DataFrame(
        [m for m in mecze if str(m.get("Liga", "")).strip() == liga])) if p]
    if not pary:
        st.info("Brak par w tej lidze.")
        return

    ja = st.selectbox("Wasza para", pary, key="oc_ja")
    moje = [m for m in mecze
            if str(m.get("Liga", "")).strip() == liga
            and ja in (str(m.get("Gospodarz", "")).strip(), str(m.get("Gość", "")).strip())]
    if not moje:
        st.info("Brak meczów dla tej pary.")
        return

    def przeciwnik(m):
        g, go = str(m.get("Gospodarz", "")).strip(), str(m.get("Gość", "")).strip()
        return go if ja == g else g

    wybrany = st.selectbox("Mecz (oceniacie przeciwną parę)", moje,
                           format_func=lambda m: f"vs {przeciwnik(m)}", key="oc_mecz")
    oceniany = przeciwnik(wybrany)
    st.markdown(f"Oceniacie: **{oceniany}**")

    with st.form("formularz_oceny"):
        ocena_label = st.radio("Ocena fair play", list(OCENY_FP.values()), index=1)
        komentarz = st.text_area("Komentarz", placeholder="Opcjonalnie (przy ocenie -1 wymagany)")
        wyslij = st.form_submit_button("Wyślij ocenę", type="primary")

    if wyslij:
        ocena = next(k for k, v in OCENY_FP.items() if v == ocena_label)
        if ocena == -1 and not komentarz.strip():
            st.error("❌ Przy ocenie -1 komentarz jest obowiązkowy.")
            return
        wpis = {
            "ID": uuid4().hex[:8],
            "Czas": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "MeczID": wybrany.get("ID", ""),
            "Liga": liga,
            "Oceniający": ja,
            "Oceniany": oceniany,
            "Ocena": ocena,
            "Komentarz": komentarz.strip(),
        }
        try:
            sheets.dodaj_ocene(wpis)
        except Exception as e:
            st.error(f"Nie udało się zapisać oceny: {e}")
            return
        st.success(f"✅ Zapisano ocenę fair play dla: {oceniany}. Dziękujemy!")


# =============================================================================
#  Zgłaszanie wyniku
# =============================================================================
def strona_zglos_wynik() -> None:
    st.header("➕ Zgłoś wynik meczu")
    st.caption("Wynik trafia do akceptacji organizatora i pojawi się w tabeli po zatwierdzeniu.")

    mecze = sheets.pobierz_mecze()
    nazwa_ligi = st.selectbox("Liga", list(config.LIGI.values()))

    dostepne = [
        m for m in mecze
        if str(m.get("Liga", "")).strip() == nazwa_ligi
        and not str(m.get("Zatwierdzono", "")).strip()
    ]
    if not dostepne:
        st.info("Brak meczów do zgłoszenia w tej lidze.")
        return

    WSZYSCY = "— wszystkie pary —"
    pary = sorted({str(m.get("Gospodarz", "")).strip() for m in dostepne}
                  | {str(m.get("Gość", "")).strip() for m in dostepne})
    kto = st.selectbox("Wasza para (filtr)", [WSZYSCY] + [p for p in pary if p])
    if kto != WSZYSCY:
        dostepne = [m for m in dostepne
                    if kto in (str(m.get("Gospodarz", "")).strip(), str(m.get("Gość", "")).strip())]

    wybrany = st.selectbox(
        "Mecz", dostepne,
        format_func=lambda m: f"{m.get('Gospodarz','?')}  vs  {m.get('Gość','?')}",
    )
    st.markdown(f"**{wybrany.get('Gospodarz','?')}** (gospodarz)  vs  **{wybrany.get('Gość','?')}** (gość)")
    st.caption("Wynik z perspektywy gospodarza (np. 6:4). Super tie-break tylko przy 1:1.")

    with st.form("formularz_wyniku"):
        c1, c2, c3 = st.columns(3)
        set1 = c1.text_input("Set 1", placeholder="6:4")
        set2 = c2.text_input("Set 2", placeholder="3:6")
        stb = c3.text_input("Super tie-break (jeśli 1:1)", placeholder="10:7")
        wyslij = st.form_submit_button("Wyślij do akceptacji", type="primary")

    if wyslij:
        try:
            wynik = liga_logic.oblicz_mecz(set1, set2, stb)
        except liga_logic.BladWyniku as e:
            st.error(f"❌ {e}")
            return
        zgloszenie = {
            "ID": uuid4().hex[:8],
            "Czas": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "MeczID": wybrany.get("ID", ""),
            "Liga": nazwa_ligi,
            "Gospodarz": wybrany.get("Gospodarz", ""),
            "Gość": wybrany.get("Gość", ""),
            "Set1": set1.strip(),
            "Set2": set2.strip(),
            "SuperTB": stb.strip(),
            "Wynik": wynik["wynik"],
            "Status": config.STATUS_OCZEKUJE,
            "Rozpatrzono": "",
        }
        try:
            sheets.dodaj_zgloszenie(zgloszenie)
        except Exception as e:
            st.error(f"Nie udało się zapisać zgłoszenia: {e}")
            return
        st.success(f"✅ Zgłoszono wynik {wynik['wynik']}. Czeka na akceptację. Dziękujemy!")
        st.balloons()


# =============================================================================
#  Panel administratora
# =============================================================================
def strona_panel_admina() -> None:
    st.header("🔒 Panel administratora")
    haslo_ok = sheets.haslo_admina()

    if not st.session_state.get("admin_zalogowany"):
        with st.form("login"):
            podane = st.text_input("Hasło administratora", type="password")
            if st.form_submit_button("Zaloguj"):
                if haslo_ok and podane == haslo_ok:
                    st.session_state["admin_zalogowany"] = True
                    st.rerun()
                else:
                    st.error("Błędne hasło.")
        return

    col_a, col_b = st.columns([4, 1])
    col_a.success("Zalogowano jako administrator.")
    if col_b.button("Wyloguj"):
        st.session_state["admin_zalogowany"] = False
        st.rerun()

    tab_zgl, tab_wynik, tab_oceny = st.tabs(
        ["✅ Zgłoszenia wyników", "➕ Dodaj wynik / walkower", "🤝 Oceny fair play"]
    )
    with tab_zgl:
        _panel_zgloszenia()
    with tab_wynik:
        _panel_dodaj_wynik()
    with tab_oceny:
        _panel_oceny_fp()


def _panel_zgloszenia() -> None:
    zgloszenia = sheets.pobierz_zgloszenia()
    oczekujace = [z for z in zgloszenia if str(z.get("Status", "")).strip() == config.STATUS_OCZEKUJE]
    st.subheader(f"Oczekujące zgłoszenia: {len(oczekujace)}")
    if not oczekujace:
        st.info("Brak zgłoszeń do rozpatrzenia.")
    for z in oczekujace:
        with st.container(border=True):
            st.markdown(f"**{z.get('Liga','')}** · {z.get('Gospodarz','')} vs {z.get('Gość','')}")
            st.markdown(
                f"Wynik: **{z.get('Wynik','')}**  (sety: {z.get('Set1','')}, {z.get('Set2','')}"
                + (f", super TB: {z.get('SuperTB','')}" if str(z.get('SuperTB','')).strip() else "")
                + f") · zgłoszono {z.get('Czas','')}"
            )
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("✅ Akceptuj", key=f"akc_{z['ID']}", type="primary"):
                try:
                    sheets.akceptuj_zgloszenie(z)
                    st.toast("Zaakceptowano i zapisano do tabeli.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd akceptacji: {e}")
            if c2.button("❌ Odrzuć", key=f"odrz_{z['ID']}"):
                try:
                    sheets.odrzuc_zgloszenie(z)
                    st.toast("Zgłoszenie odrzucone.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")


def _panel_dodaj_wynik() -> None:
    st.caption("Wpis administratora trafia od razu do tabeli (bez akceptacji).")
    mecze = sheets.pobierz_mecze()
    liga = st.selectbox("Liga", list(config.LIGI.values()), key="adm_w_liga")
    lista = [m for m in mecze if str(m.get("Liga", "")).strip() == liga]
    if not lista:
        st.info("Brak meczów w tej lidze.")
        return

    def etk(m):
        w = str(m.get("Wynik", "")).strip()
        suf = f"   [obecnie: {w}]" if w else ""
        return f"{m.get('Gospodarz','?')} vs {m.get('Gość','?')}{suf}"

    mecz = st.selectbox("Mecz", lista, format_func=etk, key="adm_w_mecz")
    gospodarz, gosc = mecz.get("Gospodarz", ""), mecz.get("Gość", "")

    obecny = str(mecz.get("Wynik", "")).strip()
    if obecny or str(mecz.get("Zatwierdzono", "")).strip():
        opis = _wynik_opis(mecz) or "—"
        with st.container(border=True):
            st.markdown(f"Ten mecz ma już wynik: **{opis}**")
            if st.button("🗑️ Usuń wynik z tabeli", key="adm_w_del"):
                try:
                    sheets.wyczysc_wynik(mecz.get("ID", ""))
                    st.toast("Wynik usunięty — mecz wraca jako nierozegrany.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")

    typ = st.radio("Typ wpisu", ["Normalny wynik", "Walkower"], horizontal=True, key="adm_w_typ")
    if typ == "Normalny wynik":
        st.caption("Wynik z perspektywy gospodarza. Super tie-break tylko przy 1:1.")
        with st.form("adm_form_wynik"):
            c1, c2, c3 = st.columns(3)
            s1 = c1.text_input("Set 1", placeholder="6:4")
            s2 = c2.text_input("Set 2", placeholder="3:6")
            stb = c3.text_input("Super tie-break", placeholder="10:7")
            ok = st.form_submit_button("Zapisz wynik", type="primary")
        if ok:
            try:
                w = liga_logic.oblicz_mecz(s1, s2, stb)
            except liga_logic.BladWyniku as e:
                st.error(f"❌ {e}")
                return
            try:
                sheets.zapisz_wynik(mecz.get("ID", ""), s1.strip(), s2.strip(), stb.strip(), w["wynik"])
            except Exception as e:
                st.error(f"Błąd zapisu: {e}")
                return
            st.success(f"✅ Zapisano wynik {w['wynik']} ({gospodarz} vs {gosc}).")
            st.rerun()
    else:
        st.caption("Walkower: zwycięzca **3 pkt**, oddający **0 pkt** (bez setów).")
        zw = st.radio("Zwycięzca walkowera:", [gospodarz, gosc], key="adm_w_zw")
        if st.button("Zapisz walkower", type="primary"):
            marker = config.WALKOWER_G if zw == gospodarz else config.WALKOWER_S
            try:
                sheets.zapisz_wynik(mecz.get("ID", ""), "", "", "", marker)
            except Exception as e:
                st.error(f"Błąd zapisu: {e}")
                return
            st.success(f"✅ Zapisano walkower — wygrana: {zw}.")
            st.rerun()


def _panel_oceny_fp() -> None:
    oceny = sheets.pobierz_oceny()
    st.subheader(f"🤝 Oceny fair play: {len(oceny)}")
    if not oceny:
        st.info("Brak ocen fair play.")
        return

    WSZYSTKIE = "— wszystkie ligi —"
    ligi = [WSZYSTKIE] + sorted({str(o.get("Liga", "")).strip() for o in oceny if str(o.get("Liga", "")).strip()})
    c1, c2 = st.columns(2)
    liga = c1.selectbox("Liga", ligi, key="adm_oc_liga")
    tylko_neg = c2.checkbox("Tylko negatywne (-1)", key="adm_oc_neg")

    widoczne = oceny
    if liga != WSZYSTKIE:
        widoczne = [o for o in widoczne if str(o.get("Liga", "")).strip() == liga]
    if tylko_neg:
        widoczne = [o for o in widoczne if _int0(o.get("Ocena")) == -1]
    widoczne = sorted(widoczne, key=lambda o: str(o.get("Czas", "")), reverse=True)

    if not widoczne:
        st.info("Brak ocen dla wybranych filtrów.")
        return
    for i, o in enumerate(widoczne):
        etykieta = OCENY_FP.get(_int0(o.get("Ocena")), str(o.get("Ocena")))
        oid = str(o.get("ID", "")).strip()
        with st.container(border=True):
            st.markdown(f"{etykieta} — **{o.get('Oceniany','')}**  ·  od: {o.get('Oceniający','')}")
            st.caption(f"{o.get('Liga','')} · {o.get('Czas','')}")
            komentarz = str(o.get("Komentarz", "")).strip()
            if komentarz:
                st.markdown(f"> {komentarz}")
            if oid and st.button("🗑️ Usuń ocenę", key=f"del_oc_{oid}_{i}"):
                try:
                    sheets.usun_ocene(oid)
                    st.toast("Ocena usunięta.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd usuwania: {e}")


# =============================================================================
#  Nawigacja
# =============================================================================
def main() -> None:
    st.sidebar.title("Menu")
    opcje = ["🏠 Strona główna"] + list(LIGI_MENU.keys())
    if _dane_sa():
        opcje += ["➕ Zgłoś wynik", "🤝 Zgłoś fair play", "🔒 Panel administratora"]
    wybor = st.sidebar.radio("Przejdź do:", opcje, label_visibility="collapsed")

    try:
        if wybor == "🏠 Strona główna":
            strona_glowna()
        elif wybor == "🤝 Zgłoś fair play":
            strona_zglos_fairplay()
        elif wybor == "➕ Zgłoś wynik":
            strona_zglos_wynik()
        elif wybor == "🔒 Panel administratora":
            strona_panel_admina()
        elif wybor in LIGI_MENU:
            strona_ligi(wybor, LIGI_MENU[wybor])
    except Exception as e:
        if sheets.skonfigurowane():
            st.error("⚠️ Nie udało się połączyć z arkuszem Google. Spróbuj odświeżyć stronę za chwilę.")
            with st.expander("Szczegóły techniczne (dla organizatora)"):
                st.exception(e)
        else:
            raise

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Liga Deblowa • NP Tennis Academy • {config.RUNDA}")
    st.sidebar.caption("Aplikację stworzył **Tomek Turek** 🎾")


main()
