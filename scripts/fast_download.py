import os
import sys
import json
import html
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import requests

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://www.hornyvadicov.sk'
DATA_FILE = 'scripts/scraped_data.json'

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

raw_images = data.get('images', [])
raw_documents = data.get('documents', [])

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# 1. Pripravíme zoznamy úloh
tasks = []

# Mapy pre prepis odkazov v HTML
url_rewrite_map = {}

for img in raw_images:
    clean_img = html.unescape(img)
    parsed = urllib.parse.urlparse(clean_img)
    if parsed.path.startswith('/data/'):
        local_rel = parsed.path.lstrip('/')
    else:
        # napr. evt_image.php?img=2752 -> data/cache_images/img_2752.jpg
        query = urllib.parse.parse_qs(parsed.query)
        img_id = query.get('img', ['unknown'])[0]
        local_rel = f"data/cache_images/evt_{img_id}.jpg"
        
    local_path = os.path.join('public', local_rel)
    url_rewrite_map[img] = '/' + local_rel.replace('\\', '/')
    url_rewrite_map[clean_img] = '/' + local_rel.replace('\\', '/')
    tasks.append((urllib.parse.urljoin(BASE_URL, clean_img), local_path))

for doc in raw_documents:
    clean_doc = html.unescape(doc)
    parsed = urllib.parse.urlparse(clean_doc)
    query = urllib.parse.parse_qs(parsed.query)
    if 'file' in query:
        file_param = query['file'][0].lstrip('/')
        local_rel = file_param
    else:
        local_rel = parsed.path.lstrip('/')
        
    local_path = os.path.join('public', local_rel)
    url_rewrite_map[doc] = '/' + local_rel.replace('\\', '/')
    url_rewrite_map[clean_doc] = '/' + local_rel.replace('\\', '/')
    tasks.append((urllib.parse.urljoin(BASE_URL, clean_doc), local_path))

print(f"Celkovo úloh na stiahnutie: {len(tasks)}")

def download_file(item):
    url, dest = item
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200 and len(r.content) > 0:
            with open(dest, 'wb') as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

# Paralelné sťahovanie s 12 vláknami
success_count = 0
with ThreadPoolExecutor(max_workers=12) as executor:
    results = executor.map(download_file, tasks)
    for res in results:
        if res:
            success_count += 1

print(f"Úspešne stiahnutých lokálnych súborov: {success_count}/{len(tasks)}")

with open('scripts/url_rewrite_map.json', 'w', encoding='utf-8') as f:
    json.dump(url_rewrite_map, f, ensure_ascii=False, indent=2)

print("Prekladová mapa súborov uložená v scripts/url_rewrite_map.json")
