/**
 * view-vault.js — Custom Web Component for Vault Sessions View
 */

class ViewVault extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <header class="view-header">
        <div>
          <h1>Vault sessions</h1>
          <p class="subtitle">Active token maps stored in Redis</p>
        </div>
      </header>

      <div class="metric-grid">
        <div class="metric-card">
          <span class="metric-label">Active sessions</span>
          <span class="metric-value" id="metric-sessions">0</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Tokens stored</span>
          <span class="metric-value" id="metric-tokens">0</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Session TTL</span>
          <span class="metric-value">30 min</span>
        </div>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>Session ID</th>
            <th>Tokens</th>
            <th>Created</th>
            <th>Expires in</th>
            <th></th>
          </tr>
        </thead>
        <tbody id="vault-table-body">
          <tr>
            <td colspan="5" class="empty-row">No sessions yet. Run a redaction to create one.</td>
          </tr>
        </tbody>
      </table>
    `;
  }
}

customElements.define("view-vault", ViewVault);
