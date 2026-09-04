import os, re, urllib.request, ssl, concurrent.futures

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

with open('public/obec-2/fotogaleria/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

album_links = re.findall(r'<a\s+href=["\'](https://www\.hornyvadicov\.sk/obec-2/fotogaleria/([^"\'?]+)(?:\?[^"\']*)?)["\']', c)
print(f"Nájdených {len(album_links)} albumov.")

def check_album(item):
    url, filename = item
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        imgs = re.findall(r'href=["\'](/evt_image\.php\?img=\d+)["\']', html)
        return url, filename, len(imgs), list(set(imgs))
    except Exception as e:
        return url, filename, 0, []

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(check_album, album_links))

total_photos = sum(r[2] for r in results)
unique_photos = set([img for r in results for img in r[3]])
print(f"Celkový počet fotiek vo všetkých 48 albumoch: {total_photos}")
print(f"Unikátnych fotiek: {len(unique_photos)}")
