import re
import urllib.request
import ssl
import json
import os
import concurrent.futures

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

with open('public/zverejnovanie/uradna-tabula-1/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find all notice links
links = re.findall(r'<a\s+class="item-href"\s+href=["\'](https://www\.hornyvadicov\.sk/zverejnovanie/uradna-tabula-1/[^"\']+)["\'][^>]*>(.*?)</a>', html)
print(f'Total notice links on Uradna tabula: {len(links)}')

# Check how many of these match existing local subpages
local_dirs = os.listdir('public/zverejnovanie/uradna-tabula-1')
matched_local = 0
for u, t in links:
    slug = u.split('/')[-1].split('?')[0].replace('.html', '')
    if slug in local_dirs:
        matched_local += 1
        print(f'Local match found for: {slug}')

print(f'Matched existing local folders: {matched_local} / {len(links)}')
