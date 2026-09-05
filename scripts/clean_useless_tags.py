import os
import re

count = 0
for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
            new_c = re.sub(r'\s*<script\s+src=[\'"][^\'"]*evt_unknown\.jpg[\'"]>\s*</script>', '', c)
            new_c = re.sub(r'\s*<link\s+rel=[\'"]stylesheet[\'"]\s+href=[\'"][^\'"]*addAnchor\.css[\'"]>', '', new_c)
            if new_c != c:
                with open(p, 'w', encoding='utf-8') as fp:
                    fp.write(new_c)
                count += 1

print(f"Cleaned addAnchor and broken script tags from {count} files.")
