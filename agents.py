# agents.py (Gemini 2.5 Flash + Groq only — no OpenAI/GPT)

import os
import base64
import json
import uuid
import threading
from datetime import datetime
from PIL import Image
import io

from config import (
    client, AGENCY_ROUTING, PRIORITY_KEYWORDS, PRIORITY_ORDER,
    FROM_EMAIL, FROM_NAME,
    DEMO_MODE,
)
from database import insert_case
from workforce import analyze_capacity_for_routes

ISSUE_LABEL_LIST = ", ".join(AGENCY_ROUTING.keys())

# ─────────────────────────────────────────
# GEMINI CLIENT SETUP (NEW SDK)
# ─────────────────────────────────────────
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    gemini_model_name = "gemini-2.5-flash"
else:
    gemini_client = None

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# ─────────────────────────────────────────────────────────
# STEP 1: DEFINE THE PYDANTIC RESPONSE SCHEMA
# ─────────────────────────────────────────────────────────
class IssueSuggestion(BaseModel):
    detected_language: str = Field(
        description="The language spoken by the user (e.g., 'English', 'Myanmar', 'Mandarin', 'Malay', 'Tamil')."
    )
    english_translation: str = Field(
        description="Translate the user's message to clear English. If already English, copy it verbatim."
    )
    suggested_label: str = Field(
        description="The exact matched label from the allowed labels list. If no match fits, use 'unknown'."
    )
    confidence_score: float = Field(
        description="Confidence value between 0.0 (low) and 1.0 (high) for the label suggestion."
    )


class EstimatedResponses(BaseModel):
    Tampines_Town_Council: str = Field(alias="Tampines Town Council")
    NEA: str
    PUB: str
    SCDF: str
    Police: str
    LTA: str
    NParks: str


class AnalysisSchema(BaseModel):
    final_labels: List[str]
    priority: str
    confidence: int
    needs_clarification: bool
    clarification_question: str
    agencies_notified: List[str]
    resident_message: str
    case_summary: str
    estimated_responses: EstimatedResponses


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def generate_case_id():
    suffix = uuid.uuid4().hex[:4].upper()
    year = datetime.now().year
    return f"TMP-{year}-{suffix}"


def compress_image(image_path, max_size_kb=1000):
    img = Image.open(image_path)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    max_dim = 1024
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buffer = io.BytesIO()
    quality = 85
    while quality > 20:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        if buffer.tell() <= max_size_kb * 1024:
            break
        quality -= 10
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def compute_priority(detected_labels: list, description: str) -> str:
    """Return the highest matching priority level."""
    text = (description + " " + " ".join(detected_labels)).lower()
    for level in PRIORITY_ORDER:
        for kw in PRIORITY_KEYWORDS[level]:
            if kw in text:
                return level
    return "LOW"


