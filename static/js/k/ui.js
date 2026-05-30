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
    const nm = $('sidebarName'); if (nm) nm.innerHTML = esc(u.display_name || u.username) + (u.status_emoji ? ` <span class="k-status-emoji" onclick="K.modals.show('editProfile')" style="cursor:pointer" title="Set status">${esc(u.status_emoji)}</span>` : ' <span class="k-status-emoji" onclick="K.modals.show(\'editProfile\')" style="cursor:pointer;font-size:11px;opacity:0.4" title="Set status">set status</span>');
    const un = $('sidebarUsername'); if (un) un.textContent = '@' + u.username;
  }
};
