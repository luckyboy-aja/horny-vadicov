import os
import re
import urllib.request
import ssl
import concurrent.futures
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

with open('public/obec-2/aktuality/index.html', 'r', encoding='utf-8') as f:
    aktuality_index_html = f.read()

# Extract all news links
news_links = re.findall(r'<a\s+href=["\'](https://www\.hornyvadicov\.sk/obec-2/aktuality/([^"\']+\.html))["\']', aktuality_index_html)
print(f"Nájdených {len(news_links)} odkazov na aktuality.")

# Load a template from an existing page
with open('public/obec-2/aktuality/index.html', 'r', encoding='utf-8') as f:
    page_template = f.read()

# We need the header up to idsk-subpage-body and the footer from </article>
header_part = page_template.split('<div class="idsk-subpage-body editor_content">')[0]
footer_part = page_template.split('</article>')[1]

images_dir = os.path.join('public', 'data', 'cache_images')
os.makedirs(images_dir, exist_ok=True)

def fetch_and_generate_article(item):
    full_url, filename = item
    slug = filename.replace('.html', '')
    dest_dir = os.path.join('public', 'obec-2', 'aktuality', slug)
    os.makedirs(dest_dir, exist_ok=True)
    dest_html_file = os.path.join(dest_dir, 'index.html')
    
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            live_html = resp.read().decode('utf-8', errors='ignore')
            
        # Extract title
        h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', live_html)
        title = h1_m.group(1).strip() if h1_m else slug
        
        # Extract date
        date_m = re.search(r'<span class="event-info-value[^"]*event-date">(.*?)</span>', live_html)
        date_str = date_m.group(1).strip() if date_m else ''
        
        # Extract main article body
        main_body_m = re.search(r'<div class="gcm-main">(.*?)</div>\s*</div>\s*</div>', live_html, re.DOTALL)
        body_content = main_body_m.group(1).strip() if main_body_m else '<p>Obsah článku sa nepodarilo načítať.</p>'
        
        # Download any embedded images
        embedded_imgs = re.findall(r'src=["\'](/[^"\']+\.(?:jpg|jpeg|png|gif)|/evt_image\.php\?[^"\']+)["\']', body_content)
        for img_src in set(embedded_imgs):
            img_url = 'https://www.hornyvadicov.sk' + img_src
            img_fname = f"aktuality_{slug}_{re.sub(r'[^a-zA-Z0-9]', '_', img_src[-20:])}.jpg"
            img_dest = os.path.join(images_dir, img_fname)
            
            if not os.path.exists(img_dest):
                try:
                    img_req = urllib.request.Request(img_url, headers=headers)
                    with urllib.request.urlopen(img_req, context=ctx, timeout=8) as img_resp:
                        with open(img_dest, 'wb') as img_fp:
                            img_fp.write(img_resp.read())
                except Exception as ie:
                    print(f"    Chyba obrázka {img_url}: {ie}")
                    
            # Rewrite in body
            body_content = body_content.replace(img_src, f"../../../data/cache_images/{img_fname}")
            
        # Remove navigation/breadcrumbs from original body if present
        body_content = re.sub(r'<nav aria-label="breadcrumb".*?</nav>', '', body_content, flags=re.DOTALL)
        body_content = re.sub(r'<div class="gcm-info".*?</div>', '', body_content, flags=re.DOTALL)
        
        # Construct IDSK subpage HTML
        # Adjust relative paths in header and footer from depth 2 (obec-2/aktuality) to depth 3 (obec-2/aktuality/slug)
        header_adj = header_part.replace('../../', '../../../')
        footer_adj = footer_part.replace('../../', '../../../')
        
        # Set title in header
        header_adj = re.sub(r'<title>.*?</title>', f'<title>{title} | Aktuality | Obec Horný Vadičov</title>', header_adj)
        header_adj = re.sub(r'<h1 class="idsk-subpage-content__title">.*?</h1>', f'<h1 class="idsk-subpage-content__title">{title}</h1>', header_adj)
        
        article_html = f"""{header_adj}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-article-meta mb-4 text-muted" style="font-size: 0.95rem; color: #555; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem;">
              <span><strong>Dátum zverejnenia:</strong> {date_str}</span>
            </div>
            
            <div class="idsk-article-content">
              {body_content}
            </div>

            <div class="mt-5 pt-3 border-top">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
                Späť na zoznam aktualít
              </a>
            </div>
          </div>
        </article>
{footer_adj}"""
        
        with open(dest_html_file, 'w', encoding='utf-8') as out_fp:
            out_fp.write(article_html)
            
        return full_url, f"./{slug}/", True
    except Exception as e:
        return full_url, None, False

print("Sťahujem a generujem stránky aktualít...")
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(fetch_and_generate_article, news_links))

success_map = {}
for full_url, local_rel, ok in results:
    if ok:
        success_map[full_url] = local_rel

print(f"Úspešne vygenerovaných: {len(success_map)} / {len(news_links)} aktualít.")

# Rewrite links in public/obec-2/aktuality/index.html
new_index_html = aktuality_index_html
for full_url, local_rel in success_map.items():
    new_index_html = new_index_html.replace(f'href="{full_url}"', f'href="{local_rel}"')
    new_index_html = new_index_html.replace(f"href='{full_url}'", f"href='{local_rel}'")

with open('public/obec-2/aktuality/index.html', 'w', encoding='utf-8') as fp:
    fp.write(new_index_html)

print("Prepojenie v public/obec-2/aktuality/index.html dokončené.")
