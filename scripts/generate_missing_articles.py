import os
import re
import urllib.parse
from pathlib import Path
import requests

public_dir = Path("public")

# Let's fix the fotogaleria link in dobrovolny-hasicsky-zbor first
dhz_file = "public/obec-2/organizacie-v-obci/dobrovolny-hasicsky-zbor/index.html"
if os.path.exists(dhz_file):
    with open(dhz_file, 'r', encoding='utf-8') as f:
        c = f.read()
    c = c.replace('brigada-chlapcov-dhz-na-cvicisku-hajnice-dna-28042023-126sk.html', '../../fotogaleria/brigada-chlapcov-dhz-na-cvicisku-hajnice-dna-28042-126/')
    with open(dhz_file, 'w', encoding='utf-8') as f:
        f.write(c)
    print("Fixed dhz fotogaleria link.")

# Read template for IDSK subpage
template_sample = """<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Obec Horný Vadičov</title>
  <link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{root_rel}assets/index-DUJfDM5J.css">
</head>
<body class="idsk-body">
  <header class="idsk-header" role="banner">
    <div class="idsk-header__brand">
      <div class="idsk-container">
        <div class="idsk-header__brand-content">
          <a href="{root_rel}" class="idsk-header__brand-logo" title="Návrat na úvodnú stránku">
            <img src="{root_rel}data/cache_images/crest.png" alt="Erb obce Horný Vadičov" class="idsk-header__logo-img">
            <div class="idsk-header__brand-text">
              <span class="idsk-header__brand-title">Horný Vadičov</span>
              <span class="idsk-header__brand-subtitle">Oficiálne stránky obce</span>
            </div>
          </a>
        </div>
      </div>
    </div>
  </header>

  <main id="main-content" class="idsk-main-content">
    <div class="idsk-container">
      <nav class="idsk-breadcrumbs" aria-label="Navigačná lišta (breadcrumbs)">
        <ol class="idsk-breadcrumbs__list">
          <li class="idsk-breadcrumbs__item"><a href="{root_rel}" class="idsk-breadcrumbs__link">Úvodná stránka</a></li>
          <li class="idsk-breadcrumbs__item" aria-current="page">{title}</li>
        </ol>
      </nav>

      <div class="idsk-subpage-layout">
        <article class="idsk-subpage-content" style="max-width: 900px; margin: 0 auto; width: 100%;">
          <div class="idsk-subpage-content__header">
            <h1 class="idsk-subpage-content__title">{title}</h1>
            {date_html}
          </div>

          <div class="idsk-subpage-body editor_content" style="font-size: 1.125rem; line-height: 1.6; margin-top: 1.5rem;">
            {body_content}
          </div>
          
          <div style="margin-top: 2rem; border-top: 1px solid #dee2e6; padding-top: 1rem;">
            <a href="javascript:history.back()" class="idsk-button idsk-button--secondary" style="display: inline-block; padding: 0.5rem 1rem; background: #f3f2f1; color: #0b0c0c; text-decoration: none; border-radius: 4px; font-weight: bold;">&larr; Späť</a>
          </div>
        </article>
      </div>
    </div>
  </main>

  <footer class="idsk-footer" role="contentinfo" style="margin-top: 4rem;">
    <div class="idsk-container">
      <div class="idsk-footer__bottom">
        <p class="idsk-footer__copyright">&copy; 2026 Obec Horný Vadičov. Všetky práva vyhradené. Vytvorené v štandarde IDSK 3.0.</p>
      </div>
    </div>
  </footer>
</body>
</html>
"""

