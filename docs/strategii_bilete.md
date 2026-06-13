# strategii_bilete.md — Logica Biletelor Tip "Loterie" CM 2026

> **Scop:** Documentează modelul matematic, logica de selecție și sistemul de permutări  
> care stau la baza generării automate a biletelor din `predictii.json`.  
> Se citește împreună cu `surse_date.md`.  
> Fișier generat: 11 iunie 2026

---

## 0. Filosofia Sistemului

Biletul de tip "loterie" nu urmărește probabilitate maximă per selecție, ci **raportul
optim între probabilitate cumulativă și cotă finală**, distribuind riscul pe mai
multe bilete cu permutări astfel încât un singur eveniment greșit să nu anuleze
întreaga investiție.

```
PRINCIPIU FUNDAMENTAL:
  Nu pariezi 10 RON pe un singur bilet de 100.000x.
  Pariezi 10 RON pe 5 bilete de 2 RON fiecare, cu cote de 5.000x–20.000x,
  acoperind variante diferite ale aceluiași set de meciuri probabile.
```

---

## 1. Modelul Matematic — Distribuția Poisson

### 1A. Teoria de bază

Golurile într-un meci de fotbal urmează o **distribuție Poisson independentă**
pentru fiecare echipă. Dacă știm câte goluri se așteaptă să marcheze fiecare
echipă (lambda), putem calcula probabilitatea oricărui scor posibil.

```
P(k goluri) = (λ^k × e^−λ) / k!

unde:
  λ (lambda) = numărul așteptat de goluri al echipei
  k = numărul exact de goluri de calculat
  e = 2.71828 (constanta lui Euler)
```

### 1B. Calculul Lambda (λ) per Echipă

Lambda nu este un număr fix — se calculează din date reale și se ajustează:

```
λ_atac_A = xG_for_A(media_10_meciuri) × (xGA_B / medie_globala_xGA)
λ_atac_B = xG_for_B(media_10_meciuri) × (xGA_A / medie_globala_xGA)

Ajustări suplimentare:
  × factor_altitudine    (Mexico City: × 0.92 — joc mai lent)
  × factor_caldura       (WBGT > 32°: × 0.85)
  × factor_absenta_star  (jucător > 30% xG absent: × 0.75)
  × factor_forma         (WhoScored rating medie 5 meciuri / 10)
```

**Valorile medii globale CM 2026 (baseline pre-turneu) — toate 48 echipe:**

| Tier | Echipe (cod FIFA) | xG_for mediu / meci | xGA mediu / meci |
| :--- | :--- | :--- | :--- |
| **Tier 1 — Elite** | ARG, FRA, BRA, ENG, ESP, GER, NED, POR | 2.1 – 2.6 | 0.7 – 1.0 |
| **Tier 2 — Puternici** | COL, BEL, USA, JPN, URU, SUI, NOR, KOR, SEN, MAR, TUR, AUT, SWE, MEX | 1.4 – 2.1 | 1.0 – 1.5 |
| **Tier 3 — Competitivi** | EGY, CZE, SCO, CAN, ECU, ALG, BIH, KSA, AUS, GHA, PAR, CIV, IRN, RSA, CRO | 0.9 – 1.5 | 1.3 – 1.9 |
| **Tier 4 — Outsideri** | IRQ, TUN, CPV, HAI, JOR, PAN, NZL, COD, UZB, CUR, QAT | 0.4 – 0.9 | 2.0 – 2.8 |

> **Notă integritate**: Lista de mai sus este sincronizată cu `OFFICIAL_48_TEAMS` din `data_audit.py`.
> Dacă adaugi sau modifici o echipă, actualizează **ambele** fișiere simultan.

---

## 2. Probabilități Derivate din Poisson

### 2A. Scor exact

```python
import math

def poisson_prob(lam, k):
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def score_probability(lambda_a, lambda_b, goals_a, goals_b):
    return poisson_prob(lambda_a, goals_a) * poisson_prob(lambda_b, goals_b)
```

### 2B. Probabilități de piață derivate automat

