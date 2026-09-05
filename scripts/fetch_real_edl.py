import requests

urls = [
    ('https://www.hornyvadicov.sk/e_download.php?file=data/editor/127sk_3.pdf&original=03_obec_HornyVadicov_KEP_POZ.pdf', 'public/data/editor/127sk_3.pdf'),
    ('https://www.hornyvadicov.sk/e_download.php?file=data/editor/127sk_4.pdf&original=04_obec_HornyVadicov_KEP_NEG.pdf', 'public/data/editor/127sk_4.pdf'),
    ('https://www.hornyvadicov.sk/e_download.php?file=/data/multipage/editor/editor-29-89-sk_1.zip&original=Priloha.zip', 'public/data/multipage/editor/editor-29-89-sk_1.zip'),
    ('https://www.hornyvadicov.sk/e_download.php?file=/data/multipage/editor/editor-20-73-sk_1.mp4&original=Video.mp4', 'public/data/multipage/editor/editor-20-73-sk_1.mp4'),
    ('https://www.hornyvadicov.sk/e_download.php?file=/data/editor/mini12sk_1.pdf&original=Logo.pdf', 'public/data/editor/mini12sk_1.pdf'),
]

headers = {'User-Agent': 'Mozilla/5.0'}

for u, dest in urls:
    try:
        r = requests.get(u, headers=headers, timeout=20)
        print(u, '->', r.status_code, len(r.content))
        if r.status_code == 200:
            with open(dest, 'wb') as f:
                f.write(r.content)
            print(f"  SAVED TO {dest}")
    except Exception as e:
        print(f"  Error {u}: {e}")
