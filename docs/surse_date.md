# surse_date.md — Catalog Surse de Date & Monitorizare CM 2026

> **Scop:** Punct central de validare a datelor pentru `world-cup-predictor`.  
> Orice decizie a algoritmului din GCP Cloud Functions trebuie trasată la una din aceste surse.  
> Fișier generat: 11 iunie 2026 | Turneu activ: 11 iun – 19 iul 2026

---

## 0. Variabile care schimbă predicția în timp real

Înainte de orice altceva, algoritmul monitorizează aceste 8 variabile cu impact direct pe golaveraj și pronostic:

| Variabilă | Impact pe piață | Sursă primară |
| :--- | :--- | :--- |
| Accidentare star confirmat | Cotă favorit +15–30% | RotoWire, Goal.com |
| Absență titular (repaus strategic) | Reduce xG echipă cu ~0.4 | Sofascore (T-60min) |
| Suspendare (acumulare cartonașe) | Schimbă structura defensivă | FIFA.com oficial |
| WBGT > 32°C (căldură extremă) | Pauze obligatorii → joc fragmentat | AccuWeather tracker |
| Altitudine (Mexico City 2.240m) | Reduce distanța de sprint, afectează pressing | Springer/Sports Medicine |
| Steam move Pinnacle/Betfair | Informație nouă a intrat în piață | Pinnacle + Betfair Exchange |
| xG live sub 0.5 la pauză | Probabilitate O2.5 scade dramatic | Sofascore xG live / FotMob |
| Arbitru cu medie > 4.5 galb/meci | Meci mai oprit, ritm redus | Transfermarkt referee profile |

---

## 1. Ierarhia de Fiabilitate a Pieței (Cote & Volatilitate)

Mișcările de linie în ultimele 24h sunt un semnal-cheie. Dacă cota se mișcă la sursele "Sharp", algoritmul **recalculează automat** biletul.

| Tier | Sursă | URL | Rol în Algoritm |
| :--- | :--- | :--- | :--- |
| **Tier 1 — Ultra Sharp** | Betfair Exchange | https://www.betfair.com/betting/football/fifa-world-cup/c-12469077 | Probabilitate no-vig pură. Volumul real de bani. |
| **Tier 2 — Sharp** | Pinnacle | https://www.pinnacle.com/en/soccer/world-cup/matchups/ | Linia de referință mondială. Mișcarea = Informație Critică Nouă. |
| **Tier 3 — Regional/Retail** | Kambi (prin case partenere) | https://www.kambi.com/ | Rețeaua de case reglementate. |
| **Comparator** | Oddschecker | https://www.oddschecker.com/football/world-cup | Agregator 30+ case în timp real. |
| **Comparator** | OddsPortal | https://www.oddsportal.com/football/world/world-cup/ | Istoric opening vs closing line, CLV calculator. |
| **Piețe predicție** | Kalshi | https://kalshi.com/events/FIFAWC | Crowd intelligence, volume $4M+. |
| **Piețe predicție** | Polymarket | https://polymarket.com/sports | Piață decentralizată, probabilități alternative. |
| **Tracker live cote** | Covers.com | https://www.covers.com/world-cup/odds | Steam move tracker, public betting %, expert picks. |
| **Tracker Kalshi+Poly** | DeFiRate | https://defirate.com/prediction-markets/world-cup-odds/ | Agregator Kalshi + Polymarket + Gemini în același loc. |
| **Squawka Odds** | Squawka | https://www.squawka.com/us/outright-markets/world-cup-2026-outright-betting-odds/ | Live odds + Polymarket tracker integrat. |

---

## 2. Surse Oficiale FIFA & Confederații

Singurele surse acceptate pentru: program oficial, rezultate finale validate, sancțiuni, loturi înregistrate.

| Sursă | URL | Date extrase | Frecvență update |
| :--- | :--- | :--- | :--- |
| FIFA.com | https://www.fifa.com/ | Program, rezultate, sancțiuni, arbitri desemnați, loturi 23 jucători | Real-time în ziua meciului |
| FIFA+ (streaming oficial) | https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup/canadamexicousa2026 | Statistici post-meci validate, event-by-event oficial | Post-meci (–30min) |
| FIFA Discipline | https://www.fifa.com/competitions/mens/worldcup/canadamexicousa2026/officials | Cartonașe acumulate, suspendări automate | Post-fiecare rundă |
| UEFA (echipe europene) | https://www.uefa.com/ | Știri oficiale jucători europeni, accidentări confirmate din club | Zilnic |
| CONMEBOL (echipe S. America) | https://www.conmebol.com/ | Știri lot Argentina, Brazilia, Uruguay, Columbia, Ecuador, Paraguay | Zilnic |
| CAF (echipe africane) | https://www.cafonline.com/ | Știri lot Maroc, Senegal, Africa de Sud, Ghana, Egipt | Zilnic |
| AFC (echipe asiatice) | https://www.the-afc.com/ | Știri lot Japonia, Coreea de Sud, Arabia Saudită, Iran, Qatar | Zilnic |
| CONCACAF (Amer. de Nord) | https://www.concacaf.com/ | Știri lot SUA, Mexic, Canada, Haiti, Panama | Zilnic |

