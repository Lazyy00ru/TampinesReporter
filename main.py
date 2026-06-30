import os

# ── Public base URL for email resolve links ──────────────────────────────────
os.environ.setdefault('APP_BASE_URL', 'https://thinner-overarch-overcook.ngrok-free.dev')

import uuid
import shutil
import threading
from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

from config import (
    PRIORITY_ORDER, AGENCY_ROUTING,
    DEMO_MODE, TEST_MODE,
    FROM_EMAIL, FROM_NAME, SENDGRID_API_KEY,
)
from agents import (
    generate_case_id, compute_priority,
    transcribe_audio, extract_issues_from_image,
    analyze_all_issues, resolve_routing, dispatch_agent,
    suggest_issue_label,  # ADDED: import the label suggestion function
)
from database import init_db, get_leaderboard_data, get_all_cases, update_case_status
from database import save_officer_profile, get_officer_profile, save_officer_message
from database import save_carousel_image, delete_carousel_image, get_all_carousel_images
from workforce import get_staff_availability, analyze_capacity

app = Flask(__name__)
init_db()
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─────────────────────────────────────────
# SERVE UPLOADED MEDIA FILES
# ─────────────────────────────────────────
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ─────────────────────────────────────────
# AGENCY CREDENTIALS
# ─────────────────────────────────────────
AGENCY_PASSWORDS = {
    "Tampines Town Council": "tampines2025",
}


# ─────────────────────────────────────────
# STATIC PAGE ROUTES — Resident
# ─────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/index.html')
def index_html():
    return render_template('index.html')


@app.route('/login.html')
def login():
    return render_template('login.html')


@app.route('/home.html')
def home():
    return render_template('home.html')


@app.route('/profile.html')
def profile():
    return render_template('profile.html')


@app.route('/confirm.html')
def confirm():
    return render_template('confirm.html')


@app.route('/chat.html')
def chat():
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def chat_api():
    from config import client

    body = request.get_json(force=True) or {}
    messages = body.get('messages', [])
    system = body.get('system', '')

    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'system', 'content': system}] + messages,
            max_tokens=1000,
            temperature=0.5
        )
        return jsonify({'content': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gemini-chat', methods=['POST'])
def gemini_chat():
    import traceback

    body = request.get_json(force=True) or {}
    messages = body.get('messages', [])
    system = body.get('system', '')
    gemini_err = None

    if GEMINI_API_KEY:
        try:
            from google import genai as google_genai
            from google.genai import types

            client = google_genai.Client(api_key=GEMINI_API_KEY)

            contents = []
            for msg in messages:
                role = 'user' if msg['role'] == 'user' else 'model'
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part(text=msg['content'])]
                ))

            config = types.GenerateContentConfig(
                system_instruction=system if system else None,
                temperature=0.4,
                max_output_tokens=2048,
            )

            response = client.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=contents,
                config=config,
            )
            print('[AI] Responded via Gemini')
            return jsonify({'content': response.text, 'provider': 'gemini'})

        except Exception as e:
            gemini_err = e
            print(f'[AI] Gemini failed ({e}) — falling back to Groq')

    try:
        from config import client as groq_client
        groq_messages = [{'role': 'system', 'content': system}] + messages
        response = groq_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=groq_messages,
            max_tokens=2048,
            temperature=0.4,
        )
        print('[AI] Responded via Groq fallback')
        return jsonify({'content': response.choices[0].message.content, 'provider': 'groq'})

    except Exception as groq_err:
        traceback.print_exc()
        gemini_msg = str(gemini_err) if gemini_err else 'no key'
        return jsonify({'error': f'Both providers failed. Gemini: {gemini_msg}. Groq: {str(groq_err)}'}), 500


@app.route('/history.html')
def history():
    return render_template('history.html')


@app.route('/leaderboard.html')
def leaderboard_page():
    return render_template('leaderboard.html')


@app.route('/static/sw.js')
def serve_sw():
    response = send_from_directory('static', 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


# ─────────────────────────────────────────
# STATIC PAGE ROUTES — Agency
# ─────────────────────────────────────────
@app.route('/agency_login.html')
def agency_login_page():
    return render_template('agency_login.html')


@app.route('/agency_dashboard.html')
def agency_dashboard_page():
    return render_template('agency_dashboard.html')


@app.route('/agency_home.html')
def agency_home_page():
    return render_template('agency_home.html')


@app.route('/agency_profile.html')
def agency_profile_page():
    return render_template('agency_profile.html')


@app.route('/agency_workforce.html')
def agency_workforce_page():
    return render_template('agency_workforce.html')


@app.route('/agency_analytics.html')
def agency_analytics_page():
    return render_template('agency_analytics.html')


# ─────────────────────────────────────────
# AGENCY AUTH ENDPOINT
# ─────────────────────────────────────────
@app.route('/agency/login', methods=['POST'])
def agency_login():
    body = request.get_json(force=True) or {}
    agency = body.get("agency", "").strip()
    password = body.get("password", "").strip()

    expected = AGENCY_PASSWORDS.get(agency)
    if not expected or password != expected:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"ok": True, "agency": agency})


