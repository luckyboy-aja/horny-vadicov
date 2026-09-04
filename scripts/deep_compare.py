import urllib.request
import ssl
import re
import os
# Standard library only

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Fetch original homepage and sitemap/menu
print("Fetching original homepage...")
req = urllib.request.Request('https://www.hornyvadicov.sk/', headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    home_html = resp.read().decode('utf-8', errors='ignore')

# Extract all links from the navigation/menus
raw_links = re.findall(r'href=["\'](/[^"\'#?]+)', home_html)
menu_links = set()
for l in raw_links:
    if any(l.startswith(x) for x in ['/assets', '/bundles', '/skins', '/js', '/css', '/data', '/images', '/modules']):
        continue
    # remove trailing file if html, or keep dir
    menu_links.add(l)

print(f"Found {len(menu_links)} unique structural menu paths on original website.")

# Check each against local public/ directory
matched = []
missing = []

for l in sorted(menu_links):
    # check possible local paths:
    # 1. public + l + 'index.html'
    # 2. public + l + '.html'
    # 3. public + l (if ends in .html)
    p1 = os.path.normpath(os.path.join('public', l.lstrip('/'), 'index.html'))
    p2 = os.path.normpath(os.path.join('public', l.lstrip('/')))
    p3 = os.path.normpath(os.path.join('public', l.lstrip('/') + '.html'))
    
    if os.path.exists(p1) or (os.path.exists(p2) and os.path.isfile(p2)) or (os.path.exists(p3) and os.path.isfile(p3)):
        matched.append(l)
    else:
        missing.append(l)

print(f"\n--- VÝSLEDOK POROVNANIA STRÁNOK ---")
print(f"Zhoda: {len(matched)} / {len(menu_links)} stránok menu existuje na novom webe.")
if missing:
    print(f"Chýbajúce stránky ({len(missing)}):")
    for m in missing:
        print(f"  [MISSING] {m}")
else:
    print("  [OK] Vsetky stranky z hlavneho menu povodneho webu existuju na novom webe!")

# 2. Compare data quantities in key modules
print("\n--- POROVNANIE POČTU ZÁZNAMOV V HLAVNÝCH MODULOCH ---")
def count_live_and_local(name, orig_url, local_rel_path, regex_live, regex_local):
    # Fetch live
    live_count = 0
    try:
        req = urllib.request.Request(orig_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            c_live = resp.read().decode('utf-8', errors='ignore')
        live_count = len(re.findall(regex_live, c_live))
    except Exception as e:
        live_count = f"Chyba ({e})"
    
    # Check local
    local_count = 0
    loc_path = os.path.join('public', local_rel_path)
    if os.path.exists(loc_path):
        with open(loc_path, 'r', encoding='utf-8') as f:
            c_local = f.read()
        local_count = len(re.findall(regex_local, c_local))
    else:
        local_count = "Súbor neexistuje"
    
    status = "[ZHODNE]" if live_count == local_count else "[ROZDIEL]"
    print(f"{name:30s} | Pôvodný: {str(live_count):5s} | Nový web: {str(local_count):5s} | {status}")

modules_to_test = [
    (
        "Zmluvy (hlavný zoznam)",
        "https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/zmluvy.html?page=all",
        "zverejnovanie/zmluvy-faktury-objednavky/index.html",
        r'<tr id="item_\d+"',
        r'<tr id="item_\d+"'
    ),
    (
        "Uznesenia OZ",
        "https://www.hornyvadicov.sk/samosprava/obecne-zastupitelstvo/uznesenia-oz/?page=all",
        "samosprava/obecne-zastupitelstvo/uznesenia-oz/index.html",
        r'<div class="item">',
        r'<div class="item">'
    ),
    (
        "Zápisnice OZ",
        "https://www.hornyvadicov.sk/samosprava/obecne-zastupitelstvo/zapisnice/?page=all",
        "samosprava/obecne-zastupitelstvo/zapisnice/index.html",
        r'<div class="item">',
        r'<div class="item">'
    ),
    (
        "Aktuality",
        "https://www.hornyvadicov.sk/obec-2/aktuality/?page=all",
        "obec-2/aktuality/index.html",
        r'<div class="item">',
        r'<div class="item">'
    ),
    (
        "Fotogaléria (albumy)",
        "https://www.hornyvadicov.sk/obec-2/fotogaleria/?page=all",
        "obec-2/fotogaleria/index.html",
        r'<div class="item">',
        r'<div class="item">'
    ),
    (
        "Voľby a referendum",
        "https://www.hornyvadicov.sk/volby-a-referendum/?page=all",
        "volby-a-referendum/index.html",
        r'<div class="item">',
        r'<div class="item">'
    ),
    (
        "VZN (Všeobecne záv. nar.)",
        "https://www.hornyvadicov.sk/samosprava/vzn/?page=all",
        "samosprava/vzn/index.html",
        r'<div class="item">',
        r'<div class="item">'
    ),
    (
        "Úradná tabuľa (aktuálne)",
        "https://www.hornyvadicov.sk/zverejnovanie/uradna-tabula-1/",
        "zverejnovanie/uradna-tabula-1/index.html",
        r'<div class="item">',
        r'<div class="item">'
    )
]

for item in modules_to_test:
    count_live_and_local(*item)
