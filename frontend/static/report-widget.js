/**
 * OneTimeView — Report a Problem Widget
 * Injects a floating "Report" button + modal on every page.
 * Submits to POST /api/report → saved directly to Supabase.
 */
(function () {
  'use strict';

  const ISSUE_TYPES = [
    { value: 'create',      label: '📝 Secret creation not working' },
    { value: 'view',        label: '👁️  Cannot view / unlock a secret' },
    { value: 'file_upload', label: '📎 File upload issue' },
    { value: 'expired',     label: '⏰ Expired page shown incorrectly' },
    { value: 'navigation',  label: '🔗 Broken link / navigation error' },
    { value: 'performance', label: '🐢 Page is very slow' },
    { value: 'other',       label: '🔧 Something else' },
  ];

  function injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      #otv-report-btn {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9000;
        display: flex;
        align-items: center;
        gap: 7px;
        padding: 9px 16px;
        background: rgba(15,16,19,0.92);
        border: 1px solid rgba(255,255,255,0.13);
        border-radius: 999px;
        color: #a1a1aa;
        font-size: 12.5px;
        font-weight: 500;
        font-family: inherit;
        cursor: pointer;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        user-select: none;
      }
      #otv-report-btn:hover {
        color: #fff;
        border-color: rgba(255,255,255,0.25);
        background: rgba(23,24,29,0.98);
      }
      #otv-report-btn svg { flex-shrink: 0; }

      #otv-report-overlay {
        display: none;
        position: fixed;
        inset: 0;
        z-index: 9100;
        background: rgba(0,0,0,0.55);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        align-items: center;
        justify-content: center;
        padding: 16px;
      }
      #otv-report-overlay.active { display: flex; }

      #otv-report-modal {
        background: #0f1013;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 28px;
        width: 100%;
        max-width: 460px;
        box-shadow: 0 24px 60px rgba(0,0,0,0.7);
        position: relative;
        animation: otvSlideUp 0.22s cubic-bezier(0.16,1,0.3,1);
      }
      @keyframes otvSlideUp {
        from { transform: translateY(18px); opacity: 0; }
        to   { transform: translateY(0);    opacity: 1; }
      }

      #otv-report-modal h2 {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
        margin: 0 0 4px 0;
        letter-spacing: -0.02em;
      }
      #otv-report-modal .otv-subtitle {
        font-size: 12.5px;
        color: #71717a;
        margin: 0 0 20px 0;
      }
      .otv-close-btn {
        position: absolute;
        top: 16px;
        right: 16px;
        background: none;
        border: none;
        color: #52525b;
        cursor: pointer;
        padding: 4px;
        border-radius: 6px;
        line-height: 1;
        transition: color 0.15s ease;
      }
      .otv-close-btn:hover { color: #fff; }

      .otv-field { margin-bottom: 14px; }
      .otv-label {
        display: block;
        font-size: 11.5px;
        font-weight: 600;
        color: #a1a1aa;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
      }
      .otv-select, .otv-textarea, .otv-input {
        width: 100%;
        background: #070809;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        color: #f4f4f5;
        font-size: 13.5px;
        font-family: inherit;
        padding: 9px 12px;
        outline: none;
        transition: border-color 0.15s ease;
        box-sizing: border-box;
      }
      .otv-select:focus, .otv-textarea:focus, .otv-input:focus {
        border-color: rgba(255,255,255,0.28);
      }
      .otv-select option { background: #0f1013; }
      .otv-textarea {
        resize: vertical;
        min-height: 90px;
        line-height: 1.55;
      }
      .otv-char-count {
        font-size: 11px;
        color: #52525b;
        text-align: right;
        margin-top: 3px;
      }
      .otv-char-count.warn { color: #f59e0b; }
      .otv-char-count.error { color: #f43f5e; }

      #otv-submit-btn {
        width: 100%;
        margin-top: 6px;
        padding: 10px 16px;
        background: #fff;
        color: #000;
        border: none;
        border-radius: 8px;
        font-size: 13.5px;
        font-weight: 600;
        font-family: inherit;
        cursor: pointer;
        transition: background 0.15s ease, opacity 0.15s ease;
      }
      #otv-submit-btn:hover { background: #e5e5e5; }
      #otv-submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

      #otv-report-success {
        text-align: center;
        padding: 10px 0 4px;
      }
      #otv-report-success .otv-success-icon {
        width: 44px;
        height: 44px;
        background: rgba(16,185,129,0.12);
        border: 1px solid rgba(16,185,129,0.25);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
        color: #10b981;
      }
      #otv-report-success h3 {
        font-size: 1rem;
        font-weight: 700;
        color: #fff;
        margin: 0 0 6px;
      }
      #otv-report-success p {
        font-size: 13px;
        color: #71717a;
        margin: 0 0 18px;
      }
      .otv-error-msg {
        font-size: 12px;
        color: #f43f5e;
        margin-top: 8px;
        text-align: center;
        display: none;
      }
    `;
    document.head.appendChild(style);
  }

  function buildModal() {
    // Floating trigger button
    const btn = document.createElement('button');
    btn.id = 'otv-report-btn';
    btn.setAttribute('aria-label', 'Report a problem');
    btn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      Report a problem
    `;

    // Overlay + modal
    const overlay = document.createElement('div');
    overlay.id = 'otv-report-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', 'otv-report-title');

    const issueOptions = ISSUE_TYPES.map(t =>
      `<option value="${t.value}">${t.label}</option>`
    ).join('');

    overlay.innerHTML = `
      <div id="otv-report-modal">
        <button class="otv-close-btn" id="otv-close-btn" aria-label="Close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>

        <!-- Form view -->
        <div id="otv-report-form-view">
          <h2 id="otv-report-title">Report a Problem</h2>
          <p class="otv-subtitle">Something not working? Let us know and we'll fix it.</p>

          <div class="otv-field">
            <label class="otv-label" for="otv-issue-type">What's the issue?</label>
            <select id="otv-issue-type" class="otv-select">
              ${issueOptions}
            </select>
          </div>

          <div class="otv-field">
            <label class="otv-label" for="otv-description">Describe the problem <span style="color:#f43f5e">*</span></label>
            <textarea id="otv-description" class="otv-textarea" maxlength="2000"
              placeholder="e.g. When I click 'Generate One-Time Link', nothing happens and no error shows…"></textarea>
            <div class="otv-char-count" id="otv-char-count">0 / 2000</div>
          </div>

          <div class="otv-field">
            <label class="otv-label" for="otv-email">Your email <span style="color:#52525b">(optional — for follow-up)</span></label>
            <input type="email" id="otv-email" class="otv-input" placeholder="you@example.com" maxlength="255">
          </div>

          <div class="otv-error-msg" id="otv-error-msg">Something went wrong. Please try again.</div>

          <button id="otv-submit-btn">Submit Report</button>
        </div>

        <!-- Success view -->
        <div id="otv-report-success" style="display:none">
          <div class="otv-success-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <h3>Report Submitted</h3>
          <p>Thank you! We've received your report and will look into it.</p>
          <button id="otv-close-success" style="
            background:none; border:1px solid rgba(255,255,255,0.12);
            color:#a1a1aa; border-radius:8px; padding:8px 20px;
            font-size:13px; font-family:inherit; cursor:pointer; transition:color .15s,border-color .15s;
          ">Close</button>
        </div>
      </div>
    `;

    document.body.appendChild(btn);
    document.body.appendChild(overlay);
  }

  function bindEvents() {
    const btn      = document.getElementById('otv-report-btn');
    const overlay  = document.getElementById('otv-report-overlay');
    const closeBtn = document.getElementById('otv-close-btn');
    const submitBtn= document.getElementById('otv-submit-btn');
    const textarea = document.getElementById('otv-description');
    const charCount= document.getElementById('otv-char-count');
    const errorMsg = document.getElementById('otv-error-msg');
    const successV = document.getElementById('otv-report-success');
    const formV    = document.getElementById('otv-report-form-view');
    const closeSuc = document.getElementById('otv-close-success');

    function openModal() {
      overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      setTimeout(() => document.getElementById('otv-issue-type')?.focus(), 80);
    }

    function closeModal() {
      overlay.classList.remove('active');
      document.body.style.overflow = '';
      // Reset form after close
      setTimeout(() => {
        formV.style.display = '';
        successV.style.display = 'none';
        document.getElementById('otv-description').value = '';
        document.getElementById('otv-email').value = '';
        document.getElementById('otv-issue-type').selectedIndex = 0;
        charCount.textContent = '0 / 2000';
        charCount.className = 'otv-char-count';
        errorMsg.style.display = 'none';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Report';
      }, 250);
    }

    btn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);
    closeSuc.addEventListener('click', closeModal);

    // Close on overlay background click
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && overlay.classList.contains('active')) closeModal();
    });

    // Character counter
    textarea.addEventListener('input', function () {
      const len = this.value.length;
      charCount.textContent = `${len} / 2000`;
      charCount.className = 'otv-char-count' + (len > 1800 ? ' warn' : '') + (len >= 2000 ? ' error' : '');
    });

    // Submit
    submitBtn.addEventListener('click', async function () {
      const issueType   = document.getElementById('otv-issue-type').value;
      const description = textarea.value.trim();
      const email       = document.getElementById('otv-email').value.trim();

      errorMsg.style.display = 'none';

      if (!description || description.length < 10) {
        errorMsg.textContent = 'Please describe the issue (at least 10 characters).';
        errorMsg.style.display = 'block';
        textarea.focus();
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting…';

      const payload = {
        page:          window.location.pathname || '/',
        issue_type:    issueType,
        description:   description,
        contact_email: email || null,
        url:           window.location.href,
        user_agent:    navigator.userAgent,
      };

      try {
        const apiBase = (typeof APP_CONFIG !== 'undefined' && APP_CONFIG.API_BASE_URL)
          ? APP_CONFIG.API_BASE_URL
          : '';
        const res = await fetch(`${apiBase}/api/report`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || `HTTP ${res.status}`);
        }

        // Show success
        formV.style.display = 'none';
        successV.style.display = 'block';

      } catch (err) {
        errorMsg.textContent = `Failed to submit: ${err.message}. Please try again.`;
        errorMsg.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Report';
      }
    });
  }

  function init() {
    injectStyles();
    buildModal();
    bindEvents();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
