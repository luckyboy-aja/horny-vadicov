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

# ==================== 1. VZN ====================
vzn_base = os.path.join('public', 'samosprava', 'vzn')
vzn_storage = os.path.join('public', 'data', 'vzn')
os.makedirs(vzn_storage, exist_ok=True)

with open(os.path.join(vzn_base, 'index.html'), 'r', encoding='utf-8') as f:
    vzn_index_html = f.read()

vzn_matches = re.findall(r'<a\s+class="item-href"\s+href=["\'](https://www\.hornyvadicov\.sk/samosprava/vzn/([^"\'?]+)(?:\?[^"\']*)?)["\']', vzn_index_html)
print(f"Nájdených {len(vzn_matches)} odkazov na VZN.")

header_vzn = vzn_index_html.split('<div class="idsk-subpage-body editor_content">')[0]
footer_vzn = vzn_index_html.split('</article>')[1]

def make_safe_slug(filename):
    clean = filename.replace('.html', '')
    # Extract ID at the end if present
    id_m = re.search(r'-(\d+)$', clean)
    item_id = id_m.group(1) if id_m else ''
    # Shorten slug to max 50 chars to avoid Windows MAX_PATH limit
    short_slug = clean[:50].rstrip('-')
    if item_id and not short_slug.endswith(item_id):
        short_slug = f"{short_slug}-{item_id}"
    return short_slug

def process_vzn(item):
    full_url, filename = item
    short_slug = make_safe_slug(filename)
    dest_dir = os.path.join(vzn_base, short_slug)
    os.makedirs(dest_dir, exist_ok=True)
    dest_html = os.path.join(dest_dir, 'index.html')
    
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            live_html = resp.read().decode('utf-8', errors='ignore')
            
        h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', live_html)
        title = h1_m.group(1).strip() if h1_m else short_slug
        
        main_m = re.search(r'<div class="gcm-main">(.*?)</div>\s*</div>\s*</div>', live_html, re.DOTALL)
        content_html = main_m.group(1).strip() if main_m else '<p>Obsah VZN.</p>'
        
        file_links = re.findall(r'href=["\'](/data/[^"\']+\.(?:pdf|docx?|jpg|png))["\']', live_html)
        downloaded = []
        for fl in set(file_links):
            f_url = 'https://www.hornyvadicov.sk' + fl
            fname = os.path.basename(fl)
            dest_f = os.path.join(vzn_storage, fname)
            if not os.path.exists(dest_f):
                try:
                    f_req = urllib.request.Request(f_url, headers=headers)
                    with urllib.request.urlopen(f_req, context=ctx, timeout=10) as f_resp:
                        with open(dest_f, 'wb') as out_f:
                            out_f.write(f_resp.read())
                except Exception as fe:
                    print(f"    Chyba sťahovania {f_url}: {fe}")
            downloaded.append((fname, f"../../../data/vzn/{fname}"))
            content_html = content_html.replace(fl, f"../../../data/vzn/{fname}")
            
        content_html = re.sub(r'<nav aria-label="breadcrumb".*?</nav>', '', content_html, flags=re.DOTALL)
        content_html = re.sub(r'<div class="gcm-info".*?</div>', '', content_html, flags=re.DOTALL)
        
        header_adj = header_vzn.replace('../../', '../../../')
        footer_adj = footer_vzn.replace('../../', '../../../')
        header_adj = re.sub(r'<title>.*?</title>', f'<title>{title} | VZN | Obec Horný Vadičov</title>', header_adj)
        header_adj = re.sub(r'<h1 class="idsk-subpage-content__title">.*?</h1>', f'<h1 class="idsk-subpage-content__title">{title}</h1>', header_adj)
        
        att_box = ""
        if downloaded:
            att_box = '<div class="idsk-attachments mt-4 p-3 border rounded bg-light"><h3>Dokument na stiahnutie:</h3><ul class="list-unstyled">'
            for fn, rel_l in downloaded:
                att_box += f'<li class="mb-2"><a href="{rel_l}" target="_blank" rel="noopener noreferrer" download class="idsk-button idsk-button--secondary"><i class="fas fa-file-pdf mr-1"></i> Stiahnuť {fn}</a></li>'
            att_box += '</ul></div>'
            
        page_code = f"""{header_adj}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-vzn-content">
              {content_html}
            </div>
            {att_box}
            <div class="mt-5 pt-3 border-top">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
                Späť na zoznam VZN
              </a>
            </div>
          </div>
        </article>
{footer_adj}"""
        with open(dest_html, 'w', encoding='utf-8') as out_fp:
            out_fp.write(page_code)
        return full_url, f"./{short_slug}/", True
    except Exception as e:
        print(f"Error {full_url}: {e}")
        return full_url, None, False

print("Sťahujem a generujem podstránky VZN...")
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    vzn_results = list(executor.map(process_vzn, vzn_matches))

vzn_map = {u: l for u, l, ok in vzn_results if ok}
print(f"Úspešne vygenerovaných {len(vzn_map)} / {len(vzn_matches)} VZN.")

for u, l in vzn_map.items():
    vzn_index_html = vzn_index_html.replace(f'href="{u}"', f'href="{l}"')
    vzn_index_html = vzn_index_html.replace(f"href='{u}'", f"href='{l}'")

