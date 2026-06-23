/**
 * view-proxy.js — Custom Web Component for Proxy View
 */

class ViewProxy extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <header class="view-header">
        <div>
          <h1>Clinical note proxy</h1>
          <p class="subtitle">Submit a note. PHI never leaves this boundary.</p>
        </div>
        <div class="boundary-badge">
          <i class="ti ti-shield-check"></i> Org control boundary
        </div>
      </header>

      <div class="proxy-grid">

        <!-- Input -->
        <div class="card">
          <div class="card-header">
            <h3><i class="ti ti-file-text"></i> Original note (doctor input)</h3>
            <span class="tag tag-coral">Contains PHI</span>
          </div>
          <textarea id="input-note" rows="10" placeholder="Paste or type the clinical note here...">Patient Rahul Sharma, DOB 14/03/1985, MRN: 4582193, presented on 12/06/2026 with persistent cough and fever (101.2 F). Contact: rahul.sharma@gmail.com, +91 98765 43210. Address: 22 MG Road, Jodhpur. Dr. Anita Verma recommends a chest X-ray and a 5-day course of azithromycin. Aadhaar 1234 5678 9012.</textarea>
          <div class="card-actions">
            <button id="btn-redact" class="btn btn-primary">
              <i class="ti ti-scan"></i> Run redaction
            </button>
            <button id="btn-clear" class="btn btn-ghost">
              <i class="ti ti-trash"></i> Clear
            </button>
          </div>
        </div>

        <!-- Redacted -->
        <div class="card">
          <div class="card-header">
            <h3><i class="ti ti-eraser"></i> Redacted (sent to external AI)</h3>
            <span class="tag tag-teal">PHI removed</span>
          </div>
          <div id="output-redacted" class="output-box placeholder">
            Run redaction to see the de-identified version of this note.
          </div>
          <div class="card-actions">
            <button id="btn-send-ai" class="btn btn-primary" disabled>
              <i class="ti ti-sparkles"></i> Send to AI assistant
            </button>
          </div>
        </div>

        <!-- Token map -->
        <div class="card">
          <div class="card-header">
            <h3><i class="ti ti-key"></i> Vault token map</h3>
            <span class="tag tag-gray">Redis (TTL 30 min)</span>
          </div>
          <div id="token-map" class="token-map placeholder">
            No active session. Token mappings will appear here after redaction.
          </div>
        </div>

        <!-- AI response -->
        <div class="card">
          <div class="card-header">
            <h3><i class="ti ti-robot"></i> AI response (restored)</h3>
            <span class="tag tag-purple">Identities restored</span>
          </div>
          <div id="output-final" class="output-box placeholder">
            The AI's response, with patient identity restored, will appear here.
          </div>
        </div>

      </div>
    `;
  }
}

customElements.define("view-proxy", ViewProxy);
