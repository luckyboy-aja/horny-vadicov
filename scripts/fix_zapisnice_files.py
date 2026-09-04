import os
import re
import urllib.parse
import requests

ZAPISNICE_PATH = 'public/samosprava/obecne-zastupitelstvo/zapisnice/index.html'
STORAGE_DIR = 'public/data/file_storage'
os.makedirs(STORAGE_DIR, exist_ok=True)

with open(ZAPISNICE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

matches = re.findall(r'href=[\"\'](https://www\.hornyvadicov\.sk/modules/file_storage/download\.php\?file=([^\"\'\>]+))[\"\']', content)
print(f"Found {len(matches)} download links in zápisnice.")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for full_url, param in matches:
    dec = urllib.parse.unquote(param)
    print(f"Processing: {param} -> {dec}")
    
    # Try downloading or finding
    try:
        r = requests.get(full_url, headers=headers, timeout=30, stream=True)
        if r.status_code == 200:
            cd = r.headers.get('content-disposition', '')
            filename = None
            if 'filename=' in cd:
                filename = cd.split('filename=')[-1].strip('\"\' ')
            if not filename:
                # fallback
                filename = f"file_{param.replace('%7C', '_')}.pdf"
            
            # sanitize filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            local_path = os.path.join(STORAGE_DIR, filename)
            if not os.path.exists(local_path):
                with open(local_path, 'wb') as fp:
                    for chunk in r.iter_content(chunk_size=8192):
                        fp.write(chunk)
                print(f"  [DOWNLOADED] {filename} ({os.path.getsize(local_path)} bytes)")
            else:
                print(f"  [EXISTS] {filename}")
            
            # Rewrite in content: relative path from public/samosprava/obecne-zastupitelstvo/zapisnice/
            rel_link = f"../../../data/file_storage/{urllib.parse.quote(filename)}"
            content = content.replace(full_url, rel_link)
        else:
            print(f"  [ERROR] status {r.status_code} for {full_url}")
    except Exception as e:
        print(f"  [EXCEPTION] {e}")

with open(ZAPISNICE_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("Finished processing zápisnice.")
