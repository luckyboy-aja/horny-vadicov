import os
import sys
import json
import re
import html
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding='utf-8')

DATA_FILE = 'scripts/scraped_data.json'
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

pages = data.get('pages', [])
print(f"Generujem IDSK 3.0 stránky pre {len(pages)} podstránok...")

# Načítame existujúcu mapu prepisov, ak existuje
rewrite_map = {}
if os.path.exists('scripts/url_rewrite_map.json'):
    with open('scripts/url_rewrite_map.json', 'r', encoding='utf-8') as f:
        rewrite_map = json.load(f)

def clean_html_content(content, root_rel):
    """Upraví cesty v autentickom HTML tak, aby odkazovali na lokálne súbory a podstránky."""
    if not content:
        return ""
    
    # 1. Prepis odkazov na dokumenty a obrázky podľa rewrite_map
    for orig, local in rewrite_map.items():
        if orig in content:
            # Napr. local je "/data/editor/something.pdf" -> root_rel + "data/editor/something.pdf"
            target = root_rel + local.lstrip('/')
            content = content.replace(f'"{orig}"', f'"{target}"')
            content = content.replace(f"'{orig}'", f"'{target}'")

    # 2. Prepis interných odkazov z www.hornyvadicov.sk na relatívne cesty v našom webe
    content = content.replace('https://www.hornyvadicov.sk/', root_rel)
    content = content.replace('http://www.hornyvadicov.sk/', root_rel)
    
    # 3. Prepis relatívnych odkazov začínajúcich / na root_rel
    # napr. href="/obec-2/o-obci/" -> href="../../obec-2/o-obci/"
    content = re.sub(r'href=["\']/([a-zA-Z0-9_\-\./]+)["\']', r'href="' + root_rel + r'\1"', content)
    content = re.sub(r'src=["\']/([a-zA-Z0-9_\-\./\?=&]+)["\']', r'src="' + root_rel + r'\1"', content)
    
    return content

def get_root_rel(path):
    parts = [p for p in path.strip('/').split('/') if p]
    depth = len(parts)
    if depth == 0:
        return './'
    return '../' * depth

