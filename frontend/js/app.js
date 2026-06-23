/**
 * app.js — Main Controller
 * Coordinates API calls, UI rendering, login states, and de-identification engine fallbacks
 */

// ── Configuration ────────────────────────────────────────────────
const USE_BACKEND = true;

// ── State ────────────────────────────────────────────────────────
let sessions = [];
const auditEvents = [];
let currentSession = null;
let currentUser = null; // Set dynamically upon gateway authorization

// ── DOM References ───────────────────────────────────────────────
const inputNote      = document.getElementById("input-note");
const outputRedacted = document.getElementById("output-redacted");
const outputFinal    = document.getElementById("output-final");
const tokenMapEl     = document.getElementById("token-map");
const btnRedact      = document.getElementById("btn-redact");
const btnSendAI      = document.getElementById("btn-send-ai");
const btnClear       = document.getElementById("btn-clear");

// ── Navigation ───────────────────────────────────────────────────
document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", (e) => {
    e.preventDefault();
    
    // Block navigation if user is not authenticated
    if (!currentUser) {
      UI.logEvent("ti-shield-lock", "Access Denied: Please authorize first.", auditEvents);
      return;
    }
    
    document.querySelectorAll(".nav-item").forEach((i) => i.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    
    item.classList.add("active");
    const targetView = document.getElementById(`view-${item.dataset.view}`);
    if (targetView) {
      targetView.classList.add("active");
    }
    
    if (item.dataset.view === "vault") {
      fetchBackendSessions();
    }
  });
});

// ── Authentication Gateway ────────────────────────────────────────
function login(username) {
  if (username === "dr_alex") {
    currentUser = {
      name: "Dr. Alex Carter, MD",
      role: "full",
      roleLabel: "HIPAA Full Access",
      avatar: "img/dr_alex_profile.png",
      isImage: true
    };
  } else {
    currentUser = {
      name: "Jash Shah",
      role: "restricted",
      roleLabel: "Restricted Access",
      avatar: "",
      isImage: false
    };
  }
  
  // Update sidebar profile card UI
  const profileCard = document.getElementById("sidebar-profile-card");
  const avatarImg = document.getElementById("sidebar-user-avatar");
  const userNameEl = document.getElementById("sidebar-user-name");
  const userRoleEl = document.getElementById("sidebar-user-role");
  
  userNameEl.textContent = currentUser.name;
  userRoleEl.textContent = currentUser.roleLabel;
  
  // Clean up any existing dynamic placeholders
  const existingPlaceholder = profileCard.querySelector(".avatar-placeholder");
  if (existingPlaceholder) existingPlaceholder.remove();

  if (currentUser.isImage) {
    avatarImg.style.display = "block";
    avatarImg.src = currentUser.avatar;
  } else {
    avatarImg.style.display = "none";
    // Create and insert profile placeholder
    const placeholder = document.createElement("div");
    placeholder.className = "avatar-placeholder user-avatar";
    placeholder.innerHTML = '<i class="ti ti-user"></i>';
    profileCard.insertBefore(placeholder, avatarImg);
  }
  
  // Toggle role CSS badge styling
  if (currentUser.role === "full") {
    userRoleEl.className = "badge-role badge-full";
  } else {
    userRoleEl.className = "badge-role badge-restricted";
  }
  
  profileCard.style.display = "flex";
  
  // Navigate to main proxy editor view
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.getElementById("view-proxy").classList.add("active");
  
  document.querySelectorAll(".nav-item").forEach((i) => i.classList.remove("active"));
  document.querySelector('.nav-item[data-view="proxy"]').classList.add("active");
  
  UI.logEvent("ti-user-check", `User ${currentUser.name} logged in (${currentUser.roleLabel})`, auditEvents);
}

// Attach login selection event listeners
document.addEventListener("DOMContentLoaded", () => {
  // Use event delegation or check interval since custom elements render synchronously
  const checkInterval = setInterval(() => {
    const cards = document.querySelectorAll(".profile-select-card");
    if (cards.length > 0) {
      clearInterval(checkInterval);
      cards.forEach((card) => {
        card.addEventListener("click", () => {
          login(card.dataset.user);
        });
      });
    }
  }, 50);
});