```python
def calc_market_probs(lambda_a, lambda_b, max_goals=8):
    """
    Calculează toate probabilitățile relevante pentru Bet Builder
    din lambdele Poisson ale celor două echipe.
    """
    prob_matrix = {}
    for ga in range(max_goals + 1):
        for gb in range(max_goals + 1):
            prob_matrix[(ga, gb)] = score_probability(lambda_a, lambda_b, ga, gb)

    # Piețe derivate
    p_home_win = sum(v for (ga, gb), v in prob_matrix.items() if ga > gb)
    p_draw     = sum(v for (ga, gb), v in prob_matrix.items() if ga == gb)
    p_away_win = sum(v for (ga, gb), v in prob_matrix.items() if ga < gb)

    p_over_15  = sum(v for (ga, gb), v in prob_matrix.items() if ga + gb > 1)
    p_over_25  = sum(v for (ga, gb), v in prob_matrix.items() if ga + gb > 2)
    p_over_35  = sum(v for (ga, gb), v in prob_matrix.items() if ga + gb > 3)

    p_btts     = sum(v for (ga, gb), v in prob_matrix.items() if ga > 0 and gb > 0)
    p_cs_home  = sum(v for (ga, gb), v in prob_matrix.items() if gb == 0)
    p_cs_away  = sum(v for (ga, gb), v in prob_matrix.items() if ga == 0)

    # Goluri în repriza 1 (estimare: ~45% din goluri în R1)
    lam_a_r1 = lambda_a * 0.45
    lam_b_r1 = lambda_b * 0.45
    p_over_05_r1 = 1 - poisson_prob(lam_a_r1 + lam_b_r1, 0)
    p_over_15_r1 = 1 - (poisson_prob(lam_a_r1 + lam_b_r1, 0)
                       + poisson_prob(lam_a_r1 + lam_b_r1, 1))

    return {
        "1X2": {"1": p_home_win, "X": p_draw, "2": p_away_win},
        "over_1.5": p_over_15,
        "over_2.5": p_over_25,
        "over_3.5": p_over_35,
        "btts_yes": p_btts,
        "btts_no": 1 - p_btts,
        "cs_home": p_cs_home,
        "cs_away": p_cs_away,
        "over_0.5_r1": p_over_05_r1,
        "over_1.5_r1": p_over_15_r1,
    }
```

### 2C. Tabel de referință rapidă (lambda → probabilitate)

| λ_total (A+B) | P(Over 0.5) | P(Over 1.5) | P(Over 2.5) | P(Over 3.5) | P(BTTS) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1.0 | 63% | 26% | 8% | 2% | 26% |
| 1.5 | 78% | 44% | 19% | 6% | 37% |
| 2.0 | 86% | 59% | 32% | 14% | 47% |
| 2.5 | 92% | 71% | 46% | 24% | 55% |
| 3.0 | 95% | 80% | 58% | 35% | 61% |
| 3.5 | 97% | 86% | 68% | 46% | 66% |
| 4.0 | 98% | 91% | 76% | 57% | 71% |
| 4.5 | 99% | 94% | 83% | 66% | 74% |
| 5.0 | 99% | 96% | 88% | 73% | 77% |

---

## 3. Logica Bet Builder — Construirea Selecției per Meci

### 3A. Ce este Bet Builder

Bet Builder combină 2–4 selecții din **același meci** într-o singură cotă multiplicată.
Avantajul: cotele sunt mai mari decât selecțiile individuale; dezavantajul: corelația
între selecții nu este întotdeauna independentă (unele case penalizează corelațiile evidente).

### 3B. Reguli de construire Bet Builder per tier de meci

