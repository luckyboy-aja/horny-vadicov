import os
import re
import urllib.parse
import requests

files_to_check = [
    'data/editor/127sk_3.pdf',
    'data/editor/127sk_4.pdf',
    'data/multipage/editor/editor-29-89-sk_1.zip',
    'data/multipage/editor/editor-20-73-sk_1.mp4',
]

for f in files_to_check:
    clean_f = f.lstrip('/')
    local_path = os.path.join('public', clean_f)
    print(f"Checking {local_path}...")
    if os.path.exists(local_path):
        print(f"  EXISTS ({os.path.getsize(local_path)} bytes)")
    else:
        # try downloading from https://www.hornyvadicov.sk/ + clean_f
        url = f"https://www.hornyvadicov.sk/{clean_f}"
        try:
            r = requests.get(url, timeout=30, stream=True)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as fp:
                    for chunk in r.iter_content(8192):
                        fp.write(chunk)
                print(f"  DOWNLOADED {url} -> {local_path} ({os.path.getsize(local_path)} bytes)")
            else:
                print(f"  Status {r.status_code} for {url}")
        except Exception as e:
            print(f"  Error downloading {url}: {e}")
