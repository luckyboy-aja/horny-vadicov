/**
 * Obec Horný Vadičov - IDSK 3.0 Administračný systém
 * Podpora pre lokálny server (npm run cms) aj priame publikovanie na GitHub Pages (GitHub API)
 */

(function () {
  'use strict';

  // Globálny stav administrácie
  const state = {
    mode: 'detecting', // 'local' | 'github' | 'offline'
    apiBase: '',
    ghToken: localStorage.getItem('horny_vadicov_gh_token') || '',
    repo: 'luckyboy-aja/horny-vadicov',
    branch: 'main',
    articles: [],
    notices: [],
    articleImageBase64: null,
    articleImageName: null,
    noticeFileBase64: null,
    noticeFileName: null
  };

  // DOM Elementy
  const el = {
    statusBadge: document.getElementById('cmsStatusBadge'),
    statusDot: document.getElementById('cmsStatusDot'),
    statusText: document.getElementById('cmsStatusText'),
    kpiArticles: document.getElementById('kpiArticles'),
    kpiBoard: document.getElementById('kpiBoard'),
    kpiVzn: document.getElementById('kpiVzn'),
    articlesTableBody: document.getElementById('articlesTableBody'),
    noticesTableBody: document.getElementById('noticesTableBody'),
    searchArticlesInput: document.getElementById('searchArticlesInput'),
    searchNoticeInput: document.getElementById('searchNoticeInput'),
    inputGhToken: document.getElementById('inputGhToken'),
    btnSaveGhToken: document.getElementById('btnSaveGhToken'),
    btnTestGhConnection: document.getElementById('btnTestGhConnection'),
    btnExportBackup: document.getElementById('btnExportBackup'),
    modalNewArticle: document.getElementById('modalNewArticle'),
    modalNewNotice: document.getElementById('modalNewNotice'),
    btnOpenNewArticleModal: document.getElementById('btnOpenNewArticleModal'),
    btnOpenNewNoticeModal: document.getElementById('btnOpenNewNoticeModal'),
    btnQuickNewArticle: document.getElementById('btnQuickNewArticle'),
    btnQuickNewNotice: document.getElementById('btnQuickNewNotice'),
    btnQuickSettings: document.getElementById('btnQuickSettings'),
    btnSubmitArticle: document.getElementById('btnSubmitArticle'),
    btnSubmitNotice: document.getElementById('btnSubmitNotice'),
    articleUploadBox: document.getElementById('articleUploadBox'),
    articleFileInput: document.getElementById('articleFileInput'),
    articleImgPreview: document.getElementById('articleImgPreview'),
    articleEditor: document.getElementById('articleEditor'),
    noticeUploadBox: document.getElementById('noticeUploadBox'),
    noticeFileInput: document.getElementById('noticeFileInput'),
    noticeFileNameLabel: document.getElementById('noticeFileNameLabel'),
    toast: document.getElementById('cmsToast'),
    toastMsg: document.getElementById('cmsToastMessage')
  };

  // Toast správa
  function showToast(message, type = 'success') {
    el.toastMsg.textContent = message;
    el.toast.className = `cms-toast is-visible cms-toast--${type}`;
    setTimeout(() => {
      el.toast.classList.remove('is-visible');
    }, 4000);
  }

  // Slugifikácia
  function slugify(text) {
    return text
      .toString()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 60);
  }

  // Prepínanie pohľadov
  function switchView(viewName) {
    document.querySelectorAll('.cms-nav-item').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.view === viewName);
    });
    document.querySelectorAll('.cms-view').forEach(view => {
      view.classList.toggle('is-active', view.id === `view-${viewName}`);
    });
  }

  // Inicializácia navigácie
  document.querySelectorAll('.cms-nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      switchView(btn.dataset.view);
    });
  });

  // Rýchle tlačidlá z nástenky
  if (el.btnQuickNewArticle) el.btnQuickNewArticle.addEventListener('click', () => openModal('modalNewArticle'));
  if (el.btnQuickNewNotice) el.btnQuickNewNotice.addEventListener('click', () => openModal('modalNewNotice'));
  if (el.btnQuickSettings) el.btnQuickSettings.addEventListener('click', () => switchView('settings'));

  // Modály
  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'flex';
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
  }

  document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      closeModal(btn.dataset.close);
    });
  });

  window.addEventListener('click', (e) => {
    if (e.target.classList.contains('cms-modal-overlay')) {
      e.target.style.display = 'none';
    }
  });

  if (el.btnOpenNewArticleModal) el.btnOpenNewArticleModal.addEventListener('click', () => openModal('modalNewArticle'));
  if (el.btnOpenNewNoticeModal) el.btnOpenNewNoticeModal.addEventListener('click', () => openModal('modalNewNotice'));

  // Formátovanie textu v editore
  document.querySelectorAll('.cms-editor-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const cmd = btn.dataset.cmd;
      const val = btn.dataset.val || null;
      if (cmd === 'createLink') {
        const url = prompt('Zadajte URL odkazu (napr. https://...):');
        if (url) document.execCommand(cmd, false, url);
      } else {
        document.execCommand(cmd, false, val);
      }
      el.articleEditor.focus();
    });
  });

  // Upload obrázka pre článok
  if (el.articleUploadBox) {
    el.articleUploadBox.addEventListener('click', () => el.articleFileInput.click());
    el.articleFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) handleArticleImage(file);
    });

    el.articleUploadBox.addEventListener('dragover', (e) => {
      e.preventDefault();
      el.articleUploadBox.style.borderColor = 'var(--idsk-color-primary)';
    });

    el.articleUploadBox.addEventListener('drop', (e) => {
      e.preventDefault();
      el.articleUploadBox.style.borderColor = '#cbd5e1';
      if (e.dataTransfer.files.length) {
        handleArticleImage(e.dataTransfer.files[0]);
      }
    });
  }

  function handleArticleImage(file) {
    state.articleImageName = file.name;
    const reader = new FileReader();
    reader.onload = (ev) => {
      state.articleImageBase64 = ev.target.result;
      el.articleImgPreview.src = ev.target.result;
      el.articleImgPreview.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }

  // Upload PDF pre úradnú tabuľu
  if (el.noticeUploadBox) {
    el.noticeUploadBox.addEventListener('click', () => el.noticeFileInput.click());
    el.noticeFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) handleNoticeFile(file);
    });
  }

  function handleNoticeFile(file) {
    state.noticeFileName = file.name;
    el.noticeFileNameLabel.textContent = `Vybraný súbor: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    const reader = new FileReader();
    reader.onload = (ev) => {
      state.noticeFileBase64 = ev.target.result;
    };
    reader.readAsDataURL(file);
  }

  // Detekcia režimu spojenia (Lokálny server vs GitHub Pages)
  async function detectEnvironment() {
    // 1. Skúsime lokálny API endpoint (bežiaci napr. cez node cms/server.js na porte 3001 alebo na aktuálnom hoste)
    const possibleBases = [
      window.location.origin,
      'http://localhost:3001'
    ];

    for (const base of possibleBases) {
      try {
        const resp = await fetch(`${base}/api/status`, { method: 'GET', mode: 'cors' });
        if (resp.ok) {
          const data = await resp.json();
          state.mode = 'local';
          state.apiBase = base;
          el.statusBadge.innerHTML = `<span class="cms-status-badge__dot"></span> Lokálny server (aktívny)`;
          if (data.stats) {
            if (el.kpiArticles) el.kpiArticles.textContent = data.stats.articlesCount;
            if (el.kpiBoard) el.kpiBoard.textContent = data.stats.boardCount;
            if (el.kpiVzn) el.kpiVzn.textContent = data.stats.vznCount;
          }
          loadLocalData();
          return;
        }
      } catch (err) {
        // Skúsime ďalší
      }
    }

    // 2. Ak lokálny server nebeží, skontrolujeme GitHub token
    if (state.ghToken) {
      state.mode = 'github';
      el.statusBadge.innerHTML = `<span class="cms-status-badge__dot"></span> GitHub Pages Cloud`;
      loadGitHubData();
    } else {
      state.mode = 'offline';
      el.statusBadge.innerHTML = `<span class="cms-status-badge__dot cms-status-badge__dot--warning"></span> Lokálny prehliadač`;
      loadFallbackData();
    }
  }

  // Načítanie dát cez lokálny API server
  async function loadLocalData() {
    try {
      // Aktuality
      const artResp = await fetch(`${state.apiBase}/api/aktuality`);
      if (artResp.ok) {
        const artData = await artResp.json();
        state.articles = artData.articles || [];
        renderArticles(state.articles);
      }

      // Úradná tabuľa
      const notResp = await fetch(`${state.apiBase}/api/uradna-tabula`);
      if (notResp.ok) {
        const notData = await notResp.json();
        state.notices = notData.notices || [];
        renderNotices(state.notices);
      }
    } catch (e) {
      console.warn('Chyba načítania lokálnych dát:', e);
    }
  }

  // Načítanie dát priamo z webu (fallback)
  async function loadFallbackData() {
    try {
      // Načítame zoznam aktualít z index.html
      const resp = await fetch('../obec-2/aktuality/');
      if (resp.ok) {
        const text = await resp.text();
        parseArticlesFromHtml(text);
      }

      // Načítame zoznam úradnej tabule
      const respTab = await fetch('../zverejnovanie/uradna-tabula-1/');
      if (respTab.ok) {
        const textTab = await respTab.text();
        parseNoticesFromHtml(textTab);
      }
    } catch (e) {
      console.warn('Chyba fallback načítania:', e);
    }
  }

  function parseArticlesFromHtml(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const links = doc.querySelectorAll('.event-link');
    const articles = [];

    links.forEach(l => {
      const name = l.querySelector('.event-name')?.textContent || '';
      const date = l.querySelector('.event-date .event-info-value')?.textContent || '';
      const perex = l.querySelector('.event-perex')?.textContent || '';
      const img = l.querySelector('img')?.getAttribute('src') || '';
      const href = l.getAttribute('href') || '';
      if (name) {
        articles.push({
          title: name.trim(),
          date: date.trim(),
          perex: perex.trim(),
          image: img,
          url: href
        });
      }
    });

    state.articles = articles;
    renderArticles(articles);
    if (el.kpiArticles) el.kpiArticles.textContent = articles.length;
  }

  function parseNoticesFromHtml(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const items = doc.querySelectorAll('.ed-item a');
    const notices = [];

    items.forEach(item => {
      const name = item.querySelector('.item-name')?.textContent || item.textContent;
      const dates = item.querySelectorAll('.item-date');
      const datesStr = Array.from(dates).map(d => d.textContent.trim()).join(' · ');
      const href = item.getAttribute('href') || '';
      if (name) {
        notices.push({
          title: name.trim(),
          dates: datesStr,
          url: href
        });
      }
    });

    state.notices = notices;
    renderNotices(notices);
    if (el.kpiBoard) el.kpiBoard.textContent = notices.length;
  }

  // Vykreslenie tabuľky aktualít
  function renderArticles(list) {
    if (!el.articlesTableBody) return;
    if (!list || !list.length) {
      el.articlesTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;">Zatiaľ nie sú evidované žiadne aktuality.</td></tr>';
      return;
    }

    el.articlesTableBody.innerHTML = list.map(item => `
      <tr>
        <td>
          <img src="${item.image ? '../' + item.image.replace(/^\.\.\//, '') : '../images/crest.png'}" alt="" style="width: 50px; height: 38px; object-fit: cover; border-radius: 4px; border: 1px solid #e2e8f0;">
        </td>
        <td>
          <strong>${escapeHtml(item.title)}</strong>
          ${item.perex ? `<div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">${escapeHtml(item.perex.substring(0, 80))}...</div>` : ''}
        </td>
        <td>${escapeHtml(item.date)}</td>
        <td style="text-align: right;">
          <a href="../obec-2/aktuality/${item.slug ? item.slug + '/' : item.url}" target="_blank" class="cms-btn cms-btn--secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;">Zobraziť</a>
        </td>
      </tr>
    `).join('');
  }

  // Vykreslenie tabuľky úradnej tabule
  function renderNotices(list) {
    if (!el.noticesTableBody) return;
    if (!list || !list.length) {
      el.noticesTableBody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 2rem;">Zatiaľ nie sú evidované žiadne oznamy.</td></tr>';
      return;
    }

    el.noticesTableBody.innerHTML = list.map(item => `
      <tr>
        <td>
          <strong>${escapeHtml(item.title)}</strong>
        </td>
        <td>${escapeHtml(item.dates || 'Platné')}</td>
        <td style="text-align: right;">
          <a href="../zverejnovanie/uradna-tabula-1/${item.slug ? item.slug + '/' : item.url}" target="_blank" class="cms-btn cms-btn--secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;">Zobraziť</a>
        </td>
      </tr>
    `).join('');
  }

  // Filtrovanie
  if (el.searchArticlesInput) {
    el.searchArticlesInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      const filtered = state.articles.filter(a => a.title.toLowerCase().includes(q) || a.perex?.toLowerCase().includes(q));
      renderArticles(filtered);
    });
  }

  if (el.searchNoticeInput) {
    el.searchNoticeInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      const filtered = state.notices.filter(n => n.title.toLowerCase().includes(q));
      renderNotices(filtered);
    });
  }

  // Odoslanie novej aktuality
  if (el.btnSubmitArticle) {
    el.btnSubmitArticle.addEventListener('click', async () => {
      const title = document.getElementById('articleTitle')?.value.trim();
      const date = document.getElementById('articleDate')?.value.trim();
      const perex = document.getElementById('articlePerex')?.value.trim();
      const contentHtml = el.articleEditor?.innerHTML.trim();

      if (!title) {
        alert('Zadajte prosím názov článku.');
        return;
      }
      if (!contentHtml || contentHtml === '<br>') {
        alert('Zadajte prosím obsah článku.');
        return;
      }

      el.btnSubmitArticle.disabled = true;
      el.btnSubmitArticle.textContent = 'Ukladám a publikujem...';

      try {
        if (state.mode === 'local') {
          // Lokálny server
          const resp = await fetch(`${state.apiBase}/api/aktuality`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title,
              date: date || new Date().toLocaleDateString('sk-SK'),
              perex,
              contentHtml,
              imageBase64: state.articleImageBase64,
              imageFileName: state.articleImageName
            })
          });

          const result = await resp.json();
          if (resp.ok && result.success) {
            showToast('Aktualita bola úspešne publikovaná na webe!');
            closeModal('modalNewArticle');
            resetArticleForm();
            loadLocalData();
          } else {
            alert('Chyba: ' + (result.error || 'Nepodarilo sa uložiť článok.'));
          }
        } else if (state.mode === 'github' && state.ghToken) {
          // Priame publikovanie na GitHub Pages cez GitHub API
          await publishArticleToGitHub({ title, date, perex, contentHtml });
          showToast('Aktualita bola odoslaná do GitHub repozitára! Web sa aktualizuje.');
          closeModal('modalNewArticle');
          resetArticleForm();
        } else {
          // Stiahnutie súboru ako záložný variant
          showToast('Režim bez servera: spustite "npm run cms" alebo nastavte GitHub token.', 'error');
          alert('Pre priame ukladanie spustite v termináli "npm run cms" alebo zadajte GitHub Token v záložke Nastavenia.');
        }
      } catch (err) {
        alert('Chyba spojenia: ' + err.message);
      } finally {
        el.btnSubmitArticle.disabled = false;
        el.btnSubmitArticle.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> Uložiť a publikovať`;
      }
    });
  }

  // Odoslanie nového oznamu na úradnú tabuľu
  if (el.btnSubmitNotice) {
    el.btnSubmitNotice.addEventListener('click', async () => {
      const title = document.getElementById('noticeTitle')?.value.trim();
      const category = document.getElementById('noticeCategory')?.value;
      const dateFrom = document.getElementById('noticeDateFrom')?.value.trim();
      const dateTo = document.getElementById('noticeDateTo')?.value.trim();
      const description = document.getElementById('noticeDesc')?.value.trim();

      if (!title) {
        alert('Zadajte prosím názov oznámenia.');
        return;
      }

      el.btnSubmitNotice.disabled = true;
      el.btnSubmitNotice.textContent = 'Vyvesujem na tabuľu...';

      try {
        if (state.mode === 'local') {
          const resp = await fetch(`${state.apiBase}/api/uradna-tabula`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title,
              category,
              dateFrom: dateFrom || new Date().toLocaleDateString('sk-SK'),
              dateTo: dateTo || new Date(Date.now() + 15 * 86400000).toLocaleDateString('sk-SK'),
              description,
              fileBase64: state.noticeFileBase64,
              fileName: state.noticeFileName
            })
          });

          const result = await resp.json();
          if (resp.ok && result.success) {
            showToast('Oznam bol úspešne vyvesený na úradnú tabuľu!');
            closeModal('modalNewNotice');
            resetNoticeForm();
            loadLocalData();
          } else {
            alert('Chyba: ' + (result.error || 'Nepodarilo sa vyvesiť oznam.'));
          }
        } else {
          alert('Pre vyvesenie spustite lokálny server príkazom "npm run cms" alebo nastavte GitHub Token v Nastaveniach.');
        }
      } catch (err) {
        alert('Chyba: ' + err.message);
      } finally {
        el.btnSubmitNotice.disabled = false;
        el.btnSubmitNotice.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> Vyvesiť na úradnú tabuľu`;
      }
    });
  }

  function resetArticleForm() {
    document.getElementById('articleTitle').value = '';
    document.getElementById('articleDate').value = '';
    document.getElementById('articlePerex').value = '';
    el.articleEditor.innerHTML = '';
    el.articleImgPreview.style.display = 'none';
    state.articleImageBase64 = null;
    state.articleImageName = null;
  }

  function resetNoticeForm() {
    document.getElementById('noticeTitle').value = '';
    document.getElementById('noticeDateFrom').value = '';
    document.getElementById('noticeDateTo').value = '';
    document.getElementById('noticeDesc').value = '';
    el.noticeFileNameLabel.textContent = 'Kliknite sem pre výber PDF súboru';
    state.noticeFileBase64 = null;
    state.noticeFileName = null;
  }

  // GitHub API publikovanie
  async function publishArticleToGitHub(data) {
    const slug = slugify(data.title) + '-' + Date.now().toString().slice(-4);
    const dateStr = data.date || new Date().toLocaleDateString('sk-SK');
    
    // Vytvorenie jednoduchej IDSK podstránky
    const pageContent = `<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(data.title)} | Aktuality | Obec Horný Vadičov (IDSK 3.0)</title>
  <link rel="icon" type="image/png" href="../../../images/crest.png">
  <link rel="stylesheet" href="../../../src/styles/idsk-tokens.css">
  <link rel="stylesheet" href="../../../src/styles/idsk-components.css">
  <link rel="stylesheet" href="../../../src/styles/main.css">