```
TIER S (λ_total ≥ 4.0) — Mismatch extrem:
  Selecție optimă: Over 2.5 + Favorit câștigă + Over 0.5 R1
  Alternativă: Over 3.5 + Favorit câștigă + PSF 2/2
  Evită: BTTS (echipa slabă rar marchează) → preferă Clean Sheet favorit

TIER A (λ_total 3.0–3.9) — Favorit clar:
  Selecție optimă: Over 2.5 + Favorit câștigă + BTTS sau gol R1
  Alternativă: Over 1.5 R1 + Favorit câștigă + Over 2.5 total
  Evită: Combinații cu scor exact (varianță prea mare)

TIER B (λ_total 2.5–2.9) — Favorit cu risc:
  Selecție optimă: BTTS + Over 2.5 SAU BTTS + Favorit câștigă
  Alternativă: Over 1.5 R1 + Favorit câștigă
  Evită: Clean Sheet (BTTS e mai probabil în meciuri echilibrate)

TIER C (λ_total 2.0–2.4) — Echilibrat:
  Selecție optimă: BTTS + Over 1.5 total
  Alternativă: Favorit câștigă + Over 1.5 R1
  Evită: Over 2.5 (probabilitate sub 55% → risc nejustificat)

TIER D (λ_total < 2.0) — Meciuri defensive:
  Selecție optimă: Sub 2.5 total SAU 1X2 simplu
  Evită: Includere în bilete de golaveraj — scad cota fără valoare adăugată
```

### 3C. Calculul cotei Bet Builder

Casele de pariuri calculează cotele Bet Builder astfel:

```
cotă_BB ≈ (1 / P_selecție_1) × (1 / P_selecție_2) × ... × (1 / P_selecție_n)
         × factor_marjă_casă (de obicei 0.85–0.92)

Exemplu:
  Over 2.5 (P=76%)  → cotă pură = 1/0.76 = 1.32
  GER câștigă (P=95%) → cotă pură = 1/0.95 = 1.05
  Over 0.5 R1 (P=82%) → cotă pură = 1/0.82 = 1.22
  
  Cotă BB brută = 1.32 × 1.05 × 1.22 = 1.69
  Cu marjă casă (×0.88) = 1.69 × 0.88 = 1.49

  → GER vs CUR BB la casa = ~1.85 (include și marja de profitabilitate)
```

---

## 4. Sistemul de Permutări — Acoperire Multi-Bilet

### 4A. Problema de bază

Pe un bilet cu 10 evenimente, dacă fiecare are probabilitate 80%:
```
P(toate 10 corecte) = 0.80^10 = 10.7%
P(9 din 10 corecte) = C(10,9) × 0.80^9 × 0.20^1 = 26.8%
P(8 din 10 corecte) = C(10,8) × 0.80^8 × 0.20^2 = 30.2%
```

Deci în 10 pariuri de 10 RON (100 RON total), în ~11% din cazuri câștigăm tot,
în ~89% din cazuri pierdem totul. **Soluția: permutări.**

### 4B. Sistemul "Core + Flex"

```
CORE = 4–5 evenimente cu probabilitate individuală > 85% (Tier S/A)
FLEX = 2–3 evenimente cu probabilitate individuală 65–84% (Tier A/B)

Bilet A = CORE(1,2,3,4) + FLEX(5,6,7)
Bilet B = CORE(1,2,3,4) + FLEX(5,6,8)    ← schimb Flex 7→8
Bilet C = CORE(1,2,3,4) + FLEX(5,7,8)    ← schimb Flex 6→8
Bilet D = CORE(1,2,3,4) + FLEX(6,7,8)    ← schimb Flex 5→8
Bilet E = CORE(1,2,3,5) + FLEX(6,7,8)    ← schimb Core 4→5

Rezultat: 5 bilete × 2 RON = 10 RON total
  → Dacă oricare 1 eveniment Flex greșit: 4 din 5 bilete pot câștiga
  → Dacă oricare 1 eveniment Core greșit: biletul E (cu Core diferit) acoperă
```

### 4C. Sistemul "Sistemă 7/8" (Pariuri Sistem)

O altă abordare: **sistemă 7 din 8** = alegi 8 evenimente, generezi C(8,7)=8 bilete
cu câte 7 evenimente fiecare. Câștigă orice bilet unde cele 7 din 7 selectate sunt corecte.

```
Avantaj: dacă 7 din 8 sunt corecte → câștig garantat (cel puțin 1 bilet corect)
Cost: 8 bilete × 2 RON = 16 RON total
```

Implementare Python:

