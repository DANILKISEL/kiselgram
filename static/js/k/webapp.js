K.webapp = {
  open(url, title) {
    const ov = $('webappOverlay');
    const fr = $('webappFrame');
    const ti = $('webappTitle');
    if (!ov || !fr) return;
    fr.src = url || 'about:blank';
    if (ti) ti.textContent = title || 'Web App';
    ov.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  },
  close() {
    const ov = $('webappOverlay');
    const fr = $('webappFrame');
    if (!ov) return;
    ov.style.display = 'none';
    if (fr) fr.src = 'about:blank';
    document.body.style.overflow = '';
  }
};
