import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─────────────────────────────────────────
# AGENT CONFIG
# ─────────────────────────────────────────
SENDGRID_API_KEY  = os.getenv("SENDGRID_API_KEY")
TWILIO_SID        = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN      = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_PHONE = os.getenv("TWILIO_FROM_PHONE")
FROM_EMAIL        = os.getenv("FROM_EMAIL", "eaglee00011@gmail.com")
FROM_NAME         = "Tampines Estate Reporter"

DEMO_MODE  = os.getenv("DEMO_MODE", "false").lower() == "true"
TEST_MODE  = os.getenv("TEST_MODE", "false").lower() == "true"
TEST_EMAIL = os.getenv("TEST_EMAIL", "")
TEST_PHONE = os.getenv("TEST_PHONE", "")


# ─────────────────────────────────────────
# FULL 61-TYPE AGENCY ROUTING TABLE
# Real agencies: PUB, NEA, SCDF, Police, Town Council, LTA, NParks
# ─────────────────────────────────────────
AGENCY_ROUTING = {
    # ── CLEANLINESS → NEA ─────────────────────────────────────────────────
    "plastic_litter":       {"agency": "NEA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "cleanliness"},
    "food_waste":           {"agency": "NEA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "cleanliness"},
    "cigarette_butt":       {"agency": "NEA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "cleanliness"},
    "dry_leaves":           {"agency": "NEA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "cleanliness"},
    "bulky_item":           {"agency": "NEA",          "email": FROM_EMAIL, "sla": "48 hours",       "category": "cleanliness"},
    "high_rise_litter":     {"agency": "NEA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "cleanliness"},
    "overflowing_bin":      {"agency": "NEA",          "email": FROM_EMAIL, "sla": "4 hours",        "category": "cleanliness"},
    "illegal_dump":         {"agency": "NEA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "cleanliness"},

    # ── STRUCTURAL / MAINTENANCE → Town Council ───────────────────────────
    "broken_pipe":          {"agency": "Town Council", "email": FROM_EMAIL, "sla": "4 hours",        "category": "structural"},
    "broken_wire":          {"agency": "Town Council", "email": FROM_EMAIL, "sla": "4 hours",        "category": "structural"},
    "road_crack":           {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},
    "footpath_crack":       {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},
    "broken_drain":         {"agency": "Town Council", "email": FROM_EMAIL, "sla": "24 hours",       "category": "structural"},
    "broken_playground":    {"agency": "Town Council", "email": FROM_EMAIL, "sla": "24 hours",       "category": "structural"},
    "lift_fault":           {"agency": "Town Council", "email": FROM_EMAIL, "sla": "4 hours",        "category": "structural"},
    "broken_letterbox":     {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},
    "broken_railing":       {"agency": "Town Council", "email": FROM_EMAIL, "sla": "24 hours",       "category": "structural"},
    "wall_crack":           {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},
    "broken_sign":          {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},
    "broken_bench":         {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},
    "broken_shelter":       {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},
    "broken_bin":           {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},
    "damaged_cctv":         {"agency": "Town Council", "email": FROM_EMAIL, "sla": "3 working days", "category": "structural"},

    # ── ELECTRICAL → Town Council ──────────────────────────────────────────
    "streetlight_fault":    {"agency": "Town Council", "email": FROM_EMAIL, "sla": "24 hours",       "category": "electrical"},
    "power_box":            {"agency": "Town Council", "email": FROM_EMAIL, "sla": "4 hours",        "category": "electrical"},
    "battery_waste":        {"agency": "NEA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "electrical"},
    "discarded_appliance":  {"agency": "NEA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "electrical"},

    # ── WATER / DRAINAGE → PUB ────────────────────────────────────────────
    "flooding":              {"agency": "PUB", "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "water"},
    "choked_drain":          {"agency": "PUB", "email": FROM_EMAIL, "sla": "4 hours",        "category": "water"},
    "manhole_overflow":      {"agency": "PUB", "email": FROM_EMAIL, "sla": "4 hours",        "category": "water"},
    "ceiling_leak":          {"agency": "PUB", "email": FROM_EMAIL, "sla": "24 hours",       "category": "water"},
    "stagnant_water":        {"agency": "PUB", "email": FROM_EMAIL, "sla": "24 hours",       "category": "water"},
    "pipe_leak":             {"agency": "PUB", "email": FROM_EMAIL, "sla": "4 hours",        "category": "water"},
    "burst_pipe":            {"agency": "PUB", "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "water"},
    "water_shortage":        {"agency": "PUB", "email": FROM_EMAIL, "sla": "4 hours",        "category": "water"},
    "dirty_water":           {"agency": "PUB", "email": FROM_EMAIL, "sla": "24 hours",       "category": "water"},
    "water_pollution":       {"agency": "PUB", "email": FROM_EMAIL, "sla": "24 hours",       "category": "water"},
    "drain_overflow":        {"agency": "PUB", "email": FROM_EMAIL, "sla": "4 hours",        "category": "water"},
    "blocked_drain":         {"agency": "PUB", "email": FROM_EMAIL, "sla": "4 hours",        "category": "water"},
    "roof_leak":             {"agency": "PUB", "email": FROM_EMAIL, "sla": "24 hours",       "category": "water"},
    "toilet_overflow":       {"agency": "PUB", "email": FROM_EMAIL, "sla": "4 hours",        "category": "water"},
    "sewage_leak":           {"agency": "PUB", "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "water"},
    "water_meter_fault":     {"agency": "PUB", "email": FROM_EMAIL, "sla": "2 working days", "category": "water"},
    "tap_leak":              {"agency": "PUB", "email": FROM_EMAIL, "sla": "24 hours",       "category": "water"},
    "water_pressure_issue":  {"agency": "PUB", "email": FROM_EMAIL, "sla": "24 hours",       "category": "water"},
    "wet_floor":             {"agency": "Town Council", "email": FROM_EMAIL, "sla": "24 hours", "category": "water"},

    # ── SAFETY / FIRE → SCDF ──────────────────────────────────────────────
    "blocked_exit":          {"agency": "SCDF",         "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "safety"},
    "fire_hazard":           {"agency": "SCDF",         "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "safety"},
    "fire_hose_reel":        {"agency": "Town Council", "email": FROM_EMAIL, "sla": "4 hours",        "category": "safety"},
    "fallen_tree":           {"agency": "NParks",       "email": FROM_EMAIL, "sla": "4 hours",        "category": "safety"},
    "graffiti":              {"agency": "Police",       "email": FROM_EMAIL, "sla": "3 working days", "category": "safety"},
    "emergency_exit_blocked":{"agency": "SCDF",         "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "safety"},
    "damaged_playground":    {"agency": "Town Council", "email": FROM_EMAIL, "sla": "2 working days", "category": "safety"},
    "broken_staircase":      {"agency": "Town Council", "email": FROM_EMAIL, "sla": "24 hours",       "category": "safety"},
    "lift_breakdown":        {"agency": "Town Council", "email": FROM_EMAIL, "sla": "4 hours",        "category": "safety"},
    "water_on_floor":        {"agency": "Town Council", "email": FROM_EMAIL, "sla": "24 hours",       "category": "safety"},
    "exposed_wires":         {"agency": "SP Group",     "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "safety"},
    "gas_leak":              {"agency": "SCDF",         "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "safety"},
    "collapsed_ceiling":     {"agency": "Town Council", "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "safety"},
    "broken_glass":          {"agency": "Town Council", "email": FROM_EMAIL, "sla": "24 hours",       "category": "safety"},
    "road_sinkhole":         {"agency": "LTA",          "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "safety"},
    "sparking_cables":       {"agency": "SP Group",     "email": FROM_EMAIL, "sla": "IMMEDIATE",      "category": "safety"},
    "unsafe_structure":      {"agency": "BCA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "safety"},

    # ── NOISE / NUISANCE → Police ─────────────────────────────────────────
    "renovation_noise":      {"agency": "Police", "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},
    "neighbour_noise":       {"agency": "Police", "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},
    "smoking_prohibited":    {"agency": "NEA",    "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "smoke_nuisance":        {"agency": "NEA",    "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "cooking_smell":         {"agency": "NEA",    "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},
    "loud_music":            {"agency": "Police", "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "party_noise":           {"agency": "Police", "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "drilling_noise":        {"agency": "Police", "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "construction_noise":    {"agency": "NEA",    "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},
    "traffic_noise":         {"agency": "LTA",    "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},
    "factory_noise":         {"agency": "NEA",    "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},
    "karaoke_noise":         {"agency": "Police", "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "shouting_noise":        {"agency": "Police", "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "vehicle_alarm":         {"agency": "Police", "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "horn_noise":            {"agency": "LTA",    "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},
    "generator_noise":       {"agency": "NEA",    "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},
    "burning_smell":         {"agency": "NEA",    "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "cigarette_smoke":       {"agency": "NEA",    "email": FROM_EMAIL, "sla": "24 hours",       "category": "noise"},
    "incense_smell":         {"agency": "NEA",    "email": FROM_EMAIL, "sla": "2 working days", "category": "noise"},

    # ── PEST / ANIMALS → NEA ──────────────────────────────────────────────
    "rat": {"agency": "NEA", "email": FROM_EMAIL, "sla": "2 working days", "category": "animal"},
    "pigeon": {"agency": "NEA", "email": FROM_EMAIL, "sla": "2 working days", "category": "animal"},
    "stray_cat": {"agency": "NEA", "email": FROM_EMAIL, "sla": "2 working days", "category": "animal"},
    "crow": {"agency": "NEA", "email": FROM_EMAIL, "sla": "2 working days", "category": "animal"},
    "stray_dog": {"agency": "AVS", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "dog": {"agency": "AVS", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "cat": {"agency": "AVS", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "snake": {"agency": "NParks", "email": FROM_EMAIL, "sla": "2 hours", "category": "animal"},
    "monitor_lizard": {"agency": "NParks", "email": FROM_EMAIL, "sla": "2 hours", "category": "animal"},
    "wild_boar": {"agency": "NParks", "email": FROM_EMAIL, "sla": "4 hours", "category": "animal"},
    "monkey": {"agency": "NParks", "email": FROM_EMAIL, "sla": "4 hours", "category": "animal"},
    "otter": {"agency": "NParks", "email": FROM_EMAIL, "sla": "4 hours", "category": "animal"},
    "squirrel": {"agency": "NParks", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "bat": {"agency": "NParks", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "owl": {"agency": "NParks", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "parrot": {"agency": "NParks", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "chicken": {"agency": "NEA", "email": FROM_EMAIL, "sla": "2 working days", "category": "animal"},
    "duck": {"agency": "NParks", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "frog": {"agency": "NParks", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "turtle": {"agency": "NParks", "email": FROM_EMAIL, "sla": "1 working day", "category": "animal"},
    "fish_dead": {"agency": "NParks", "email": FROM_EMAIL, "sla": "24 hours", "category": "animal"},
    "dead_bird": {"agency": "NEA", "email": FROM_EMAIL, "sla": "24 hours", "category": "animal"},
    "dead_cat": {"agency": "NEA", "email": FROM_EMAIL, "sla": "24 hours", "category": "animal"},
    "dead_dog": {"agency": "NEA", "email": FROM_EMAIL, "sla": "24 hours", "category": "animal"},

    # ── VEHICLES → LTA ────────────────────────────────────────────────────
    "illegal_parking":      {"agency": "LTA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "vehicles"},
    "abandoned_vehicle":    {"agency": "LTA",          "email": FROM_EMAIL, "sla": "3 working days", "category": "vehicles"},
    "footpath_obstruction": {"agency": "LTA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "vehicles"},
    "pmd":                  {"agency": "LTA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "vehicles"},
    "road_marking":         {"agency": "LTA",          "email": FROM_EMAIL, "sla": "3 working days", "category": "vehicles"},
    "carpark_gantry":       {"agency": "LTA",          "email": FROM_EMAIL, "sla": "24 hours",       "category": "vehicles"},

    # ── GREENERY → NParks ─────────────────────────────────────────────────
    "overgrown_grass":          {"agency": "NParks",   "email": FROM_EMAIL, "sla": "3 working days", "category": "greenery"},
    "fallen_uprooted_tree":     {"agency": "NParks",   "email": FROM_EMAIL, "sla": "4 hours",        "category": "greenery"},
    "dead_tree":                {"agency": "NParks",   "email": FROM_EMAIL, "sla": "3 working days", "category": "greenery"},
    "dry_leaves_accumulation":  {"agency": "NParks",   "email": FROM_EMAIL, "sla": "3 working days", "category": "greenery"},
    "illegal_plant":            {"agency": "NParks",   "email": FROM_EMAIL, "sla": "5 working days", "category": "greenery"},
}

# Priority levels and their trigger keywords
PRIORITY_KEYWORDS = {
    "CRITICAL": ["fire", "smoke", "explosion", "collapse", "scdf", "emergency", "call 995", "unconscious", "trapped", "gas leak"],
    "HIGH":     ["electrical spark", "flooding", "flood", "exposed wire", "broken wire", "bee nest", "hornet", "bee swarm",
                 "blocked exit", "fire escape", "water rising", "lift stuck", "overflowing manhole"],
    "MEDIUM":   ["broken pipe", "water leak", "ceiling leak", "fallen tree", "pest", "rat", "mosquito",
                 "overflowing bin", "illegal dump", "pothole", "broken drain"],
    "LOW":      ["litter", "grass", "overgrown", "graffiti", "noise", "sign", "bench", "cctv", "shelter"],
}

PRIORITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]