# ─────────────────────────────────────────────────────────
# STEP 2: MULTI-LANGUAGE TEXT TO LABEL SUGGESTION AGENT
# ─────────────────────────────────────────────────────────
def suggest_issue_label(user_text):
    """
    Analyzes raw multi-language text using Gemini 2.5 Flash Structured Outputs.
    Translates context to English behind the scenes and returns a strict, validated label suggestion
    using labels from config.py.
    """
    if not gemini_client:
        print("[Analysis] Gemini client not initialized!")
        return None

    from config import AGENCY_ROUTING
    ALLOWED_LABELS = list(AGENCY_ROUTING.keys())
    labels_description = "\n".join([f"  - {label}" for label in ALLOWED_LABELS])

    prompt = f"""
    You are an advanced classification backend engine for a municipal estate reporting application.
    Your task is to analyze the following user text input (which may be in any language), 
    understand what municipal issue they are complaining about, and match it to one of our 
    valid backend classification system labels.

    USER REPORT:
    "{user_text}"

    VALID BACKEND LABELS SYSTEM (choose ONLY from this list):
    {labels_description}

    CRITICAL RULES:
    1. FIRST, understand the user's complaint regardless of language. Then translate the meaning to English.
    2. Map the issue to the MOST APPROPRIATE label from the list above.
    3. Examples of mapping:
       - Mosquito breeding, puddles, standing water, flooded area, water pooling → "stagnant_water"
       - Trash, rubbish, garbage, littering, dumping, waste → "litter"
       - High grass, weeds, overgrown vegetation, wild plants → "overgrown_grass"
       - Broken pipe, water leak, burst pipe, plumbing issue → "broken_pipe"
       - Clogged drain, blocked drain, water not flowing, drainage problem → "choked_drain"
       - Rats, mice, rodent infestation, pest problem → "pests"
       - Broken light, streetlight not working, lamp post issue → "broken_lamp"
       - Broken bench, damaged seating, bench repair → "broken_bench"
       - Flooding, flood, water rising, submerged area → "flooding"
       - Fire, smoke, burning smell, fire hazard → "fire_hazard"
       - Fallen tree, tree down, uprooted tree, tree branch → "fallen_tree"
       - Illegal parking, car parked wrongly, obstructing vehicle → "illegal_parking"
       - Noise complaint, loud music, renovation noise, construction sound → "renovation_noise"

    4. The 'suggested_label' value MUST be chosen strictly from the VALID BACKEND LABELS list above.
    5. If the issue completely doesn't match any category, set 'suggested_label' to "unknown".
    6. The 'english_translation' should be a clear English description of what the user said.
    7. The 'detected_language' should identify the original language (e.g., 'English', 'Myanmar', 'Mandarin', 'Malay', 'Tamil', 'Vietnamese', 'Thai', etc.)
    """

    try:
        print("[Analysis] Parsing text for labels via Gemini...")

        response = gemini_client.models.generate_content(
            model=gemini_model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IssueSuggestion,
                temperature=0.1,
            ),
        )

        structured_result = response.parsed
        print(f"[Analysis] Success! Detected Language: {structured_result.detected_language}")
        print(f"[Analysis] English Translation: {structured_result.english_translation[:100]}...")
        print(f"[Analysis] Suggested Label Token: {structured_result.suggested_label}")
        print(f"[Analysis] Confidence Score: {structured_result.confidence_score}")
        return structured_result

    except Exception as e:
        print(f"[Analysis] Gemini text classification failed: {e}. Falling back to Groq...")
        return None


# ─────────────────────────────────────────
# COMPONENT 1: NATIVE MULTI-LANGUAGE VOICE → TEXT
# ─────────────────────────────────────────
def transcribe_audio(audio_path):
    """
    Transcribes audio using Gemini 2.5 Flash by passing raw audio bytes inline.
    Preserves the native spoken language and script accurately.
    Falls back to Groq Whisper if Gemini is unavailable.
    """
    if not gemini_client:
        print("[Audio] Gemini client not initialized. Falling back to Groq Whisper...")
        return _transcribe_audio_groq(audio_path)

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    mime_type = "audio/webm"
    if audio_path.endswith(".mp3"):
        mime_type = "audio/mp3"
    elif audio_path.endswith(".wav"):
        mime_type = "audio/wav"
    elif audio_path.endswith(".m4a"):
        mime_type = "audio/m4a"

    print(f"[Audio] Reading audio file inline: {audio_path}")
    print(f"[Audio] MIME type: {mime_type}, bytes size: {len(audio_bytes)}")

    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

    prompt = (
        "You are an expert audio transcriber for a municipal reporting application. "
        "Listen to this audio clip carefully and transcribe EXACTLY what the user said. "
        "DO NOT translate their words into English. "
        "If the speaker talks in Myanmar language, output native Myanmar script. "
        "If they speak in Mandarin, output Chinese characters. "
        "If they speak in Malay, Tamil, or English, write out their exact spoken text in that language. "
        "Capture their original spoken language accurately. "
        "Return ONLY the raw text transcription. Do not include introductory text, explanations, or metadata."
    )

    try:
        print("[Audio] Calling Gemini for transcription...")

        response = gemini_client.models.generate_content(
            model=gemini_model_name,
            contents=[audio_part, prompt]
        )

        transcription = ""
        if response and hasattr(response, 'text'):
            transcription = response.text.strip() if response.text else ""
        elif response and hasattr(response, 'candidates') and response.candidates:
            transcription = response.candidates[0].content.parts[0].text.strip()

        if not transcription:
            print("[Audio] Gemini returned empty transcription. Falling back to Groq...")
            return _transcribe_audio_groq(audio_path)

        print(f"[Audio] Gemini transcription: {transcription}")
        return transcription

    except Exception as e:
        print(f"[Audio] Gemini transcription failed: {e}. Falling back to Groq Whisper...")
        return _transcribe_audio_groq(audio_path)


