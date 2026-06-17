#!/usr/bin/env python3
"""
world-cup-predictor/backend/main.py
────────────────────────────────────
Model Poisson avansat pentru CM 2026 cu integrare API-Sports,
modificatori contextuali dinamic și audit complet.
"""

import json
import math
import os
import sys
import traceback
from datetime import datetime, timezone
from itertools import combinations

# ── Strat de integritate (obligatoriu) ──────────────────────────────────────
try:
    from data_audit import run_full_audit, DataIntegrityError
    AUDIT_AVAILABLE = True
except ImportError:
    print("FATAL: data_audit.py lipsește.", file=sys.stderr)
    sys.exit(2)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from scipy.stats import poisson as sp_poisson
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# ─── CĂI ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(BASE_DIR, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "predictii_avansate.json")
RESULTS_FILE = os.path.join(BASE_DIR, "results_manual.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── CONSTANTE ──────────────────────────────────────────────────────────────
GLOBAL_AVG_XGA  = 1.18
ALT_THRESHOLD   = 1500
ALT_FACTOR      = 0.92
HEAT_FACTOR     = 0.85
STAR_ABSENT_F   = 0.75
R1_SHARE        = 0.45

# ─── API-Sports ─────────────────────────────────────────────────────────────
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_FOOTBALL_KEY:
    print("AVERTISMENT: API_FOOTBALL_KEY nu este setat. Se va folosi doar fallback static.", file=sys.stderr)
API_BASE_URL = "https://v3.football.api-sports.io"

# ─── DATE STATICE (fallback) ──────────────────────────────────────────────
TEAMS = {
    "ARG": {"xgf":2.31,"xga":0.82,"form":7.9,"rank":1},
    "FRA": {"xgf":2.25,"xga":0.88,"form":7.6,"rank":2},
    "BEL": {"xgf":1.95,"xga":1.08,"form":7.0,"rank":3},
    "ENG": {"xgf":2.21,"xga":0.91,"form":7.4,"rank":4},
    "BRA": {"xgf":2.11,"xga":1.12,"form":7.2,"rank":5},
    "ESP": {"xgf":2.35,"xga":0.78,"form":7.8,"rank":6},
    "POR": {"xgf":2.18,"xga":0.92,"form":7.5,"rank":7},
    "NED": {"xgf":2.15,"xga":1.02,"form":7.3,"rank":8},
    "COL": {"xgf":1.82,"xga":1.15,"form":7.1,"rank":9},
    "GER": {"xgf":2.28,"xga":0.95,"form":7.5,"rank":13},
    "MAR": {"xgf":1.48,"xga":1.05,"form":6.8,"rank":14},
    "CRO": {"xgf":1.48,"xga":1.28,"form":6.5,"rank":15},
    "USA": {"xgf":1.71,"xga":1.18,"form":7.0,"rank":16},
    "JPN": {"xgf":1.88,"xga":1.11,"form":7.1,"rank":17},
    "URU": {"xgf":1.55,"xga":1.18,"form":6.7,"rank":18},
    "SUI": {"xgf":1.74,"xga":0.98,"form":7.1,"rank":19},
    "SEN": {"xgf":1.61,"xga":1.15,"form":6.9,"rank":20},
    "KOR": {"xgf":1.41,"xga":1.19,"form":6.5,"rank":21},
    "NOR": {"xgf":2.08,"xga":1.08,"form":7.2,"rank":22},
    "IRN": {"xgf":0.88,"xga":1.42,"form":5.7,"rank":24},
    "AUT": {"xgf":1.78,"xga":1.21,"form":7.0,"rank":26},
    "TUR": {"xgf":1.52,"xga":1.24,"form":6.7,"rank":29},
    "EGY": {"xgf":1.24,"xga":1.31,"form":6.2,"rank":31},
    "CZE": {"xgf":1.38,"xga":1.31,"form":6.2,"rank":34},
    "SCO": {"xgf":1.35,"xga":1.28,"form":6.3,"rank":38},
    "MEX": {"xgf":1.52,"xga":1.21,"form":6.8,"rank":11},
    "QAT": {"xgf":0.62,"xga":2.15,"form":4.8,"rank":43},
    "ECU": {"xgf":1.18,"xga":0.92,"form":6.4,"rank":44},
    "ALG": {"xgf":1.18,"xga":1.48,"form":6.0,"rank":46},
    "CIV": {"xgf":1.31,"xga":1.45,"form":6.1,"rank":52},
    "AUS": {"xgf":0.98,"xga":1.62,"form":5.8,"rank":59},
    "GHA": {"xgf":1.15,"xga":1.51,"form":5.9,"rank":60},
    "PAR": {"xgf":0.95,"xga":1.58,"form":5.5,"rank":68},
    "IRQ": {"xgf":0.68,"xga":2.05,"form":5.0,"rank":71},
    "RSA": {"xgf":0.87,"xga":1.68,"form":5.2,"rank":67},
    "KSA": {"xgf":0.95,"xga":1.72,"form":5.6,"rank":56},
    "CPV": {"xgf":0.81,"xga":1.95,"form":5.4,"rank":91},
    "BIH": {"xgf":1.21,"xga":1.42,"form":6.1,"rank":55},
    "CAN": {"xgf":1.68,"xga":1.35,"form":6.9,"rank":41},
    "SWE": {"xgf":1.62,"xga":1.21,"form":6.8,"rank":25},
    "TUN": {"xgf":0.78,"xga":1.78,"form":5.3,"rank":74},
    "NZL": {"xgf":0.72,"xga":1.92,"form":5.1,"rank":103},
    "PAN": {"xgf":0.68,"xga":1.98,"form":5.0,"rank":89},
    "HAI": {"xgf":0.51,"xga":2.41,"form":4.5,"rank":88},
    "JOR": {"xgf":0.58,"xga":2.18,"form":4.9,"rank":87},
    "CUR": {"xgf":0.71,"xga":2.28,"form":5.1,"rank":112},
    "COD": {"xgf":0.88,"xga":2.01,"form":5.2,"rank":98},
    "UZB": {"xgf":0.72,"xga":1.98,"form":5.0,"rank":107},
}

TEAM_NAMES_RO = {
    "ARG":"Argentina","FRA":"Franța","BRA":"Brazilia","ENG":"Anglia",
    "ESP":"Spania","GER":"Germania","NED":"Olanda","POR":"Portugalia",
    "BEL":"Belgia","COL":"Columbia","JPN":"Japonia","KOR":"Coreea de Sud",
    "URU":"Uruguay","SUI":"Elveția","NOR":"Norvegia","SWE":"Suedia",
    "MEX":"Mexic","AUT":"Austria","TUR":"Turcia","SEN":"Senegal",
    "MAR":"Maroc","USA":"SUA","CRO":"Croația","EGY":"Egipt",
    "CZE":"Cehia","SCO":"Scoția","CAN":"Canada","ECU":"Ecuador",
    "ALG":"Algeria","BIH":"Bosnia","KSA":"Arabia Saudită","AUS":"Australia",
    "GHA":"Ghana","PAR":"Paraguay","CIV":"Coasta de Fildeș","IRN":"Iran",
    "RSA":"Africa de Sud","IRQ":"Irak","TUN":"Tunisia","CPV":"Capul Verde",
    "HAI":"Haiti","JOR":"Iordania","PAN":"Panama","NZL":"Noua Zeelandă",
    "COD":"Congo DR","UZB":"Uzbekistan","CUR":"Curaçao","QAT":"Qatar",
}

# ─── PROGRAM MECIURI — toate 72 ──────────────────────────────────────────────

FIXTURES = [
    # ── GRUPA A ──────────────────────────────────────────────────────────────
    {"id":"A1","home":"MEX","away":"RSA","group":"A","md":1,"date":"2026-06-11","venue":"Mexico City","alt":2240},
    {"id":"A2","home":"KOR","away":"CZE","group":"A","md":1,"date":"2026-06-12","venue":"Guadalajara","alt":1558},
    {"id":"A3","home":"MEX","away":"KOR","group":"A","md":2,"date":"2026-06-18","venue":"Guadalajara","alt":1558},
    {"id":"A4","home":"RSA","away":"CZE","group":"A","md":2,"date":"2026-06-18","venue":"Atlanta","alt":320},
    {"id":"A5","home":"MEX","away":"CZE","group":"A","md":3,"date":"2026-06-24","venue":"Mexico City","alt":2240},
    {"id":"A6","home":"RSA","away":"KOR","group":"A","md":3,"date":"2026-06-24","venue":"Guadalajara","alt":1558},
    # ── GRUPA B ──────────────────────────────────────────────────────────────
    {"id":"B1","home":"CAN","away":"BIH","group":"B","md":1,"date":"2026-06-13","venue":"Toronto","alt":76},
    {"id":"B2","home":"QAT","away":"SUI","group":"B","md":1,"date":"2026-06-13","venue":"San Francisco","alt":5},
    {"id":"B3","home":"CAN","away":"QAT","group":"B","md":2,"date":"2026-06-19","venue":"Vancouver","alt":5},
    {"id":"B4","home":"BIH","away":"SUI","group":"B","md":2,"date":"2026-06-19","venue":"Seattle","alt":5},
    {"id":"B5","home":"CAN","away":"SUI","group":"B","md":3,"date":"2026-06-24","venue":"Vancouver","alt":5},
    {"id":"B6","home":"BIH","away":"QAT","group":"B","md":3,"date":"2026-06-24","venue":"Toronto","alt":76},
    # ── GRUPA C ──────────────────────────────────────────────────────────────
    {"id":"C1","home":"BRA","away":"MAR","group":"C","md":1,"date":"2026-06-13","venue":"New York","alt":5},
    {"id":"C2","home":"HAI","away":"SCO","group":"C","md":1,"date":"2026-06-14","venue":"Boston","alt":5},
    {"id":"C3","home":"BRA","away":"SCO","group":"C","md":2,"date":"2026-06-20","venue":"Philadelphia","alt":12},
    {"id":"C4","home":"HAI","away":"MAR","group":"C","md":2,"date":"2026-06-19","venue":"New York","alt":5},
    {"id":"C5","home":"BRA","away":"HAI","group":"C","md":3,"date":"2026-06-24","venue":"Miami","alt":2},
    {"id":"C6","home":"SCO","away":"MAR","group":"C","md":3,"date":"2026-06-24","venue":"Boston","alt":5},
    # ── GRUPA D ──────────────────────────────────────────────────────────────
    {"id":"D1","home":"USA","away":"PAR","group":"D","md":1,"date":"2026-06-13","venue":"Los Angeles","alt":86},
    {"id":"D2","home":"AUS","away":"TUR","group":"D","md":1,"date":"2026-06-13","venue":"Vancouver","alt":5},
    {"id":"D3","home":"USA","away":"AUS","group":"D","md":2,"date":"2026-06-20","venue":"Los Angeles","alt":86},
    {"id":"D4","home":"PAR","away":"TUR","group":"D","md":2,"date":"2026-06-20","venue":"Dallas","alt":142},
    {"id":"D5","home":"USA","away":"TUR","group":"D","md":3,"date":"2026-06-25","venue":"Seattle","alt":5},
    {"id":"D6","home":"PAR","away":"AUS","group":"D","md":3,"date":"2026-06-25","venue":"Kansas City","alt":270},
    # ── GRUPA E ──────────────────────────────────────────────────────────────
    {"id":"E1","home":"GER","away":"CUR","group":"E","md":1,"date":"2026-06-14","venue":"Houston","alt":14},
    {"id":"E2","home":"CIV","away":"ECU","group":"E","md":1,"date":"2026-06-14","venue":"Philadelphia","alt":12},
    {"id":"E3","home":"GER","away":"CIV","group":"E","md":2,"date":"2026-06-20","venue":"Houston","alt":14},
    {"id":"E4","home":"CUR","away":"ECU","group":"E","md":2,"date":"2026-06-19","venue":"Dallas","alt":142},
    {"id":"E5","home":"GER","away":"ECU","group":"E","md":3,"date":"2026-06-25","venue":"Houston","alt":14},
    {"id":"E6","home":"CIV","away":"CUR","group":"E","md":3,"date":"2026-06-25","venue":"Philadelphia","alt":12},
    # ── GRUPA F ──────────────────────────────────────────────────────────────
    {"id":"F1","home":"NED","away":"JPN","group":"F","md":1,"date":"2026-06-14","venue":"Los Angeles","alt":86},
    {"id":"F2","home":"SWE","away":"TUN","group":"F","md":1,"date":"2026-06-14","venue":"Seattle","alt":5},
    {"id":"F3","home":"NED","away":"SWE","group":"F","md":2,"date":"2026-06-22","venue":"Los Angeles","alt":86},
    {"id":"F4","home":"JPN","away":"TUN","group":"F","md":2,"date":"2026-06-23","venue":"Dallas","alt":142},
    {"id":"F5","home":"NED","away":"TUN","group":"F","md":3,"date":"2026-06-27","venue":"Los Angeles","alt":86},
    {"id":"F6","home":"JPN","away":"SWE","group":"F","md":3,"date":"2026-06-27","venue":"Seattle","alt":5},
    # ── GRUPA G ──────────────────────────────────────────────────────────────
    {"id":"G1","home":"BEL","away":"EGY","group":"G","md":1,"date":"2026-06-15","venue":"Philadelphia","alt":12},
    {"id":"G2","home":"IRN","away":"NZL","group":"G","md":1,"date":"2026-06-16","venue":"Seattle","alt":5},
    {"id":"G3","home":"BEL","away":"IRN","group":"G","md":2,"date":"2026-06-21","venue":"Philadelphia","alt":12},
    {"id":"G4","home":"EGY","away":"NZL","group":"G","md":2,"date":"2026-06-22","venue":"Boston","alt":5},
    {"id":"G5","home":"BEL","away":"NZL","group":"G","md":3,"date":"2026-06-27","venue":"Philadelphia","alt":12},
    {"id":"G6","home":"EGY","away":"IRN","group":"G","md":3,"date":"2026-06-27","venue":"Seattle","alt":5},
    # ── GRUPA H ──────────────────────────────────────────────────────────────
    {"id":"H1","home":"ESP","away":"CPV","group":"H","md":1,"date":"2026-06-15","venue":"Kansas City","alt":270},
    {"id":"H2","home":"KSA","away":"URU","group":"H","md":1,"date":"2026-06-15","venue":"Miami","alt":2},
    {"id":"H3","home":"ESP","away":"KSA","group":"H","md":2,"date":"2026-06-21","venue":"Kansas City","alt":270},
    {"id":"H4","home":"CPV","away":"URU","group":"H","md":2,"date":"2026-06-21","venue":"Atlanta","alt":320},
    {"id":"H5","home":"ESP","away":"URU","group":"H","md":3,"date":"2026-06-26","venue":"Miami","alt":2},
    {"id":"H6","home":"CPV","away":"KSA","group":"H","md":3,"date":"2026-06-26","venue":"Kansas City","alt":270},
    # ── GRUPA I ──────────────────────────────────────────────────────────────
    {"id":"I1","home":"FRA","away":"SEN","group":"I","md":1,"date":"2026-06-16","venue":"Atlanta","alt":320},
    {"id":"I2","home":"IRQ","away":"NOR","group":"I","md":1,"date":"2026-06-16","venue":"Boston","alt":5},
    {"id":"I3","home":"FRA","away":"IRQ","group":"I","md":2,"date":"2026-06-22","venue":"Atlanta","alt":320},
    {"id":"I4","home":"SEN","away":"NOR","group":"I","md":2,"date":"2026-06-22","venue":"Miami","alt":2},
    {"id":"I5","home":"FRA","away":"NOR","group":"I","md":3,"date":"2026-06-26","venue":"Atlanta","alt":320},
    {"id":"I6","home":"SEN","away":"IRQ","group":"I","md":3,"date":"2026-06-26","venue":"Boston","alt":5},
    # ── GRUPA J ──────────────────────────────────────────────────────────────
    {"id":"J1","home":"ARG","away":"ALG","group":"J","md":1,"date":"2026-06-16","venue":"Dallas","alt":142},
    {"id":"J2","home":"AUT","away":"JOR","group":"J","md":1,"date":"2026-06-16","venue":"Miami","alt":2},
    {"id":"J3","home":"ARG","away":"AUT","group":"J","md":2,"date":"2026-06-22","venue":"Dallas","alt":142},
    {"id":"J4","home":"ALG","away":"JOR","group":"J","md":2,"date":"2026-06-22","venue":"Atlanta","alt":320},
    {"id":"J5","home":"ARG","away":"JOR","group":"J","md":3,"date":"2026-06-27","venue":"Dallas","alt":142},
    {"id":"J6","home":"ALG","away":"AUT","group":"J","md":3,"date":"2026-06-27","venue":"Miami","alt":2},
    # ── GRUPA K ──────────────────────────────────────────────────────────────
    {"id":"K1","home":"POR","away":"COD","group":"K","md":1,"date":"2026-06-17","venue":"Kansas City","alt":270},
    {"id":"K2","home":"UZB","away":"COL","group":"K","md":1,"date":"2026-06-17","venue":"Los Angeles","alt":86},
    {"id":"K3","home":"POR","away":"UZB","group":"K","md":2,"date":"2026-06-23","venue":"Kansas City","alt":270},
    {"id":"K4","home":"COD","away":"COL","group":"K","md":2,"date":"2026-06-23","venue":"Los Angeles","alt":86},
    {"id":"K5","home":"POR","away":"COL","group":"K","md":3,"date":"2026-06-27","venue":"New York","alt":5},
    {"id":"K6","home":"COD","away":"UZB","group":"K","md":3,"date":"2026-06-27","venue":"San Francisco","alt":5},
    # ── GRUPA L ──────────────────────────────────────────────────────────────
    {"id":"L1","home":"ENG","away":"CRO","group":"L","md":1,"date":"2026-06-17","venue":"San Francisco","alt":5},
    {"id":"L2","home":"GHA","away":"PAN","group":"L","md":1,"date":"2026-06-17","venue":"New York","alt":5},
    {"id":"L3","home":"ENG","away":"GHA","group":"L","md":2,"date":"2026-06-23","venue":"San Francisco","alt":5},
    {"id":"L4","home":"CRO","away":"PAN","group":"L","md":2,"date":"2026-06-23","venue":"Seattle","alt":5},
    {"id":"L5","home":"ENG","away":"PAN","group":"L","md":3,"date":"2026-06-27","venue":"San Francisco","alt":5},
    {"id":"L6","home":"GHA","away":"CRO","group":"L","md":3,"date":"2026-06-27","venue":"New York","alt":5},
]

# ─── FUNCȚII API-Sports (pentru statistici echipe) ──────────────────────────

def enrich_team_data_from_api(teams_dict: dict) -> dict:
    """
    Îmbogățește datele echipelor cu statistici din API.
    Dacă API-ul nu răspunde, păstrează datele statice.
    """
    if not API_FOOTBALL_KEY:
        return teams_dict
    new_teams = teams_dict.copy()
    for code in list(new_teams.keys()):
        stats = fetch_team_statistics(code)
        if stats:
            if stats["avg_goals_scored"] > 0:
                new_teams[code]["xgf"] = stats["avg_goals_scored"]
            if stats["avg_goals_conceded"] > 0:
                new_teams[code]["xga"] = stats["avg_goals_conceded"]
            new_teams[code]["possession"] = stats.get("avg_possession", 50.0)
            new_teams[code]["fouls"] = stats.get("avg_fouls", 0.0)
            new_teams[code]["cards"] = stats.get("avg_yellow", 0.0) + stats.get("avg_red", 0.0) * 3
    return new_teams
    
def fetch_live_fixtures_from_api(league_id: int = 1, season: int = 2026) -> dict:
    """
    Interoghează API-Football pentru toate meciurile din CM 2026.
    Returnează dict cu ID-ul nostru (ex: "A1") -> scoruri și status.
    Dacă eșuează, returnează dict gol.
    """
    if not API_FOOTBALL_KEY or not REQUESTS_AVAILABLE:
        return {}

    # Hartă nume API → codul nostru (3 litere)
    api_name_to_code = {
        "Argentina": "ARG", "France": "FRA", "Brazil": "BRA", "England": "ENG",
        "Spain": "ESP", "Germany": "GER", "Netherlands": "NED", "Portugal": "POR",
        "Belgium": "BEL", "Colombia": "COL", "Japan": "JPN", "South Korea": "KOR",
        "Korea Republic": "KOR", "Uruguay": "URU", "Switzerland": "SUI", "Norway": "NOR",
        "Sweden": "SWE", "Mexico": "MEX", "Austria": "AUT", "Turkey": "TUR",
        "Senegal": "SEN", "Morocco": "MAR", "USA": "USA", "United States": "USA",
        "Croatia": "CRO", "Egypt": "EGY", "Czech Republic": "CZE", "Scotland": "SCO",
        "Canada": "CAN", "Ecuador": "ECU", "Algeria": "ALG", "Bosnia-Herzegovina": "BIH",
        "Saudi Arabia": "KSA", "Australia": "AUS", "Ghana": "GHA", "Paraguay": "PAR",
        "Ivory Coast": "CIV", "Côte d'Ivoire": "CIV", "Iran": "IRN", "South Africa": "RSA",
        "Iraq": "IRQ", "Tunisia": "TUN", "Cape Verde": "CPV", "Haiti": "HAI",
        "Jordan": "JOR", "Panama": "PAN", "New Zealand": "NZL", "Congo DR": "COD",
        "DR Congo": "COD", "Uzbekistan": "UZB", "Curacao": "CUR", "Curaçao": "CUR",
        "Qatar": "QAT"
    }

    try:
        url = f"{API_BASE_URL}/fixtures"
        params = {"league": league_id, "season": season}
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"  ⚠️ API-Football a răspuns cu status {resp.status_code}")
            return {}
        data = resp.json()
        if not data.get("response"):
            return {}

        result = {}
        for m in data["response"]:
            home_api = m.get("teams", {}).get("home", {}).get("name")
            away_api = m.get("teams", {}).get("away", {}).get("name")

            home_code = api_name_to_code.get(home_api)
            away_code = api_name_to_code.get(away_api)

            if home_code is None or away_code is None:
                continue

            # Găsim meciul nostru după codurile de 3 litere
            our_fixture = None
            for fx in FIXTURES:
                if fx["home"] == home_code and fx["away"] == away_code:
                    our_fixture = fx
                    break

            if not our_fixture:
                continue

            our_id = our_fixture["id"]
            goals = m.get("goals", {})
            status_short = m.get("fixture", {}).get("status", {}).get("short", "NS")

            if status_short in ("FT", "AET", "PEN"):
                status_str = "finished"
            elif status_short in ("LIVE", "HT", "1H", "2H"):
                status_str = "live"
            else:
                status_str = "scheduled"

            result[our_id] = {
                "home_score": goals.get("home"),
                "away_score": goals.get("away"),
                "status": status_str,
            }

        return result

    except Exception as e:
        print(f"  ⚠️ Eroare la preluarea fixture-urilor din API: {e}")
        return {}
    
