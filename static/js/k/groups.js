K.groups = {
  async create() {
    const name = $('groupNameInput')?.value?.trim();
    if (!name) { K.ui.toast('Group name required', 'error'); return; }
    try {
      const d = await K.api.post(V2 + '/groups/create', {name, member_ids: K.modals._groupMemberIds});
      if (d.success) {
        K.ui.toast('Group created', 'success'); K.modals.close();
        K.modals._groupMemberIds = []; K.modals._groupMemberNames = [];
        K.chat.loadList();
      } else { K.ui.toast('Failed', 'error'); }
    } catch(e) { K.ui.toast('Failed to create group', 'error'); }
  }
};
