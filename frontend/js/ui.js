/**
 * ui.js — Encapsulates UI rendering, highlighting, and logging
 */

class UI {
  static get CATEGORY_LABELS() {
    return {
      NAME: "Name", DATE: "Date", PHONE: "Phone",
      EMAIL: "Email", MRN: "MRN", SSN: "SSN",
      AADHAAR: "Aadhaar", ADDRESS: "Address",
    };
  }

  static highlightPseudonyms(text, tokenMap) {
    let html = this.escapeHtml(text);
    for (const p of Object.keys(tokenMap)) {
      html = html.split(this.escapeHtml(p)).join(`<span class="pseudo">${this.escapeHtml(p)}</span>`);
    }
    return html;
  }

  static highlightRestored(text, tokenMap) {
    let html = this.escapeHtml(text);
    for (const original of Object.values(tokenMap)) {
      html = html.split(this.escapeHtml(original)).join(`<span class="restored">${this.escapeHtml(original)}</span>`);
    }
    return html;
  }

  static renderTokenMap(tokenMap) {
    const tokenMapEl = document.getElementById("token-map");
    tokenMapEl.className = "token-map";
    tokenMapEl.innerHTML = "";
    for (const [pseudonym, original] of Object.entries(tokenMap)) {
      const category = pseudonym.startsWith("Patient") ? "NAME" : pseudonym.split("_")[0];
      const row      = document.createElement("div");
      row.className  = "token-row";
      row.innerHTML  = `
        <span class="pseudo-label">${this.escapeHtml(pseudonym)}</span>
        <span class="arrow"><i class="ti ti-arrow-right"></i></span>
        <span class="original-label">${this.escapeHtml(original)}</span>
        <span class="category-badge">${this.CATEGORY_LABELS[category] || category}</span>
        <i class="ti ti-lock" title="Stored securely in Redis"></i>
      `;
      tokenMapEl.appendChild(row);
    }
  }

  static renderVaultTable(sessions, onDeleteSession) {
    const tbody = document.getElementById("vault-table-body");
    tbody.innerHTML = "";
    if (!sessions.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-row">No sessions yet. Run a redaction to create one.</td></tr>';
      return;
    }
    for (const s of sessions) {
      const tr      = document.createElement("tr");
      tr.innerHTML  = `
        <td>${s.id}</td>
        <td>${s.tokenCount}</td>
        <td>${s.createdAt.toLocaleTimeString()}</td>
        <td>${s.expiresInMins} min</td>
        <td><i class="ti ti-trash" style="cursor:pointer;color:var(--text-tertiary)" data-session="${s.id}" title="Delete session from Redis"></i></td>
      `;
      tbody.appendChild(tr);
    }
    tbody.querySelectorAll("[data-session]").forEach((icon) => {
      icon.addEventListener("click", () => {
        const id = icon.dataset.session;
        if (onDeleteSession) onDeleteSession(id);
      });
    });
  }

  static updateMetrics(sessions) {
    document.getElementById("metric-sessions").textContent = sessions.length;
    document.getElementById("metric-tokens").textContent   =
      sessions.reduce((s, sess) => s + sess.tokenCount, 0);
  }

  static logEvent(icon, message, auditEvents) {
    auditEvents.unshift({ icon, message, time: new Date() });
    const container  = document.getElementById("audit-log");
    container.innerHTML = "";
    for (const ev of auditEvents) {
      const div      = document.createElement("div");
      div.className  = "audit-entry";
      div.innerHTML  = `
        <i class="ti ${ev.icon}"></i>
        <span>${this.escapeHtml(ev.message)}</span>
        <span class="audit-time">${ev.time.toLocaleTimeString()}</span>
      `;
      container.appendChild(div);
    }
  }

  static escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
  }
}

window.UI = UI;
