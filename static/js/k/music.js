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
