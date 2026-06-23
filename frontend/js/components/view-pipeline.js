/**
 * view-pipeline.js — Custom Web Component for Pipeline Overview View
 */

class ViewPipeline extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <header class="view-header">
        <div>
          <h1>Pipeline overview</h1>
          <p class="subtitle">How a note moves through the redaction proxy</p>
        </div>
      </header>

      <div class="pipeline">
        <div class="pipeline-step">
          <div class="step-icon c-gray"><i class="ti ti-stethoscope"></i></div>
          <div class="step-body">
            <h4>1. Doctor submits note</h4>
            <p>Clinical note sent to the internal proxy API. Never leaves the org boundary unredacted.</p>
          </div>
        </div>
        <div class="pipeline-arrow"><i class="ti ti-arrow-down"></i></div>

        <div class="pipeline-step">
          <div class="step-icon c-coral"><i class="ti ti-scan"></i></div>
          <div class="step-body">
            <h4>2. Redaction engine</h4>
            <p>Regex rules + NLP entity detection run in parallel to catch names, dates, MRNs, contact details, addresses.</p>
          </div>
        </div>
        <div class="pipeline-arrow"><i class="ti ti-arrow-down"></i></div>

        <div class="pipeline-step">
          <div class="step-icon c-amber"><i class="ti ti-lock"></i></div>
          <div class="step-body">
            <h4>3. Vault stores token map</h4>
            <p>"Patient A" ↔ "Rahul Sharma" stored securely in Redis with a session TTL.</p>
          </div>
        </div>
        <div class="pipeline-arrow"><i class="ti ti-arrow-down"></i></div>

        <div class="pipeline-step">
          <div class="step-icon c-teal"><i class="ti ti-cloud-upload"></i></div>
          <div class="step-body">
            <h4>4. Clean text sent to external AI</h4>
            <p>No real names, dates, or identifiers leave the system. Only pseudonymized text is sent.</p>
          </div>
        </div>
        <div class="pipeline-arrow"><i class="ti ti-arrow-down"></i></div>

        <div class="pipeline-step">
          <div class="step-icon c-teal"><i class="ti ti-message-reply"></i></div>
          <div class="step-body">
            <h4>5. AI responds with pseudonyms</h4>
            <p>The external model's response references "Patient A" and other tokens only.</p>
          </div>
        </div>
        <div class="pipeline-arrow"><i class="ti ti-arrow-down"></i></div>

        <div class="pipeline-step">
          <div class="step-icon c-purple"><i class="ti ti-replace"></i></div>
          <div class="step-body">
            <h4>6. Vault restores identities</h4>
            <p>Pseudonyms swapped back to real patient details before the result reaches the doctor.</p>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define("view-pipeline", ViewPipeline);
