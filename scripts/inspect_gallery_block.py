import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

url = 'https://www.hornyvadicov.sk/obec-2/fotogaleria/vadicovsky-kotlik-2282026-609sk.html'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# find gallery photos block
gal = re.search(r'<div class="gallery[^"]*">(.*?)</div>\s*</div>', html, re.DOTALL)
if gal:
    print('Found gallery block:', gal.group(0)[:600].replace('\n', ' '))
else:
    # find where evt_image is used
    m = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>\s*<img[^>]+src=["\']([^"\']+)["\']', html)
    print('Found a -> img pairs:', len(m))
    for a, img in m[:5]:
        print('  A:', a, '| IMG:', img)