// Logout Handler
const btnLogout = document.getElementById("btn-logout");
if (btnLogout) {
  btnLogout.addEventListener("click", (e) => {
    e.preventDefault();
    currentUser = null;
    document.getElementById("sidebar-profile-card").style.display = "none";
    
    // Clear outputs and navigate back to login view
    btnClear.click();
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    document.getElementById("view-login").classList.add("active");
    
    UI.logEvent("ti-logout", "User logged out from EHR proxy session", auditEvents);
  });
}

// ── Action: Run Redaction ─────────────────────────────────────────
btnRedact.addEventListener("click", async () => {
  const text = inputNote.value.trim();
  if (!text) return;

  btnRedact.disabled = true;
  btnRedact.innerHTML = '<i class="ti ti-loader-2 animate-spin"></i> Redacting...';

  try {
    let cleanText, tokenMap, entitiesFound, sessionId;

    if (USE_BACKEND) {
      try {
        const data = await API.redact(text);
        cleanText = data.clean_text;
        tokenMap = data.token_map;
        entitiesFound = data.entities_found;
        sessionId = data.session_id;
      } catch (err) {
        console.warn("Backend redaction failed. Falling back to client-side engine.", err);
        UI.logEvent("ti-alert-circle", `Backend error: ${err.message}. Running locally...`, auditEvents);
        
        // Local Fallback
        const local = redact(text);
        cleanText = local.cleanText;
        tokenMap = local.tokenMap;
        entitiesFound = Object.keys(tokenMap).length;
        sessionId = newSessionId();
      }
    } else {
      const local = redact(text);
      cleanText = local.cleanText;
      tokenMap = local.tokenMap;
      entitiesFound = Object.keys(tokenMap).length;
      sessionId = newSessionId();
    }

    if (entitiesFound === 0) {
      outputRedacted.className = "output-box placeholder";
      outputRedacted.textContent = "No PHI detected in this note.";
      btnSendAI.disabled = true;
      return;
    }

    outputRedacted.className = "output-box";
    outputRedacted.innerHTML = UI.highlightPseudonyms(cleanText, tokenMap);

    resetFinalOutput();
    UI.renderTokenMap(tokenMap);

    currentSession = {
      id: sessionId,
      tokenMap,
      cleanText,
      createdAt: new Date(),
      tokenCount: entitiesFound,
      expiresInMins: 30
    };

    const existingIndex = sessions.findIndex(s => s.id === sessionId);
    if (existingIndex !== -1) {
      sessions[existingIndex] = currentSession;
    } else {
      sessions.unshift(currentSession);
    }
    
    UI.renderVaultTable(sessions, deleteSessionCallback);
    UI.updateMetrics(sessions);
    UI.logEvent("ti-scan", `Redacted — ${entitiesFound} entities detected. Session: ${currentSession.id}`, auditEvents);

    btnSendAI.disabled = false;
  } catch (err) {
    console.error(err);
    UI.logEvent("ti-alert-circle", `Redaction error: ${err.message}`, auditEvents);
  } finally {
    btnRedact.disabled = false;
    btnRedact.innerHTML = '<i class="ti ti-scan"></i> Run redaction';
  }
});

