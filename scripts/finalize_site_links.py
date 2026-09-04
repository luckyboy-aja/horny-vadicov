"""
finalize_site_links.py
1. Updates 6 paginated pages to use ?page=all so all archive records are included.
2. Resolves all remaining 1202 relative links:
   - Local directory/file links -> relative {root_rel}
   - Remote archive/detail records -> https://www.hornyvadicov.sk/... with target="_blank"
   - Forms -> action="./" or original site
3. Verifies zero broken links remain.
"""

import os
import sys
import re
import json
import requests
import lxml.html
from pathlib import Path
from urllib.parse import unquote

sys.stdout.reconfigure(encoding='utf-8')

BASE_ORIGIN = "https://www.hornyvadicov.sk"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

PUBLIC_DIR = Path("public")

# Load maps
module_map = {}
if Path('scripts/module_download_map.json').exists():
    with open('scripts/module_download_map.json', 'r', encoding='utf-8') as f:
        module_map = json.load(f)

rewrite_map = {}
if Path('scripts/url_rewrite_map.json').exists():
    with open('scripts/url_rewrite_map.json', 'r', encoding='utf-8') as f:
        rewrite_map = json.load(f)

def get_root_rel(html_file):
    rel = Path(html_file).relative_to(PUBLIC_DIR)
    depth = len(rel.parts) - 1
    return "./" if depth == 0 else "../" * depth

def clean_extracted_html(content_html, root_rel):
    """Clean CMS HTML: fix module downloads, e_downloads, rewrite maps, etc."""
    if not content_html:
        return ""
    
    # 1. Fix module downloads
    def sub_module(m):
        q = m.group(1)
        href_raw = m.group(2)
        href_dec = href_raw.replace('&amp;', '&')
        loc = module_map.get(href_dec) or module_map.get(href_raw)
        if loc:
            return f'href={q}{root_rel}{loc.lstrip("/")}{q}'
        return f'href={q}{BASE_ORIGIN}{href_dec}{q} target="_blank" rel="noopener noreferrer"'
    
    content_html = re.sub(
        r'href=(["\'])(\/modules\/file_storage\/download\.php\?[^"\']*)\1',
        sub_module,
        content_html
    )
    
    # 2. Fix e_download
    def sub_edownload(m):
        q = m.group(1)
        href_raw = m.group(2)
        href_dec = href_raw.replace('&amp;', '&')
        fmatch = re.search(r'file=([^&"\']*)', href_dec)
        if fmatch:
            fpath = unquote(fmatch.group(1)).lstrip('/')
            if (PUBLIC_DIR / fpath).exists():
                return f'href={q}{root_rel}{fpath}{q}'
        return f'href={q}{BASE_ORIGIN}{href_dec}{q} target="_blank" rel="noopener noreferrer"'
    
    content_html = re.sub(
        r'href=(["\'])(\/e_download\.php\?[^"\']*)\1',
        sub_edownload,
        content_html
    )
    
    # 3. Apply rewrite map
    for orig, local in rewrite_map.items():
        if orig in content_html:
            target = root_rel + local.lstrip('/')
            content_html = content_html.replace(f'"{orig}"', f'"{target}"')
            content_html = content_html.replace(f"'{orig}'", f"'{target}'")
            
    return content_html

PAGINATED_PAGES = [
    {
        'path': 'obec-2/aktuality',
        'url': f'{BASE_ORIGIN}/obec-2/aktuality/?page=all',
        'file': PUBLIC_DIR / 'obec-2/aktuality/index.html'
    },
    {
        'path': 'obec-2/fotogaleria',
        'url': f'{BASE_ORIGIN}/obec-2/fotogaleria/?page=all',
        'file': PUBLIC_DIR / 'obec-2/fotogaleria/index.html'
    },
    {
        'path': 'samosprava/obecne-zastupitelstvo/uznesenia-oz',
        'url': f'{BASE_ORIGIN}/samosprava/obecne-zastupitelstvo/uznesenia-oz/?page=all',
        'file': PUBLIC_DIR / 'samosprava/obecne-zastupitelstvo/uznesenia-oz/index.html'
    },
    {
        'path': 'samosprava/obecne-zastupitelstvo/zapisnice',
        'url': f'{BASE_ORIGIN}/samosprava/obecne-zastupitelstvo/zapisnice/?page=all',
        'file': PUBLIC_DIR / 'samosprava/obecne-zastupitelstvo/zapisnice/index.html'
    },
    {
        'path': 'volby-a-referendum',
        'url': f'{BASE_ORIGIN}/volby-a-referendum/?page=all',
        'file': PUBLIC_DIR / 'volby-a-referendum/index.html'
    },
    {
        'path': 'zverejnovanie/zmluvy-faktury-objednavky',
        'url': f'{BASE_ORIGIN}/zverejnovanie/zmluvy-faktury-objednavky/?page=all',
        'file': PUBLIC_DIR / 'zverejnovanie/zmluvy-faktury-objednavky/index.html'
    },
]