# Šablóna IDSK 3.0 podstránky
def render_idsk_page(page, root_rel):
    title = page.get('title', 'Obec Horný Vadičov')
    breadcrumbs = page.get('breadcrumbs', [])
    submenu = page.get('submenu', [])
    raw_content = page.get('content_html', '')
    
    cleaned_content = clean_html_content(raw_content, root_rel)
    
    # Generovanie breadcrumb položiek
    bc_html = f'<li class="idsk-breadcrumbs__item"><a href="{root_rel}" class="idsk-breadcrumbs__link">Úvodná stránka</a></li>\n'
    for idx, b in enumerate(breadcrumbs):
        b_text = b.get('text', '').strip()
        b_link = b.get('link', '').strip()
        if not b_text or b_text.lower() in ['úvodná stránka', 'uvodna stranka']:
            continue
        is_last = (idx == len(breadcrumbs) - 1)
        if is_last or not b_link:
            bc_html += f'        <li class="idsk-breadcrumbs__item" aria-current="page">{b_text}</li>\n'
        else:
            href = root_rel + b_link.lstrip('/')
            bc_html += f'        <li class="idsk-breadcrumbs__item"><a href="{href}" class="idsk-breadcrumbs__link">{b_text}</a></li>\n'

    # Generovanie bočného menu (Sidebar)
    sidebar_html = ""
    if submenu:
        sidebar_html += f"""
        <aside class="idsk-subpage-sidebar">
          <h2 class="idsk-subpage-sidebar__header">Menu sekcie</h2>
          <ul class="idsk-subpage-sidebar__nav">
"""
        for s in submenu:
            s_text = s.get('text', '').strip()
            s_href = s.get('href', '').strip()
            s_active = s.get('active', False)
            if not s_text or not s_href:
                continue
            active_class = " is-active" if s_active or s_href == page.get('path') else ""
            href = root_rel + s_href.lstrip('/')
            sidebar_html += f'            <li><a href="{href}" class="idsk-subpage-sidebar__link{active_class}">{s_text}</a></li>\n'
        sidebar_html += """          </ul>
        </aside>
"""

    layout_class = "idsk-subpage-layout" if submenu else "idsk-subpage-layout--single"

    html_template = f"""<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Obec Horný Vadičov (IDSK 3.0)</title>
  <meta name="description" content="{title} - Oficiálne webové sídlo obce Horný Vadičov v štandarde IDSK 3.0">
  <link rel="icon" type="image/png" href="{root_rel}images/crest.png">
  <link rel="stylesheet" href="{root_rel}src/styles/idsk-tokens.css">
  <link rel="stylesheet" href="{root_rel}src/styles/idsk-components.css">
  <link rel="stylesheet" href="{root_rel}src/styles/main.css">
</head>
<body>
  <!-- 1. Bezbariérový odkaz na hlavný obsah (WCAG 2.1 AA) -->
  <a href="#main-content" class="idsk-skip-link">Preskočiť na hlavný obsah</a>

  <!-- 2. Štátny a samosprávny identifikačný prúžok (IDSK 3.0) -->
  <div class="idsk-gov-bar" role="region" aria-label="Identifikátor verejnej správy">
    <div class="idsk-container">
      <div class="idsk-gov-bar__inner">
        <div class="idsk-gov-bar__brand">
          <span class="idsk-gov-bar__flag" aria-hidden="true">
            <span class="idsk-gov-bar__flag-strip idsk-gov-bar__flag-strip--white"></span>
            <span class="idsk-gov-bar__flag-strip idsk-gov-bar__flag-strip--blue"></span>
            <span class="idsk-gov-bar__flag-strip idsk-gov-bar__flag-strip--red"></span>
          </span>
          <span class="idsk-gov-bar__text">Oficiálna stránka samosprávy Slovenskej republiky</span>
          <button type="button" class="idsk-gov-bar__info-btn" id="govBarToggle" aria-expanded="false" aria-controls="govBarInfo">
            Ako spoznáte oficiálnu stránku?
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M7 10l5 5 5-5z"/>
            </svg>
          </button>
        </div>

        <div class="idsk-gov-bar__tools">
          <div class="idsk-gov-bar__a11y-group" role="group" aria-label="Nástroje prístupnosti">
            <button type="button" class="idsk-a11y-btn" id="btnContrast" title="Prepnúť režim vysokého kontrastu">Kontrast</button>
            <button type="button" class="idsk-a11y-btn" id="btnFontIncrease" title="Zväčšiť písmo">A+</button>
            <button type="button" class="idsk-a11y-btn" id="btnFontReset" title="Pôvodná veľkosť písma">A</button>
          </div>
          <div class="idsk-gov-bar__lang">
            <span style="font-weight: 700; color: var(--idsk-color-primary);">SK</span>
            <span style="color: #A0AEC0;"> | </span>
            <a href="{root_rel}en/" style="color: var(--idsk-color-text-secondary); text-decoration: none;" title="English version">EN</a>
          </div>
        </div>
      </div>

      <div class="idsk-gov-bar__collapsible-info" id="govBarInfo">
        <p><strong>Oficiálna doména samosprávy SR:</strong> Táto stránka je oficiálnym webovým sídlom obce Horný Vadičov v zmysle Zákona č. 369/1990 Zb. o obecnom zriadení. Používa bezpečné šifrované spojenie (HTTPS) a spĺňa štandardy jednotného dizajn manuálu elektronických služieb (IDSK 3.0).</p>
      </div>
    </div>
  </div>

  <!-- 3. Hlavná hlavička obce -->
  <header class="idsk-header" role="banner">
    <div class="idsk-container">
      <div class="idsk-header__inner">
        <a href="{root_rel}" class="idsk-header__logo" aria-label="Návrat na úvodnú stránku obce Horný Vadičov">
          <img src="{root_rel}images/crest.png" alt="Erb obce Horný Vadičov" class="idsk-header__crest">
          <div class="idsk-header__text">
            <span class="idsk-header__title">Obec Horný Vadičov</span>
            <span class="idsk-header__subtitle">Okres Kysucké Nové Mesto | Žilinský kraj</span>
          </div>
        </a>

        <div class="idsk-header__actions">
          <div class="idsk-header__contacts">
            <a href="tel:+421414229221" class="idsk-contact-chip" title="Zavolajte na obecný úrad">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
              <span>041 / 422 92 21</span>
            </a>
            <a href="mailto:urad@hornyvadicov.sk" class="idsk-contact-chip" title="Napíšte nám e-mail">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
              <span>urad@hornyvadicov.sk</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </header>

  <!-- 4. Hlavná navigácia -->
  <div class="idsk-nav-wrapper">
    <div class="idsk-container">
      <nav class="idsk-nav" aria-label="Hlavná navigácia">
        <ul class="idsk-nav__list" id="navList">
          <li class="idsk-nav__item"><a href="{root_rel}obec-2/o-obci/" class="idsk-nav__link"><span>Obec</span></a></li>
          <li class="idsk-nav__item"><a href="{root_rel}samosprava/starostka-obce/" class="idsk-nav__link"><span>Samospráva</span></a></li>
          <li class="idsk-nav__item"><a href="{root_rel}zverejnovanie/uradna-tabula-1/" class="idsk-nav__link"><span>Zverejňovanie</span></a></li>
          <li class="idsk-nav__item"><a href="{root_rel}projekty/" class="idsk-nav__link"><span>Projekty</span></a></li>
          <li class="idsk-nav__item"><a href="{root_rel}uzemny-plan/" class="idsk-nav__link"><span>Územný plán</span></a></li>
          <li class="idsk-nav__item"><a href="{root_rel}volby-a-referendum/" class="idsk-nav__link"><span>Voľby</span></a></li>
          <li class="idsk-nav__item"><a href="{root_rel}obec-2/organizacie-v-obci/" class="idsk-nav__link"><span>Organizácie</span></a></li>
          <li class="idsk-nav__item"><a href="{root_rel}kontakt/uradne-hodiny/" class="idsk-nav__link"><span>Kontakt</span></a></li>
        </ul>
      </nav>
    </div>
  </div>

  <!-- Hlavný obsah podstránky -->
  <main id="main-content">
    <div class="idsk-container">
      <nav class="idsk-breadcrumbs" aria-label="Navigačná lišta (breadcrumbs)">
        <ol class="idsk-breadcrumbs__list">
{bc_html}        </ol>
      </nav>

      <div class="{layout_class}">
{sidebar_html}
        <article class="idsk-subpage-content">
          <div class="idsk-subpage-content__header">
            <h1 class="idsk-subpage-content__title">{title}</h1>
          </div>

          <div class="idsk-subpage-body editor_content">
{cleaned_content}
          </div>

          <div style="margin-top: 32px; border-top: 1px solid #E2E8F0; padding-top: 20px;">
            <a href="{root_rel}" class="idsk-btn idsk-btn--secondary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="transform: rotate(180deg);"><path d="M5 13h11.86l-5.43 5.43 1.42 1.42L21.14 12l-8.29-8.29-1.42 1.42L16.86 11H5v2z"/></svg>
              <span>Návrat na úvodnú stránku</span>
            </a>
          </div>
        </article>
      </div>
    </div>
  </main>

  <!-- 5. IDSK Pätička -->
  <footer class="idsk-footer" role="contentinfo">
    <div class="idsk-footer__tricolor" aria-hidden="true">
      <span class="idsk-footer__tricolor-strip idsk-footer__tricolor-strip--white"></span>
      <span class="idsk-footer__tricolor-strip idsk-footer__tricolor-strip--blue"></span>
      <span class="idsk-footer__tricolor-strip idsk-footer__tricolor-strip--red"></span>
    </div>

    <div class="idsk-container">
      <div class="idsk-footer__grid">
        <div class="idsk-footer__col">
          <div class="idsk-footer__brand">
            <img src="{root_rel}images/crest.png" alt="Erb obce Horný Vadičov" class="idsk-footer__crest">
            <div>
              <h3 class="idsk-footer__title">Obec Horný Vadičov</h3>
              <p class="idsk-footer__text">Samosprávny orgán obce v okrese Kysucké Nové Mesto.</p>
            </div>
          </div>
        </div>

        <div class="idsk-footer__col">
          <h4 class="idsk-footer__heading">Kontakt a sídlo</h4>
          <address class="idsk-footer__address">
            <p>Obecný úrad Horný Vadičov</p>
            <p>Horný Vadičov 160</p>
            <p>023 45 Horný Vadičov</p>
            <p>Tel: <a href="tel:+421414229221">041 / 422 92 21</a></p>
            <p>E-mail: <a href="mailto:urad@hornyvadicov.sk">urad@hornyvadicov.sk</a></p>
          </address>
        </div>

        <div class="idsk-footer__col">
          <h4 class="idsk-footer__heading">Dôležité odkazy</h4>
          <ul class="idsk-footer__links">
            <li><a href="{root_rel}zverejnovanie/uradna-tabula-1/">Elektronická úradná tabuľa</a></li>
            <li><a href="{root_rel}samosprava/gdpr-infozakon/">Ochrana osobných údajov (GDPR)</a></li>
            <li><a href="{root_rel}zverejnovanie/zmluvy-faktury-objednavky/">Zmluvy, faktúry a objednávky</a></li>
            <li><a href="{root_rel}zverejnovanie/verejne-obstaravanie/profil/">Verejné obstarávanie</a></li>
          </ul>
        </div>
      </div>

      <div class="idsk-footer__bottom">
        <p class="idsk-footer__copyright">&copy; 2026 Obec Horný Vadičov. Všetky práva vyhradené. Vytvorené v štandarde IDSK 3.0.</p>
        <p class="idsk-footer__provider">Technický prevádzkovateľ: <strong><a href="https://www.prosoft.sk" target="_blank" rel="noopener noreferrer" style="color: #FFFFFF; text-decoration: underline;">PROSOFT</a></strong></p>
      </div>
    </div>
  </footer>

  <script src="{root_rel}src/scripts/app.js"></script>
</body>
</html>"""
    return html_template

# Spustenie generovania pre všetky podstránky
generated_count = 0
for p in pages:
    path = p.get('path', '').strip('/')
    if not path:
        continue # Hlavná stránka je už index.html v koreni
        
    root_rel = get_root_rel(path)
    page_html = render_idsk_page(p, root_rel)
    
    # Uložíme do public/path/index.html
    target_dir = os.path.join('public', path)
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, 'index.html')
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(page_html)
    generated_count += 1

print(f"\nÚspešne vygenerovaných {generated_count} IDSK 3.0 podstránok v priečinku public/!")
