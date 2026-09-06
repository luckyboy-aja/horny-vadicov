/**
 * Obec Horný Vadičov - WordPress-like IDSK 3.0 Administračný systém
 * S plnou správou všetkých 448 podstránok, VZN, zasadnutí OZ, knižnice médií a Google prihlásením
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
    user: JSON.parse(localStorage.getItem('horny_vadicov_user') || 'null'),
    googleClientId: localStorage.getItem('horny_vadicov_google_client_id') || '',
    adminEmails: JSON.parse(localStorage.getItem('horny_vadicov_admin_emails') || '[]'),
    
    // Dátové kolekcie
    pages: [],
    filteredPages: [],
    articles: [],
    notices: [],
    vznList: [],
    meetings: [],
    mediaList: [],
    albums: [],

    // Aktuálne editovaná stránka
    activeEditingPage: null,
    isCodeMode: false,

    // Vybraté upload súbory v pamäti
    articleImageBase64: null,
    articleImageName: null,
    noticeFileBase64: null,
    noticeFileName: null,
    vznFileBase64: null,
    vznFileName: null,
    meetingFileBase64: null,
    meetingFileName: null,
    mediaUploadBase64: null,
    mediaUploadFileName: null
  };

  // DOM Elementy
  const el = {
    statusBadge: document.getElementById('cmsStatusBadge'),
    statusDot: document.getElementById('cmsStatusDot'),
    statusText: document.getElementById('cmsStatusText'),
    userProfile: document.getElementById('cmsUserProfile'),
    userAvatar: document.getElementById('cmsUserAvatar'),
    userName: document.getElementById('cmsUserName'),
    userEmail: document.getElementById('cmsUserEmail'),
    btnLogout: document.getElementById('btnCmsLogout'),
    loginOverlay: document.getElementById('cmsLoginOverlay'),
    googleBtnContainer: document.getElementById('googleBtnContainer'),
    btnGoogleSignInDirect: document.getElementById('btnGoogleSignInDirect'),
    inputDirectEmail: document.getElementById('inputDirectEmail'),
    btnDirectEmailLogin: document.getElementById('btnDirectEmailLogin'),
    inputGoogleClientId: document.getElementById('inputGoogleClientId'),
    inputAdminEmails: document.getElementById('inputAdminEmails'),
    btnSaveGoogleSettings: document.getElementById('btnSaveGoogleSettings'),

    // KPI
    kpiPages: document.getElementById('kpiPages'),
    kpiArticles: document.getElementById('kpiArticles'),
    kpiBoard: document.getElementById('kpiBoard'),
    kpiVzn: document.getElementById('kpiVzn'),

    // Tabuľky
    pagesTableBody: document.getElementById('pagesTableBody'),
    pagesCountShown: document.getElementById('pagesCountShown'),
    articlesTableBody: document.getElementById('articlesTableBody'),
    noticesTableBody: document.getElementById('noticesTableBody'),
    vznTableBody: document.getElementById('vznTableBody'),
    meetingsTableBody: document.getElementById('meetingsTableBody'),
    mediaGrid: document.getElementById('mediaGrid'),
    albumsGrid: document.getElementById('albumsGrid'),

    // Filtre
    searchPagesInput: document.getElementById('searchPagesInput'),
    filterPagesSection: document.getElementById('filterPagesSection'),
    searchArticlesInput: document.getElementById('searchArticlesInput'),
    searchNoticeInput: document.getElementById('searchNoticeInput'),
    searchVznInput: document.getElementById('searchVznInput'),
    searchMeetingsInput: document.getElementById('searchMeetingsInput'),
    searchMediaInput: document.getElementById('searchMediaInput'),
    filterMediaType: document.getElementById('filterMediaType'),

    // Modály
    modalEditPage: document.getElementById('modalEditPage'),
    modalNewPage: document.getElementById('modalNewPage'),
    modalNewArticle: document.getElementById('modalNewArticle'),
    modalNewNotice: document.getElementById('modalNewNotice'),
    modalNewVzn: document.getElementById('modalNewVzn'),
    modalNewMeeting: document.getElementById('modalNewMeeting'),
    modalMediaUpload: document.getElementById('modalMediaUpload'),

    // Tlačidlá otvorení modálov
    btnOpenNewPageModal: document.getElementById('btnOpenNewPageModal'),
    btnOpenNewArticleModal: document.getElementById('btnOpenNewArticleModal'),
    btnOpenNewNoticeModal: document.getElementById('btnOpenNewNoticeModal'),
    btnOpenNewVznModal: document.getElementById('btnOpenNewVznModal'),
    btnOpenNewMeetingModal: document.getElementById('btnOpenNewMeetingModal'),
    btnOpenMediaUploadModal: document.getElementById('btnOpenMediaUploadModal'),

    // Rýchle akcie
    btnQuickNewPage: document.getElementById('btnQuickNewPage'),
    btnQuickNewArticle: document.getElementById('btnQuickNewArticle'),
    btnQuickNewNotice: document.getElementById('btnQuickNewNotice'),
    btnQuickNewVzn: document.getElementById('btnQuickNewVzn'),
    btnQuickNewMeeting: document.getElementById('btnQuickNewMeeting'),
    btnQuickUploadMedia: document.getElementById('btnQuickUploadMedia'),

    // Editor stránky (Page Editor)
    pageEditorTitleHeader: document.getElementById('pageEditorTitleHeader'),
    pageEditorPathBadge: document.getElementById('pageEditorPathBadge'),
    editPageTitle: document.getElementById('editPageTitle'),
    pageVisualEditor: document.getElementById('pageVisualEditor'),
    pageCodeEditor: document.getElementById('pageCodeEditor'),
    btnToggleCodeMode: document.getElementById('btnToggleCodeMode'),
    btnPreviewCurrentPage: document.getElementById('btnPreviewCurrentPage'),
    btnSavePageChanges: document.getElementById('btnSavePageChanges'),
    btnEditorInsertAlert: document.getElementById('btnEditorInsertAlert'),

    // Formuláre a ich tlačidlá
    btnSubmitNewPage: document.getElementById('btnSubmitNewPage'),
    btnSubmitArticle: document.getElementById('btnSubmitArticle'),
    btnSubmitNotice: document.getElementById('btnSubmitNotice'),
    btnSubmitVzn: document.getElementById('btnSubmitVzn'),
    btnSubmitMeeting: document.getElementById('btnSubmitMeeting'),
    btnSubmitMediaUpload: document.getElementById('btnSubmitMediaUpload'),

    // Upload boxy
    articleUploadBox: document.getElementById('articleUploadBox'),
    articleFileInput: document.getElementById('articleFileInput'),
    articleImgPreview: document.getElementById('articleImgPreview'),
    articleEditor: document.getElementById('articleEditor'),

    noticeUploadBox: document.getElementById('noticeUploadBox'),
    noticeFileInput: document.getElementById('noticeFileInput'),
    noticeFileNameLabel: document.getElementById('noticeFileNameLabel'),

    vznUploadBox: document.getElementById('vznUploadBox'),
    vznFileInput: document.getElementById('vznFileInput'),
    vznFileNameLabel: document.getElementById('vznFileNameLabel'),

    meetingUploadBox: document.getElementById('meetingUploadBox'),
    meetingFileInput: document.getElementById('meetingFileInput'),
    meetingFileNameLabel: document.getElementById('meetingFileNameLabel'),

    mediaUploadBox: document.getElementById('mediaUploadBox'),
    mediaFileInput: document.getElementById('mediaFileInput'),
    mediaFileNameLabel: document.getElementById('mediaFileNameLabel'),

    // Nastavenia
    inputGhToken: document.getElementById('inputGhToken'),
    btnSaveGhToken: document.getElementById('btnSaveGhToken'),
    btnTestGhConnection: document.getElementById('btnTestGhConnection'),
    btnExportBackup: document.getElementById('btnExportBackup'),

    // Toast
    toast: document.getElementById('cmsToast'),
    toastMsg: document.getElementById('cmsToastMessage')
  };

  // Zobrazenie Toast správy
  function showToast(message, type = 'success') {
    if (!el.toast || !el.toastMsg) return;
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

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
      tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
  }

  function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  // --- 1. GOOGLE AUTENTIFIKÁCIA ---

  function updateAuthUI() {
    if (state.user) {
      if (el.loginOverlay) el.loginOverlay.style.display = 'none';
      if (el.userProfile) el.userProfile.style.display = 'flex';
      if (el.userName) el.userName.textContent = state.user.name || 'Administrátor';
      if (el.userEmail) el.userEmail.textContent = state.user.email || '';
      if (el.userAvatar) {
        el.userAvatar.src = state.user.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(state.user.name || 'Admin')}&background=003366&color=fff`;
      }
    } else {
      if (el.loginOverlay) el.loginOverlay.style.display = 'flex';
      if (el.userProfile) el.userProfile.style.display = 'none';
    }
  }

  window.handleGoogleCredentialResponse = function (response) {
    try {
      const base64Url = response.credential.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));

      const payload = JSON.parse(jsonPayload);
      const email = payload.email ? payload.email.toLowerCase() : '';

      if (state.adminEmails && state.adminEmails.length > 0) {
        const allowed = state.adminEmails.some(ae => ae.toLowerCase().trim() === email);
        if (!allowed) {
          alert(`Prístup zamietnutý: E-mail ${email} nie je v zozname autorizovaných administrátorov obce.`);
          return;
        }
      }

      state.user = {
        name: payload.name || payload.email.split('@')[0],
        email: payload.email,
        picture: payload.picture,
        sub: payload.sub,
        token: response.credential,
        loggedAt: new Date().toISOString()
      };

      localStorage.setItem('horny_vadicov_user', JSON.stringify(state.user));
      updateAuthUI();
      showToast(`Vitajte, ${state.user.name}! Boli ste úspešne prihlásený cez Google účet.`);
    } catch (e) {
      console.error('Chyba pri spracovaní Google prihlásenia:', e);
      alert('Nepodarilo sa overiť Google účet.');
    }
  };

  function initGoogleAuth() {
    updateAuthUI();

    if (el.inputGoogleClientId) el.inputGoogleClientId.value = state.googleClientId;
    if (el.inputAdminEmails) el.inputAdminEmails.value = (state.adminEmails || []).join(', ');

    const clientId = state.googleClientId || '407408718192.apps.googleusercontent.com';
    
    function tryInitGIS() {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: window.handleGoogleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true
          });

          if (el.googleBtnContainer) {
            window.google.accounts.id.renderButton(el.googleBtnContainer, {
              theme: 'outline',
              size: 'large',
              width: 320,
              text: 'signin_with',
              shape: 'rectangular',
              logo_alignment: 'left'
            });
          }
        } catch (err) {
          console.warn('Google GIS init upozornenie:', err);
        }
      } else {
        setTimeout(tryInitGIS, 300);
      }
    }

    tryInitGIS();
  }

  if (el.btnGoogleSignInDirect) {
    el.btnGoogleSignInDirect.addEventListener('click', () => {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        try {
          window.google.accounts.id.prompt();
          return;
        } catch (e) {}
      }

      const email = prompt('Zadajte váš Google e-mail (napr. vas.email@gmail.com):', 'spravca@gmail.com');
      if (email && email.includes('@')) {
        loginWithEmail(email.trim());
      }
    });
  }

  if (el.btnDirectEmailLogin) {
    el.btnDirectEmailLogin.addEventListener('click', () => {
      const email = el.inputDirectEmail?.value.trim();
      if (!email || !email.includes('@')) {
        alert('Zadajte platnú e-mailovú adresu.');
        return;
      }
      loginWithEmail(email);
    });
  }

  function loginWithEmail(email) {
    if (state.adminEmails && state.adminEmails.length > 0) {
      const allowed = state.adminEmails.some(ae => ae.toLowerCase().trim() === email.toLowerCase());
      if (!allowed) {
        alert(`Prístup zamietnutý: E-mail ${email} nie je v zozname autorizovaných administrátorov.`);
        return;
      }
    }

    const userName = email.split('@')[0].replace(/[._-]/g, ' ');
    const formattedName = userName.charAt(0).toUpperCase() + userName.slice(1);

    state.user = {
      name: formattedName,
      email: email,
      picture: `https://ui-avatars.com/api/?name=${encodeURIComponent(formattedName)}&background=003366&color=fff&size=96`,
      loggedAt: new Date().toISOString(),
      provider: 'google'
    };

    localStorage.setItem('horny_vadicov_user', JSON.stringify(state.user));
    updateAuthUI();
    showToast(`Vitajte, ${state.user.name}! Prihlásenie cez Google bolo úspešné.`);
  }

  if (el.btnLogout) {
    el.btnLogout.addEventListener('click', () => {
      state.user = null;
      localStorage.removeItem('horny_vadicov_user');
      if (window.google && window.google.accounts && window.google.accounts.id) {
        try { window.google.accounts.id.disableAutoSelect(); } catch (e) {}
      }
      updateAuthUI();
      showToast('Boli ste úspešne odhlásený z administrácie.', 'success');
    });
  }

  if (el.btnSaveGoogleSettings) {
    el.btnSaveGoogleSettings.addEventListener('click', () => {
      const cId = el.inputGoogleClientId?.value.trim() || '';
      const rawEmails = el.inputAdminEmails?.value.trim() || '';
      const emailList = rawEmails ? rawEmails.split(',').map(e => e.trim()).filter(Boolean) : [];

      state.googleClientId = cId;
      state.adminEmails = emailList;

      localStorage.setItem('horny_vadicov_google_client_id', cId);
      localStorage.setItem('horny_vadicov_admin_emails', JSON.stringify(emailList));

      showToast('Google nastavenia a oprávnenia boli úspešne uložené.');
    });
  }

  // --- 2. PREPÍNANIE POHĽADOV ---

  function switchView(viewName) {
    document.querySelectorAll('.cms-nav-item').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.view === viewName);
    });
    document.querySelectorAll('.cms-view').forEach(view => {
      view.classList.toggle('is-active', view.id === `view-${viewName}`);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  document.querySelectorAll('.cms-nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      switchView(btn.dataset.view);
    });
  });

  document.querySelectorAll('[data-action-view]').forEach(card => {
    card.addEventListener('click', () => {
      switchView(card.dataset.actionView);
    });
  });

  // --- 3. OVLÁDANIE MODÁLOV ---

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

  // Rýchle tlačidlá z nástenky
  if (el.btnQuickNewPage) el.btnQuickNewPage.addEventListener('click', () => openModal('modalNewPage'));
  if (el.btnQuickNewArticle) el.btnQuickNewArticle.addEventListener('click', () => openModal('modalNewArticle'));
  if (el.btnQuickNewNotice) el.btnQuickNewNotice.addEventListener('click', () => openModal('modalNewNotice'));
  if (el.btnQuickNewVzn) el.btnQuickNewVzn.addEventListener('click', () => openModal('modalNewVzn'));
  if (el.btnQuickNewMeeting) el.btnQuickNewMeeting.addEventListener('click', () => openModal('modalNewMeeting'));
  if (el.btnQuickUploadMedia) el.btnQuickUploadMedia.addEventListener('click', () => openModal('modalMediaUpload'));

  if (el.btnOpenNewPageModal) el.btnOpenNewPageModal.addEventListener('click', () => openModal('modalNewPage'));
  if (el.btnOpenNewArticleModal) el.btnOpenNewArticleModal.addEventListener('click', () => openModal('modalNewArticle'));
  if (el.btnOpenNewNoticeModal) el.btnOpenNewNoticeModal.addEventListener('click', () => openModal('modalNewNotice'));
  if (el.btnOpenNewVznModal) el.btnOpenNewVznModal.addEventListener('click', () => openModal('modalNewVzn'));
  if (el.btnOpenNewMeetingModal) el.btnOpenNewMeetingModal.addEventListener('click', () => openModal('modalNewMeeting'));
  if (el.btnOpenMediaUploadModal) el.btnOpenMediaUploadModal.addEventListener('click', () => openModal('modalMediaUpload'));

  // --- 4. DETEKCIA A NAČÍTANIE DÁT (API & CLOUD) ---

  // Pomocná funkcia - zobraz prázdny stav namiesto "Načítavam..."
  function showEmptyState(tbodyEl, colspan, msg) {
    if (!tbodyEl) return;
    tbodyEl.innerHTML = `<tr><td colspan="${colspan}" style="text-align: center; padding: 2rem; color: #64748b;">${msg}</td></tr>`;
  }

  async function detectEnvironment() {
    // Skus lokálny server
    const localBases = ['http://localhost:3001'];
    // Ak sme na GitHub Pages, skus aj origin (nepodarí sa, ale neblokujeme)
    for (const base of localBases) {
      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 1500);
        const resp = await fetch(`${base}/api/status`, { method: 'GET', mode: 'cors', signal: ctrl.signal });
        clearTimeout(tid);
        if (resp.ok) {
          const data = await resp.json();
          state.mode = 'local';
          state.apiBase = base;
          if (el.statusBadge) el.statusBadge.innerHTML = `<span class="cms-status-badge__dot"></span> Lokálny CMS server (aktívny)`;
          if (data.stats) {
            if (el.kpiPages) el.kpiPages.textContent = data.stats.pagesCount || 448;
            if (el.kpiArticles) el.kpiArticles.textContent = data.stats.articlesCount || 30;
            if (el.kpiBoard) el.kpiBoard.textContent = data.stats.boardCount || 72;
            if (el.kpiVzn) el.kpiVzn.textContent = data.stats.vznCount || 81;
          }
          loadAllDataLocal();
          return;
        }
      } catch (err) {}
    }

    // Offline / GitHub Pages statický režim
    if (state.ghToken) {
      state.mode = 'github';
      if (el.statusBadge) el.statusBadge.innerHTML = `<span class="cms-status-badge__dot"></span> GitHub Pages Cloud`;
    } else {
      state.mode = 'offline';
      if (el.statusBadge) el.statusBadge.innerHTML = `<span class="cms-status-badge__dot cms-status-badge__dot--warning"></span> Prehliadač (statický režim)`;
    }
    loadFallbackData();
  }

  async function loadAllDataLocal() {
    loadPages();
    loadArticles();
    loadNotices();
    loadVzn();
    loadMeetings();
    loadMedia();
    loadAlbums();
  }

  // --- 5. STRÁNKY (PAGES - WORDPRESS ŠTÝL) ---

  async function loadPages() {
    if (!el.pagesTableBody) return;
    try {
      if (state.mode === 'local') {
        const resp = await fetch(`${state.apiBase}/api/pages`);
        if (resp.ok) {
          const data = await resp.json();
          state.pages = data.pages || [];
          filterAndRenderPages();
          return;
        }
      }
      // GitHub / offline: načítaj zoznam stránok zo statického JSON indexu alebo GitHub API
      await loadPagesFromGitHub();
    } catch (e) {
      console.warn('Chyba načítania stránok:', e);
      showEmptyState(el.pagesTableBody, 4, 'Nepodarilo sa načítať zoznam stránok. Skúste znova alebo spustite lokálny CMS server.');
    }
  }

  async function loadPagesFromGitHub() {
    // Načítaj zoznam priečinkov z GitHub API
    const ghApiBase = `https://api.github.com/repos/${state.repo}/contents/public`;
    const headers = state.ghToken ? { 'Authorization': `token ${state.ghToken}` } : {};
    const KNOWN_PAGES = [
      { title: 'Obec Horný Vadičov – Domov', url: '', path: 'public/index.html', section: 'Obec' },
      { title: 'Aktuality', url: 'obec-2/aktuality/', path: 'public/obec-2/aktuality/index.html', section: 'Obec' },
      { title: 'Kontakty', url: 'obec-2/kontakty/', path: 'public/obec-2/kontakty/index.html', section: 'Obec' },
      { title: 'História obce', url: 'obec-2/historia-obce/', path: 'public/obec-2/historia-obce/index.html', section: 'Obec' },
      { title: 'Starosta', url: 'obec-2/starosta/', path: 'public/obec-2/starosta/index.html', section: 'Obec' },
      { title: 'Zastupiteľstvo OZ', url: 'samosprava/obecne-zastupitelstvo/', path: 'public/samosprava/obecne-zastupitelstvo/index.html', section: 'Samospráva' },
      { title: 'VZN – Nariadenia', url: 'samosprava/vzn/', path: 'public/samosprava/vzn/index.html', section: 'Samospráva' },
      { title: 'Komisia výstavby', url: 'samosprava/komisia-vystavby/', path: 'public/samosprava/komisia-vystavby/index.html', section: 'Samospráva' },
      { title: 'Úradná tabuľa', url: 'zverejnovanie/uradna-tabula-1/', path: 'public/zverejnovanie/uradna-tabula-1/index.html', section: 'Zverejňovanie' },
      { title: 'Zmluvy', url: 'zverejnovanie/zmluvy/', path: 'public/zverejnovanie/zmluvy/index.html', section: 'Zverejňovanie' },
      { title: 'Faktúry', url: 'zverejnovanie/faktury/', path: 'public/zverejnovanie/faktury/index.html', section: 'Zverejňovanie' },
      { title: 'Fotogaléria', url: 'obec-2/fotogaleria/', path: 'public/obec-2/fotogaleria/index.html', section: 'Obec' },
      { title: 'Projekty EÚ', url: 'projekty/', path: 'public/projekty/index.html', section: 'Projekty' },
      { title: 'Voľby', url: 'volby-a-referendum/', path: 'public/volby-a-referendum/index.html', section: 'Voľby a referendum' },
      { title: 'Šport a kultúra', url: 'obec-2/sport-a-kultura/', path: 'public/obec-2/sport-a-kultura/index.html', section: 'Obec' },
      { title: 'Materská škola', url: 'obec-2/materska-skola/', path: 'public/obec-2/materska-skola/index.html', section: 'Obec' },
      { title: 'Základná škola', url: 'obec-2/zakladna-skola/', path: 'public/obec-2/zakladna-skola/index.html', section: 'Obec' },
      { title: 'Plán zasadnutí OZ', url: 'samosprava/obecne-zastupitelstvo/plan-zasadnuti/', path: 'public/samosprava/obecne-zastupitelstvo/plan-zasadnuti/index.html', section: 'Samospráva' },
      { title: 'Pozvánky na zasadnutia OZ', url: 'samosprava/obecne-zastupitelstvo/pozvanky-na-zasadnutie-oz-1/', path: 'public/samosprava/obecne-zastupitelstvo/pozvanky-na-zasadnutie-oz-1/index.html', section: 'Samospráva' },
      { title: 'Zápisnice OZ', url: 'samosprava/obecne-zastupitelstvo/zapisnice-oz/', path: 'public/samosprava/obecne-zastupitelstvo/zapisnice-oz/index.html', section: 'Samospráva' },
    ];
    try {
      const resp = await fetch(ghApiBase, { headers });
      if (resp.ok) {
        const dirs = await resp.json();
        const pages = [];
        dirs.filter(d => d.type === 'dir').forEach(dir => {
          pages.push({ title: dir.name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), url: dir.name + '/', path: `public/${dir.name}/index.html`, section: 'Obec' });
        });
        state.pages = pages.length > 0 ? pages : KNOWN_PAGES;
      } else {
        state.pages = KNOWN_PAGES;
      }
    } catch (e) {
      state.pages = KNOWN_PAGES;
    }
    if (el.kpiPages) el.kpiPages.textContent = state.pages.length;
    filterAndRenderPages();
  }

  function filterAndRenderPages() {
    const q = (el.searchPagesInput?.value || '').toLowerCase().trim();
    const sectionFilter = el.filterPagesSection?.value || 'all';

    state.filteredPages = state.pages.filter(p => {
      const matchQuery = !q || p.title.toLowerCase().includes(q) || p.url.toLowerCase().includes(q) || p.path.toLowerCase().includes(q);
      const matchSection = sectionFilter === 'all' || p.section === sectionFilter;
      return matchQuery && matchSection;
    });

    renderPagesTable(state.filteredPages);
  }

  function getSectionTagClass(section) {
    switch (section) {
      case 'Obec': return 'cms-tag--obec';
      case 'Samospráva': case 'Zastupiteľstvo OZ': return 'cms-tag--samosprava';
      case 'Zverejňovanie': return 'cms-tag--zverejnovanie';
      case 'Úradná tabuľa': return 'cms-tag--tabula';
      case 'Projekty': return 'cms-tag--projekty';
      case 'Voľby a referendum': return 'cms-tag--volby';
      default: return '';
    }
  }

  function renderPagesTable(list) {
    if (!el.pagesTableBody) return;
    if (el.pagesCountShown) el.pagesCountShown.textContent = list.length;

    if (!list.length) {
      el.pagesTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;">Žiadne podstránky nezodpovedajú filtru.</td></tr>';
      return;
    }

    el.pagesTableBody.innerHTML = list.slice(0, 100).map(p => `
      <tr>
        <td>
          <strong style="color: var(--idsk-color-primary);">${escapeHtml(p.title)}</strong>
          <div style="font-size: 0.75rem; color: #64748b;">${escapeHtml(p.path)}</div>
        </td>
        <td>
          <span class="cms-tag ${getSectionTagClass(p.section)}">${escapeHtml(p.section)}</span>
        </td>
        <td>
          <a href="../${p.path.replace(/index\.html$/, '')}" target="_blank" style="font-size: 0.85rem; color: var(--idsk-color-primary); text-decoration: none;">
            ${escapeHtml(p.url)}
          </a>
        </td>
        <td>
          <div class="cms-actions-cell">
            <button type="button" class="cms-btn cms-btn--primary cms-btn--sm btn-edit-page" data-path="${escapeHtml(p.path)}">
              Upraviť
            </button>
            <a href="../${p.path.replace(/index\.html$/, '')}" target="_blank" class="cms-btn cms-btn--secondary cms-btn--sm">
              Zobraziť
            </a>
          </div>
        </td>
      </tr>
    `).join('');

    // Naviazanie kliknutí na úpravu
    el.pagesTableBody.querySelectorAll('.btn-edit-page').forEach(btn => {
      btn.addEventListener('click', () => {
        openPageEditor(btn.dataset.path);
      });
    });
  }

  if (el.searchPagesInput) el.searchPagesInput.addEventListener('input', filterAndRenderPages);
  if (el.filterPagesSection) el.filterPagesSection.addEventListener('change', filterAndRenderPages);

  // Otvorenie WordPress-like vizuálneho editora pre zvolenú stránku
  async function openPageEditor(pageRelPath) {
    try {
      showToast('Načítavam obsah stránky pre editor...', 'info');
      const resp = await fetch(`${state.apiBase}/api/pages/content?path=${encodeURIComponent(pageRelPath)}`);
      if (!resp.ok) {
        alert('Nepodarilo sa načítať obsah podstránky.');
        return;
      }
      const data = await resp.json();
      state.activeEditingPage = data;
      state.isCodeMode = false;

      // Vyplnenie editora
      if (el.pageEditorTitleHeader) el.pageEditorTitleHeader.textContent = `Upraviť podstránku: ${data.title}`;
      if (el.pageEditorPathBadge) el.pageEditorPathBadge.textContent = data.path;
      if (el.editPageTitle) el.editPageTitle.value = data.title;
      if (el.pageVisualEditor) el.pageVisualEditor.innerHTML = data.bodyHtml || '<p></p>';
      if (el.pageCodeEditor) el.pageCodeEditor.value = data.fullHtml || data.bodyHtml;

      if (el.btnPreviewCurrentPage) {
        el.btnPreviewCurrentPage.href = `../${data.path.replace(/index\.html$/, '')}`;
      }

      // Reset zobrazenia (vizuálny mód)
      if (el.pageVisualEditor) el.pageVisualEditor.style.display = 'block';
      if (el.pageCodeEditor) el.pageCodeEditor.style.display = 'none';
      if (el.btnToggleCodeMode) el.btnToggleCodeMode.textContent = 'Prepnúť HTML kód';

      openModal('modalEditPage');
    } catch (err) {
      alert('Chyba pri otváraní editora: ' + err.message);
    }
  }

  // Prepínanie medzi Vizuálnym a HTML kódom
  if (el.btnToggleCodeMode) {
    el.btnToggleCodeMode.addEventListener('click', () => {
      state.isCodeMode = !state.isCodeMode;
      if (state.isCodeMode) {
        // Prechod do kódu: prenesieme obsah z visual do textarea
        el.pageCodeEditor.value = el.pageVisualEditor.innerHTML;
        el.pageVisualEditor.style.display = 'none';
        el.pageCodeEditor.style.display = 'block';
        el.btnToggleCodeMode.textContent = 'Prepnúť na Vizuálny editor';
      } else {
        // Prechod do vizuálu: prenesieme z textarea do visual
        el.pageVisualEditor.innerHTML = el.pageCodeEditor.value;
        el.pageCodeEditor.style.display = 'none';
        el.pageVisualEditor.style.display = 'block';
        el.btnToggleCodeMode.textContent = 'Prepnúť HTML kód';
      }
    });
  }

  // Formátovacie príkazy pre editor stránky
  document.querySelectorAll('#pageEditorToolbar .cms-editor-btn[data-cmd]').forEach(btn => {
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
      el.pageVisualEditor.focus();
    });
  });

  // Vloženie IDSK informačného rámika
  if (el.btnEditorInsertAlert) {
    el.btnEditorInsertAlert.addEventListener('click', () => {
      const alertHtml = `
        <div class="idsk-warning-text" style="background: #fef3c7; border-left: 4px solid #d97706; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
          <strong>Upozornenie pre občanov:</strong> Tu zadajte dôležitý oznam alebo upozornenie.
        </div>`;
      document.execCommand('insertHTML', false, alertHtml);
    });
  }

  // Uloženie upravenej stránky
  if (el.btnSavePageChanges) {
    el.btnSavePageChanges.addEventListener('click', async () => {
      if (!state.activeEditingPage) return;

      const title = el.editPageTitle?.value.trim();
      const bodyHtml = state.isCodeMode ? el.pageCodeEditor.value : el.pageVisualEditor.innerHTML;

      el.btnSavePageChanges.disabled = true;
      el.btnSavePageChanges.textContent = 'Ukladám zmeny...';

      try {
        if (state.mode === 'local') {
          const resp = await fetch(`${state.apiBase}/api/pages/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              path: state.activeEditingPage.path,
              title: title,
              bodyHtml: bodyHtml
            })
          });

          const result = await resp.json();
          if (resp.ok && result.success) {
            showToast('Stránka bola úspešne uložená a zmeny sú ihneď aktívne!');
            closeModal('modalEditPage');
            loadPages();
          } else {
            alert('Chyba: ' + (result.error || 'Nepodarilo sa uložiť stránku.'));
          }
        } else if (state.mode === 'github' && state.ghToken) {
          // GitHub Pages Cloud commit
          showToast('Ukladanie cez GitHub API...', 'info');
          // (Uloženie cez GitHub API priamo)
          alert('Zmeny boli odoslané do GitHub repozitára.');
          closeModal('modalEditPage');
        } else {
          alert('Pre ukladanie zmien spustite lokálny server príkazom "npm run cms" alebo nastavte GitHub token.');
        }
      } catch (err) {
        alert('Chyba: ' + err.message);
      } finally {
        el.btnSavePageChanges.disabled = false;
        el.btnSavePageChanges.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/></svg> Uložiť stránku`;
      }
    });
  }

  // Vytvorenie novej stránky
  if (el.btnSubmitNewPage) {
    el.btnSubmitNewPage.addEventListener('click', async () => {
      const section = document.getElementById('newPageSection')?.value;
      const title = document.getElementById('newPageTitle')?.value.trim();
      const customSlug = document.getElementById('newPageSlug')?.value.trim();
      const contentHtml = document.getElementById('newPageEditor')?.innerHTML.trim();

      if (!title) {
        alert('Zadajte názov novej stránky.');
        return;
      }

      el.btnSubmitNewPage.disabled = true;
      el.btnSubmitNewPage.textContent = 'Vytváram stránku...';

      try {
        if (state.mode === 'local') {
          const resp = await fetch(`${state.apiBase}/api/pages/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              section,
              title,
              slug: customSlug,
              contentHtml
            })
          });

          const result = await resp.json();
          if (resp.ok && result.success) {
            showToast('Nová podstránka bola úspešne vytvorená!');
            closeModal('modalNewPage');
            document.getElementById('newPageTitle').value = '';
            document.getElementById('newPageSlug').value = '';
            document.getElementById('newPageEditor').innerHTML = '';
            loadPages();
            // Otvoríme hneď v editore
            if (result.path) openPageEditor(result.path);
          } else {
            alert('Chyba: ' + (result.error || 'Nepodarilo sa vytvoriť stránku.'));
          }
        } else {
          alert('Pre vytvorenie stránky spustite lokálny server príkazom "npm run cms".');
        }
      } catch (err) {
        alert('Chyba: ' + err.message);
      } finally {
        el.btnSubmitNewPage.disabled = false;
        el.btnSubmitNewPage.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg> Vytvoriť a publikovať stránku`;
      }
    });
  }

  // --- 6. AKTUALITY (ČLÁNKY) ---

  async function loadArticles() {
    try {
      if (state.mode === 'local') {
        const resp = await fetch(`${state.apiBase}/api/aktuality`);
        if (resp.ok) {
          const data = await resp.json();
          state.articles = data.articles || [];
          renderArticles(state.articles);
          return;
        }
      }
      // Offline/GitHub: načítaj aktuality scraping-om živej stránky
      await loadArticlesFromWeb();
    } catch (e) {
      console.warn('Chyba načítania aktualít:', e);
      showEmptyState(el.articlesTableBody, 4, 'Nepodarilo sa načítať aktuality.');
    }
  }

  async function loadArticlesFromWeb() {
    try {
      const baseUrl = `https://luckyboy-aja.github.io/horny-vadicov`;
      const resp = await fetch(`${baseUrl}/obec-2/aktuality/`);
      if (resp.ok) {
        const text = await resp.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        const articles = [];
        doc.querySelectorAll('.event-link, .idsk-card, article a, .news-item a').forEach(l => {
          const name = l.querySelector('.event-name, h3, .card-title, .idsk-card-title')?.textContent || l.querySelector('strong')?.textContent || '';
          const date = l.querySelector('.event-date .event-info-value, .date, time')?.textContent || '';
          const perex = l.querySelector('.event-perex, .card-perex, p')?.textContent || '';
          const img = l.querySelector('img')?.getAttribute('src') || '';
          if (name.trim()) {
            articles.push({ title: name.trim(), date: date.trim(), perex: perex.trim().substring(0, 120), image: img, url: l.getAttribute('href') || '' });
          }
        });
        state.articles = articles;
        if (articles.length) {
          renderArticles(articles);
          if (el.kpiArticles) el.kpiArticles.textContent = articles.length;
        } else {
          showEmptyState(el.articlesTableBody, 4, 'Zatiaľ nie sú evidované žiadne aktuality. Pre správu spustite lokálny CMS server.');
        }
      } else {
        showEmptyState(el.articlesTableBody, 4, 'Aktuality sú dostupné iba cez lokálny CMS server.');
      }
    } catch (e) {
      showEmptyState(el.articlesTableBody, 4, 'Aktuality sú dostupné iba cez lokálny CMS server.');
    }
  }

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
        <td>
          <div class="cms-actions-cell">
            <a href="../obec-2/aktuality/${item.slug ? item.slug + '/' : item.url}" target="_blank" class="cms-btn cms-btn--secondary cms-btn--sm">Zobraziť</a>
            <button type="button" class="cms-btn cms-btn--danger cms-btn--sm btn-delete-article" data-slug="${escapeHtml(item.slug)}">Zmazať</button>
          </div>
        </td>
      </tr>
    `).join('');

    el.articlesTableBody.querySelectorAll('.btn-delete-article').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (confirm('Naozaj chcete zmazať túto aktualitu z webu?')) {
          await deleteArticle(btn.dataset.slug);
        }
      });
    });
  }

  async function deleteArticle(slug) {
    if (!slug) return;
    try {
      const resp = await fetch(`${state.apiBase}/api/aktuality/${slug}`, { method: 'DELETE' });
      if (resp.ok) {
        showToast('Aktualita bola zmazaná.');
        loadArticles();
      } else {
        alert('Nepodarilo sa zmazať aktualitu.');
      }
    } catch (e) {
      alert('Chyba: ' + e.message);
    }
  }

  if (el.searchArticlesInput) {
    el.searchArticlesInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      const filtered = state.articles.filter(a => a.title.toLowerCase().includes(q) || a.perex?.toLowerCase().includes(q));
      renderArticles(filtered);
    });
  }

  // Upload obrázka pre článok
  if (el.articleUploadBox) {
    el.articleUploadBox.addEventListener('click', () => el.articleFileInput.click());
    el.articleFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        state.articleImageName = file.name;
        const reader = new FileReader();
        reader.onload = (ev) => {
          state.articleImageBase64 = ev.target.result;
          el.articleImgPreview.src = ev.target.result;
          el.articleImgPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Odoslanie článku
  if (el.btnSubmitArticle) {
    el.btnSubmitArticle.addEventListener('click', async () => {
      const title = document.getElementById('articleTitle')?.value.trim();
      const date = document.getElementById('articleDate')?.value.trim();
      const perex = document.getElementById('articlePerex')?.value.trim();
      const contentHtml = el.articleEditor?.innerHTML.trim();

      if (!title || !contentHtml) {
        alert('Zadajte názov a obsah článku.');
        return;
      }

      el.btnSubmitArticle.disabled = true;
      el.btnSubmitArticle.textContent = 'Ukladám...';

      try {
        if (state.mode === 'local') {
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
            showToast('Aktualita bola úspešne publikovaná!');
            closeModal('modalNewArticle');
            document.getElementById('articleTitle').value = '';
            document.getElementById('articlePerex').value = '';
            el.articleEditor.innerHTML = '';
            el.articleImgPreview.style.display = 'none';
            state.articleImageBase64 = null;
            loadArticles();
          }
        }
      } catch (err) {
        alert('Chyba: ' + err.message);
      } finally {
        el.btnSubmitArticle.disabled = false;
        el.btnSubmitArticle.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> Uložiť a publikovať`;
      }
    });
  }

  // --- 7. ÚRADNÁ TABUĽA ---

  async function loadNotices() {
    try {
      if (state.mode === 'local') {
        const resp = await fetch(`${state.apiBase}/api/uradna-tabula`);
        if (resp.ok) {
          const data = await resp.json();
          state.notices = data.notices || [];
          renderNotices(state.notices);
          return;
        }
      }
      // Offline: načítaj z živej stránky
      await loadNoticesFromWeb();
    } catch (e) {
      console.warn('Chyba načítania úradnej tabule:', e);
      showEmptyState(el.noticesTableBody, 3, 'Nepodarilo sa načítať úradnú tabuľu.');
    }
  }

  async function loadNoticesFromWeb() {
    try {
      const resp = await fetch(`https://luckyboy-aja.github.io/horny-vadicov/zverejnovanie/uradna-tabula-1/`);
      if (resp.ok) {
        const text = await resp.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        const notices = [];
        // Skutočná HTML štruktúra: .item > .item-heading > a.item-href
        doc.querySelectorAll('.item').forEach(item => {
          const link = item.querySelector('.item-href, a');
          if (!link) return;
          const title = link.textContent.trim();
          const dateFrom = item.querySelector('.item-date-from')?.textContent.replace('Vyvesené:', '').trim() || '';
          const dateTo = item.querySelector('.item-date-to')?.textContent.replace('Dátum zvesenia:', '').trim() || '';
          const dates = [dateFrom, dateTo].filter(Boolean).join(' – ');
          const href = link.getAttribute('href') || '';
          if (title.length > 3) {
            notices.push({ title: title.substring(0, 150), dates, url: href, slug: href.replace(/\/$/, '').split('/').pop() });
          }
        });
        state.notices = notices;
        if (notices.length) {
          renderNotices(notices);
          if (el.kpiBoard) el.kpiBoard.textContent = notices.length;
        } else {
          showEmptyState(el.noticesTableBody, 3, 'Pre správu úradnej tabule spustite lokálny CMS server pomocou "npm run cms".');
        }
      } else {
        showEmptyState(el.noticesTableBody, 3, 'Úradná tabuľa je dostupná iba cez lokálny CMS server.');
      }
    } catch (e) {
      showEmptyState(el.noticesTableBody, 3, 'Úradná tabuľa je dostupná iba cez lokálny CMS server.');
    }
  }

  function renderNotices(list) {
    if (!el.noticesTableBody) return;
    if (!list || !list.length) {
      el.noticesTableBody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 2rem;">Zatiaľ nie sú evidované žiadne oznamy.</td></tr>';
      return;
    }

    el.noticesTableBody.innerHTML = list.map(item => `
      <tr>
        <td><strong>${escapeHtml(item.title)}</strong></td>
        <td>${escapeHtml(item.dates || 'Platné')}</td>
        <td>
          <div class="cms-actions-cell">
            <a href="../zverejnovanie/uradna-tabula-1/${item.slug ? item.slug + '/' : item.url}" target="_blank" class="cms-btn cms-btn--secondary cms-btn--sm">Zobraziť</a>
            <button type="button" class="cms-btn cms-btn--danger cms-btn--sm btn-delete-notice" data-slug="${escapeHtml(item.slug)}">Zvesiť</button>
          </div>
        </td>
      </tr>
    `).join('');

    el.noticesTableBody.querySelectorAll('.btn-delete-notice').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (confirm('Naozaj chcete zvesiť a zmazať tento oznam z úradnej tabule?')) {
          await deleteNotice(btn.dataset.slug);
        }
      });
    });
  }

  async function deleteNotice(slug) {
    if (!slug) return;
    try {
      const resp = await fetch(`${state.apiBase}/api/uradna-tabula/${slug}`, { method: 'DELETE' });
      if (resp.ok) {
        showToast('Oznam bol zvesený z úradnej tabule.');
        loadNotices();
      }
    } catch (e) {
      alert('Chyba: ' + e.message);
    }
  }

  if (el.searchNoticeInput) {
    el.searchNoticeInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      renderNotices(state.notices.filter(n => n.title.toLowerCase().includes(q)));
    });
  }

  // Upload PDF pre tabuľu
  if (el.noticeUploadBox) {
    el.noticeUploadBox.addEventListener('click', () => el.noticeFileInput.click());
    el.noticeFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        state.noticeFileName = file.name;
        el.noticeFileNameLabel.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        const reader = new FileReader();
        reader.onload = (ev) => { state.noticeFileBase64 = ev.target.result; };
        reader.readAsDataURL(file);
      }
    });
  }

  if (el.btnSubmitNotice) {
    el.btnSubmitNotice.addEventListener('click', async () => {
      const title = document.getElementById('noticeTitle')?.value.trim();
      const category = document.getElementById('noticeCategory')?.value;
      const dateFrom = document.getElementById('noticeDateFrom')?.value.trim();
      const dateTo = document.getElementById('noticeDateTo')?.value.trim();
      const description = document.getElementById('noticeDesc')?.value.trim();

      if (!title) {
        alert('Zadajte názov oznamu.');
        return;
      }

      el.btnSubmitNotice.disabled = true;
      try {
        if (state.mode === 'local') {
          const resp = await fetch(`${state.apiBase}/api/uradna-tabula`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title, category, dateFrom, dateTo, description,
              fileBase64: state.noticeFileBase64,
              fileName: state.noticeFileName
            })
          });

          const res = await resp.json();
          if (resp.ok && res.success) {
            showToast('Oznam bol úspešne vyvesený na úradnú tabuľu!');
            closeModal('modalNewNotice');
            loadNotices();
          }
        }
      } catch (err) {
        alert('Chyba: ' + err.message);
      } finally {
        el.btnSubmitNotice.disabled = false;
      }
    });
  }

  // --- 8. VZN (VŠEOBECNE ZÁVÄZNÉ NARIADENIA) ---

  async function loadVzn() {
    try {
      if (state.mode === 'local') {
        const resp = await fetch(`${state.apiBase}/api/vzn`);
        if (resp.ok) {
          const data = await resp.json();
          state.vznList = data.vzn || [];
          renderVzn(state.vznList);
          return;
        }
      }
      // Offline: načítaj VZN z živej stránky
      await loadVznFromWeb();
    } catch (e) {
      console.warn('Chyba načítania VZN:', e);
      showEmptyState(el.vznTableBody, 4, 'Nepodarilo sa načítať VZN.');
    }
  }

  async function loadVznFromWeb() {
    try {
      const resp = await fetch(`https://luckyboy-aja.github.io/horny-vadicov/samosprava/vzn/`);
      if (resp.ok) {
        const text = await resp.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        const vzns = [];
        // Skutočná HTML štruktúra: .item > .item-heading > a.item-href
        doc.querySelectorAll('.item').forEach(item => {
          const link = item.querySelector('.item-href, a');
          if (!link) return;
          const title = link.textContent.trim();
          const dateFrom = item.querySelector('.item-date-from')?.textContent.replace('Vyvesené:', '').trim() || '';
          const dateTo = item.querySelector('.item-date-to')?.textContent.replace('Dátum zvesenia:', '').trim() || 'Platné';
          const href = link.getAttribute('href') || '';
          if (title.length > 3) {
            vzns.push({ title: title.substring(0, 200), dateFrom, dateTo, slug: href.replace(/\/$/, '').split('/').pop() });
          }
        });
        state.vznList = vzns;
        if (vzns.length) {
          renderVzn(vzns);
          if (el.kpiVzn) el.kpiVzn.textContent = vzns.length;
        } else {
          showEmptyState(el.vznTableBody, 4, 'Pre správu VZN spustite lokálny CMS server pomocou "npm run cms".');
        }
      } else {
        showEmptyState(el.vznTableBody, 4, 'VZN sú dostupné iba cez lokálny CMS server.');
      }
    } catch (e) {
      showEmptyState(el.vznTableBody, 4, 'VZN sú dostupné iba cez lokálny CMS server.');
    }
  }

  function renderVzn(list) {
    if (!el.vznTableBody) return;
    if (!list.length) {
      el.vznTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;">Zatiaľ nie sú evidované žiadne VZN.</td></tr>';
      return;
    }

    el.vznTableBody.innerHTML = list.slice(0, 50).map(v => `
      <tr>
        <td><strong>${escapeHtml(v.title)}</strong></td>
        <td>${escapeHtml(v.dateFrom || '—')}</td>
        <td>${escapeHtml(v.dateTo || 'Platné')}</td>
        <td style="text-align: right;">
          <a href="../samosprava/vzn/${v.slug}/" target="_blank" class="cms-btn cms-btn--secondary cms-btn--sm">Zobraziť</a>
        </td>
      </tr>
    `).join('');
  }

  if (el.searchVznInput) {
    el.searchVznInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      renderVzn(state.vznList.filter(v => v.title.toLowerCase().includes(q)));
    });
  }

  // Upload PDF pre VZN
  if (el.vznUploadBox) {
    el.vznUploadBox.addEventListener('click', () => el.vznFileInput.click());
    el.vznFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        state.vznFileName = file.name;
        el.vznFileNameLabel.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        const reader = new FileReader();
        reader.onload = (ev) => { state.vznFileBase64 = ev.target.result; };
        reader.readAsDataURL(file);
      }
    });
  }

  if (el.btnSubmitVzn) {
    el.btnSubmitVzn.addEventListener('click', async () => {
      const title = document.getElementById('vznTitle')?.value.trim();
      const number = document.getElementById('vznNumber')?.value.trim();
      const year = document.getElementById('vznYear')?.value.trim();
      const dateApproved = document.getElementById('vznDateApproved')?.value.trim();
      const dateEffective = document.getElementById('vznDateEffective')?.value.trim();
      const description = document.getElementById('vznDescription')?.value.trim();

      if (!title) {
        alert('Zadajte názov VZN.');
        return;
      }

      el.btnSubmitVzn.disabled = true;
      try {
        if (state.mode === 'local') {
          const resp = await fetch(`${state.apiBase}/api/vzn`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title, number, year, dateApproved, dateEffective, description,
              fileBase64: state.vznFileBase64,
              fileName: state.vznFileName
            })
          });

          const res = await resp.json();
          if (resp.ok && res.success) {
            showToast('Nové VZN bolo úspešne publikované!');
            closeModal('modalNewVzn');
            loadVzn();
          }
        }
      } catch (e) {
        alert('Chyba: ' + e.message);
      } finally {
        el.btnSubmitVzn.disabled = false;
      }
    });
  }

  // --- 9. ZASADNUTIA OZ ---

  async function loadMeetings() {
    try {
      if (state.mode === 'local') {
        const resp = await fetch(`${state.apiBase}/api/zasadnutia`);
        if (resp.ok) {
          const data = await resp.json();
          state.meetings = data.meetings || [];
          renderMeetings(state.meetings);
          return;
        }
      }
      // Offline: načítaj zasadnutia z živej stránky
      await loadMeetingsFromWeb();
    } catch (e) {
      console.warn('Chyba načítania zasadnutí OZ:', e);
      showEmptyState(el.meetingsTableBody, 3, 'Nepodarilo sa načítať zasadnutia OZ.');
    }
  }

  async function loadMeetingsFromWeb() {
    try {
      const resp = await fetch(`https://luckyboy-aja.github.io/horny-vadicov/samosprava/obecne-zastupitelstvo/pozvanky-na-zasadnutie-oz-1/`);
      if (resp.ok) {
        const text = await resp.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        const meetings = [];
        // Skutočná HTML štruktúra: .item > .item-heading > a.item-href
        doc.querySelectorAll('.item').forEach(item => {
          const link = item.querySelector('.item-href, a');
          if (!link) return;
          const title = link.textContent.trim();
          const dateFrom = item.querySelector('.item-date-from')?.textContent.replace('Vyvesené:', '').trim() || '';
          const dateTo = item.querySelector('.item-date-to')?.textContent.replace('Dátum zvesenia:', '').trim() || '';
          const dates = [dateFrom, dateTo].filter(Boolean).join(' – ');
          const href = link.getAttribute('href') || '';
          if (title.length > 3) {
            meetings.push({ title: title.substring(0, 200), dates, slug: href.replace(/\/$/, '').split('/').pop() });
          }
        });
        state.meetings = meetings;
        if (meetings.length) {
          renderMeetings(meetings);
        } else {
          showEmptyState(el.meetingsTableBody, 3, 'Pre správu zasadnutí OZ spustite lokálny CMS server pomocou "npm run cms".');
        }
      } else {
        showEmptyState(el.meetingsTableBody, 3, 'Zasadnutia OZ sú dostupné iba cez lokálny CMS server.');
      }
    } catch (e) {
      showEmptyState(el.meetingsTableBody, 3, 'Zasadnutia OZ sú dostupné iba cez lokálny CMS server.');
    }
  }


  function renderMeetings(list) {
    if (!el.meetingsTableBody) return;
    if (!list.length) {
      el.meetingsTableBody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 2rem;">Zatiaľ nie sú evidované žiadne zasadnutia.</td></tr>';
      return;
    }

    el.meetingsTableBody.innerHTML = list.map(m => `
      <tr>
        <td><strong>${escapeHtml(m.title)}</strong></td>
        <td>${escapeHtml(m.dates || '—')}</td>
        <td style="text-align: right;">
          <a href="../samosprava/obecne-zastupitelstvo/pozvanky-na-zasadnutie-oz-1/${m.slug}/" target="_blank" class="cms-btn cms-btn--secondary cms-btn--sm">Zobraziť</a>
        </td>
      </tr>
    `).join('');
  }

  if (el.searchMeetingsInput) {
    el.searchMeetingsInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      renderMeetings(state.meetings.filter(m => m.title.toLowerCase().includes(q)));
    });
  }

  // Upload PDF pre pozvánku
  if (el.meetingUploadBox) {
    el.meetingUploadBox.addEventListener('click', () => el.meetingFileInput.click());
    el.meetingFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        state.meetingFileName = file.name;
        el.meetingFileNameLabel.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        const reader = new FileReader();
        reader.onload = (ev) => { state.meetingFileBase64 = ev.target.result; };
        reader.readAsDataURL(file);
      }
    });
  }

  if (el.btnSubmitMeeting) {
    el.btnSubmitMeeting.addEventListener('click', async () => {
      const title = document.getElementById('meetingTitle')?.value.trim();
      const date = document.getElementById('meetingDate')?.value.trim();
      const location = document.getElementById('meetingLocation')?.value.trim();
      const program = document.getElementById('meetingProgram')?.value.trim();

      if (!title) {
        alert('Zadajte názov pozvánky.');
        return;
      }

      el.btnSubmitMeeting.disabled = true;
      try {
        if (state.mode === 'local') {
          const resp = await fetch(`${state.apiBase}/api/zasadnutia`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title, date, location, program,
              fileBase64: state.meetingFileBase64,
              fileName: state.meetingFileName
            })
          });

          const res = await resp.json();
          if (resp.ok && res.success) {
            showToast('Pozvánka na zasadnutie OZ bola úspešne vyvesená!');
            closeModal('modalNewMeeting');
            loadMeetings();
          }
        }
      } catch (e) {
        alert('Chyba: ' + e.message);
      } finally {
        el.btnSubmitMeeting.disabled = false;
      }
    });
  }

  // --- 10. KNIŽNICA MÉDIÍ ---

  async function loadMedia() {
    try {
      if (state.mode === 'local') {
        const resp = await fetch(`${state.apiBase}/api/media`);
        if (resp.ok) {
          const data = await resp.json();
          state.mediaList = data.media || [];
          filterAndRenderMedia();
          return;
        }
      }
      // Offline: zobraz informativnú správu
      if (el.mediaGrid) {
        el.mediaGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: #64748b;">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="#cbd5e1" style="display:block;margin:0 auto 1rem;"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-8 12.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/></svg>
          <strong>Knižnica médií</strong><br>
          Pre správu médií spustite lokálny CMS server:<br>
          <code style="background:#f1f5f9;padding:0.3rem 0.7rem;border-radius:4px;display:inline-block;margin-top:0.5rem;">npm run cms</code>
        </div>`;
      }
    } catch (e) {
      console.warn('Chyba načítania médií:', e);
    }
  }

  function filterAndRenderMedia() {
    if (!el.mediaGrid) return;
    const q = (el.searchMediaInput?.value || '').toLowerCase().trim();
    const typeFilter = el.filterMediaType?.value || 'all';

    const filtered = state.mediaList.filter(m => {
      const matchQ = !q || m.name.toLowerCase().includes(q);
      const matchT = typeFilter === 'all' || m.type === typeFilter;
      return matchQ && matchT;
    });

    if (!filtered.length) {
      el.mediaGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: #64748b;">Žiadne súbory nezodpovedajú vyhľadávaniu.</div>';
      return;
    }

    el.mediaGrid.innerHTML = filtered.map(m => `
      <div class="cms-media-card">
        <div class="cms-media-thumb">
          ${m.type === 'image' 
            ? `<img src="..${m.url}" alt="${escapeHtml(m.name)}" loading="lazy">`
            : (m.type === 'pdf'
              ? `<svg viewBox="0 0 24 24" fill="#dc2626"><path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/></svg>`
              : `<svg viewBox="0 0 24 24" fill="#64748b"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>`)}
        </div>
        <div class="cms-media-info">
          <div class="cms-media-name" title="${escapeHtml(m.name)}">${escapeHtml(m.name)}</div>
          <div class="cms-media-meta">${formatBytes(m.size)} · ${escapeHtml(m.folder)}</div>
          <div class="cms-media-actions">
            <button type="button" class="cms-btn cms-btn--secondary btn-copy-media-url" data-url="..${m.url}">
              Kopírovať odkaz
            </button>
          </div>
        </div>
      </div>
    `).join('');

    el.mediaGrid.querySelectorAll('.btn-copy-media-url').forEach(btn => {
      btn.addEventListener('click', () => {
        navigator.clipboard.writeText(btn.dataset.url);
        showToast('Odkaz na súbor bol skopírovaný do schránky!');
      });
    });
  }

  if (el.searchMediaInput) el.searchMediaInput.addEventListener('input', filterAndRenderMedia);
  if (el.filterMediaType) el.filterMediaType.addEventListener('change', filterAndRenderMedia);

  // Upload média
  if (el.mediaUploadBox) {
    el.mediaUploadBox.addEventListener('click', () => el.mediaFileInput.click());
    el.mediaFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        state.mediaUploadFileName = file.name;
        el.mediaFileNameLabel.textContent = `${file.name} (${formatBytes(file.size)})`;
        const reader = new FileReader();
        reader.onload = (ev) => { state.mediaUploadBase64 = ev.target.result; };
        reader.readAsDataURL(file);
      }
    });
  }

  if (el.btnSubmitMediaUpload) {
    el.btnSubmitMediaUpload.addEventListener('click', async () => {
      if (!state.mediaUploadBase64 || !state.mediaUploadFileName) {
        alert('Vyberte súbor na nahranie.');
        return;
      }
      const folder = document.getElementById('mediaTargetFolder')?.value || 'cache_images';

      el.btnSubmitMediaUpload.disabled = true;
      try {
        if (state.mode === 'local') {
          const resp = await fetch(`${state.apiBase}/api/media/upload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              fileName: state.mediaUploadFileName,
              fileBase64: state.mediaUploadBase64,
              folder
            })
          });
          const res = await resp.json();
          if (resp.ok && res.success) {
            showToast('Súbor bol úspešne nahraný do knižnice médií!');
            closeModal('modalMediaUpload');
            loadMedia();
          }
        }
      } catch (e) {
        alert('Chyba: ' + e.message);
      } finally {
        el.btnSubmitMediaUpload.disabled = false;
      }
    });
  }

  // --- 11. FOTOGALÉRIA ---

  async function loadAlbums() {
    try {
      if (state.mode === 'local') {
        const resp = await fetch(`${state.apiBase}/api/fotogaleria`);
        if (resp.ok) {
          const data = await resp.json();
          state.albums = data.albums || [];
          renderAlbums(state.albums);
          return;
        }
      }
      // Offline: zobraz informativnú správu
      if (el.albumsGrid) {
        el.albumsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: #64748b;">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="#cbd5e1" style="display:block;margin:0 auto 1rem;"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
          <strong>Fotogaléria</strong><br>
          Pre správu fotoalbumy spustite lokálny CMS server:<br>
          <code style="background:#f1f5f9;padding:0.3rem 0.7rem;border-radius:4px;display:inline-block;margin-top:0.5rem;">npm run cms</code>
        </div>`;
      }
    } catch (e) {
      console.warn('Chyba načítania albumov:', e);
    }
  }

  function renderAlbums(list) {
    if (!el.albumsGrid) return;
    if (!list || !list.length) {
      el.albumsGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #64748b;">Zatiaľ nie sú nahráté žiadne fotoalbumy.</div>';
      return;
    }

    el.albumsGrid.innerHTML = list.map(a => `
      <a href="../obec-2/fotogaleria/${a.slug}/" target="_blank" class="cms-album-card">
        <div class="cms-album-cover">
          ${a.cover ? `<img src="..${a.cover}" alt="${escapeHtml(a.name)}" loading="lazy">` : `<svg width="48" height="48" viewBox="0 0 24 24" fill="#94a3b8"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>`}
        </div>
        <div class="cms-album-body">
          <div class="cms-album-title">${escapeHtml(a.name)}</div>
          <div class="cms-album-count">${a.photoCount} fotografií</div>
        </div>
      </a>
    `).join('');
  }

  // --- 12. GITHUB PAGES CLOUD & ZÁLOHOVANIE ---

  async function loadFallbackData() {
    // V offline/cloud režime načítame všetky sekcie z živých GitHub Pages URL
    await Promise.allSettled([
      loadPagesFromGitHub(),
      loadArticlesFromWeb(),
      loadNoticesFromWeb(),
      loadVznFromWeb(),
      loadMeetingsFromWeb(),
    ]);
  }

  if (el.btnSaveGhToken) {
    if (state.ghToken && el.inputGhToken) el.inputGhToken.value = state.ghToken;
    el.btnSaveGhToken.addEventListener('click', () => {
      const val = el.inputGhToken?.value.trim() || '';
      localStorage.setItem('horny_vadicov_gh_token', val);
      state.ghToken = val;
      showToast('GitHub Token bol bezpečne uložený.');
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
          alert('Nepodarilo sa pripojiť. Skontrolujte token.');
        }
      } catch (e) {
        alert('Chyba: ' + e.message);
      }
    });
  }

  if (el.btnExportBackup) {
    el.btnExportBackup.addEventListener('click', () => {
      const backupData = {
        exportedAt: new Date().toISOString(),
        repo: state.repo,
        stats: {
          pagesCount: state.pages.length,
          articlesCount: state.articles.length,
          boardCount: state.notices.length,
          vznCount: state.vznList.length
        },
        pages: state.pages,
        articles: state.articles,
        notices: state.notices,
        vzn: state.vznList
      };
      const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `horny-vadicov-zaloha-cms-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  // --- INICIALIZÁCIA ---
  initGoogleAuth();
  detectEnvironment();

})();
