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
