import os
import re
import urllib.parse
from pathlib import Path
import requests

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
            # Get relative url from public
            rel_to_public = os.path.relpath(target, Path("public").resolve()).replace('\\', '/')
            missing_html.append((str(html_path), ref, rel_to_public))

unique_missing = {}
for src, ref, rel in missing_html:
    unique_missing[rel] = (src, ref)

print(f"Unique missing .html targets: {len(unique_missing)}")
for rel, (src, ref) in unique_missing.items():
    print(f"  {rel}")
