/**
 * app.js — Updated with direct Anthropic API call
 * No backend needed — API called directly from browser
 */

// ── CONFIG ────────────────────────────────────────────────────────
const USE_BACKEND    = false;
const BACKEND_URL    = "http://localhost:5000/api";
const ANTHROPIC_KEY  = window.ANTHROPIC_KEY; // paste your key here
/*const ANTHROPIC_KEY  = "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"; // paste your key here
*/
// ─────────────────────────────────────────────────────────────────

// ── Navigation ───────────────────────────────────────────────────
document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".nav-item").forEach((i) => i.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    item.classList.add("active");
    document.getElementById(`view-${item.dataset.view}`).classList.add("active");
  });
});

// ── State ────────────────────────────────────────────────────────
const sessions    = [];
const auditEvents = [];
let   currentSession = null;

const CATEGORY_LABELS = {
  NAME: "Name", DATE: "Date", PHONE: "Phone",
  EMAIL: "Email", MRN: "MRN", SSN: "SSN",
  AADHAAR: "Aadhaar", ADDRESS: "Address",
};

// ── Elements ─────────────────────────────────────────────────────
const inputNote      = document.getElementById("input-note");
const outputRedacted = document.getElementById("output-redacted");
const outputFinal    = document.getElementById("output-final");
const tokenMapEl     = document.getElementById("token-map");
const btnRedact      = document.getElementById("btn-redact");
const btnSendAI      = document.getElementById("btn-send-ai");
const btnClear       = document.getElementById("btn-clear");

// ── Run Redaction ─────────────────────────────────────────────────
btnRedact.addEventListener("click", () => {
  const text = inputNote.value.trim();
  if (!text) return;

  const { cleanText, tokenMap } = redact(text);
  const entitiesFound = Object.keys(tokenMap).length;

  if (entitiesFound === 0) {
    outputRedacted.className   = "output-box placeholder";
    outputRedacted.textContent = "No PHI detected in this note.";
    return;
  }

  outputRedacted.className  = "output-box";
  outputRedacted.innerHTML  = highlightPseudonyms(cleanText, tokenMap);

  resetFinalOutput();
  renderTokenMap(tokenMap);

  currentSession = {
    id: newSessionId(), tokenMap, cleanText, createdAt: new Date()
  };

  sessions.unshift(currentSession);
  renderVaultTable();
  updateMetrics();
  logEvent("ti-scan", `Redacted — ${entitiesFound} entities detected. Session: ${currentSession.id}`);

  btnSendAI.disabled = false;
});

// ── Clear ─────────────────────────────────────────────────────────
btnClear.addEventListener("click", () => {
  inputNote.value            = "";
  outputRedacted.className   = "output-box placeholder";
  outputRedacted.textContent = "Run redaction to see the de-identified version of this note.";
  resetFinalOutput();
  tokenMapEl.className       = "token-map placeholder";
  tokenMapEl.textContent     = "No active session. Token mappings will appear here after redaction.";
  btnSendAI.disabled         = true;
  currentSession             = null;
});

function resetFinalOutput() {
  outputFinal.className   = "output-box placeholder";
  outputFinal.textContent = "The AI's response, with patient identity restored, will appear here.";
}

// ── Send to AI ────────────────────────────────────────────────────
btnSendAI.addEventListener("click", async () => {
  if (!currentSession) return;

  btnSendAI.disabled  = true;
  btnSendAI.innerHTML = '<i class="ti ti-loader-2"></i> Waiting for AI...';
  logEvent("ti-cloud-upload", `Sent pseudonymized text to AI (session ${currentSession.id})`);

  try {
    let aiRawResponse;

    if (ANTHROPIC_KEY && ANTHROPIC_KEY !== "YOUR_API_KEY_HERE") {
      // ── Direct Anthropic API call ─────────────────────────────
      aiRawResponse = await callAnthropicDirect(currentSession.cleanText);
    } else {
      // ── Mock response (no key set) ────────────────────────────
      await new Promise((r) => setTimeout(r, 800));
      aiRawResponse = buildMockAIResponse(currentSession.tokenMap);
    }

    // Restore real identities in AI response
    const restoredResponse = restore(aiRawResponse, currentSession.tokenMap);

    outputFinal.className = "output-box";
    outputFinal.innerHTML = highlightRestored(restoredResponse, currentSession.tokenMap);
    logEvent("ti-replace", `Identities restored in AI response (session ${currentSession.id})`);

  } catch (err) {
    logEvent("ti-alert-circle", `AI error: ${err.message}`);
    // Fallback to mock on any error
    const mock      = buildMockAIResponse(currentSession.tokenMap);
    const restored  = restore(mock, currentSession.tokenMap);
    outputFinal.className = "output-box";
    outputFinal.innerHTML = highlightRestored(restored, currentSession.tokenMap);
    logEvent("ti-info-circle", "Showing demo response (API unavailable)");
  } finally {
    btnSendAI.innerHTML = '<i class="ti ti-sparkles"></i> Send to AI assistant';
    btnSendAI.disabled  = false;
  }
});

