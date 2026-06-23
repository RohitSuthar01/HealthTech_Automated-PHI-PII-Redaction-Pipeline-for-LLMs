/**
 * api.js — Encapsulates backend HTTP fetch calls
 */

class API {
  static get BASE_URL() {
    return "http://localhost:5001/api";
  }

  static async redact(text) {
    const response = await fetch(`${this.BASE_URL}/redact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || "Backend redaction failed");
    }
    return response.json();
  }

  static async ask(sessionId, cleanText) {
    const response = await fetch(`${this.BASE_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        clean_text: cleanText
      })
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || "Backend AI call failed");
    }
    return response.json();
  }

  static async getSessions() {
    const response = await fetch(`${this.BASE_URL}/sessions`);
    if (!response.ok) {
      throw new Error("Failed to fetch backend sessions");
    }
    return response.json();
  }

  static async deleteSession(sessionId) {
    const response = await fetch(`${this.BASE_URL}/sessions/${sessionId}`, {
      method: "DELETE"
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || "Failed to delete session from database");
    }
    return response.json();
  }
}

window.API = API;
