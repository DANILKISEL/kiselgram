const SAVED_LIMIT = 50;

K.saved = {
  async load() {
    const list = $('savedMessagesList'); if (!list) return;
    list.innerHTML = K.ui.loader();
    try {
      const d = await K.api.get(V2 + '/saved_messages?limit=' + SAVED_LIMIT);
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
