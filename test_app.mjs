import { chromium } from 'playwright';
const BASE = 'http://127.0.0.1:8080';

async function test() {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  let ok = 0, fail = 0;

  async function req(method, url, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.data = body;
    try {
      const resp = await page.request.fetch(url, opts);
      const text = await resp.text();
      const status = resp.status();
      console.log(`  ${status} ${method} ${url} -> ${text.slice(0,100)}`);
      if (status >= 200 && status < 400) ok++; else fail++;
      return { status, text, json: () => { try { return JSON.parse(text); } catch { return null; } } };
    } catch (e) {
      console.log(`  ERR ${method} ${url} -> ${e.message}`);
      fail++;
      return null;
    }
  }

  // 1. Health check
  console.log('\n--- Health ---');
  await req('GET', `${BASE}/health`);

  // 2. Auth & get token
  console.log('\n--- Auth (auth.kiselgram.ru on 8081) ---');
  const AUTH = 'http://127.0.0.1:8081';
  let token = null;
  const regResp = await req('POST', `${AUTH}/api/register`, { username: 'playwright', password: 'test123', confirm_password: 'test123' });
  if (regResp) {
    const rj = regResp.json();
    if (rj && rj.token) token = rj.token;
  }
  if (!token) {
    const loginResp = await req('POST', `${AUTH}/api/login`, { username: 'playwright', password: 'test123' });
    if (loginResp) {
      const lj = loginResp.json();
      if (lj && lj.token) token = lj.token;
    }
  }
  console.log('  Token:', token ? token.slice(0, 30) + '...' : 'NONE');

  const auth = token ? { 'Authorization': `Bearer ${token}` } : {};

  async function aReq(method, url, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json', ...auth } };
    if (body) opts.data = body;
    try {
      const resp = await page.request.fetch(url, opts);
      const text = await resp.text();
      const status = resp.status();
      console.log(`  ${status} ${method} ${url} -> ${text.slice(0,120)}`);
      if (status >= 200 && status < 400) ok++; else fail++;
      return { status, text, json: () => { try { return JSON.parse(text); } catch { return null; } } };
    } catch (e) {
      console.log(`  ERR ${method} ${url} -> ${e.message}`);
      fail++;
      return null;
    }
  }

  if (!token) {
    console.log('  No token - skipping authed tests');
  } else {
    // 3. Profile
    console.log('\n--- Profile ---');
    await aReq('GET', `${BASE}/api/profile`);
    await aReq('PUT', `${BASE}/api/profile`, { first_name: 'Playwright', last_name: 'Test', bio: 'Testing!' });
    await aReq('GET', `${BASE}/api/profile/settings`);
    await aReq('PUT', `${BASE}/api/profile/settings`, { theme: 'dark', language: 'en' });
    await aReq('PUT', `${BASE}/api/profile/privacy`, { show_status: false, show_online: false });
    await aReq('PUT', `${BASE}/api/profile/notifications`, { messages: true, groups: false });

    // 4. Sessions
    console.log('\n--- Sessions ---');
    await aReq('GET', `${BASE}/api/sessions`);

    // 5. Contacts
    console.log('\n--- Contacts ---');
    await aReq('GET', `${BASE}/api/contacts`);
    await aReq('GET', `${BASE}/api/blocked_users`);

    // 6. Premium
    console.log('\n--- Premium ---');
    await aReq('GET', `${BASE}/api/premium`);
    await aReq('POST', `${BASE}/api/premium/subscribe`, { plan: 'monthly' });

    // 7. Polls
    console.log('\n--- Polls ---');
    const pollCreate = await aReq('POST', `${BASE}/api/polls/create`, { question: 'Best language?', options: ['Java', 'Python', 'Kotlin'] });
    let pollId = null;
    if (pollCreate) { const pj = pollCreate.json(); if (pj && pj.id) pollId = pj.id; }
    if (pollId) {
      await aReq('POST', `${BASE}/api/polls/vote`, { poll_id: pollId, option_index: 0 });
      await aReq('GET', `${BASE}/api/polls/${pollId}/results`);
    }

    // 8. Stories
    console.log('\n--- Stories ---');
    await aReq('GET', `${BASE}/api/stories`);
    const storyCreate = await aReq('POST', `${BASE}/api/stories/upload`, { file_path: '/test/story.jpg', type: 'image' });
    let storyId = null;
    if (storyCreate) { const sj = storyCreate.json(); if (sj && sj.id) storyId = sj.id; }
    if (storyId) {
      await aReq('POST', `${BASE}/api/stories/${storyId}/reaction`, { emoji: '🔥' });
      await aReq('POST', `${BASE}/api/stories/${storyId}/reply`, { text: 'Nice story!' });
      await aReq('GET', `${BASE}/api/stories/${storyId}/stats`);
      await aReq('DELETE', `${BASE}/api/stories/${storyId}`);
    }

    // 9. Invite links
    console.log('\n--- Invite Links ---');
    await aReq('POST', `${BASE}/api/groups/1/invites`, {});
    await aReq('GET', `${BASE}/api/groups/1/invites`);

    // 10. Message pins
    console.log('\n--- Message Pins ---');
    await aReq('POST', `${BASE}/api/messages/pin`, { message_id: 1 });
    await aReq('GET', `${BASE}/api/messages/pinned`);
    await aReq('POST', `${BASE}/api/messages/pin/dismiss`);

    // 11. Read receipts
    console.log('\n--- Read Receipts ---');
    await aReq('POST', `${BASE}/api/messages/1/read`, {});
    await aReq('GET', `${BASE}/api/messages/1/read_by`);

    // 12. Group permissions
    console.log('\n--- Group Permissions ---');
    await aReq('GET', `${BASE}/api/groups/1/permissions`);
    await aReq('POST', `${BASE}/api/groups/1/permissions`, { send_messages: true, send_media: false });

    // 13. Recent searches
    console.log('\n--- Recent Searches ---');
    await aReq('POST', `${BASE}/api/recent_searches`, { query: 'hello world' });
    await aReq('GET', `${BASE}/api/recent_searches`);
    await aReq('DELETE', `${BASE}/api/recent_searches`);

    // 14. Referrals
    console.log('\n--- Referrals ---');
    await aReq('GET', `${BASE}/api/referrals/code`);
    await aReq('GET', `${BASE}/api/referrals/count`);

    // 15. Features
    console.log('\n--- Features ---');
    await aReq('GET', `${BASE}/api/features`);

    // 16. Push subscriptions
    console.log('\n--- Push ---');
    await aReq('POST', `${BASE}/api/push/subscribe`, { endpoint: 'https://example.com/push', keys: { p256dh: 'key', auth: 'auth' } });
    await aReq('GET', `${BASE}/api/push/vapid_public_key`);
    await aReq('DELETE', `${BASE}/api/push/unsubscribe`);

    // 17. Preloaded avatars
    console.log('\n--- Preloaded ---');
    await aReq('GET', `${BASE}/api/preloaded/avatars`);

    // 18. Calls
    console.log('\n--- Calls ---');
    await aReq('GET', `${BASE}/api/calls`);

    // 19. Favorites
    console.log('\n--- Favorites ---');
    await aReq('GET', `${BASE}/api/favorites`);
  }

  console.log(`\n=== RESULTS: ${ok} OK, ${fail} FAIL ===`);
  await browser.close();
}

test().catch(e => { console.error(e); process.exit(1); });
