import os
import re

found = []
for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
            m = re.findall(r'href=["\'](https?://(?:www\.)?hornyvadicov\.sk[^"\']*)["\']', c)
            if m:
                found.append((p, m))

print(f"Files with hornyvadicov domain in href: {len(found)}")
for p, m in found[:10]:
    print(p, "->", len(m), "links")
    for l in m[:3]:
        print("   ", l)