with open(os.path.join(vzn_base, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(vzn_index_html)
print("VZN zoznam prepojený.")


# ==================== 2. POZVÁNKY OZ ====================
pozv_base = os.path.join('public', 'samosprava', 'obecne-zastupitelstvo', 'pozvanky-na-zasadnutie-oz-1')
pozv_storage = os.path.join('public', 'data', 'pozvanky')
os.makedirs(pozv_storage, exist_ok=True)

with open(os.path.join(pozv_base, 'index.html'), 'r', encoding='utf-8') as f:
    pozv_index_html = f.read()

pozv_matches = re.findall(r'<a\s+class="item-href"\s+href=["\'](https://www\.hornyvadicov\.sk/samosprava/obecne-zastupitelstvo/pozvanky-na-zasadnutie-oz-1/([^"\'?]+)(?:\?[^"\']*)?)["\']', pozv_index_html)
print(f"\nNájdených {len(pozv_matches)} odkazov na Pozvánky OZ.")

header_pozv = pozv_index_html.split('<div class="idsk-subpage-body editor_content">')[0]
footer_pozv = pozv_index_html.split('</article>')[1]

def process_pozvanka(item):
    full_url, filename = item
    short_slug = make_safe_slug(filename)
    dest_dir = os.path.join(pozv_base, short_slug)
    os.makedirs(dest_dir, exist_ok=True)
    dest_html = os.path.join(dest_dir, 'index.html')
    
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            live_html = resp.read().decode('utf-8', errors='ignore')
            
        h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', live_html)
        title = h1_m.group(1).strip() if h1_m else short_slug
        
        main_m = re.search(r'<div class="gcm-main">(.*?)</div>\s*</div>\s*</div>', live_html, re.DOTALL)
        content_html = main_m.group(1).strip() if main_m else '<p>Obsah pozvánky.</p>'
        
        file_links = re.findall(r'href=["\'](/data/[^"\']+\.(?:pdf|docx?|jpg|png))["\']', live_html)
        downloaded = []
        for fl in set(file_links):
            f_url = 'https://www.hornyvadicov.sk' + fl
            fname = os.path.basename(fl)
            dest_f = os.path.join(pozv_storage, fname)
            if not os.path.exists(dest_f):
                try:
                    f_req = urllib.request.Request(f_url, headers=headers)
                    with urllib.request.urlopen(f_req, context=ctx, timeout=10) as f_resp:
                        with open(dest_f, 'wb') as out_f:
                            out_f.write(f_resp.read())
                except Exception as fe:
                    print(f"    Chyba sťahovania {f_url}: {fe}")
            downloaded.append((fname, f"../../../../data/pozvanky/{fname}"))
            content_html = content_html.replace(fl, f"../../../../data/pozvanky/{fname}")
            
        content_html = re.sub(r'<nav aria-label="breadcrumb".*?</nav>', '', content_html, flags=re.DOTALL)
        content_html = re.sub(r'<div class="gcm-info".*?</div>', '', content_html, flags=re.DOTALL)
        
        header_adj = header_pozv.replace('../../../', '../../../../')
        footer_adj = footer_pozv.replace('../../../', '../../../../')
        header_adj = re.sub(r'<title>.*?</title>', f'<title>{title} | Pozvánky OZ | Obec Horný Vadičov</title>', header_adj)
        header_adj = re.sub(r'<h1 class="idsk-subpage-content__title">.*?</h1>', f'<h1 class="idsk-subpage-content__title">{title}</h1>', header_adj)
        
        att_box = ""
        if downloaded:
            att_box = '<div class="idsk-attachments mt-4 p-3 border rounded bg-light"><h3>Príloha / Pozvánka na stiahnutie:</h3><ul class="list-unstyled">'
            for fn, rel_l in downloaded:
                att_box += f'<li class="mb-2"><a href="{rel_l}" target="_blank" rel="noopener noreferrer" download class="idsk-button idsk-button--secondary"><i class="fas fa-file-pdf mr-1"></i> Stiahnuť {fn}</a></li>'
            att_box += '</ul></div>'
            
        page_code = f"""{header_adj}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-pozvanka-content">
              {content_html}
            </div>
            {att_box}
            <div class="mt-5 pt-3 border-top">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
                Späť na zoznam pozvánok
              </a>
            </div>
          </div>
        </article>
{footer_adj}"""
        with open(dest_html, 'w', encoding='utf-8') as out_fp:
            out_fp.write(page_code)
        return full_url, f"./{short_slug}/", True
    except Exception as e:
        print(f"Error {full_url}: {e}")
        return full_url, None, False

print("Sťahujem a generujem podstránky Pozvánok OZ...")
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    pozv_results = list(executor.map(process_pozvanka, pozv_matches))

pozv_map = {u: l for u, l, ok in pozv_results if ok}
print(f"Úspešne vygenerovaných {len(pozv_map)} / {len(pozv_matches)} Pozvánok OZ.")

for u, l in pozv_map.items():
    pozv_index_html = pozv_index_html.replace(f'href="{u}"', f'href="{l}"')
    pozv_index_html = pozv_index_html.replace(f"href='{u}'", f"href='{l}'")

with open(os.path.join(pozv_base, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(pozv_index_html)
print("Pozvánky OZ zoznam prepojený.")