# ─── MODIFICATOR CONTEXTUAL DINAMIC ───────────────────────────────────────

def load_results_manual() -> dict:
    """Încarcă results_manual.json și returnează un dict."""
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if isinstance(v, dict) and "home_score" in v}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_team_gd(team_code: str, results: dict) -> float:
    """Calculează golaverajul total al echipei din meciurile jucate."""
    gd = 0.0
    for fx in FIXTURES:
        if fx["home"] == team_code or fx["away"] == team_code:
            rid = fx["id"]
            if rid in results and results[rid].get("status") == "finished":
                hs = results[rid]["home_score"]
                as_ = results[rid]["away_score"]
                if fx["home"] == team_code:
                    gd += (hs - as_)
                else:
                    gd += (as_ - hs)
    return gd

def aplica_modificator_contextual(echipa_ataca: str, echipa_apara: str, faza_competitie: int, results: dict) -> tuple[float, float]:
    """Ajustează lambda pentru atac și apărare pe baza golaverajului, necesităților de calificare."""
    factor_atac = 1.0
    factor_aparare = 1.0

    gd_atac = get_team_gd(echipa_ataca, results)
    gd_apara = get_team_gd(echipa_apara, results)

    if gd_atac >= 5:
        factor_atac *= 1.25
    elif gd_atac >= 3:
        factor_atac *= 1.10

    if gd_apara <= -5:
        factor_aparare *= 0.85
    elif gd_apara <= -3:
        factor_aparare *= 0.95

    if faza_competitie == 3:
        if gd_atac < 0:
            factor_atac *= 1.20
            factor_aparare *= 0.90
        elif gd_atac > 3:
            factor_atac *= 0.90
            factor_aparare *= 1.10
    elif faza_competitie == 2:
        if gd_atac >= 4:
            factor_atac *= 0.95
            factor_aparare *= 1.05

    if "cards" in TEAMS.get(echipa_ataca, {}):
        cards = TEAMS[echipa_ataca].get("cards", 0.0)
        if cards > 3.0:
            factor_atac *= 0.95
    if "cards" in TEAMS.get(echipa_apara, {}):
        cards = TEAMS[echipa_apara].get("cards", 0.0)
        if cards > 3.0:
            factor_aparare *= 1.05

    return factor_atac, factor_aparare