---

## 3. Live Scores, Lineupuri & Date Meci în Timp Real

Surse de integrat direct în pipeline-ul GCP pentru date intra-meci.

| Sursă | URL CM 2026 | Date cheie pentru algoritm | Latență |
| :--- | :--- | :--- | :--- |
| **Sofascore** ⭐ | https://www.sofascore.com/football/tournament/world/world-championship/16 | xG live, heatmaps, rating jucători, lineup confirmat, cornere, posesie, presing | < 30s |
| Sofascore Power Rankings | https://www.sofascore.com/news/sofascore-power-rankings-for-wc-2026 | Simulare pre-turneu bazată pe formă + cote | Pre-meci |
| **Flashscore** | https://www.flashscore.com/football/world/world-cup/ | Scoruri live ultrarapide, H2H complet, odds live integrate, tracker evenimente | < 10s |
| **FotMob** | https://www.fotmob.com/tournaments/77/overview/world-cup | xG live, lineup confirmat T-60min, momentum index vizual | < 20s |
| **ESPN Soccer** | https://www.espn.com/soccer/league/_/name/fifa.world | Lineup-uri confirmate, știri accidentări cu detalii clinice, ESPN BPI (Power Index) | T-2h |
| 365Scores | https://www.365scores.com/football/world-cup | Live scores, lineupuri probabile, clasament grupe actualizat | < 60s |
| BBC Sport | https://www.bbc.com/sport/football/world-cup | Live coverage text, rapoarte de meci, analize tactice post-meci | Live |
| CBS Sports | https://www.cbssports.com/soccer/world-cup/ | Previzualizări meciuri, știri lot, predicții | Zilnic |

---

## 4. Statistici Avansate & xG (Baseline Static + Update Săptămânal)

Folosite pre-turneu pentru construirea distribuțiilor Poisson și ca referință istorică continuă.

| Sursă | URL | Date extrase | Utilizare în algoritm |
| :--- | :--- | :--- | :--- |
| **FBref (StatsBomb)** ⭐ | https://fbref.com/en/comps/1/2026/2026-World-Cup-Stats | xG, xGA, xA, PPDA, progressive passes/carries, shot maps per echipă/jucător | `baseline_static.json` — calibrare model Poisson |
| FBref Scores & Fixtures | https://fbref.com/en/comps/1/schedule/World-Cup-Scores-and-Fixtures | Toate cele 104 meciuri cu fixture_id, dată, stadion, scor final | Structura turneu |
| FBref Player Stats | https://fbref.com/en/comps/1/stats/World-Cup-Stats | Statistici individuale: goluri, xG/90, presing, duels | Identificare jucători-cheie absenți |
| **Understat** | https://understat.com/ | xG per șut cu vizualizare, xA, model propriu pe ligile europene | Calibrare secundară pentru loturile europene |
| **WhoScored** | https://www.whoscored.com/ | Ratinguri jucători 0–10, forma echipă (ultimele 5), formații utilizate | Modificator formă pentru `lambda` Poisson |
| **FootyStats** ⭐ | https://footystats.org/world-cup | BTTS%, Over 2.5% historical, First Half Goals%, Clean Sheet%, trends 5/10 meciuri | Cel mai util pentru calibrare piețe goluri |
| StatPair | https://statpair.com/ | xG cu CLV, EV, Kelly staking, model aproape de StatsBomb | Validare valoare pariu vs cotă |
| FootyMetrics | https://www.footymetrics.com/ | Trends automate jucători/echipe, odds integrate, filtrare ultimele N meciuri | Screening rapid de valoare |
| Opta / Stats Perform | https://www.statsperform.com/ | Furnizor primar de date (indirect prin Sofascore, WhoScored, Sky Sports) | Nu accesat direct — referință pentru calitatea datelor |

---

## 5. Știri Echipe, Accidentări & Loturi (Fereastra 24h – 1h)

Cel mai critic layer. O absență confirmată în dimineața meciului poate schimba complet predicția.

