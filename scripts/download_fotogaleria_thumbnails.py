import os
import re
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

p = 'public/obec-2/fotogaleria/index.html'
with open(p, 'r', encoding='utf-8') as fp:
    c = fp.read()

imgs = re.findall(r'src=["\'](https://www\.hornyvadicov\.sk/evt_image\.php\?img=(\d+)[^"\']*)["\']', c)
print(f"Nájdených {len(imgs)} externých miniatúr fotogalérie.")

img_dir = os.path.join('public', 'data', 'cache_images')
os.makedirs(img_dir, exist_ok=True)

for full_src, img_id in imgs:
    fname = f"gal_thumb_{img_id}.jpg"
    dest_path = os.path.join(img_dir, fname)
    if not os.path.exists(dest_path):
        clean_url = full_src.replace('&amp;', '&')
        try:
            req = urllib.request.Request(clean_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                with open(dest_path, 'wb') as out_f:
                    out_f.write(resp.read())
            print(f"  [OK] Stiahnuté {fname}")
        except Exception as e:
            print(f"  [FAIL] {fname}: {e}")
    
    # replace in HTML
    rel_path = f"../../data/cache_images/{fname}"
    c = c.replace(full_src, rel_path)

with open(p, 'w', encoding='utf-8') as fp:
    fp.write(c)

print("Všetky miniatúry fotogalérie stiahnuté a prepojené.")
