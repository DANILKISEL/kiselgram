'use strict';

const $ = (id) => document.getElementById(id);
const esc = (s) => { if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML.replace(/'/g, '&#39;'); };
const fmtTime = (ts) => { if (!ts) return ''; try { const d = new Date(ts), n = new Date(); const diff = n - d; if (diff < MINUTE_MS) return 'now'; if (diff < HOUR_MS) return Math.floor(diff/MINUTE_MS)+'m'; if (diff < DAY_MS) return Math.floor(diff/HOUR_MS)+'h'; return d.toLocaleDateString(); } catch(e) { return ''; } };
const safeDate = (val) => { if (val == null || val === '') return null; const d = new Date(val); return isNaN(d.getTime()) ? null : d; };
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

const V2 = '/api.v2/api';
const V3 = '/api.v3/api';

const MINUTE_MS = 60000;
const HOUR_MS = 3600000;
const DAY_MS = 86400000;

const isDesktopView = new URLSearchParams(window.location.search).get('view') === 'desktop';

const K = {
  isDesktop: isDesktopView,
  state: {
    user: null, chats: [], contacts: [], stories: [],
    activeChat: null, replyTo: null, online: navigator.onLine,
    blockedUsers: [],
    pinned: (() => { try { return JSON.parse(localStorage.getItem('k_pinned')||'[]'); } catch(e) { return []; } })(),
    folders: (() => { try { return JSON.parse(localStorage.getItem('k_folders')||'[]'); } catch(e) { return []; } })(),
    activeFolder: null,
    saveURL() {
      const p = new URLSearchParams(window.location.search);
      if (K.state.activeChat) p.set('chat', K.state.activeChat.type+':'+K.state.activeChat.id);
      else p.delete('chat');
      const stab = document.querySelector('.k-stab.active');
      if (stab) p.set('settings', stab.dataset.tab);
      else p.delete('settings');
      const n = window.location.pathname + '?' + p.toString();
      if (n !== window.location.href.replace(window.location.origin,'')) history.replaceState(null, '', n);
    },
    restoreURL() {
      const p = new URLSearchParams(window.location.search);
      const chat = p.get('chat');
      if (chat) {
        const [type, id] = chat.split(':');
        if (type && id) { K.state._pendingChat = {type, id: parseInt(id, 10)}; }
      }
      const stab = p.get('settings');
      if (stab) K.state._pendingSettings = stab;
    }
  }
};

window.K = K;
window.$ = $;
window.esc = esc;
window.fmtTime = fmtTime;
window.debounce = debounce;
window.V2 = V2;
window.V3 = V3;

window.addEventListener('beforeunload', function() {
  if (K._pollIntervals) K._pollIntervals.forEach(clearInterval);
});
