import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

urls = [
    ('Fotogaleria', 'https://www.hornyvadicov.sk/obec-2/fotogaleria/', 'public/obec-2/fotogaleria/index.html'),
    ('Uznesenia OZ', 'https://www.hornyvadicov.sk/samosprava/obecne-zastupitelstvo/uznesenia-oz/', 'public/samosprava/obecne-zastupitelstvo/uznesenia-oz/index.html'),
    ('Zapisnice OZ', 'https://www.hornyvadicov.sk/samosprava/obecne-zastupitelstvo/zapisnice/', 'public/samosprava/obecne-zastupitelstvo/zapisnice/index.html'),
    ('Volby a ref.', 'https://www.hornyvadicov.sk/volby-a-referendum/', 'public/volby-a-referendum/index.html'),
]

for name, u, lp in urls:
    req = urllib.request.Request(u, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as resp:
        live = resp.read().decode('utf-8', errors='ignore')
    with open(lp, 'r', encoding='utf-8') as f:
        loc = f.read()
    
    print(f"\n--- {name} ---")
    # find links to files or download
    live_downloads = re.findall(r'href=["\'](/modules/file_storage/download\.php\?[^"\']+|/data/[^"\']+)["\']', live)
    loc_downloads = re.findall(r'href=["\']([^"\']+\.(?:pdf|docx?|jpg|png)|[^"\']*download\.php[^"\']*)["\']', loc)
    print(f"  Live file/attachment links: {len(live_downloads)}")
    print(f"  Local file/attachment links: {len(loc_downloads)}")
    
    # find headings in content
    live_headings = re.findall(r'<h[234][^>]*>(.*?)</h[234]>', live)
    loc_headings = re.findall(r'<h[234][^>]*>(.*?)</h[234]>', loc)
    print(f"  Live content headings: {len(live_headings)}, Local content headings: {len(loc_headings)}")
