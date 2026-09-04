"""
fix_module_downloads.py
- Fetches all /modules/file_storage/download.php links from original site
- Downloads the actual files
- Saves a mapping for updating pages
"""
import re, json, os, sys
from pathlib import Path
import requests
from urllib.parse import unquote, urlencode, parse_qs, urlparse

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://www.hornyvadicov.sk"
OUT_DIR = Path("public/data/file_storage")
OUT_DIR.mkdir(parents=True, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Collect all unique module links from generated pages
all_module_links = set()
for html_file in Path('public').rglob('*.html'):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find both encoded and decoded versions
    mods = re.findall(r'href=["\'](/modules/file_storage/download\.php\?[^"\']*)["\']', content)
    for l in mods:
        all_module_links.add(l.replace('&amp;', '&'))

print(f"Found {len(all_module_links)} unique module download links")

# Try to load existing mapping
mapping_file = Path("scripts/module_download_map.json")
mapping = {}
if mapping_file.exists():
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    print(f"Loaded {len(mapping)} existing mappings")

# Download each file
for i, link in enumerate(sorted(all_module_links), 1):
    if link in mapping:
        print(f"[{i}/{len(all_module_links)}] SKIP (already mapped): {link[:60]}")
        continue
    
    full_url = f"{BASE_URL}{link}"
    print(f"[{i}/{len(all_module_links)}] Fetching: {link[:60]}")
    
    try:
        r = requests.get(full_url, headers=headers, timeout=20, allow_redirects=True)
        
        if r.status_code != 200:
            print(f"  -> HTTP {r.status_code}, skipping")
            mapping[link] = None
            continue
        
        # Get filename from Content-Disposition
        cd = r.headers.get('Content-Disposition', '')
        filename = None
        if cd:
            m = re.search(r'filename\*?=["\']?(?:UTF-8\'\')?([^"\';\r\n]+)', cd, re.I)
            if m:
                filename = unquote(m.group(1).strip().strip('"\''))
        
        # Fallback to URL
        if not filename:
            # Try to get from URL query param
            parsed = urlparse(full_url)
            qs = parse_qs(parsed.query)
            file_param = qs.get('file', [''])[0]
            if file_param:
                # Extract the part after |
                parts = file_param.split('|')
                filename = f"file_{parts[-1]}.bin" if parts else "unknown.bin"
            else:
                filename = "unknown.bin"
        
        # Sanitize filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        out_path = OUT_DIR / filename
        
        # Handle duplicates
        if out_path.exists():
            base = out_path.stem
            ext = out_path.suffix
            counter = 1
            while out_path.exists():
                out_path = OUT_DIR / f"{base}_{counter}{ext}"
                counter += 1
        
        with open(out_path, 'wb') as f:
            f.write(r.content)
        
        local_path = f"/data/file_storage/{out_path.name}"
        mapping[link] = local_path
        print(f"  -> Saved: {out_path.name} ({len(r.content)} bytes)")
        
    except Exception as e:
        print(f"  -> ERROR: {e}")
        mapping[link] = None
    
    # Save mapping after each download
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"\n=== Done ===")
successful = sum(1 for v in mapping.values() if v)
print(f"Successfully mapped: {successful}/{len(all_module_links)}")
print(f"Failed: {len([v for v in mapping.values() if v is None])}")
