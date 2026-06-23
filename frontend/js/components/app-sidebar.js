/**
 * app-sidebar.js — Custom Web Component for Sidebar
 */

class AppSidebar extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <aside class="sidebar">
        <div class="brand">
          <i class="ti ti-shield-lock"></i>
          <span>PHI Redaction Proxy</span>
        </div>
        <nav class="nav">
          <a href="#" class="nav-item active" data-view="proxy">
            <i class="ti ti-message-2"></i> New note
          </a>
          <a href="#" class="nav-item" data-view="pipeline">
            <i class="ti ti-route"></i> Pipeline
          </a>
          <a href="#" class="nav-item" data-view="vault">
            <i class="ti ti-lock"></i> Vault sessions
          </a>
          <a href="#" class="nav-item" data-view="logs">
            <i class="ti ti-list-details"></i> Audit log
          </a>
          <a href="#" class="nav-item" data-view="settings">
            <i class="ti ti-settings"></i> Settings
          </a>
        </nav>
        
        <!-- Clinician Profile Card -->
        <div class="sidebar-user" id="sidebar-profile-card" style="display: none;">
          <img class="user-avatar" id="sidebar-user-avatar" src="img/dr_alex_profile.png" alt="Dr. Alex Carter" />
          <div class="user-info">
            <div class="user-name" id="sidebar-user-name">Dr. Alex Carter, MD</div>
            <div class="user-role">
              <span class="badge-role" id="sidebar-user-role">HIPAA Full Access</span>
            </div>
            <a href="#" class="user-switch-btn" id="btn-logout">Switch Profile</a>
          </div>
        </div>

        <div class="sidebar-footer">
          <div class="status-pill">
            <span class="dot dot-green"></span> Vault: connected
          </div>
          <div class="status-pill">
            <span class="dot dot-green"></span> Engine: ready
          </div>
        </div>
      </aside>
    `;
  }
}

customElements.define("app-sidebar", AppSidebar);
