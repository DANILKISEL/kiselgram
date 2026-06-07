K.admin = {
  _filter: 'pending',
  async init() {
    try {
      const d = await K.api.get(V2 + '/profile');
      if (d.success && d.data?.is_admin) {
        const btn = $('adminTabBtn');
        if (btn) btn.style.display = '';
        K.admin.loadDashboard();
        K.admin.loadReports();
        K.admin.loadUsers();
      }
    } catch(e) {}
  },
  async loadDashboard() {
    const el = $('adminDashboard'); if (!el) return;
    try {
      const d = await K.api.get('/api/admin/dashboard');
      if (d.success && d.data) {
        el.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px">
          <div class="k-stat-card"><div class="k-stat-number">${d.data.total_users}</div><div class="k-stat-label">Total Users</div></div>
          <div class="k-stat-card"><div class="k-stat-number">${d.data.pending_reports}</div><div class="k-stat-label">Pending Reports</div></div>
          <div class="k-stat-card"><div class="k-stat-number">${d.data.total_reports}</div><div class="k-stat-label">Total Reports</div></div>
          <div class="k-stat-card"><div class="k-stat-number">${d.data.users_today}</div><div class="k-stat-label">New Today</div></div>
        </div>`;
      }
    } catch(e) { el.innerHTML = '<div style="color:var(--text-muted)">Failed to load</div>'; }
  },
  filterReports(status) {
    K.admin._filter = status;
    document.querySelectorAll('#reportsList ~ [data-status]').forEach(b => b.classList.toggle('active', b.dataset.status === status));
    K.admin.loadReports();
  },
  async loadReports() {
    const el = $('reportsList'); if (!el) return;
    el.innerHTML = K.ui.loader();
    try {
      const d = await K.api.get('/api/admin/reports?status=' + K.admin._filter);
      if (!d.success) { el.innerHTML = '<div style="color:var(--text-muted);padding:12px">Failed to load reports</div>'; return; }
      const reports = d.data?.reports || [];
      if (!reports.length) { el.innerHTML = '<div style="color:var(--text-muted);padding:12px">No reports found</div>'; return; }
      el.innerHTML = reports.map(r => `
        <div class="k-settings-item" style="flex-direction:column;align-items:stretch;gap:8px;padding:12px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div style="font-size:13px;font-weight:600">#${r.id}</div>
            <span style="font-size:11px;color:var(--text-muted)">${r.created_at ? fmtTime(r.created_at) : ''}</span>
          </div>
          <div style="font-size:12px;color:var(--text-muted)">
            <div>From: <strong>${esc(r.reported_username||'User #'+r.reporter_id)}</strong></div>
            <div>About: <strong>${esc(r.reported_username||'User #'+r.reported_user_id)}</strong></div>
            ${r.reported_message_id ? '<div>Message: <a href="#" onclick="event.preventDefault();K.ui.toast(\'Open chat to view message #'+r.reported_message_id+'\',\'info\')">#'+r.reported_message_id+'</a></div>' : ''}
          </div>
          <div style="font-size:13px">${esc(r.reason)}</div>
          <div style="font-size:11px;color:var(--text-muted)">Status: ${esc(r.status)}</div>
          ${r.status === 'pending' ? `
          <div style="display:flex;gap:4px;flex-wrap:wrap">
            <button class="k-btn k-btn-primary" style="font-size:11px;padding:4px 8px" onclick="K.admin.resolveReport(${r.id})">Resolve</button>
            <button class="k-btn k-btn-secondary" style="font-size:11px;padding:4px 8px" onclick="K.admin.dismissReport(${r.id})">Dismiss</button>
            <button class="k-btn" style="font-size:11px;padding:4px 8px;background:var(--accent-red);color:white;border:none;border-radius:8px;cursor:pointer" onclick="K.admin.actionReport(${r.id},${r.reported_user_id},'warn')">Warn</button>
            ${r.reported_message_id ? `<button class="k-btn" style="font-size:11px;padding:4px 8px;background:var(--accent-orange);color:white;border:none;border-radius:8px;cursor:pointer" onclick="K.admin.actionReport(${r.id},${r.reported_user_id},'delete_message')">Delete Msg</button>` : ''}
            <button class="k-btn" style="font-size:11px;padding:4px 8px;background:#dc2626;color:white;border:none;border-radius:8px;cursor:pointer" onclick="K.admin.actionReport(${r.id},${r.reported_user_id},'ban_user')">Ban User</button>
          </div>` : ''}
        </div>
      `).join('');
    } catch(e) { el.innerHTML = '<div style="color:var(--text-muted)">Error loading reports</div>'; }
  },
  async resolveReport(id) {
    try {
      const d = await K.api.post('/api/admin/reports/' + id + '/resolve');
      if (d.success) { K.ui.toast('Report resolved', 'success'); K.admin.loadReports(); }
      else { K.ui.toast('Failed', 'error'); }
    } catch(e) { K.ui.toast('Error', 'error'); }
  },
  async dismissReport(id) {
    try {
      const d = await K.api.post('/api/admin/reports/' + id + '/dismiss');
      if (d.success) { K.ui.toast('Report dismissed', 'success'); K.admin.loadReports(); }
      else { K.ui.toast('Failed', 'error'); }
    } catch(e) { K.ui.toast('Error', 'error'); }
  },
  async actionReport(id, userId, actionType) {
    if (!K.ui.confirm('Take action: ' + actionType + '?')) return;
    try {
      const d = await K.api.post('/api/admin/reports/' + id + '/action', {action_type: actionType, user_id: userId});
      if (d.success) { K.ui.toast('Action applied', 'success'); K.admin.loadReports(); }
      else { K.ui.toast('Failed', 'error'); }
    } catch(e) { K.ui.toast('Error', 'error'); }
  },
  async loadUsers() {
    const el = $('adminUsersList'); if (!el) return;
    el.innerHTML = K.ui.loader();
    try {
      const d = await K.api.get('/api/admin/users?page=1');
      if (!d.success) { el.innerHTML = '<div style="color:var(--text-muted);padding:12px">Failed</div>'; return; }
      const users = d.data?.users || [];
      el.innerHTML = users.map(u => `
        <div class="k-settings-item" style="padding:8px 12px">
          <span><strong>${esc(u.username)}</strong>${u.is_admin ? ' <span style="color:var(--accent-blue);font-size:11px">admin</span>' : ''}${u.is_bot ? ' <span style="color:var(--accent-green);font-size:11px">bot</span>' : ''}<br><span style="font-size:11px;color:var(--text-muted)">${u.email||'no email'} • ${u.is_online ? '<span style="color:var(--online-green)">online</span>' : 'offline'} • ${u.email_verified ? 'verified' : 'unverified'}</span></span>
          <button class="k-icon-btn" style="font-size:14px;width:28px;height:28px" onclick="K.admin.toggleAdmin(${u.id})" title="Toggle admin"><i class="fas fa-shield-alt"></i></button>
        </div>
      `).join('');
    } catch(e) { el.innerHTML = '<div style="color:var(--text-muted)">Error</div>'; }
  },
  async toggleAdmin(userId) {
    try {
      const d = await K.api.post('/api/admin/users/' + userId + '/toggle-admin');
      if (d.success) { K.ui.toast('Admin toggled', 'success'); K.admin.loadUsers(); }
    } catch(e) {}
  }
};
