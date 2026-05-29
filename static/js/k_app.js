(function(){
'use strict';

const $ = (id) => document.getElementById(id);
const esc = (s) => { if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; };
const fmtTime = (ts) => { if (!ts) return ''; try { const d = new Date(ts), n = new Date(); const diff = n - d; if (diff < 6e4) return 'now'; if (diff < 36e5) return Math.floor(diff/6e4)+'m'; if (diff < 864e5) return Math.floor(diff/36e5)+'h'; return d.toLocaleDateString(); } catch(e) { return ''; } };
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

const V2 = '/api.v2/api';

const K = {
  state: {
    user: null, chats: [], contacts: [], stories: [],
    activeChat: null, replyTo: null, online: navigator.onLine,
    blockedUsers: [],
    pinned: JSON.parse(localStorage.getItem('k_pinned')||'[]'),
    folders: JSON.parse(localStorage.getItem('k_folders')||'[]'),
    activeFolder: null,
    saveURL() {
      const p = new URLSearchParams(window.location.search);
      if (K.state.activeChat) p.set('chat', K.state.activeChat.type+':'+K.state.activeChat.id);
      else p.delete('chat');
      const stab = document.querySelector('.k-stab.active');
      if (stab) p.set('settings', stab.dataset.tab);
      else p.delete('settings');
      const n = window.location.pathname + '?' + p.toString();
      if (n !== window.location.href.replace(window.location.origin,'')) history.replaceState(null, '', n);
    },
    restoreURL() {
      const p = new URLSearchParams(window.location.search);
      const chat = p.get('chat');
      if (chat) {
        const [type, id] = chat.split(':');
        if (type && id) { K.state._pendingChat = {type, id: parseInt(id)}; }
      }
      const stab = p.get('settings');
      if (stab) K.state._pendingSettings = stab;
    }
  }
};

K.api = {
  _headers(extra) {
    const h = {...extra};
    const acc = K.auth.accounts[K.auth.activeIdx];
    if (acc && acc.token) h['Authorization'] = 'Bearer ' + acc.token;
    return h;
  },
  async _fetch(url, opts) {
    const r = await fetch(url, opts);
    if (r.ok) return r.json();
    let body;
    try { body = await r.json(); } catch(e) { body = {}; }
    const err = new Error(body?.error?.message || `HTTP ${r.status}`);
    err.status = r.status;
    err.body = body;
    throw err;
  },
  async get(url) { return this._fetch(url, {headers: this._headers()}); },
  async post(url, body) {
    const isForm = body instanceof FormData;
    const h = this._headers(isForm ? {} : {'Content-Type':'application/json'});
    return this._fetch(url, { method: 'POST', headers: h, body: isForm ? body : JSON.stringify(body) });
  },
  async put(url, body) { return this._fetch(url, { method: 'PUT', headers: this._headers({'Content-Type':'application/json'}), body: JSON.stringify(body) }); },
  async del(url) { return this._fetch(url, {method: 'DELETE', headers: this._headers()}); }
};

K.ui = {
  toast(msg, type='info') {
    const t = $('toast'); if (!t) return;
    t.textContent = msg; t.className = 'k-toast show';
    clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('show'), 2500);
  },
  confirm(msg) { return new Promise(resolve => {
    const o = $('modalOverlay'); o.style.display = 'flex';
    $('modalContent').innerHTML = `
      <div class="k-modal-header"><h3>Confirm</h3></div>
      <div class="k-modal-body"><p>${esc(msg)}</p></div>
      <div class="k-modal-footer">
        <button class="k-btn k-btn-secondary" onclick="K.modals.close();K.ui._confirmRes(false)">Cancel</button>
        <button class="k-btn k-btn-danger" onclick="K.modals.close();K.ui._confirmRes(true)">Confirm</button>
      </div>`;
    K.ui._confirmRes = resolve;
  })},
  prompt(msg, defaultValue='') { return new Promise(resolve => {
    const o = $('modalOverlay'); o.style.display = 'flex';
    const mid = 'uiPrompt_' + Date.now();
    $('modalContent').innerHTML = `
      <div class="k-modal-header"><h3>${esc(msg)}</h3><button class="k-modal-close" onclick="K.modals.close();K.ui._promptRes()"><i class="fas fa-times"></i></button></div>
      <div class="k-modal-body">
        <input class="k-input" id="${mid}" value="${esc(defaultValue)}" placeholder="${esc(msg)}" autocomplete="off">
      </div>
      <div class="k-modal-footer">
        <button class="k-btn k-btn-secondary" onclick="K.modals.close();K.ui._promptRes()">Cancel</button>
        <button class="k-btn k-btn-primary" onclick="K.ui._promptRes(document.getElementById('${mid}')?.value||'')">OK</button>
      </div>`;
    setTimeout(() => document.getElementById(mid)?.focus(), 100);
    K.ui._promptRes = resolve;
  })},
  loader() { return '<div class="k-loader"></div>'; },
  avatar(name='?', url='') {
    const l = (name||'?')[0].toUpperCase();
    if (url) return `<img src="${url}" alt="" style="width:100%;height:100%;object-fit:cover">`;
    return `<span style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;border-radius:50%;color:white;font-weight:600;background:linear-gradient(135deg,var(--accent-blue),var(--accent-green))">${l}</span>`;
  },
  renderUser() {
    const u = K.state.user; if (!u) return;
    const av = $('sidebarAvatar'); if (av) av.innerHTML = K.ui.avatar(u.username, u.avatar_url);
    const nm = $('sidebarName'); if (nm) nm.textContent = u.display_name || u.username;
    const se = u.status_emoji || '';
    if (nm && se) nm.textContent = se + ' ' + nm.textContent;
    const un = $('sidebarUsername'); if (un) un.textContent = '@' + u.username;
  }
};

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

K.views = {
  show(name) {
    if (window.innerWidth <= 768) { const _sb = $('sidebar'), _mb = $('menuBtn'), _bd = $('sidebarBackdrop'); _sb?.classList.remove('open'); _mb?.classList.remove('active'); _bd?.classList.remove('open'); }
    document.querySelectorAll('.k-panel').forEach(p => p.classList.remove('active'));
    const p = $('panel-'+name); if (p) p.classList.add('active');
    document.querySelectorAll('.k-nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === name));
    K.chat.close();
    if (name === 'chats') { K.chat.loadList(); }
    if (name === 'saved') K.saved.load();
    if (name === 'stories') K.stories.load();
    if (name === 'contacts') K.contacts.load();
    if (name === 'calls') K.calls.load();
    if (name === 'music') K.music.load();
    if (name === 'settings') { K.settings.loadPrivacy(); K.settings.loadSessions(); }
    K.state.saveURL();
  }
};

K.chat = {
  async loadList() {
    const c = $('chatList'); if (!c) return;
    c.innerHTML = K.ui.loader();
    try {
      const d = await K.api.get(V2 + '/chat_list');
      if (d.success) K.chat.renderList(d.data.chats);
      else c.innerHTML = '<div class="k-empty"><p>Failed to load</p></div>';
    } catch(e) { c.innerHTML = '<div class="k-empty"><i class="fas fa-wifi-slash"></i><h3>Connection error</h3><p onclick="K.chat.loadList()" style="color:var(--accent-blue);cursor:pointer">Tap to retry</p></div>'; }
  },
  renderList(chats) {
    const c = $('chatList'); if (!c) return;
    K.state.chats = chats;
    if (!chats || !chats.length) {
      c.innerHTML = `<div class="k-empty"><i class="fas fa-comment"></i><h3>No chats yet</h3><p>Search users to start chatting</p><button class="k-btn k-btn-primary" style="margin-top:16px" onclick="K.chat.startNew()"><i class="fas fa-plus"></i> New Chat</button></div>`;
      return;
    }
    const af = K.state.activeFolder;
    let filtered = chats;
    if (af) {
      const f = K.state.folders.find(x => x.name === af);
      if (f?.chats?.length) {
        const ids = new Set(f.chats.map(x => x.type+':'+x.id));
        filtered = chats.filter(chat => {
          const cid = chat.chat_type === 'personal' ? (chat.peer?.user_id || chat.peer?.id) : (chat.group?.group_id || chat.channel?.channel_id);
          return ids.has(chat.chat_type+':'+cid);
        });
      }
    }
    const pinned = K.state.pinned || [];
    const sorted = [...filtered].sort((a,b) => {
      const aId = a.chat_type === 'personal' ? (a.peer?.user_id || a.peer?.id) : (a.group?.group_id || a.channel?.channel_id);
      const bId = b.chat_type === 'personal' ? (b.peer?.user_id || b.peer?.id) : (b.group?.group_id || b.channel?.channel_id);
      const aP = pinned.includes(a.chat_type+':'+aId);
      const bP = pinned.includes(b.chat_type+':'+bId);
      if (aP && !bP) return -1;
      if (!aP && bP) return 1;
      return 0;
    });
    c.innerHTML = sorted.map(chat => {
      if (chat.chat_type === 'saved' || chat.chat_type === 'saved_messages') return '';
      const id = chat.chat_type === 'personal' ? (chat.peer?.user_id || chat.peer?.id) : (chat.group?.group_id || chat.channel?.channel_id);
      const name = chat.peer?.display_name || chat.peer?.username || chat.group?.name || chat.channel?.name || 'Unknown';
      const statusEmoji = chat.peer?.status_emoji || '';
      const avatar = chat.peer?.avatar_url || chat.group?.avatar_url || chat.channel?.avatar_url;
      const type = chat.chat_type;
      const isActive = K.state.activeChat?.type === type && K.state.activeChat?.id === id;
      const isPinned = K.state.pinned?.includes(type+':'+id);
      let preview = '';
      if (chat.last_message) {
        const lm = chat.last_message;
        if (lm.file_type === 'image' || lm.file_name?.match(/\.(jpg|jpeg|png|gif|webp)/i)) preview = '<i class="fas fa-camera"></i> Photo';
        else if (lm.file_type === 'video') preview = '<i class="fas fa-video"></i> Video';
        else if (lm.file_type === 'voice' || lm.file_type === 'audio') preview = '<i class="fas fa-microphone"></i> Voice';
        else preview = esc((lm.content||'').substring(0,80));
      }
      const time = chat.last_message?.timestamp ? fmtTime(chat.last_message.timestamp) : '';
      const unread = chat.unread_count || 0;
      const isOnline = type === 'personal' && chat.peer?.is_online;
      return `<div class="k-chat-item ${isActive?'active':''} ${isPinned?'pinned':''}" onclick="K.chat.open('${type}',${id})" data-type="${type}" data-id="${id}">
        <div class="k-chat-avatar ${type}">${K.ui.avatar(name, avatar)}${isOnline ? '<span class="k-online-dot"></span>' : ''}</div>
        <div class="k-chat-info">
          <div class="k-chat-name-row"><span class="k-chat-name">${statusEmoji ? esc(statusEmoji+' ') : ''}${esc(name)}${isPinned ? ' <i class="fas fa-thumbtack" style="font-size:10px;color:var(--accent-blue);transform:rotate(45deg);margin-left:2px"></i>' : ''}</span><span class="k-chat-time">${time}</span></div>
          <div class="k-chat-preview"><span>${preview}</span>${unread ? `<span class="k-unread">${unread>99?'99+':unread}</span>` : ''}</div>
        </div>
      </div>`;
    }).join('');
  },
  startNew() {
    K.modals.show('newChat');
    setTimeout(() => $('newChatSearch')?.focus(), 100);
  },
  async open(type, id) {
    K.state.activeChat = { type, id };
    K.state.saveURL();
    K.chat.reply.cancel();
    const _sb = $('sidebar'), _mb = $('menuBtn'), _bd = $('sidebarBackdrop'); _sb?.classList.remove('open'); _mb?.classList.remove('active'); _bd?.classList.remove('open');
    document.querySelectorAll('.k-chat-item').forEach(i => i.classList.remove('active'));
    const sel = document.querySelector(`.k-chat-item[data-type="${type}"][data-id="${id}"]`);
    if (sel) sel.classList.add('active');
    $('chatView').classList.add('active');
    document.querySelectorAll('.k-panel').forEach(p => p.classList.remove('active'));
    if (window.innerWidth > 768) { const cp = $('panel-chats'); if (cp) cp.classList.add('active'); }
    $('chatMenu').style.display = 'none';
    $('chatInfo').style.display = 'none';
    await K.chat.loadHeader(type, id);
    await K.chat.loadMessages(type, id);
    $('messageInput').focus();
    if (type === 'personal') { try { await K.api.post(V2 + `/mark_read/${id}`); K.chat.loadList(); } catch(e) {} }
  },
  close() {
    K.state.activeChat = null;
    $('chatView').classList.remove('active');
  },
  async loadHeader(type, id) {
    const nameEl = $('chatName'), statusEl = $('chatStatus'), avatarEl = $('chatAvatar');
    const chat = K.state.chats?.find(c => {
      if (type === 'personal') return (c.peer?.user_id || c.peer?.id) === id;
      if (type === 'group') return c.group?.group_id === id;
      if (type === 'channel') return c.channel?.channel_id === id;
    });
    const cb = $('callBtn');
    if (cb) cb.style.display = (type === 'personal') ? 'flex' : 'none';
    if (chat) {
      const peer = chat.peer || chat.group || chat.channel;
      if (peer) {
        const pname = peer.display_name || peer.name || peer.username || 'User #'+id;
        const emoji = peer.status_emoji || '';
        if (nameEl) nameEl.textContent = emoji ? emoji + ' ' + pname : pname;
        if (avatarEl) { avatarEl.innerHTML = K.ui.avatar(pname, peer.avatar_url); avatarEl.className = 'k-chat-avatar-sm'+(type==='group'?' group':type==='channel'?' channel':''); }
        if (statusEl) { statusEl.textContent = peer.is_online ? 'online' : ''; statusEl.className = 'k-chat-header-status'+(peer.is_online?' online':''); }
        return;
      }
    }
    try {
      if (type === 'personal') {
        const d = await K.api.get(V2 + '/users?search=' + encodeURIComponent('user' + id));
        if (d.success) {
          const users = d.data?.users || [];
          const u = users.find(x => x.user_id === id);
          if (u) {
            const emoji = u.status_emoji || '';
            if (nameEl) nameEl.textContent = emoji ? emoji + ' ' + (u.display_name || u.username) : (u.display_name || u.username);
            if (avatarEl) { avatarEl.className = 'k-chat-avatar-sm'; avatarEl.innerHTML = K.ui.avatar(u.display_name||u.username, u.avatar_url); }
            if (statusEl) { statusEl.textContent = u.is_online ? 'online' : ''; statusEl.className = 'k-chat-header-status'+(u.is_online?' online':''); }
          }
          const cb = $('callBtn'); if (cb) cb.style.display = 'flex';
        }
        if (nameEl && !nameEl.textContent) nameEl.textContent = 'User #'+id;
      } else if (type === 'group') {
        const d = await K.api.get(V2 + `/groups/${id}`);
        if (d.success && d.data) {
          const g = d.data;
          if (nameEl) nameEl.textContent = g.name;
          if (avatarEl) { avatarEl.className = 'k-chat-avatar-sm group'; avatarEl.innerHTML = K.ui.avatar(g.name, g.avatar_url); }
          if (statusEl) { statusEl.textContent = (g.member_count||0)+' members'; statusEl.className = 'k-chat-header-status'; }
        }
      } else if (type === 'channel') {
        const d = await K.api.get(V2 + `/channels/${id}`);
        if (d.success && d.data) {
          const ch = d.data;
          if (nameEl) nameEl.textContent = ch.name;
          if (avatarEl) { avatarEl.className = 'k-chat-avatar-sm channel'; avatarEl.innerHTML = K.ui.avatar(ch.name, ch.avatar_url); }
          if (statusEl) { statusEl.textContent = (ch.subscriber_count||0)+' subscribers'; statusEl.className = 'k-chat-header-status'; }
        }
      }
    } catch(e) {}
  },
  async loadMessages(type, id, append=false) {
    const mc = $('messagesContainer'); if (!mc) return;
    const after = append ? (K.chat._cursor || 0) : 0;
    if (!append) { K.chat._cursor = 0; K.chat._hasMore = true; mc.innerHTML = K.ui.loader(); }
    if (!K.chat._hasMore && append) return;
    try {
      let url;
      if (type === 'personal') url = V2 + `/messages/${id}`;
      else if (type === 'group') url = V2 + `/group_messages/${id}`;
      else if (type === 'channel') url = V2 + `/channel_messages/${id}`;
      const d = await K.api.get(url + `?after=${after}&limit=50`);
      const msgs = (d.data && d.data.messages) || d.messages || [];
      const pag = d.data?.pagination;
      K.chat._hasMore = pag?.has_more ?? false;
      if (pag?.next_cursor) K.chat._cursor = pag.next_cursor;
      if (append) {
        if (!msgs.length) { K.chat._hasMore = false; return; }
        const prevScroll = mc.scrollHeight;
        mc.insertAdjacentHTML('afterbegin', msgs.map(m => K.chat.renderMessage(m)).join(''));
        mc.scrollTop = mc.scrollHeight - prevScroll;
      } else {
        K.chat.renderMessages(msgs);
        if (K.chat._hasMore) mc.insertAdjacentHTML('afterend', '<div id="loadMoreTrigger" style="text-align:center;padding:8px"><button class="k-btn k-btn-secondary" onclick="K.chat.loadMore()">Load older messages</button></div>');
      }
    } catch(e) { if (!append) mc.innerHTML = '<div class="k-empty"><i class="fas fa-exclamation-triangle"></i><h3>Error</h3><p onclick="K.chat.loadMessages(type,id)" style="color:var(--accent-blue);cursor:pointer">Tap to retry</p></div>'; }
  },
  async loadMore() {
    if (!K.state.activeChat) return;
    const lm = $('loadMoreTrigger'); if (lm) lm.remove();
    await K.chat.loadMessages(K.state.activeChat.type, K.state.activeChat.id, true);
  },
  renderMessages(msgs) {
    const mc = $('messagesContainer'); if (!mc) return;
    let html = '', lastDate = '', lastSender = null, lastTime = null;
    const uid = K.state.user?.user_id;
    for (const m of msgs) {
      const d = new Date(m.timestamp || Date.now());
      const ds = d.toLocaleDateString();
      if (ds !== lastDate) {
        lastDate = ds; lastSender = null; lastTime = null;
        const today = new Date(); const y = new Date(today); y.setDate(y.getDate()-1);
        let label = d.toLocaleDateString(undefined, {month:'long', day:'numeric'});
        if (ds === today.toLocaleDateString()) label = 'Today';
        else if (ds === y.toLocaleDateString()) label = 'Yesterday';
        html += `<div class="k-date-divider"><span>${label}</span></div>`;
      }
      const isOwn = m.sender_id === uid || m.is_own;
      const consecutive = m.sender_id === lastSender && lastTime && (new Date(m.timestamp) - new Date(lastTime)) < 300000;
      html += K.chat._messageHtml(m, isOwn, consecutive);
      lastSender = m.sender_id; lastTime = m.timestamp;
    }
    mc.innerHTML = html || `<div class="k-empty" style="padding:40px 20px"><i class="fas fa-comments"></i><h3>No messages yet</h3><p>Say hello!</p></div>`;
    K.chat._scrollToBottom();
  },
  _messageHtml(m, isOwn, consecutive) {
    const time = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}) : '';
    const mid = m.message_id || m.id;
    const isRead = m.is_read === true || m.is_read === 1;
    const statusIcon = !isOwn ? '' : (isRead ? '<i class="fas fa-check-double" style="font-size:10px;color:var(--accent-blue)"></i>' : '<i class="fas fa-check" style="font-size:10px"></i>');
    let att = '';
    const fileUrl = m.file_url || m.file_path || '';
    const fileName = m.file_name || '';
    const fileType = m.file_type || '';
    if (m.file_path || m.file_type || m.file_name) {
      const isImg = fileType === 'image' || fileName.match(/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i);
      const isVid = fileType === 'video' || fileName.match(/\.(mp4|webm|avi|mov|mkv)$/i);
      const isAud = fileType === 'audio' || fileType === 'voice' || fileName.match(/\.(mp3|wav|m4a|ogg)$/i);
      if (isImg && fileUrl) {
        att = `<div class="k-msg-attachment"><img src="${fileUrl}" loading="lazy" onclick="K.chat.lightbox('${esc(fileUrl)}')"></div>`;
      } else if (isVid && fileUrl) {
        att = `<div class="k-msg-attachment"><video src="${fileUrl}" controls preload="metadata" style="max-width:260px;max-height:200px;border-radius:12px"></video></div>`;
      } else if (isAud && fileUrl) {
        att = `<div class="k-msg-attachment"><audio src="${fileUrl}" controls style="max-width:220px;height:36px;border-radius:8px"></audio><button class="k-icon-btn" onclick="event.stopPropagation();K.music.likeMusic(${m.message_id||m.id})" title="Add to My Music" style="font-size:14px;width:28px;height:28px;display:inline-flex;vertical-align:middle"><i class="fas fa-heart"></i></button></div>`;
      } else if (fileUrl) {
        const icon = fileName.match(/\.pdf$/i) ? 'fa-file-pdf' : fileName.match(/\.(doc|docx)$/i) ? 'fa-file-word' : 'fa-file';
        att = `<div class="k-msg-file"><i class="fas ${icon}"></i> <a href="${fileUrl}" target="_blank" rel="noopener">${esc(fileName||'File')}</a></div>`;
      }
    }
    let reply = '';
    if (m.reply_to_id) reply = `<div class="k-msg-reply"><div style="font-weight:600;font-size:11px">↩ Reply</div>${esc(m.reply_to_content||'')}</div>`;
    const sName = (!isOwn && !consecutive && (m.sender_username||m.sender_name)) ? `<div class="k-msg-sender">${esc(m.sender_username||m.sender_name)}</div>` : '';
    let reactions = '';
    if (m.reactions && typeof m.reactions === 'object') {
      const entries = Object.entries(m.reactions);
      if (entries.length) {
        reactions = `<div class="k-msg-reactions">${entries.map(([t,c]) => `<span class="k-reaction-badge" onclick="event.stopPropagation();K.chat.react(${mid},'${t}')">${t} ${c}</span>`).join('')}</div>`;
      }
    }
    const cls = isOwn ? 'outgoing' : 'incoming';
    const content = m.content ? `<div class="k-msg-text">${esc(m.content).replace(/\n/g,'<br>')}</div>` : '';
    return `<div class="k-msg ${cls}" data-msg-id="${mid}">
      ${sName}${reply}${att}${content ? `<div class="k-msg-bubble">${content}<div class="k-msg-meta">${time} ${statusIcon}</div></div>` : (att ? `<div class="k-msg-bubble"><div class="k-msg-meta">${time} ${statusIcon}</div></div>` : '')}${reactions}
      <div class="k-msg-actions">
        <button class="k-msg-action-btn" onclick="K.chat.reply.set(${mid},'${esc((m.content||'').substring(0,40))}')" title="Reply"><i class="fas fa-reply"></i></button>
        <button class="k-msg-action-btn" onclick="K.chat.react(${mid})" title="React"><i class="fas fa-smile"></i></button>
        <button class="k-msg-action-btn" onclick="K.chat.copy(${mid})" title="Copy"><i class="fas fa-copy"></i></button>
        ${isOwn ? `<button class="k-msg-action-btn" onclick="K.chat.edit(${mid})" title="Edit"><i class="fas fa-pen"></i></button>
        <button class="k-msg-action-btn" onclick="K.chat.delete(${mid})" title="Delete" style="color:var(--accent-red)"><i class="fas fa-trash"></i></button>` : ''}
      </div>
    </div>`;
  },
  renderMessage(m) { return K.chat._messageHtml(m, m.sender_id === K.state.user?.user_id || m.is_own, false); },
  _scrollToBottom() { const mc = $('messagesContainer'); if (mc) { mc.scrollTop = mc.scrollHeight; } },
  async send() {
    const input = $('messageInput'); if (!input) return;
    const content = input.value.trim();
    if (!content || !K.state.activeChat) return;
    const { type, id } = K.state.activeChat;
    let payload = { content }, url;
    if (type === 'personal') { url = V2 + '/send_message'; payload.receiver_id = id; }
    else if (type === 'group') { url = V2 + '/send_group_message'; payload.group_id = id; }
    else if (type === 'channel') { url = V2 + '/send_channel_message'; payload.channel_id = id; }
    if (K.state.replyTo) { payload.reply_to_id = K.state.replyTo; K.chat.reply.cancel(); }
    input.value = ''; input.style.height = 'auto'; K.chat.input.handle();
    const tmpId = 'tmp_'+Date.now();
    const optMsg = { message_id: tmpId, content, sender_id: K.state.user?.user_id, sender_username: K.state.user?.display_name, timestamp: new Date().toISOString(), is_own: true };
    const mc = $('messagesContainer');
    if (mc) {
      const empty = mc.querySelector('.k-empty');
      if (empty) mc.innerHTML = '';
      mc.insertAdjacentHTML('beforeend', K.chat._messageHtml(optMsg, true, false));
      K.chat._scrollToBottom();
    }
    try {
      const d = await K.api.post(url, payload);
      if (d.success) { K.chat.loadMessages(type, id); K.chat.loadList(); }
      else { K.ui.toast('Send failed', 'error'); }
    } catch(e) { K.ui.toast('Message not sent', 'error'); }
  },
  input: {
    _typingTimer: null,
    handle() {
      const input = $('messageInput'), btn = $('sendBtn');
      if (input) { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 100) + 'px'; }
      if (btn) btn.disabled = !(input?.value.trim());
      clearTimeout(K.chat.input._typingTimer);
      K.chat.input._typingTimer = setTimeout(() => K.chat._sendTyping(), 500);
    },
    keydown(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); K.chat.send(); } }
  },
  _typingSent: false,
  async _sendTyping() {
    if (!K.state.activeChat || K.chat._typingSent) return;
    K.chat._typingSent = true;
    const { type, id } = K.state.activeChat;
    try { await K.api.post(V2 + `/typing/${type}/${id}`); } catch(e) {}
    setTimeout(() => { K.chat._typingSent = false; }, 4000);
  },
  reply: {
    set(msgId, text) {
      K.state.replyTo = msgId;
      const bar = $('replyBar'); if (!bar) return;
      $('replyName').textContent = 'Replying';
      $('replyText').textContent = text || '';
      bar.style.display = 'flex'; $('messageInput')?.focus();
    },
    cancel() { K.state.replyTo = null; const bar = $('replyBar'); if (bar) bar.style.display = 'none'; }
  },
  async copy(msgId) {
    const el = document.querySelector(`[data-msg-id="${msgId}"] .k-msg-text`);
    const text = el?.textContent || '';
    try { await navigator.clipboard.writeText(text); K.ui.toast('Copied', 'success'); } catch(e) { K.ui.toast('Copy failed', 'error'); }
  },
  async react(msgId, emoji) {
    if (!msgId) return;
    const emojis = ['❤️','😂','👍','🔥','😮','😢','🙏'];
    if (emoji) {
      try {
        const d = await K.api.post(V2 + '/reactions/add', { message_id: msgId, reaction_type: emoji });
        if (d.success) K.chat.loadMessages(K.state.activeChat.type, K.state.activeChat.id);
        else K.ui.toast('React failed', 'error');
      } catch(e) {}
      return;
    }
    const picker = document.querySelector('.k-reaction-picker');
    if (picker) { picker.remove(); return; }
    const overlay = document.createElement('div');
    overlay.className = 'k-reaction-picker';
    overlay.innerHTML = emojis.map(e => `<span onclick="K.chat._pickReaction(${msgId},'${e}')">${e}</span>`).join('');
    overlay.onclick = (ev) => { if (ev.target === overlay) overlay.remove(); };
    const msgEl = document.querySelector(`[data-msg-id="${msgId}"]`);
    if (msgEl) { msgEl.style.position = 'relative'; msgEl.appendChild(overlay); setTimeout(() => overlay.classList.add('active'), 10); }
    else overlay.remove();
  },
  _pickReaction(msgId, emoji) {
    document.querySelector('.k-reaction-picker')?.remove();
    K.chat.react(msgId, emoji);
  },
    async uploadFiles(input) {
    if (!input?.files?.length || !K.state.activeChat) return;
    const { type, id } = K.state.activeChat;
    const fd = new FormData();
    const msgText = $('messageInput')?.value?.trim();
    for (const f of input.files) fd.append('file', f);
    if (msgText) fd.append('message_text', msgText);
    if (type === 'personal') fd.append('receiver_id', id);
    else if (type === 'group') fd.append('group_id', id);
    else if (type === 'channel') fd.append('channel_id', id);
    try {
      const d = await K.api.post('/files/upload_file', fd);
      if (d.success) { $('messageInput').value = ''; K.chat.loadMessages(type, id); K.ui.toast('File sent', 'success'); }
      else K.ui.toast('Upload failed', 'error');
    } catch(e) { K.ui.toast('Upload error', 'error'); }
    input.value = '';
  },
  async delete(msgId) {
    if (!msgId || !await K.ui.confirm('Delete this message?')) return;
    try {
      const d = await K.api.post(V2 + `/messages/${msgId}/delete`);
      if (d.success) {
        const el = document.querySelector(`[data-msg-id="${msgId}"]`);
        if (el) el.style.opacity = '0.3';
        K.ui.toast('Deleted', 'success');
      } else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Delete failed', 'error'); }
  },
  async edit(msgId) {
    const el = document.querySelector(`[data-msg-id="${msgId}"] .k-msg-text`);
    const oldText = el?.textContent || '';
    const text = await K.ui.prompt('Edit message:', oldText);
    if (!text || text === oldText) return;
    try {
      const d = await K.api.post(V2 + `/messages/${msgId}/edit`, { content: text });
      if (d.success) {
        K.ui.toast('Edited', 'success');
        K.chat.loadMessages(K.state.activeChat.type, K.state.activeChat.id);
      } else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Edit failed', 'error'); }
  },
  lightbox(url) {
    const o = document.createElement('div');
    o.className = 'k-modal-overlay';
    o.style.cssText = 'background:rgba(0,0,0,0.95);cursor:pointer';
    o.onclick = () => o.remove();
    const img = document.createElement('img');
    img.src = url; img.style.cssText = 'max-width:90%;max-height:90%;border-radius:8px;object-fit:contain';
    o.appendChild(img); document.body.appendChild(o);
  },
  async startCall() {
    if (!K.state.activeChat || K.state.activeChat.type !== 'personal') return;
    const peerId = K.state.activeChat.id;
    try {
      const d = await K.api.post(V2 + '/video/create-room', {user_id: peerId});
      if (d.success && d.data?.room_id) {
        const url = 'http://localhost:5001/video/join/' + d.data.room_id;
        K.calls.start(url, peerId);
      } else K.ui.toast('Failed to create call', 'error');
    } catch(e) { K.ui.toast('Call failed', 'error'); }
  },
  menu: {
    toggle() {
      const menu = $('chatMenu'), info = $('chatInfo');
      info.style.display = 'none';
      if (!K.state.activeChat) return;
      const { type, id } = K.state.activeChat;
      if (menu.style.display === 'block') { menu.style.display = 'none'; return; }
      menu.style.display = 'block';
      const key = type+':'+id;
      const isPinned = K.state.pinned?.includes(key);
      let items = '';
      items += `<div class="k-chat-menu-item" onclick="K.chat.menu.togglePin('${key}')"><i class="fas fa-thumbtack"></i> ${isPinned ? 'Unpin' : 'Pin'}</div>`;
      if (type === 'personal') {
        items += `<div class="k-chat-menu-item" onclick="K.chat.menu.block(${id})"><i class="fas fa-ban"></i> Block User</div>`;
        items += `<div class="k-chat-menu-item" onclick="K.chat.menu.clear(${id})"><i class="fas fa-trash"></i> Clear Chat</div>`;
      } else if (type === 'group') {
        items += `<div class="k-chat-menu-item" onclick="K.chat.info.toggle()"><i class="fas fa-users"></i> View Members</div>`;
        items += `<div class="k-chat-menu-item danger" onclick="K.chat.menu.leaveGroup(${id})"><i class="fas fa-sign-out-alt"></i> Leave Group</div>`;
      } else if (type === 'channel') {
        items += `<div class="k-chat-menu-item" onclick="K.chat.info.toggle()"><i class="fas fa-info-circle"></i> Channel Info</div>`;
        items += `<div class="k-chat-menu-item" onclick="K.chat.menu.unsubscribe(${id})"><i class="fas fa-bell-slash"></i> Unsubscribe</div>`;
      }
      if (K.state.folders?.length) {
        items += `<div style="border-top:1px solid var(--border-color);margin:6px 0;padding-top:6px;font-size:11px;color:var(--text-muted);padding:6px 12px 0">Folders</div>`;
        items += K.state.folders.map(f => {
          const inF = f.chats?.some(x => x.type === type && x.id === id);
          return `<div class="k-chat-menu-item" onclick="K.chat.menu.toggleFolder('${esc(f.name)}','${type}',${id})"><i class="fas fa-folder${inF?'-open':''}"></i> ${inF ? 'Remove from' : 'Add to'} ${esc(f.name)}</div>`;
        }).join('');
      }
      menu.innerHTML = items || '<div style="padding:16px;color:var(--text-muted)">No actions</div>';
    },
    togglePin(key) {
      let p = K.state.pinned || [];
      const idx = p.indexOf(key);
      if (idx >= 0) p.splice(idx, 1);
      else p.push(key);
      K.state.pinned = p;
      localStorage.setItem('k_pinned', JSON.stringify(p));
      K.settings.saveToServer();
      K.chat.loadList();
      K.chat.menu.toggle();
    },
    toggleFolder(fname, type, id) {
      const f = K.state.folders.find(x => x.name === fname);
      if (!f) return;
      if (!f.chats) f.chats = [];
      const idx = f.chats.findIndex(x => x.type === type && x.id === id);
      if (idx >= 0) f.chats.splice(idx, 1);
      else f.chats.push({type, id});
      K.state.folders = K.state.folders.map(x => x.name === fname ? f : x);
      localStorage.setItem('k_folders', JSON.stringify(K.state.folders));
      K.settings.saveToServer();
      K.chat.loadList();
      K.chat.menu.toggle();
    },
    async block(id) { if (await K.ui.confirm('Block this user?')) { try { const d = await K.api.post(V2 + `/block_user/${id}`); if (d.success) { K.ui.toast('Blocked', 'success'); K.chat.close(); K.chat.loadList(); } } catch(e) { K.ui.toast('Failed', 'error'); } } },
    async leaveGroup(id) { if (await K.ui.confirm('Leave this group?')) { try { const d = await K.api.post(V2 + `/leave_group/${id}`); if (d.success) { K.ui.toast('Left group', 'success'); K.chat.close(); K.chat.loadList(); } } catch(e) { K.ui.toast('Failed', 'error'); } } },
    async unsubscribe(id) { if (await K.ui.confirm('Unsubscribe?')) { try { const d = await K.api.post(V2 + `/channels/${id}/unsubscribe`); if (d.success) { K.ui.toast('Unsubscribed', 'success'); K.chat.close(); K.chat.loadList(); } } catch(e) { K.ui.toast('Failed', 'error'); } } },
    async clear(id) { if (await K.ui.confirm('Clear all messages?')) { try { const d = await K.api.post(V2 + '/clear_chat', {chat_id: id}); if (d.success) { K.chat.loadMessages(K.state.activeChat.type, id); K.ui.toast('Chat cleared', 'success'); } else K.ui.toast('Failed', 'error'); } catch(e) { K.ui.toast('Failed', 'error'); } } }
  },
  info: {
    async toggle() {
      const info = $('chatInfo'), menu = $('chatMenu');
      menu.style.display = 'none';
      if (!K.state.activeChat) return;
      if (info.style.display === 'block') { info.style.display = 'none'; return; }
      info.style.display = 'block'; info.innerHTML = K.ui.loader();
      const { type, id } = K.state.activeChat;
      try {
        if (type === 'group') {
          const d = await K.api.get(V2 + `/groups/${id}/members`);
          if (d.success) {
            const data = d.data;
            info.innerHTML = `<div class="k-info-title">Members (${data.pagination?.total||data.members?.length||0})</div>
              ${(data.members||[]).map(m => `<div class="k-info-row"><div class="k-info-avatar">${(m.username||'?')[0].toUpperCase()}</div><div class="k-info-data"><div class="k-info-name">${esc(m.username)}</div><div class="k-info-role">${m.role||'member'}</div></div></div>`).join('')}`;
          }
        } else if (type === 'channel') {
          const d = await K.api.get(V2 + `/channels/${id}`);
          if (d.success) {
            const ch = d.data;
            info.innerHTML = `<div class="k-info-desc"><strong>Description:</strong><br>${esc(ch.description||'No description')}</div>
              <div class="k-info-stat"><strong>Subscribers:</strong> ${ch.subscriber_count||0}</div>`;
          }
        } else { info.innerHTML = ''; }
      } catch(e) { info.innerHTML = '<div class="k-info-empty">Failed to load info</div>'; }
    }
  }
};

K.contacts = {
  async load() {
    try {
      const d = await K.api.get(V2 + '/contacts');
      if (d.success) {
        K.state.contacts = d.data?.contacts || [];
        K.contacts.render(K.state.contacts);
      }
    } catch(e) {}
  },
  render(contacts) {
    const c = $('contactsList'); if (!c) return;
    if (!contacts?.length) {
      c.innerHTML = '<div class="k-empty"><i class="fas fa-address-book"></i><h3>No contacts</h3><p>Add people to your contacts</p></div>';
      return;
    }
    c.innerHTML = contacts.map(ct =>
      `<div class="k-contact-item" onclick="K.chat.open('personal',${ct.user_id})">
        <div class="k-contact-avatar">${K.ui.avatar(ct.username, ct.avatar_url)}</div>
        <div class="k-contact-info">
          <div class="k-contact-name">${esc((ct.status_emoji||'')+' '+(ct.display_name||ct.username))}</div>
          <div class="k-contact-username">@${esc(ct.username)}${ct.is_online ? ' <span class="k-contact-status">● Online</span>' : ''}</div>
        </div>
        <button class="k-icon-btn" onclick="event.stopPropagation();K.contacts.rename(${ct.user_id})" title="Rename"><i class="fas fa-pen"></i></button>
      </div>`
    ).join('');
  },
  async add(userId) {
    try {
      const d = await K.api.post(V2 + '/contacts', {contact_id: userId});
      if (d.success) { K.ui.toast('Contact added', 'success'); K.contacts.load(); K.modals.close(); }
      else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Failed to add contact', 'error'); }
  },
  async rename(contactId) {
    const name = await K.ui.prompt('Custom name:');
    if (name && name.trim()) {
      try {
        const d = await K.api.post(V2 + '/contacts/rename', {contact_id: contactId, name: name.trim()});
        if (d.success) { K.ui.toast('Renamed', 'success'); K.contacts.load(); }
      } catch(e) { K.ui.toast('Failed', 'error'); }
    }
  },
  search(q) {
    const filtered = q ? K.state.contacts.filter(c => (c.display_name||c.username).toLowerCase().includes(q.toLowerCase())) : K.state.contacts;
    K.contacts.render(filtered);
  }
};

K.modals = {
  show(name) {
    const overlay = $('modalOverlay'), content = $('modalContent');
    if (!overlay || !content) return;
    overlay.style.display = 'flex';
    const fn = K.modals[name];
    content.innerHTML = typeof fn === 'function' ? fn() : '<div class="k-modal-body">Unknown modal</div>';
    if (name === 'createGroup') { K.modals._groupMemberIds = []; K.modals._groupMemberNames = []; }
  },
  close() { $('modalOverlay').style.display = 'none'; },
  newChat() {
    return `
      <div class="k-modal-header"><h3>New Chat</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
      <div class="k-modal-body">
        <input class="k-input" id="newChatSearch" placeholder="Search users..." oninput="K.modals._searchNewChat(this.value)" autocomplete="off">
        <div id="newChatResults"></div>
      </div>
      <div class="k-modal-footer"><button class="k-btn k-btn-secondary" onclick="K.modals.close()">Cancel</button></div>`;
  },
  _searchNewChat: debounce(async (q) => {
    const r = $('newChatResults'); if (!r) return;
    if (!q || q.length < 2) { r.innerHTML = '<div style="padding:16px;color:var(--text-muted);text-align:center">Type at least 2 characters</div>'; return; }
    r.innerHTML = K.ui.loader();
    try {
      const d = await K.api.get(V2 + `/users?search=${encodeURIComponent(q)}`);
      if (!d.success) { r.innerHTML = '<div style="padding:16px;color:var(--text-muted);text-align:center">No users found</div>'; return; }
      const users = d.data?.users || [];
      if (!users.length) { r.innerHTML = '<div style="padding:16px;color:var(--text-muted);text-align:center">No users found</div>'; return; }
      r.innerHTML = users.map(u =>
        `<div class="k-contact-item" onclick="K.chat.open('personal',${u.user_id});K.modals.close()">
          <div class="k-contact-avatar">${K.ui.avatar(u.username, u.avatar_url)}</div>
          <div class="k-contact-info"><div class="k-contact-name">${esc(u.display_name||u.username)}</div><div class="k-contact-username">@${esc(u.username)}</div></div>
        </div>`
      ).join('');
    } catch(e) { r.innerHTML = '<div style="padding:16px;color:var(--text-muted);text-align:center">Search failed</div>'; }
  }, 300),
  createGroup() {
    return `
      <div class="k-modal-header"><h3>Create Group</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
      <div class="k-modal-body">
        <input class="k-input" id="groupNameInput" placeholder="Group name">
        <input class="k-input" id="groupMemberSearch" placeholder="Search members..." oninput="K.modals._searchMembers(this.value)">
        <div id="groupSelectedMembers" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;min-height:0"></div>
        <div id="groupMemberResults" style="max-height:180px;overflow-y:auto"></div>
      </div>
      <div class="k-modal-footer">
        <button class="k-btn k-btn-secondary" onclick="K.modals.close()">Cancel</button>
        <button class="k-btn k-btn-primary" onclick="K.groups.create()">Create</button>
      </div>`;
  },
  addContact() {
    return `
      <div class="k-modal-header"><h3>Add Contact</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
      <div class="k-modal-body">
        <input class="k-input" id="addContactInput" placeholder="Search users..." oninput="K.modals._searchUsers(this.value)">
        <div id="addContactResults"></div>
      </div>
      <div class="k-modal-footer"><button class="k-btn k-btn-secondary" onclick="K.modals.close()">Cancel</button></div>`;
  },
  editProfile() {
    const u = K.state.user || {};
    return `
      <div class="k-modal-header"><h3>Edit Profile</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
      <div class="k-modal-body">
        <label style="font-size:13px;font-weight:500;margin-bottom:4px;display:block">Display Name</label>
        <input class="k-input" id="editDisplayName" value="${esc(u.display_name||'')}" placeholder="Display name">
        <label style="font-size:13px;font-weight:500;margin-bottom:4px;display:block">Bio</label>
        <textarea class="k-input" id="editBio" rows="3" placeholder="About you">${esc(u.bio||'')}</textarea>
        <label style="font-size:13px;font-weight:500;margin-bottom:4px;display:block;margin-top:8px">Status Emoji</label>
        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px" id="emojiPicker">
          ${['🌴','💼','🎮','📚','🎵','🏖️','💪','😴','❤️','🔥','🌟','🎯','💡','🎨','🏃','☕'].map(e => `<span class="k-emoji-opt${(u.status_emoji||'')===e?' active':''}" onclick="document.getElementById('statusEmoji').value=this.textContent;document.querySelectorAll('.k-emoji-opt').forEach(x=>x.classList.remove('active'));this.classList.add('active')">${e}</span>`).join('')}
        </div>
        <input class="k-input" id="statusEmoji" value="${esc(u.status_emoji||'')}" placeholder="Or type any emoji" style="margin-bottom:4px">
        <button class="k-btn k-btn-secondary" style="width:100%;margin-top:4px" onclick="document.getElementById('avatarUpload').click()"><i class="fas fa-camera"></i> Change Photo</button>
        <input type="file" id="avatarUpload" accept="image/*" style="display:none" onchange="K.profile.uploadAvatar(this)">
      </div>
      <div class="k-modal-footer">
        <button class="k-btn k-btn-secondary" onclick="K.modals.close()">Cancel</button>
        <button class="k-btn k-btn-primary" onclick="K.profile.save()">Save</button>
      </div>`;
  },
  _groupMemberIds: [],
  _groupMemberNames: [],
  _searchMembers: debounce(async (q) => {
    const r = $('groupMemberResults'); if (!r) return;
    if (!q || q.length < 1) { r.innerHTML = ''; return; }
    try {
      const d = await K.api.get(V2 + `/users?search=${encodeURIComponent(q)}`);
      if (!d.success) return;
      const users = d.data?.users || [];
      const existing = new Set(K.modals._groupMemberIds);
      r.innerHTML = users.filter(u => !existing.has(u.user_id)).map(u =>
        `<div class="k-contact-item" onclick="K.modals._addMember(${u.user_id},'${esc(u.display_name||u.username)}')">
          <div class="k-contact-avatar">${K.ui.avatar(u.username, u.avatar_url)}</div>
          <div class="k-contact-info"><div class="k-contact-name">${esc(u.display_name||u.username)}</div><div class="k-contact-username">@${esc(u.username)}</div></div>
        </div>`
      ).join('');
    } catch(e) {}
  }, 300),
  _addMember(id, name) {
    K.modals._groupMemberIds.push(id); K.modals._groupMemberNames.push(name);
    $('groupSelectedMembers').innerHTML = K.modals._groupMemberNames.map((n,i) =>
      `<span style="background:var(--accent-blue);color:white;padding:4px 8px 4px 12px;border-radius:16px;font-size:13px;display:inline-flex;align-items:center;gap:6px">${esc(n)}<button onclick="K.modals._removeMember(${i})" style="background:none;border:none;color:white;cursor:pointer;font-size:14px;padding:0;line-height:1">&times;</button></span>`
    ).join('');
    $('groupMemberResults').innerHTML = ''; $('groupMemberSearch').value = '';
  },
  _removeMember(idx) {
    K.modals._groupMemberIds.splice(idx,1); K.modals._groupMemberNames.splice(idx,1);
    const sel = $('groupSelectedMembers');
    if (sel) sel.innerHTML = K.modals._groupMemberNames.map((n,i) => `<span style="background:var(--accent-blue);color:white;padding:4px 8px 4px 12px;border-radius:16px;font-size:13px;display:inline-flex;align-items:center;gap:6px">${esc(n)}<button onclick="K.modals._removeMember(${i})" style="background:none;border:none;color:white;cursor:pointer;font-size:14px;padding:0;line-height:1">&times;</button></span>`).join('');
  },
  _searchUsers: debounce(async (q) => {
    const r = $('addContactResults'); if (!r) return;
    if (!q || q.length < 1) { r.innerHTML = ''; return; }
    try {
      const d = await K.api.get(V2 + `/users?search=${encodeURIComponent(q)}`);
      if (!d.success) return;
      const users = d.data?.users || [];
      r.innerHTML = users.map(u =>
        `<div class="k-contact-item" onclick="K.contacts.add(${u.user_id})">
          <div class="k-contact-avatar">${K.ui.avatar(u.username, u.avatar_url)}</div>
          <div class="k-contact-info"><div class="k-contact-name">${esc(u.display_name||u.username)}</div><div class="k-contact-username">@${esc(u.username)}</div></div>
        </div>`
      ).join('');
    } catch(e) {}
  }, 300)
};

K.groups = {
  async create() {
    const name = $('groupNameInput')?.value?.trim();
    if (!name) { K.ui.toast('Group name required', 'error'); return; }
    try {
      const d = await K.api.post(V2 + '/groups/create', {name, member_ids: K.modals._groupMemberIds});
      if (d.success) {
        K.ui.toast('Group created', 'success'); K.modals.close();
        K.modals._groupMemberIds = []; K.modals._groupMemberNames = [];
        K.chat.loadList();
      } else { K.ui.toast('Failed', 'error'); }
    } catch(e) { K.ui.toast('Failed to create group', 'error'); }
  }
};

K.stories = {
  async load() {
    try {
      const d = await K.api.get(V2 + '/stories');
      if (d.success) {
        K.state.stories = d.data?.stories || [];
        K.stories._renderRow();
        K.stories._renderGrid();
      }
    } catch(e) {}
  },
  _renderRow() {
    const row = $('storiesRow'); if (!row) return;
    const stories = K.state.stories;
    let html = `<div class="k-story-circle" onclick="K.stories.create()">
      <div class="k-story-ring" style="background:var(--border-color)"><div style="width:100%;height:100%;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--bg-surface);color:var(--text-muted);font-size:24px;border:2px solid var(--sidebar-bg)"><i class="fas fa-plus"></i></div></div>
      <span class="k-story-username">Add</span>
    </div>`;
    if (stories?.length) html += stories.map(s => {
      const hasUnviewed = s.has_unviewed;
      return `<div class="k-story-circle" onclick="K.stories.view(${s.user_id})">
        <div class="k-story-ring ${!hasUnviewed?'viewed':''}">
          ${s.avatar_url ? `<img src="${s.avatar_url}">` : `<div style="width:100%;height:100%;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--accent-blue),var(--accent-green));color:white;font-weight:600;font-size:20px;border:2px solid var(--sidebar-bg)">${(s.username||'?')[0].toUpperCase()}</div>`}
        </div>
        <span class="k-story-username">${esc((s.username||'').substring(0,8))}</span>
      </div>`;
    }).join('');
    row.innerHTML = html;
  },
  _renderGrid() {
    const grid = $('storiesGrid'); if (!grid) return;
    const stories = K.state.stories;
    if (!stories?.length) { grid.innerHTML = '<div class="k-empty" style="grid-column:1/-1"><i class="fas fa-camera"></i><h3>No stories</h3><p>Be the first to share</p></div>'; return; }
    grid.innerHTML = stories.map(s => {
      const first = s.stories?.[0]; if (!first) return '';
      return `<div class="k-story-card" onclick="K.stories.view(${s.user_id})">
        ${first.media_type === 'video' ? `<video src="${first.media_path}"></video>` : `<img src="${first.media_path}" loading="lazy">`}
        <div class="k-story-card-overlay"><span>${esc(s.username)}</span></div>
      </div>`;
    }).join('');
  },
  async view(userId) {
    const storyGroup = K.state.stories.find(s => s.user_id === userId);
    const stories = storyGroup?.stories; if (!stories?.length) return;
    const viewer = $('storyViewer'); viewer.style.display = 'flex'; viewer.style.flexDirection = 'column';
    let idx = 0, timer = null;
    const show = (i) => {
      if (timer) clearTimeout(timer);
      const s = stories[i]; if (!s) { K.stories.close(); return; }
      K.stories._activeStory = s;
      $('storyViewerName').textContent = storyGroup.username;
      $('storyViewerAvatar').innerHTML = K.ui.avatar(storyGroup.username);
      $('storyMedia').innerHTML = s.media_type === 'video'
        ? `<video src="${s.media_path}" autoplay controls style="max-width:100%;max-height:80vh"></video>`
        : `<img src="${s.media_path}" style="max-width:100%;max-height:80vh">`;
      $('storyLikeCount').textContent = s.like_count || 0;
      $('storyProgress').innerHTML = stories.map((_, si) =>
        `<div class="k-story-progress-seg"><div class="k-story-progress-fill" style="width:${si<i?'100%':si===i?'0%':'0%'}"></div></div>`
      ).join('');
      if (s.media_type !== 'video') {
        const fill = $('storyProgress')?.querySelectorAll('.k-story-progress-fill')[i];
        if (fill) { fill.style.transition = 'width 5s linear'; fill.style.width = '100%'; }
        timer = setTimeout(() => { if (i+1 < stories.length) show(i+1); else K.stories.close(); }, 5000);
      }
      try { K.api.post(V2 + `/stories/${s.story_id}/view`); } catch(e) {}
    };
    show(0);
    const next = () => { if (idx+1 < stories.length) { idx++; show(idx); } else K.stories.close(); };
    const prev = () => { if (idx > 0) { idx--; show(idx); } };
    viewer.onclick = (e) => { if (e.target === viewer || e.target.closest('.k-story-header') || e.target.closest('.k-story-actions')) return; const rect = viewer.getBoundingClientRect(); if (e.clientX < rect.width/3) prev(); else next(); };
    document.addEventListener('keydown', K.stories._keyHandler = (e) => { if (e.key === 'Escape') K.stories.close(); else if (e.key === 'ArrowRight') next(); else if (e.key === 'ArrowLeft') prev(); });
  },
  close() {
    $('storyViewer').style.display = 'none';
    K.stories._activeStory = null;
    if (K.stories._keyHandler) document.removeEventListener('keydown', K.stories._keyHandler);
  },
  async like() {
    const viewer = $('storyViewer'); if (viewer.style.display !== 'flex') return;
    if (K.stories._activeStory) {
      const s = K.stories._activeStory;
      try {
        const d = await K.api.post(V2 + `/stories/${s.story_id}/like`);
        if (d.success) $('storyLikeCount').textContent = d.data?.like_count ?? 0;
      } catch(e) {}
    }
  },
  async react() {
    const viewer = $('storyViewer'); if (viewer.style.display !== 'flex') return;
    const reactions = ['heart', 'fire', 'laugh', 'wow', 'sad', 'angry'];
    const emoji = reactions[Math.floor(Math.random()*reactions.length)];
    if (K.stories._activeStory) {
      const s = K.stories._activeStory;
      try { await K.api.post(V2 + `/stories/${s.story_id}/reaction`, {reaction: emoji}); K.ui.toast('Reacted!', 'success'); } catch(e) {}
    }
  },
  async create() {
    const input = document.createElement('input');
    input.type = 'file'; input.accept = 'image/*,video/*'; input.style.display = 'none';
    input.onchange = async () => {
      if (!input.files?.length) return;
      const fd = new FormData(); fd.append('media', input.files[0]);
      const caption = await K.ui.prompt('Caption (optional):');
      if (caption) fd.append('caption', caption);
      try {
        const d = await K.api.post(V2 + '/stories/create', fd);
        if (d.success) { K.ui.toast('Story posted!', 'success'); K.stories.load(); }
        else K.ui.toast('Failed', 'error');
      } catch(e) { K.ui.toast('Upload failed', 'error'); }
    };
    input.click();
  }
};

K.saved = {
  async load() {
    const list = $('savedMessagesList'); if (!list) return;
    list.innerHTML = K.ui.loader();
    try {
      const d = await K.api.get(V2 + '/saved_messages?limit=50');
      if (d.success) {
        const msgs = d.data?.messages || [];
        if (!msgs.length) { list.innerHTML = '<div class="k-empty"><i class="fas fa-bookmark"></i><h3>No saved messages</h3></div>'; return; }
        list.innerHTML = msgs.map(sm => {
          const orig = sm.original_message || {};
          return `<div class="k-saved-item">
            <div class="k-saved-meta">${esc(orig.sender_username||'')} · ${sm.saved_at ? fmtTime(sm.saved_at) : ''}</div>
            <div class="k-saved-content">${esc(orig.content||'No content')}</div>
          </div>`;
        }).join('');
      }
    } catch(e) { list.innerHTML = '<div class="k-empty">Failed to load</div>'; }
  }
};

K.calls = {
  _roomUrl: null, _peerId: null, _timer: null, _started: null,
  start(url, peerId) {
    K.calls._roomUrl = url;
    K.calls._peerId = peerId;
    const overlay = $('videoOverlay');
    const frame = $('videoFrame');
    if (overlay) overlay.style.display = 'flex';
    if (frame) {
      frame.innerHTML = `<iframe src="${url}" allow="camera;microphone;display-capture" style="width:100%;height:100%;border:none"></iframe>`;
    }
    $('videoCallPeer').textContent = 'In call';
    K.calls._started = Date.now();
    K.calls._updateTimer();
    K.calls._timer = setInterval(K.calls._updateTimer, 1000);
  },
  _updateTimer() {
    if (!K.calls._started) return;
    const elapsed = Math.floor((Date.now() - K.calls._started) / 1000);
    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const s = String(elapsed % 60).padStart(2, '0');
    const t = m + ':' + s;
    $('videoCallDuration').textContent = t;
    $('miniDuration').textContent = t;
  },
  minimize() {
    $('videoOverlay').style.display = 'none';
    $('videoMinimized').style.display = 'flex';
  },
  maximize() {
    $('videoMinimized').style.display = 'none';
    $('videoOverlay').style.display = 'flex';
  },
  endCall() {
    clearInterval(K.calls._timer);
    K.calls._timer = null;
    K.calls._started = null;
    $('videoOverlay').style.display = 'none';
    $('videoMinimized').style.display = 'none';
    const frame = $('videoFrame');
    if (frame) frame.innerHTML = '<div class="k-loader" style="margin:auto"></div>';
    K.calls._roomUrl = null;
    K.calls._peerId = null;
    K.chat.loadList();
  },
  async load() {
    const list = $('callsList'); if (!list) return;
    list.innerHTML = K.ui.loader();
    try {
      const d = await K.api.get(V2 + '/calls/history');
      if (d.success) {
        const calls = d.data?.calls || [];
        if (!calls.length) { list.innerHTML = '<div class="k-empty"><i class="fas fa-phone-alt"></i><h3>No calls yet</h3></div>'; return; }
        list.innerHTML = calls.map(c => `
          <div class="k-call-item" onclick="K.chat.open('personal',${c.peer_id||c.other_user_id})">
            <div class="k-call-icon"><i class="fas fa-${c.direction==='outgoing'?'phone-alt':'phone-alt'}"></i></div>
            <div class="k-call-info">
              <div class="k-call-name">${esc(c.peer_name||'Unknown')}</div>
              <div class="k-call-meta">${c.direction==='outgoing'?'Outgoing':'Incoming'} · ${c.status||'ended'} · ${c.duration ? Math.floor(c.duration/60)+'m' : '--'}</div>
            </div>
            <div class="k-call-time">${fmtTime(c.created_at)}</div>
          </div>
        `).join('');
      }
    } catch(e) { list.innerHTML = '<div class="k-empty">Failed to load</div>'; }
  }
};

K.music = {
  _tracks: JSON.parse(localStorage.getItem('k_music_tracks')||'[]'),
  async load() {
    const list = $('musicList'); if (!list) return;
    list.innerHTML = K.ui.loader();
    try {
      const d = await K.api.get(V2 + '/music/library');
      if (d.success) {
        K.music._tracks = d.data?.tracks || [];
        localStorage.setItem('k_music_tracks', JSON.stringify(K.music._tracks));
        K.music.render();
      }
    } catch(e) { list.innerHTML = '<div class="k-empty">Failed to load</div>'; }
  },
  render() {
    const list = $('musicList'); if (!list) return;
    if (!K.music._tracks.length) {
      list.innerHTML = '<div class="k-empty"><i class="fas fa-music"></i><h3>No music yet</h3><p>Heart audio messages to save them</p></div>';
      return;
    }
    list.innerHTML = K.music._tracks.map((t, i) =>
      `<div class="k-music-item" onclick="K.music.play(${i})">
        <div class="k-music-cover"><i class="fas fa-music"></i></div>
        <div class="k-music-info">
          <div class="k-music-title">${esc(t.title||t.file_name||'Unknown')}</div>
          <div class="k-music-artist">${esc(t.artist||'Unknown')}</div>
        </div>
        <button class="k-icon-btn" onclick="event.stopPropagation();K.music.remove(${t.id})" style="flex-shrink:0" title="Remove"><i class="fas fa-trash"></i></button>
      </div>`
    ).join('');
    if (K.music._audio) {
      list.insertAdjacentHTML('beforeend', `<div class="k-music-player">
        <div class="k-music-player-info">
          <span id="musicNowPlaying">${esc(K.music._tracks[K.music._currentIdx]?.title||'')}</span>
          <button class="k-icon-btn" onclick="K.music.stop()"><i class="fas fa-stop"></i></button>
        </div>
      </div>`);
    }
  },
  _currentIdx: -1,
  _audio: null,
  play(idx) {
    const t = K.music._tracks[idx];
    if (!t?.file_url) return;
    if (K.music._audio) { K.music._audio.pause(); K.music._audio = null; }
    K.music._currentIdx = idx;
    K.music._audio = new Audio(t.file_url);
    K.music._audio.play();
    K.music.render();
  },
  stop() {
    if (K.music._audio) { K.music._audio.pause(); K.music._audio = null; }
    K.music._currentIdx = -1;
    K.music.render();
  },
  async remove(id) {
    try {
      const d = await K.api.del(V2 + '/music/library/' + id);
      if (d.success) { K.ui.toast('Removed', 'success'); K.music.load(); }
      else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Error', 'error'); }
  },
  async likeMusic(msgId) {
    try {
      const d = await K.api.post(V2 + '/music/library', {message_id: msgId});
      if (d.success) { K.ui.toast('Added to music library', 'success'); K.music.load(); }
      else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Error', 'error'); }
  }
};

K.search = {
  global: debounce(async (q) => {
    const dd = $('searchDropdown');
    if (!q || q.length < 2) { if (dd) dd.classList.remove('active'); return; }
    try {
      const d = await K.api.get(V2 + `/search/global?q=${encodeURIComponent(q)}`);
      if (d.success && d.data?.results) {
        const r = d.data.results;
        let html = '';
        if (r.users?.length) html += r.users.map(u => `<div class="k-contact-item" onclick="K.chat.open('personal',${u.user_id});$('searchDropdown').classList.remove('active')"><div class="k-contact-avatar">${K.ui.avatar(u.username, u.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(u.display_name||u.username)}</div><div class="k-contact-username">@${esc(u.username)}</div></div></div>`).join('');
        if (r.groups?.length) html += r.groups.map(g => `<div class="k-contact-item" onclick="K.chat.open('group',${g.group_id});$('searchDropdown').classList.remove('active')"><div class="k-contact-avatar group">${K.ui.avatar(g.name, g.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(g.name)}</div></div></div>`).join('');
        if (r.channels?.length) html += r.channels.map(ch => `<div class="k-contact-item" onclick="K.chat.open('channel',${ch.channel_id});$('searchDropdown').classList.remove('active')"><div class="k-contact-avatar channel">${K.ui.avatar(ch.name, ch.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(ch.name)}</div></div></div>`).join('');
        if (html) { dd.innerHTML = html; dd.classList.add('active'); }
        else dd.classList.remove('active');
        const sr = $('searchResults');
        if (sr) {
          const su = sr.querySelector('#searchUsers'); if (su) su.innerHTML = (r.users||[]).map(u => `<div class="k-contact-item" onclick="K.chat.open('personal',${u.user_id})"><div class="k-contact-avatar">${K.ui.avatar(u.username, u.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(u.display_name||u.username)}</div><div class="k-contact-username">@${esc(u.username)}</div></div></div>`).join('');
          const sg = sr.querySelector('#searchGroups'); if (sg) sg.innerHTML = (r.groups||[]).map(g => `<div class="k-contact-item" onclick="K.chat.open('group',${g.group_id})"><div class="k-contact-avatar group">${K.ui.avatar(g.name, g.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(g.name)}</div></div></div>`).join('');
          const sc = sr.querySelector('#searchChannels'); if (sc) sc.innerHTML = (r.channels||[]).map(ch => `<div class="k-contact-item" onclick="K.chat.open('channel',${ch.channel_id})"><div class="k-contact-avatar channel">${K.ui.avatar(ch.name, ch.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(ch.name)}</div></div></div>`).join('');
        }
      }
    } catch(e) { dd?.classList.remove('active'); }
  }, 300)
};

K.settings = {
  _isDark() { return document.documentElement.getAttribute('data-theme') === 'dark'; },
  toggleTheme() {
    const isDark = !K.settings._isDark();
    K.settings._applyTheme(isDark);
  },
  setTheme(t) {
    K.settings._applyTheme(t === 'dark');
  },
  _applyTheme(isDark) {
    if (isDark) document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('k_theme', isDark ? 'dark' : 'light');
    const sw = $('themeSwitch'); if (sw) sw.checked = isDark;
    const icon = $('themeIcon'); if (icon) icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    const label = $('themeLabel'); if (label) label.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    const ni = $('navThemeIcon'); if (ni) ni.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    const nl = $('navThemeLabel'); if (nl) nl.textContent = isDark ? 'Light mode' : 'Dark mode';
    K.settings.saveToServer();
  },
  setFontSize(s) {
    document.querySelectorAll('.k-font-btn').forEach(b => b.classList.toggle('active', b.dataset.size === s));
    const sizes = { small: '13px', medium: '14px', large: '16px' };
    document.querySelector('.k-app').style.fontSize = sizes[s] || '14px';
    localStorage.setItem('k_font_size', s);
    K.settings.saveToServer();
  },
  switchTab(tab) {
    document.querySelectorAll('.k-stab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('.k-settings-tab-content').forEach(p => p.style.display = p.dataset.tab === tab ? '' : 'none');
    if (tab === 'folders') K.settings.renderFolders();
    if (tab === 'themes') K.settings.renderSavedThemes();
    if (tab === 'privacy') K.settings.loadPrivacy();
    if (tab === 'sessions') K.settings.loadSessions();
    K.state.saveURL();
  },
  setHero(url) {
    const bg = $('splashScreen')?.querySelector('.k-splash-bg');
    if (bg) {
      if (url) { bg.style.backgroundImage = 'url(' + url + ')'; localStorage.setItem('k_hero_url', url); }
      else { bg.style.backgroundImage = ''; localStorage.removeItem('k_hero_url'); }
    }
    K.settings.saveToServer();
  },
  loadHero() {
    const url = localStorage.getItem('k_hero_url');
    if (url) { const bg = $('splashScreen')?.querySelector('.k-splash-bg'); if (bg) bg.style.backgroundImage = 'url(' + url + ')'; }
    const hu = $('heroUrlInput'); if (hu) hu.value = url || '';
  },
  async loadPrivacy() {
    try {
      const d = await K.api.get(V2 + '/profile/privacy');
      if (d.success && d.data) {
        const selects = document.querySelectorAll('.k-settings-item select');
        if (selects[0]) selects[0].value = d.data.last_seen || 'everyone';
        if (selects[1]) selects[1].value = d.data.profile_photo || 'everyone';
      }
    } catch(e) {}
  },
  async updatePrivacy(key, value) {
    try {
      await K.api.put(V2 + '/profile', {[key]: value});
      K.ui.toast('Privacy updated', 'success');
    } catch(e) { K.ui.toast('Failed', 'error'); }
  },
  async loadSessions() {
    try {
      const d = await K.api.get(V2 + '/sessions');
      if (d.success) {
        const list = $('sessionsList');
        if (list) {
          const sessions = d.data?.sessions || [];
          list.innerHTML = sessions.length ? sessions.map(s =>
            `<div class="k-settings-item"><span><strong>${esc(s.device||'Unknown')}</strong>${s.is_current ? ' <span style="color:var(--online-green)">(current)</span>' : ''}<br><span style="font-size:12px;color:var(--text-muted)">${esc(s.ip_address||'')}</span></span><span style="font-size:11px;color:var(--text-muted)">${s.last_activity||s.last_active ? fmtTime(s.last_activity||s.last_active) : ''}</span></div>`
          ).join('') : '<div style="color:var(--text-muted);padding:12px">No active sessions</div>';
        }
      }
    } catch(e) {}
  },
  setMyColor(color) {
    document.documentElement.style.setProperty('--bubble-my', color);
    localStorage.setItem('k_color_my', color);
    K.settings.saveToServer();
  },
  setTheirColor(color) {
    document.documentElement.style.setProperty('--bubble-their', color);
    localStorage.setItem('k_color_their', color);
    K.settings.saveToServer();
  },
  addFolder() {
    const name = prompt('Folder name:');
    if (name && name.trim()) {
      K.state.folders = K.state.folders || [];
      K.state.folders.push({name: name.trim(), chats: []});
      localStorage.setItem('k_folders', JSON.stringify(K.state.folders));
      K.settings.saveToServer();
      K.settings.renderFolders();
      K.settings.renderFolderBar();
    }
  },
  deleteFolder(name) {
    K.state.folders = (K.state.folders||[]).filter(f => f.name !== name);
    localStorage.setItem('k_folders', JSON.stringify(K.state.folders));
    K.settings.saveToServer();
    if (K.state.activeFolder === name) K.state.activeFolder = null;
    K.settings.renderFolders();
    K.settings.renderFolderBar();
    K.chat.loadList();
  },
  renameFolder(oldName) {
    const newName = prompt('New folder name:', oldName);
    if (newName && newName.trim() && newName.trim() !== oldName) {
      const f = K.state.folders.find(x => x.name === oldName);
      if (f) { f.name = newName.trim(); localStorage.setItem('k_folders', JSON.stringify(K.state.folders)); K.settings.saveToServer(); K.settings.renderFolders(); K.settings.renderFolderBar(); }
    }
  },
  renderFolders() {
    const list = $('foldersList'); if (!list) return;
    const folders = K.state.folders || [];
    if (!folders.length) { list.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:13px">No folders yet. Create one to organize chats.</div>'; return; }
    list.innerHTML = folders.map(f =>
      `<div class="k-settings-item">
        <span><i class="fas fa-folder" style="margin-right:8px;color:var(--accent-blue)"></i>${esc(f.name)} <span style="font-size:11px;color:var(--text-muted)">(${(f.chats||[]).length} chats)</span></span>
        <span style="display:flex;gap:4px">
          <button class="k-icon-btn" onclick="K.settings.renameFolder('${esc(f.name)}')" style="font-size:14px;width:28px;height:28px" title="Rename"><i class="fas fa-pen"></i></button>
          <button class="k-icon-btn" onclick="K.settings.deleteFolder('${esc(f.name)}')" style="font-size:14px;width:28px;height:28px;color:var(--accent-red)" title="Delete"><i class="fas fa-trash"></i></button>
        </span>
      </div>`
    ).join('');
  },
  renderFolderBar() {
    const bar = $('folderBar'); if (!bar) return;
    const folders = K.state.folders || [];
    if (!folders.length) { bar.style.display = 'none'; return; }
    bar.style.display = 'flex';
    const af = K.state.activeFolder;
    bar.innerHTML = `<button class="k-folder-btn ${!af?'active':''}" onclick="K.state.activeFolder=null;K.settings.renderFolderBar();K.chat.loadList()">All</button>` +
      folders.map(f => `<button class="k-folder-btn ${af===f.name?'active':''}" onclick="K.state.activeFolder='${esc(f.name)}';K.settings.renderFolderBar();K.chat.loadList()">${esc(f.name)}</button>`).join('');
  },
  saveCurrentTheme() {
    const saved = JSON.parse(localStorage.getItem('k_saved_themes')||'[]');
    const t = {
      name: 'Theme ' + (saved.length + 1),
      version: 1,
      theme: K.settings._isDark() ? 'dark' : 'light',
      font_size: localStorage.getItem('k_font_size')||'medium',
      color_my: localStorage.getItem('k_color_my')||'#5e72e4',
      color_their: localStorage.getItem('k_color_their')||'#e8e8e8',
      hero_url: localStorage.getItem('k_hero_url')||''
    };
    saved.push(t);
    localStorage.setItem('k_saved_themes', JSON.stringify(saved));
    K.settings.saveToServer();
    K.settings.renderSavedThemes();
    K.ui.toast('Theme saved', 'success');
  },
  renderSavedThemes() {
    const list = $('themeList'); if (!list) return;
    const saved = JSON.parse(localStorage.getItem('k_saved_themes')||'[]');
    if (!saved.length) { list.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:13px">No saved themes</div>'; return; }
    list.innerHTML = saved.map((t, i) =>
      `<div class="k-settings-item">
        <span><span style="display:inline-block;width:16px;height:16px;border-radius:50%;background:${t.color_my};margin-right:8px;vertical-align:middle"></span>${esc(t.name)}</span>
        <span style="display:flex;gap:4px">
          <button class="k-btn k-btn-secondary" style="padding:4px 10px;font-size:12px" onclick="K.settings.applySavedTheme(${i})">Apply</button>
          <button class="k-icon-btn" onclick="K.settings.deleteSavedTheme(${i})" style="font-size:14px;width:28px;height:28px;color:var(--accent-red)" title="Delete"><i class="fas fa-trash"></i></button>
        </span>
      </div>`
    ).join('');
    const cl = $('savedThemeList');
    if (cl) cl.innerHTML = list.innerHTML;
  },
  applySavedTheme(idx) {
    const saved = JSON.parse(localStorage.getItem('k_saved_themes')||'[]');
    const t = saved[idx]; if (!t) return;
    K.settings._applyTheme(t.theme === 'dark');
    K.settings.setFontSize(t.font_size);
    K.settings.setMyColor(t.color_my);
    K.settings.setTheirColor(t.color_their);
    K.settings.setHero(t.hero_url);
    K.settings.saveToServer();
    K.ui.toast('Theme applied: ' + t.name, 'success');
  },
  deleteSavedTheme(idx) {
    const saved = JSON.parse(localStorage.getItem('k_saved_themes')||'[]');
    saved.splice(idx, 1);
    localStorage.setItem('k_saved_themes', JSON.stringify(saved));
    K.settings.saveToServer();
    K.settings.renderSavedThemes();
  },
  exportTheme() {
    const t = {
      name: 'Kiselgram Theme',
      version: 1,
      theme: K.settings._isDark() ? 'dark' : 'light',
      font_size: localStorage.getItem('k_font_size')||'medium',
      color_my: localStorage.getItem('k_color_my')||'#5e72e4',
      color_their: localStorage.getItem('k_color_their')||'#e8e8e8',
      hero_url: localStorage.getItem('k_hero_url')||''
    };
    const blob = new Blob([JSON.stringify(t, null, 2)], {type: 'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'kiselgram-theme.ktqh';
    a.click();
    URL.revokeObjectURL(a.href);
  },
  async loadFromServer() {
    try {
      const d = await K.api.get(V2 + '/k/settings');
      if (d.success && d.data?.settings) {
        const s = d.data.settings;
        if (s.pinned) { K.state.pinned = s.pinned; localStorage.setItem('k_pinned', JSON.stringify(s.pinned)); }
        if (s.folders) { K.state.folders = s.folders; localStorage.setItem('k_folders', JSON.stringify(s.folders)); }
        if (s.hero_url) { localStorage.setItem('k_hero_url', s.hero_url); K.settings.loadHero(); }
        if (s.theme) { localStorage.setItem('k_theme', s.theme); K.settings._applyTheme(s.theme === 'dark'); }
        if (s.font_size) { localStorage.setItem('k_font_size', s.font_size); K.settings.setFontSize(s.font_size); }
        if (s.color_my) { localStorage.setItem('k_color_my', s.color_my); K.settings.setMyColor(s.color_my); }
        if (s.color_their) { localStorage.setItem('k_color_their', s.color_their); K.settings.setTheirColor(s.color_their); }
        if (s.saved_themes) { localStorage.setItem('k_saved_themes', JSON.stringify(s.saved_themes)); }
        if (s.music_tracks) { K.music._tracks = s.music_tracks; localStorage.setItem('k_music_tracks', JSON.stringify(s.music_tracks)); }
      }
    } catch(e) {}
  },
  async saveToServer() {
    const settings = {
      pinned: K.state.pinned || [],
      folders: K.state.folders || [],
      hero_url: localStorage.getItem('k_hero_url') || '',
      theme: localStorage.getItem('k_theme') || 'light',
      font_size: localStorage.getItem('k_font_size') || 'medium',
      color_my: localStorage.getItem('k_color_my') || '#5e72e4',
      color_their: localStorage.getItem('k_color_their') || '#e8e8e8',
      saved_themes: JSON.parse(localStorage.getItem('k_saved_themes')||'[]'),
      music_tracks: K.music._tracks || []
    };
    try {
      await K.api.put(V2 + '/k/settings', {settings});
    } catch(e) {}
  },
  importTheme(input) {
    if (!input?.files?.length) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const t = JSON.parse(e.target.result);
        if (t.theme) K.settings._applyTheme(t.theme === 'dark');
        if (t.font_size) K.settings.setFontSize(t.font_size);
        if (t.color_my) K.settings.setMyColor(t.color_my);
        if (t.color_their) K.settings.setTheirColor(t.color_their);
        if (t.hero_url) K.settings.setHero(t.hero_url);
        K.ui.toast('Theme imported: ' + (t.name||'Unknown'), 'success');
      } catch(e) { K.ui.toast('Invalid theme file', 'error'); }
    };
    reader.readAsText(input.files[0]);
    input.value = '';
  }
};

K.profile = {
  async save() {
    const name = $('editDisplayName')?.value?.trim();
    const bio = $('editBio')?.value?.trim();
    const statusEmoji = $('statusEmoji')?.value?.trim() || '';
    try {
      const d = await K.api.put(V2 + '/profile', {display_name: name, bio, status_emoji: statusEmoji});
      if (d.success) {
        K.ui.toast('Profile updated', 'success');
        if (K.state.user) { K.state.user.display_name = name; K.state.user.bio = bio; K.state.user.status_emoji = statusEmoji; }
        K.ui.renderUser(); K.modals.close();
      } else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Error', 'error'); }
  },
  async uploadAvatar(input) {
    if (!input?.files?.length) return;
    const fd = new FormData(); fd.append('avatar', input.files[0]);
    try {
      const d = await K.api.post(V2 + '/profile/avatar', fd);
      if (d.success) {
        K.ui.toast('Photo updated', 'success');
        if (K.state.user) K.state.user.avatar_url = d.data?.avatar_url;
        K.ui.renderUser();
      }
    } catch(e) { K.ui.toast('Upload failed', 'error'); }
  }
};

document.addEventListener('DOMContentLoaded', async () => {
  document.addEventListener('click', (e) => {
    const dd = $('searchDropdown');
    if (dd && !e.target.closest('.k-search-box')) dd.classList.remove('active');
    const menu = $('chatMenu');
    if (menu && !e.target.closest('#chatMenuBtn') && !e.target.closest('.k-chat-menu')) menu.style.display = 'none';
  });

  const menuBtn = $('menuBtn');
  const sb = $('sidebar');
  const backdrop = $('sidebarBackdrop');
  function closeSidebar() { sb?.classList.remove('open'); menuBtn?.classList.remove('active'); backdrop?.classList.remove('open'); }
  if (menuBtn) {
    menuBtn.addEventListener('click', (e) => { e.stopPropagation(); sb?.classList.toggle('open'); menuBtn.classList.toggle('active'); backdrop?.classList.toggle('open'); });
    backdrop?.addEventListener('click', closeSidebar);
    document.addEventListener('click', (e) => {
      if (sb?.classList.contains('open') && !sb.contains(e.target) && !menuBtn.contains(e.target)) {
        closeSidebar();
      }
    });
  }

  $('sidebar')?.querySelector('.k-sidebar-user')?.addEventListener('click', () => { K.modals.show('editProfile'); });
  document.querySelectorAll('.k-nav-item').forEach(item => {
    item.addEventListener('click', closeSidebar);
  });

  const savedTheme = localStorage.getItem('k_theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  K.settings._applyTheme(savedTheme === 'dark' || (!savedTheme && prefersDark));
  const fs = localStorage.getItem('k_font_size') || 'medium';
  K.settings.setFontSize(fs);
  const myColor = localStorage.getItem('k_color_my') || '#5e72e4';
  const theirColor = localStorage.getItem('k_color_their') || '#e8e8e8';
  document.documentElement.style.setProperty('--bubble-my', myColor);
  document.documentElement.style.setProperty('--bubble-their', theirColor);
  const myInput = $('myColor'); if (myInput) myInput.value = myColor;
  const theirInput = $('theirColor'); if (theirInput) theirInput.value = theirColor;

  await K.auth.init();

  await K.settings.loadFromServer();
  K.settings.loadHero();
  K.settings.renderFolderBar();
  K.state.restoreURL();
  if (K.state._pendingChat) {
    const pc = K.state._pendingChat;
    delete K.state._pendingChat;
    K.chat.open(pc.type, pc.id);
  } else if (K.state._pendingSettings) {
    const ps = K.state._pendingSettings;
    delete K.state._pendingSettings;
    K.views.show('settings');
    setTimeout(() => K.settings.switchTab(ps), 100);
  }

  setInterval(() => K.chat.loadList(), 15000);
  setInterval(() => { if (K.state.activeChat) K.chat.loadMessages(K.state.activeChat.type, K.state.activeChat.id); }, 5000);
  setInterval(() => K.stories.load(), 60000);
  setInterval(() => K.saved.load(), 30000);
});

window.K = K;
window.$ = $;
})();
