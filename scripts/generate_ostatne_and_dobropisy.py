import os
import re
import urllib.request
import ssl
import concurrent.futures

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

storage_dir = os.path.join('public', 'data', 'ostatne')
os.makedirs(storage_dir, exist_ok=True)

# 1. Fix self links in zmluvy
for z_path in [
    'public/zverejnovanie/zmluvy-faktury-objednavky/index.html',
    'public/zverejnovanie/zmluvy-faktury-objednavky/faktury/index.html',
    'public/zverejnovanie/zmluvy-faktury-objednavky/objednavky/index.html'
]:
    if os.path.exists(z_path):
        with open(z_path, 'r', encoding='utf-8') as fp:
            c = fp.read()
        c = c.replace('https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/zmluvy.html?filterClear=1', './')
        c = c.replace('https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/zmluvy.html', './')
        with open(z_path, 'w', encoding='utf-8') as fp:
            fp.write(c)
print("Self-links v zmluvy opravené.")

# 2. Process Ostatne dokumenty, Dobropisy, Zakazky
sections = [
    ('ostatne-dokumenty', 'public/zverejnovanie/ostatne-dokumenty'),
    ('dobropisy', 'public/zverejnovanie/dobropisy'),
    ('zakazky', 'public/zverejnovanie/verejne-obstaravanie/zakazky')
]

def make_safe_slug(filename):
    clean = filename.replace('.html', '')
    id_m = re.search(r'-(\d+)$', clean)
    item_id = id_m.group(1) if id_m else ''
    short_slug = clean[:50].rstrip('-')
    if item_id and not short_slug.endswith(item_id):
        short_slug = f"{short_slug}-{item_id}"
    return short_slug

for sec_name, sec_base in sections:
    idx_path = os.path.join(sec_base, 'index.html')
    if not os.path.exists(idx_path):
        continue
    with open(idx_path, 'r', encoding='utf-8') as fp:
        html = fp.read()
        
    matches = re.findall(r'<a\s+class="item-href"\s+href=["\'](https://www\.hornyvadicov\.sk/[^"\']+/([^"\'?]+)(?:\?[^"\']*)?)["\']', html)
    if not matches:
        matches = re.findall(r'<a\s+href=["\'](https://www\.hornyvadicov\.sk/[^"\']+/([^"\'?]+)(?:\?[^"\']*)?)["\']', html)
    
    # filter out self or modules
    valid_matches = [(u, fn) for u, fn in matches if not any(x in u for x in ['download.php', 'javascript:', '#', 'zmluvy.html'])]
    print(f"\nSpracovávam {sec_name}: {len(valid_matches)} položiek...")
    
    header_part = html.split('<div class="idsk-subpage-body editor_content">')[0]
    footer_part = html.split('</article>')[1]
    
    url_map = {}
    for full_url, filename in valid_matches:
        short_slug = make_safe_slug(filename)
        dest_dir = os.path.join(sec_base, short_slug)
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = os.path.join(dest_dir, 'index.html')
        
        try:
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                live = resp.read().decode('utf-8', errors='ignore')
                
            h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', live)
            title = h1_m.group(1).strip() if h1_m else short_slug
            
            main_m = re.search(r'<div class="gcm-main">(.*?)</div>\s*</div>\s*</div>', live, re.DOTALL)
            content = main_m.group(1).strip() if main_m else '<p>Obsah dokumentu.</p>'
            
            file_links = re.findall(r'href=["\'](/data/[^"\']+\.(?:pdf|docx?|jpg|png))["\']', live)
            downloaded = []
            for fl in set(file_links):
                f_url = 'https://www.hornyvadicov.sk' + fl
                fname = os.path.basename(fl)
                f_dest = os.path.join(storage_dir, fname)
                if not os.path.exists(f_dest):
                    try:
                        f_req = urllib.request.Request(f_url, headers=headers)
                        with urllib.request.urlopen(f_req, context=ctx, timeout=10) as f_r:
                            with open(f_dest, 'wb') as ofp:
                                ofp.write(f_r.read())
                    except Exception as fe:
                        print(f"    Chyba sťahovania {f_url}: {fe}")
                # calculate rel path from subpage to storage
                depth = sec_base.count('/') + 1
                prefix = '../' * (depth + 1)
                downloaded.append((fname, f"{prefix}data/ostatne/{fname}"))
                content = content.replace(fl, f"{prefix}data/ostatne/{fname}")
                
            content = re.sub(r'<nav aria-label="breadcrumb".*?</nav>', '', content, flags=re.DOTALL)
            content = re.sub(r'<div class="gcm-info".*?</div>', '', content, flags=re.DOTALL)
            
            header_adj = header_part.replace('../../', '../../../').replace('../../../../', '../../../../../')
            footer_adj = footer_part.replace('../../', '../../../').replace('../../../../', '../../../../../')
            header_adj = re.sub(r'<title>.*?</title>', f'<title>{title} | Obec Horný Vadičov</title>', header_adj)
            header_adj = re.sub(r'<h1 class="idsk-subpage-content__title">.*?</h1>', f'<h1 class="idsk-subpage-content__title">{title}</h1>', header_adj)
            
            att_box = ""
            if downloaded:
                att_box = '<div class="idsk-attachments mt-4 p-3 border rounded bg-light"><h3>Dokumenty na stiahnutie:</h3><ul class="list-unstyled">'
                for fn, rel_l in downloaded:
                    att_box += f'<li class="mb-2"><a href="{rel_l}" target="_blank" rel="noopener noreferrer" download class="idsk-button idsk-button--secondary"><i class="fas fa-file-pdf mr-1"></i> Stiahnuť {fn}</a></li>'
                att_box += '</ul></div>'
                
            sub_page = f"""{header_adj}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-doc-content">
              {content}
            </div>
            {att_box}
            <div class="mt-5 pt-3 border-top">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
                Späť na zoznam
              </a>
            </div>
          </div>
        </article>
{footer_adj}"""
            with open(dest_file, 'w', encoding='utf-8') as out_fp:
                out_fp.write(sub_page)
            url_map[full_url] = f"./{short_slug}/"
        except Exception as e:
            print(f"  Chyba {full_url}: {e}")
            
    # Rewrite links in index.html
    for u, loc in url_map.items():
        html = html.replace(f'href="{u}"', f'href="{loc}"')
        html = html.replace(f"href='{u}'", f"href='{loc}'")
    with open(idx_path, 'w', encoding='utf-8') as fp:
        fp.write(html)
    print(f"  {sec_name} prepojené ({len(url_map)} podstránok).")
