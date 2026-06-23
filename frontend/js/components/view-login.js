/**
 * view-login.js — Custom Web Component for Login Screen
 */

class ViewLogin extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <div class="login-overlay">
        <div class="login-card">
          <div class="login-brand">
            <i class="ti ti-shield-lock"></i>
            <span>HealthTech PHI Redaction Gate</span>
          </div>
          <h2>Access Gateway Authorization</h2>
          <p class="login-subtitle">Please select a clinician profile to log in to the EHR EHR-connected proxy. Access is logged for compliance auditing.</p>
          
          <div class="profile-select-grid">
            <!-- Full Access Profile -->
            <div class="profile-select-card" data-user="dr_alex">
              <div class="profile-card-header">
                <img class="profile-select-avatar" src="img/dr_alex_profile.png" alt="Dr. Alex Carter" />
                <span class="access-badge badge-full">Full HIPAA Access</span>
              </div>
              <div class="profile-card-body">
                <h3>Dr. Alex Carter, MD</h3>
                <p class="profile-title">Chief Medical Director</p>
                <p class="profile-desc">Full de-identification & identity restoration privileges. All clinical summaries restored.</p>
              </div>
            </div>

            <!-- Restricted Access Profile -->
            <div class="profile-select-card" data-user="jash_shah">
              <div class="profile-card-header">
                <div class="profile-select-avatar avatar-placeholder">
                  <i class="ti ti-user"></i>
                </div>
                <span class="access-badge badge-restricted">Restricted Access</span>
              </div>
              <div class="profile-card-body">
                <h3>Jash Shah</h3>
                <p class="profile-title">Research Assistant</p>
                <p class="profile-desc">De-identification privileges only. Stored patient identities remain redacted in AI summaries.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define("view-login", ViewLogin);