# ─── MODEL POISSON ──────────────────────────────────────────────────────────

def poisson_pmf(lam: float, k: int) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    if SCIPY_AVAILABLE:
        return float(sp_poisson.pmf(k, lam))
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def calc_probs(lam_h: float, lam_a: float, max_g: int = 9) -> dict:
    mat = {(gh, ga): poisson_pmf(lam_h, gh) * poisson_pmf(lam_a, ga)
           for gh in range(max_g) for ga in range(max_g)}
    p1 = sum(v for (gh, ga), v in mat.items() if gh > ga)
    px = sum(v for (gh, ga), v in mat.items() if gh == ga)
    p2 = sum(v for (gh, ga), v in mat.items() if gh < ga)
    o15 = sum(v for (gh, ga), v in mat.items() if gh + ga > 1)
    o25 = sum(v for (gh, ga), v in mat.items() if gh + ga > 2)
    o35 = sum(v for (gh, ga), v in mat.items() if gh + ga > 3)
    btts = sum(v for (gh, ga), v in mat.items() if gh > 0 and ga > 0)
    cs_h = sum(v for (gh, ga), v in mat.items() if ga == 0)
    cs_a = sum(v for (gh, ga), v in mat.items() if gh == 0)
    l1h = lam_h * R1_SHARE
    l1a = lam_a * R1_SHARE
    l1t = l1h + l1a
    o05_r1 = 1.0 - poisson_pmf(l1t, 0)
    o15_r1 = 1.0 - poisson_pmf(l1t, 0) - poisson_pmf(l1t, 1)
    return {
        "p1": round(p1, 4), "px": round(px, 4), "p2": round(p2, 4),
        "o15": round(o15, 4), "o25": round(o25, 4), "o35": round(o35, 4),
        "btts": round(btts, 4), "cs_h": round(cs_h, 4), "cs_a": round(cs_a, 4),
        "o05_r1": round(o05_r1, 4), "o15_r1": round(o15_r1, 4),
    }

