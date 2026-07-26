(function() {
'use strict';

K.features = {};

// ── Emoji / Sticker / GIF Picker ────────────────────────────

const EMOJI_CATEGORIES = [
  { name: 'Smileys', emojis: ['😀','😃','😄','😁','😅','😂','🤣','😊','😇','🙂','😉','😌','😍','🥰','😘','😗','😋','😛','😜','🤪','😝','🤑','🤗','🤭','🫢','🫣','🤫','🤔','🫡','🤐','🤨','😐','😑','😶','🫥','😏','😒','🙄','😬','😮','😯','😲','😳','🥺','😢','😭','😤','😠','😡','🤬','💀','☠️'] },
  { name: 'Gestures', emojis: ['👋','🤚','🖐️','✋','🖖','🫱','🫲','🫳','🫴','👌','🤌','🤏','✌️','🤞','🫰','🫵','🤟','🤘','🤙','👈','👉','👆','🖕','👇','☝️','🫵','👍','👎','✊','👊','🤛','🤜','👏','🙌','🫶','👐','🤲','🤝','🙏','✍️','💅','🤳'] },
  { name: 'People', emojis: ['👶','🧒','👦','👧','🧑','👨','👩','🧓','👴','👵','👨‍👩‍👧‍👦','👨‍👩‍👧','👨‍👩‍👦','👩‍👩‍👧','👨‍👨‍👧','👪','👨‍👧','👩‍👧','🧑‍🤝‍🧑','👫','👬','👭','💑','👩‍❤️‍👨','👨‍❤️‍👨','👩‍❤️‍👩','💏','👩‍❤️‍💋‍👨','👨‍❤️‍💋‍👨','👩‍❤️‍💋‍👩','🧑‍🧑‍🧒','🧑‍🧑‍🧒‍🧒','🧑‍🧒','🧑‍🧒‍🧒'] },
  { name: 'Nature', emojis: ['🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐸','🐵','🙈','🙉','🙊','🐒','🐔','🐧','🐦','🐤','🐣','🐥','🦆','🦅','🦉','🦇','🐺','🐗','🐴','🦄','🐝','🐛','🦋','🐌','🐞','🐜','🪰','🪲','🪳','🦟','🦗','🕷️','🦂','🐢','🐍','🦎','🦖','🦕','🐙','🦑','🪼','🦐','🦞','🦀','🐡','🐠','🐟','🐬','🐳','🐋','🦈','🪸','🐊'] },
  { name: 'Food', emojis: ['🍏','🍎','🍐','🍊','🍋','🍌','🍉','🍇','🍓','🫐','🍈','🍒','🍑','🥭','🍍','🥥','🥝','🍅','🍆','🥑','🥦','🥬','🥒','🌽','🫑','🥕','🫒','🧄','🧅','🥔','🍠','🫘','🥐','🍞','🥖','🧀','🥚','🍳','🥓','🥩','🍗','🍖','🌭','🍔','🍟','🍕','🫓','🥪','🥙','🧆','🌮','🌯','🥗','🥘','🫕','🥫','🍝','🍜','🍲','🍛','🍣','🍱','🥟','🦪','🍤','🍙','🍚','🍘','🍥','🥠','🥮','🍢','🍡','🍧','🍨','🍦','🥧','🧁','🍰','🎂','🍮','🍭','🍬','🍫','🍿','🍩','🍪','🌰','🥜','🍯','🥛','🍼','🫖','☕','🍵','🧃','🥤','🧋','🍶','🍺','🍻','🥂','🍷','🫗','🥃','🍸','🍹','🧉','🍾','🧊','🥄','🍴','🍽️','🥣','🥡','🥢','🧂'] },
  { name: 'Activity', emojis: ['⚽','🏀','🏈','⚾','🥎','🎾','🏐','🏉','🥏','🎱','🪀','🏓','🏸','🏒','🏑','🥍','🏏','🪃','🥅','⛳','🪁','🏹','🎣','🤿','🥊','🥋','🎽','🛹','🛼','🛷','⛸️','🥌','🎿','⛷️','🏂','🪂','🏋️','🤼','🤸','🤺','⛹️','🤾','🏌️','🏇','🧘','🏄','🏊','🤽','🚣','🧗','🚵','🚴','🎪','🎭','🎨','🎬','🎤','🎧','🎼','🎹','🥁','🪘','🎷','🎺','🎸','🪕','🎻','🎲','♟️','🎯','🎳','🎮','🕹️'] },
  { name: 'Travel', emojis: ['🚗','🚕','🚙','🚌','🚎','🏎️','🚓','🚑','🚒','🚐','🛻','🚚','🚛','🚜','🏍️','🛵','🛺','🚲','🛴','🛹','🛼','🚏','🛣️','🛤️','⛽','🛞','🚨','🚥','🚦','🛑','🚧','⚓','🛟','⛵','🛶','🚤','🛳️','⛴️','🛥️','🚢','✈️','🛩️','🛫','🛬','🪂','💺','🚁','🚟','🚠','🚡','🛰️','🚀','🛸','🏠','🏡','🏘️','🏚️','🏗️','🏢','🏭','🏣','🏤','🏥','🏦','🏨','🏩','🏪','🏫','🏬','🏯','🏰','💒','🗼','🗽','⛪','🕌','🛕','🕍','⛩️','🕋','⛲','⛺','🌁','🌃','🏙️','🌄','🌅','🌆','🌇','🌉','🗾','🏔️','⛰️','🌋','🗻'] },
  { name: 'Symbols', emojis: ['❤️','🧡','💛','💚','💙','💜','🖤','🤍','🤎','💔','❣️','💕','💞','💓','💗','💖','💘','💝','💟','☮️','✝️','☪️','🕉️','☸️','✡️','🔯','🕎','☯️','🦸','🦹','🧙','🧚','🧛','🧜','🧝','🧞','🧟','🧌','💌','💋','💄','👑','👒','🎩','🎓','🧢','🪖','⛑️','👑','💍','👓','🕶️','🥽','🥼','🦺','👔','👕','👖','🧣','🧤','🧥','🧦','👗','👘','🥻','🩱','🩲','🩳','👙','👚','🪭','👛','👜','👝','🎒','🩴','👞','👟','🥾','🥿','👠','👡','🩰','👢','👣','🪮'] },
  { name: 'Objects', emojis: ['📱','💻','🖥️','🖨️','⌨️','🖱️','🖲️','🕹️','🗜️','💽','💾','💿','📀','📼','📷','📸','📹','🎥','📽️','🎞️','📞','☎️','📟','📠','📺','📻','🎙️','🎚️','🎛️','🧭','⏱️','⏲️','⏰','🕰️','⌛','⏳','📡','🔋','🪫','🔌','💡','🔦','🕯️','🪔','🧯','🗑️','🛢️','💸','💵','💴','💶','💷','🪙','💰','💳','💎','⚖️','🪜','🧰','🪛','🔧','🔨','⚒️','🛠️','⛏️','🪚','🔩','⚙️','🪤','🧱','⛓️','🧲','🔫','💣','🧨','🪓','🔪','🗡️','⚔️','🛡️','🚬','⚰️','🪦','⚱️','🏺','🔮','📿','🧿','🪬'] },
];

let _emojiPickerVisible = false;

function toggleEmojiPicker() {
  const picker = $('emojiPicker');
  if (!picker) { createEmojiPicker(); return toggleEmojiPicker(); }
  picker.style.display = picker.style.display === 'flex' ? 'none' : 'flex';
  _emojiPickerVisible = picker.style.display === 'flex';
}

function createEmojiPicker() {
  const container = document.createElement('div');
  container.id = 'emojiPicker';
  container.className = 'k-emoji-picker';
  container.innerHTML = `
    <div class="k-emoji-tabs">
      <button class="k-emoji-tab active" onclick="K.features.switchEmojiTab(0,this)"><i class="fas fa-smile"></i></button>
      <button class="k-emoji-tab" onclick="K.features.switchEmojiTab(1,this)"><i class="fas fa-hand-peace"></i></button>
      <button class="k-emoji-tab" onclick="K.features.switchEmojiTab(2,this)"><i class="fas fa-user"></i></button>
      <button class="k-emoji-tab" onclick="K.features.switchEmojiTab(3,this)"><i class="fas fa-leaf"></i></button>
      <button class="k-emoji-tab" onclick="K.features.switchEmojiTab(4,this)"><i class="fas fa-utensils"></i></button>
      <button class="k-emoji-tab" onclick="K.features.switchEmojiTab(5,this)"><i class="fas fa-futbol"></i></button>
      <button class="k-emoji-tab" onclick="K.features.switchEmojiTab(6,this)"><i class="fas fa-car"></i></button>
      <button class="k-emoji-tab" onclick="K.features.switchEmojiTab(7,this)"><i class="fas fa-heart"></i></button>
      <button class="k-emoji-tab" onclick="K.features.switchEmojiTab(8,this)"><i class="fas fa-cog"></i></button>
      <button class="k-emoji-tab gif-tab" onclick="K.features.showGifTab(this)"><i class="fas fa-gift"></i> GIF</button>
    </div>
    <div class="k-emoji-search">
      <input class="k-emoji-search-input" placeholder="Search emoji..." oninput="K.features.filterEmoji(this.value)">
    </div>
    <div class="k-emoji-grid" id="emojiGrid">${EMOJI_CATEGORIES[0].emojis.map(e => `<span class="k-emoji-cell" onclick="K.features.insertEmoji('${e}')">${e}</span>`).join('')}</div>
  `;
  const inputArea = $('inputArea');
  if (inputArea) inputArea.parentNode.insertBefore(container, inputArea.nextSibling);
}

function insertEmoji(emoji) {
  const input = $('messageInput');
  if (!input) return;
  const start = input.selectionStart;
  const val = input.value;
  input.value = val.substring(0, start) + emoji + val.substring(input.selectionEnd);
  input.selectionStart = input.selectionEnd = start + emoji.length;
  input.focus();
  K.chat.input.handle();
}

function switchEmojiTab(idx, btn) {
  document.querySelectorAll('.k-emoji-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  const grid = $('emojiGrid');
  if (grid && EMOJI_CATEGORIES[idx]) {
    grid.innerHTML = EMOJI_CATEGORIES[idx].emojis.map(e => `<span class="k-emoji-cell" onclick="K.features.insertEmoji('${e}')">${e}</span>`).join('');
  }
}

function filterEmoji(query) {
  const grid = $('emojiGrid');
  if (!grid) return;
  if (!query.trim()) { grid.querySelectorAll('.k-emoji-cell').forEach(c => c.style.display = ''); return; }
  const q = query.toLowerCase();
  grid.querySelectorAll('.k-emoji-cell').forEach(c => {
    c.style.display = c.textContent.includes(q) ? '' : 'none';
  });
}

let _gifCache = [];
function showGifTab(btn) {
  document.querySelectorAll('.k-emoji-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  const grid = $('emojiGrid');
  if (!grid) return;
  if (_gifCache.length) {
    grid.innerHTML = _gifCache.map(g => `<img class="k-gif-cell" src="${esc(g.url)}" alt="GIF" onclick="K.features.sendGif('${esc(g.url)}')" loading="lazy">`).join('');
    return;
  }
  grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--text-muted)"><i class="fas fa-search" style="font-size:24px;margin-bottom:8px;display:block"></i>Search GIFs via Tenor<br><button class="k-btn k-btn-secondary" style="margin-top:8px" onclick="K.features.searchGIF(\'trending\')">Load Trending</button></div>';
}

async function searchGIF(query) {
  const grid = $('emojiGrid');
  if (!grid) return;
  grid.innerHTML = '<div class="k-loader"></div>';
  try {
    const d = await K.api.get('/api.v2/api/gifs/search?q=' + encodeURIComponent(query) + '&limit=30');
    if (d.success && d.data?.gifs) {
      _gifCache = d.data.gifs;
      grid.innerHTML = d.data.gifs.map(g => `<img class="k-gif-cell" src="${esc(g.url)}" alt="GIF" onclick="K.features.sendGif('${esc(g.url)}')" loading="lazy">`).join('');
    } else {
      grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--text-muted)">No GIFs found</div>';
    }
  } catch(e) {
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--text-muted)">Failed to load GIFs</div>';
  }
}

async function sendGif(url) {
  if (!K.state.activeChat) return;
  const { type, id } = K.state.activeChat;
  try {
    const payload = { content: '', file_url: url, file_type: 'gif' };
    if (type === 'personal') payload.receiver_id = id;
    else if (type === 'group') payload.group_id = id;
    else if (type === 'channel') payload.channel_id = id;
    const d = await K.api.post(V2 + '/send_message', payload);
    if (d.success) { K.chat.loadMessages(type, id); }
    else { K.ui.toast('Failed to send GIF', 'error'); }
  } catch(e) { K.ui.toast('Error sending GIF', 'error'); }
  const picker = $('emojiPicker');
  if (picker) picker.style.display = 'none';
}


// ── Polls ───────────────────────────────────────────────────

function showCreatePoll() {
  K.modals.show('createPoll');
  const container = $('modalContent');
  if (!container) return;
  container.innerHTML = `
    <div class="k-modal-header">
      <h3>Create Poll</h3>
      <button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button>
    </div>
    <div class="k-modal-body">
      <div class="k-form-group">
        <label>Question</label>
        <input class="k-input" id="pollQuestion" placeholder="Ask something..." maxlength="255">
      </div>
      <div class="k-form-group" id="pollOptions">
        <label>Options</label>
        <input class="k-input poll-option" placeholder="Option 1" maxlength="100">
        <input class="k-input poll-option" placeholder="Option 2" maxlength="100">
      </div>
      <button class="k-btn k-btn-secondary" style="width:100%;margin-top:6px;padding:6px;font-size:12px" onclick="K.features.addPollOption()"><i class="fas fa-plus"></i> Add option</button>
      <div class="k-form-group" style="flex-direction:row;align-items:center;gap:8px;margin-top:10px">
        <input type="checkbox" id="pollMultiple" style="width:16px;height:16px">
        <label for="pollMultiple" style="margin:0">Allow multiple answers</label>
      </div>
      <div class="k-form-group" style="flex-direction:row;align-items:center;gap:8px">
        <input type="checkbox" id="pollAnonymous" checked style="width:16px;height:16px">
        <label for="pollAnonymous" style="margin:0">Anonymous voting</label>
      </div>
    </div>
    <div class="k-modal-footer">
      <button class="k-btn k-btn-secondary" onclick="K.modals.close()">Cancel</button>
      <button class="k-btn k-btn-primary" onclick="K.features.createPoll()">Send Poll</button>
    </div>`;
}

function addPollOption() {
  const container = $('pollOptions');
  if (!container) return;
  const count = container.querySelectorAll('.poll-option').length;
  if (count >= 10) { K.ui.toast('Maximum 10 options', 'warning'); return; }
  const input = document.createElement('input');
  input.className = 'k-input poll-option';
  input.placeholder = 'Option ' + (count + 1);
  input.maxLength = 100;
  container.appendChild(input);
}

async function createPoll() {
  const question = $('pollQuestion')?.value?.trim();
  if (!question) { K.ui.toast('Enter a question', 'error'); return; }
  const optionInputs = document.querySelectorAll('.poll-option');
  const options = [];
  optionInputs.forEach(i => { const v = i.value.trim(); if (v) options.push(v); });
  if (options.length < 2) { K.ui.toast('Need at least 2 options', 'error'); return; }
  if (!K.state.activeChat) { K.ui.toast('No active chat', 'error'); return; }
  const { type, id } = K.state.activeChat;
  const multiple = $('pollMultiple')?.checked || false;
  const anonymous = $('pollAnonymous')?.checked !== false;
  try {
    const d = await K.api.post(V2 + '/polls/create', {
      question, options, is_multiple: multiple, is_anonymous: anonymous,
      chat_type: type, chat_id: id
    });
    if (d.success) {
      K.ui.toast('Poll created', 'success');
      K.modals.close();
      K.chat.loadMessages(type, id);
    } else {
      K.ui.toast(d.error?.message || 'Failed', 'error');
    }
  } catch(e) { K.ui.toast('Error creating poll', 'error'); }
}

async function votePoll(pollId, optionIdx) {
  try {
    const d = await K.api.post(V2 + '/polls/vote', { poll_id: pollId, option_index: optionIdx });
    if (d.success) {
      if (K.state.activeChat) K.chat.loadMessages(K.state.activeChat.type, K.state.activeChat.id);
    } else {
      K.ui.toast(d.error?.message || 'Vote failed', 'error');
    }
  } catch(e) { K.ui.toast('Vote error', 'error'); }
}

function renderPoll(poll, msgId) {
  const total = poll.votes?.reduce((a,b) => a + b, 0) || 0;
  const myVote = poll.my_votes || [];
  const multiple = poll.is_multiple;
  return `<div class="k-poll" data-poll-id="${poll.id}" data-msg-id="${msgId}">
    <div class="k-poll-question">${esc(poll.question)}</div>
    <div class="k-poll-options">
      ${poll.options.map((opt, i) => {
        const count = poll.votes?.[i] || 0;
        const pct = total ? Math.round(count / total * 100) : 0;
        const voted = myVote.includes(i);
        return `<div class="k-poll-option ${voted ? 'voted' : ''}" onclick="${!poll.closed && !voted ? `K.features.votePoll(${poll.id},${i})` : ''}">
          <div class="k-poll-bar" style="width:${pct}%"></div>
          <span class="k-poll-label">${esc(opt)}</span>
          <span class="k-poll-pct">${pct}%</span>
          ${voted ? '<i class="fas fa-check k-poll-check"></i>' : ''}
        </div>`;
      }).join('')}
    </div>
    <div class="k-poll-footer">
      <span>${total} vote${total !== 1 ? 's' : ''}</span>
      ${multiple ? '<span>Multiple choice</span>' : ''}
      ${poll.is_anonymous ? '<span>Anonymous</span>' : ''}
      ${poll.closed ? '<span>Closed</span>' : ''}
    </div>
  </div>`;
}


// ── Forward Messages ─────────────────────────────────────────

async function showForwardDialog(msgId) {
  K.modals.show('forward');
  const container = $('modalContent');
  if (!container) return;
  container.innerHTML = `<div class="k-modal-header"><h3>Forward to...</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
    <div class="k-modal-body"><div class="k-search-box" style="margin:0 0 8px"><i class="fas fa-search"></i><input class="k-search-input" id="forwardSearch" placeholder="Search chats..." oninput="K.features.filterForwardChats(this.value)"></div>
    <div id="forwardChatList">${K.ui.loader()}</div></div>`;
  try {
    const d = await K.api.get(V2 + '/chat_list');
    if (d.success) {
      const list = $('forwardChatList');
      if (list) {
        K.features._forwardChats = d.data.chats || [];
        list.innerHTML = (d.data.chats || []).map(c => {
          const isSaved = c.is_saved;
          const name = isSaved ? 'Saved Messages' : (c.peer?.display_name || c.peer?.username || c.group?.name || c.channel?.name || 'Unknown');
          const id = isSaved ? (K.state.user?.user_id || c.peer?.user_id) : (c.chat_type === 'personal' ? (c.peer?.user_id || c.peer?.id) : (c.group?.group_id || c.channel?.channel_id));
          const type = isSaved ? 'personal' : c.chat_type;
          const isSelf = isSaved || (type === 'personal' && id === K.state.user?.user_id);
          const avatar = isSaved ? '<i class="fas fa-bookmark" style="font-size:18px;color:var(--accent-blue)"></i>' : (c.peer?.avatar_url || c.group?.avatar_url || c.channel?.avatar_url ? `<img src="${esc(c.peer?.avatar_url || c.group?.avatar_url || c.channel?.avatar_url)}" style="width:40px;height:40px;border-radius:50%;object-fit:cover">` : `<span style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;border-radius:50%;color:white;font-weight:600;background:linear-gradient(135deg,var(--accent-blue),var(--accent-green))">${name[0].toUpperCase()}</span>`);
          return `<div class="k-forward-item" onclick="K.features.doForward(${msgId},'${type}',${id})">
            <div class="k-forward-avatar">${avatar}</div>
            <div class="k-forward-name">${esc(name)}${isSelf ? ' <span style="font-size:11px;color:var(--text-muted)">(Saved)</span>' : ''}</div>
          </div>`;
        }).join('') || '<div class="k-empty">No chats</div>';
      }
    }
  } catch(e) {
    const list = $('forwardChatList');
    if (list) list.innerHTML = '<div class="k-empty">Failed to load chats</div>';
  }
}

K.features._forwardChats = [];

function filterForwardChats(query) {
  const items = document.querySelectorAll('.k-forward-item');
  if (!query.trim()) { items.forEach(i => i.style.display = ''); return; }
  const q = query.toLowerCase();
  items.forEach(i => {
    i.style.display = i.querySelector('.k-forward-name')?.textContent?.toLowerCase()?.includes(q) ? '' : 'none';
  });
}

async function doForward(msgId, targetType, targetId) {
  try {
    const d = await K.api.post(V2 + '/messages/forward', {
      message_id: msgId,
      target_type: targetType,
      target_id: targetId
    });
    if (d.success) {
      K.ui.toast('Forwarded', 'success');
      K.modals.close();
    } else {
      K.ui.toast(d.error?.message || 'Forward failed', 'error');
    }
  } catch(e) { K.ui.toast('Forward error', 'error'); }
}


// ── Enhanced Media Viewer ──────────────────────────────────

K.features._mediaViewerItems = [];
K.features._mediaViewerIdx = 0;

function showMediaViewer(items, startIdx) {
  K.features._mediaViewerItems = items;
  K.features._mediaViewerIdx = startIdx || 0;
  const overlay = $('mediaViewer') || createMediaViewer();
  overlay.style.display = 'flex';
  K.features._renderMediaItem();
}

function createMediaViewer() {
  const div = document.createElement('div');
  div.id = 'mediaViewer';
  div.className = 'k-media-viewer';
  div.innerHTML = `
    <div class="k-media-header">
      <span class="k-media-counter" id="mediaCounter">1/1</span>
      <button class="k-icon-btn" style="color:white" onclick="K.features.closeMediaViewer()"><i class="fas fa-times"></i></button>
    </div>
    <button class="k-media-nav k-media-prev" id="mediaPrev" onclick="K.features.navigateMedia(-1)"><i class="fas fa-chevron-left"></i></button>
    <button class="k-media-nav k-media-next" id="mediaNext" onclick="K.features.navigateMedia(1)"><i class="fas fa-chevron-right"></i></button>
    <div class="k-media-content" id="mediaContent"></div>
    <div class="k-media-footer">
      <a class="k-media-download" id="mediaDownload" download><i class="fas fa-download"></i></a>
    </div>`;
  div.onclick = (e) => { if (e.target === div) K.features.closeMediaViewer(); };
  document.body.appendChild(div);
  return div;
}

function _renderMediaItem() {
  const items = K.features._mediaViewerItems;
  const idx = K.features._mediaViewerIdx;
  const content = $('mediaContent');
  const counter = $('mediaCounter');
  const prev = $('mediaPrev');
  const next = $('mediaNext');
  if (!items.length || !content) return;
  const item = items[idx];
  if (counter) counter.textContent = (idx + 1) + '/' + items.length;
  if (prev) prev.style.display = idx > 0 ? '' : 'none';
  if (next) next.style.display = idx < items.length - 1 ? '' : 'none';
  const isVideo = item.file_type === 'video' || item.file_name?.match(/\.(mp4|webm|avi|mov)$/i);
  const isImage = !isVideo && (item.file_type === 'image' || item.file_url?.match(/\.(jpg|jpeg|png|gif|webp)$/i));
  if (isVideo) {
    content.innerHTML = `<video src="${esc(item.file_url)}" controls autoplay style="max-width:90%;max-height:80vh;border-radius:8px"></video>`;
  } else if (isImage) {
    content.innerHTML = `<div class="k-media-zoom-container"><img src="${esc(item.file_url)}" class="k-media-img" alt="Media"></div>`;
    const img = content.querySelector('.k-media-img');
    if (img) {
      let scale = 1;
      img.onwheel = (e) => {
        e.preventDefault();
        scale = Math.max(0.5, Math.min(5, scale - e.deltaY * 0.001));
        img.style.transform = 'scale(' + scale + ')';
      };
    }
  } else {
    content.innerHTML = `<div style="color:white;text-align:center;padding:40px"><i class="fas fa-file" style="font-size:48px;margin-bottom:12px;display:block"></i>${esc(item.file_name || 'File')}</div>`;
  }
  const dl = $('mediaDownload');
  if (dl) { dl.href = item.file_url || '#'; }
}

function navigateMedia(dir) {
  K.features._mediaViewerIdx += dir;
  K.features._renderMediaItem();
}

function closeMediaViewer() {
  const overlay = $('mediaViewer');
  if (overlay) overlay.style.display = 'none';
}


// ── In-Chat Search ──────────────────────────────────────────

K.features._chatSearchResults = [];
K.features._chatSearchIdx = -1;

function toggleChatSearch() {
  const bar = $('chatSearchBar');
  if (bar) { bar.style.display = bar.style.display === 'flex' ? 'none' : 'flex'; if (bar.style.display === 'flex') { const inp = bar.querySelector('input'); if (inp) { inp.value = ''; inp.focus(); } } }
}

async function searchMessages(query) {
  if (!K.state.activeChat || !query.trim()) return;
  const { type, id } = K.state.activeChat;
  try {
    const d = await K.api.get(V2 + '/messages/search?chat_type=' + type + '&chat_id=' + id + '&q=' + encodeURIComponent(query));
    if (d.success && d.data?.messages?.length) {
      K.features._chatSearchResults = d.data.messages;
      K.features._chatSearchIdx = 0;
      K.features._highlightSearchResults(query);
      K.features._scrollToSearchResult();
    } else {
      K.ui.toast('No results', 'info');
    }
  } catch(e) { K.ui.toast('Search failed', 'error'); }
}

function _highlightSearchResults(query) {
  document.querySelectorAll('.k-msg-text').forEach(el => {
    const text = el.textContent || '';
    if (!query) { el.innerHTML = esc(text); return; }
    const lower = text.toLowerCase();
    const q = query.toLowerCase();
    if (lower.includes(q)) {
      const idx = lower.indexOf(q);
      el.innerHTML = esc(text.substring(0, idx)) + '<mark>' + esc(text.substring(idx, idx + q.length)) + '</mark>' + esc(text.substring(idx + q.length));
    }
  });
}

function _scrollToSearchResult() {
  const msgs = K.features._chatSearchResults;
  const idx = K.features._chatSearchIdx;
  if (!msgs?.length || idx < 0) return;
  const msgId = msgs[idx].message_id || msgs[idx].id;
  const el = document.querySelector(`[data-msg-id="${msgId}"]`);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.style.transition = 'background 0.5s';
    el.style.background = 'var(--accent-blue-translucent)';
    setTimeout(() => { el.style.background = ''; }, 2000);
  }
  const countEl = $('chatSearchCount');
  if (countEl) countEl.textContent = (idx + 1) + '/' + msgs.length;
}

function navigateSearch(dir) {
  const results = K.features._chatSearchResults;
  if (!results?.length) return;
  K.features._chatSearchIdx = Math.max(0, Math.min(results.length - 1, K.features._chatSearchIdx + dir));
  K.features._scrollToSearchResult();
}


// ── Pinned Messages ─────────────────────────────────────────

async function togglePinMessage(msgId, chatType, chatId) {
  try {
    const d = await K.api.post(V2 + '/messages/pin', { message_id: msgId, chat_type: chatType, chat_id: chatId });
    if (d.success) {
      K.ui.toast(d.data?.pinned ? 'Pinned' : 'Unpinned', 'success');
      K.chat.loadMessages(chatType, chatId);
      K.features.loadPinnedMessages(chatType, chatId);
    }
  } catch(e) { K.ui.toast('Failed', 'error'); }
}

async function loadPinnedMessages(chatType, chatId) {
  const bar = $('pinnedBar');
  if (!bar) return;
  try {
    const d = await K.api.get(V2 + '/messages/pinned?chat_type=' + chatType + '&chat_id=' + chatId);
    if (d.success && d.data?.messages?.length) {
      const msgs = d.data.messages;
      bar.style.display = 'flex';
      bar.innerHTML = `<i class="fas fa-thumbtack" style="color:var(--accent-blue);font-size:14px"></i>
        <div class="k-pinned-content">
          <div class="k-pinned-msg" id="pinnedMsgContent">${esc(msgs[0].content?.substring(0, 80) || 'Message')}</div>
        </div>
        <button class="k-icon-btn" style="font-size:12px" onclick="K.features.dismissPinned('${chatType}',${chatId})"><i class="fas fa-times"></i></button>`;
    } else {
      bar.style.display = 'none';
    }
  } catch(e) { bar.style.display = 'none'; }
}

async function dismissPinned(chatType, chatId) {
  const bar = $('pinnedBar');
  if (bar) bar.style.display = 'none';
  try {
    await K.api.post(V2 + '/messages/pinned/dismiss', { chat_type: chatType, chat_id: chatId });
  } catch(e) {}
}


// ── Group Admin Tools ───────────────────────────────────────

async function showGroupManagement(groupId) {
  K.modals.show('groupManage');
  const container = $('modalContent');
  if (!container) return;
  container.innerHTML = `<div class="k-modal-header"><h3>Group Management</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
    <div class="k-modal-body"><div class="k-tabs">
      <button class="k-tab active" onclick="K.features.switchGroupTab('members',this)">Members</button>
      <button class="k-tab" onclick="K.features.switchGroupTab('invites',this)">Invite Links</button>
      <button class="k-tab" onclick="K.features.switchGroupTab('settings',this)">Settings</button>
    </div>
    <div id="groupManageContent">${K.ui.loader()}</div></div>`;
  K.features._currentGroupId = groupId;
  K.features.loadGroupMembers(groupId);
}

let _currentGroupId = null;

async function switchGroupTab(tab, btn) {
  document.querySelectorAll('#groupManageContent ~ .k-tabs .k-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  if (tab === 'members') K.features.loadGroupMembers(K.features._currentGroupId);
  else if (tab === 'invites') K.features.loadGroupInvites(K.features._currentGroupId);
  else if (tab === 'settings') K.features.loadGroupSettings(K.features._currentGroupId);
}

async function loadGroupMembers(groupId) {
  const content = $('groupManageContent');
  if (!content) return;
  content.innerHTML = K.ui.loader();
  try {
    const d = await K.api.get(V2 + '/groups/' + groupId + '/members');
    if (d.success) {
      const members = d.data?.members || [];
      const isAdmin = members.some(m => m.user_id === K.state.user?.user_id && (m.role === 'creator' || m.role === 'admin'));
      content.innerHTML = `<div style="margin-bottom:8px;display:flex;gap:6px">
        <input class="k-input" id="memberSearch" placeholder="Search members..." style="flex:1" oninput="K.features.filterGroupMembers(this.value)">
        ${isAdmin ? `<button class="k-btn k-btn-primary" style="white-space:nowrap" onclick="K.features.showInviteLink(${groupId})"><i class="fas fa-link"></i> Invite</button>` : ''}
      </div>
      <div id="membersList">${members.map(m => {
        const roleIcon = m.role === 'creator' ? '👑' : m.role === 'admin' ? '⭐' : '';
        return `<div class="k-info-row">
          <div class="k-info-avatar">${(m.username||'?')[0].toUpperCase()}</div>
          <div class="k-info-data">
            <div class="k-info-name">${esc(m.username)} ${roleIcon}</div>
            <div class="k-info-role">${m.role||'member'}</div>
          </div>
          ${isAdmin && m.user_id !== K.state.user?.user_id ? `<div class="k-info-actions">
            ${m.role !== 'admin' ? `<button class="k-icon-btn" onclick="K.features.promoteMember(${groupId},${m.user_id})" title="Promote to admin"><i class="fas fa-crown"></i></button>` : `<button class="k-icon-btn" onclick="K.features.demoteMember(${groupId},${m.user_id})" title="Demote"><i class="fas fa-user"></i></button>`}
            <button class="k-icon-btn" onclick="K.features.removeMember(${groupId},${m.user_id})" title="Remove" style="color:var(--accent-red)"><i class="fas fa-times"></i></button>
          </div>` : ''}
        </div>`;
      }).join('')}</div>`;
    }
  } catch(e) { content.innerHTML = '<div class="k-empty">Failed to load members</div>'; }
}

async function loadGroupInvites(groupId) {
  const content = $('groupManageContent');
  if (!content) return;
  content.innerHTML = '<div class="k-loader"></div>';
  try {
    const d = await K.api.get(V2 + '/groups/' + groupId + '/invites');
    if (d.success) {
      const invites = d.data?.invites || [];
      content.innerHTML = `<button class="k-btn k-btn-primary" style="width:100%;margin-bottom:8px;padding:8px" onclick="K.features.createInviteLink(${groupId})"><i class="fas fa-plus"></i> Create invite link</button>
        <div id="inviteLinksList">${invites.map(inv => `<div class="k-invite-link-row">
          <span class="k-invite-link">${esc(inv.link||inv.code)}</span>
          <span style="font-size:11px;color:var(--text-muted)">${inv.uses||0} uses</span>
          <button class="k-icon-btn" onclick="navigator.clipboard.writeText('${esc(inv.link||'')}')"><i class="fas fa-copy"></i></button>
          <button class="k-icon-btn" onclick="K.features.revokeInviteLink(${groupId},'${esc(inv.id||inv.code)}')" style="color:var(--accent-red)"><i class="fas fa-trash"></i></button>
        </div>`).join('') || '<div style="text-align:center;padding:20px;color:var(--text-muted)">No invite links yet</div>'}</div>`;
    }
  } catch(e) { content.innerHTML = '<div class="k-empty">Failed to load invites</div>'; }
}

async function loadGroupSettings(groupId) {
  const content = $('groupManageContent');
  if (!content) return;
  try {
    const d = await K.api.get(V2 + '/groups/' + groupId);
    if (d.success) {
      const g = d.data;
      content.innerHTML = `<div class="k-form-group">
        <label>Group Name</label>
        <input class="k-input" id="groupNameEdit" value="${esc(g.name||'')}">
      </div>
      <div class="k-form-group">
        <label>Description</label>
        <textarea class="k-input" id="groupDescEdit" rows="3">${esc(g.description||'')}</textarea>
      </div>
      <div class="k-form-group" style="flex-direction:row;align-items:center;gap:8px">
        <input type="checkbox" id="groupPublicToggle" ${g.is_public ? 'checked' : ''} style="width:16px;height:16px">
        <label for="groupPublicToggle" style="margin:0">Public group (anyone can join)</label>
      </div>
      <button class="k-btn k-btn-primary" style="width:100%;padding:8px" onclick="K.features.saveGroupSettings(${groupId})"><i class="fas fa-save"></i> Save</button>`;
    }
  } catch(e) { content.innerHTML = '<div class="k-empty">Failed to load settings</div>'; }
}

async function saveGroupSettings(groupId) {
  const name = $('groupNameEdit')?.value?.trim();
  const desc = $('groupDescEdit')?.value?.trim();
  const isPublic = $('groupPublicToggle')?.checked || false;
  if (!name) { K.ui.toast('Name required', 'error'); return; }
  try {
    const d = await K.api.post(V2 + '/groups/' + groupId + '/update', { name, description: desc, is_public: isPublic });
    if (d.success) { K.ui.toast('Settings saved', 'success'); K.chat.loadHeader('group', groupId); }
    else K.ui.toast(d.error?.message || 'Failed', 'error');
  } catch(e) { K.ui.toast('Error saving settings', 'error'); }
}

async function createInviteLink(groupId) {
  try {
    const d = await K.api.post(V2 + '/groups/' + groupId + '/invites/create', {});
    if (d.success) {
      K.ui.toast('Invite link created', 'success');
      K.features.loadGroupInvites(groupId);
    } else K.ui.toast(d.error?.message || 'Failed', 'error');
  } catch(e) { K.ui.toast('Error', 'error'); }
}

async function revokeInviteLink(groupId, linkId) {
  if (!await K.ui.confirm('Revoke this invite link?')) return;
  try {
    const d = await K.api.post(V2 + '/groups/' + groupId + '/invites/revoke', { link_id: linkId });
    if (d.success) {
      K.ui.toast('Link revoked', 'success');
      K.features.loadGroupInvites(groupId);
    }
  } catch(e) { K.ui.toast('Error', 'error'); }
}

async function promoteMember(groupId, userId) {
  try {
    const d = await K.api.post(V2 + '/groups/' + groupId + '/promote', { user_id: userId });
    if (d.success) { K.ui.toast('Promoted', 'success'); K.features.loadGroupMembers(groupId); }
    else K.ui.toast('Failed', 'error');
  } catch(e) { K.ui.toast('Error', 'error'); }
}

async function demoteMember(groupId, userId) {
  try {
    const d = await K.api.post(V2 + '/groups/' + groupId + '/demote', { user_id: userId });
    if (d.success) { K.ui.toast('Demoted', 'success'); K.features.loadGroupMembers(groupId); }
  } catch(e) { K.ui.toast('Error', 'error'); }
}

async function removeMember(groupId, userId) {
  if (!await K.ui.confirm('Remove this member?')) return;
  try {
    const d = await K.api.post(V2 + '/groups/' + groupId + '/remove_member', { user_id: userId });
    if (d.success) { K.ui.toast('Removed', 'success'); K.features.loadGroupMembers(groupId); }
  } catch(e) { K.ui.toast('Error', 'error'); }
}

function filterGroupMembers(query) {
  const items = document.querySelectorAll('#membersList .k-info-row');
  if (!query.trim()) { items.forEach(i => i.style.display = ''); return; }
  const q = query.toLowerCase();
  items.forEach(i => {
    const name = i.querySelector('.k-info-name')?.textContent?.toLowerCase() || '';
    i.style.display = name.includes(q) ? '' : 'none';
  });
}

async function showInviteLink(groupId) {
  try {
    const d = await K.api.post(V2 + '/groups/' + groupId + '/invites/create', {});
    if (d.success && d.data?.link) {
      K.ui.toast('Link: ' + d.data.link, 'success');
      await navigator.clipboard.writeText(d.data.link);
      K.features.loadGroupInvites(groupId);
    }
  } catch(e) { K.ui.toast('Error', 'error'); }
}



// ── Export (original) ─────────────────────────────────

Object.assign(K.features, {
  toggleEmojiPicker, insertEmoji, switchEmojiTab, filterEmoji,
  showGifTab, searchGIF, sendGif,
  showCreatePoll, addPollOption, createPoll, votePoll, renderPoll,
  showForwardDialog, filterForwardChats, doForward,
  showMediaViewer, navigateMedia, closeMediaViewer,
  toggleChatSearch, searchMessages, navigateSearch,
  togglePinMessage, loadPinnedMessages, dismissPinned,
  showGroupManagement, switchGroupTab, loadGroupMembers, loadGroupInvites, loadGroupSettings,
  saveGroupSettings, createInviteLink, revokeInviteLink,
  promoteMember, demoteMember, removeMember, filterGroupMembers, showInviteLink
});


// ── Text Formatting Toolbar ─────────────────────────────

K.features._formatActive = null;

function toggleFormatBar() {
  const bar = $('formatBar');
  if (!bar) return;
  const shown = bar.style.display === 'flex';
  bar.style.display = shown ? 'none' : 'flex';
  if (!shown) {
    const inp = $('messageInput');
    if (inp) { inp.focus(); }
  }
}

function applyFormat(type) {
  const inp = $('messageInput');
  if (!inp) return;
  const start = inp.selectionStart;
  const end = inp.selectionEnd;
  const val = inp.value;
  const selected = val.substring(start, end);
  let wrapped = '';
  switch (type) {
    case 'bold': wrapped = '**' + selected + '**'; break;
    case 'italic': wrapped = '*' + selected + '*'; break;
    case 'underline': wrapped = '__' + selected + '__'; break;
    case 'strike': wrapped = '~~' + selected + '~~'; break;
    case 'mono': wrapped = '`' + selected + '`'; break;
    case 'spoiler': wrapped = '||' + selected + '||'; break;
    case 'blockquote': wrapped = '> ' + selected.replace(/\n/g, '\n> '); break;
    default: return;
  }
  inp.value = val.substring(0, start) + wrapped + val.substring(end);
  inp.selectionStart = inp.selectionEnd = start + wrapped.length;
  inp.focus();
  K.chat.input.handle();
  const bar = $('formatBar');
  if (bar && type !== 'blockquote') bar.style.display = 'none';
}


// ── Schedule Message ────────────────────────────────────

function showSchedulePicker() {
  if (!K.state.activeChat) { K.ui.toast('No active chat', 'error'); return; }
  const now = new Date();
  now.setMinutes(now.getMinutes() + 5);
  const iso = now.toISOString().slice(0, 16);
  K.modals.show('schedule');
  const container = $('modalContent');
  if (!container) return;
  container.innerHTML = `
    <div class="k-modal-header"><h3>Schedule Message</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
    <div class="k-modal-body">
      <div class="k-form-group">
        <label>Send at</label>
        <input class="k-input" type="datetime-local" id="scheduleDate" value="${iso}">
      </div>
      <div class="k-form-group">
        <label>Message</label>
        <textarea class="k-input" id="scheduleMessage" rows="3" placeholder="Your message..."></textarea>
      </div>
    </div>
    <div class="k-modal-footer">
      <button class="k-btn k-btn-secondary" onclick="K.modals.close()">Cancel</button>
      <button class="k-btn k-btn-primary" onclick="K.features.sendScheduled()">Schedule</button>
    </div>`;
}

async function sendScheduled() {
  const dateVal = $('scheduleDate')?.value;
  const msg = $('scheduleMessage')?.value?.trim();
  if (!dateVal || !msg) { K.ui.toast('Fill all fields', 'error'); return; }
  const ts = new Date(dateVal).getTime() / 1000;
  if (ts < Date.now() / 1000 + 60) { K.ui.toast('Must be at least 1 min from now', 'error'); return; }
  const { type, id } = K.state.activeChat;
  try {
    const d = await K.api.post(V2 + '/messages/schedule', { content: msg, chat_id: id, send_at: ts });
    if (d.success) { K.ui.toast('Scheduled ✓', 'success'); K.modals.close(); }
    else K.ui.toast(d.error?.message || 'Failed', 'error');
  } catch(e) { K.ui.toast('Error', 'error'); }
}


// ── Read Receipts ───────────────────────────────────────

async function showReadReceipts(msgId) {
  try {
    const d = await K.api.get(V2 + `/messages/${msgId}/read_by`);
    if (d.success && d.data?.readers?.length) {
      const names = d.data.readers.map(r => r.username).join(', ');
      K.ui.toast('Read by: ' + names, 'info');
    } else {
      K.ui.toast('Not read yet', 'info');
    }
  } catch(e) { /* ignore */ }
}


// ── Contact Sharing ─────────────────────────────────────

async function shareContact(userId) {
  if (!K.state.activeChat) return;
  const { type, id } = K.state.activeChat;
  try {
    const d = await K.api.get(V2 + '/get_user_id/' + userId);
    if (d.success) {
      const user = d.data;
      const content = `👤 ${user.username || user.display_name || 'User'}`;
      const payload = { content, receiver_id: id, file_type: 'contact' };
      await K.api.post(V2 + '/send_message', payload);
      K.ui.toast('Contact shared', 'success');
      K.chat.loadMessages(type, id);
    }
  } catch(e) { K.ui.toast('Error sharing contact', 'error'); }
}


// ── Dice / Random ───────────────────────────────────────

async function sendDice(emoji) {
  if (!K.state.activeChat) return;
  const { type, id } = K.state.activeChat;
  const dice = emoji || ['🎲','🎯','🏀','⚽','🎳','🎰'][Math.floor(Math.random() * 6)];
  const result = Math.floor(Math.random() * 6) + 1;
  const content = `${dice} ${result}`;
  try {
    const payload = { content };
    if (type === 'personal') payload.receiver_id = id;
    else if (type === 'group') payload.group_id = id;
    else if (type === 'channel') payload.channel_id = id;
    const d = await K.api.post(V2 + '/send_message', payload);
    if (d.success) K.chat.loadMessages(type, id);
  } catch(e) { /* ignore */ }
}


// ── Chat Archive / Unarchive ────────────────────────────

async function toggleArchive() {
  if (!K.state.activeChat) return;
  const { type, id } = K.state.activeChat;
  try {
    const d = await K.api.post(V2 + '/chats/' + id + '/archive');
    if (d.success) {
      K.ui.toast(d.data.archived ? 'Archived' : 'Unarchived', 'success');
      K.state.activeChat = null;
      K.chat.loadList();
      document.querySelector('.k-chat-area').style.display = 'none';
    }
  } catch(e) { K.ui.toast('Error', 'error'); }
}


// ── Mute / Unmute ───────────────────────────────────────

async function toggleMute() {
  if (!K.state.activeChat) return;
  const { type, id } = K.state.activeChat;
  try {
    const d = await K.api.post(V2 + '/chats/' + id + '/mute');
    if (d.success) {
      K.ui.toast(d.data.muted ? 'Muted' : 'Unmuted', 'success');
    }
  } catch(e) { K.ui.toast('Error', 'error'); }
}


// ── Chat Theme Picker ───────────────────────────────────

function showThemePicker() {
  if (!K.state.activeChat) return;
  const { type, id } = K.state.activeChat;
  const colors = ['default','#e17076','#7bc862','#e5c77a','#65aadd','#a695e7','#ee7aae','#6ec9c8','#eaa065','#a5a5a5'];
  K.modals.show('theme');
  const container = $('modalContent');
  if (!container) return;
  container.innerHTML = `
    <div class="k-modal-header"><h3>Chat Theme</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
    <div class="k-modal-body">
      <label>Accent Color</label>
      <div class="k-theme-colors">${colors.map(c => `<div class="k-theme-color ${c === 'default' ? 'active' : ''}" style="background:${c === 'default' ? 'var(--accent-blue)' : c}" onclick="K.features.setChatTheme(${id},'${c}')"></div>`).join('')}</div>
      <label style="margin-top:12px;display:block">Auto-Delete Timer</label>
      <select class="k-input" id="autoDeleteSelect" onchange="K.features.setAutoDelete(${id}, this.value)">
        <option value="0">Off</option>
        <option value="86400">24 hours</option>
        <option value="604800">7 days</option>
        <option value="2592000">30 days</option>
      </select>
    </div>`;
}

async function setChatTheme(chatId, color) {
  try {
    const d = await K.api.post(V2 + '/chats/' + chatId + '/theme', { theme_color: color === 'default' ? null : color });
    if (d.success) {
      document.querySelectorAll('.k-theme-color').forEach(el => el.classList.remove('active'));
      event.target.classList.add('active');
      const chat = document.querySelector('.k-chat-area');
      if (chat && color !== 'default') chat.style.setProperty('--chat-accent', color);
      else chat?.style.removeProperty('--chat-accent');
      K.ui.toast('Theme updated', 'success');
    }
  } catch(e) { /* ignore */ }
}

async function setAutoDelete(chatId, ttl) {
  try {
    await K.api.post(V2 + '/chats/' + chatId + '/theme', { auto_delete_ttl: parseInt(ttl) || null });
    K.ui.toast(ttl > 0 ? 'Auto-delete set' : 'Auto-delete off', 'success');
  } catch(e) { /* ignore */ }
}


// ── Hashtag Support ─────────────────────────────────────

document.addEventListener('click', function(e) {
  const hashtag = e.target.closest('.k-msg-hashtag');
  if (hashtag) {
    const tag = hashtag.textContent?.trim();
    if (tag && K.state.activeChat) {
      K.features.searchMessages(tag);
      const bar = $('chatSearchBar');
      if (bar) { bar.style.display = 'flex'; const inp = bar.querySelector('input'); if (inp) inp.value = tag; }
    }
  }
});


// ── Message Translate ──────────────────────────────────

async function translateMessage(msgId, text) {
  const btn = document.querySelector(`[data-msg-id="${msgId}"] .k-translate-btn`);
  if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; btn.disabled = true; }
  try {
    const d = await K.api.post(V2 + '/messages/translate', { text, target_lang: 'en' });
    if (d.success && d.data?.translated) {
      const el = document.querySelector(`[data-msg-id="${msgId}"] .k-msg-text`);
      if (el && !el.dataset.translated) {
        el.dataset.original = el.innerHTML;
        el.innerHTML = esc(d.data.translated);
        el.dataset.translated = '1';
      }
      K.ui.toast('Translated to English', 'success');
    } else { K.ui.toast('Translation failed', 'error'); }
  } catch(e) { K.ui.toast('Translation error', 'error'); }
  if (btn) { btn.innerHTML = '<i class="fas fa-language"></i>'; btn.disabled = false; }
}


// ── Search by Date ─────────────────────────────────────

function showDateSearch() {
  if (!K.state.activeChat) return;
  K.modals.show('dateSearch');
  const container = $('modalContent');
  if (!container) return;
  container.innerHTML = `
    <div class="k-modal-header"><h3>Search by Date</h3><button class="k-modal-close" onclick="K.modals.close()"><i class="fas fa-times"></i></button></div>
    <div class="k-modal-body">
      <div class="k-form-group">
        <label>Date</label>
        <input class="k-input" type="date" id="searchDate">
      </div>
      <button class="k-btn k-btn-primary" style="width:100%;padding:8px" onclick="K.features.searchByDate()"><i class="fas fa-search"></i> Search</button>
      <div id="dateSearchResults" style="margin-top:12px"></div>
    </div>`;
}

async function searchByDate() {
  const dateStr = $('searchDate')?.value;
  if (!dateStr) { K.ui.toast('Select a date', 'error'); return; }
  const { type, id } = K.state.activeChat;
  const resultsEl = $('dateSearchResults');
  if (resultsEl) resultsEl.innerHTML = '<div class="k-loader"></div>';
  try {
    const d = await K.api.get(V2 + '/messages/search_by_date?chat_id=' + id + '&date=' + dateStr);
    if (d.success && d.data?.messages?.length) {
      K.features._chatSearchResults = d.data.messages;
      K.features._chatSearchIdx = 0;
      K.features._highlightSearchResults('');
      K.features._scrollToSearchResult();
      K.modals.close();
    } else {
      if (resultsEl) resultsEl.innerHTML = '<div class="k-empty">No messages on this date</div>';
    }
  } catch(e) {
    if (resultsEl) resultsEl.innerHTML = '<div class="k-empty">Search failed</div>';
  }
}


// ── Delete for Everyone ────────────────────────────────

async function deleteForEveryone(msgId) {
  if (!await K.ui.confirm('Delete this message for everyone?')) return;
  try {
    const d = await K.api.post(V2 + `/messages/${msgId}/delete`, { for_all: true });
    if (d.success && K.state.activeChat) {
      K.chat.loadMessages(K.state.activeChat.type, K.state.activeChat.id);
    }
  } catch(e) { K.ui.toast('Error', 'error'); }
}


// ── Keyboard shortcuts (extended) ─────────────────────

document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'f' && K.state.activeChat) {
    e.preventDefault();
    K.features.toggleChatSearch();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'e' && K.state.activeChat) {
    e.preventDefault();
    K.features.toggleEmojiPicker();
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'F' && K.state.activeChat) {
    e.preventDefault();
    K.features.toggleFormatBar();
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S' && K.state.activeChat) {
    e.preventDefault();
    K.features.showSchedulePicker();
  }
});


// ── Export (extended) ──────────────────────────────────

Object.assign(K.features, {
  toggleFormatBar, applyFormat,
  showSchedulePicker, sendScheduled,
  showReadReceipts,
  shareContact,
  sendDice,
  toggleArchive,
  toggleMute,
  showThemePicker, setChatTheme, setAutoDelete,
  translateMessage,
  showDateSearch, searchByDate,
  deleteForEveryone
});

})();
