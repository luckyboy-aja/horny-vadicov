"""
Fix remaining broken links:
1. Download /data/uredni_deska/ files
2. Fix /images/crest.png -> ./images/crest.png in root index.html
3. Fix /data/editor/71sk_1_big.gif path
"""
import re, sys, os, requests
from pathlib import Path
from urllib.parse import unquote

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://www.hornyvadicov.sk"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 1. Download uredni_deska files
uredni_files = [
    "/data/uredni_deska/obsah1237_1.pdf",
    "/data/uredni_deska/obsah1235_1.pdf",
    "/data/uredni_deska/obsah1234_1.pdf",
    "/data/uredni_deska/obsah1236_1.pdf",
]

Path("public/data/uredni_deska").mkdir(parents=True, exist_ok=True)

for f_path in uredni_files:
    local = Path("public") / f_path.lstrip('/')
    if not local.exists():
        url = f"{BASE_URL}{f_path}"
        print(f"Downloading: {url}")
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                with open(local, 'wb') as fp:
                    fp.write(r.content)
                print(f"  -> Saved {local.name} ({len(r.content)} bytes)")
            else:
                print(f"  -> HTTP {r.status_code}")
        except Exception as e:
            print(f"  -> ERROR: {e}")
    else:
        print(f"Already exists: {local}")

# 2. Fix /images/crest.png in root index.html
print("\nFixing root index.html...")
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for /images/crest.png
count = content.count('"/images/crest.png"')
if count:
    content = content.replace('"/images/crest.png"', '"./images/crest.png"')
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  -> Fixed {count} /images/crest.png references")
else:
    print("  -> No /images/crest.png found in root index.html")

# 3. Fix /data/editor/71sk_1_big.gif in symboly-obce page
print("\nFixing symboly-obce page...")
sym_file = 'public/obec-2/symboly-obce/index.html'
with open(sym_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Check what needs fixing
gifs = re.findall(r'src=["\'](/data/editor/[^"\']*gif[^"\']*)["\']', content)
print(f"  Found {len(gifs)} gif src links")
for g in gifs:
    print(f"  {g}")

# Fix: /data/editor/71sk_1_big.gif?gcm_date=... -> ../../data/editor/71sk_1_big.gif
def fix_gif(m):
    src = m.group(1)
    # Remove query string
    clean = src.split('?')[0]
    # Convert to relative path (depth=2 for obec-2/symboly-obce)
    return f'src="../../{clean.lstrip("/")}"'

new_content = re.sub(r'src=["\'](/data/editor/[^"\']*gif[^"\']*)["\']', fix_gif, content)
if new_content != content:
    with open(sym_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("  -> Fixed symboly-obce gif links")

# 4. Now regenerate the 4 new pages using the fetch_missing_pages script logic
# but with the new uredni_deska files available
print("\nRegenerating 4 detail pages with proper file paths...")

import json
sys.path.insert(0, 'scripts')
from nav_builder import render_navigation_markup

MODULE_MAP = {}
if Path('scripts/module_download_map.json').exists():
    with open('scripts/module_download_map.json') as f:
        MODULE_MAP = json.load(f)

PAGES_TO_FIX = [
    {
        'html_file': 'public/zverejnovanie/uradna-tabula-1/oznamenie-o-doruceni-pisomnosti-pre-stefana-kacerika-bytom-horny-vadicov-1431/index.html',
        'e_download_src': '/data/uredni_deska/obsah1237_1.pdf',
        'depth': 3
    },
    {
        'html_file': 'public/zverejnovanie/uradna-tabula-1/uznesenia-z-neplanovaneho-zasadnutia-obecneho-zastupitelstva-13082026-1429/index.html',
        'e_download_src': '/data/uredni_deska/obsah1235_1.pdf',
        'depth': 3
    },
    {
        'html_file': 'public/zverejnovanie/uradna-tabula-1/zapisnica-z-neplanovaneho-rokovania-obecneho-zastupitelstva-obce-horny-vadicov-13082026-1428/index.html',
        'e_download_src': '/data/uredni_deska/obsah1234_1.pdf',
        'depth': 3
    },
    {
        'html_file': 'public/zverejnovanie/uradna-tabula-1/zverejnenie-zameru-prevodu-vlastnictva-majetku-obce-horny-vadicov-1430/index.html',
        'e_download_src': '/data/uredni_deska/obsah1236_1.pdf',
        'depth': 3
    },
]

for p in PAGES_TO_FIX:
    root_rel = '../' * p['depth']
    with open(p['html_file'], 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix e_download links
    def fix_edl(m):
        href = m.group(1)
        file_match = re.search(r'file=([^&"\']+)', href.replace('&amp;', '&'))
        if file_match:
            file_path = unquote(file_match.group(1))
            clean_path = file_path.lstrip('/')
            local_file = Path("public") / clean_path
            if local_file.exists():
                return f'href="{root_rel}{clean_path}"'
        return f'href="https://www.hornyvadicov.sk{href}"'
    
    new_content = re.sub(r'href=["\'](/e_download\.php\?[^"\']*)["\']', fix_edl, content)
    if new_content != content:
        with open(p['html_file'], 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  -> Fixed {p['html_file']}")

print("\nDone!")
