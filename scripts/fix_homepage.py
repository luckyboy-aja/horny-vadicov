"""
fix_homepage.py - Fixes external links in index.html
"""
import re, sys, json
from pathlib import Path
from urllib.parse import unquote

sys.stdout.reconfigure(encoding='utf-8')

# Load module mapping
with open('scripts/module_download_map.json', 'r', encoding='utf-8') as f:
    module_map = json.load(f)

# root_rel for homepage is "./"
root_rel = "./"

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# 1. Fix module download links
def fix_module(m):
    href = m.group(1)
    # Strip the base URL
    path = href.replace('https://www.hornyvadicov.sk', '').replace('http://www.hornyvadicov.sk', '')
    path_decoded = path.replace('&amp;', '&')
    local = module_map.get(path_decoded) or module_map.get(path)
    if local:
        return f'href="{root_rel}{local.lstrip("/")}"'
    return m.group(0)

content = re.sub(
    r'href="(https?://(?:www\.)?hornyvadicov\.sk/modules/file_storage/download\.php\?[^"]*)"',
    fix_module,
    content
)

# 2. Fix e_download.php links
def fix_edownload(m):
    href = m.group(1)
    path = href.replace('https://www.hornyvadicov.sk', '').replace('http://www.hornyvadicov.sk', '')
    file_match = re.search(r'file=([^&"\']+)', path)
    if not file_match:
        return m.group(0)
    file_path = unquote(file_match.group(1))
    clean_path = file_path.lstrip('/')
    local_file = Path("public") / clean_path
    if local_file.exists():
        return f'href="{root_rel}{clean_path}"'
    # Try to download it
    return m.group(0)  # Keep as external link if file doesn't exist locally

content = re.sub(
    r'href="(https?://(?:www\.)?hornyvadicov\.sk/e_download\.php\?[^"]*)"',
    fix_edownload,
    content
)

# 3. Fix links to pages that exist in our site
def fix_internal(m):
    href = m.group(1)
    path = href.replace('https://www.hornyvadicov.sk', '').replace('http://www.hornyvadicov.sk', '')
    # Check if it's a path to a local directory  
    clean = path.strip('/').split('?')[0].split('#')[0]
    local_dir = Path("public") / clean
    if local_dir.is_dir():
        return f'href="{root_rel}{path.lstrip("/")}"'
    # Also check if .html path has been converted to a directory (without extension)
    clean_no_ext = re.sub(r'\.html$', '', clean)
    local_dir2 = Path("public") / clean_no_ext
    if local_dir2.is_dir():
        # Return path without .html extension, as directory
        new_path = path.rstrip('/').replace('.html', '') + '/'
        return f'href="{root_rel}{new_path.lstrip("/")}"'
    return m.group(0)

content = re.sub(
    r'href="(https?://(?:www\.)?hornyvadicov\.sk/[^"]*)"',
    fix_internal,
    content
)

# Count fixes
mod_fixes = content.count('hornyvadicov.sk')
orig_count = original.count('hornyvadicov.sk')
print(f"External links: {orig_count} -> {mod_fixes} remaining")

if content != original:
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("index.html patched successfully")
else:
    print("No changes needed")
