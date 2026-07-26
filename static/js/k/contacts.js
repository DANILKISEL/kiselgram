K.contacts = {
  async load() {
    try {
      const d = await K.api.get(V2 + '/contacts');
      if (d.success) {
        K.state.contacts = d.data?.contacts || [];
        K.contacts.render(K.state.contacts);
      }
    } catch(e) { K.ui.toast('Failed to load contacts', 'error'); }
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
          <div class="k-contact-name">${esc(ct.display_name||ct.username)}${ct.is_premium && (!ct.status_emoji || ct.status_emoji === '⭐') ? '<img src="/static/img/img.png" alt="" style="width:16px;height:16px;vertical-align:middle;display:inline-block;margin-left:2px">' : (ct.status_emoji ? ' ' + esc(ct.status_emoji) : '')}</div>
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
    const filtered = q ? (K.state.contacts||[]).filter(c => (c.display_name||c.username).toLowerCase().includes(q.toLowerCase())) : (K.state.contacts||[]);
    K.contacts.render(filtered);
  }
};
