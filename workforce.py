"""
workforce.py — Tampines Estate Reporter
Real 7-agency, 2-officer roster aligned with agents.py _OFFICER_ROSTER.

Each agency has exactly 2 named officers.
Live workload (open cases per officer) is read from the database.
The capacity checker and /workforce endpoint use this data.
"""

import random
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# AGENCY ROSTER — mirrors _OFFICER_ROSTER in agents.py exactly
# Each agency: 2 officers, icon, full name, categories they handle.
# ─────────────────────────────────────────────────────────────────────────────

AGENCY_ROSTER = {
    "NEA": {
        "full_name":      "National Environment Agency",
        "icon":           "🌿",
        "department":     "Environmental Health & Enforcement",
        "shift_hours":    "8:00 AM – 10:00 PM",
        "total_strength": 2,
        "categories":     ["cleanliness", "pest", "noise", "electrical"],
        "officers": [
            {"id": "NEA-01", "name": "Officer Lim Wei Jie",  "tier": 2},
            {"id": "NEA-02", "name": "Officer Priya Nair",   "tier": 2},
        ],
    },
    "Town Council": {
        "full_name":      "Tampines Town Council",
        "icon":           "🏘️",
        "department":     "Estate Management & Operations",
        "shift_hours":    "7:00 AM – 11:00 PM",
        "total_strength": 2,
        "categories":     ["structural", "electrical", "safety", "water", "cleanliness", "greenery", "vehicles", "noise"],
        "officers": [
            {"id": "TC-01",  "name": "Officer Ahmad Fauzi",  "tier": 2},
            {"id": "TC-02",  "name": "Officer Rachel Teo",   "tier": 2},
        ],
    },
    "PUB": {
        "full_name":      "Public Utilities Board",
        "icon":           "💧",
        "department":     "Water & Drainage Operations",
        "shift_hours":    "24 Hours",
        "total_strength": 2,
        "categories":     ["water"],
        "officers": [
            {"id": "PUB-01", "name": "Officer Tan Boon Kiat",  "tier": 2},
            {"id": "PUB-02", "name": "Officer Suresh Kumar",   "tier": 2},
        ],
    },
    "SCDF": {
        "full_name":      "Singapore Civil Defence Force",
        "icon":           "🚒",
        "department":     "Fire Safety & Emergency Response",
        "shift_hours":    "24 Hours",
        "total_strength": 2,
        "categories":     ["safety"],
        "officers": [
            {"id": "SCDF-01", "name": "Officer Jason Ng",      "tier": 1},
            {"id": "SCDF-02", "name": "Officer Hafiz Roslan",  "tier": 1},
        ],
    },
    "Police": {
        "full_name":      "Singapore Police Force",
        "icon":           "👮",
        "department":     "Public Order & Enforcement",
        "shift_hours":    "24 Hours",
        "total_strength": 2,
        "categories":     ["noise", "safety"],
        "officers": [
            {"id": "SPF-01", "name": "Officer Chua Mei Ling", "tier": 1},
            {"id": "SPF-02", "name": "Officer David Raj",     "tier": 1},
        ],
    },
    "LTA": {
        "full_name":      "Land Transport Authority",
        "icon":           "🚗",
        "department":     "Traffic & Vehicle Operations",
        "shift_hours":    "8:00 AM – 10:00 PM",
        "total_strength": 2,
        "categories":     ["vehicles"],
        "officers": [
            {"id": "LTA-01", "name": "Officer Wong Kah Hoe",  "tier": 2},
            {"id": "LTA-02", "name": "Officer Nur Aisyah",    "tier": 2},
        ],
    },
    "NParks": {
        "full_name":      "National Parks Board",
        "icon":           "🌳",
        "department":     "Parks & Greenery Management",
        "shift_hours":    "7:00 AM – 7:00 PM",
        "total_strength": 2,
        "categories":     ["greenery", "safety"],
        "officers": [
            {"id": "NP-01",  "name": "Officer Eugene Loh",    "tier": 2},
            {"id": "NP-02",  "name": "Officer Siti Rahayu",   "tier": 2},
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# LIVE WORKLOAD — reads open-case count per officer from DB
# ─────────────────────────────────────────────────────────────────────────────

def _load_workload_for_agency(agency_name: str) -> dict:
    """Return {officer_name: open_case_count} for all officers in an agency."""
    roster = AGENCY_ROSTER.get(agency_name, {})
    officers = roster.get("officers", [])
    workload = {o["name"]: 0 for o in officers}
    try:
        from database import get_all_cases
        for case in get_all_cases():
            if (case.get("status") or "Open") == "Resolved":
                continue
            # cases.agencies is a pipe-separated string of agency short names
            case_agencies = [a.strip() for a in (case.get("agencies") or "").split("|")]
            if agency_name not in case_agencies:
                continue
            name = (case.get("assigned_officer") or "").strip()
            if name in workload:
                workload[name] += 1
    except Exception as exc:
        print(f"[WORKFORCE] workload query failed: {exc}")
    return workload


# ─────────────────────────────────────────────────────────────────────────────
# AVAILABILITY SNAPSHOT
# ─────────────────────────────────────────────────────────────────────────────

def get_staff_availability(agency_name: str) -> dict:
    """
    Return live availability snapshot for an agency.
    Officer status is derived from their actual open-case count in the DB.
    """
    agency = AGENCY_ROSTER.get(agency_name)
    if not agency:
        return {"error": f"No roster for {agency_name}"}

    workload = _load_workload_for_agency(agency_name)

    officers_out  = []
    total_free    = 0
    total_on_case = 0

    for off in agency["officers"]:
        open_cases = workload.get(off["name"], 0)

        # Status from real DB load
        if open_cases == 0:
            status    = "free"
            free_n    = 1
            on_case_n = 0
        elif open_cases <= 2:
            status    = "on_case"
            free_n    = 0
            on_case_n = 1
        else:
            status    = "at_capacity"
            free_n    = 0
            on_case_n = 1

        total_free    += free_n
        total_on_case += on_case_n

        officers_out.append({
            "id":         off["id"],
            "name":       off["name"],
            "tier":       off["tier"],
            "open_cases": open_cases,
            "status":     status,          # "free" | "on_case" | "at_capacity"
            "free":       free_n,
            "on_case":    on_case_n,
        })

    total_on_duty  = len(agency["officers"])
    util_pct = round((total_on_case / max(total_on_duty, 1)) * 100)

    return {
        "agency":          agency_name,
        "full_name":       agency["full_name"],
        "icon":            agency["icon"],
        "department":      agency["department"],
        "total_strength":  agency["total_strength"],
        "shift_hours":     agency["shift_hours"],
        "categories":      agency["categories"],
        "total_on_duty":   total_on_duty,
        "total_free":      total_free,
        "total_on_case":   total_on_case,
        "utilisation_pct": util_pct,
        "officers":        officers_out,
        "snapshot_time":   datetime.now().strftime("%d %b %Y, %H:%M"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# BEST-FIT OFFICER SELECTION
# ─────────────────────────────────────────────────────────────────────────────

def find_best_officer(availability: dict, category: str, priority: str) -> Optional[dict]:
    """Pick the officer with the fewest open cases (load-balance). Prefer free."""
    officers = availability.get("officers", [])
    if not officers:
        return None
    # Sort: free first, then by open_cases ascending
    return min(officers, key=lambda o: (o["open_cases"] >= 3, o["open_cases"]))


# ─────────────────────────────────────────────────────────────────────────────
# CAPACITY ANALYSIS — main entry point called by agents.py
# ─────────────────────────────────────────────────────────────────────────────

SLA_HOURS = {
    "IMMEDIATE":      0.5,
    "4 hours":        4,
    "24 hours":       24,
    "48 hours":       48,
    "2 working days": 16,
    "3 working days": 24,
    "5 working days": 40,
}

_RESPONSE_HRS_BY_PRIORITY = {
    "CRITICAL": 1,
    "HIGH":     2,
    "MEDIUM":   4,
    "LOW":      8,
}


def analyze_capacity(agency_name: str, category: str, priority: str, sla: str) -> dict:
    """
    Full capacity analysis for a single incoming case.
    Uses real DB workload, not random simulation.
    """
    availability = get_staff_availability(agency_name)
    if "error" in availability:
        return {"error": availability["error"]}

    best_officer = find_best_officer(availability, category, priority)
    free_count   = availability["total_free"]
    util_pct     = availability["utilisation_pct"]
    base_hrs     = _RESPONSE_HRS_BY_PRIORITY.get(priority.upper(), 4)

    # Extra delay if officer is already busy
    if best_officer:
        load = best_officer["open_cases"]
        if load >= 3:
            delay_multiplier = 3.0
        elif load >= 1:
            delay_multiplier = 2.0
        else:
            delay_multiplier = 1.0
    else:
        delay_multiplier = 3.0

    estimated_hrs = round(base_hrs * delay_multiplier, 1)

    # Verdict
    if free_count == 0 or util_pct >= 100:
        verdict = "🔴 Understaffed"
        has_cap = False
    elif util_pct >= 50:
        verdict = "⚠️ Stretched"
        has_cap = True
    else:
        verdict = "✅ Sufficient"
        has_cap = True

    # Human-readable note
    if not best_officer:
        note = (
            f"No officers available for {agency_name} right now. "
            f"All {availability['total_on_duty']} officers are at capacity. "
            f"Estimated wait: {estimated_hrs} hrs."
        )
    elif verdict == "🔴 Understaffed":
        note = (
            f"{agency_name} is understaffed ({util_pct}% utilisation). "
            f"This {priority.upper()} case will be queued. "
            f"Estimated response: {estimated_hrs} hrs (SLA: {sla})."
        )
    elif verdict == "⚠️ Stretched":
        note = (
            f"Staff stretched — '{best_officer['name']}' available but has {best_officer['open_cases']} open case(s). "
            f"Estimated response: {estimated_hrs} hrs (SLA: {sla})."
        )
    else:
        note = (
            f"'{best_officer['name']}' is free with {best_officer['open_cases']} open cases. "
            f"Estimated response within {estimated_hrs} hrs (SLA: {sla})."
        )

    return {
        "agency":                  agency_name,
        "category":                category,
        "priority":                priority,
        "sla":                     sla,
        "has_capacity":            has_cap,
        "assigned_position":       best_officer,   # keeps same key name for DB compat
        "free_staff_count":        free_count,
        "on_duty_count":           availability["total_on_duty"],
        "utilisation_pct":         util_pct,
        "estimated_response_hrs":  estimated_hrs,
        "queue_delay_hrs":         0,
        "queue_cases_ahead":       availability["total_on_case"],
        "capacity_verdict":        verdict,
        "capacity_note":           note,
        "staff_snapshot":          availability,
    }


def analyze_capacity_for_routes(routes: list) -> list:
    """
    Run capacity analysis for every route in the dispatch list.
    Attaches capacity info directly to each route dict (mutates + returns).
    """
    for route in routes:
        agency   = route.get("agency", "")
        category = route.get("category", "general")
        priority = route.get("priority", "MEDIUM")
        sla      = route.get("sla", "24 hours")

        cap = analyze_capacity(agency, category, priority, sla)
        route["capacity"] = cap

    return routes