K.auth = {
  accounts: JSON.parse(localStorage.getItem('k_accounts') || '[]'),
  activeIdx: parseInt(localStorage.getItem('k_active_idx') || '0'),

  hideSplash() {
    const s = $('splashScreen'); if (s) { s.classList.add('fade-out'); setTimeout(() => { if (s) s.style.display = 'none'; }, 600); }
  },
  _startSplashTimer() {
    const fill = $('splashFill'); if (!fill) return;
    let pct = 0;
    const step = () => { pct += 5; fill.style.width = Math.min(pct, 100) + '%'; if (pct < 100) setTimeout(step, 100); };
    step();
    setTimeout(() => K.auth.hideSplash(), 2000);
  },
  async init() {
    K.auth._startSplashTimer();
    if (this.accounts.length > 0) K.auth.activeIdx = Math.min(K.auth.activeIdx, this.accounts.length - 1);
    try {
      const d = await K.api.get(V2 + '/profile');
      if (d.success && d.data) {
        K.state.user = d.data;
        K.ui.renderUser();
        K.auth.renderTabs();
        K.chat.loadList();
        K.contacts.load();
        K.stories.load();
        K.settings.loadPrivacy();
        K.settings.loadSessions();
        K.saved.load();
        return;
      }
    } catch(e) { console.warn('K init error', e); }
    if (this.accounts.length > 0) {
      this.removeAccount(this.activeIdx);
      location.reload();
    } else {
      setTimeout(() => { window.location.href = '/'; }, 2200);
    }
  },
  async login(username, password) {
    try {
      const d = await K.api.post(V2 + '/auth/login', {username, password});
      if (d.success && d.data && d.data.session_token) {
        const u = d.data.user;
        this.accounts.push({username: u.username, displayName: u.display_name || u.username, avatarUrl: u.avatar_url || '', userId: u.user_id, token: d.data.session_token});
        this.activeIdx = this.accounts.length - 1;
        this._save();
        K.auth.renderTabs();
        return {success: true};
      }
      return {success: false, error: d.error?.message || 'Login failed'};
    } catch(e) {
      return {success: false, error: e.body?.error?.message || e.message || 'Invalid credentials'};
    }
  },
  async register(username, email, password) {
    try {
      const d = await K.api.post(V2 + '/auth/register', {username, email, password});
      if (d.success && d.data && d.data.session_token) {
        const u = d.data.user;
        this.accounts.push({username: u.username, displayName: u.display_name || u.username, avatarUrl: u.avatar_url || '', userId: u.user_id, token: d.data.session_token});
        this.activeIdx = this.accounts.length - 1;
        this._save();
        K.auth.renderTabs();
        return {success: true};
      }
      return {success: false, error: d.error?.message || 'Registration failed'};
    } catch(e) {
      return {success: false, error: 'Server error'};
    }
  },
  switchAccount(idx) {
    if (idx === this.activeIdx || idx < 0 || idx >= this.accounts.length) return;
    this.activeIdx = idx;
    this._save();
    location.reload();
  },
  removeAccount(idx) {
    if (idx < 0 || idx >= this.accounts.length) return;
    this.accounts.splice(idx, 1);
    if (this.activeIdx >= this.accounts.length) this.activeIdx = Math.max(0, this.accounts.length - 1);
    this._save();
  },
  async logout() {
    if (await K.ui.confirm('Sign out?')) {
      try { await K.api.post(V2 + '/auth/logout'); } catch(e) {}
      const wasActive = this.activeIdx;
      this.accounts.splice(wasActive, 1);
      if (this.accounts.length === 0) { this._save(); window.location.href = '/'; return; }
      if (this.activeIdx >= this.accounts.length) this.activeIdx = 0;
      this._save();
      location.reload();
    }
  },
  renderTabs() {
    const c = $('accountTabs'); if (!c) return;
    c.innerHTML = this.accounts.map((a, i) =>
      `<div class="k-acc-tab ${i === K.auth.activeIdx ? 'active' : ''}" onclick="K.auth.switchAccount(${i})" title="${esc(a.displayName)}">${esc(a.username[0] || '?').toUpperCase()}</div>`
    ).join('') + `<div class="k-acc-tab k-acc-add" onclick="K.auth.showAddAccount()" title="Add account">+</div>`;
  },
  showAddAccount() {
    const o = $('modalOverlay'); o.style.display = 'flex';
    $('modalContent').innerHTML = `
      <div class="k-modal-header"><h3>Add Account</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
      <div class="k-modal-body">
        <input class="k-input" id="loginUser" placeholder="Username" autocomplete="off">
        <input class="k-input" type="password" id="loginPass" placeholder="Password">
        <div id="loginExtra" style="display:none">
          <input class="k-input" id="loginEmail" placeholder="Email" autocomplete="off">
        </div>
        <p style="font-size:12px;color:var(--text-muted);margin-top:-4px">
          <span id="loginToggleText">Don't have an account?</span>
          <a href="#" onclick="K.auth.toggleLoginMode();return false" id="loginToggleLink" style="color:var(--accent-blue)">Register</a>
        </p>
      </div>
      <div class="k-modal-footer">
        <button class="k-btn k-btn-secondary" onclick="K.modals.close()">Cancel</button>
        <button class="k-btn k-btn-primary" id="loginBtn" onclick="K.auth.doAddAccount()">Login</button>
      </div>`;
    K.auth._loginMode = 'login';
    setTimeout(() => $('loginUser')?.focus(), 100);
  },
  toggleLoginMode() {
    const extra = $('loginExtra'); const btn = $('loginBtn');
    const tl = $('loginToggleLink'); const tt = $('loginToggleText');
    if (K.auth._loginMode === 'login') {
      K.auth._loginMode = 'register';
      if (extra) extra.style.display = 'block';
      if (btn) btn.textContent = 'Register';
      if (tl) tl.textContent = 'Login';
      if (tt) tt.textContent = 'Already have an account? ';
    } else {
      K.auth._loginMode = 'login';
      if (extra) extra.style.display = 'none';
      if (btn) btn.textContent = 'Login';
      if (tl) tl.textContent = 'Register';
      if (tt) tt.textContent = "Don't have an account? ";
    }
  },
  async doAddAccount() {
    const btn = $('loginBtn'); if (btn) btn.disabled = true;
    const user = $('loginUser')?.value?.trim();
    const pass = $('loginPass')?.value;
    if (!user || !pass) { K.ui.toast('Enter username and password', 'error'); if (btn) btn.disabled = false; return; }
    try {
      let r;
      if (K.auth._loginMode === 'register') {
        const email = $('loginEmail')?.value?.trim();
        if (!email) { K.ui.toast('Enter your email', 'error'); if (btn) btn.disabled = false; return; }
        r = await K.auth.register(user, email, pass);
      } else {
        r = await K.auth.login(user, pass);
      }
      if (r.success) { K.modals.close(); K.ui.toast('Account added', 'success'); setTimeout(() => location.reload(), 500); }
      else { K.ui.toast(r.error || 'Failed', 'error'); }
    } catch(e) { K.ui.toast('Connection error', 'error'); }
    if (btn) btn.disabled = false;
  },
  _save() {
    localStorage.setItem('k_accounts', JSON.stringify(this.accounts));
    localStorage.setItem('k_active_idx', String(this.activeIdx));
  }
};