def assign_tier(score: float) -> str:
    if score >= 8.5: return "S"
    if score >= 7.5: return "A"
    if score >= 6.0: return "B"
    if score >= 5.0: return "C"
    return "D"

def build_bet(probs: dict, tier: str, home: str, away: str) -> dict:
    fav = home if probs["p1"] >= probs["p2"] else away
    p_fav = max(probs["p1"], probs["p2"])
    if tier == "S":
        if probs["o35"] > 0.55:
            desc = f"Over 3.5 + {fav} câștigă + PSF 2/2"
            prob = probs["o35"] * p_fav * 0.63
        else:
            desc = f"Over 2.5 + {fav} câștigă + Over 0.5 R1"
            prob = probs["o25"] * p_fav * probs["o05_r1"]
    elif tier == "A":
        desc = f"Over 2.5 + {fav} câștigă + BTTS"
        prob = probs["o25"] * p_fav * probs["btts"]
    elif tier == "B":
        if probs["btts"] > probs["cs_h"] and probs["btts"] > probs["cs_a"]:
            desc = f"BTTS + {fav} câștigă + Over 1.5 R1"
            prob = probs["btts"] * p_fav * probs["o15_r1"]
        else:
            desc = f"Over 2.5 + {fav} câștigă"
            prob = probs["o25"] * p_fav
    else:
        desc = f"Over 1.5 + {fav} câștigă"
        prob = probs["o15"] * p_fav
    return {"description": desc, "probability": round(prob, 4)}