# ─────────────────────────────────────────
# ANALYZE ENDPOINT
# ─────────────────────────────────────────
@app.route('/analyze', methods=['POST'])
@app.route('/analyze', methods=['POST'])
def analyze():
    result = {
        "transcript": None,
        "detected_language": None,       # e.g. "Myanmar", "Mandarin", "Malay", "Tamil"
        "english_translation": None,     # AI-translated English version of the voice report
        "image_result": None,
        "analysis": None,
        "routes": None,
        "location": None,
        "case_id": None,
        "dispatch": None,
        "needs_clarification": False,
        "clarification_question": "",
        "error": None
    }

    saved_image_paths = []

    try:
        audio_file = request.files.get('audio')
        extra_context = request.form.get('extra_context', '')
        location = request.form.get('location', '')
        lat = request.form.get('lat', '')
        lng = request.form.get('lng', '')
        resident_phone = request.form.get('phone', '')
        resident_name = request.form.get('name', '')

        if location:
            result["location"] = location
        elif lat and lng:
            result["location"] = f"{lat}, {lng}"

        # ── Step 1: Multi-Language Transcription ──
        if audio_file:
            ext = audio_file.filename.rsplit('.', 1)[-1] if '.' in audio_file.filename else 'webm'
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_audio.{ext}')
            audio_file.save(audio_path)

            result["transcript"] = transcribe_audio(audio_path)

            # Check if transcription failed
            if result["transcript"] and (
                    result["transcript"].startswith("Error") or result["transcript"].startswith("No speech")):
                print(f"[ANALYZE] Transcription issue: {result['transcript']}")
                # Don't fail completely, just note it
                result["transcript"] = ""

            if os.path.exists(audio_path):
                os.remove(audio_path)

        # ── Step 2: Multi-image extraction ──
        # Initialize image_result BEFORE any conditional blocks
        image_result = {"detected_labels": [], "description": "", "confidence": 50}
        raw_image_files = [request.files.get('image')]
        idx = 2
        while True:
            extra = request.files.get(f'image_{idx}')
            if extra is None:
                break
            raw_image_files.append(extra)
            idx += 1
        image_files = [f for f in raw_image_files if f is not None]

        if image_files:
            for idx_img, img_file in enumerate(image_files):
                img_ext = img_file.filename.rsplit('.', 1)[-1].lower() if '.' in img_file.filename else 'jpg'
                path = os.path.join(app.config['UPLOAD_FOLDER'], f'tmp_{uuid.uuid4().hex[:8]}.{img_ext}')
                img_file.save(path)
                saved_image_paths.append(path)
            image_result = extract_issues_from_image(saved_image_paths)
            result["image_result"] = image_result

        preview_only = request.form.get('preview_only', '') == 'true'

        # ── Step 3: Voice to Label Suggestion using Gemini ──
        # Initialize analysis with default values
        analysis = None

        if result["transcript"] and result["transcript"].strip():
            print(f"[ANALYZE] Processing voice transcript: {result['transcript']}")

            # Call the multi-language label suggestion agent
            label_suggestion = suggest_issue_label(result["transcript"])

            if label_suggestion and label_suggestion.suggested_label != "unknown":
                # Successfully mapped to a valid label
                final_labels = [label_suggestion.suggested_label]
                case_summary = label_suggestion.english_translation
                detected_language = label_suggestion.detected_language
                confidence = label_suggestion.confidence_score

                print(f"[ANALYZE] ✓ Language: {detected_language}")
                print(f"[ANALYZE] ✓ Translation: {case_summary}")
                print(f"[ANALYZE] ✓ Label: {final_labels[0]} (confidence: {confidence})")

                # Surface language + translation to the frontend
                result["detected_language"] = detected_language
                result["english_translation"] = case_summary

                # Build analysis with the suggested label
                analysis = {
                    "final_labels": final_labels,
                    "case_summary": case_summary,
                    "resident_message": result["transcript"],
                    "priority": "MEDIUM",
                    "needs_clarification": confidence < 0.6,
                    "clarification_question": f"Are you reporting an issue with {final_labels[0].replace('_', ' ')}?" if confidence < 0.6 else "",
                    "confidence": int(confidence * 100)
                }

            elif label_suggestion and label_suggestion.suggested_label == "unknown":
                # Voice was processed but didn't match any known label
                print(
                    f"[ANALYZE] Voice didn't match any known label. Translation: {label_suggestion.english_translation}")

                # Still surface the language + translation so UI can show it
                result["detected_language"] = label_suggestion.detected_language
                result["english_translation"] = label_suggestion.english_translation

                # Still try to use image labels if available
                final_labels = image_result.get("detected_labels", [])
                case_summary = label_suggestion.english_translation or image_result.get("description",
                                                                                        "Municipal issue report.")

                analysis = {
                    "final_labels": final_labels,
                    "case_summary": case_summary,
                    "resident_message": result["transcript"],
                    "priority": "MEDIUM",
                    "needs_clarification": not final_labels,
                    "clarification_question": f"Could you please confirm the issue? Based on your report: {case_summary[:100]}" if not final_labels else "",
                    "confidence": 50
                }
            else:
                # Voice analysis completely failed
                print(f"[ANALYZE] Voice label suggestion failed. Falling back to image detection.")
                final_labels = image_result.get("detected_labels", [])
                case_summary = image_result.get("description", "Municipal issue report.")

                analysis = {
                    "final_labels": final_labels,
                    "case_summary": case_summary,
                    "resident_message": result["transcript"] or "Voice recording provided but could not be processed.",
                    "priority": "MEDIUM",
                    "needs_clarification": not final_labels,
                    "clarification_question": "Could you please describe the issue in more detail?" if not final_labels else "",
                    "confidence": image_result.get("confidence", 50)
                }

        elif image_result.get("detected_labels"):
            # No voice, but we have images
            final_labels = image_result.get("detected_labels", [])
            case_summary = image_result.get("description", "Municipal issue report.")

            analysis = {
                "final_labels": final_labels,
                "case_summary": case_summary,
                "resident_message": "Report submitted via photo.",
                "priority": "MEDIUM",
                "needs_clarification": False,
                "clarification_question": "",
                "confidence": image_result.get("confidence", 50)
            }
        else:
            # No voice and no images with detectable issues
            analysis = {
                "final_labels": [],
                "case_summary": "Unable to determine issue from provided media.",
                "resident_message": result["transcript"] or "No description provided.",
                "priority": "LOW",
                "needs_clarification": True,
                "clarification_question": "Please describe the issue or upload clearer photos.",
                "confidence": 0
            }

        # Store analysis in result
        result["analysis"] = analysis

        # Priority calculation override
        if result["analysis"] and result["analysis"].get("final_labels"):
            computed_priority = compute_priority(
                result["analysis"].get("final_labels", []),
                result["analysis"].get("case_summary", "") + result["analysis"].get("resident_message", "")
            )
            if PRIORITY_ORDER.index(computed_priority) < PRIORITY_ORDER.index(
                    result["analysis"].get("priority", "LOW")):
                result["analysis"]["priority"] = computed_priority

        if preview_only:
            return jsonify(result)

        # Resolve agency routes
        if result["analysis"] and result["analysis"].get("final_labels"):
            routes = resolve_routing(result["analysis"].get("final_labels", []),
                                     priority=result["analysis"].get("priority", "MEDIUM"))
            if not routes:
                routes = [{
                    "agency": "Tampines Town Council",
                    "email": FROM_EMAIL,
                    "sla": "3 working days",
                    "category": "general",
                    "labels_covered": result["analysis"].get("final_labels", [])
                }]
            result["routes"] = routes

        # ── Step 4: Generate unique Case Identifier ──
        if preview_only:
            return jsonify(result)

        case_id = generate_case_id()
        result["case_id"] = case_id

        # Stable cross-device filename mapping
        renamed_image_paths = []
        for i, old_path in enumerate(saved_image_paths):
            f_ext = old_path.rsplit('.', 1)[-1].lower() if '.' in old_path else 'jpg'
            new_name = f'{case_id}_img{i + 1}.{f_ext}'
            new_path = os.path.join(app.config['UPLOAD_FOLDER'], new_name)
            try:
                shutil.copy2(old_path, new_path)
                os.remove(old_path)
                renamed_image_paths.append(new_name)
            except Exception:
                renamed_image_paths.append(os.path.basename(old_path))
        saved_image_paths = renamed_image_paths

        # ── Step 5: Background Thread Agent Dispatching ──
        if result["analysis"] and result.get("routes"):
            dispatch_sink = {}
            dispatch_thread = threading.Thread(
                target=dispatch_agent,
                args=(
                    case_id,
                    result["analysis"],
                    result["routes"],
                    result["transcript"] or "",
                    result["location"] or "",
                    resident_phone or None,
                    saved_image_paths if saved_image_paths else None,
                    resident_name or None,
                ),
                kwargs={"result_sink": dispatch_sink},
                daemon=True
            )
            dispatch_thread.start()
            dispatch_thread.join(timeout=25)

            result["dispatch"] = {
                "status": "dispatched",
                "agencies": [r["agency"] for r in result["routes"]],
            }

    except Exception as e:
        result["error"] = str(e)
        import traceback
        traceback.print_exc()
        for p in saved_image_paths:
            if os.path.exists(p):
                os.remove(p)

    return jsonify(result)
