/**
 * view-logs.js — Custom Web Component for Audit Log View
 */

class ViewLogs extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <header class="view-header">
        <div>
          <h1>Audit log</h1>
          <p class="subtitle">Every redaction and restoration event, for compliance review</p>
        </div>
      </header>

      <div id="audit-log" class="audit-log">
        <p class="empty-row">No events yet.</p>
      </div>
    `;
  }
}

customElements.define("view-logs", ViewLogs);
