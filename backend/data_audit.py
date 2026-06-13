"""
world-cup-predictor/backend/data_audit.py
─────────────────────────────────────────────────────────────────────────────
Strat de integritate a datelor — rulat ÎNAINTE de orice calcul Poisson.

PRINCIPII:
  • Fail-Fast  : prima problemă detectată oprește execuția imediat.
  • Imutabilitate: zero valori implicite / fallback. Dacă datele lipsesc → crash.
  • Single Source of Truth: OFFICIAL_48_TEAMS este registrul canonical.
  • Auditabil  : fiecare eroare specifică exact echipa/meciul/câmpul vinovat.

UTILIZARE:
  from data_audit import run_full_audit
  run_full_audit(TEAMS, FIXTURES)   # ridică DataIntegrityError dacă ceva e greșit
"""

from __future__ import annotations
from typing import Any

# ─── EXCEPȚIE PERSONALIZATĂ ───────────────────────────────────────────────────

class DataIntegrityError(Exception):
    """
    Ridicată când validarea datelor eșuează.
    Conține contextul complet al problemei pentru debugging rapid.

    Exemplu output:
        DataIntegrityError: [TEAM_MISSING_FIELD] Echipa 'QAT' — câmp 'xgf' este None.
          → team       : QAT
          → field      : xgf
          → value      : None
          → fix        : Adaugă valoarea xgf pentru QAT în dicționarul TEAMS din main.py
          → audit_step : validate_team_data
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        self.context: dict[str, Any] = context or {}
        super().__init__(message)

    def __str__(self) -> str:
        base = super().__str__()
        if not self.context:
            return base
        details = "\n".join(f"  → {k:<14}: {v}" for k, v in self.context.items())
        return f"{base}\n{details}"


# ─── REGISTRUL OFICIAL — SURSA DE ADEVĂR ─────────────────────────────────────

# Cele 48 de echipe calificate la CM 2026.
# Orice echipă din TEAMS sau FIXTURES care NU apare aici → eroare imediată.
# Orice echipă din această listă care NU are date în TEAMS → eroare imediată.

OFFICIAL_48_TEAMS: frozenset[str] = frozenset({
    # ── TIER 1 — ELITE (rank 1–10, xGF > 2.0) ────────────────────────────
    "ARG",  # Argentina       — Rank 1
    "FRA",  # Franța          — Rank 2
    "BEL",  # Belgia          — Rank 3
    "ENG",  # Anglia          — Rank 4
    "BRA",  # Brazilia        — Rank 5
    "ESP",  # Spania          — Rank 6
    "POR",  # Portugalia      — Rank 7
    "NED",  # Olanda          — Rank 8
    # ── TIER 2 — PUTERNICI (rank 11–30, xGF 1.5–2.1) ─────────────────────
    "COL",  # Columbia        — Rank 9
    "GER",  # Germania        — Rank 13
    "MAR",  # Maroc           — Rank 14
    "CRO",  # Croația         — Rank 15
    "USA",  # SUA             — Rank 16
    "JPN",  # Japonia         — Rank 17
    "URU",  # Uruguay         — Rank 18
    "SUI",  # Elveția         — Rank 19
    "SEN",  # Senegal         — Rank 20
    "KOR",  # Coreea de Sud   — Rank 21
    "NOR",  # Norvegia        — Rank 22
    "AUT",  # Austria         — Rank 26
    "TUR",  # Turcia          — Rank 29
    "SWE",  # Suedia          — Rank 25
    "MEX",  # Mexic           — Rank 11
    # ── TIER 3 — COMPETITIVI (rank 31–70, xGF 1.0–1.5) ───────────────────
    "EGY",  # Egipt           — Rank 31
    "CZE",  # Cehia           — Rank 34
    "SCO",  # Scoția          — Rank 38
    "CAN",  # Canada          — Rank 41
    "ECU",  # Ecuador         — Rank 44
    "ALG",  # Algeria         — Rank 46
    "BIH",  # Bosnia-Herțeg.  — Rank 55
    "KSA",  # Arabia Saudită  — Rank 56
    "AUS",  # Australia       — Rank 59
    "GHA",  # Ghana           — Rank 60
    "PAR",  # Paraguay        — Rank 68
    "CIV",  # Coasta de Fildeș— Rank 52
    "IRN",  # Iran            — Rank 24
    "RSA",  # Africa de Sud   — Rank 67
    # ── TIER 4 — OUTSIDERI (rank 71+, xGF < 1.0) ─────────────────────────
    "IRQ",  # Irak            — Rank 71
    "TUN",  # Tunisia         — Rank 74
    "CPV",  # Capul Verde     — Rank 91
    "HAI",  # Haiti           — Rank 88
    "JOR",  # Iordania        — Rank 87
    "PAN",  # Panama          — Rank 89
    "NZL",  # Noua Zeelandă   — Rank 103
    "COD",  # Congo DR        — Rank 98
    "UZB",  # Uzbekistan      — Rank 107
    "CUR",  # Curaçao         — Rank 112
    "QAT",  # Qatar           — Rank 43
})

# Verificare la import că avem exact 48
assert len(OFFICIAL_48_TEAMS) == 48, (
    f"OFFICIAL_48_TEAMS conține {len(OFFICIAL_48_TEAMS)} echipe, nu 48! "
    "Verifică lista de mai sus."
)

# ─── SPECIFICAȚII CÂMPURI ECHIPE ─────────────────────────────────────────────

# format: "câmp": (valoare_minimă, valoare_maximă, permite_None)
TEAM_FIELD_SPECS: dict[str, tuple[float, float, bool]] = {
    "xgf":  (0.05, 4.50, False),   # Expected Goals For / meci
    "xga":  (0.05, 4.50, False),   # Expected Goals Against / meci
    "form": (1.00, 10.0, False),   # Rating formă echipă (WhoScored scale)
    "rank": (1,    250,  False),   # Ranking FIFA
}

# Câmpuri obligatorii per fixture
FIXTURE_REQUIRED_KEYS: frozenset[str] = frozenset({
    "id", "home", "away", "group", "md", "date", "venue", "alt"
})

EXPECTED_FIXTURES    = 72
EXPECTED_GROUPS      = 12
EXPECTED_PER_GROUP   = 6   # meciuri per grupă (C(4,2) = 6)


# ─── FUNCȚII DE VALIDARE ──────────────────────────────────────────────────────

def _raise(code: str, msg: str, **ctx) -> None:
    """Helper intern: ridică DataIntegrityError cu cod și context."""
    raise DataIntegrityError(
        f"[{code}] {msg}",
        context={**ctx, "audit_step": _raise.__name__}  # suprascris de caller
    )


def validate_official_registry(teams: dict) -> None:
    """
    Pas 1 — Cross-check bilateral:
      a) Echipe din TEAMS care NU sunt în registrul oficial → probabil typo.
      b) Echipe din registrul oficial care NU au date în TEAMS → lipsă date.
    """
    teams_set = frozenset(teams.keys())

    # a) Echipe extra (necunoscute)
    extra = teams_set - OFFICIAL_48_TEAMS
    if extra:
        raise DataIntegrityError(
            f"[UNKNOWN_TEAMS] {len(extra)} echipă/echipe din TEAMS nu există "
            f"în registrul oficial CM 2026.",
            context={
                "unknown_teams":  sorted(extra),
                "hint":           "Verifică typo-uri în codurile de echipă (3 litere).",
                "audit_step":     "validate_official_registry",
            }
        )

    # b) Echipe lipsă din TEAMS
    missing = OFFICIAL_48_TEAMS - teams_set
    if missing:
        raise DataIntegrityError(
            f"[MISSING_TEAMS] {len(missing)} echipă/echipe din registrul oficial "
            f"NU au date statistice în TEAMS.",
            context={
                "missing_teams":  sorted(missing),
                "fix":            "Adaugă intrările lipsă în dicționarul TEAMS din main.py",
                "audit_step":     "validate_official_registry",
            }
        )


def validate_team_data(teams: dict) -> None:
    """
    Pas 2 — Validare câmp cu câmp pentru fiecare echipă:
      • Niciun câmp nu poate fi None / NaN / lipsă.
      • Valorile trebuie să fie în intervalele definite în TEAM_FIELD_SPECS.
      • Zero fallback-uri implicite permise.
    """
    import math

    for code, data in teams.items():
        if not isinstance(data, dict):
            raise DataIntegrityError(
                f"[INVALID_TEAM_TYPE] Datele pentru '{code}' nu sunt un dict.",
                context={"team": code, "type_found": type(data).__name__,
                         "audit_step": "validate_team_data"}
            )

        for field, (vmin, vmax, allow_none) in TEAM_FIELD_SPECS.items():
            # Câmp complet absent
            if field not in data:
                raise DataIntegrityError(
                    f"[MISSING_FIELD] Echipa '{code}' — câmpul '{field}' lipsește complet.",
                    context={
                        "team":       code,
                        "field":      field,
                        "fix":        f"Adaugă '{field}': <valoare> în TEAMS['{code}']",
                        "audit_step": "validate_team_data",
                    }
                )

            val = data[field]

            # None
            if val is None:
                if allow_none:
                    continue
                raise DataIntegrityError(
                    f"[NULL_FIELD] Echipa '{code}' — câmp '{field}' este None.",
                    context={
                        "team":       code,
                        "field":      field,
                        "value":      None,
                        "fix":        "Înlocuiește None cu valoarea reală din FBref/WhoScored.",
                        "audit_step": "validate_team_data",
                    }
                )

            # NaN / Inf (float corupt)
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                raise DataIntegrityError(
                    f"[NAN_FIELD] Echipa '{code}' — câmp '{field}' este NaN/Inf.",
                    context={
                        "team":       code,
                        "field":      field,
                        "value":      val,
                        "fix":        "Valoare float coruptă — reverificat sursa de date.",
                        "audit_step": "validate_team_data",
                    }
                )

            # Tip incorect
            if not isinstance(val, (int, float)):
                raise DataIntegrityError(
                    f"[WRONG_TYPE] Echipa '{code}' — câmp '{field}' nu e numeric.",
                    context={
                        "team":       code,
                        "field":      field,
                        "value":      val,
                        "type_found": type(val).__name__,
                        "audit_step": "validate_team_data",
                    }
                )

            # În afara intervalului valid
            if not (vmin <= val <= vmax):
                raise DataIntegrityError(
                    f"[OUT_OF_RANGE] Echipa '{code}' — câmp '{field}' = {val} "
                    f"este în afara intervalului [{vmin}, {vmax}].",
                    context={
                        "team":        code,
                        "field":       field,
                        "value":       val,
                        "valid_range": f"[{vmin}, {vmax}]",
                        "fix":         "Actualizează valoarea în TEAMS sau verifică sursa.",
                        "audit_step":  "validate_team_data",
                    }
                )


def validate_fixtures(fixtures: list, teams: dict) -> None:
    """
    Pas 3 — Validare structurală a celor 72 de meciuri:
      • Număr exact de meciuri: 72.
      • ID-uri unice.
      • Toate câmpurile obligatorii prezente și non-null.
      • home/away referențiază echipe din TEAMS (validate anterior).
      • Numărul corect de meciuri per grupă.
    """
    # 3a. Număr total
    if len(fixtures) != EXPECTED_FIXTURES:
        raise DataIntegrityError(
            f"[WRONG_FIXTURE_COUNT] {len(fixtures)} meciuri găsite, "
            f"așteptate {EXPECTED_FIXTURES}.",
            context={
                "found":      len(fixtures),
                "expected":   EXPECTED_FIXTURES,
                "fix":        "Verifică lista FIXTURES din main.py — trebuie să conțină exact 72.",
                "audit_step": "validate_fixtures",
            }
        )

    # 3b. ID-uri duplicate
    ids = [fx["id"] for fx in fixtures if "id" in fx]
    seen, dupes = set(), set()
    for fid in ids:
        (dupes if fid in seen else seen).add(fid)
    if dupes:
        raise DataIntegrityError(
            f"[DUPLICATE_FIXTURE_IDS] ID-uri duplicate detectate.",
            context={
                "duplicate_ids": sorted(dupes),
                "fix":           "Fiecare meci trebuie să aibă un ID unic (ex: 'A1'..'L6').",
                "audit_step":    "validate_fixtures",
            }
        )

    # 3c. Câmpuri per fixture + referință echipe
    groups_seen: dict[str, set[str]] = {}

    for fx in fixtures:
        fid = fx.get("id", "<unknown>")

        # Câmpuri obligatorii
        missing_keys = FIXTURE_REQUIRED_KEYS - set(fx.keys())
        if missing_keys:
            raise DataIntegrityError(
                f"[MISSING_FIXTURE_KEYS] Meciul '{fid}' lipsesc câmpuri obligatorii.",
                context={
                    "fixture_id":    fid,
                    "missing_keys":  sorted(missing_keys),
                    "fix":           "Adaugă câmpurile lipsă în FIXTURES din main.py.",
                    "audit_step":    "validate_fixtures",
                }
            )

        # Nicio valoare None în câmpuri critice
        for key in FIXTURE_REQUIRED_KEYS:
            if fx.get(key) is None:
                raise DataIntegrityError(
                    f"[NULL_FIXTURE_FIELD] Meciul '{fid}' — câmpul '{key}' este None.",
                    context={
                        "fixture_id": fid,
                        "field":      key,
                        "fix":        "Înlocuiește None cu valoarea corectă.",
                        "audit_step": "validate_fixtures",
                    }
                )

        # home/away există în TEAMS
        for side in ("home", "away"):
            code = fx.get(side)
            if code not in teams:
                raise DataIntegrityError(
                    f"[UNKNOWN_TEAM_IN_FIXTURE] Meciul '{fid}' — "
                    f"echipa '{code}' ({side}) nu are date statistice.",
                    context={
                        "fixture_id":  fid,
                        "side":        side,
                        "team_code":   code,
                        "fix":         f"Adaugă '{code}' în TEAMS sau corectează codul.",
                        "audit_step":  "validate_fixtures",
                    }
                )

        # Colectare echipe per grupă pentru Pasul 3d
        grp = fx.get("group", "?")
        groups_seen.setdefault(grp, set())
        groups_seen[grp].add(fx["home"])
        groups_seen[grp].add(fx["away"])

    # 3d. 12 grupe cu exact 4 echipe fiecare
    if len(groups_seen) != EXPECTED_GROUPS:
        raise DataIntegrityError(
            f"[WRONG_GROUP_COUNT] {len(groups_seen)} grupe detectate, "
            f"așteptate {EXPECTED_GROUPS}.",
            context={
                "found_groups": sorted(groups_seen.keys()),
                "audit_step":   "validate_fixtures",
            }
        )

    for grp, team_set in groups_seen.items():
        if len(team_set) != 4:
            raise DataIntegrityError(
                f"[WRONG_TEAMS_IN_GROUP] Grupa '{grp}' are {len(team_set)} echipe, "
                f"așteptate 4.",
                context={
                    "group":      grp,
                    "teams_found": sorted(team_set),
                    "expected":   4,
                    "fix":        "Verifică că toate cele 6 meciuri ale grupei sunt prezente.",
                    "audit_step": "validate_fixtures",
                }
            )

    # 3e. Număr meciuri per grupă (C(4,2) = 6)
    group_counts: dict[str, int] = {}
    for fx in fixtures:
        grp = fx.get("group", "?")
        group_counts[grp] = group_counts.get(grp, 0) + 1

    for grp, cnt in group_counts.items():
        if cnt != EXPECTED_PER_GROUP:
            raise DataIntegrityError(
                f"[WRONG_MATCH_COUNT_IN_GROUP] Grupa '{grp}' are {cnt} meciuri, "
                f"așteptate {EXPECTED_PER_GROUP}.",
                context={
                    "group":      grp,
                    "count":      cnt,
                    "expected":   EXPECTED_PER_GROUP,
                    "audit_step": "validate_fixtures",
                }
            )


def validate_no_duplicates_in_group(fixtures: list) -> None:
    """
    Pas 4 — Verifică că nicio pereche (home, away) nu apare de două ori
    în aceeași grupă (meci duplicat sub forme inversate: A vs B și B vs A).
    """
    seen_pairs: set[frozenset] = set()
    for fx in fixtures:
        pair = frozenset({fx["home"], fx["away"]})
        if pair in seen_pairs:
            raise DataIntegrityError(
                f"[DUPLICATE_MATCHUP] Meciul {fx['home']} vs {fx['away']} "
                f"apare de două ori în lista de fixture-uri.",
                context={
                    "fixture_id":  fx["id"],
                    "home":        fx["home"],
                    "away":        fx["away"],
                    "fix":         "Șterge duplicatul din FIXTURES.",
                    "audit_step":  "validate_no_duplicates_in_group",
                }
            )
        seen_pairs.add(pair)


# ─── AUDIT COMPLET ────────────────────────────────────────────────────────────

def run_full_audit(teams: dict, fixtures: list) -> None:
    """
    Punct de intrare principal. Rulează toți pașii în ordine.
    La prima problemă detectată → DataIntegrityError imediat.
    Dacă totul e OK → returnează None silențios.

    Integrare în main.py:
        from data_audit import run_full_audit, DataIntegrityError
        try:
            run_full_audit(TEAMS, FIXTURES)
        except DataIntegrityError as e:
            print(f"AUDIT EȘUAT:\\n{e}")
            sys.exit(1)
    """

    steps = [
        ("1/4 Registru oficial (48 echipe)",    lambda: validate_official_registry(teams)),
        ("2/4 Date statistice echipe",           lambda: validate_team_data(teams)),
        ("3/4 Structură fixture-uri (72 meciuri)", lambda: validate_fixtures(fixtures, teams)),
        ("4/4 Duplicare matchup-uri",            lambda: validate_no_duplicates_in_group(fixtures)),
    ]

    print("─" * 60)
    print("  DATA AUDIT — CM 2026 Predictor")
    print("─" * 60)

    for label, fn in steps:
        print(f"  [ RUN ] {label} ...", end=" ", flush=True)
        fn()   # ridică DataIntegrityError dacă eșuează
        print("✅ OK")

    print("─" * 60)
    print(f"  AUDIT PASSED — {len(teams)} echipe · {len(fixtures)} meciuri · 0 erori")
    print("─" * 60)
