/**
 * view-settings.js — Custom Web Component for Settings View
 */

class ViewSettings extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <header class="view-header">
        <div>
          <h1>Settings</h1>
          <p class="subtitle">Configure detection rules and proxy behaviour</p>
        </div>
      </header>

      <div class="card settings-card">
        <h3>Detection categories</h3>
        <div class="toggle-row">
          <label class="toggle"><input type="checkbox" checked disabled /><span>Names</span></label>
          <label class="toggle"><input type="checkbox" checked disabled /><span>Dates</span></label>
          <label class="toggle"><input type="checkbox" checked disabled /><span>Phone numbers</span></label>
          <label class="toggle"><input type="checkbox" checked disabled /><span>Emails</span></label>
          <label class="toggle"><input type="checkbox" checked disabled /><span>MRN / patient IDs</span></label>
          <label class="toggle"><input type="checkbox" checked disabled /><span>Addresses</span></label>
          <label class="toggle"><input type="checkbox" checked disabled /><span>Aadhaar / SSN</span></label>
        </div>
        <p class="note">These map directly to the regex + NLP rules implemented in <code>redaction_engine.py</code>. Toggles are illustrative for this demo build.</p>
      </div>

      <div class="card settings-card">
        <h3>Vault</h3>
        <div class="form-row">
          <label>Redis URL</label>
          <input type="text" value="redis://localhost:6379/0" disabled />
        </div>
        <div class="form-row">
          <label>Token TTL (seconds)</label>
          <input type="text" value="1800" disabled />
        </div>
      </div>
    `;
  }
}

customElements.define("view-settings", ViewSettings);
