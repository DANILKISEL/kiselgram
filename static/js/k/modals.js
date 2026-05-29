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
