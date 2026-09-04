"""
Download and create pages for the 4 missing news detail pages referenced from homepage
"""
import sys, re, os, json, requests
import lxml.html
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

# Import nav builder
sys.path.insert(0, 'scripts')
from nav_builder import render_navigation_markup

MISSING_PAGES = [
    "https://www.hornyvadicov.sk/zverejnovanie/uradna-tabula-1/oznamenie-o-doruceni-pisomnosti-pre-stefana-kacerika-bytom-horny-vadicov-1431.html",
    "https://www.hornyvadicov.sk/zverejnovanie/uradna-tabula-1/zverejnenie-zameru-prevodu-vlastnictva-majetku-obce-horny-vadicov-1430.html",
    "https://www.hornyvadicov.sk/zverejnovanie/uradna-tabula-1/uznesenia-z-neplanovaneho-zasadnutia-obecneho-zastupitelstva-13082026-1429.html",
    "https://www.hornyvadicov.sk/zverejnovanie/uradna-tabula-1/zapisnica-z-neplanovaneho-rokovania-obecneho-zastupitelstva-obce-horny-vadicov-13082026-1428.html",
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Load module map and rewrite map  
with open('scripts/module_download_map.json', 'r', encoding='utf-8') as f:
    module_map = json.load(f)

with open('scripts/url_rewrite_map.json', 'r', encoding='utf-8') as f:
    rewrite_map = json.load(f)

def clean_content(content, root_rel):
    # Apply rewrite map
    for orig, local in rewrite_map.items():
        if orig in content:
            target = root_rel + local.lstrip('/')
            content = content.replace(f'"{orig}"', f'"{target}"')
            content = content.replace(f"'{orig}'", f"'{target}'")
    
    # Replace absolute URLs
    content = content.replace('https://www.hornyvadicov.sk/', root_rel)
    content = content.replace('http://www.hornyvadicov.sk/', root_rel)
    
    # Fix relative / links
    content = re.sub(r'href=["\']/([a-zA-Z0-9_\-\./]+)["\']', f'href="{root_rel}\\1"', content)
    content = re.sub(r'src=["\']/([a-zA-Z0-9_\-\./\?=&]+)["\']', f'src="{root_rel}\\1"', content)
    
    # Fix module download links
    def fix_mod(m):
        href = m.group(1).replace('&amp;', '&')
        local = module_map.get(href)
        if local:
            return f'href="{root_rel}{local.lstrip("/")}"'
        return m.group(0)
    content = re.sub(r'href=["\'](/modules/file_storage/download\.php\?[^"\']*)["\']', fix_mod, content)
    
    return content

for url in MISSING_PAGES:
    print(f"\nFetching: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        
        doc = lxml.html.fromstring(r.text)
        
        # Get title
        h1 = doc.xpath('//h1/text()')
        title = h1[0].strip() if h1 else url.split('/')[-1]
        
        # Get content
        main_nodes = doc.xpath('//div[contains(@class, "gcm-main")]')
        content_html = ""
        if main_nodes:
            for h in main_nodes[0].xpath('.//h1'):
                h.drop_tree()
            content_html = lxml.html.tostring(main_nodes[0], encoding='unicode')
        
        # Determine local path
        url_path = url.replace('https://www.hornyvadicov.sk', '').rstrip('/')
        # Remove .html extension and create directory
        url_path = re.sub(r'\.html$', '', url_path)
        local_dir = Path('public') / url_path.lstrip('/')
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # Get root_rel
        parts = url_path.strip('/').split('/')
        depth = len(parts)
        root_rel = '../' * depth
        
        # Clean content
        cleaned = clean_content(content_html, root_rel)
        
        # Get nav
        nav_html = render_navigation_markup(root_rel, url_path)
        
        # Breadcrumbs
        bc_html = f'<li class="idsk-breadcrumbs__item"><a href="{root_rel}" class="idsk-breadcrumbs__link">Úvodná stránka</a></li>\n'
        bc_html += f'<li class="idsk-breadcrumbs__item"><a href="{root_rel}zverejnovanie/uradna-tabula-1/" class="idsk-breadcrumbs__link">Úradná tabuľa</a></li>\n'
        bc_html += f'<li class="idsk-breadcrumbs__item" aria-current="page">{title}</li>\n'
        
        html = f"""<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Obec Horný Vadičov (IDSK 3.0)</title>
  <link rel="icon" type="image/png" href="{root_rel}images/crest.png">
  <link rel="stylesheet" href="{root_rel}src/styles/idsk-tokens.css">
  <link rel="stylesheet" href="{root_rel}src/styles/idsk-components.css">
  <link rel="stylesheet" href="{root_rel}src/styles/main.css">
</head>
<body>
  <a href="#main-content" class="idsk-skip-link">Preskočiť na hlavný obsah</a>
  <div class="idsk-nav-wrapper">
    <div class="idsk-container">
      <nav class="idsk-nav" aria-label="Hlavná navigácia">
{nav_html}
      </nav>
    </div>
  </div>
  <main id="main-content">
    <div class="idsk-container">
      <nav class="idsk-breadcrumbs" aria-label="Navigačná lišta (breadcrumbs)">
        <ol class="idsk-breadcrumbs__list">
{bc_html}        </ol>
      </nav>
      <div class="idsk-subpage-layout--single">
        <article class="idsk-subpage-content">
          <div class="idsk-subpage-content__header">
            <h1 class="idsk-subpage-content__title">{title}</h1>
          </div>
          <div class="idsk-subpage-body editor_content">
{cleaned}
          </div>
          <div style="margin-top: 32px; border-top: 1px solid #E2E8F0; padding-top: 20px;">
            <a href="{root_rel}zverejnovanie/uradna-tabula-1/" class="idsk-btn idsk-btn--secondary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="transform: rotate(180deg);"><path d="M5 13h11.86l-5.43 5.43 1.42 1.42L21.14 12l-8.29-8.29-1.42 1.42L16.86 11H5v2z"/></svg>
              <span>Späť na Úradnú tabuľu</span>
            </a>
          </div>
        </article>
      </div>
    </div>
  </main>
  <script src="{root_rel}src/scripts/app.js"></script>
</body>
</html>"""
        
        target = local_dir / 'index.html'
        with open(target, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  -> Created: {target}")
        
    except Exception as e:
        print(f"  -> ERROR: {e}")

print("\nDone!")
