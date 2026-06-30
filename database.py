"""
database.py — Tampines Estate Reporter
SQLite persistence layer (drop-in replacement for Google Sheets).

To upgrade to PostgreSQL later, set the DATABASE_URL environment variable:
  DATABASE_URL=postgresql://user:pass@host:5432/tampines

All public functions mirror the Sheets API exactly so the rest of the code
needs minimal changes.
"""

import os
import sqlite3
import contextlib
from datetime import datetime

# ── Connection config ──────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")          # set for Postgres
SQLITE_PATH  = os.getenv("SQLITE_PATH", "tampines.db")  # SQLite file path

_USE_POSTGRES = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")

# ── Schema ─────────────────────────────────────────────────────────────────
_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS cases (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id          TEXT UNIQUE NOT NULL,
    timestamp        TEXT NOT NULL,
    labels           TEXT,
    priority         TEXT,
    agencies         TEXT,
    slas             TEXT,
    location         TEXT,
    transcript       TEXT,
    case_summary     TEXT,
    email_sent       TEXT,
    sms_sent         TEXT,
    confidence       TEXT,
    needs_clarif     TEXT,
    resident_name    TEXT,
    resident_phone   TEXT,
    image_paths      TEXT,
    status           TEXT DEFAULT 'Open',
    assigned_officer  TEXT,
    capacity_verdict  TEXT,
    estimated_hrs     TEXT
);
"""

_CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_cases_phone ON cases(resident_phone);"

# ── NEW: Officer profiles table schema ─────────────────────────────────────
_CREATE_OFFICER_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS officer_profiles (
    officer_id TEXT PRIMARY KEY,
    officer_name TEXT NOT NULL,
    agency TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    profile_image TEXT,
    last_updated TEXT,
    UNIQUE(officer_id, agency)
)
"""

_CREATE_OFFICER_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS officer_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    officer_id TEXT,
    resident_email TEXT,
    resident_phone TEXT,
    message TEXT,
    image_attachment TEXT,
    timestamp TEXT
)
"""

_CREATE_CAROUSEL_IMAGES_TABLE = """
CREATE TABLE IF NOT EXISTS carousel_images (
    slide_key  TEXT PRIMARY KEY,
    image_data TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


# ── Connection helpers ──────────────────────────────────────────────────────
@contextlib.contextmanager
def _get_conn():
    """Yield a database connection (SQLite or Postgres)."""
    if _USE_POSTGRES:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def init_db():
    """Create tables if they don't exist. Call once at app startup."""
    sql_create = _CREATE_TABLE
    sql_index  = _CREATE_INDEX
    if _USE_POSTGRES:
        sql_create = sql_create.replace(
            "INTEGER PRIMARY KEY AUTOINCREMENT",
            "SERIAL PRIMARY KEY"
        )
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql_create)
        cur.execute(sql_index)
        # ── Migration: add image_paths column to existing databases ──
        try:
            cur.execute("ALTER TABLE cases ADD COLUMN image_paths TEXT")
        except Exception:
            pass  # column already exists — safe to ignore
        # ── Migration: add workforce columns ──
        for col in ["assigned_officer TEXT", "capacity_verdict TEXT", "estimated_hrs TEXT"]:
            try:
                cur.execute(f"ALTER TABLE cases ADD COLUMN {col}")
            except Exception:
                pass

        # ── NEW: Create officer_profiles table ─────────────────────────────────
        try:
            cur.execute(_CREATE_OFFICER_PROFILES_TABLE)
            print("[DB] Created/verified officer_profiles table")
        except Exception as e:
            print(f"[DB] Officer profiles table creation skipped: {e}")

        # ── NEW: Create officer_messages table ─────────────────────────────────
        try:
            cur.execute(_CREATE_OFFICER_MESSAGES_TABLE)
            print("[DB] Created/verified officer_messages table")
        except Exception as e:
            print(f"[DB] Officer messages table creation skipped: {e}")

        # ── NEW: Create carousel_images table ──────────────────────────────────
        try:
            cur.execute(_CREATE_CAROUSEL_IMAGES_TABLE)
            print("[DB] Created/verified carousel_images table")
        except Exception as e:
            print(f"[DB] Carousel images table creation skipped: {e}")

    print(f"[DB] Initialised ({'PostgreSQL' if _USE_POSTGRES else 'SQLite @ ' + SQLITE_PATH})")


