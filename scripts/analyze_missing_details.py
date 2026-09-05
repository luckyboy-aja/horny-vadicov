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

print("\n--- SAMPLE EMPTY EXT (no dot in filename) ---")
empty_items = [m for m in missing_details if m['ext'] == '']
print(f"Total: {len(empty_items)}")
unique_empty_refs = set(m['ref'] for m in empty_items)
for r in list(unique_empty_refs)[:25]:
    print(f"  Ref: {r}")

print("\n--- SAMPLE MISSING CSS ---")
css_items = [m for m in missing_details if m['ext'] == '.css']
for m in css_items[:10]:
    print(f"  {m['source']} -> {m['ref']} -> {m['target']}")

print("\n--- SAMPLE MISSING PDF / DOCX / PHP ---")
doc_items = [m for m in missing_details if m['ext'] in ('.pdf', '.docx', '.php')]
for m in doc_items:
    print(f"  {m['source']} -> {m['ref']} -> {m['target']}")