// ── Direct Anthropic API call ─────────────────────────────────────
async function callAnthropicDirect(cleanText) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type":            "application/json",
      "x-api-key":               ANTHROPIC_KEY,
      "anthropic-version":       "2023-06-01",
      "anthropic-dangerous-request-check": "skip",
    },
    body: JSON.stringify({
      model:      "claude-sonnet-4-6",
      max_tokens: 512,
      messages: [{
        role:    "user",
        content: `You are a clinical decision support assistant. 
Summarise the following de-identified clinical note and suggest next steps. 
Use the placeholder names exactly as given — do NOT invent real names.\n\n${cleanText}`
      }]
    })
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || `API error ${res.status}`);
  }

  const data = await res.json();
  return data.content[0].text;
}

// ── Rendering helpers ─────────────────────────────────────────────
function highlightPseudonyms(text, tokenMap) {
  let html = escapeHtml(text);
  for (const p of Object.keys(tokenMap)) {
    html = html.split(escapeHtml(p)).join(`<span class="pseudo">${escapeHtml(p)}</span>`);
  }
  return html;
}

function highlightRestored(text, tokenMap) {
  let html = escapeHtml(text);
  for (const original of Object.values(tokenMap)) {
    html = html.split(escapeHtml(original)).join(`<span class="restored">${escapeHtml(original)}</span>`);
  }
  return html;
}

function renderTokenMap(tokenMap) {
  tokenMapEl.className = "token-map";
  tokenMapEl.innerHTML = "";
  for (const [pseudonym, original] of Object.entries(tokenMap)) {
    const category = pseudonym.startsWith("Patient") ? "NAME" : pseudonym.split("_")[0];
    const row      = document.createElement("div");
    row.className  = "token-row";
    row.innerHTML  = `
      <span class="pseudo-label">${escapeHtml(pseudonym)}</span>
      <span class="arrow"><i class="ti ti-arrow-right"></i></span>
      <span class="original-label">${escapeHtml(original)}</span>
      <span class="category-badge">${CATEGORY_LABELS[category] || category}</span>
      <i class="ti ti-lock" title="Stored in Vault"></i>
    `;
    tokenMapEl.appendChild(row);
  }
}

function renderVaultTable() {
  const tbody = document.getElementById("vault-table-body");
  tbody.innerHTML = "";
  if (!sessions.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-row">No sessions yet.</td></tr>';
    return;
  }
  for (const s of sessions) {
    const tr      = document.createElement("tr");
    tr.innerHTML  = `
      <td>${s.id}</td>
      <td>${Object.keys(s.tokenMap).length}</td>
      <td>${s.createdAt.toLocaleTimeString()}</td>
      <td>30 min</td>
      <td><i class="ti ti-trash" style="cursor:pointer;color:var(--text-tertiary)" data-session="${s.id}"></i></td>
    `;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("[data-session]").forEach((icon) => {
    icon.addEventListener("click", () => {
      const id  = icon.dataset.session;
      const idx = sessions.findIndex((s) => s.id === id);
      if (idx !== -1) sessions.splice(idx, 1);
      logEvent("ti-trash", `Vault session ${id} deleted`);
      renderVaultTable();
      updateMetrics();
    });
  });
}

function updateMetrics() {
  document.getElementById("metric-sessions").textContent = sessions.length;
  document.getElementById("metric-tokens").textContent   =
    sessions.reduce((s, sess) => s + Object.keys(sess.tokenMap).length, 0);
}

function logEvent(icon, message) {
  auditEvents.unshift({ icon, message, time: new Date() });
  const container  = document.getElementById("audit-log");
  container.innerHTML = "";
  for (const ev of auditEvents) {
    const div      = document.createElement("div");
    div.className  = "audit-entry";
    div.innerHTML  = `
      <i class="ti ${ev.icon}"></i>
      <span>${escapeHtml(ev.message)}</span>
      <span class="audit-time">${ev.time.toLocaleTimeString()}</span>
    `;
    container.appendChild(div);
  }
}

function buildMockAIResponse(tokenMap) {
  const patient = Object.keys(tokenMap).find((k) => k.startsWith("Patient")) || "Patient A";
  return `Summary: ${patient} presents with respiratory symptoms consistent with a mild lower respiratory tract infection. Recommend completing the prescribed antibiotic course, repeat chest imaging if symptoms persist beyond 5 days, and a follow-up consult. No red-flag findings noted for ${patient} at this time.`;
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}
