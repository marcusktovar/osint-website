/* Yemen Field Notes: accessible, dependency-free renderer. All content is text,
   not HTML interpreted from external sources. */
'use strict';

const $ = (selector) => document.querySelector(selector);
const el = (tag, className, value) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = String(value);
  return node;
};

function sourceLink(sourceId, sources, label) {
  const source = sources[sourceId];
  if (!source || !/^https:\/\//.test(source.url)) return null;
  const link = el('a', '', label || source.name);
  link.href = source.url;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.title = source.name;
  return link;
}

function renderStats(data) {
  const grid = $('#stats');
  grid.replaceChildren();
  data.stats.forEach((item) => {
    const card = el('article', 'stat-card');
    card.append(el('div', 'stat-card-label', item.label));
    const number = el('div', 'stat-card-value', item.value);
    number.append(el('span', 'stat-card-unit', item.unit));
    card.append(number);
    const detail = el('p', 'stat-card-details');
    const link = sourceLink(item.source_id, data.sources, item.detail);
    if (link) detail.append(link);
    else detail.textContent = item.detail;
    card.append(detail);
    grid.append(card);
  });
}

function renderSections(data) {
  const root = $('#sections');
  root.replaceChildren();
  data.sections.forEach((section) => {
    const article = el('section', 'guide-section');
    article.id = section.id;
    article.setAttribute('aria-labelledby', `${section.id}-title`);
    const header = el('div', 'section-heading');
    header.append(el('div', 'section-index', `${section.number} / ${section.eyebrow}`));
    const title = el('h2', '', section.title);
    title.id = `${section.id}-title`;
    header.append(title, el('p', 'section-subtitle', section.subtitle));
    const body = el('div', 'section-body');
    section.paragraphs.forEach((item) => {
      const p = el('p', 'paragraph', item.text);
      if (item.sources?.length) {
        const citations = el('span', 'paragraph-sources');
        citations.setAttribute('aria-label', 'Sources for preceding paragraph');
        item.sources.forEach((id, index) => {
          const a = sourceLink(id, data.sources, `[${index + 1}]`);
          if (a) citations.append(a);
        });
        p.append(citations);
      }
      body.append(p);
    });
    if (section.notice) body.append(el('aside', 'section-notice', section.notice));
    const readMore = el('div', 'section-readmore');
    readMore.append(el('span', '', 'Further reading ↗'));
    section.source_ids.slice(0, 3).forEach((sourceId) => {
      const link = sourceLink(sourceId, data.sources);
      if (link) readMore.append(link);
    });
    body.append(readMore);
    article.append(header, body);
    root.append(article);
  });
}

function renderSources(data) {
  const list = $('#source-list');
  list.replaceChildren();
  for (const [id, source] of Object.entries(data.sources)) {
    const item = el('li', 'source-item');
    const link = sourceLink(id, data.sources);
    if (!link) continue;
    link.append(el('span', '', '↗'));
    const detail = el('span', 'source-detail', source.kind);
    item.append(link, detail);
    list.append(item);
  }
  $('#methodology').textContent = data.methodology || '';
}

function renderStatus(data) {
  const mode = data.build_mode;
  const main = mode === 'refreshed'
    ? 'Source check completed'
    : mode === 'partial'
      ? 'Some sources refreshed; dated values retained'
      : mode === 'cached'
        ? 'Saved values shown; remote sources unavailable'
        : 'Initial research snapshot (not a live refresh)';
  $('#edition-status').textContent = main;
  $('#footer-updated').textContent = `Edition: ${mode} · ${data.generated_at_utc.slice(0, 10)}`;
}

async function main() {
  try {
    const response = await fetch('./data/sections.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!Array.isArray(data.sections) || !Array.isArray(data.stats) || !data.sources) {
      throw new Error('Invalid sections data');
    }
    renderStats(data);
    renderSections(data);
    renderSources(data);
    renderStatus(data);
    // The nav may be opened with a #anchor before the JSON finished loading.
    if (location.hash && location.hash !== '#top') {
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) requestAnimationFrame(() => target.scrollIntoView());
    }
  } catch (error) {
    console.error('Site data could not be loaded:', error);
    const section = $('#sections');
    section.replaceChildren();
    const message = el('div', 'error-state', 'The guide could not load its data file. Start a local web server in the project folder, or open the published site through GitHub Pages.');
    message.append(el('p', '', 'For local testing: python -m http.server 8000 --directory site'));
    section.append(message);
    $('#edition-status').textContent = 'Unable to load site data';
  }
}

document.addEventListener('DOMContentLoaded', main);