| Sursă | URL | Date cheie | Fereastră timp |
| :--- | :--- | :--- | :--- |
| **RotoWire** ⭐ | https://www.rotowire.com/soccer/world-cup.php | Tabel accidentări toate 48 echipe, lineup-uri preconizate auto-update, știri rapide | T-24h și T-1h |
| RotoWire Injury Table | https://www.rotowire.com/soccer/injury-report.php | Status per jucător: out / questionable / probable / active | T-24h → T-1h |
| **Yahoo Sports WC Tracker** | https://sports.yahoo.com/soccer/live/2026-world-cup-news-live-tracker-injuries-squads-storylines-and-updates-as-the-tournament-looms-200000653.html | Live tracker actualizat continuu pe durata turneului | Live (ore) |
| **The Athletic** | https://theathletic.com/soccer/world-cup/ | Jurnalism cu surse din interior echipe naționale, știri tactice confirmate | Zilnic |
| Goal.com | https://www.goal.com/en/world-cup | Știri lot, declarații antrenori, istoricul accidentărilor per jucător | Zilnic |
| AllAboutFPL | https://allaboutfpl.com/tag/world-cup-2026/ | Lineup-uri preconizate toate 48 echipe cu ratinguri fantasy și note accidentări | T-48h per meci |
| ESPN Injury Reports | https://www.espn.com/soccer/league/_/name/fifa.world | Accidentări cu detalii clinice (tip accidentare, prognoză revenire) | Zilnic |

---

## 6. Analiză Tactică (Pre-meci & Post-meci)

Util pentru înțelegerea strategiei de joc per echipă — mai ales în grupele unde echipele gestionează golaverajul.

| Sursă | URL | Utilizare |
| :--- | :--- | :--- |
| **Tifo Football (YouTube)** | https://www.youtube.com/@TifoFootball | Analize tactice video: presing triggers, tranziții, utilizare formații |
| **The Analyst (Stats Perform)** | https://www.theanalyst.com/ | Set piece danger %, tactical trends, comparații formații (powered by Opta) |
| WhoScored Match Reports | https://www.whoscored.com/ | Heatmaps poziționale, care jucători au jucat în afara poziției, formații last 10 |

---

## 7. Factori Contextuali (Vreme, Altitudine, Arbitri)

Modificatori de ritm care afectează direct piețele de goluri (over/under) și BTTS.

### 7A. Vreme & Condiții Climatice

| Sursă | URL | Date cheie | Impact |
| :--- | :--- | :--- | :--- |
| **AccuWeather WC2026 Tracker** ⭐ | https://www.accuweather.com/en/sports/live-news/world-cup-2026-weather-updates-forecasts-for-key-matches-stadium-conditions-and-fan-impacts/1898671 | WBGT per stadion, alerte vreme severă, forecast pre-meci | WBGT > 32° → pauze obligatorii → scade ritm |
| Bloomberg WC2026 Heat Analysis | https://www.bloomberg.com/graphics/2026-fifa-world-cup-games-weather/ | Heat burden per echipă, calendarul termic complet al turneului | Tunisia + Franța = cel mai expuse |
| NPR Heat Risk Analysis | https://www.npr.org/2026/06/04/nx-s1-5742519/world-cup-fifa-hot-weather-risk-climate-miami | Risc termic per meci, kickoff times ajustate, stadioane acoperite | 1/3 din meciuri la risc ridicat |
| National Weather Service | https://www.weather.gov/ | Forecast specific per oraș gazdă (Dallas, Miami, LA, KC, Houston etc.) | Prognoza de precipitații: meci ploios → mai puține goluri din joc liber |

### 7B. Altitudine (Impact direct pe xG și pressing)

| Oraș gazdă | Altitudine | Impact documentat |
| :--- | :--- | :--- |
| Mexico City (Estadio Azteca) | **2.240 m** | Mingea zboară cu ~10% mai repede, presing epuizant, avantaj echipe adaptate |
| Guadalajara (Estadio Akron) | **1.558 m** | Efect moderat, echipele ne-aclimatizate pierd ~8% din capacitate aerobică |
| Monterrey (Estadio BBVA) | **538 m** | Impact minim |

> **Sursă academică:** https://link.springer.com/article/10.1007/s40279-026-02415-6  
> (Sports Medicine review oficial — heat, altitude, air pollution, travel la CM 2026)

### 7C. Arbitri

