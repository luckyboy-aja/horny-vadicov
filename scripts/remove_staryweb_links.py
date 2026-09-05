import os
import re

count = 0
for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
            if 'staryweb.hornyvadicov.sk' in c:
                # Remove the link paragraph or anchor
                c = re.sub(r'\s*<p[^>]*>\s*<a\s+href=[\'"]https://staryweb\.hornyvadicov\.sk/[^>]*>.*?</a>\s*</p>', '', c, flags=re.IGNORECASE)
                c = re.sub(r'<a\s+href=[\'"]https://staryweb\.hornyvadicov\.sk/[^>]*>.*?</a>', '', c, flags=re.IGNORECASE)
                with open(p, 'w', encoding='utf-8') as fp:
                    fp.write(c)
                count += 1

print(f"Removed staryweb.hornyvadicov.sk from {count} HTML pages.")
