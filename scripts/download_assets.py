import os
import sys
import json
import urllib.parse
import requests

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://www.hornyvadicov.sk'
DATA_FILE = 'scripts/scraped_data.json'

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

images = data.get('images', [])
documents = data.get('documents', [])

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Stahujem {len(images)} obrazkov do public/ ...")
downloaded_imgs = 0
for idx, img_path in enumerate(images, 1):
    clean_path = img_path.split('?')[0].lstrip('/')
    target_path = os.path.join('public', clean_path)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    if os.path.exists(target_path):
        downloaded_imgs += 1
        continue

    url = urllib.parse.urljoin(BASE_URL, img_path)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            with open(target_path, 'wb') as f:
                f.write(r.content)
            downloaded_imgs += 1
            if idx % 20 == 0:
                print(f"  [{idx}/{len(images)}] Stiahnute: {clean_path}")
    except Exception as e:
        print(f"  Chyba pri stahovani {img_path}: {e}")

print(f"Stiahnute obrazky: {downloaded_imgs}/{len(images)}")

print(f"\nStahujem {len(documents)} dokumentov do public/ ...")
downloaded_docs = 0
doc_map = {} # mapuje original URL/query na lokalnu cestu

for idx, doc_path in enumerate(documents, 1):
    url = urllib.parse.urljoin(BASE_URL, doc_path)
    # Zisti lokalnu cielovu cestu
    # napr. /e_download.php?file=/data/editor/39sk_1.pdf&original=Zmluva.pdf
    parsed = urllib.parse.urlparse(doc_path)
    query = urllib.parse.parse_qs(parsed.query)
    
    if 'file' in query:
        clean_name = query['file'][0].lstrip('/')
    else:
        clean_name = parsed.path.lstrip('/')
        
    target_path = os.path.join('public', clean_name)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    doc_map[doc_path] = '/' + clean_name.replace('\\', '/')

    if os.path.exists(target_path):
        downloaded_docs += 1
        continue

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 0:
            with open(target_path, 'wb') as f:
                f.write(r.content)
            downloaded_docs += 1
            if idx % 20 == 0:
                print(f"  [{idx}/{len(documents)}] Stiahnuty dokument: {clean_name}")
    except Exception as e:
        print(f"  Chyba pri stahovani {doc_path}: {e}")

print(f"Stiahnute dokumenty: {downloaded_docs}/{len(documents)}")

with open('scripts/doc_map.json', 'w', encoding='utf-8') as f:
    json.dump(doc_map, f, ensure_ascii=False, indent=2)

print("Mapa dokumentov ulozena v scripts/doc_map.json.")
