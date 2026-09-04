import os
import re

for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
            imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', c)
            ext_imgs = [i for i in imgs if i.startswith('http')]
            if ext_imgs:
                print(f"{p}: {len(ext_imgs)} external images")
                for ei in ext_imgs[:3]:
                    print("  ", ei)
