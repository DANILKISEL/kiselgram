const SECOND_MS = 1000;

K.calls = {
  _timer: null, _started: null,
  start(url, peerId) {
    const overlay = $('videoOverlay');
    const frame = $('videoFrame');
    if (overlay) overlay.style.display = 'flex';
    if (frame) {
      frame.innerHTML = `<iframe src="${esc(url)}" allow="camera;microphone;display-capture" style="width:100%;height:100%;border:none"></iframe>`;
    }
    const vcp = $('videoCallPeer'); if (vcp) vcp.textContent = 'In call';
    K.calls._started = Date.now();
    K.calls._updateTimer();
    K.calls._timer = setInterval(K.calls._updateTimer, SECOND_MS);
  },
  _updateTimer() {
    if (!K.calls._started) return;
    const elapsed = Math.floor((Date.now() - K.calls._started) / SECOND_MS);
    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const s = String(elapsed % 60).padStart(2, '0');
    const t = m + ':' + s;
    const vcd = $('videoCallDuration'); if (vcd) vcd.textContent = t;
    const md = $('miniDuration'); if (md) md.textContent = t;
  },
  minimize() {
    const vo = $('videoOverlay'); if (vo) vo.style.display = 'none';
    const vm = $('videoMinimized'); if (vm) vm.style.display = 'flex';
  },
  maximize() {
    const vm = $('videoMinimized'); if (vm) vm.style.display = 'none';
    const vo = $('videoOverlay'); if (vo) vo.style.display = 'flex';
  },
  endCall() {
    clearInterval(K.calls._timer);
    K.calls._timer = null;
    K.calls._started = null;
    const vo = $('videoOverlay'); if (vo) vo.style.display = 'none';
    const vm = $('videoMinimized'); if (vm) vm.style.display = 'none';
    const frame = $('videoFrame');
    if (frame) frame.innerHTML = '<div class="k-loader" style="margin:auto"></div>';
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