def _transcribe_audio_groq(audio_path):
    """
    Fallback transcription using Groq's Whisper endpoint.
    Uses whisper-large-v3-turbo for fast, multilingual transcription.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("[Audio] GROQ_API_KEY not set. Cannot transcribe.")
        return "Error processing voice clip. Please try again or type your report."

    try:
        import groq as groq_sdk
        groq_client = groq_sdk.Groq(api_key=groq_api_key)

        print(f"[Audio] Calling Groq Whisper for transcription: {audio_path}")

        with open(audio_path, "rb") as f:
            response = groq_client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=f,
                response_format="verbose_json",
            )

        detected_lang = getattr(response, "language", "unknown")
        print(f"[Audio] Groq Whisper detected language: {detected_lang}")

        transcription = (response.text or "").strip()
        if not transcription:
            return "No speech detected in audio recording."

        print(f"[Audio] Groq Whisper transcription: {transcription}")
        return transcription

    except Exception as e:
        print(f"[Audio] Groq Whisper transcription failed: {e}")
        return "Error processing voice clip. Please try again or type your report."


# ─────────────────────────────────────────
# COMPONENT 2: MULTI-ISSUE EXTRACTOR (Gemini Vision → Groq fallback)
# ─────────────────────────────────────────
def extract_issues_from_image(image_paths):
    """Return a JSON object with all detected issue labels from one or more images.
       Uses Gemini first, falls back to Groq Llama Vision."""
    if isinstance(image_paths, str):
        image_paths = [image_paths]

    prompt = f"""You are an AI assistant for Singapore HDB estate issue reporting.

Analyze ALL provided images and detect every estate issue present across all of them.

Return ONLY valid JSON — no markdown, no explanation — in this exact format:
{{
  "detected_labels": ["label1", "label2"],
  "description": "One sentence describing all issues seen across all images",
  "confidence": 85
}}

Valid labels (pick only from this list): {ISSUE_LABEL_LIST}

Rules:
- List every issue you can see across ALL images, not just one
- confidence is 0-100
- If nothing estate-related is visible in any image, return detected_labels as []"""

    # Try Gemini first (new SDK)
    if gemini_client:
        try:
            image_parts = []
            for path in image_paths:
                img = Image.open(path)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                image_parts.append(img)

            response = gemini_client.models.generate_content(
                model=gemini_model_name,
                contents=[prompt, *image_parts]
            )
            raw = response.text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            try:
                result = json.loads(raw)
                print("[Vision] Using Gemini (new SDK)")
                return result
            except Exception:
                return {"detected_labels": [], "description": raw, "confidence": 40}
        except Exception as e:
            print(f"[Vision] Gemini failed: {e}. Falling back to Groq...")

    # Fallback to Groq Llama Vision
    content = []
    for path in image_paths:
        image_data = compress_image(path)
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})
    content.append({"type": "text", "text": prompt})

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": content}],
        max_tokens=300
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"detected_labels": [], "description": raw, "confidence": 40}


# ─────────────────────────────────────────
# COMPONENT 3: MULTI-ISSUE ANALYSIS (Gemini 2.5 Flash → Groq Fallback)
# ─────────────────────────────────────────
def analyze_all_issues(transcript: str, image_result: dict, location: str, extra_context: str = ""):
    """
    Merge voice + image signals, confirm/extend labels, determine priority,
    check if clarification is needed, and compose the smart user response.
    Uses Gemini first with Pydantic Structured Outputs, falls back to Groq.
    """
    labels_from_image = image_result.get("detected_labels", [])
    img_description = image_result.get("description", "")
    img_confidence = image_result.get("confidence", 50)

    prompt_system = f"""You are an intelligent multi-issue estate routing AI for Tampines HDB, Singapore.
All issues are handled by Tampines Town Council unless another agency is explicit.

Your job:
1. Merge information from the resident's voice report and image analysis
2. Identify ALL distinct issues present — a single photo can have multiple problems
3. For each issue, pick the best matching label from the approved list
4. Determine overall priority: CRITICAL / HIGH / MEDIUM / LOW
5. If confidence < 60, set needs_clarification=true and write a follow-up question
6. Compose a smart, friendly resident_message (max 3 sentences) that:
   - Confirms Tampines Town Council has been notified
   - Lists "What to do NOW" safety steps if HIGH or CRITICAL
   - Gives SLA expectations
   - Is warm and empathetic
