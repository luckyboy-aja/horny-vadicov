import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

url = 'https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/zmluvy/zmluva-o-grantovom-ucte-1286.html?kshow=4'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

main = re.search(r'<div class="gcm-main">(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
if main:
    text = re.sub(r'<[^>]+>', ' ', main.group(1))
    print(' '.join(text.split())[:600])
