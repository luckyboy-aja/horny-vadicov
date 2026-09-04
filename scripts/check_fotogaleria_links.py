import re

with open('public/obec-2/fotogaleria/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

links = re.findall(r'href=["\']([^"\']*fotogaleria[^"\']*)["\']', c)
print(f"Total fotogaleria links in page: {len(links)}")
for l in links[:15]:
    print(" ", l)
