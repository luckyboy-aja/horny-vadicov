import os
import re

files_to_clean = [
    'public/zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/zmluvy/index.html',
    'public/zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/faktury/index.html',
    'public/zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/objednavky/index.html'
]

total_cleaned = 0
for p in files_to_clean:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as fp:
            c = fp.read()
        
        # Replace <a class="item-href" href="https://www.hornyvadicov.sk/..." target="_blank" rel="noopener noreferrer">(.*?)</a>
        new_c, count = re.subn(
            r'<a\s+class="item-href"\s+href=["\']https://www\.hornyvadicov\.sk/[^"\']+["\'][^>]*>(.*?)</a>',
            r'<span class="item-title font-weight-bold" style="color: #1a202c;">\1</span>',
            c
        )
        with open(p, 'w', encoding='utf-8') as fp:
            fp.write(new_c)
        print(f"{p}: cleaned {count} external links.")
        total_cleaned += count

print(f"Celkovo vyčistených {total_cleaned} odkazov v archíve ZFO.")