# ─────────────────────────────────────────
# LEADERBOARD ENDPOINT
# ─────────────────────────────────────────
def _load_leaderboard_from_db():
    try:
        data = get_leaderboard_data()
        if not data["reporters"] and not any(a["cases"] for a in data["agencies"]):
            return None
        return data
    except Exception as e:
        print(f"[LEADERBOARD ERROR] {e}")
        return None


@app.route('/leaderboard')
def leaderboard():
    data = _load_leaderboard_from_db()
    if data is None:
        return jsonify({"reporters": [], "agencies": _default_agencies(), "source": "empty"})
    data["source"] = "db"
    return jsonify(data)


def _default_agencies():
    return [
        {"name": "Tampines Town Council", "icon": "🏘️", "cases": 0, "avgHrs": 12, "rating": 92},
    ]


# ─────────────────────────────────────────
# CASES ENDPOINTS
# ─────────────────────────────────────────
@app.route('/cases')
def list_cases():
    rows = get_all_cases()
    return jsonify({"total": len(rows), "cases": rows})


@app.route('/cases/<case_id>/status', methods=['PATCH'])
def patch_case_status(case_id):
    body = request.get_json(force=True) or {}
    status = body.get("status", "").strip()
    if not status:
        return jsonify({"error": "status field required"}), 400
    ok = update_case_status(case_id, status)
    if ok:
        return jsonify({"case_id": case_id, "status": status})
    return jsonify({"error": "update failed"}), 500


@app.route('/cases/agency/<path:agency_name>')
def cases_for_agency(agency_name):
    rows = get_all_cases()
    parts = [p.strip().lower() for p in agency_name.split('/')]
    filtered = [
        r for r in rows
        if any(p in (r.get('agencies') or '').lower() for p in parts)
    ]
    return jsonify({"total": len(filtered), "agency": agency_name, "cases": filtered})


