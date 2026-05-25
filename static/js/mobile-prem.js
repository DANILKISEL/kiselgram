// static/js/mobile-prem.js — Premium mobile extensions
// This extends mobile-spec.js with premium-only features.
// mobile-spec.js must be loaded before this file.

(function() {
    'use strict';
    if (window.innerWidth > 768) return;

    // Story viewer integration for premium users
    var origOpen = window.openStoryViewer;
    if (origOpen) {
        window.openStoryViewer = function(uid) {
            origOpen.call(this, uid);
            document.body.classList.add('story-viewer-open');
            var nav = document.querySelector('.mobile-bottom-nav');
            if (nav) nav.style.display = 'none';
        };
    }
    var origClose = window.closeStoryViewer;
    if (origClose) {
        window.closeStoryViewer = function() {
            origClose.call(this);
            document.body.classList.remove('story-viewer-open');
            var nav = document.querySelector('.mobile-bottom-nav');
            if (nav) nav.style.display = 'flex';
        };
    }
})();