| Sursă | URL | Date extrase | Utilizare |
| :--- | :--- | :--- | :--- |
| **FIFA Arbitri Oficiali** | https://www.fifa.com/competitions/mens/worldcup/canadamexicousa2026/officials | Arbitru desemnat per meci (cu 72h înainte) | Stil arbitraj influențează nr. cartonașe |
| **Transfermarkt Referee Stats** | https://www.transfermarkt.com/schiedsrichter/statistik/schiedsrichter | Medie galb/meci, roșii/meci, penalty acordate/meci, stil permisiv vs strict | Input direct în algoritmul de golaveraj |
| Sofascore Referee Profile | https://www.sofascore.com/ | Profil arbitru cu ultimele meciuri arbitrate, medii galb/roșii/penalty | Validare cross cu Transfermarkt |

---

## 8. APIs Programatice (Integrare Python / GCP)

Accesate programatic din `main.py`. Necesită API key unde este specificat.

| Sursă | URL | Endpoint relevant | Cost | Utilizare |
| :--- | :--- | :--- | :--- | :--- |
| **Sportmonks** ⭐ | https://www.sportmonks.com/football-api/world-cup-api/ | `/fixtures`, `/livescores`, `/odds`, `/predictions`, `/xg` | Plătit (trial gratis) | All-in-one: xG live, cote 50+ case, 15s latență |
| **API-Football** | https://www.api-football.com/ | `GET /fixtures?league=1&season=2026`, `/injuries`, `/odds/live`, `/lineups` | Free tier disponibil | Lineup-uri, accidentări, cote live. Liga ID=1 |
| **TheStatsAPI** | https://www.thestatsapi.com/world-cup | `/matches`, `/odds` (Bet365+Pinnacle+Betfair+Kambi), `/xg`, `/lineups` | $50/lună, 7 zile trial | CLV tracking, 4 bookmakers în același JSON |
| WorldCupAPI | https://worldcupapi.com/ | `/live`, `/fixtures`, `/lineups`, `/odds-movement` | Verifică pricing | Dedicat exclusiv CM 2026, H2H integrat |
| **GitHub WC2026 (Free)** | https://github.com/rezarahiminia/worldcup2026 | REST simplu, JSON, update real-time în turneu | **Gratuit** | Ideal pentru testare și prototip rapid |

### Exemplu Python (API-Football — Free Tier)

```python
import requests

API_KEY = "YOUR_KEY_HERE"
BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-rapidapi-key": API_KEY}
LEAGUE_ID = 1      # FIFA World Cup
SEASON = 2026

def get_fixtures():
    r = requests.get(f"{BASE}/fixtures", headers=HEADERS,
                     params={"league": LEAGUE_ID, "season": SEASON})
    return r.json()["response"]

def get_lineups(fixture_id):
    r = requests.get(f"{BASE}/fixtures/lineups", headers=HEADERS,
                     params={"fixture": fixture_id})
    return r.json()["response"]

def get_injuries(fixture_id):
    r = requests.get(f"{BASE}/injuries", headers=HEADERS,
                     params={"fixture": fixture_id})
    return r.json()["response"]

def get_live_odds(fixture_id):
    r = requests.get(f"{BASE}/odds/live", headers=HEADERS,
                     params={"fixture": fixture_id})
    return r.json()["response"]
```

### Exemplu Python (Sofascore — Scraping cu respectarea ToS)

```python
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

def get_sofascore_lineups(event_id):
    url = f"https://api.sofascore.com/api/v1/event/{event_id}/lineups"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_sofascore_live_stats(event_id):
    url = f"https://api.sofascore.com/api/v1/event/{event_id}/statistics"
    r = requests.get(url, headers=HEADERS)
    return r.json()
```

> ⚠️ **Notă legală:** Folosiți API-urile oficiale acolo unde există. Scraping-ul direct pe site-uri fără API oficial trebuie respectat conform ToS al fiecărui site. Sofascore permite utilizare personală non-comercială.

---

## 9. Protocolul de Alerte în Timp Real (Workflow GCP Cloud Functions)

Algoritmul rulează verificări automate la 4 ferestre de timp înainte de fluierul de start:

```
[T-48h] → Filtru Baseline
[T-24h] → Filtru Meteo + Presă
[T-12h] → Filtru Sharp Line (Pinnacle/Betfair)
[T-1h]  → Filtru Final Confirmare (Lineup oficial)
```

### T-48h — Baseline Refresh

```
Surse: FBref + FootyStats + WhoScored
Acțiuni:
  - Actualizează xG_for și xG_against per echipă din ultimele 10 meciuri
  - Recalculează lambda Poisson pentru fiecare pereche de echipe
  - Verifică FBref Scores & Fixtures pentru fixture_id corect
Output: baseline_static.json actualizat
```

