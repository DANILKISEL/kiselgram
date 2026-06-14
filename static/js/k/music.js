K.music = {
  _tracks: (() => { try { return JSON.parse(localStorage.getItem('k_music_tracks')||'[]'); } catch(e) { return []; } })(),
  _currentIdx: -1,
  _audio: null,
  _urlTrack: null,
  _progTimer: null,
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
      `<div class="k-music-item${K.music._currentIdx===i?' playing':''}" onclick="K.music.play(${i})">
        <div class="k-music-cover"><i class="fas fa-music"></i></div>
        <div class="k-music-info">
          <div class="k-music-title">${esc(t.title||t.file_name||'Unknown')}</div>
          <div class="k-music-artist">${esc(t.artist||'Unknown')}</div>
        </div>
        <button class="k-icon-btn" onclick="event.stopPropagation();K.music.remove(${t.id})" style="flex-shrink:0" title="Remove"><i class="fas fa-trash"></i></button>
      </div>`
    ).join('');
  },
  play(idx) {
    const t = K.music._tracks[idx];
    if (!t?.file_url) return;
    if (K.music._audio) { K.music._audio.pause(); K.music._audio = null; }
    K.music._currentIdx = idx;
    K.music._audio = new Audio(t.file_url);
    K.music._audio.volume = parseFloat(localStorage.getItem('k_music_volume')||'1') || 0;
    K.music._audio.onended = () => {
      if (K.music._currentIdx + 1 < K.music._tracks.length) {
        K.music.play(K.music._currentIdx + 1);
      } else {
        K.music.stop();
      }
    };
    K.music._audio.play().catch(() => { K.ui.toast('Playback failed', 'error'); K.music.stop(); });
    K.music.showPlayer();
    K.music._updatePlayer();
    K.music._startProgress();
    K.music.render();
  },
  stop() {
    clearInterval(K.music._progTimer);
    K.music._progTimer = null;
    if (K.music._audio) { K.music._audio.pause(); K.music._audio = null; }
    K.music._currentIdx = -1;
    K.music._urlTrack = null;
    K.music.hidePlayer();
    K.music.render();
  },
  playPause() {
    if (!K.music._audio) return;
    if (K.music._audio.paused) {
      K.music._audio.play().catch(() => { K.ui.toast('Playback failed', 'error'); K.music.stop(); });
      K.music._startProgress();
    } else {
      K.music._audio.pause();
      clearInterval(K.music._progTimer);
    }
    K.music._updatePlayBtn();
  },
  setVolume(v) {
    const vol = parseFloat(v) || 0;
    if (K.music._audio) K.music._audio.volume = vol;
    localStorage.setItem('k_music_volume', vol);
  },
  async addCurrentToPlaylist() {
    const src = K.music._tracks[K.music._currentIdx] || K.music._urlTrack;
    const fileUrl = src?.file_url || src?.url;
    if (!fileUrl) { K.ui.toast('Nothing to add', 'info'); return; }
    try {
      const d = await K.api.post(V2 + '/music/library', {
        file_url: fileUrl,
        file_name: src.file_name || null,
        artist: src.artist || null,
        title: src.title || null,
        duration: src.duration || 0,
        source_message_id: src.source_message_id || src.message_id || null
      });
      if (d.success) { K.ui.toast('Added to library', 'success'); K.music.load(); }
      else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Error', 'error'); }
  },
  showPlayer() {
    const el = $('chatMusicPlayer');
    if (el) el.style.display = 'flex';
  },
  hidePlayer() {
    clearInterval(K.music._progTimer);
    K.music._progTimer = null;
    const el = $('chatMusicPlayer');
    if (el) el.style.display = 'none';
  },
  _startProgress() {
    clearInterval(K.music._progTimer);
    K.music._progTimer = setInterval(K.music._updateProgress, 250);
    K.music._updateProgress();
  },
  _updateProgress() {
    if (!K.music._audio) return;
    const fill = $('cmpProgressFill');
    const timeEl = $('cmpTime');
    if (fill) fill.style.width = (K.music._audio.currentTime / (K.music._audio.duration || 1) * 100) + '%';
    if (timeEl) timeEl.textContent = K.music._fmtTime(K.music._audio.currentTime) + ' / ' + K.music._fmtTime(K.music._audio.duration);
  },
  _fmtTime(s) {
    if (!s || !isFinite(s)) return '0:00';
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return m + ':' + String(sec).padStart(2, '0');
  },
  _updatePlayer() {
    const t = K.music._tracks[K.music._currentIdx];
    const u = K.music._urlTrack;
    const nameEl = $('cmpTrackName');
    const artistEl = $('cmpTrackArtist');
    if (nameEl) nameEl.textContent = t?.title || t?.file_name || u?.title || 'Unknown';
    if (artistEl) artistEl.textContent = t?.artist || u?.artist || 'Unknown';
    K.music._updatePlayBtn();
  },
  _updatePlayBtn() {
    const btn = $('cmpPlayBtn');
    if (!btn) return;
    btn.innerHTML = K.music._audio && !K.music._audio.paused
      ? '<i class="fas fa-pause"></i>'
      : '<i class="fas fa-play"></i>';
  },
  async remove(id) {
    try {
      const d = await K.api.del(V2 + '/music/library/' + id);
      if (d.success) { K.ui.toast('Removed', 'success'); K.music.load(); }
      else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Error', 'error'); }
  },
  playUrl(url, title, artist, messageId) {
    if (K.music._audio) { K.music._audio.pause(); K.music._audio = null; }
    K.music._currentIdx = -1;
    K.music._urlTrack = { url, title, artist, message_id: messageId };
    K.music._audio = new Audio(url);
    K.music._audio.volume = parseFloat(localStorage.getItem('k_music_volume')||'1');
    K.music._audio.onended = () => { K.music.stop(); };
    K.music._audio.play().catch(() => { K.ui.toast('Playback failed', 'error'); K.music.stop(); });
    K.music.showPlayer();
    K.music._updatePlayer();
    K.music._startProgress();
  },
  async likeMusic(msgId) {
    try {
      const d = await K.api.post(V2 + '/music/library', {message_id: msgId});
      if (d.success) { K.ui.toast('Added to music library', 'success'); K.music.load(); }
      else K.ui.toast('Failed', 'error');
    } catch(e) { K.ui.toast('Error', 'error'); }
  }
};