# ── Write ───────────────────────────────────────────────────────────────────
def insert_case(
    case_id, analysis, routes, transcript, location,
    dispatch_results, resident_phone=None, resident_name=None,
    image_paths=None
):
    """Insert one case row. Returns True on success."""
    agencies_str   = " | ".join([r["agency"] for r in routes])
    slas_str       = " | ".join([r["sla"]    for r in routes])
    labels_str     = ", ".join(analysis.get("final_labels", []))
    image_paths_str = " | ".join(image_paths) if image_paths else ""
    placeholder    = "%s" if _USE_POSTGRES else "?"

    # Extract workforce capacity info for ALL routes, pipe-separated (mirrors agencies/slas)
    _officers, _verdicts, _hrs = [], [], []
    for r in routes:
        cap  = r.get("capacity", {}) or {}
        pos  = cap.get("assigned_position") or {}
        _officers.append(pos.get("title", ""))
        _verdicts.append(cap.get("capacity_verdict", ""))
        _hrs.append(str(cap.get("estimated_response_hrs", "")))
    assigned_officer = " | ".join(_officers)
    capacity_verdict = " | ".join(_verdicts)
    estimated_hrs    = " | ".join(_hrs)

    sql = f"""
        INSERT INTO cases
            (case_id, timestamp, labels, priority, agencies, slas, location,
             transcript, case_summary, email_sent, sms_sent, confidence,
             needs_clarif, resident_name, resident_phone, image_paths, status,
             assigned_officer, capacity_verdict, estimated_hrs)
        VALUES
            ({', '.join([placeholder]*20)})
        ON CONFLICT(case_id) DO NOTHING
    """
    if not _USE_POSTGRES:
        sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO").replace(
            "\n        ON CONFLICT(case_id) DO NOTHING", ""
        )

    row = (
        case_id,
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        labels_str,
        analysis.get("priority", ""),
        agencies_str,
        slas_str,
        location or "",
        transcript or "",
        analysis.get("case_summary", ""),
        "✅" if dispatch_results.get("emails_ok") else "❌",
        "✅" if dispatch_results.get("sms")       else "❌",
        str(analysis.get("confidence", "")),
        str(analysis.get("needs_clarification", False)),
        resident_name   or "",
        resident_phone  or "",
        image_paths_str,
        "Open",
        assigned_officer,
        capacity_verdict,
        estimated_hrs,
    )

    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, row)

            # ── Back-fill: if this submission has a real name, update all older
            #    rows for the same phone that have a blank/missing name.
            #    This makes the leaderboard name retroactively correct.
            if resident_name and resident_name.strip() and resident_phone:
                ph = "%s" if _USE_POSTGRES else "?"
                cur.execute(
                    f"UPDATE cases SET resident_name = {ph} "
                    f"WHERE resident_phone = {ph} "
                    f"AND (resident_name IS NULL OR resident_name = '')",
                    (resident_name.strip(), resident_phone),
                )
                updated = cur.rowcount
                if updated:
                    print(f"[DB] Back-filled name '{resident_name}' onto {updated} older row(s) for {resident_phone}")

        print(f"[DB] Inserted case {case_id}")
        return True
    except Exception as exc:
        print(f"[DB ERROR] insert_case: {exc}")
        return False


# ── Read ────────────────────────────────────────────────────────────────────
def get_all_cases():
    """Return all rows as a list of dicts, newest first."""
    sql = "SELECT * FROM cases ORDER BY id DESC"
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[DB ERROR] get_all_cases: {exc}")
        return []