### T-24h — Filtru Meteo & Presă

```
Surse: AccuWeather + RotoWire + Goal.com + Yahoo Sports Tracker
Acțiuni:
  - Extrage WBGT forecast pentru stadionul meciului
  - IF WBGT > 32°C → aplică multiplicator ritm (-0.3 goluri estimate)
  - Verifică tabel accidentări RotoWire pentru toți jucătorii cu rating > 6.5
  - IF jucător critic marcat "Out" → recalculează xG echipei (-0.25 to -0.5)
  - Verifică declarații oficiale antrenori (Goal.com, The Athletic)
Output: alerta_t24.json cu modificatori activi
```

### T-12h — Filtru Sharp Line (Pinnacle + Betfair)

```
Surse: Pinnacle + Betfair Exchange + OddsPortal
Acțiuni:
  - Compară cota curentă vs cota de deschidere (opening line)
  - IF mișcare > 10% fără știre publică → FLAG: "steam_move_detected"
  - Calculează no-vig probability din Betfair Exchange
  - IF no-vig_prob(echipă) > 75% → confirmă selecție; IF < 55% → marchează pentru review
  - Verifică Covers.com pentru "where sharps bet" indicator
Output: alerta_t12.json cu flag-uri de recalculare
```

### T-1h — Filtru Final Confirmare (Lineup Oficial)

```
Surse: Sofascore (T-60min) + FotMob + RotoWire
Acțiuni:
  - Extrage lineup confirmat oficial
  - Compară cu lineup preconizat din baseline
  - IF diferențe > 2 jucători titulari → recalculează xG și lambda
  - IF star attacker pe bancă → schimbă O2.5 în O1.5 sau PSF
  - Verifică arbitrul desemnat (Transfermarkt stats)
  - IF arbitru medie galb/meci > 4.5 → marchează meci ca "high-interruption-risk"
Output: predictii.json final trimis către frontend
```

---

## 10. Logica de Decizie Automată (Decision Tree Simplificat)

```
PENTRU FIECARE MECI ÎN T-1h:
│
├─ Condiții extreme (WBGT > 32° SAU furtuni severe)?
│   ├─ DA → Reduce lambda total cu 20%, preferă O1.5 față de O2.5
│   └─ NU → Continuă
│
├─ Steam move detectat la Pinnacle (> 10% fără știre publică)?
│   ├─ DA → Prioritizează direcția mișcării cotei, recalculează probabilitate
│   └─ NU → Continuă cu no-vig Betfair ca referință
│
├─ Jucător critic (xG contribuție > 30%) absent?
│   ├─ DA → Scade lambda echipei cu 0.3–0.5, revizuiește selecție BTTS
│   └─ NU → Continuă
│
├─ Lineup confirmat diferă > 2 jucători față de cel preconizat?
│   ├─ DA → Recalculează complet biletul pentru acel meci
│   └─ NU → Confirmă selecția
│
└─ OUTPUT: predictii.json → GCP Storage → frontend/app.js
```

---

## 11. Cerințe Python (requirements.txt)

```txt
requests==2.32.3
beautifulsoup4==4.12.3
pandas==2.2.2
numpy==1.26.4
scipy==1.13.1
lxml==5.2.2
python-dotenv==1.0.1
google-cloud-storage==2.17.0
google-cloud-functions==1.16.0
schedule==1.2.2
```

---

## 12. Note Importante de Implementare

- **FBref (fbref.com):** Liga CM 2026 are `league_id=1`, `season=2026`. URL baza statistici: `https://fbref.com/en/comps/1/2026/2026-World-Cup-Stats`
- **API-Football:** Free tier = 100 req/zi. Pentru CM activ (72 meciuri × 4 endpoint-uri) → necesită plan plătit sau distribuire req pe zile.
- **Sofascore:** API public neoficial. Nu există SLA garantat. Folosiți ca backup, nu ca sursă primară în producție.
- **Betfair Exchange:** Necesită cont + API Key oficială. [https://developer.betfair.com/]
- **Pinnacle:** Nu are API public. Scraping permis pentru uz personal conform ToS.
- **AccuWeather:** API oficial la [https://developer.accuweather.com/] — endpoint `hourly/12hour/{locationKey}` pentru forecast stadion.
- **Date sensibile:** Nu urcați `API_KEY` pe GitHub. Folosiți `.env` local și `GCP Secret Manager` în cloud.

---

*Ultima actualizare: 11 iunie 2026 — Ziua 1 CM 2026*  
*50 surse catalogate | 9 categorii funcționale | 4 ferestre timp protocolare*