def generate_commentary(fx: dict, probs: dict, lam_h: float, lam_a: float,
                        tier: str) -> dict:
    h = fx["home"]; a = fx["away"]
    hn = TEAM_NAMES_RO.get(h, h); an = TEAM_NAMES_RO.get(a, a)
    fav_code = h if probs["p1"] >= probs["p2"] else a
    under_code = a if fav_code == h else h
    fav_name = TEAM_NAMES_RO.get(fav_code, fav_code)
    und_name = TEAM_NAMES_RO.get(under_code, under_code)
    p_fav = round(max(probs["p1"], probs["p2"]) * 100)
    p_draw = round(probs["px"] * 100)
    p_und = round(min(probs["p1"], probs["p2"]) * 100)
    lam_t = round(lam_h + lam_a, 2)
    o25 = round(probs["o25"] * 100)
    o35 = round(probs["o35"] * 100)
    btts = round(probs["btts"] * 100)
    csh = round(probs["cs_h"] * 100)
    csa = round(probs["cs_a"] * 100)
    o05r1 = round(probs["o05_r1"] * 100)
    o15r1 = round(probs["o15_r1"] * 100)
    alt = fx.get("alt", 0)

    if p_fav >= 90:
        fav_text = (f"{fav_name} intră ca favorit copleșitor — {p_fav}% victorie "
                    f"conform distribuției Poisson (λ {round(lam_h,1)} vs λ {round(lam_a,1)}). "
                    f"{und_name} are {p_und}% șanse și {p_draw}% egalitate.")
    elif p_fav >= 72:
        fav_text = (f"{fav_name} favorit clar — {p_fav}% victorie. "
                    f"{und_name} are {p_und}% șanse reale; egalitate {p_draw}%. "
                    f"Un gol marcat devreme de outsider poate schimba dinamica.")
    elif p_fav >= 55:
        fav_text = (f"{fav_name} favorit modest — {p_fav}% vs egalitate {p_draw}% "
                    f"vs {und_name} {p_und}%. Meci deschis, probabilitățile sunt comprimate.")
    else:
        fav_text = (f"Meci echilibrat: {hn} {probs['p1']*100:.0f}% — "
                    f"egalitate {p_draw}% — {an} {probs['p2']*100:.0f}%. "
                    f"Nicio echipă nu are avantaj statistic clar.")

    if lam_t >= 4.0:
        goals_text = (f"λ combinat {lam_t} — cel mai ridicat nivel de goluri așteptate. "
                      f"Over 2.5: {o25}% · Over 3.5: {o35}%. Meciul e structurat pentru scoruri largi.")
    elif lam_t >= 3.0:
        goals_text = (f"λ combinat {lam_t} — golaveraj ridicat. "
                      f"Over 2.5: {o25}% · Over 3.5: {o35}%. Așteptăm 3+ goluri în scenariul de bază.")
    elif lam_t >= 2.0:
        goals_text = (f"λ combinat {lam_t} — golaveraj moderat. "
                      f"Over 2.5: {o25}% · Over 1.5: {round(probs['o15']*100)}%. "
                      f"Meciul poate produce 2-3 goluri.")
    else:
        goals_text = (f"λ combinat {lam_t} — meci defensiv așteptat. "
                      f"Over 2.5: {o25}% (sub pragul de valoare). Sub 2.5 are probabilitate mai mare.")

    if btts >= 60:
        btts_text = (f"Ambele echipe marchează — BTTS: {btts}%. "
                     f"Ambele au offensive xG real și defensive vulnerabile.")
    elif btts >= 40:
        btts_text = (f"BTTS moderat: {btts}%. "
                     f"Clean sheet {hn}: {csh}% · clean sheet {an}: {csa}%. "
                     f"Outsider-ul poate marca dacă prinde o tranziție.")
    else:
        cs_team = fav_name if csh > csa else und_name
        max_cs = max(csh, csa)
        btts_text = (f"BTTS improbabil: {btts}%. "
                     f"{cs_team} are {max_cs}% șanse de clean sheet — outsider-ul riscă să nu marcheze deloc.")

    if o05r1 >= 85:
        r1_text = (f"Repriza 1 explozivă: {o05r1}% minim un gol · "
                   f"{o15r1}% peste 1.5 goluri în primele 45 min.")
    elif o05r1 >= 65:
        r1_text = f"Repriza 1 activă: {o05r1}% cel puțin un gol în prima repriză."
    else:
        r1_text = f"Repriza 1 prudentă: {o05r1}% primul gol în 45 min — echipele pot fi conservatoare."

    modifiers = []
    if alt >= 2000:
        modifiers.append(f"⚠️ Altitudine critică {alt}m ({fx['venue']}) — lambda redus cu 8%,"
                         f" joc mai lent, pressing epuizant pentru echipe ne-aclimatizate.")
    elif alt >= 1500:
        modifiers.append(f"⚠️ Altitudine moderată {alt}m ({fx['venue']}) — efect mic aplicat în model.")
    mod_text = " | ".join(modifiers) if modifiers else "Condiții standard — niciun modificator contextual activ."

    tier_texts = {
        "S": "TIER S — probabilitate 85%+ golaveraj ridicat. Selectează cu încredere în Bet Builder.",
        "A": "TIER A — probabilitate 72-84%. Solidă pentru sistemele principale.",
        "B": "TIER B — probabilitate 62-71%. Valoare bună; verifică accidentările cu 1h înainte.",
        "C": "TIER C — probabilitate 52-61%. Include doar în biletele speculative sau ca flex.",
        "D": "TIER D — sub 52%. Evită în biletele principale.",
    }
    tier_text = tier_texts.get(tier, "")

    sources_active = [
        {"name": "FBref xG Baseline", "status": "active",
         "detail": f"xGF {TEAMS[fx['home']]['xgf']} / xGA {TEAMS[fx['home']]['xga']} ({TEAM_NAMES_RO.get(fx['home'],fx['home'])})"},
        {"name": "FBref xG Baseline", "status": "active",
         "detail": f"xGF {TEAMS[fx['away']]['xgf']} / xGA {TEAMS[fx['away']]['xga']} ({TEAM_NAMES_RO.get(fx['away'],fx['away'])})"},
        {"name": "WorldCupAPI live", "status": "attempted",
         "detail": "Scoruri live — fallback la scheduled dacă API offline"},
        {"name": "API-Sports Statistics", "status": "active" if API_FOOTBALL_KEY else "inactive",
         "detail": "Statistici echipe din API-Sports" if API_FOOTBALL_KEY else "Nu este configurat API key"},
    ]
    return {
        "favorit": fav_text,
        "golaveraj": goals_text,
        "btts_cs": btts_text,
        "repriza_1": r1_text,
        "modificatori": mod_text,
        "verdict": tier_text,
        "surse": sources_active,
        "date_model": {
            "lambda_home": round(lam_h, 3),
            "lambda_away": round(lam_a, 3),
            "lambda_total": lam_t,
            "p_fav_pct": p_fav,
            "o25_pct": o25,
            "btts_pct": btts,
            "o05_r1_pct": o05r1,
        }
    }

