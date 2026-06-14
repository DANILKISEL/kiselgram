const MIN_QUERY_LENGTH = 2;
const DEBOUNCE_DELAY_MS = 300;

K.search = {
  global: debounce(async (q) => {
    const dd = $('searchDropdown');
    if (!q || q.length < MIN_QUERY_LENGTH) { if (dd) dd.classList.remove('active'); return; }
    try {
      const d = await K.api.get(V2 + `/search/global?q=${encodeURIComponent(q)}`);
      if (d.success && d.data?.results) {
        const r = d.data.results;
        let html = '';
        if (r.users?.length) html += r.users.map(u => `<div class="k-contact-item" onclick="K.chat.open('personal',${u.user_id});$('searchDropdown').classList.remove('active')"><div class="k-contact-avatar">${K.ui.avatar(u.username, u.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(u.display_name||u.username)}</div><div class="k-contact-username">@${esc(u.username)}</div></div></div>`).join('');
        if (r.groups?.length) html += r.groups.map(g => `<div class="k-contact-item" onclick="K.chat.open('group',${g.group_id});$('searchDropdown').classList.remove('active')"><div class="k-contact-avatar group">${K.ui.avatar(g.name, g.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(g.name)}</div></div></div>`).join('');
        if (r.channels?.length) html += r.channels.map(ch => `<div class="k-contact-item" onclick="K.chat.open('channel',${ch.channel_id});$('searchDropdown').classList.remove('active')"><div class="k-contact-avatar channel">${K.ui.avatar(ch.name, ch.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(ch.name)}</div></div></div>`).join('');
        if (html) { dd.innerHTML = html; dd.classList.add('active'); }
        else dd.classList.remove('active');
        const sr = $('searchResults');
        if (sr) {
          const su = sr.querySelector('#searchUsers'); if (su) su.innerHTML = (r.users||[]).map(u => `<div class="k-contact-item" onclick="K.chat.open('personal',${u.user_id})"><div class="k-contact-avatar">${K.ui.avatar(u.username, u.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(u.display_name||u.username)}</div><div class="k-contact-username">@${esc(u.username)}</div></div></div>`).join('');
          const sg = sr.querySelector('#searchGroups'); if (sg) sg.innerHTML = (r.groups||[]).map(g => `<div class="k-contact-item" onclick="K.chat.open('group',${g.group_id})"><div class="k-contact-avatar group">${K.ui.avatar(g.name, g.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(g.name)}</div></div></div>`).join('');
          const sc = sr.querySelector('#searchChannels'); if (sc) sc.innerHTML = (r.channels||[]).map(ch => `<div class="k-contact-item" onclick="K.chat.open('channel',${ch.channel_id})"><div class="k-contact-avatar channel">${K.ui.avatar(ch.name, ch.avatar_url)}</div><div class="k-contact-info"><div class="k-contact-name">${esc(ch.name)}</div></div></div>`).join('');
        }
      }
    } catch(e) { dd?.classList.remove('active'); }
  }, DEBOUNCE_DELAY_MS)
};
