import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

url = 'https://www.hornyvadicov.sk/obec-2/fotogaleria/vadicovsky-kotlik-2282026-609sk.html'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
print('Total img tags in album page:', len(imgs))
for i in imgs[:10]:
    print(' ', i)

# check highslide or gallery links
a_imgs = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*class="[^"]*highslide[^"]*"', html)
print('Highslide links:', len(a_imgs))
for a in a_imgs[:5]:
    print(' ', a)