```python
from itertools import combinations

def generate_system_bets(events, k, stake_per_ticket=2.0):
    """
    Generează toate biletele dintr-o sistemă k-din-n.
    events: lista de dict-uri cu {id, meci, cotă, probabilitate, bet_type}
    k: câte evenimente per bilet (ex: 7 din 8)
    """
    tickets = []
    for combo in combinations(events, k):
        combined_odds = 1.0
        combined_prob = 1.0
        for ev in combo:
            combined_odds *= ev["odds"]
            combined_prob *= ev["probability"]
        tickets.append({
            "events": [ev["id"] for ev in combo],
            "combined_odds": round(combined_odds, 2),
            "combined_probability": round(combined_prob * 100, 2),
            "potential_win": round(combined_odds * stake_per_ticket, 2),
            "stake": stake_per_ticket
        })
    return sorted(tickets, key=lambda t: t["combined_probability"], reverse=True)
```

### 4D. Matricea de Acoperire Recomandate CM 2026

Bazat pe cele 72 meciuri analizate, propunem 3 sisteme de bilete simultane:

```
SISTEM CONSERVATOR (risc minim, cotă moderată)
  Core: #1(GER-CUR), #3(ESP-CPV), #4(FRA-IRQ), #5(BRA-HAI)
  Flex pool: #7(IRQ-NOR), #8(POR-COD), #11(QAT-SUI), #12(SWE-TUN)
  Bilete: 5 × 2 RON = 10 RON | Cotă combinată est.: 15–60x
  Cel mai probabil scenariu de câștig

SISTEM MEDIU (echilibru cotă/probabilitate)
  Core: #1(GER-CUR), #3(ESP-CPV), #6(ENG-PAN), #8(POR-COD)
  Flex pool: #13(BRA-SCO), #15(ENG-GHA), #16(BEL-EGY), #19(JPN-TUN)
  Bilete: 5 × 2 RON = 10 RON | Cotă combinată est.: 60–300x
  Raport optim valoare/risc

SISTEM SPECULATIV (cotă maximă, risc ridicat)
  Core: #1(GER-CUR), #3(ESP-CPV), #5(BRA-HAI)
  Flex pool: #24(FRA-SEN), #26(BRA-MAR), #28(NED-SWE), #30(EGY-NZL)
  Bilete: 5 × 2 RON = 10 RON | Cotă combinată est.: 500–5.000x
  Tip "loterie" — pentru free bets și mize mici
```

---

## 5. Criteriul Kelly — Dimensionarea Mizei

Kelly Criterion calculează miza optimă în funcție de avantajul față de casă:

```
f* = (b × p − q) / b

unde:
  f* = fracțiunea din bankroll de pariat
  b  = cota net (cotă − 1)
  p  = probabilitatea estimată de câștig (Poisson model)
  q  = probabilitatea de pierdere (1 − p)

Exemplu (Germania vs Curaçao, O2.5):
  Cotă casă: 1.35 → b = 0.35
  Probabilitate model: 76% → p = 0.76, q = 0.24
  f* = (0.35 × 0.76 − 0.24) / 0.35 = (0.266 − 0.24) / 0.35 = 7.4%

  → La un bankroll de 100 RON → miză optimă = 7.4 RON
  → Kelly fracționat (0.25 Kelly) → 1.85 RON (recomandat pentru risc redus)
```

**Regulă practică pentru free bets (10 RON gratis):**
```
Nu se aplică Kelly pe free bet — miza este deja fixă.
Optimizarea se face la nivel de structură bilet (selecții) nu la nivel de miză.
Obiectiv: maximizarea Expected Value a biletului cu miza fixă.

EV = probabilitate_câștig × câștig_potențial − (1 − probabilitate_câștig) × miză
```

---

## 6. Detectarea Valorii (Value Bet)

O selecție are valoare dacă probabilitatea noastră estimată > probabilitatea implicată
de casă (no-vig).

