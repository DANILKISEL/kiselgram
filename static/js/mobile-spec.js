// static/js/mobile-spec.js — Mobile SPA with native-feeling interactions
(function() {
    'use strict';
    if (window.innerWidth > 768) return;

    var isChatOpen = false;

    // ===== TOAST =====
    window.showMobileToast = function(msg, duration) {
        duration = duration || 2500;
        var existing = document.querySelector('.mobile-toast');
        if (existing) { existing.remove(); }
        var t = document.createElement('div');
        t.className = 'mobile-toast';
        t.textContent = msg;
        document.body.appendChild(t);
        setTimeout(function() {
            t.classList.add('hiding');
            setTimeout(function() { t.remove(); }, 300);
        }, duration);
    };

    // ===== CONNECTION STATUS =====
    (function initConnectionBar() {
        var bar = document.createElement('div');
        bar.id = 'connectionBar';
        document.body.appendChild(bar);
        function update(status) {
            bar.className = status;
            if (status === 'offline') bar.innerHTML = '<i class="fas fa-wifi-slash"></i> No connection';
            else if (status === 'reconnecting') bar.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Reconnecting…';
        }
        if (!navigator.onLine) update('offline');
        window.addEventListener('online', function() {
            bar.className = '';
            setTimeout(function() { showMobileToast('Back online'); }, 400);
        });
        window.addEventListener('offline', function() { update('offline'); });
    })();

    // ===== PANEL HELPERS =====
    function adjustPanels() {
        var navHeight = 60;
        ['contactsView','createGroupView','createChannelView'].forEach(function(id) {
            var el = document.getElementById(id);
            if (el) el.style.bottom = navHeight + 'px';
        });
        var sp = document.getElementById('settingsPanel');
        if (sp) sp.style.bottom = navHeight + 'px';
        var pp = document.getElementById('privacyPanel');
        if (pp) pp.style.bottom = navHeight + 'px';
    }

    function positionStories() {
        var stories = document.getElementById('storiesRow');
        var search = document.querySelector('.global-search-container');
        if (stories && search) {
            search.insertAdjacentElement('afterend', stories);
        }
    }

    // ===== TAB SWITCHING WITH ANIMATION =====
    var navItems = document.querySelectorAll('.bottom-nav-item');
    window.setActiveTab = function(viewId, animate) {
        if (animate === undefined) animate = true;
        if (isChatOpen && viewId === 'chats') { return; }

        navItems.forEach(function(item) { item.classList.toggle('active', item.dataset.view === viewId); });

        var emptyChat = document.getElementById('emptyChat');
        var contactsView = document.getElementById('contactsView');
        var searchCont = document.querySelector('.global-search-container');
        var storiesRow = document.getElementById('storiesRow');

        function hideAll() {
            ['contactsView','createGroupView','createChannelView','chatView'].forEach(function(id) {
                var el = document.getElementById(id);
                if (el) { el.classList.remove('slide-in'); el.classList.add('slide-out'); }
            });
        }

        function showView(el) {
            if (!el) return;
            el.style.display = 'flex';
            el.classList.remove('slide-out');
            el.classList.add('slide-in');
        }

        hideAll();

        if (viewId === 'contacts') {
            isChatOpen = false;
            showView(contactsView);
            if (emptyChat) emptyChat.style.display = 'none';
            if (searchCont) searchCont.style.display = 'none';
            if (storiesRow) storiesRow.style.display = 'none';
        } else if (viewId === 'chats') {
            isChatOpen = false;
            if (emptyChat) emptyChat.style.display = 'flex';
            if (contactsView) contactsView.style.display = 'none';
            if (searchCont) { searchCont.style.display = 'block'; searchCont.classList.remove('active'); }
            if (storiesRow) storiesRow.style.display = 'flex';
            if (typeof window.loadChatList === 'function') window.loadChatList();
        } else if (viewId === 'settings') {
            if (typeof window.openSettingsPanel === 'function') window.openSettingsPanel();
        } else if (viewId === 'search') {
            isChatOpen = false;
            if (emptyChat) emptyChat.style.display = 'flex';
            if (contactsView) contactsView.style.display = 'none';
            if (searchCont) { searchCont.style.display = 'block'; searchCont.classList.add('active'); }
            if (storiesRow) storiesRow.style.display = 'flex';
            var inp = document.getElementById('globalSearchInput');
            if (inp) inp.focus();
        }
        adjustPanels();
    };

    navItems.forEach(function(item) {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            setActiveTab(this.dataset.view);
        });
    });

    document.getElementById('mobileSearchIcon').addEventListener('click', function() {
        var sc = document.querySelector('.global-search-container');
        sc.classList.toggle('active');
        if (sc.classList.contains('active')) {
            document.getElementById('globalSearchInput').focus();
        }
    });

    document.getElementById('contactsBackBtn').addEventListener('click', function() { setActiveTab('chats'); });
    document.getElementById('createGroupBackBtn')?.addEventListener('click', function() { setActiveTab('contacts'); });
    document.getElementById('createChannelBackBtn')?.addEventListener('click', function() { setActiveTab('contacts'); });

    // ===== PULL-TO-REFRESH =====
    (function initPullToRefresh() {
        var container = document.getElementById('emptyChat');
        if (!container) return;
        var ptr = document.createElement('div');
        ptr.id = 'pullToRefresh';
        ptr.innerHTML = '<div class="ptr-spinner"></div><span class="ptr-text"><i class="fas fa-arrow-down"></i> Pull to refresh</span>';
        container.appendChild(ptr);
        var startY = 0, pulling = false, moved = 0;
        container.addEventListener('touchstart', function(e) {
            if (container.scrollTop > 0) return;
            startY = e.touches[0].clientY;
            pulling = true;
            moved = 0;
        }, { passive: true });
        container.addEventListener('touchmove', function(e) {
            if (!pulling) return;
            var dy = e.touches[0].clientY - startY;
            if (dy < 0) { moved = 0; return; }
            moved = dy;
            ptr.style.transform = 'translateY(' + Math.min(dy * 0.4, 60) + 'px)';
        }, { passive: true });
        container.addEventListener('touchend', function() {
            pulling = false;
            if (moved > 80) {
                ptr.classList.add('loading');
                ptr.querySelector('.ptr-text').textContent = 'Refreshing…';
                ptr.style.transform = 'translateY(60px)';
                if (typeof window.loadChatList === 'function') {
                    window.loadChatList().then(function() {
                        ptr.classList.remove('loading');
                        ptr.style.transform = '';
                        setTimeout(function() {
                            ptr.querySelector('.ptr-text').innerHTML = '<i class="fas fa-arrow-down"></i> Pull to refresh';
                        }, 300);
                    })['catch'](function() {
                        ptr.classList.remove('loading');
                        ptr.style.transform = '';
                        ptr.querySelector('.ptr-text').textContent = 'Pull to refresh';
                    });
                } else {
                    ptr.classList.remove('loading');
                    ptr.style.transform = '';
                }
            } else {
                ptr.style.transform = '';
            }
            moved = 0;
        }, { passive: true });
    })();

    // ===== SWIPE GESTURES =====
    function initChatItemSwipe() {
        var list = document.getElementById('mobileChatList');
        if (!list) return;
        list.querySelectorAll('.chat-item').forEach(function(item) {
            if (item.dataset.swipeInit) return;
            item.dataset.swipeInit = '1';

            var actions = document.createElement('div');
            actions.className = 'swipe-actions';
            actions.innerHTML = '\
                <button class="swipe-action-btn pin"><i class="fas fa-thumbtack"></i><span>Pin</span></button>\
                <button class="swipe-action-btn mute"><i class="fas fa-bell-slash"></i><span>Mute</span></button>\
                <button class="swipe-action-btn delete"><i class="fas fa-trash"></i><span>Delete</span></button>';
            item.appendChild(actions);

            var startX = 0, startY = 0, swiping = false;
            item.addEventListener('touchstart', function(e) {
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
                swiping = false;
            }, { passive: true });

            item.addEventListener('touchmove', function(e) {
                var dx = startX - e.touches[0].clientX;
                var dy = Math.abs(e.touches[0].clientY - startY);
                if (dy > Math.abs(dx) * 0.5) return;
                if (dx > 10) {
                    swiping = true;
                    var reveal = Math.min(dx, 216);
                    item.style.transform = 'translateX(' + (-reveal) + 'px)';
                    actions.style.transform = 'translateX(' + (216 - reveal - 216) + 'px)';
                }
            }, { passive: true });

            item.addEventListener('touchend', function() {
                if (!swiping) return;
                var dx = startX - 0;
                var threshold = 80;
                if (Math.abs(item.style.transform.replace(/[^0-9\-]/g, '')) > threshold) {
                    item.classList.add('swiping');
                    item.style.transform = 'translateX(-216px)';
                    actions.style.transform = 'translateX(0)';
                } else {
                    item.style.transform = '';
                    actions.style.transform = '';
                }
                swiping = false;
            }, { passive: true });

            actions.querySelector('.swipe-action-btn.delete').addEventListener('click', function(e) {
                e.stopPropagation();
                var chatId = item.dataset.chatId;
                if (chatId && typeof window.deleteChat === 'function') {
                    window.deleteChat(chatId);
                } else {
                    showMobileToast('Chat deleted');
                }
                item.style.transform = '';
                actions.style.transform = '';
                item.classList.remove('swiping');
            });

            actions.querySelector('.swipe-action-btn.pin').addEventListener('click', function(e) {
                e.stopPropagation();
                var chatId = item.dataset.chatId;
                if (chatId && typeof window.togglePinChat === 'function') {
                    window.togglePinChat(chatId);
                } else {
                    showMobileToast(item.classList.contains('pinned') ? 'Unpinned' : 'Pinned');
                }
                item.style.transform = '';
                actions.style.transform = '';
                item.classList.remove('swiping');
            });

            actions.querySelector('.swipe-action-btn.mute').addEventListener('click', function(e) {
                e.stopPropagation();
                showMobileToast('Chat muted');
                item.style.transform = '';
                actions.style.transform = '';
                item.classList.remove('swiping');
            });

            // Long press context
            var longPressTimer;
            item.addEventListener('touchstart', function() {
                longPressTimer = setTimeout(function() {
                    item.classList.add('pressed');
                }, 400);
            }, { passive: true });
            item.addEventListener('touchend', function() {
                clearTimeout(longPressTimer);
                item.classList.remove('pressed');
            }, { passive: true });
            item.addEventListener('touchmove', function() {
                clearTimeout(longPressTimer);
                item.classList.remove('pressed');
            }, { passive: true });
        });
    }

    // ===== SWIPE TO GO BACK =====
    function initSwipeBack() {
        var chatView = document.getElementById('chatView');
        if (!chatView) return;
        var startX = 0, swiping = false;
        chatView.addEventListener('touchstart', function(e) {
            if (chatView.style.display !== 'flex') return;
            startX = e.touches[0].clientX;
            if (startX < 30) swiping = true;
        }, { passive: true });
        chatView.addEventListener('touchmove', function(e) {
            if (!swiping) return;
            var dx = e.touches[0].clientX - startX;
            if (dx < 0) { swiping = false; return; }
            chatView.style.transform = 'translateX(' + (dx * 0.5) + 'px)';
            chatView.style.opacity = 1 - (dx / 400);
        }, { passive: true });
        chatView.addEventListener('touchend', function() {
            if (!swiping) return;
            var dx = parseInt(chatView.style.transform) || 0;
            if (dx > 80) {
                chatView.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
                chatView.style.transform = 'translateX(100%)';
                chatView.style.opacity = '0';
                setTimeout(function() {
                    chatView.style.display = 'none';
                    chatView.style.transform = '';
                    chatView.style.opacity = '';
                    chatView.style.transition = '';
                    isChatOpen = false;
                    setActiveTab('chats');
                }, 250);
            } else {
                chatView.style.transition = 'transform 0.25s ease, opacity 0.25s ease';
                chatView.style.transform = '';
                chatView.style.opacity = '';
                setTimeout(function() { chatView.style.transition = ''; }, 300);
            }
            swiping = false;
        }, { passive: true });
    }

    // ===== MESSAGE ACTION SHEET =====
    (function initActionSheet() {
        var sheet = document.createElement('div');
        sheet.id = 'messageActionSheet';
        sheet.className = 'message-action-sheet';
        sheet.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:var(--bg-surface);border-radius:20px 20px 0 0;padding:20px;padding-bottom:max(20px,env(safe-area-inset-bottom));z-index:3000;transform:translateY(100%);transition:transform 0.35s cubic-bezier(.4,0,.2,1);box-shadow:0 -4px 20px rgba(0,0,0,0.15);';
        sheet.innerHTML = '\
            <div style="display:flex;flex-direction:column;gap:4px;">\
                <div style="width:36px;height:4px;background:var(--border-color);border-radius:4px;margin:0 auto 12px;flex-shrink:0;"></div>\
                <button class="action-sheet-btn" data-action="reply"><i class="fas fa-reply"></i> Reply</button>\
                <button class="action-sheet-btn" data-action="forward"><i class="fas fa-share"></i> Forward</button>\
                <button class="action-sheet-btn" data-action="react"><i class="fas fa-smile"></i> React</button>\
                <button class="action-sheet-btn" data-action="copy"><i class="fas fa-copy"></i> Copy</button>\
                <button class="action-sheet-btn" data-action="delete" style="color:var(--accent-red);"><i class="fas fa-trash" style="color:var(--accent-red);"></i> Delete</button>\
                <button class="action-sheet-btn" data-action="cancel" style="margin-top:8px;justify-content:center;color:var(--text-muted);font-weight:600;">Cancel</button>\
            </div>';
        document.body.appendChild(sheet);

        var overlay = document.createElement('div');
        overlay.className = 'action-sheet-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.4);z-index:2999;display:none;-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px);';
        document.body.appendChild(overlay);

        var curMsgId = null, curContent = '';

        function show(msgId, content, isOwn) {
            curMsgId = msgId; curContent = content;
            var del = sheet.querySelector('[data-action="delete"]');
            if (del) del.style.display = isOwn ? 'flex' : 'none';
            var react = sheet.querySelector('[data-action="react"]');
            if (react) react.style.display = window.isPremium ? 'flex' : 'none';
            overlay.style.display = 'block';
            requestAnimationFrame(function() { sheet.style.transform = 'translateY(0)'; });
        }

        function hide() {
            sheet.style.transform = 'translateY(100%)';
            overlay.style.display = 'none';
            curMsgId = null;
        }

        overlay.addEventListener('click', hide);
        sheet.addEventListener('click', function(e) {
            var btn = e.target.closest('[data-action]');
            if (!btn) return;
            var action = btn.dataset.action;
            if (action === 'cancel') { hide(); return; }
            if (!curMsgId) return;
            switch(action) {
                case 'reply':
                    if (typeof window.setReply === 'function') window.setReply(curMsgId);
                    break;
                case 'forward':
                    if (typeof window.showForwardModal === 'function') window.showForwardModal(curMsgId);
                    else showMobileToast('Forward not available');
                    break;
                case 'react':
                    if (typeof window.showReactionPicker === 'function') window.showReactionPicker(curMsgId);
                    else showMobileToast('Reactions require Premium');
                    break;
                case 'copy':
                    navigator.clipboard?.writeText(curContent).then(function() { showMobileToast('Copied!'); });
                    break;
                case 'delete':
                    if (confirm('Delete this message?')) {
                        if (typeof window.deleteMessage === 'function') window.deleteMessage(curMsgId);
                    }
                    break;
            }
            hide();
        });

        window.showMessageActions = show;

        function attach() {
            var container = document.getElementById('messagesContainer');
            if (!container) return;
            container.addEventListener('contextmenu', function(e) { e.preventDefault(); });
            container.addEventListener('click', function(e) {
                var bubble = e.target.closest('.message-bubble');
                if (!bubble) return;
                var wrapper = bubble.closest('.message-wrapper');
                if (!wrapper) return;
                var msgId = wrapper.id.replace('msg-', '');
                var textEl = bubble.querySelector('.message-text');
                var content = textEl ? textEl.innerText : '';
                var isOwn = wrapper.classList.contains('outgoing');
                show(msgId, content, isOwn);
            });
        }

        var origLoad = window.loadMessages;
        if (origLoad) {
            window.loadMessages = function(type, id) {
                return origLoad.call(this, type, id).then(function() {
                    attach();
                    return Promise.resolve();
                })['catch'](function(e) {
                    console.error('Failed to load messages:', e);
                    var container = document.getElementById('messagesContainer');
                    if (container) {
                        container.innerHTML = '<div class="empty-state"><div class="empty-icon"><i class="fas fa-exclamation-triangle"></i></div><p>Failed to load messages</p><button class="modal-btn modal-btn-primary" onclick="window.loadMessages(\'' + type + '\',' + id + ')">Retry</button></div>';
                    }
                });
            };
        }

        document.addEventListener('DOMContentLoaded', attach);
    })();

    // ===== OVERRIDE OPEN CHAT =====
    var origOpenChat = window.openChat;
    window.openChat = async function(type, id) {
        if (origOpenChat) {
            try { await origOpenChat.call(this, type, id); } catch (e) { console.error('openChat error:', e); }
        }
        document.getElementById('emptyChat').style.display = 'none';
        document.getElementById('contactsView').style.display = 'none';
        document.querySelector('.global-search-container').style.display = 'none';
        document.getElementById('storiesRow').style.display = 'none';
        var cv = document.getElementById('chatView');
        cv.style.display = 'flex';
        cv.style.transform = 'translateX(100%)';
        cv.style.opacity = '0';
        cv.style.transition = 'none';
        requestAnimationFrame(function() {
            cv.style.transition = 'transform 0.3s cubic-bezier(.4,0,.2,1), opacity 0.25s ease';
            cv.style.transform = '';
            cv.style.opacity = '';
            setTimeout(function() { cv.style.transition = ''; }, 350);
        });
        addBackButton();
        isChatOpen = true;
        navItems.forEach(function(item) { item.classList.toggle('active', item.dataset.view === 'chats'); });
        adjustPanels();
    };

    var origShowChats = window.showChatsView;
    window.showChatsView = function() {
        if (isChatOpen) {
            var cv = document.getElementById('chatView');
            cv.style.transition = 'transform 0.25s ease, opacity 0.25s ease';
            cv.style.transform = 'translateX(100%)';
            cv.style.opacity = '0';
            setTimeout(function() {
                cv.style.display = 'none';
                cv.style.transform = '';
                cv.style.opacity = '';
                cv.style.transition = '';
                isChatOpen = false;
            }, 250);
            return;
        }
        if (origShowChats) origShowChats.call(this);
        setActiveTab('chats');
    };

    var origHideContacts = window.hideContactsView;
    window.hideContactsView = function() {
        if (origHideContacts) origHideContacts.call(this);
        setActiveTab('chats');
    };

    // ===== BACK BUTTON =====
    function addBackButton() {
        var left = document.querySelector('#chatView .chat-header-left');
        if (left && !document.getElementById('mobileBackBtn')) {
            var btn = document.createElement('button');
            btn.id = 'mobileBackBtn';
            btn.innerHTML = '<i class="fas fa-arrow-left"></i>';
            btn.setAttribute('aria-label', 'Back');
            btn.onclick = function() {
                var cv = document.getElementById('chatView');
                cv.style.transition = 'transform 0.25s ease, opacity 0.25s ease';
                cv.style.transform = 'translateX(100%)';
                cv.style.opacity = '0';
                setTimeout(function() {
                    cv.style.display = 'none';
                    cv.style.transform = '';
                    cv.style.opacity = '';
                    cv.style.transition = '';
                    isChatOpen = false;
                    setActiveTab('chats');
                }, 250);
            };
            left.prepend(btn);
        }
    }

    // ===== CHAT LIST SYNC =====
    function syncChatList() {
        var real = document.getElementById('chatList');
        var mobile = document.getElementById('mobileChatList');
        if (!real || !mobile) return;

        // Show skeletons while loading
        if (!real.querySelector('.chat-item')) {
            var skeletonHTML = '';
            for (var i = 0; i < 8; i++) {
                skeletonHTML += '\
                    <div class="chat-item" style="display:flex;align-items:center;gap:12px;padding:12px 16px;">\
                        <div class="skeleton skeleton-avatar"></div>\
                        <div style="flex:1;min-width:0;">\
                            <div class="skeleton skeleton-line short"></div>\
                            <div class="skeleton skeleton-line"></div>\
                        </div>\
                    </div>';
            }
            mobile.innerHTML = skeletonHTML;
        }

        var checkInterval = setInterval(function() {
            if (real.querySelector('.chat-item')) {
                clearInterval(checkInterval);
                mobile.innerHTML = real.innerHTML;
                mobile.querySelectorAll('.chat-item').forEach(function(item) {
                    var type = item.dataset.chatType;
                    var id = item.dataset.chatId;
                    if (type && id) {
                        item.onclick = function() { window.openChat(type, parseInt(id)); };
                    }
                });
                initChatItemSwipe();
            }
        }, 100);

        setTimeout(function() { clearInterval(checkInterval); }, 5000);
    }

    var origLoadChatList = window.loadChatList;
    if (origLoadChatList) {
        window.loadChatList = async function() {
            await origLoadChatList.apply(this, arguments);
            syncChatList();
        };
    }

    var customizeBtn = document.getElementById('chatCustomizeBtn');
    if (customizeBtn) {
        customizeBtn.onclick = typeof window.openChatCustomization === 'function'
            ? window.openChatCustomization
            : function() { window.showPremiumModal?.('wallpapers'); };
    }

    // ===== PROFILE & CREATE BUTTONS =====
    function addProfileButton() {
        var content = document.querySelector('.settings-content');
        if (content && !document.getElementById('mobileProfileBtn')) {
            var section = document.createElement('div');
            section.className = 'settings-section';
            section.innerHTML = '<h3>Account</h3><button id="mobileProfileBtn" class="profile-action-btn" style="width:100%;justify-content:center;"><i class="fas fa-user"></i><span>View / Edit Profile</span></button>';
            content.appendChild(section);
            document.getElementById('mobileProfileBtn').onclick = function() {
                if (typeof window.openProfileModal === 'function') window.openProfileModal();
                if (typeof window.closeSettingsPanel === 'function') window.closeSettingsPanel();
            };
        }
    }

    function addCreateButtons() {
        var header = document.querySelector('#contactsView .panel-header');
        if (header && !document.getElementById('mobileCreateGroupBtn')) {
            var div = document.createElement('div');
            div.style.display = 'flex'; div.style.gap = '8px';
            div.innerHTML = '\
                <button id="mobileCreateGroupBtn" class="header-action-btn" title="Create Group"><i class="fas fa-users"></i></button>\
                <button id="mobileCreateChannelBtn" class="header-action-btn" title="Create Channel"><i class="fas fa-bullhorn"></i></button>';
            var existing = header.querySelector('.header-action-btn');
            if (existing) existing.insertAdjacentElement('afterend', div);
            else header.appendChild(div);
            document.getElementById('mobileCreateGroupBtn').onclick = function() { window.showCreateGroupView?.(); };
            document.getElementById('mobileCreateChannelBtn').onclick = function() { window.showCreateChannelView?.(); };
        }
    }

    // ===== INIT =====
    function init() {
        positionStories();
        adjustPanels();
        addProfileButton();
        addCreateButtons();
        setActiveTab('chats', false);
        initSwipeBack();

        setTimeout(function() { syncChatList(); }, 100);
        setTimeout(function() { syncChatList(); }, 500);
        setTimeout(function() { syncChatList(); }, 1500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    new MutationObserver(function() {
        if (document.getElementById('chatView')?.style.display === 'flex') {
            addBackButton();
        }
    }).observe(document.body, { childList: true, subtree: true });

    window.togglePopoutMenu = window.closePopout = function() {};
})();
