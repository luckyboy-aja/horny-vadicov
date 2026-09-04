import urllib.request
import ssl
import re
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

checks = [
    {
        'name': 'Aktuality',
        'url': 'https://www.hornyvadicov.sk/obec-2/aktuality/',
        'local': 'public/obec-2/aktuality/index.html',
        'pattern': r'id="event-\d+"'
    },
    {
        'name': 'Fotogaléria',
        'url': 'https://www.hornyvadicov.sk/obec-2/fotogaleria/',
        'local': 'public/obec-2/fotogaleria/index.html',
        'pattern': r'id="gallery-\d+"|class="[^"]*gallery-item[^"]*"|id="event-\d+"'
    },
    {
        'name': 'Uznesenia OZ',
        'url': 'https://www.hornyvadicov.sk/samosprava/obecne-zastupitelstvo/uznesenia-oz/',
        'local': 'public/samosprava/obecne-zastupitelstvo/uznesenia-oz/index.html',
        'pattern': r'id="resolution-\d+"|class="[^"]*resolution-item[^"]*"|class="item"'
    },
    {
        'name': 'Zápisnice OZ',
        'url': 'https://www.hornyvadicov.sk/samosprava/obecne-zastupitelstvo/zapisnice/',
        'local': 'public/samosprava/obecne-zastupitelstvo/zapisnice/index.html',
        'pattern': r'class="item"'
    },
    {
        'name': 'Úradná tabuľa',
        'url': 'https://www.hornyvadicov.sk/zverejnovanie/uradna-tabula-1/',
        'local': 'public/zverejnovanie/uradna-tabula-1/index.html',
        'pattern': r'<div class="item">'
    },
    {
        'name': 'Zmluvy',
        'url': 'https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/zmluvy.html',
        'local': 'public/zverejnovanie/zmluvy-faktury-objednavky/index.html',
        'pattern': r'<tr id="item_\d+"'
    },
    {
        'name': 'VZN',
        'url': 'https://www.hornyvadicov.sk/samosprava/vzn/',
        'local': 'public/samosprava/vzn/index.html',
        'pattern': r'<div class="item">'
    },
    {
        'name': 'Voľby a referendum',
        'url': 'https://www.hornyvadicov.sk/volby-a-referendum/',
        'local': 'public/volby-a-referendum/index.html',
        'pattern': r'<div class="item">'
    },
]

print("=== DETAILNÉ POROVNANIE POČTOV DÁT ===")
for c in checks:
    # live with page=all
    url_all = c['url'] + ('?page=all' if not 'zmluvy.html' in c['url'] else '')
    req = urllib.request.Request(url_all, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            live_html = resp.read().decode('utf-8', errors='ignore')
        live_matches = re.findall(c['pattern'], live_html)
        live_count = len(live_matches)
    except Exception as e:
        live_count = f"Chyba: {e}"
    
    with open(c['local'], 'r', encoding='utf-8') as f:
        local_html = f.read()
    local_matches = re.findall(c['pattern'], local_html)
    local_count = len(local_matches)
    
    status = "[ZHODNE]" if live_count == local_count else "[ROZDIEL]"
    print(f"{c['name']:22s} | Pôvodný (všetko): {str(live_count):4s} | Nový web: {str(local_count):4s} | {status}")
