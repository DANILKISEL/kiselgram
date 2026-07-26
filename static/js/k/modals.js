const SEARCH_DEBOUNCE = 300;
const MIN_SEARCH_LENGTH = 2;

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
    if (!q || q.length < MIN_SEARCH_LENGTH) { r.innerHTML = '<div style="padding:16px;color:var(--text-muted);text-align:center">Type at least 2 characters</div>'; return; }
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
  }, SEARCH_DEBOUNCE),
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
    const isPremium = u.is_premium;
    return `
      <div class="k-modal-header"><h3>Edit Profile</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
      <div class="k-modal-body">
        <label style="font-size:13px;font-weight:500;margin-bottom:4px;display:block">Display Name</label>
        <input class="k-input" id="editDisplayName" value="${esc(u.display_name||'')}" placeholder="Display name">
        <label style="font-size:13px;font-weight:500;margin-bottom:4px;display:block">Bio</label>
        <textarea class="k-input" id="editBio" rows="3" placeholder="About you">${esc(u.bio||'')}</textarea>
        ${isPremium ? `
        <label style="font-size:13px;font-weight:500;margin-bottom:4px;display:block;margin-top:8px">Status Emoji <span style="color:var(--accent-gold);font-size:11px">(Premium)</span></label>
        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px" id="emojiPicker">
          ${['🌴','💼','🎮','📚','🎵','🏖️','💪','😴','❤️','🔥','🌟','🎯','💡','🎨','🏃','☕'].map(e => `<span class="k-emoji-opt${(u.status_emoji||'')===e?' active':''}" onclick="document.getElementById('statusEmoji').value=this.textContent;document.querySelectorAll('.k-emoji-opt').forEach(x=>x.classList.remove('active'));this.classList.add('active')">${e}</span>`).join('')}
        </div>
        <input class="k-input" id="statusEmoji" value="${esc(u.status_emoji||'')}" placeholder="Change status emoji" style="margin-bottom:4px" oninput="if(!this.value)this.value='⭐'">
        ` : ''}
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
    } catch(e) { K.ui.toast('Failed to search users', 'error'); }
  }, SEARCH_DEBOUNCE),
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
  async _switchProfileTab(el, tab, userId) {
    document.querySelectorAll('.k-profile-tab').forEach(t => t.classList.remove('k-profile-tab-active'));
    if (el) el.classList.add('k-profile-tab-active');
    const container = $('profileTabContent');
    if (!container) return;
    container.innerHTML = K.ui.loader();
    try {
      if (tab === 'playlist') await K.modals._loadTabPlaylist(container, userId);
      else if (tab === 'stories') await K.modals._loadTabStories(container, userId);
      else if (tab === 'files') await K.modals._loadTabFiles(container, userId);
      else if (tab === 'gifts') container.innerHTML = '<div style="padding:30px 0;color:var(--text-muted)"><i class="fas fa-gift" style="font-size:32px;margin-bottom:8px"></i><div style="font-size:13px">No gifts yet</div></div>';
    } catch(e) { container.innerHTML = '<div style="padding:30px 0;color:var(--text-muted);font-size:13px">Failed to load</div>'; }
  },
  async _loadTabPlaylist(container, userId) {
    const d = await K.api.get(V2 + `/users/${userId}/music`);
    const tracks = d.data?.tracks;
    if (!tracks || !tracks.length) { container.innerHTML = '<div style="padding:30px 0;color:var(--text-muted);font-size:13px"><i class="fas fa-music" style="font-size:32px;margin-bottom:8px;display:block"></i>No music in library yet</div>'; return; }
    let html = '<div style="display:flex;flex-direction:column;gap:4px">';
    tracks.forEach(t => {
      const name = t.title || t.file_name || 'Unknown';
      const artist = t.artist || '';
      html += `<div style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:8px;cursor:pointer" onmouseover="this.style.background='var(--bg-secondary)'" onmouseout="this.style.background=''" onclick="K.music.playUrl('${esc(t.file_url)}','${esc(name)}','${esc(artist)}')">
        <div style="width:36px;height:36px;border-radius:8px;background:var(--accent-blue);display:flex;align-items:center;justify-content:center;color:white;font-size:14px"><i class="fas fa-music"></i></div>
        <div style="flex:1;text-align:left;font-size:13px"><div style="font-weight:500">${esc(name)}</div>${artist ? '<div style="font-size:11px;color:var(--text-muted)">' + esc(artist) + '</div>' : ''}</div>
        <div style="font-size:11px;color:var(--text-muted)">${t.duration ? K.music._fmtTime ? K.music._fmtTime(t.duration) : t.duration + 's' : ''}</div>
      </div>`;
    });
    container.innerHTML = html + '</div>';
  },
  async _loadTabStories(container, userId) {
    const d = await K.api.get(V2 + '/stories');
    const storiesData = d.data?.stories || [];
    const userStories = storiesData.find(s => s.user_id === userId);
    if (!userStories || !userStories.stories || !userStories.stories.length) { container.innerHTML = '<div style="padding:30px 0;color:var(--text-muted);font-size:13px"><i class="fas fa-story" style="font-size:32px;margin-bottom:8px;display:block"></i>No stories yet</div>'; return; }
    let html = '<div style="display:flex;flex-direction:column;gap:6px">';
    userStories.stories.forEach(s => {
      const isVideo = s.media_type === 'video';
      html += `<div style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:8px;background:var(--bg-secondary)">
        <div style="width:40px;height:40px;border-radius:8px;overflow:hidden;background:var(--bg-primary);flex-shrink:0">${s.media_url ? (isVideo ? '<i class="fas fa-video" style="display:flex;align-items:center;justify-content:center;width:100%;height:100%;color:var(--accent-blue)"></i>' : `<img src="${esc(s.media_url)}" style="width:100%;height:100%;object-fit:cover">`) : '<i class="fas fa-image" style="display:flex;align-items:center;justify-content:center;width:100%;height:100%;color:var(--text-muted)"></i>'}</div>
        <div style="flex:1;text-align:left;font-size:12px"><div style="font-weight:500">${s.caption ? esc(s.caption).substring(0, 40) + (s.caption.length > 40 ? '...' : '') : (isVideo ? 'Video story' : 'Photo story')}</div><div style="font-size:11px;color:var(--text-muted)">${s.created_at ? fmtTime(s.created_at) : ''}</div></div>
        ${!s.is_viewed ? '<span style="width:8px;height:8px;border-radius:50%;background:var(--accent-blue);flex-shrink:0"></span>' : ''}
      </div>`;
    });
    container.innerHTML = html + '</div>';
  },
  async _loadTabFiles(container, userId) {
    const d = await K.api.get(V2 + `/users/${userId}/files`);
    const files = d.data?.files;
    if (!files || !files.length) { container.innerHTML = '<div style="padding:30px 0;color:var(--text-muted);font-size:13px"><i class="fas fa-file" style="font-size:32px;margin-bottom:8px;display:block"></i>No shared files</div>'; return; }
    let html = '<div style="display:flex;flex-direction:column;gap:4px">';
    files.forEach(f => {
      const icon = f.file_type === 'image' ? 'fa-image' : f.file_type === 'video' ? 'fa-video' : f.file_type === 'audio' ? 'fa-music' : 'fa-file';
      const iconColor = f.file_type === 'image' ? 'var(--accent-green)' : f.file_type === 'video' ? 'var(--accent-purple)' : f.file_type === 'audio' ? 'var(--accent-blue)' : 'var(--text-muted)';
      const thumb = f.file_type === 'image' && f.thumbnail_path ? `<img src="${esc(f.thumbnail_path)}" style="width:100%;height:100%;object-fit:cover">` : `<i class="fas ${icon}" style="display:flex;align-items:center;justify-content:center;width:100%;height:100%;color:${iconColor};font-size:18px"></i>`;
      html += `<div style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:8px;cursor:pointer" onmouseover="this.style.background='var(--bg-secondary)'" onmouseout="this.style.background=''" onclick="window.open('${esc(f.file_path)}','_blank')">
        <div style="width:40px;height:40px;border-radius:8px;overflow:hidden;background:var(--bg-primary);flex-shrink:0">${thumb}</div>
        <div style="flex:1;text-align:left;font-size:12px;overflow:hidden"><div style="font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${f.file_name ? esc(f.file_name) : 'Untitled'}</div><div style="font-size:11px;color:var(--text-muted)">${f.file_type || 'unknown'}${f.file_size ? ' · ' + K.ui.formatSize(f.file_size) : ''}</div></div>
        <div style="font-size:11px;color:var(--text-muted)">${f.timestamp ? fmtTime(f.timestamp) : ''}</div>
      </div>`;
    });
    container.innerHTML = html + '</div>';
  },
  async viewProfile(userId) {
    const overlay = $('modalOverlay'), content = $('modalContent');
    if (!overlay || !content) return;
    overlay.style.display = 'flex';
    content.innerHTML = K.ui.loader();
    let u;
    try {
      const d = await K.api.get(V2 + `/users/${userId}`);
      if (!d.success || !d.data) { content.innerHTML = '<div class="k-modal-body"><p style="text-align:center;padding:20px;color:var(--text-muted)">User not found</p></div>'; return; }
      u = d.data;
    } catch(e) { content.innerHTML = '<div class="k-modal-body"><p style="text-align:center;padding:20px;color:var(--text-muted)">Failed to load profile</p></div>'; return; }

    const initial = (u.display_name||u.username)[0].toUpperCase();
    const avatarHtml = u.avatar_url
      ? `<img src="${esc(u.avatar_url)}" style="width:100%;height:100%;object-fit:cover">`
      : initial;

    content.innerHTML = `