def get_leaderboard_data():
    """
    Aggregate reporter scores and agency case counts.

    Name resolution strategy (per phone number):
      1. Use the most recent non-empty resident_name for that phone.
      2. If no name was ever provided → display "Reporter #XXXX"
         where XXXX = last 4 digits of the phone number.
         This gives every user a consistent, unique, non-embarrassing identity.

    Returns {"reporters": [...], "agencies": [...]}.
    """
    AGENCY_BASE = {
        "Tampines Town Council": {"avgHrs": 12, "rating": 92, "icon": "🏘️"},
    }

    rows = get_all_cases()   # newest → oldest (ORDER BY id DESC)

    reporters   = {}   # phone → stats dict
    agency_hits = {}   # agency_name → count

    # ── Pass 1: collect the LATEST non-empty name per phone ──────────────────
    # rows are newest-first, so the first non-empty name we see for a phone
    # is already the most recent one.
    latest_name = {}   # phone → best name string found so far
    for row in rows:
        phone = (row.get("resident_phone") or "").strip()
        name  = (row.get("resident_name")  or "").strip()
        if phone and name and phone not in latest_name:
            latest_name[phone] = name

    # ── Pass 2: aggregate scores ──────────────────────────────────────────────
    for row in rows:
        phone    = (row.get("resident_phone") or "").strip()
        priority = (row.get("priority")       or "LOW").strip().upper()
        location = (row.get("location")       or "").strip()
        agencies = (row.get("agencies")       or "").strip()
        email_ok = row.get("email_sent", "") == "✅"

        if not phone:
            continue

        # Resolve display name: latest known name, or "Reporter #XXXX"
        if phone in latest_name:
            display_name = latest_name[phone]
        else:
            suffix = phone[-4:] if len(phone) >= 4 else phone
            display_name = f"Reporter #{suffix}"

        has_location = bool(location)
        score = 10
        if priority in ("CRITICAL", "HIGH"):
            score += 5
        elif priority == "MEDIUM":
            score += 3
        if has_location:
            score += 1
        if email_ok:
            score += 2

        if phone not in reporters:
            reporters[phone] = {
                "name":     display_name,
                "phone":    phone,
                "total":    0,
                "score":    0,
                "critical": 0,
                "high":     0,
                "medium":   0,
                "low":      0,
            }
        else:
            # Always keep the most up-to-date resolved name
            reporters[phone]["name"] = display_name

        r = reporters[phone]
        r["total"] += 1
        r["score"] += score
        if   priority == "CRITICAL": r["critical"] += 1
        elif priority == "HIGH":     r["high"]     += 1
        elif priority == "MEDIUM":   r["medium"]   += 1
        else:                        r["low"]      += 1

        for ag in [a.strip() for a in agencies.split("|") if a.strip()]:
            agency_hits[ag] = agency_hits.get(ag, 0) + 1

    sorted_reporters = sorted(reporters.values(), key=lambda x: x["score"], reverse=True)

    agencies_list = [
        {
            "name":   name,
            "icon":   base["icon"],
            "cases":  agency_hits.get(name, 0),
            "avgHrs": base["avgHrs"],
            "rating": base["rating"],
        }
        for name, base in AGENCY_BASE.items()
    ]
    agencies_list.sort(key=lambda x: x["rating"], reverse=True)

    return {"reporters": sorted_reporters, "agencies": agencies_list}


def update_case_status(case_id: str, status: str):
    """Update a case's status (e.g. 'Open' → 'Resolved')."""
    placeholder = "%s" if _USE_POSTGRES else "?"
    sql = f"UPDATE cases SET status = {placeholder} WHERE case_id = {placeholder}"
    try:
        with _get_conn() as conn:
            conn.cursor().execute(sql, (status, case_id))
        return True
    except Exception as exc:
        print(f"[DB ERROR] update_case_status: {exc}")
        return False


