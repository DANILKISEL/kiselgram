'use strict';

const MD_TAGS = new Set(['b','i','u','s','strong','em','del','ins','mark','code','pre','a','br','p','ul','ol','li','blockquote','h1','h2','h3','h4','hr','sub','sup','small','span']);

K.markdown = {

  render(text) {
    if (!text) return '';

    // Phase 1: Markdown → safe HTML
    let html = text;

    // Code block first (```...```)
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
      return '<pre><code class="k-copy-code">' + esc(code.trim()) + '</code></pre>';
    });

    // Inline code (`...`)
    html = html.replace(/`([^`]+)`/g, (_, c) => '<code class="k-copy-code">' + esc(c) + '</code>');

    // Bold **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic *text*
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Underline __text__ (but avoid treating __ as strikethrough conflict)
    html = html.replace(/__([^_]+?)__/g, '<u>$1</u>');

    // Strikethrough ~~text~~
    html = html.replace(/~~(.+?)~~/g, (_, t) => '<del>' + t + '</del>');

    // Spoiler ||text||
    html = html.replace(/\|\|(.+?)\|\|/g, (_, t) => '<span class="k-spoiler">' + esc(t) + '</span>');

    // Blockquote > text
    html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

    // Hashtags #hashtag
    html = html.replace(/(^|\s)(#[a-zA-Zа-яА-Я0-9_]+)/g, (_, before, tag) => {
      return before + '<span class="k-msg-hashtag">' + tag + '</span>';
    });

    // Highlight ==text==
    html = html.replace(/==(.+?)==/g, (_, t) => '<mark>' + t + '</mark>');

    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, t, u) => {
      const url = u.trim();
      if (!url.startsWith('http://') && !url.startsWith('https://')) return _;
      return '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(t) + '</a>';
    });

    // Auto-link bare URLs
    html = html.replace(/(^|\s)(https?:\/\/[^\s<]+)/g, (_, before, url) => {
      return before + '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(url) + '</a>';
    });

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    // Phase 2: Sanitize — allow only safe tags, strip all attributes on raw HTML tags
    html = html.replace(/<(\/?)([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>/g, (match, slash, tag, attrs) => {
      const lower = tag.toLowerCase();
      if (!MD_TAGS.has(lower)) return esc(match);
      // Keep href on <a>, keep class on <span>, strip everything else
      if (lower === 'a' && !slash) {
        const h = attrs.match(/href="([^"]*)"/);
        if (h) return '<a href="' + esc(h[1]) + '" target="_blank" rel="noopener noreferrer">';
        return '<a>';
      }
      if (lower === 'span' && !slash) {
        const c = attrs.match(/class="([^"]*)"/);
        if (c) return '<span class="' + esc(c[1]) + '">';
        return '<span>';
      }
      return '<' + slash + lower + '>';
    });

    return html;
  },

  strip(text) {
    if (!text) return '';
    return text
      .replace(/```[\s\S]*?```/g, '')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/__(.+?)__/g, '$1')
      .replace(/~~(.+?)~~/g, '$1')
      .replace(/\|\|(.+?)\|\|/g, '$1')
      .replace(/==(.+?)==/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/<\/?[a-zA-Z][a-zA-Z0-9]*\b[^>]*>/g, '')
      .replace(/\n/g, ' ')
      .substring(0, 80);
  }
};
