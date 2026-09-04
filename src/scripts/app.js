// Interaktivita pre web obce Horný Vadičov v štandarde IDSK 3.0

document.addEventListener('DOMContentLoaded', () => {
  initGovBar();
  initAccessibility();
  initMobileNav();
  initTabs();
  initNewsFilter();
  initNoticeboardSearch();
  initNewsModal();
  initLiveSearch();
});

// 1. Identifikačný pruh štátnej správy a samosprávy
function initGovBar() {
  const toggleBtn = document.getElementById('govBarToggle');
  const infoPanel = document.getElementById('govBarInfo');

  if (toggleBtn && infoPanel) {
    toggleBtn.addEventListener('click', () => {
      const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
      toggleBtn.setAttribute('aria-expanded', !isExpanded);
      infoPanel.classList.toggle('is-open', !isExpanded);
    });
  }
}

// 2. Prístupnosť (A11y) - Kontrast a Veľkosť písma
function initAccessibility() {
  const contrastBtn = document.getElementById('btnContrast');
  const fontIncreaseBtn = document.getElementById('btnFontIncrease');
  const fontResetBtn = document.getElementById('btnFontReset');

  // Cyklovanie kontrastu: normal -> bw -> yellow -> normal
  let contrastState = 0; // 0 = normal, 1 = black-white, 2 = yellow-black
  
  if (contrastBtn) {
    contrastBtn.addEventListener('click', () => {
      document.body.classList.remove('high-contrast-bw', 'high-contrast-yellow');
      contrastState = (contrastState + 1) % 3;
      
      if (contrastState === 1) {
        document.body.classList.add('high-contrast-bw');
        contrastBtn.setAttribute('aria-label', 'Vysoký kontrast: Čierno-biely aktívny');
      } else if (contrastState === 2) {
        document.body.classList.add('high-contrast-yellow');
        contrastBtn.setAttribute('aria-label', 'Vysoký kontrast: Žlto-čierny aktívny');
      } else {
        contrastBtn.setAttribute('aria-label', 'Normálny kontrast');
      }
    });
  }

  // Zmena veľkosti písma
  let fontScale = 0; // 0 = normal, 1 = lg, 2 = xl
  if (fontIncreaseBtn) {
    fontIncreaseBtn.addEventListener('click', () => {
      document.body.classList.remove('font-scale-lg', 'font-scale-xl');
      fontScale = (fontScale + 1) % 3;
      if (fontScale === 1) {
        document.body.classList.add('font-scale-lg');
      } else if (fontScale === 2) {
        document.body.classList.add('font-scale-xl');
      }
    });
  }

  if (fontResetBtn) {
    fontResetBtn.addEventListener('click', () => {
      document.body.classList.remove('font-scale-lg', 'font-scale-xl');
      fontScale = 0;
    });
  }
}

// 3. Mobilná navigácia
function initMobileNav() {
  const toggle = document.getElementById('navToggle');
  const menuList = document.getElementById('navList');

  if (toggle && menuList) {
    toggle.addEventListener('click', () => {
      const isOpen = menuList.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', isOpen);
    });

    // Zatvorenie menu po kliknutí na odkaz
    menuList.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        menuList.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }
}

// 4. Filtrovanie aktualít
function initNewsFilter() {
  const filterBtns = document.querySelectorAll('.idsk-filter-btn');
  const cards = document.querySelectorAll('.idsk-news-grid .idsk-card');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');

      const filter = btn.getAttribute('data-filter');

      cards.forEach(card => {
        const category = card.getAttribute('data-category');
        if (filter === 'all' || category === filter) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
}

// 5. Vyhľadávanie v Úradnej tabuli
function initNoticeboardSearch() {
  const searchInput = document.getElementById('tableSearchInput');
  const tableRows = document.querySelectorAll('#noticeboardTable tbody tr');

  if (searchInput && tableRows.length) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase().trim();

      tableRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(term)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  }
}

// 6. Globálne živé vyhľadávanie
function initLiveSearch() {
  const globalSearch = document.getElementById('globalSearchInput');
  if (globalSearch) {
    globalSearch.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const term = globalSearch.value.trim();
        if (term) {
          // Scroll to news or noticeboard and filter
          const newsSection = document.getElementById('aktuality');
          if (newsSection) {
            newsSection.scrollIntoView({ behavior: 'smooth' });
          }
          const noticeSearch = document.getElementById('tableSearchInput');
          if (noticeSearch) {
            noticeSearch.value = term;
            noticeSearch.dispatchEvent(new Event('input'));
          }
        }
      }
    });
  }
}

// 7. Modálne okno s detailom oznamu
function initNewsModal() {
  const modalBackdrop = document.getElementById('newsModal');
  const modalTitle = document.getElementById('modalTitle');
  const modalDate = document.getElementById('modalDate');
  const modalText = document.getElementById('modalText');
  const modalImg = document.getElementById('modalImg');
  const modalClose = document.getElementById('modalClose');

  if (!modalBackdrop) return;

  document.querySelectorAll('.js-open-modal').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const card = trigger.closest('.idsk-card');
      if (!card) return;

      const title = card.querySelector('.idsk-card__title').textContent;
      const date = card.querySelector('.idsk-card__meta').textContent.trim();
      const perex = card.querySelector('.idsk-card__perex').textContent;
      const fullText = card.getAttribute('data-fulltext') || perex;
      const img = card.querySelector('.idsk-card__image');

      modalTitle.textContent = title;
      modalDate.textContent = date;
      modalText.innerHTML = fullText.replace(/\n/g, '<br><br>');
      
      if (img) {
        modalImg.src = img.src;
        modalImg.alt = title;
        modalImg.style.display = 'block';
      } else {
        modalImg.style.display = 'none';
      }

      modalBackdrop.classList.add('is-open');
      modalBackdrop.setAttribute('aria-hidden', 'false');
      modalClose.focus();
    });
  });

  function closeModal() {
    modalBackdrop.classList.remove('is-open');
    modalBackdrop.setAttribute('aria-hidden', 'true');
  }

  if (modalClose) {
    modalClose.addEventListener('click', closeModal);
  }

  modalBackdrop.addEventListener('click', (e) => {
    if (e.target === modalBackdrop) {
      closeModal();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalBackdrop.classList.contains('is-open')) {
      closeModal();
    }
  });
}

// 8. Záložkový systém (Aktuality, Úradná tabuľa, OVS, Rozhlas)
function initTabs() {
  const tabBtns = document.querySelectorAll('.js-tab-btn');
  const tabPanes = document.querySelectorAll('.js-tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');

      tabBtns.forEach(b => {
        b.classList.remove('is-active');
        b.setAttribute('aria-selected', 'false');
      });

      btn.classList.add('is-active');
      btn.setAttribute('aria-selected', 'true');

      tabPanes.forEach(pane => {
        if (pane.id === targetTab) {
          pane.style.display = 'block';
        } else {
          pane.style.display = 'none';
        }
      });
    });
  });
}

