# 🎾 Liga Deblowo-Mikstowa NP Tennis Academy

Aplikacja (Streamlit + Google Sheets) dla ligi **deblowej/mikstowej** — gramy
**parami**, bez kalendarza kolejek (mecze umawiane samodzielnie w oknie rundy),
z systemem gospodarz/gość, zgłaszaniem wyników do akceptacji i klasyfikacją Fair Play.

## Najważniejsze różnice vs liga singlowa

- **Zawodnik = para** (np. „Jan Kowalski / Anna Nowak").
- **Brak kolejek i dat meczów** — każda para gra z każdą w swojej lidze, kiedy się umówią.
- **Dwie rundy** z osobnymi zapisami (Runda 1: 15.10.2026–24.12.2026, Runda 2: 15.01.2027–30.04.2027).
- **Awanse/spadki:** 2 najlepsze pary Ligi 2 → Liga 1, 2 ostatnie Ligi 1 → Liga 2 (w kolejnej rundzie).
- W tej rundzie: **tylko mikst**, 2 grupy po 9 par.

## Uruchomienie

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Konfiguracja Google Sheets

Możesz **użyć tego samego konta serwisowego** co w lidze singlowej — wystarczy nowy arkusz.

1. Utwórz **nowy arkusz Google** (np. „Liga Debel NP 2026").
2. **Udostępnij** go adresowi konta serwisowego (`...iam.gserviceaccount.com`) jako **Edytor**.
3. Zbuduj `.streamlit/secrets.toml`:
   ```powershell
   python make_secrets.py "C:\sciezka\do\klucz.json"
   ```
   (podaj ID nowego arkusza i hasło administratora), albo skopiuj `gcp_service_account`
   z singlowego `secrets.toml` i zmień tylko `spreadsheet_id`.
4. **Zaimportuj dane:** w arkuszu **Plik → Importuj → Prześlij** → `Liga_Debel_DANE.xlsx`
   → **„Zastąp arkusz kalkulacyjny"**. To wgra pary, rozlosowane mecze (każda z każdą,
   zbalansowane gospodarz/gość 4/4) i puste zakładki na zgłoszenia/oceny.
5. `streamlit run app.py`.

> Zakładki: `mecze`, `zgloszenia`, `fairplay` (roster par), `fairplay_oceny`, `ustawienia`.

## Punktacja (w kodzie)

- Mecz do 2 wygranych setów; przy 1:1 super tie-break do 10.
- Zwycięstwo 3 pkt, porażka 1 pkt, walkower 3:0.
- Remisy: punkty → bezpośredni pojedynek (2 pary) → różnica setów → różnica gemów.

## Pliki

| Plik | Rola |
|------|------|
| `app.py` | interfejs |
| `liga_logic.py` | punktacja i tabela par (czysta logika) |
| `sheets.py` | połączenie z Google Sheets |
| `config.py` | ligi, runda, nagłówki kolumn |
| `Liga_Debel_DANE.xlsx` | dane do importu (pary + mecze) |
| `test_logic.py` | testy (`python test_logic.py`) |
| `data/regulamin.md` | regulamin |

## Kolejna runda (Runda 2)

Nowe zapisy → nowe pary (po awansach/spadkach). Wygeneruj nowy plik z meczami
analogicznie i zaimportuj do (najlepiej nowego) arkusza Rundy 2.