</head>
<body>
  <div class="idsk-container" style="padding-top: 2rem;">
    <h1>${escapeHtml(data.title)}</h1>
    <div style="color: #666; margin-bottom: 1.5rem;">Dátum zverejnenia: ${dateStr}</div>
    <div style="font-size: 1.1rem; line-height: 1.7;">
      ${data.contentHtml}
    </div>
    <div style="margin-top: 2rem;">
      <a href="../" class="idsk-button">← Späť na zoznam aktualít</a>
    </div>
  </div>
</body>
</html>`;

    // Commit cez GitHub REST API
    const path = `public/obec-2/aktuality/${slug}/index.html`;
    const url = `https://api.github.com/repos/${state.repo}/contents/${path}`;
    const resp = await fetch(url, {
      method: 'PUT',
      headers: {
        'Authorization': `token ${state.ghToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: `feat(cms): nová aktualita ${data.title}`,
        content: btoa(unescape(encodeURIComponent(pageContent))),
        branch: state.branch
      })
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.message || 'GitHub API chyba');
    }
  }

  // Nastavenie GitHub Tokenu
  if (el.btnSaveGhToken) {
    if (state.ghToken && el.inputGhToken) {
      el.inputGhToken.value = state.ghToken;
    }
    el.btnSaveGhToken.addEventListener('click', () => {
      const val = el.inputGhToken.value.trim();
      localStorage.setItem('horny_vadicov_gh_token', val);
      state.ghToken = val;
      showToast('GitHub Token bol uložený do prehliadača.');
      detectEnvironment();
    });
  }

  if (el.btnTestGhConnection) {
    el.btnTestGhConnection.addEventListener('click', async () => {
      const token = el.inputGhToken?.value.trim() || state.ghToken;
      if (!token) {
        alert('Najskôr zadajte GitHub Token.');
        return;
      }
      try {
        const resp = await fetch(`https://api.github.com/repos/${state.repo}`, {
          headers: { 'Authorization': `token ${token}` }
        });
        if (resp.ok) {
          const data = await resp.json();
          alert(`Spojenie úspešné! Repozitár: ${data.full_name}, oprávnenie overené.`);
        } else {
          alert('Nepodarilo sa pripojiť. Skontrolujte platnosť tokenu.');
        }
      } catch (e) {
        alert('Chyba: ' + e.message);
      }
    });
  }

  // Export JSON zálohy
  if (el.btnExportBackup) {
    el.btnExportBackup.addEventListener('click', () => {
      const backupData = {
        exportedAt: new Date().toISOString(),
        repo: state.repo,
        articlesCount: state.articles.length,
        articles: state.articles,
        noticesCount: state.notices.length,
        notices: state.notices
      };
      const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `horny-vadicov-zaloha-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  // Pomocná funkcia na escape HTML
  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
      tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
  }

  // Spustenie detekcie
  detectEnvironment();

})();
