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

base_dir = os.path.join('public', 'zverejnovanie', 'uradna-tabula-1')
storage_dir = os.path.join('public', 'data', 'uredni_deska')
os.makedirs(storage_dir, exist_ok=True)

with open(os.path.join(base_dir, 'index.html'), 'r', encoding='utf-8') as f:
    tabula_index_html = f.read()

# Find all notice links
matches = re.findall(r'<a\s+class="item-href"\s+href=["\'](https://www\.hornyvadicov\.sk/zverejnovanie/uradna-tabula-1/([^"\'?]+)(?:\?[^"\']*)?)["\']', tabula_index_html)
print(f"Nájdených {len(matches)} odkazov na úradnú tabuľu.")

# Template from uradna-tabula-1/index.html
header_part = tabula_index_html.split('<div class="idsk-subpage-body editor_content">')[0]
footer_part = tabula_index_html.split('</article>')[1]

def fetch_and_generate_notice(item):
    full_url, filename = item
    slug = filename.replace('.html', '')
    dest_dir = os.path.join(base_dir, slug)
    os.makedirs(dest_dir, exist_ok=True)
    dest_html_file = os.path.join(dest_dir, 'index.html')
    
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            live_html = resp.read().decode('utf-8', errors='ignore')
            
        # Extract title
        h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', live_html)
        title = h1_m.group(1).strip() if h1_m else slug
        
        # Extract dates
        dates_m = re.findall(r'<span class="item-date[^"]*">(.*?)</span>', live_html)
        dates_str = " · ".join([d.strip() for d in dates_m]) if dates_m else ''
        
        # Extract main content / attachment area
        main_m = re.search(r'<div class="gcm-main">(.*?)</div>\s*</div>\s*</div>', live_html, re.DOTALL)
        content_html = main_m.group(1).strip() if main_m else '<p>Obsah oznamu.</p>'
        
        # Look for attached files in content or in file lists
        file_links = re.findall(r'href=["\'](/data/uredni_deska/[^"\']+|/data/[^"\']+\.(?:pdf|docx?|jpg|jpeg|png))["\']', live_html)
        downloaded_files = []
        for fl in set(file_links):
            f_url = 'https://www.hornyvadicov.sk' + fl
            fname = os.path.basename(fl)
            dest_file = os.path.join(storage_dir, fname)
            
            if not os.path.exists(dest_file):
                try:
                    f_req = urllib.request.Request(f_url, headers=headers)
                    with urllib.request.urlopen(f_req, context=ctx, timeout=10) as f_resp:
                        with open(dest_file, 'wb') as out_f:
                            out_f.write(f_resp.read())
                except Exception as fe:
                    print(f"    Chyba sťahovania {f_url}: {fe}")
            
            downloaded_files.append((fname, f"../../../data/uredni_deska/{fname}"))
            content_html = content_html.replace(fl, f"../../../data/uredni_deska/{fname}")
            
        # Clean up navigation
        content_html = re.sub(r'<nav aria-label="breadcrumb".*?</nav>', '', content_html, flags=re.DOTALL)
        content_html = re.sub(r'<div class="gcm-info".*?</div>', '', content_html, flags=re.DOTALL)
        
        # Build IDSK page
        header_adj = header_part.replace('../../', '../../../')
        footer_adj = footer_part.replace('../../', '../../../')
        
        header_adj = re.sub(r'<title>.*?</title>', f'<title>{title} | Úradná tabuľa | Obec Horný Vadičov</title>', header_adj)
        header_adj = re.sub(r'<h1 class="idsk-subpage-content__title">.*?</h1>', f'<h1 class="idsk-subpage-content__title">{title}</h1>', header_adj)
        
        attachments_box = ""
        if downloaded_files:
            attachments_box = '<div class="idsk-attachments mt-4 p-3 border rounded bg-light"><h3>Prílohy na stiahnutie:</h3><ul class="list-unstyled">'
            for fn, rel_l in downloaded_files:
                attachments_box += f'<li class="mb-2"><a href="{rel_l}" target="_blank" rel="noopener noreferrer" download class="idsk-button idsk-button--secondary"><i class="fas fa-file-download mr-1"></i> Stiahnuť {fn}</a></li>'
            attachments_box += '</ul></div>'
            
        notice_html = f"""{header_adj}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-notice-meta mb-4 text-muted" style="font-size: 0.95rem; color: #555; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem;">
              <span><strong>Oznam úradnej tabule:</strong> {dates_str}</span>
            </div>
            
            <div class="idsk-notice-content">
              {content_html}
            </div>
            
            {attachments_box}

            <div class="mt-5 pt-3 border-top">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
                Späť na Úradnú tabuľu
              </a>
            </div>
          </div>
        </article>
{footer_adj}"""
        
        with open(dest_html_file, 'w', encoding='utf-8') as out_fp:
            out_fp.write(notice_html)
            
        return full_url, f"./{slug}/", True
    except Exception as e:
        return full_url, None, False

print("Sťahujem a generujem stránky úradnej tabule...")
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch_and_generate_notice, matches))

success_map = {}
for full_url, local_rel, ok in results:
    if ok:
        success_map[full_url] = local_rel

print(f"Úspešne vygenerovaných: {len(success_map)} / {len(matches)} podstránok úradnej tabule.")

# Rewrite links in public/zverejnovanie/uradna-tabula-1/index.html
new_index_html = tabula_index_html
for full_url, local_rel in success_map.items():
    new_index_html = new_index_html.replace(f'href="{full_url}"', f'href="{local_rel}"')
    new_index_html = new_index_html.replace(f"href='{full_url}'", f"href='{local_rel}'")

with open(os.path.join(base_dir, 'index.html'), 'w', encoding='utf-8') as fp:
    fp.write(new_index_html)

print("Prepojenie v public/zverejnovanie/uradna-tabula-1/index.html dokončené.")