print("=== 1. Aktualizujem paginovane stranky na kompletny obsah (?page=all) ===")
for p in PAGINATED_PAGES:
    print(f"Stahujem {p['url']}...")
    try:
        r = requests.get(p['url'], headers=HEADERS, timeout=20)
        r.encoding = 'utf-8'
        if r.status_code != 200:
            print(f"  Chyba: status {r.status_code}")
            continue
            
        doc = lxml.html.fromstring(r.text)
        main_nodes = doc.xpath('//div[contains(@class, "gcm-main")]')
        if not main_nodes:
            main_nodes = doc.xpath('//div[contains(@class, "editor_content")]')
            
        if not main_nodes:
            print("  Nenasiel sa hlavny obsah!")
            continue
            
        # Odstranit zdvojene h1
        for h in main_nodes[0].xpath('.//h1'):
            h.drop_tree()
            
        content_html = lxml.html.tostring(main_nodes[0], encoding='unicode')
        root_rel = get_root_rel(p['file'])
        cleaned = clean_extracted_html(content_html, root_rel)
        
        # Nahradit v existujucom subore medzi <div class="idsk-subpage-body editor_content"> a </div>
        orig_file_content = p['file'].read_text(encoding='utf-8')
        
        pattern = r'(<div class="idsk-subpage-body editor_content">)(.*?)(</div>\s*<div style="margin-top: 32px;)'
        m = re.search(pattern, orig_file_content, re.S)
        if m:
            new_file_content = orig_file_content[:m.start(2)] + "\n" + cleaned + "\n          " + orig_file_content[m.end(2):]
            p['file'].write_text(new_file_content, encoding='utf-8')
            print(f"  -> Uspesne aktualizovana: {p['file']}")
        else:
            print(f"  -> Nenajdeny vzor pre vkladanie do {p['file']}")
    except Exception as e:
        print(f"  Chyba pri {p['path']}: {e}")

print("\n=== 2. Prepis vsetkych zvysnych relativnych odkazov ===")

all_html = list(PUBLIC_DIR.rglob("index.html"))
root_index = Path("index.html")
if root_index.exists():
    all_html.append(root_index)

total_patched_links = 0
files_modified = 0

for hf in all_html:
    is_root = (hf == root_index)
    root_rel = "./" if is_root else get_root_rel(hf)
    
    content = hf.read_text(encoding='utf-8')
    orig_content = content
    
    # 1. Oprava action="/..." vo formularoch
    def sub_form(m):
        action = m.group(1)
        if action.startswith('/') and not action.startswith('/horny-vadicov'):
            return 'action="./"'
        return m.group(0)
    content = re.sub(r'action=["\'](/[^"\']*)["\']', sub_form, content)
    
    # 2. Oprava src="/..."
    def sub_src(m):
        src = m.group(1)
        if src.startswith(('/horny-vadicov', '//', 'http', 'data:')):
            return m.group(0)
        clean = src.lstrip('/').split('?')[0].split('#')[0]
        local_file = PUBLIC_DIR / clean
        if local_file.exists():
            return f'src="{root_rel}{clean}"'
        else:
            return f'src="{BASE_ORIGIN}{src}"'
    content = re.sub(r'src=["\'](/[^"\']+)["\']', sub_src, content)
    
    # 3. Oprava href="/..."
    def sub_href(m):
        href = m.group(1)
        if href.startswith(('/horny-vadicov', '//', 'http', 'mailto:', 'tel:', '#', 'javascript:')):
            return m.group(0)
            
        clean = href.lstrip('/').split('?')[0].split('#')[0]
        
        # Check if local dir with index.html
        local_dir = PUBLIC_DIR / clean
        if clean != "" and local_dir.is_dir() and (local_dir / 'index.html').exists():
            query_and_hash = href[len('/' + clean):]
            # preserve query/hash
            return f'href="{root_rel}{clean}/{query_and_hash}"'
        elif clean != "" and (PUBLIC_DIR / clean).is_file():
            query_and_hash = href[len('/' + clean):]
            return f'href="{root_rel}{clean}{query_and_hash}"'
        elif clean == "":
            return f'href="{root_rel}"'
        else:
            # External detail page or archive link on original portal
            return f'href="{BASE_ORIGIN}{href}" target="_blank" rel="noopener noreferrer"'
            
    content = re.sub(r'href=["\'](/[^"\']+)["\']', sub_href, content)
    
    if content != orig_content:
        hf.write_text(content, encoding='utf-8')
        files_modified += 1

print(f"Modifikovanych suborov: {files_modified}/{len(all_html)}")

print("\n=== 3. Znovu spustam verifikaciu webu ===")
os.system("python scripts/verify_site.py")