missing_list = [
  'covid-19/manual-pre-obcanov-ako-zvladnut-ochorenie-covid-19-variant-omikron-v-domacnosti-29sk.html',
  'covid-19/informacie-k-ockovaniu-na-covid-19-30sk.html',
  'zverejnovanie/projekty/projekt-rekonstrukcia-sportoveho-ihriska-pri-zs-v-obci-horny-vadicov-561sk.html',
  'zverejnovanie/projekty/narodny-projekt-podpora-opatrovatelskej-sluzby-plagat-496sk.html',
  'zverejnovanie/projekty/zvysenie-kapacit-v-materskej-skole-horny-vadicov-plagat-339sk.html',
  'zverejnovanie/projekty/informacia-o-projekte-zvysenie-kapacit-v-ms-horny-vadicov-s-dokumentaciou-316sk.html',
  'zverejnovanie/projekty/informacia-o-projekte-znizenie-energetickej-narocnosti-ms-s-dokumentaciou-315sk.html',
  'zverejnovanie/projekty/znizenie-energetickej-narocnosti-materskej-skolky-horny-vadicov-plagat-310sk.html',
  'obec-2/sport/futbal-1/2-rocnik-placovy-futbalovy-turnaj-o-pohar-starostky-obce-horny-vadicov-na-pocest-jozefa-minarika-590sk.html',
  'obec-2/sport/futbal-1/futbalovy-placovy-turnaj-o-pohar-starostky-obce-horny-vadicov-423sk.html',
  'obec-2/sport/futbal-1/futbalovy-placovy-turnaj-1272025-414sk.html',
  'obec-2/sport/hokejbal-1/vianocny-hokejbalovy-turnaj-27122025-491sk.html',
  'obec-2/sport/hokejbal-1/hokejbalovy-turnaj-9rocnik-divina-luky-bears-1miesto-377sk.html',
  'obec-2/sport/hokejbal-1/velkonocny-hokejbalovy-turnaj-2042025-369sk.html',
  'obec-2/sport/hokejbal-1/hokejbalisti-vadicov-ziskali-1miesto-338sk.html',
  'obec-2/sport/hokejbal-1/hokejbalovy-turnaj-27122024-314sk.html',
  'obec-2/organizacie-v-obci/jednota-dochodcov-slovenska/stretnutie-clenov-jds-na-gulasovke-1182026-607sk.html',
  'obec-2/organizacie-v-obci/dobrovolny-hasicsky-zbor/aktuality-dhz-horny-vadicov-1/hasicsky-vikend-v-hornom-vadicove-8-982026-588sk.html',
  'obec-2/organizacie-v-obci/dobrovolny-hasicsky-zbor/aktuality-dhz-horny-vadicov-1/vycvik-pre-clenov-dhzo-22022026-v-obci-horny-vadicov-508sk.html',
  'obec-2/organizacie-v-obci/dobrovolny-hasicsky-zbor/aktuality-dhz-horny-vadicov-1/nasi-mladi-hasici-opat-uspesni-495sk.html',
  'obec-2/organizacie-v-obci/dobrovolny-hasicsky-zbor/aktuality-dhz-horny-vadicov-1/vysledok-ankety-dobrovolni-hasici-roka-2024-379sk.html',
  'obec-2/organizacie-v-obci/dobrovolny-hasicsky-zbor/aktuality-dhz-horny-vadicov-1/dhz-horny-vadicov-sa-dostal-do-top30-v-ankete-dobrovolny-hasicsky-zbor-roka-321sk.html',
  'obec-2/kniznica/aktuality/podujatie-s-kronikarom-mgr-stefanom-zajacom-520sk.html',
  'obec-2/kniznica/podujatia/citajme-si-2026-540sk.html',
  'obec-2/kniznica/podujatia/skolsky-klub-deti-v-kniznici-17032026-539sk.html',
  'obec-2/kniznica/podujatia/navsteva-deti-z-materskej-skoly-horny-vadicov-12032023-538sk.html',
  'obec-2/kniznica/podujatia/podujatie-kronika-obce-horny-vadicov-s-panom-kronikarom-mgrstefanom-zajacom-525sk.html',
  'obec-2/kniznica/podujatia/deti-zo-skolskeho-klubu-deti-v-kniznici-16042025-519sk.html',
  'obec-2/kniznica/podujatia/navsteva-deti-z-materskej-skoly-v-kniznici-518sk.html',
  'obec-2/kniznica/podujatia/otvorenie-kniznice-v-kulturno-informacnom-centre-s-kniznicou-horny-vadicov-517sk.html',
  'obec-2/kniznica/podujatia/15a1632023-skolkari-a-prvaci-zs-v-kniznici-383sk.html',
  'obec-2/kniznica/podujatia/1632023-navsteva-deti-zo-skolskeho-klubu-deti-382sk.html',
]

headers = {'User-Agent': 'Mozilla/5.0'}

for rel_path in missing_list:
    dest_file = os.path.join('public', rel_path.replace('/', os.sep))
    if os.path.exists(dest_file):
        continue
    
    url = f"https://www.hornyvadicov.sk/{rel_path}"
    print(f"Fetching {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            html = r.text
            # Extract title
            title_m = re.search(r'<title>(.*?)</title>', html)
            title = title_m.group(1).split('|')[0].strip() if title_m else "Oznam"
            
            # Extract main content
            content_m = re.search(r'<div class="editor_content readable">(.*?)<div class="cleaner"></div>', html, re.DOTALL)
            if not content_m:
                content_m = re.search(r'<div class="gcm-main">(.*?)<div class="cleaner"></div>', html, re.DOTALL)
            if not content_m:
                content_m = re.search(r'<div id="widget_\d+"[^>]*>(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
            
            body = content_m.group(1) if content_m else "<p>Obsah dokumentu.</p>"
            
            # Extract date if any
            date_m = re.search(r'<div class="date[^"]*">(.*?)</div>', html)
            date_html = f'<p class="idsk-metadata" style="color: #505a5f; margin-top: 0.5rem;">Dátum zverejnenia: {date_m.group(1).strip()}</p>' if date_m else ""
            
            # Compute root relative
            depth = len(rel_path.split('/')) - 1
            root_rel = '../' * depth if depth > 0 else './'
            
            # Clean external links in body
            body = body.replace('https://www.hornyvadicov.sk/', root_rel)
            body = body.replace('http://www.hornyvadicov.sk/', root_rel)
            
            # Download any images inside body
            for img_src in re.findall(r'<img [^>]*src=[\'"]([^\'"]+)[\'"]', body):
                if img_src.startswith('/data/') or img_src.startswith('data/'):
                    img_clean = img_src.lstrip('/')
                    local_img = os.path.join('public', img_clean.replace('/', os.sep))
                    if not os.path.exists(local_img):
                        os.makedirs(os.path.dirname(local_img), exist_ok=True)
                        try:
                            ir = requests.get(f"https://www.hornyvadicov.sk/{img_clean}", headers=headers, timeout=10)
                            if ir.status_code == 200:
                                with open(local_img, 'wb') as img_f:
                                    img_f.write(ir.content)
                                print(f"  Downloaded img: {img_clean}")
                        except Exception as ie:
                            print(f"  Error img {img_clean}: {ie}")
                    # rewrite img src to root_rel + img_clean
                    body = body.replace(img_src, root_rel + img_clean)

            page_html = template_sample.format(
                title=title,
                date_html=date_html,
                body_content=body,
                root_rel=root_rel
            )
            
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            with open(dest_file, 'w', encoding='utf-8') as pf:
                pf.write(page_html)
            print(f"  SAVED {dest_file}")
        else:
            print(f"  Status {r.status_code} for {url}")
    except Exception as e:
        print(f"  Error {url}: {e}")

print("Done processing missing articles.")
