import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

urls = [
    'https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/zmluvy/zmluva-o-grantovom-ucte-1286.html?kshow=4',
    'https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/faktury/faktury-od-0101-2015-do-3112-2015-139.html?kshow=3',
    'https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/objednavky/objednavky-od-01012015-do-31122015-138.html?kshow=2'
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html)
        h1_text = h1.group(1).strip() if h1 else 'No H1'
        files = re.findall(r'href=["\'](/data/[^"\']+\.(?:pdf|docx?|jpg|png)|/modules/file_storage/[^"\']+)["\']', html)
        print(f"URL: {u.split('/')[-1]}")
        print(f"  Title: {h1_text}")
        print(f"  Files: {files}")
    except Exception as e:
        print(f"Error {u}: {e}")