# ── NEW: Officer profile functions ──────────────────────────────────────────
def save_officer_profile(officer_id: str, officer_name: str, agency: str, email: str = None, phone: str = None, profile_image: str = None):
    """Save or update officer profile information."""
    placeholder = "%s" if _USE_POSTGRES else "?"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _get_conn() as conn:
        cur = conn.cursor()

        # Check if exists
        cur.execute(
            f"SELECT officer_id FROM officer_profiles WHERE officer_id = {placeholder} AND agency = {placeholder}",
            (officer_id, agency)
        )
        existing = cur.fetchone()

        if existing:
            # Update existing
            if profile_image:
                cur.execute(
                    f"""UPDATE officer_profiles 
                        SET email = {placeholder}, phone = {placeholder}, profile_image = {placeholder}, last_updated = {placeholder}
                        WHERE officer_id = {placeholder} AND agency = {placeholder}""",
                    (email or "", phone or "", profile_image, current_time, officer_id, agency)
                )
            else:
                cur.execute(
                    f"""UPDATE officer_profiles 
                        SET email = {placeholder}, phone = {placeholder}, last_updated = {placeholder}
                        WHERE officer_id = {placeholder} AND agency = {placeholder}""",
                    (email or "", phone or "", current_time, officer_id, agency)
                )
        else:
            # Insert new
            cur.execute(
                f"""INSERT INTO officer_profiles 
                    (officer_id, officer_name, agency, email, phone, profile_image, last_updated)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})""",
                (officer_id, officer_name, agency, email or "", phone or "", profile_image, current_time)
            )
        return True


def get_officer_profile(officer_id: str, agency: str):
    """Retrieve officer profile by ID and agency."""
    placeholder = "%s" if _USE_POSTGRES else "?"
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            f"SELECT officer_id, officer_name, agency, email, phone, profile_image, last_updated FROM officer_profiles WHERE officer_id = {placeholder} AND agency = {placeholder}",
            (officer_id, agency)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def save_officer_message(officer_id: str, resident_email: str, resident_phone: str, message: str, image_attachment: str = None):
    """Store a message from resident to officer."""
    placeholder = "%s" if _USE_POSTGRES else "?"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""INSERT INTO officer_messages 
                (officer_id, resident_email, resident_phone, message, image_attachment, timestamp)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})""",
            (officer_id, resident_email, resident_phone, message, image_attachment, current_time)
        )
        return True

# ── Carousel image functions ────────────────────────────────────────────────
def save_carousel_image(slide_key: str, image_data: str):
    """Upsert a carousel image (base64 data URL) for a given slide key."""
    placeholder = "%s" if _USE_POSTGRES else "?"
    updated_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if _USE_POSTGRES:
        sql = f"""
            INSERT INTO carousel_images (slide_key, image_data, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder})
            ON CONFLICT (slide_key) DO UPDATE
              SET image_data = EXCLUDED.image_data, updated_at = EXCLUDED.updated_at
        """
    else:
        sql = f"""
            INSERT OR REPLACE INTO carousel_images (slide_key, image_data, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder})
        """
    try:
        with _get_conn() as conn:
            conn.cursor().execute(sql, (slide_key, image_data, updated_at))
        return True
    except Exception as exc:
        print(f"[DB ERROR] save_carousel_image: {exc}")
        return False


def delete_carousel_image(slide_key: str):
    """Remove a carousel image by slide key."""
    placeholder = "%s" if _USE_POSTGRES else "?"
    sql = f"DELETE FROM carousel_images WHERE slide_key = {placeholder}"
    try:
        with _get_conn() as conn:
            conn.cursor().execute(sql, (slide_key,))
        return True
    except Exception as exc:
        print(f"[DB ERROR] delete_carousel_image: {exc}")
        return False


def get_all_carousel_images():
    """Return all carousel images as a dict {slide_key: image_data}."""
    sql = "SELECT slide_key, image_data FROM carousel_images"
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        return {r[0]: r[1] for r in rows}
    except Exception as exc:
        print(f"[DB ERROR] get_all_carousel_images: {exc}")
        return {}