<div class="k-modal-header"><h3>Profile</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
<div class="k-modal-body" style="padding:0">
  <div style="height:120px;background:linear-gradient(135deg,var(--accent-blue),var(--accent-purple));display:flex;align-items:flex-end;padding:12px 16px;position:relative">
    <div style="width:64px;height:64px;border-radius:50%;border:3px solid white;overflow:hidden;background:var(--bg-primary);display:flex;align-items:center;justify-content:center;color:white;font-weight:600;font-size:26px">${avatarHtml}</div>
    <div style="margin-left:12px;margin-bottom:2px;color:white;text-shadow:0 1px 3px rgba(0,0,0,0.3)">
      <div style="font-size:16px;font-weight:600">${esc(u.display_name||u.username)}${u.is_premium && (!u.status_emoji || u.status_emoji === '⭐') ? '<img src="/static/img/img.png" alt="" style="width:18px;height:18px;vertical-align:middle;display:inline-block;margin-left:3px">' : (u.status_emoji ? ' ' + esc(u.status_emoji) : '')}</div>
      <div style="font-size:12px;opacity:0.9">@${esc(u.username)}${u.is_bot ? ' <span style="background:rgba(255,255,255,0.3);padding:1px 6px;border-radius:4px;font-size:10px">BOT</span>' : ''}</div>
    </div>
  </div>
  ${u.bio ? `<div style="padding:10px 16px;font-size:13px;color:var(--text-muted);border-bottom:1px solid var(--border-color)">${esc(u.bio)}</div>` : ''}
  <div style="display:flex;gap:16px;padding:10px 16px;border-bottom:1px solid var(--border-color);font-size:12px">
    <span style="color:${u.is_online ? 'var(--online-green)' : 'var(--text-muted)'}">${u.is_online ? '● Online' : u.last_seen ? 'Last seen ' + fmtTime(u.last_seen) : 'Offline'}</span>
    ${u.is_contact ? '<span style="color:var(--accent-green)"><i class="fas fa-check-circle"></i> In contacts</span>' : ''}
    <span style="color:var(--text-muted);cursor:pointer" onclick="K.modals.close();K.chat.open('personal',${u.user_id})"><i class="fas fa-comment"></i> Message</span>
    ${u.is_bot && u.bot_webapp_url ? `<span style="color:var(--accent-blue);cursor:pointer" onclick="K.modals.close();K.webapp.open('${esc(u.bot_webapp_url)}','${esc(u.display_name||u.username)}')"><i class="fas fa-globe"></i> Web App</span>` : ''}
  </div>
  <div class="k-profile-tabs" style="display:flex;border-bottom:2px solid var(--border-color)">
    <div class="k-profile-tab k-profile-tab-active" data-tab="playlist" onclick="K.modals._switchProfileTab(this,'playlist',${u.user_id})">Playlist</div>
    <div class="k-profile-tab" data-tab="stories" onclick="K.modals._switchProfileTab(this,'stories',${u.user_id})">Stories</div>
    <div class="k-profile-tab" data-tab="files" onclick="K.modals._switchProfileTab(this,'files',${u.user_id})">Files</div>
    <div class="k-profile-tab" data-tab="gifts" onclick="K.modals._switchProfileTab(this,'gifts',${u.user_id})">Gifts</div>
  </div>
  <div id="profileTabContent" style="min-height:200px;padding:16px;text-align:center;color:var(--text-muted);font-size:13px">${K.ui.loader()}</div>
</div>`;
    K.modals._switchProfileTab(document.querySelector('.k-profile-tab-active'), 'playlist', u.user_id);
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
    } catch(e) { K.ui.toast('Failed to search users', 'error'); }
  }, SEARCH_DEBOUNCE)
};