// ── Action: Send to AI ────────────────────────────────────────────
btnSendAI.addEventListener("click", async () => {
  if (!currentSession) return;

  btnSendAI.disabled = true;
  btnSendAI.innerHTML = '<i class="ti ti-loader-2 animate-spin"></i> Waiting for AI...';
  UI.logEvent("ti-cloud-upload", `Sent de-identified note to AI (Session: ${currentSession.id})`, auditEvents);

  try {
    let aiRawResponse, restoredResponse;

    if (USE_BACKEND) {
      try {
        const data = await API.ask(currentSession.id, currentSession.cleanText);
        aiRawResponse = data.ai_response_raw;
        restoredResponse = data.ai_response_restored;
      } catch (err) {
        console.warn("Backend AI call failed. Falling back to local mock response.", err);
        UI.logEvent("ti-alert-circle", `AI backend failed: ${err.message}. Showing local mock response.`, auditEvents);
        
        // Local Fallback
        aiRawResponse = buildMockAIResponse(currentSession.tokenMap);
        restoredResponse = restore(aiRawResponse, currentSession.tokenMap);
      }
    } else {
      aiRawResponse = buildMockAIResponse(currentSession.tokenMap);
      restoredResponse = restore(aiRawResponse, currentSession.tokenMap);
    }

    // Role-based Access Rules checking de-redaction permissions
    if (currentUser && currentUser.role === "restricted") {
      outputFinal.className = "output-box";
      outputFinal.innerHTML = `
        <div class="warning-banner">
          <i class="ti ti-lock-off"></i>
          <div>
            <p>Access Denied (Compliance Policy)</p>
            <span>Your role (${currentUser.roleLabel}) does not have privileges to view restored patient identities. Stored mapping identifiers remain masked.</span>
          </div>
        </div>
        <div class="output-box" style="margin-top: 1rem;">${UI.highlightPseudonyms(aiRawResponse, currentSession.tokenMap)}</div>
      `;
      UI.logEvent("ti-shield-alert", `Access Denied: Identity restoration blocked for ${currentUser.name} (Restricted Access)`, auditEvents);
    } else {
      outputFinal.className = "output-box";
      outputFinal.innerHTML = UI.highlightRestored(restoredResponse, currentSession.tokenMap);
      UI.logEvent("ti-replace", `Identities restored in AI response (Session: ${currentSession.id})`, auditEvents);
    }

  } catch (err) {
    console.error(err);
    UI.logEvent("ti-alert-circle", `AI error: ${err.message}`, auditEvents);
  } finally {
    btnSendAI.innerHTML = '<i class="ti ti-sparkles"></i> Send to AI assistant';
    btnSendAI.disabled = false;
  }
});

// ── Action: Clear ─────────────────────────────────────────────────
btnClear.addEventListener("click", () => {
  inputNote.value = "";
  outputRedacted.className = "output-box placeholder";
  outputRedacted.textContent = "Run redaction to see the de-identified version of this note.";
  resetFinalOutput();
  tokenMapEl.className = "token-map placeholder";
  tokenMapEl.textContent = "No active session. Token mappings will appear here after redaction.";
  btnSendAI.disabled = true;
  currentSession = null;
});

function resetFinalOutput() {
  outputFinal.className = "output-box placeholder";
  outputFinal.textContent = "The AI's response, with patient identity restored, will appear here.";
}

// ── Action: Delete Session Callback ───────────────────────────────
async function deleteSessionCallback(id) {
  // Restricted assistants are blocked from deleting audit entries
  if (currentUser && currentUser.role === "restricted") {
    UI.logEvent("ti-shield-alert", `Access Denied: Delete operation blocked for ${currentUser.name}`, auditEvents);
    alert("Compliance Warning: Research Assistants are not authorized to clear active vault sessions from the database.");
    return;
  }

  try {
    if (USE_BACKEND) {
      await API.deleteSession(id);
      UI.logEvent("ti-trash", `Vault session ${id} deleted from Redis database`, auditEvents);
    } else {
      UI.logEvent("ti-trash", `Vault session ${id} deleted locally`, auditEvents);
    }
  } catch (err) {
    console.error(err);
    UI.logEvent("ti-alert-circle", `Delete failed: ${err.message}`, auditEvents);
  } finally {
    sessions = sessions.filter(s => s.id !== id);
    UI.renderVaultTable(sessions, deleteSessionCallback);
    UI.updateMetrics(sessions);
  }
}

// ── Sync with Backend Sessions ────────────────────────────────────
async function fetchBackendSessions() {
  if (!USE_BACKEND || !currentUser) return;
  try {
    const data = await API.getSessions();
    sessions = data.sessions.map((s) => ({
      id: s.id,
      tokenCount: s.token_count,
      createdAt: new Date(),
      expiresInMins: s.expires_in_mins
    }));
    
    UI.renderVaultTable(sessions, deleteSessionCallback);
    UI.updateMetrics(sessions);
  } catch (err) {
    console.error("Backend session fetch failed:", err);
  }
}

// ── Mock Helpers ─────────────────────────────────────────────────
function buildMockAIResponse(tokenMap) {
  const patient = Object.keys(tokenMap).find((k) => k.startsWith("Patient")) || "Patient A";
  return `Summary: ${patient} presents with respiratory symptoms consistent with a mild lower respiratory tract infection. Recommend completing the prescribed antibiotic course, repeat chest imaging if symptoms persist beyond 5 days, and a follow-up consult. No red-flag findings noted for ${patient} at this time.`;
}

// Initial sync trigger
fetchBackendSessions();
if (USE_BACKEND) {
  setInterval(fetchBackendSessions, 5000); // Polling sync
}