# ─────────────────────────────────────────
# DEBUG ENDPOINT
# ─────────────────────────────────────────
@app.route('/debug/images')
def debug_images():
    upload_dir = app.config['UPLOAD_FOLDER']
    try:
        files = sorted(os.listdir(upload_dir))
    except Exception as e:
        files = [f"ERROR: {e}"]
    rows = get_all_cases()[:10]
    cases_info = [{"case_id": r["case_id"], "image_paths": r.get("image_paths", "")} for r in rows]
    return jsonify({
        "upload_folder": upload_dir,
        "folder_exists": os.path.isdir(upload_dir),
        "files_in_uploads": files,
        "recent_cases_image_paths": cases_info,
    })


# ─────────────────────────────────────────
# CAROUSEL IMAGES ENDPOINTS
# ─────────────────────────────────────────
@app.route('/carousel-images', methods=['GET'])
def get_carousel_images():
    return jsonify(get_all_carousel_images())


@app.route('/carousel-images', methods=['POST'])
def save_carousel_images():
    body = request.get_json(force=True) or {}
    images = body.get('images', {})
    if not images:
        return jsonify({'error': 'No images provided'}), 400
    saved = []
    failed = []
    for key, data in images.items():
        ok = save_carousel_image(key, data)
        (saved if ok else failed).append(key)
    return jsonify({'saved': saved, 'failed': failed})


@app.route('/carousel-images/<string:slide_key>', methods=['DELETE'])
def remove_carousel_image(slide_key):
    ok = delete_carousel_image(slide_key)
    if ok:
        return jsonify({'deleted': slide_key})
    return jsonify({'error': 'Delete failed'}), 500


# ─────────────────────────────────────────
# AI SUMMARY ENDPOINT
# ─────────────────────────────────────────
@app.route('/ai_summary')
def ai_summary():
    rows = get_all_cases()

    agency_name = request.args.get('agency', '').strip()
    if agency_name:
        parts = [p.strip().lower() for p in agency_name.split('/')]
        rows = [r for r in rows if any(p in (r.get('agencies') or '').lower() for p in parts)]

    HUMAN_PRIOS = {'CRITICAL', 'HIGH'}
    human_cases = [c for c in rows if
                   (c.get('priority') or '').upper() in HUMAN_PRIOS and (c.get('status') or 'Open') != 'Resolved']
    ai_cases = [c for c in rows if (c.get('priority') or '').upper() not in HUMAN_PRIOS]

    from collections import Counter
    cat_counter = Counter()
    for c in rows:
        for lbl in (c.get('labels') or '').split(','):
            lbl = lbl.strip()
            if lbl:
                cat_counter[lbl] += 1
    categories = [{'label': k, 'count': v} for k, v in cat_counter.most_common(10)]

    return jsonify({
        'total': len(rows),
        'human_cases': human_cases,
        'ai_cases': ai_cases,
        'categories': categories,
        'counts': {
            'open': len([c for c in rows if (c.get('status') or 'Open') != 'Resolved']),
            'critical': len([c for c in rows if (c.get('priority') or '').upper() == 'CRITICAL']),
            'high': len([c for c in rows if (c.get('priority') or '').upper() == 'HIGH']),
            'ai_assigned': len([c for c in rows if (c.get('priority') or '').upper() not in HUMAN_PRIOS and (
                    c.get('status') or 'Open') != 'Resolved']),
            'resolved': len([c for c in rows if (c.get('status') or 'Open') == 'Resolved']),
        }
    })


# ─────────────────────────────────────────
# WORKFORCE ENDPOINT
# ─────────────────────────────────────────
@app.route('/workforce')
def workforce_overview():
    from workforce import AGENCY_ROSTER
    agency_filter = request.args.get('agency', '').strip()
    agencies = list(AGENCY_ROSTER.keys())
    if agency_filter:
        agencies = [a for a in agencies if agency_filter.lower() in a.lower()]

    result = {}
    for name in agencies:
        result[name] = get_staff_availability(name)

    return jsonify({"agencies": result, "total_agencies": len(result)})


@app.route('/workforce/capacity')
def workforce_capacity():
    agency = request.args.get('agency', 'Tampines Town Council')
    category = request.args.get('category', 'cleanliness')
    priority = request.args.get('priority', 'MEDIUM')
    sla = request.args.get('sla', '24 hours')

    cap = analyze_capacity(agency, category, priority, sla)
    return jsonify(cap)


