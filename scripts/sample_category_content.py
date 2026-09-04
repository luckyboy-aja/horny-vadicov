import urllib.request
import ssl
import re
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

with open('scripts/all_external_targets.json', 'r', encoding='utf-8') as f:
    cats = json.load(f)

for cat, urls in cats.items():
    if not urls:
        continue
    sample_url = urls[0]
    try:
        req = urllib.request.Request(sample_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        # Check files/attachments in page
        files = re.findall(r'href=["\'](/data/[^"\']+\.(?:pdf|docx?|jpg|png)|/modules/file_storage/[^"\']+)["\']', html)
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html)
        h1_text = h1.group(1).strip() if h1 else 'No H1'
        print(f"[{cat}] {sample_url}")
        print(f"  H1: {h1_text}")
        print(f"  Attachments/files ({len(files)}): {files[:3]}")
    except Exception as e:
        print(f"[{cat}] {sample_url} -> Error: {e}")
