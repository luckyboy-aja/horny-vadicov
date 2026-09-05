import os
import re
import urllib.parse
from pathlib import Path
from collections import Counter

public_dir = Path("public")
html_files = list(public_dir.rglob("index.html"))
if Path("index.html").exists():
    html_files.append(Path("index.html"))

missing_by_type = Counter()
missing_details = []

for html_path in html_files:
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    refs = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', content)
    for ref in refs:
        if ref.startswith(("#", "mailto:", "tel:", "javascript:", "http://", "https://")):
            continue
        clean_ref = ref.split("?")[0].split("#")[0]
        clean_ref = urllib.parse.unquote(clean_ref)
        if not clean_ref:
            continue
            
        target = (html_path.parent / clean_ref).resolve()
        if not target.exists() and not (target / "index.html").exists():
            ext = target.suffix.lower()
            missing_by_type[ext] += 1
            missing_details.append({
                'source': str(html_path),
                'ref': ref,
                'target': str(target),
                'ext': ext
            })

print(f"Total missing: {len(missing_details)}")
print("By extension:", missing_by_type)

# Let's inspect some of the .html missing targets
print("\nSample missing .html:")
html_missing = [m for m in missing_details if m['ext'] == '.html']
for m in html_missing[:15]:
    print(f"  {m['source']} -> {m['ref']}")

# Let's inspect missing images/media
media_missing = [m for m in missing_details if m['ext'] in ('.jpg', '.png', '.jpeg', '.gif', '.svg', '.mp3', '.pdf')]
print(f"\nTotal missing media/docs: {len(media_missing)}")
for m in media_missing[:15]:
    print(f"  {m['source']} -> {m['ref']}")