# ─────────────────────────────────────────
# ANALYTICS ENDPOINT
# ─────────────────────────────────────────
@app.route('/analytics')
def analytics():
    from collections import Counter, defaultdict
    from datetime import datetime, timedelta

    rows = get_all_cases()

    period_days = int(request.args.get('days', 30))
    cutoff = datetime.now() - timedelta(days=period_days)
    filtered = []
    for r in rows:
        try:
            ts = datetime.strptime(r.get('timestamp', ''), '%d/%m/%Y %H:%M:%S')
            if ts >= cutoff:
                filtered.append((ts, r))
        except Exception:
            filtered.append((datetime.now(), r))
    period_rows = [r for _, r in filtered]

    total = len(period_rows)
    resolved = sum(1 for r in period_rows if (r.get('status') or '') == 'Resolved')
    open_ = total - resolved

    agency_counter = Counter()
    for r in period_rows:
        for ag in (r.get('agencies') or '').split('|'):
            ag = ag.strip()
            if ag:
                agency_counter[ag] += 1

    from config import AGENCY_ROUTING
    label_to_cat = {k: v['category'] for k, v in AGENCY_ROUTING.items()}
    cat_counter = Counter()
    for r in period_rows:
        for lbl in (r.get('labels') or '').split(','):
            lbl = lbl.strip()
            cat = label_to_cat.get(lbl, lbl)
            if cat:
                cat_counter[cat] += 1

    prio_counter = Counter()
    for r in period_rows:
        p = (r.get('priority') or 'LOW').upper()
        prio_counter[p] += 1

    num_buckets = min(8, max(1, period_days // 7)) if period_days >= 7 else period_days
    bucket_days = max(1, period_days // num_buckets)
    trend = []
    now = datetime.now()
    for i in range(num_buckets):
        bucket_end = now - timedelta(days=i * bucket_days)
        bucket_start = bucket_end - timedelta(days=bucket_days)
        label = f"W{num_buckets - i}" if period_days >= 7 else f"D{num_buckets - i}"
        b = {'label': label, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for ts, r in filtered:
            if bucket_start <= ts < bucket_end:
                p = (r.get('priority') or 'LOW').upper()
                if p == 'CRITICAL':
                    b['critical'] += 1
                elif p == 'HIGH':
                    b['high'] += 1
                elif p == 'MEDIUM':
                    b['medium'] += 1
                else:
                    b['low'] += 1
        trend.append(b)
    trend.reverse()

    heatmap = [[0] * 7 for _ in range(8)]
    HOUR_BUCKETS = [6, 9, 12, 15, 18, 21, 0, 3]
    for ts, _ in filtered:
        dow = ts.weekday()
        h = ts.hour
        bucket = 7
        for bi, bh in enumerate(HOUR_BUCKETS):
            if bh <= h < (HOUR_BUCKETS[bi + 1] if bi < 7 else 24):
                bucket = bi
                break
        heatmap[bucket][dow] += 1

    return jsonify({
        'total': total,
        'resolved': resolved,
        'open': open_,
        'critical': prio_counter.get('CRITICAL', 0),
        'agency': dict(agency_counter),
        'category': dict(cat_counter),
        'priority': {
            'CRITICAL': prio_counter.get('CRITICAL', 0),
            'HIGH': prio_counter.get('HIGH', 0),
            'MEDIUM': prio_counter.get('MEDIUM', 0),
            'LOW': prio_counter.get('LOW', 0),
        },
        'trend': trend,
        'heatmap': heatmap,
        'period_days': period_days,
    })


# ─────────────────────────────────────────
# DEBUG: LIST AVAILABLE GEMINI MODELS
# ─────────────────────────────────────────
@app.route('/debug/gemini-models')
def list_gemini_models():
    try:
        from google import genai as google_genai
        client = google_genai.Client(api_key=GEMINI_API_KEY)
        models = client.models.list()
        names = [m.name for m in models]
        return jsonify({'models': names})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# OFFICER RESOLVE ENDPOINT
# ─────────────────────────────────────────
@app.route('/cases/<case_id>/resolve', methods=['GET'])
def resolve_case_via_email(case_id):
    ok = update_case_status(case_id, 'Resolved')
    status_line = "✅ Case resolved successfully." if ok else "⚠️ Could not update case status (may already be resolved)."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Case Resolved · Tampines Estate Reporter</title>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
      font-family: 'Inter', Arial, sans-serif;
      background: #F4F7FD;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}
    .card {{
      background: #ffffff;
      border-radius: 20px;
      border: 1px solid #E2E8F0;
      max-width: 480px;
      width: 100%;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,0.07);
    }}
    .card-header {{
      background: #1A3A6B;
      padding: 20px 24px;
    }}
    .card-header-title {{
      font-size: 16px;
      font-weight: 800;
      color: #fff;
      letter-spacing: -0.01em;
    }}
    .card-header-sub {{
      font-size: 12px;
      color: #93C5FD;
      margin-top: 4px;
    }}
    .card-body {{
      padding: 32px 28px;
      text-align: center;
    }}
    .big-icon {{
      font-size: 64px;
      margin-bottom: 16px;
      display: block;
    }}
    .card-title {{
      font-size: 22px;
      font-weight: 800;
      color: #0E1C34;
      margin-bottom: 10px;
      letter-spacing: -0.02em;
    }}
    .case-pill {{
      display: inline-block;
      background: #EFF6FF;
      color: #1E40AF;
      font-size: 13px;
      font-weight: 700;
      padding: 6px 16px;
      border-radius: 20px;
      margin-bottom: 18px;
      border: 1px solid #BFDBFE;
    }}
    .card-msg {{
      font-size: 14px;
      color: #4B5563;
      line-height: 1.65;
      margin-bottom: 24px;
    }}
    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #F0FDF4;
      color: #16A34A;
      font-size: 13px;
      font-weight: 700;
      padding: 10px 20px;
      border-radius: 12px;
      border: 1px solid #BBF7D0;
    }}
    .card-footer {{
      background: #F8FAFE;
      padding: 14px 24px;
      font-size: 11px;
      color: #8C9BB0;
      text-align: center;
      border-top: 1px solid #EEF2F8;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="card-header">
      <div class="card-header-title">🏘️ Tampines Estate Reporter</div>
      <div class="card-header-sub">Case Resolution Portal</div>
    </div>
    <div class="card-body">
      <span class="big-icon">✅</span>
      <div class="card-title">Case Marked as Resolved</div>
      <div class="case-pill">📋 {case_id}</div>
      <p class="card-msg">
        Thank you for resolving this case. The resident and agency dashboard
        have been notified automatically. No further action is required.
      </p>
      <div class="status-badge">
        <span>●</span>
        <span>Status: Resolved</span>
      </div>
    </div>
    <div class="card-footer">
      Tampines Estate Reporter · Automated Dispatch System · {status_line}
    </div>
  </div>
</body>
</html>"""

    return html, 200, {'Content-Type': 'text/html'}


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "demo_mode": DEMO_MODE,
        "test_mode": TEST_MODE,
        "issue_types_loaded": len(AGENCY_ROUTING),
        "services": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "sqlite": True,
        }
    })


@app.route('/config')
def get_config():
    return jsonify({
        'groq_api_key': os.getenv('GROQ_API_KEY', '')
    })


# ── OFFICER CONTACT AND PROFILE ENDPOINTS ──────────────────────────────────
@app.route('/officer/contact', methods=['POST'])
def officer_contact():
    try:
        officer_name = request.form.get('officer_name', '')
        officer_id = request.form.get('officer_id', '')
        agency = request.form.get('agency', '')
        resident_email = request.form.get('email', '')
        resident_phone = request.form.get('phone', '')
        message = request.form.get('message', '')

        image_file = request.files.get('image')
        profile_image = None

        if image_file and image_file.filename:
            ext = image_file.filename.rsplit('.', 1)[-1].lower() if '.' in image_file.filename else 'jpg'
            filename = f"officer_{officer_id}_profile.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            if os.path.exists(filepath):
                os.remove(filepath)

            image_file.save(filepath)
            profile_image = filename
            print(f"[PROFILE] Saved profile picture for {officer_name}: {filepath}")

        save_officer_profile(officer_id, officer_name, agency, resident_email, resident_phone, profile_image)
        print(f"[DATABASE] Saved/updated profile for {officer_name}")

        if message:
            save_officer_message(officer_id, resident_email, resident_phone, message, profile_image)
            print(f"[MESSAGE] Saved message from {resident_email} to {officer_name}")

        return jsonify({
            "success": True,
            "message": f"Profile updated for {officer_name}",
            "profile_image": profile_image,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[CONTACT ERROR] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/officer/profile/<officer_id>/<agency>', methods=['GET'])
def get_officer_profile_endpoint(officer_id, agency):
    try:
        profile = get_officer_profile(officer_id, agency)
        if profile:
            return jsonify(profile)
        else:
            return jsonify({"exists": False})
    except Exception as e:
        print(f"[PROFILE ERROR] {e}")
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# DISPATCH EMAIL TO OFFICER ON CONFIRMATION
# ─────────────────────────────────────────

_OFFICER_NAME_TO_ID = {
    "Officer Lim Wei Jie": ("NEA-01", "NEA"),
    "Officer Priya Nair": ("NEA-02", "NEA"),
    "Officer Ahmad Fauzi": ("TC-01", "Town Council"),
    "Officer Rachel Teo": ("TC-02", "Town Council"),
    "Officer Tan Boon Kiat": ("PUB-01", "PUB"),
    "Officer Suresh Kumar": ("PUB-02", "PUB"),
    "Officer Jason Ng": ("SCDF-01", "SCDF"),
    "Officer Hafiz Roslan": ("SCDF-02", "SCDF"),
    "Officer Chua Mei Ling": ("SPF-01", "Police"),
    "Officer David Raj": ("SPF-02", "Police"),
    "Officer Wong Kah Hoe": ("LTA-01", "LTA"),
    "Officer Nur Aisyah": ("LTA-02", "LTA"),
    "Officer Eugene Loh": ("NP-01", "NParks"),
    "Officer Siti Rahayu": ("NP-02", "NParks"),
}


def _send_officer_email_via_sendgrid(to_email: str, officer_name: str, case: dict, resolution_plan: str = '',
                                     base_url: str = ''):
    try:
        import urllib.request, urllib.error, json as _json
        case_id = case.get("case_id", "—")
        priority = (case.get("priority") or "—").upper()
        location = case.get("location") or "Not specified"
        summary = case.get("case_summary") or case.get("transcript") or "No description"
        agency = (case.get("agencies") or "").split("|")[0].strip() or "—"
        sla = (case.get("slas") or "").split("|")[0].strip() or "—"
        timestamp = case.get("timestamp") or datetime.now().strftime("%d/%m/%Y %H:%M")

        prio_color = {
            "CRITICAL": "#DC2626", "HIGH": "#EA580C",
            "MEDIUM": "#D97706", "LOW": "#16A34A",
        }.get(priority, "#344B6C")

        html_body = f"""
<div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #E2E8F0;">
  <div style="background:#1A3A6B;padding:20px 24px;">
    <div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.01em;">🏘️ Tampines Estate Reporter</div>
    <div style="font-size:12px;color:#93C5FD;margin-top:4px;">Case Assignment Notification</div>
  </div>
  <div style="padding:24px;">
    <div style="font-size:15px;font-weight:700;color:#0E1C34;margin-bottom:4px;">Dear {officer_name},</div>
    <div style="font-size:13px;color:#344B6C;margin-bottom:20px;line-height:1.6;">
      A new case has been assigned to you. Please review the details below.
    </div>

    <div style="background:#F8FAFE;border:1px solid #E2E8F0;border-radius:12px;padding:16px 18px;margin-bottom:16px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <span style="font-size:11px;font-weight:800;background:{prio_color};color:#fff;padding:3px 10px;border-radius:20px;text-transform:uppercase;">{priority}</span>
        <span style="font-size:12px;font-weight:700;color:#C47900;">{case_id}</span>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:12px;">
        <tr><td style="padding:5px 0;color:#6C7A91;font-weight:600;width:110px;">📍 Location</td><td style="color:#0E1C34;font-weight:600;">{location}</td></tr>
        <tr><td style="padding:5px 0;color:#6C7A91;font-weight:600;">🏢 Agency</td><td style="color:#0E1C34;font-weight:600;">{agency}</td></tr>
        <tr><td style="padding:5px 0;color:#6C7A91;font-weight:600;">⏱ SLA</td><td style="color:#0E1C34;font-weight:600;">{sla}</td></tr>
        <tr><td style="padding:5px 0;color:#6C7A91;font-weight:600;">🕐 Reported</td><td style="color:#0E1C34;font-weight:600;">{timestamp}</td></tr>
        <tr><td style="padding:5px 0;color:#6C7A91;font-weight:600;vertical-align:top;">📋 Summary</td><td style="color:#0E1C34;font-weight:600;line-height:1.5;">{summary}</td></tr>
      </table>
    </div>

    <div style="font-size:12px;color:#6C7A91;line-height:1.6;margin-top:8px;">
      Please review the case details and click the button below once the issue has been resolved on-site.
    </div>
  </div>

  <div style="padding:0 24px 20px;">
    <a href="__RESOLVE_URL__"
       style="display:block;text-align:center;background:#16A34A;color:#ffffff;
              font-size:14px;font-weight:800;padding:14px 24px;border-radius:12px;
              text-decoration:none;letter-spacing:-0.01em;">
      ✅ Mark Case as Resolved
    </a>
    <div style="font-size:11px;color:#9CA3AF;text-align:center;margin-top:8px;line-height:1.5;">
      Clicking this button will mark the case <strong>{case_id}</strong> as Resolved
    </div>
  </div>

  <div style="background:#F4F7FD;padding:14px 24px;font-size:11px;color:#8C9BB0;text-align:center;border-top:1px solid #EEF2F8;">
    Tampines Estate Reporter · Automated Dispatch System · Do not reply to this email
  </div>
</div>"""

        resolve_url = f"{base_url}/cases/{case_id}/resolve" if base_url else f"/cases/{case_id}/resolve"
        html_body = html_body.replace('__RESOLVE_URL__', resolve_url)

        payload = _json.dumps({
            "personalizations": [{"to": [{"email": to_email, "name": officer_name}]}],
            "from": {"email": FROM_EMAIL, "name": FROM_NAME},
            "subject": f"[{priority}] Case Assignment: {case_id} — {location}",
            "content": [{"type": "text/html", "value": html_body}],
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[EMAIL] SendGrid response: {resp.status}")
            return (resp.status in (200, 202), '')
    except Exception as exc:
        print(f"[EMAIL] SendGrid error: {exc}")
        return (False, str(exc))


@app.route('/cases/<case_id>/notify-resident', methods=['POST'])
def notify_resident(case_id):
    import urllib.request as _urllib_req
    import urllib.parse as _urllib_parse
    import json as _json

    try:
        all_cases = get_all_cases()
        case = next((c for c in all_cases if c.get('case_id') == case_id), None)
        if not case:
            return jsonify({'success': False, 'error': 'Case not found'}), 404

        resident_phone = (case.get('resident_phone') or '').strip()
        if not resident_phone:
            return jsonify({'success': False, 'error': 'No resident phone on file'}), 400

        req_json = request.get_json(silent=True) or {}
        event = req_json.get('event', 'open')
        agency = req_json.get('agency', case.get('agencies', 'Town Council'))
        officer = req_json.get('officer', case.get('assigned_officer', 'the officer'))
        location = req_json.get('location', case.get('location', ''))
        priority = (case.get('priority') or 'LOW').upper()

        if event == 'processing':
            body_text = (
                f"✅ *Tampines Estate Reporter*\n\n"
                f"Your case *{case_id}* has been assigned and is now being processed.\n\n"
                f"📍 Location: {location or 'Not specified'}\n"
                f"🏢 Agency: {agency}\n"
                f"👷 Officer: {officer}\n"
                f"⚡ Priority: {priority}\n\n"
                f"You'll be notified again once it's resolved."
            )
        else:
            body_text = (
                f"🔔 *Tampines Estate Reporter*\n\n"
                f"Your case *{case_id}* is now open and under review.\n\n"
                f"📍 Location: {location or 'Not specified'}\n"
                f"🏢 Agency: {agency}\n"
                f"⚡ Priority: {priority}\n\n"
                f"An officer will be assigned shortly."
            )

        if DEMO_MODE:
            print(f"[DEMO] Would WhatsApp {resident_phone}: {body_text[:80]}...")
            return jsonify({'success': True, 'demo': True, 'phone': resident_phone})

        from config import TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM_PHONE
        if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_FROM_PHONE:
            return jsonify({'success': False, 'error': 'Twilio not configured'}), 503

        to_phone = resident_phone if resident_phone.startswith('+') else '+' + resident_phone

        for from_addr in [f'whatsapp:{TWILIO_FROM_PHONE}', TWILIO_FROM_PHONE]:
            to_addr = f'whatsapp:{to_phone}' if 'whatsapp' in from_addr else to_phone
            payload = _urllib_parse.urlencode({
                'To': to_addr,
                'From': from_addr,
                'Body': body_text,
            }).encode('utf-8')
            url = f'https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json'
            req = _urllib_req.Request(url, data=payload, method='POST')
            import base64 as _b64
            creds = _b64.b64encode(f'{TWILIO_SID}:{TWILIO_TOKEN}'.encode()).decode()
            req.add_header('Authorization', f'Basic {creds}')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            try:
                with _urllib_req.urlopen(req, timeout=10) as resp:
                    resp_body = _json.loads(resp.read().decode())
                    sid = resp_body.get('sid', '')
                    print(f"[NOTIFY-RESIDENT] Sent to {to_addr} — SID {sid}")
                    return jsonify({'success': True, 'phone': to_phone, 'sid': sid})
            except Exception as tw_err:
                print(f"[NOTIFY-RESIDENT] {from_addr} failed: {tw_err}")
                continue

        return jsonify({'success': False, 'error': 'Both WhatsApp and SMS delivery failed'}), 502

    except Exception as e:
        print(f'[NOTIFY-RESIDENT ERROR] {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# Add this test endpoint to main.py to test audio transcription separately:

@app.route('/test-transcribe', methods=['POST'])
def test_transcribe():
    """Test endpoint to debug audio transcription."""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    ext = audio_file.filename.rsplit('.', 1)[-1] if '.' in audio_file.filename else 'webm'
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f'test_audio.{ext}')
    audio_file.save(audio_path)

    try:
        from agents import transcribe_audio
        transcription = transcribe_audio(audio_path)
        return jsonify({
            'success': True,
            'transcription': transcription,
            'audio_path': audio_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'audio_path': audio_path
        }), 500
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


@app.route('/cases/<case_id>/dispatch-email', methods=['POST'])
def dispatch_email_to_officer(case_id):
    try:
        all_cases = get_all_cases()
        case = next((c for c in all_cases if c.get('case_id') == case_id), None)
        if not case:
            return jsonify({'success': False, 'error': 'Case not found'}), 404

        raw_officers = (case.get('assigned_officer') or '').strip()
        if not raw_officers:
            return jsonify({'success': False, 'error': 'No officer assigned to this case'}), 400

        officer_names = [n.strip() for n in raw_officers.replace(',', '|').split('|') if n.strip()]
        print(f'[DISPATCH EMAIL] case={case_id} officers={officer_names}')

        req_json = request.get_json(silent=True) or {}
        resolution_plan = req_json.get('resolution_plan', '')

        _env_base = os.environ.get('APP_BASE_URL', '').rstrip('/')
        _fwd_host = request.headers.get('X-Forwarded-Host', '').strip()
        if _env_base:
            base_url = _env_base
        elif _fwd_host:
            proto = request.headers.get('X-Forwarded-Proto', 'https')
            base_url = f"{proto}://{_fwd_host}"
        else:
            raw = request.host_url.rstrip('/')
            if '127.0.0.1' in raw or 'localhost' in raw:
                import socket as _sock
                try:
                    lan_ip = _sock.gethostbyname(_sock.gethostname())
                    port_part = ':' + raw.split(':')[-1] if ':' in raw.split('//')[-1] else ''
                    base_url = f"http://{lan_ip}{port_part}"
                except Exception:
                    base_url = raw
            else:
                base_url = raw

        results = []
        sent_count = 0
        no_email = []

        for officer_name in officer_names:
            lookup = _OFFICER_NAME_TO_ID.get(officer_name)
            officer_email = None
            if lookup:
                officer_id, agency = lookup
                profile = get_officer_profile(officer_id, agency)
                if profile and profile.get('email'):
                    officer_email = profile['email']

            if not officer_email:
                if DEMO_MODE:
                    # In demo mode, fall back to FROM_EMAIL so dispatch still succeeds
                    officer_email = FROM_EMAIL
                    print(f'[DISPATCH EMAIL] No profile email for {officer_name} — using demo fallback: {officer_email}')
                else:
                    print(f'[DISPATCH EMAIL] No profile email for {officer_name} — skipping')
                    no_email.append(officer_name)
                    continue

            if DEMO_MODE:
                print(f'[DEMO] Would email {officer_name} <{officer_email}> for case {case_id}')
                sent_count += 1
                results.append({'officer': officer_name, 'email': officer_email, 'demo': True})
                continue

            ok, err_msg = _send_officer_email_via_sendgrid(officer_email, officer_name, case, resolution_plan, base_url)
            if ok:
                sent_count += 1
                results.append({'officer': officer_name, 'email': officer_email})
            else:
                results.append({'officer': officer_name, 'error': err_msg})

        if sent_count > 0:
            update_case_status(case_id, 'Processing')
            print(f'[STATUS] {case_id} → Processing ({sent_count} email(s) sent)')
            first = results[0]
            return jsonify({
                'success': True,
                'emails_sent': sent_count,
                'results': results,
                'email_sent_to': first.get('email', ''),
                'officer': first.get('officer', ''),
                'demo': DEMO_MODE,
            })
        else:
            missing = ', '.join(no_email) or 'all officers'
            return jsonify({'success': False,
                            'error': f'No email configured for: {missing}. Set emails in Workforce profiles.'}), 400

    except Exception as e:
        print(f'[DISPATCH EMAIL ERROR] {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port, host='0.0.0.0')