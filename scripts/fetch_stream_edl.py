import requests

urls = [
    ('https://www.hornyvadicov.sk/e_download.php?file=/data/multipage/editor/editor-20-73-sk_1.mp4&original=Video.mp4', 'public/data/multipage/editor/editor-20-73-sk_1.mp4'),
    ('https://www.hornyvadicov.sk/e_download.php?file=/data/editor/mini12sk_1.pdf&original=Logo.pdf', 'public/data/editor/mini12sk_1.pdf'),
]

headers = {'User-Agent': 'Mozilla/5.0'}

for u, dest in urls:
    try:
        r = requests.get(u, headers=headers, timeout=60, stream=True)
        print(u, '->', r.status_code)
        if r.status_code == 200:
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            print(f"  SAVED TO {dest}")
    except Exception as e:
        print(f"  Error {u}: {e}")
