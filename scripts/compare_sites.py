import os
import json
import re
import urllib.request
import ssl
from collections import defaultdict

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

print("=== 1. ANALÝZA LOKÁLNYCH STRÁNOK (NOVÝ WEB) ===")
local_pages = []
for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            rel_path = os.path.relpath(os.path.join(root, f), 'public').replace('\\', '/')
            # route
            if rel_path == 'index.html':
                route = '/'
            elif rel_path.endswith('/index.html'):
                route = '/' + rel_path[:-10] + '/'
            else:
                route = '/' + rel_path
            local_pages.append((route, os.path.join(root, f)))

print(f"Celkový počet lokálnych HTML stránok v public/: {len(local_pages)}")

print("\n=== 2. ANALÝZA MENU A ODKAZOV Z PÔVODNÉHO WEBU (https://www.hornyvadicov.sk) ===")
try:
    req = urllib.request.Request('https://www.hornyvadicov.sk/', headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        home_html = resp.read().decode('utf-8', errors='ignore')
    
    # Extract all menu / internal links from original homepage
    orig_menu_links = set(re.findall(r'href=["\'](/[^"\'#?]+\.html|/[^"\'#?]+/)["\']', home_html))
    print(f"Počet unikátnych navigačných odkazov z hlavného menu pôvodného webu: {len(orig_menu_links)}")
    
    # Check which menu links from original web exist locally
    local_routes_set = set(r[0] for r in local_pages)
    
    # Normalized matching
    missing_routes = []
    present_routes = []
    for o_link in sorted(orig_menu_links):
        # Ignore asset links
        if any(o_link.startswith(x) for x in ['/assets', '/bundles', '/skins', '/js', '/css', '/data', '/images']):
            continue
        
        # Check direct or trailing slash or index.html
        norm = o_link
        if not norm.endswith('/') and not norm.endswith('.html'):
            norm += '/'
        
        if norm in local_routes_set or o_link in local_routes_set or (norm.rstrip('/') + '/index.html') in local_routes_set:
            present_routes.append(o_link)
        else:
            missing_routes.append(o_link)
            
    print(f"Menu položky prítomné na novom webe: {len(present_routes)}")
    print(f"Menu položky chýbajúce na novom webe: {len(missing_routes)}")
    if missing_routes:
        print("Chýbajúce položky z menu:")
        for m in missing_routes[:20]:
            print(f"  - {m}")
except Exception as e:
    print(f"Chyba pri sťahovaní pôvodného webu: {e}")

print("\n=== 3. KONTROLA DÁT V HLAVNÝCH MODULOCH ===")
# Modules to compare:
# - Zmluvy: count items
# - Úradná tabuľa: count items
# - Uznesenia OZ: count items
# - Zápisnice OZ: count items
# - Aktuality: count items
# - Fotogaléria: count albums
# - VZN: count items

def check_local_items(rel_path, pattern):
    full_p = os.path.join('public', rel_path)
    if not os.path.exists(full_p):
        return 0
    with open(full_p, 'r', encoding='utf-8') as f:
        c = f.read()
    return len(re.findall(pattern, c))

modules = [
    ('Zmluvy (2022-2026)', 'zverejnovanie/zmluvy-faktury-objednavky/index.html', r'<tr id="item_\d+"'),
    ('Zmluvy (Archív do 2022)', 'zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/zmluvy/index.html', r'<tr id="item_\d+"'),
    ('Úradná tabuľa', 'zverejnovanie/uradna-tabula-1/index.html', r'<tr id="item_\d+"|<div class="table-row'),
    ('Uznesenia OZ', 'samosprava/obecne-zastupitelstvo/uznesenia-oz/index.html', r'<tr id="item_\d+"|<div class="table-row'),
    ('Zápisnice OZ', 'samosprava/obecne-zastupitelstvo/zapisnice/index.html', r'<tr id="item_\d+"|<div class="table-row'),
    ('VZN', 'samosprava/vzn/index.html', r'<tr id="item_\d+"|<div class="table-row'),
    ('Aktuality', 'obec-2/aktuality/index.html', r'<div class="item"|<article|<div class="col'),
    ('Fotogaléria', 'obec-2/fotogaleria/index.html', r'class="gallery-item"|class="album"|<div class="col'),
    ('Voľby a referendum', 'volby-a-referendum/index.html', r'<tr id="item_\d+"|<div class="table-row'),
]

for name, path, pat in modules:
    count = check_local_items(path, pat)
    print(f"  {name:25s}: {count} položiek na novom webe")

print("\n=== 4. KONTROLA LOKÁLNYCH DOKUMENTOV A PRÍLOH (public/data/) ===")
doc_types = defaultdict(int)
total_docs_size = 0
for root, dirs, files in os.walk('public/data'):
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        doc_types[ext] += 1
        total_docs_size += os.path.getsize(os.path.join(root, f))

print(f"Celkový počet uložených súborov/dokumentov: {sum(doc_types.values())}")
print(f"Celková veľkosť dokumentov: {total_docs_size / (1024*1024):.2f} MB")
for ext, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {ext or '(bez pripony)'}: {count} súborov")