7. Write a concise case_summary (max 2 sentences) for officers

Valid labels: {ISSUE_LABEL_LIST}

Priority guide:
- CRITICAL: fire, explosion, gas leak, structural collapse, trapped persons → tell resident to call 995
- HIGH: exposed live wire, active flooding, bee swarm, blocked fire exit, lift entrapment
- MEDIUM: broken pipe, fallen tree, pest, overflowing bin, pothole, ceiling leak
- LOW: litter, noise, overgrown grass, graffiti, minor damage"""

    prompt_user = f"""Voice transcript: "{transcript or 'No voice report'}"

Image analysis: {img_description}
Image detected labels: {labels_from_image}
Image confidence: {img_confidence}%

Location: {location or 'Not provided'}
Additional context: {extra_context or 'None'}"""

    full_prompt = prompt_system + "\n\n" + prompt_user

    if gemini_client:
        try:
            response = gemini_client.models.generate_content(
                model=gemini_model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.25,
                    max_output_tokens=2000,
                    response_mime_type="application/json",
                    response_schema=AnalysisSchema,
                )
            )

            validated_data = AnalysisSchema.model_validate_json(response.text)
            result = validated_data.model_dump(by_alias=True)
            print("[Analysis] Using Gemini (Structured Pydantic JSON)")
            return result

        except Exception as e:
            print(f"[Analysis] Gemini structured output failed: {e}. Falling back to Groq...")

    # Fallback to Groq Llama 70B
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": prompt_system + "\n\nRespond ONLY in valid JSON — no markdown."},
            {"role": "user", "content": prompt_user}
        ],
        max_tokens=700,
        temperature=0.25
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {
            "final_labels": labels_from_image or ["illegal_dump"],
            "priority": "MEDIUM",
            "confidence": 50,
            "needs_clarification": False,
            "clarification_question": "",
            "agencies_notified": ["Tampines Town Council"],
            "resident_message": "Your report has been received. We will look into it shortly.",
            "case_summary": raw,
            "estimated_responses": {
                "Tampines Town Council": "Pending",
                "NEA": "Pending",
                "PUB": "Pending",
                "SCDF": "Pending",
                "Police": "Pending",
                "LTA": "Pending",
                "NParks": "Pending"
            }
        }


# ─────────────────────────────────────────
# COMPONENT 4: RESOLVE ROUTING FOR LABELS
# ─────────────────────────────────────────

_OFFICER_ROSTER = {
    "NEA": [{"id": "NEA-01", "name": "Officer Lim Wei Jie"}, {"id": "NEA-02", "name": "Officer Priya Nair"}],
    "Town Council": [{"id": "TC-01", "name": "Officer Ahmad Fauzi"}, {"id": "TC-02", "name": "Officer Rachel Teo"}],
    "PUB": [{"id": "PUB-01", "name": "Officer Tan Boon Kiat"}, {"id": "PUB-02", "name": "Officer Suresh Kumar"}],
    "SCDF": [{"id": "SCDF-01", "name": "Officer Jason Ng"}, {"id": "SCDF-02", "name": "Officer Hafiz Roslan"}],
    "Police": [{"id": "SPF-01", "name": "Officer Chua Mei Ling"}, {"id": "SPF-02", "name": "Officer David Raj"}],
    "LTA": [{"id": "LTA-01", "name": "Officer Wong Kah Hoe"}, {"id": "LTA-02", "name": "Officer Nur Aisyah"}],
    "NParks": [{"id": "NP-01", "name": "Officer Eugene Loh"}, {"id": "NP-02", "name": "Officer Siti Rahayu"}],
}

_RESPONSE_HRS_BY_PRIORITY = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 4,
    "LOW": 8,
}

_CAPACITY_THRESHOLDS = {
    "available": 0,
    "busy": 1,
    "at_capacity": 3,
}


def _load_officer_workload(agency: str) -> dict:
    from database import get_all_cases
    officers = _OFFICER_ROSTER.get(agency, [])
    workload = {o["name"]: 0 for o in officers}
    try:
        all_cases = get_all_cases()
        for case in all_cases:
            if (case.get("status") or "Open") == "Resolved":
                continue
            name = (case.get("assigned_officer") or "").strip()
            if name in workload:
                workload[name] += 1
    except Exception as exc:
        print(f"[ROUTING] Could not load officer workload: {exc}")
    return workload


def _pick_officer(agency: str) -> dict:
    officers = _OFFICER_ROSTER.get(agency, [])
    if not officers:
        return {"id": "DUTY", "name": "Duty Officer"}
    if len(officers) == 1:
        return officers[0]

    workload = _load_officer_workload(agency)
    return min(officers, key=lambda o: workload.get(o["name"], 0))


def _capacity_verdict(officer_name: str, agency: str, priority: str) -> dict:
    workload = _load_officer_workload(agency)
    load = workload.get(officer_name, 0)
    base_hrs = _RESPONSE_HRS_BY_PRIORITY.get(priority, 4)

    if load >= _CAPACITY_THRESHOLDS["at_capacity"]:
        verdict = "At Capacity"
        est_hrs = base_hrs * 3
    elif load >= _CAPACITY_THRESHOLDS["busy"]:
        verdict = "Busy"
        est_hrs = base_hrs * 2
    else:
        verdict = "On Call" if priority == "CRITICAL" else "Urgent" if priority == "HIGH" else "Available"
        est_hrs = base_hrs

    return {"capacity_verdict": verdict, "estimated_response_hrs": est_hrs}


def resolve_routing(final_labels: list, priority: str = "MEDIUM") -> list:
    seen_agencies = {}
    for label in final_labels:
        route = AGENCY_ROUTING.get(label)
        if not route:
            continue
        agency = route["agency"]
        if agency not in seen_agencies:
            seen_agencies[agency] = {
                "agency": agency,
                "email": route["email"],
                "sla": route["sla"],
                "category": route["category"],
                "labels_covered": [],
                "priority": priority,
            }
        seen_agencies[agency]["labels_covered"].append(label)

    routes = list(seen_agencies.values())
    routes = analyze_capacity_for_routes(routes)

    for route in routes:
        cap = route.get("capacity") or {}
        agency = route["agency"]
        assigned = (cap.get("assigned_position") or {}).get("title", "").strip()
        if not assigned:
            officer = _pick_officer(agency)
            cap_info = _capacity_verdict(officer["name"], agency, priority)
            route["capacity"] = {
                **cap,
                "assigned_position": {
                    "title": officer["name"],
                    "id": officer["id"],
                },
                **cap_info,
            }
            print(
                f"[ROUTING] {agency} → {officer['name']} | {route['capacity']['capacity_verdict']} | ~{route['capacity']['estimated_response_hrs']}h")

    return routes


# ─────────────────────────────────────────
# COMPONENT 5: DB LOGGER
# ─────────────────────────────────────────
def log_to_db(case_id, analysis, routes, transcript, location,
              dispatch_results, resident_phone=None, resident_name=None,
              image_paths=None):
    if DEMO_MODE:
        print(f"[DEMO] Would log {case_id} to DB")
        return True
    return insert_case(
        case_id, analysis, routes, transcript, location,
        dispatch_results, resident_phone, resident_name,
        image_paths=image_paths
    )


# ─────────────────────────────────────────
# COMPONENT 6: DISPATCH AGENT
# ─────────────────────────────────────────
def dispatch_agent(case_id, analysis, routes, transcript, location,
                   resident_phone=None, image_paths=None, resident_name=None,
                   result_sink=None):
    print(f"\n{'=' * 55}")
    print(f"[AGENT] Dispatching {case_id}")
    print(f"[AGENT] Labels: {analysis.get('final_labels')} | Priority: {analysis.get('priority')}")
    print(f"[AGENT] Agencies: {[r['agency'] for r in routes]}")
    print(f"{'=' * 55}\n")

    results = {"emails_ok": False, "sms": False, "db": False}

    results["db"] = log_to_db(
        case_id, analysis, routes, transcript, location,
        results, resident_phone, resident_name,
        image_paths=image_paths
    )

    print(f"\n[AGENT] Dispatch complete for {case_id}: {results}\n")

    if result_sink is not None:
        result_sink.update(results)

    return results