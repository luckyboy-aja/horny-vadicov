import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://www.hornyvadicov.sk/obec-2/aktuality/hasicsky-vikend-8-982026-587sk.html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Extract main article
article = re.search(r'<div class="gcm-main">(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
if article:
    print('Found gcm-main content length:', len(article.group(1)))
    # find images
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', article.group(1))
    print('Images:', imgs)
    # find files
    files = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', article.group(1))
    print('Links:', files[:5])