```python
def has_value(our_probability, bookmaker_odds, margin=1.0):
    """
    Verifică dacă o selecție are valoare față de cota casei.
    our_probability: float 0–1 (din modelul Poisson)
    bookmaker_odds: float (cota oferită de casă, ex: 1.85)
    margin: threshold minim de avantaj în procente
    """
    implied_prob = 1 / bookmaker_odds
    edge = (our_probability - implied_prob) / implied_prob * 100
    return {
        "has_value": our_probability > implied_prob + (margin / 100),
        "edge_percent": round(edge, 2),
        "our_prob": round(our_probability * 100, 2),
        "implied_prob": round(implied_prob * 100, 2),
        "fair_odds": round(1 / our_probability, 3)
    }

# Exemplu utilizare:
result = has_value(our_probability=0.76, bookmaker_odds=1.40, margin=2.0)
# → {"has_value": True, "edge_percent": 6.4, "our_prob": 76.0, "implied_prob": 71.4}
```

**Closing Line Value (CLV)** — indicatorul suprem de calitate al unui pariu:
```
CLV = cota_la_care_ai_pariat / cota_de_închidere_Pinnacle

CLV > 1.0 → ai prins valoare (ai pariat mai devreme decât "smart money")
CLV < 1.0 → piața a mișcat împotrivă (informație nouă negativă a intrat)
CLV = 1.0 → neutru

Sursa pentru tracking CLV: TheStatsAPI (https://www.thestatsapi.com/world-cup)
```

---

## 7. Logica PSF (Pauză/Final) — Alternativă la Over/Under

PSF (numită și Half-Time/Full-Time sau Pauza/Final) este o piață alternativă
când Over 2.5 are probabilitate < 65%.

### Tipurile de PSF recomandate per situație

| Situație | PSF recomandat | Probabilitate tipică | Cotă tipică |
| :--- | :--- | :--- | :--- |
| Favorit clar, marchează rapid | 2/2 (favorit câștigă ambele reprize) | 55–70% | 1.6–2.2 |
| Echipă slabă rezistă în R1 | 1/2 sau X/2 (egalitate la pauză, favorit câștigă) | 20–35% | 3.5–5.0 |
| Meci defensiv, favorit modest | 2/1 sau X/1 (returul surprinde) | 8–15% | 7.0–15.0 |
| Cotă speculativă | 1/2 (outsider conduce la pauză, favorit egalează) | 5–12% | 10.0–20.0 |

### PSF Recomandate pentru Top Meciuri CM 2026

```
Germania vs Curaçao:     PSF 2/2 (GER conduce la pauză și câștigă) — ~70% prob.
Argentina vs Iordania:   PSF 2/2 — ~65% prob.
Spania vs Capul Verde:   PSF 2/2 — ~62% prob.
Brazilia vs Haiti:       PSF 2/2 — ~60% prob.
Anglia vs Panama:        PSF 2/2 — ~58% prob. (Panama poate rezista R1)
Franța vs Irak:          PSF X/2 alternativă (Franța poate fi prudentă R1) — ~28%
```

---

## 8. Algoritmul Complet de Generare Bilete (main.py flow)

