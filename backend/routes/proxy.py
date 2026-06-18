"""
routes/proxy.py
---------------
API endpoints:

POST /api/redact
    Input : { "text": "<clinical note>" }
    Output: { "session_id", "clean_text", "token_map", "entities_found" }

POST /api/ask
    Input : { "session_id": "...", "clean_text": "..." }
    Output: { "ai_response_raw", "ai_response_restored" }
    (sends clean_text to Claude/GPT, restores identities in response)

POST /api/restore
    Input : { "session_id": "...", "text": "<AI response with pseudonyms>" }
    Output: { "restored_text" }

GET  /api/sessions
    Output: { "sessions": [ session_id, ... ] }

DELETE /api/sessions/<session_id>
    Output: { "deleted": true }
"""

import os
import requests
from flask import Blueprint, request, jsonify
from redaction_engine import redact, restore, new_session_id
from vault import vault

proxy_bp = Blueprint("proxy", __name__)


# ─────────────────────────────────────────────
# POST /api/redact
# ─────────────────────────────────────────────
@proxy_bp.route("/redact", methods=["POST"])
def redact_note():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    clean_text, token_map, entities = redact(text)
    session_id = new_session_id()

    # Store token map in Vault
    vault.store(session_id, token_map)

    return jsonify({
        "session_id":     session_id,
        "clean_text":     clean_text,
        "token_map":      token_map,
        "entities_found": len(token_map),
        "entities":       [
            {"original": e["original"], "category": e["category"]}
            for e in entities
        ]
    }), 200


# ─────────────────────────────────────────────
# POST /api/ask  — send clean text to external AI
# ─────────────────────────────────────────────
@proxy_bp.route("/ask", methods=["POST"])
def ask_ai():
    data       = request.get_json(force=True)
    session_id = data.get("session_id", "")
    clean_text = data.get("clean_text", "").strip()

    if not clean_text or not session_id:
        return jsonify({"error": "session_id and clean_text are required"}), 400

    token_map = vault.get(session_id)
    if not token_map:
        return jsonify({"error": "Session not found or expired"}), 404

    # ── Call external AI ──────────────────────────────────────────────
    api_key  = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"

    ai_response_raw = _call_ai(clean_text, api_key, provider)

    # ── Restore identities in AI response ────────────────────────────
    ai_response_restored = restore(ai_response_raw, token_map)

    return jsonify({
        "session_id":           session_id,
        "ai_response_raw":      ai_response_raw,       # has pseudonyms only
        "ai_response_restored": ai_response_restored   # real patient names back
    }), 200


def _call_ai(clean_text, api_key, provider):
    """Send pseudonymised text to external AI and return its response."""

    if not api_key:
        # Fallback demo response when no API key is set
        return (
            "Based on the clinical note provided, the patient presents with "
            "symptoms consistent with a mild lower respiratory tract infection. "
            "Recommend completing the antibiotic course and scheduling a follow-up "
            "in 5 days to review imaging results."
        )

    if provider == "anthropic":
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-6",
                "max_tokens": 512,
                "messages": [
                    {
                        "role":    "user",
                        "content": (
                            "You are a clinical decision support assistant. "
                            "Summarise the following de-identified clinical note "
                            "and suggest next steps. Use the placeholder names "
                            "exactly as given — do NOT invent real names.\n\n"
                            + clean_text
                        )
                    }
                ]
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    else:  # openai
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a clinical decision support assistant. Use placeholder names exactly as given."},
                    {"role": "user",   "content": clean_text}
                ]
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────
# POST /api/restore  — manually restore a text
# ─────────────────────────────────────────────
@proxy_bp.route("/restore", methods=["POST"])
def restore_text():
    data       = request.get_json(force=True)
    session_id = data.get("session_id", "")
    text       = data.get("text", "")

    token_map = vault.get(session_id)
    if not token_map:
        return jsonify({"error": "Session not found or expired"}), 404

    return jsonify({"restored_text": restore(text, token_map)}), 200


# ─────────────────────────────────────────────
# GET /api/sessions
# ─────────────────────────────────────────────
@proxy_bp.route("/sessions", methods=["GET"])
def list_sessions():
    return jsonify({"sessions": vault.all_sessions()}), 200


# ─────────────────────────────────────────────
# DELETE /api/sessions/<session_id>
# ─────────────────────────────────────────────
@proxy_bp.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    vault.delete(session_id)
    return jsonify({"deleted": True, "session_id": session_id}), 200