# ─── FUNCȚIE PRINCIPALĂ ──────────────────────────────────────────────────────

def run():
    global TEAMS
    print(f"[{datetime.now(timezone.utc).isoformat()}] WC2026 Predictor pornit.")

    # 1. Audit
    try:
        run_full_audit(TEAMS, FIXTURES)
    except DataIntegrityError as exc:
        print(f"\n{'='*60}", file=sys.stderr)
        print("  ❌  AUDIT EȘUAT — Execuție oprită.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    # 2. Încărcare rezultate manuale
    results = fetch_live_fixtures_from_api()
    print(f"  → Rezultate live încărcate din API: {len(results)} meciuri.")
    if not results:
        print("  ⚠️ API-Football nu a returnat date. Se folosește fallback manual.")
        results = load_results_manual()
        print(f"  → Fallback manual: {len(results)} meciuri.")
    if len(results) == 0:
        print("  ⚠️  ATENȚIE: Nu s-au încărcat rezultate! Verifică calea fișierului.")
        print(f"  → Calea căutată: {RESULTS_FILE}")
        print(f"  → Există fișierul? {os.path.exists(RESULTS_FILE)}")
        
    # 3. Îmbogățire date echipe din API-Sports
    if API_FOOTBALL_KEY:
        print("  → Se încearcă îmbogățirea datelor echipelor din API-Sports...")
        TEAMS = enrich_team_data_from_api(TEAMS)
        print("  → Date îmbogățite.")
    else:
        print("  → API-Sports key lipsă, se folosesc date statice.")

    # 4. Calcul pentru fiecare meci
    results_list = []
    for fx in FIXTURES:
        h, a = fx["home"], fx["away"]
        th = TEAMS[h]
        ta = TEAMS[a]

        lam_h = th["xgf"] * (ta["xga"] / GLOBAL_AVG_XGA)
        lam_a = ta["xgf"] * (th["xga"] / GLOBAL_AVG_XGA)

        if fx.get("alt", 0) >= ALT_THRESHOLD:
            lam_h *= ALT_FACTOR
            lam_a *= ALT_FACTOR

        faza = fx.get("md", 1)
        factor_atac, factor_aparare = aplica_modificator_contextual(h, a, faza, results)
        lam_h *= factor_atac
        lam_a *= factor_aparare

        probs = calc_probs(lam_h, lam_a)
        fav_strength = abs(probs["p1"] - probs["p2"])
        score = (probs["o25"] * 0.45 + probs["btts"] * 0.25
                 + probs["o05_r1"] * 0.15 + fav_strength * 0.15) * 10
        tier = assign_tier(score)
        bet = build_bet(probs, tier, h, a)

        rid = fx["id"]
        if rid in results and results[rid].get("status") == "finished":
            actual_h = results[rid]["home_score"]
            actual_a = results[rid]["away_score"]
            status = "finished"
        else:
            actual_h = None
            actual_a = None
            status = "scheduled"

        fav_code = h if probs["p1"] >= probs["p2"] else a
        pred_outcome = None
        if status == "finished" and actual_h is not None:
            if actual_h > actual_a:
                actual_winner = h
            elif actual_a > actual_h:
                actual_winner = a
            else:
                actual_winner = "draw"
            if fav_code == actual_winner:
                pred_outcome = "correct"
            elif probs["px"] > 0.30 and actual_winner == "draw":
                pred_outcome = "draw_hit"
            else:
                pred_outcome = "wrong"

        commentary = generate_commentary(fx, probs, lam_h, lam_a, tier)

        results_list.append({
            "id": fx["id"],
            "home": h,
            "home_name": TEAM_NAMES_RO.get(h, h),
            "away": a,
            "away_name": TEAM_NAMES_RO.get(a, a),
            "group": fx["group"],
            "matchday": fx["md"],
            "date": fx["date"],
            "venue": fx["venue"],
            "status": status,
            "score": {"home": actual_h, "away": actual_a},
            "prediction": {
                "favorite": fav_code,
                "fav_name": TEAM_NAMES_RO.get(fav_code, fav_code),
                "outcome": pred_outcome,
            },
            "lambda": {"home": round(lam_h, 3), "away": round(lam_a, 3)},
            "probs": probs,
            "ranking_score": round(score, 3),
            "tier": tier,
            "bet": bet,
            "commentary": commentary,
        })

    results_list.sort(key=lambda x: x["ranking_score"], reverse=True)
    top = [r for r in results_list if r["tier"] in ("S", "A", "B")][:15]

    def make_ticket(ev_ids, label, note):
        evs = [r for r in results_list if r["id"] in ev_ids]
        if not evs:
            return {"label": label, "note": note, "events": [], "combined_odds": 1, "combined_prob_pct": 100}
        odds = math.prod(1 / max(r["bet"]["probability"], 0.01) * 0.90 for r in evs)
        prob = math.prod(max(r["bet"]["probability"], 0.01) for r in evs)
        return {
            "label": label, "note": note,
            "events": [{"id": r["id"], "match": f"{r['home']} vs {r['away']}",
                        "bet": r["bet"]["description"],
                        "prob_pct": round(r["bet"]["probability"] * 100, 1)}
                       for r in evs],
            "combined_odds": round(odds, 1),
            "combined_prob_pct": round(prob * 100, 3),
        }

    s_ids = [r["id"] for r in results_list if r["tier"] == "S"][:7]
    a_ids = [r["id"] for r in results_list if r["tier"] == "A"][:8]

    tickets = [
        make_ticket(s_ids[:7], "Bilet A — Maxim Sigur", "Tier S × 7. Cotă ~15–50x"),
        make_ticket(s_ids[:5] + a_ids[:2], "Bilet B — S+A Balansate", "5 Tier S + 2 Tier A. Cotă ~20–70x"),
        make_ticket(s_ids[:4] + a_ids[2:6], "Bilet C — S+A Temporal", "4S + 4A pe date diferite. ~30–90x"),
        make_ticket(s_ids[:3] + a_ids[:4], "Bilet D — Speculativ", "Include selecții BTTS. ~80–300x"),
        make_ticket(a_ids[:7], "Bilet E — Contra-Hedge", "Complet diferit de A. ~25–80x"),
    ]

    output = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tournament": "FIFA World Cup 2026",
            "total_matches": len(results_list),
            "live_available": bool(results),
            "model_version": "1.1-poisson-contextual",
        },
        "top_30": results_list[:30],
        "all_72": results_list,
        "tickets": tickets,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  ✅ predictii_avansate.json scris ({len(results_list)} meciuri, {len(tickets)} bilete).")

if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        sys.exit(1)