```python
# main.py — Structura logicii principale

import json
from poisson_model import calc_market_probs
from value_detector import has_value
from permutation_engine import generate_system_bets
from data_loader import load_baseline, load_alerts

def generate_predictions():
    # 1. Încarcă datele
    baseline = load_baseline("data/baseline_static.json")
    alerts   = load_alerts("data/alerta_t1h.json")    # actualizat de pipeline T-1h

    predictions = []

    for match in baseline["matches"]:
        # 2. Calculează lambdele cu ajustările din alerte
        lam_a = match["xg_for_home"] * (match["xga_away"] / baseline["global_avg_xga"])
        lam_b = match["xg_for_away"] * (match["xga_home"] / baseline["global_avg_xga"])

        # Aplică modificatori din alerte
        if alerts.get(match["id"], {}).get("wbgt_extreme"):
            lam_a *= 0.85
            lam_b *= 0.85
        if alerts.get(match["id"], {}).get("star_absent_home"):
            lam_a *= 0.75
        if alerts.get(match["id"], {}).get("star_absent_away"):
            lam_b *= 0.75

        # 3. Calculează probabilitățile
        probs = calc_market_probs(lam_a, lam_b)

        # 4. Determină selecția optimă Bet Builder
        bet = build_bet_builder(probs, match["tier"])

        # 5. Verifică valoarea față de cotele din piață
        value = has_value(bet["probability"], bet["bookmaker_odds"])

        # 6. Scor final pentru ranking
        score = probs["over_2.5"] * 0.5 + probs["btts_yes"] * 0.3 + \
                (1 if value["has_value"] else 0.7) * 0.2

        predictions.append({
            "match_id": match["id"],
            "home": match["home"],
            "away": match["away"],
            "group": match["group"],
            "date": match["date"],
            "lambda_home": round(lam_a, 3),
            "lambda_away": round(lam_b, 3),
            "probs": probs,
            "bet": bet,
            "value": value,
            "ranking_score": round(score, 4),
            "tier": match["tier"]
        })

    # 7. Sortează după scor și generează biletele
    predictions.sort(key=lambda x: x["ranking_score"], reverse=True)
    top_matches = predictions[:30]

    # 8. Generează sistemele de bilete cu permutări
    tickets = {
        "conservator": generate_system_bets(top_matches[:8], k=7, stake_per_ticket=2.0),
        "mediu":        generate_system_bets(top_matches[8:16], k=7, stake_per_ticket=2.0),
        "speculativ":   generate_system_bets(top_matches[4:12], k=6, stake_per_ticket=1.5),
    }

    # 9. Salvează output
    output = {
        "generated_at": "ISO timestamp",
        "tournament": "FIFA World Cup 2026",
        "top_predictions": predictions[:30],
        "tickets": tickets
    }

    with open("data/predictii.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return output


def build_bet_builder(probs, tier):
    """Selectează tipul de Bet Builder bazat pe tier și probabilități."""
    if tier == "S":
        if probs["over_3.5"] > 0.5:
            return {"type": "Over 3.5 + Favorit câștigă + PSF 2/2",
                    "probability": probs["over_3.5"] * probs["1X2"]["1"] * 0.65}
        return {"type": "Over 2.5 + Favorit câștigă + Over 0.5 R1",
                "probability": probs["over_2.5"] * probs["1X2"]["1"] * probs["over_0.5_r1"]}

    elif tier == "A":
        return {"type": "Over 2.5 + Favorit câștigă + BTTS",
                "probability": probs["over_2.5"] * probs["1X2"]["1"] * probs["btts_yes"]}

    elif tier == "B":
        if probs["btts_yes"] > probs["cs_home"]:
            return {"type": "BTTS + Favorit câștigă + Over 1.5 R1",
                    "probability": probs["btts_yes"] * probs["1X2"]["1"] * probs["over_1.5_r1"]}
        return {"type": "Over 2.5 + Favorit câștigă",
                "probability": probs["over_2.5"] * probs["1X2"]["1"]}

    else:  # C sau D
        return {"type": "Over 1.5 + Favorit câștigă",
                "probability": probs["over_1.5"] * probs["1X2"]["1"]}
```

---

## 9. Structura `baseline_static.json`

Template pentru datele pre-turneu stocate local (nu se urcă pe GitHub):

```json
{
  "tournament": "FIFA World Cup 2026",
  "generated_at": "2026-06-11T00:00:00Z",
  "global_avg_xga": 1.18,
  "matches": [
    {
      "id": "wc2026_001",
      "home": "Mexico",
      "away": "South Africa",
      "group": "A",
      "matchday": 1,
      "date": "2026-06-11",
      "venue": "Estadio Azteca, Mexico City",
      "altitude_m": 2240,
      "tier": "B",
      "xg_for_home": 1.52,
      "xg_against_home": 1.21,
      "xg_for_away": 0.87,
      "xg_against_away": 1.68,
      "form_home": 6.8,
      "form_away": 5.2,
      "h2h_avg_goals": 2.4,
      "bookmaker_odds": {
        "home_win": 1.52,
        "draw": 3.80,
        "away_win": 5.50,
        "over_2.5": 1.95,
        "btts_yes": 2.10
      }
    }
  ]
}
```

---

## 10. Structura `predictii.json` (Output Frontend)

Template pentru outputul trimis către `frontend/app.js`:

