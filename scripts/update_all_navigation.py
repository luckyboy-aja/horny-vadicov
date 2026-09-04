import os
import sys
import re
from nav_builder import render_navigation_markup

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update index.html
with open('index.html', 'r', encoding='utf-8') as f:
    index_content = f.read()

index_nav_html = render_navigation_markup('./', '')

# Replace <ul class="idsk-nav__list" id="navList">...</ul> in index.html
new_index_content = re.sub(
    r'<ul class="idsk-nav__list" id="navList">.*?</ul>',
    index_nav_html.strip(),
    index_content,
    flags=re.DOTALL
)

if new_index_content != index_content:
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_index_content)
    print("Úspešne aktualizovaná navigácia v index.html!")
else:
    print("Upozornenie: Nepodarilo sa nájsť ul#navList v index.html")

# 2. Update scripts/generate_all_idsk_pages.py
with open('scripts/generate_all_idsk_pages.py', 'r', encoding='utf-8') as f:
    gen_content = f.read()

# Add import if missing
if 'from nav_builder import render_navigation_markup' not in gen_content:
    gen_content = "from nav_builder import render_navigation_markup\n" + gen_content

# In render_idsk_page, add nav_html = render_navigation_markup(root_rel, page.get('path', ''))
# And replace <ul class="idsk-nav__list" id="navList">...</ul> with {nav_html}
old_nav_block = """  <!-- 4. Hlavná navigácia -->
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
  </div>"""

new_nav_block = """  <!-- 4. Hlavná prístupná navigácia (IDSK 3.0 Mega-Menu Ribbon 1:1) -->
  <div class="idsk-nav-wrapper">
    <div class="idsk-container">
      <nav class="idsk-nav" aria-label="Hlavná navigácia">
        <button type="button" class="idsk-nav__toggle" id="navToggle" aria-expanded="false" aria-controls="navList">
          <svg viewBox="0 0 24 24"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
          <span>MENU</span>
        </button>
{nav_html}
      </nav>
    </div>
  </div>"""

if old_nav_block in gen_content:
    gen_content = gen_content.replace(old_nav_block, new_nav_block)
    # Also inject nav_html variable before html_template
    gen_content = gen_content.replace(
        "layout_class = \"idsk-subpage-layout\" if submenu else \"idsk-subpage-layout--single\"",
        "layout_class = \"idsk-subpage-layout\" if submenu else \"idsk-subpage-layout--single\"\n    nav_html = render_navigation_markup(root_rel, page.get('path', ''))"
    )
    with open('scripts/generate_all_idsk_pages.py', 'w', encoding='utf-8') as f:
        f.write(gen_content)
    print("Úspešne aktualizovaný skript scripts/generate_all_idsk_pages.py!")
else:
    print("Upozornenie: Nepodarilo sa nájsť old_nav_block v scripts/generate_all_idsk_pages.py")
