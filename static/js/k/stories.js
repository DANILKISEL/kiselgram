K.stories = {
  async load() {
    try {
      const d = await K.api.get(V2 + '/stories');
      if (d.success) {
        K.state.stories = d.data?.stories || [];
        K.stories._renderRow();
        K.stories._renderGrid();
      }
    } catch(e) { console.error('Stories load:', e); }
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
          ${s.avatar_url ? `<img src="${esc(s.avatar_url)}">` : `<div style="width:100%;height:100%;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--accent-blue),var(--accent-green));color:white;font-weight:600;font-size:20px;border:2px solid var(--sidebar-bg)">${(s.username||'?')[0].toUpperCase()}</div>`}
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
        ${first.media_type === 'video' ? `<video src="${esc(first.media_path)}"></video>` : `<img src="${esc(first.media_path)}" loading="lazy">`}
        <div class="k-story-card-overlay"><span>${esc(s.username)}</span></div>
      </div>`;
    }).join('');
  },
  async view(userId) {
    const storyGroup = K.state.stories.find(s => s.user_id === userId);
    const stories = storyGroup?.stories; if (!stories?.length) return;
    const viewer = $('storyViewer'); if (!viewer) return; viewer.style.display = 'flex'; viewer.style.flexDirection = 'column';
    let idx = 0;
    const show = (i) => {
      if (K.stories._storyTimer) { clearTimeout(K.stories._storyTimer); K.stories._storyTimer = null; }
      const s = stories[i]; if (!s) { K.stories.close(); return; }
      K.stories._activeStory = s;
      const svn = $('storyViewerName'); if (svn) svn.textContent = storyGroup.username;
      const sva = $('storyViewerAvatar'); if (sva) sva.innerHTML = K.ui.avatar(storyGroup.username);
      const sm = $('storyMedia'); if (sm) sm.innerHTML = s.media_type === 'video'
        ? `<video src="${esc(s.media_path)}" autoplay controls style="max-width:100%;max-height:80vh"></video>`
        : `<img src="${esc(s.media_path)}" style="max-width:100%;max-height:80vh">`;
      const slc = $('storyLikeCount'); if (slc) slc.textContent = s.like_count || 0;
      const sp = $('storyProgress'); if (sp) sp.innerHTML = stories.map((_, si) =>
        `<div class="k-story-progress-seg"><div class="k-story-progress-fill" style="width:${si<i?'100%':si===i?'0%':'0%'}"></div></div>`
      ).join('');
      if (s.media_type !== 'video') {
        const fill = $('storyProgress')?.querySelectorAll('.k-story-progress-fill')[i];
        if (fill) { fill.style.transition = 'width 5s linear'; fill.style.width = '100%'; }
        K.stories._storyTimer = setTimeout(() => { if (i+1 < stories.length) show(i+1); else K.stories.close(); }, 5000);
      }
      try { K.api.post(V2 + `/stories/${s.story_id}/view`); } catch(_) {}
    };
    show(0);
    const next = () => { if (idx+1 < stories.length) { idx++; show(idx); } else K.stories.close(); };
    const prev = () => { if (idx > 0) { idx--; show(idx); } };
    viewer.onclick = (e) => { if (e.target === viewer || e.target.closest('.k-story-header') || e.target.closest('.k-story-actions')) return; const rect = viewer.getBoundingClientRect(); if (e.clientX < rect.width/3) prev(); else next(); };
    document.addEventListener('keydown', K.stories._keyHandler = (e) => { if (e.key === 'Escape') K.stories.close(); else if (e.key === 'ArrowRight') next(); else if (e.key === 'ArrowLeft') prev(); });
  },
  close() {
    const sv = $('storyViewer'); if (sv) sv.style.display = 'none';
    K.stories._activeStory = null;
    if (K.stories._keyHandler) document.removeEventListener('keydown', K.stories._keyHandler);
    if (K.stories._storyTimer) { clearTimeout(K.stories._storyTimer); K.stories._storyTimer = null; }
  },
  async like() {
    const viewer = $('storyViewer'); if (viewer.style.display !== 'flex') return;
    if (K.stories._activeStory) {
      const s = K.stories._activeStory;
      try {
        const d = await K.api.post(V2 + `/stories/${s.story_id}/like`);
        if (d.success) $('storyLikeCount').textContent = d.data?.like_count ?? 0;
      } catch(_) {}
    }
  },
  async react() {
    const viewer = $('storyViewer'); if (viewer.style.display !== 'flex') return;
    const reactions = ['heart', 'fire', 'laugh', 'wow', 'sad', 'angry'];
    const emoji = reactions[Math.floor(Math.random()*reactions.length)];
    if (K.stories._activeStory) {
      const s = K.stories._activeStory;
      try { await K.api.post(V2 + `/stories/${s.story_id}/reaction`, {reaction: emoji}); K.ui.toast('Reacted!', 'success'); } catch(_) {}
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
