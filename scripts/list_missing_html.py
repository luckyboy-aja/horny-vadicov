import os
import re
import urllib.parse
from pathlib import Path

public_dir = Path("public")
html_files = list(public_dir.rglob("index.html"))

missing_html = []

for html_path in html_files:
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    refs = re.findall(r'href=["\']([^"\']+\.html)["\']', content)
    for ref in refs:
        if ref.startswith(("#", "mailto:", "tel:", "javascript:", "http://", "https://")):
            continue
        clean_ref = ref.split("?")[0].split("#")[0]
        clean_ref = urllib.parse.unquote(clean_ref)
        target = (html_path.parent / clean_ref).resolve()
        if not target.exists():
            missing_html.append((str(html_path), ref, str(target)))

print(f"Total missing .html links: {len(missing_html)}")
for src, ref, tgt in missing_html:
    print(f"{src} -> {ref}")
