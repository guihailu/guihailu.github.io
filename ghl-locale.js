(() => {
  'use strict';
  const languages = ['zh-Hant', 'zh-Hans', 'en'];
  const copy = window.GHL_COPY || {};
  const skip = 'script,style,noscript,template,textarea,select:not(#cat-series),pre,code,svg,[aria-hidden="true"],[data-ghl-ui]';
  const attributes = ['alt', 'aria-label', 'placeholder', 'title'];
  const originals = new WeakMap();
  const grouped = new WeakMap();
  const title = document.title;
  let active = 'zh-Hant';
  let observer;
  let picker;
  let notice;
  const normalize = value => value.trim().replace(/\s+/g, ' ');
  function row(value) { return Object.hasOwn(copy, normalize(value)) ? copy[normalize(value)] : null; }
  function phrase(value) {
    const text = normalize(value);
    const record = row(text);
    if (record) return record[languages.indexOf(active)] || text;
    if (active === 'en') {
      const count = text.match(/^已[读讀]\s*(\d+)\s*\/\s*(\d+)$/);
      if (count) return 'Read ' + count[1] + '/' + count[2];
      const empty = text.match(/^没找到「(.*)」$/);
      if (empty) return 'No results for “' + empty[1] + '”';
      const total = text.match(/^(\d+)\s*篇$/);
      if (total) return total[1] + (total[1] === '1' ? ' article' : ' articles');
    }
    if (active === 'zh-Hant') return text.replace(/^已读(?=\s*\d)/, '已讀').replace(/^没找到「/, '沒找到「');
    return text;
  }
  function change(node, slot, current, write) {
    const record = originals.get(node) || {};
    let item = record[slot];
    if (!item || current !== item.value) item = { source: current };
    const key = normalize(item.source);
    if (!key) return;
    const replacement = phrase(key);
    // Retain leading and trailing whitespace separating adjacent inline elements.
    item.value = replacement === key ? item.source : item.source.replace(/\S[\s\S]*\S|\S/, () => replacement);
    if (current !== item.value) write(item.value);
    record[slot] = item;
    originals.set(node, record);
  }
  function render(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (!node.parentElement || node.parentElement.closest(skip)) return;
      change(node, 'text', node.data, value => { node.data = value; });
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE || node.matches(skip)) return;
    for (const attr of attributes) {
      if (node.hasAttribute(attr)) change(node, attr, node.getAttribute(attr), value => node.setAttribute(attr, value));
    }
    // Translate rich paragraphs as complete sentences; keep their original nodes for Chinese.
    if (grouped.has(node)) {
      if (active === 'en') return;
      node.replaceChildren(...grouped.get(node));
      grouped.delete(node);
    }
    if (active === 'en' && node.matches('details.entry > summary h2, .cat-title > a')) {
      const id = node.hash ? node.hash.slice(1) : node.closest('details.entry')?.id;
      const english = window.GHL_ARTICLE_TITLES?.[id];
      if (english) {
        grouped.set(node, [...node.childNodes]);
        const label = document.createElement('span');
        label.className = 't-main';
        label.textContent = english;
        node.replaceChildren(label);
        return;
      }
    }
    if (active === 'en' && node.tagName === 'P' && node.childElementCount && node.querySelectorAll('*').length &&
        [...node.querySelectorAll('*')].every(el => /^(B|I|EM|STRONG|SPAN|BR|WBR|U)$/.test(el.tagName) && !el.attributes.length)) {
      const source = [...node.childNodes].map(child => {
        const record = originals.get(child);
        if (child.nodeType === Node.TEXT_NODE && record?.text) return record.text.source;
        return originalText(child);
      }).join('');
      const english = row(source)?.[2];
      if (english && english !== normalize(source)) {
        grouped.set(node, [...node.childNodes]);
        node.textContent = english;
        return;
      }
    }
    for (const child of node.childNodes) render(child);
  }
  function originalText(node) {
    if (node.nodeType === Node.TEXT_NODE) return originals.get(node)?.text?.source ?? node.data;
    return [...node.childNodes].map(originalText).join('');
  }
  function watch() {
    observer.observe(document.body, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:attributes});
  }
  function setLanguage(value, chosen) {
    active = languages.includes(value) ? value : 'zh-Hant';
    observer.disconnect();
    document.documentElement.lang = active;
    document.documentElement.dataset.ghlLang = active;
    try { localStorage.setItem('ghl_lang', active); } catch (_) {}
    if (chosen && new URLSearchParams(location.search).has('lang')) {
      const url = new URL(location.href);
      url.searchParams.set('lang', active);
      try { history.replaceState(null, '', url); } catch (_) {}
    }
    document.title = phrase(title);
    render(document.body);
    picker.value = active;
    notice.hidden = active !== 'en';
    watch();
    document.dispatchEvent(new CustomEvent('ghl-language-changed'));
  }
  function boot() {
    const header = document.querySelector('header');
    if (!header) return;
    const wrapper = document.createElement('label');
    wrapper.className = 'ghl-locale';
    wrapper.dataset.ghlUi = '';
    picker = document.createElement('select');
    picker.className = 'ghl-locale-select';
    picker.setAttribute('aria-label', '語言 / 语言 / Language');
    ['繁體','简体','English'].forEach((label,i) => {
      const option = new Option(label, languages[i]); option.lang=languages[i]; picker.add(option);
    });
    wrapper.append(picker);
    header.insertBefore(wrapper, header.querySelector('nav'));
    notice = document.createElement('p');
    notice.className = 'ghl-translation-notice';
    notice.dataset.ghlUi = '';
    notice.lang = 'en';
    notice.hidden = true;
    notice.textContent = 'Machine-translated reading copy. Switch to Chinese to read the original.';
    const content = document.querySelector('.hero, #main-content, main');
    if (content?.matches('.hero')) content.append(notice);
    else if (content) content.prepend(notice); else header.after(notice);
    for (const [i, link] of [...header.querySelectorAll('nav a')].entries()) {
      const img = link.querySelector('img.navimg, img[alt]');
      if (!img) continue;
      const label = document.createElement('span');
      label.dataset.ghlUi = '';
      label.className = 'ghl-img-label';
      label.setAttribute('aria-hidden','true');
      label.textContent = ['Part I','Part II','Part III','Part IV','Library'][i] || row(img.alt)?.[2] || img.alt;
      link.append(label);
    }
    observer = new MutationObserver(records => {
      observer.disconnect();
      const pending = new Set();
      for (const record of records) {
        if (record.type === 'childList') record.addedNodes.forEach(node => pending.add(node));
        else pending.add(record.target);
      }
      for (const node of pending) if (node.isConnected) render(node);
      watch();
    });
    let initial = new URLSearchParams(location.search).get('lang');
    if (!languages.includes(initial)) { try { initial = localStorage.getItem('ghl_lang'); } catch (_) {} }
    setLanguage(initial);
    picker.addEventListener('change', () => setLanguage(picker.value, true));
    window.GHL_SET_LANGUAGE = value => setLanguage(value,true);
  }
  window.GHL_PHRASE = phrase;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})();
