import re
import urllib.request
import ssl
import json
import concurrent.futures

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

with open('public/zverejnovanie/uradna-tabula-1/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

links = re.findall(r'<a\s+class="item-href"\s+href=["\'](https://www\.hornyvadicov\.sk/zverejnovanie/uradna-tabula-1/[^"\']+)["\'][^>]*>(.*?)</a>', html)
print(f'Total notice links to check: {len(links)}')

def fetch_notice(item):
    url, title = item
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
        files = re.findall(r'href=["\'](/data/uredni_deska/[^"\']+)["\']', content)
        if not files:
            files = re.findall(r'href=["\'](/data/[^"\']+\.(?:pdf|docx?|jpg|png))["\']', content)
        return {
            'url': url,
            'title': title.strip(),
            'files': list(dict.fromkeys(files))
        }
    except Exception as e:
        return {'url': url, 'title': title.strip(), 'error': str(e), 'files': []}

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch_notice, links))

has_files = [r for r in results if r['files']]
print(f'Notices with attached files: {len(has_files)} / {len(results)}')
all_files = list(set([f for r in results for f in r['files']]))
print(f'Total unique files in notices: {len(all_files)}')
for r in results[:5]:
    print(r['title'][:40], '->', r['files'])