```json
{
  "generated_at": "2026-06-11T19:00:00Z",
  "tournament": "FIFA World Cup 2026",
  "top_predictions": [
    {
      "match_id": "wc2026_025",
      "home": "Germany",
      "away": "Curacao",
      "group": "E",
      "date": "2026-06-14",
      "tier": "S",
      "ranking_score": 0.9421,
      "lambda_home": 3.41,
      "lambda_away": 0.48,
      "probs": {
        "over_2.5": 0.889,
        "over_3.5": 0.712,
        "btts_yes": 0.341,
        "over_0.5_r1": 0.934,
        "1X2": {"1": 0.971, "X": 0.024, "2": 0.005}
      },
      "bet": {
        "type": "Over 3.5 + GER câștigă + PSF 2/2",
        "probability": 0.449,
        "bookmaker_odds": 1.85,
        "has_value": true,
        "edge_percent": 3.2
      },
      "alerts": {
        "wbgt_extreme": false,
        "star_absent_home": false,
        "star_absent_away": false,
        "steam_move": false
      }
    }
  ],
  "tickets": {
    "conservator": [
      {
        "ticket_id": "A1",
        "events": ["wc2026_025", "wc2026_043", "wc2026_051", "wc2026_066", "wc2026_008"],
        "combined_odds": 28.4,
        "combined_probability": 35.2,
        "stake": 2.0,
        "potential_win": 56.8
      }
    ]
  }
}
```

---

## 11. Limitări Cunoscute ale Modelului

| Limitare | Impact | Mitigare |
| :--- | :--- | :--- |
| Poisson presupune independența golurilor | Subestimează rezultatele de tip 0-0 | Corecție Dixon-Coles (opțional) |
| Lambda bazat pe forma din sezon (club), nu internațional | Overestimează echipele cu jucători în formă la club dar slabi la națională | Ajustare factor "internațional discount" = × 0.88 |
| Nu modelează explicit set piece-urile | Set piece = ~30% din goluri la CM | Adaugă modifier din The Analyst set piece data |
| Nu modelează "managementul meciului" | Echipele calificate pot juca mai defensiv în MD3 | Verificare status calificare înainte de MD3 |
| Corelație selecții Bet Builder | Casa reduce cotele pentru selecții corelate (ex: favorit câștigă + clean sheet) | Evită combinații evident corelate pozitiv |
| Model static pentru primele meciuri (MD1) | Fără date din turneu = mai multă incertitudine | Reantrenează lambda după fiecare rundă cu date reale |

---

## 12. Glossar Termeni

| Termen | Definiție |
| :--- | :--- |
| **λ (Lambda)** | Numărul așteptat de goluri. Parametrul central al modelului Poisson. |
| **xG** | Expected Goals — calitatea ocaziilor de gol, nu numărul lor brut. |
| **BTTS** | Both Teams To Score — ambele echipe marchează cel puțin un gol. |
| **PSF** | Pauză/Final — predicție pentru scorul la pauță și scorul final. |
| **CLV** | Closing Line Value — cota ta vs cota de închidere Pinnacle. |
| **Steam Move** | Mișcare bruscă de cotă cauzată de un pariu mare de la un jucător ascuțit (sharp). |
| **no-vig** | Cota fără marja casei (Betfair Exchange). Reprezintă probabilitatea reală. |
| **Tier S/A/B/C/D** | Clasificarea meciurilor după probabilitatea de golaveraj ridicat (din surse_date.md). |
| **BetBuilder** | Combinarea a 2–4 selecții din același meci într-o singură cotă. |
| **Sistemă k/n** | Sistem de pariuri unde generezi toate combinațiile de k bilete din n evenimente. |
| **Edge** | Avantajul față de casă în procente. Edge > 0 = pariu cu valoare. |
| **Kelly Criterion** | Formula matematică pentru miza optimă în funcție de edge și bankroll. |
| **WBGT** | Wet Bulb Globe Temperature — indicator de stres termic care declanșează pauze în meci. |
| **PPDA** | Passes Per Defensive Action — indicator al intensității pressing-ului. |

---

*Ultima actualizare: 11 iunie 2026 — Ziua 1 CM 2026*  
*Model: Distribuție Poisson bivariată | Versiune: 1.0*  
*Se citește împreună cu: `surse_date.md`, `main.py`, `baseline_static.json`*
