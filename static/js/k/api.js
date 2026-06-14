K.api = {
  _headers(extra) {
    const h = {...extra};
    try {
      const acc = K.auth.accounts[K.auth.activeIdx];
      if (acc && acc.token) h['Authorization'] = 'Bearer ' + acc.token;
    } catch(_) {}
    return h;
  },
  async _fetch(url, opts) {
    const r = await fetch(url, opts);
    if (r.ok) return r.json();
    let body;
    try { body = await r.json(); } catch(e) { body = {}; }
    const err = new Error(body?.error?.message || `HTTP ${r.status}`);
    err.status = r.status;
    err.body = body;
    throw err;
  },
  async get(url) { return this._fetch(url, {headers: this._headers()}); },
  async post(url, body) {
    const isForm = body instanceof FormData;
    const h = this._headers(isForm ? {} : {'Content-Type':'application/json'});
    return this._fetch(url, { method: 'POST', headers: h, body: isForm ? body : JSON.stringify(body) });
  },
  async put(url, body) { return this._fetch(url, { method: 'PUT', headers: this._headers({'Content-Type':'application/json'}), body: JSON.stringify(body) }); },
  async del(url) { return this._fetch(url, {method: 'DELETE', headers: this._headers()}); },
  async delete(url) { return this.del(url); }
};
