"""
patch_all_pages.py
Patches all generated HTML pages to:
1. Replace /modules/file_storage/download.php links with local file paths
2. Fix remaining external hornyvadicov.sk links to local paths
3. Replace e_download.php links with direct file paths
4. Fix any remaining root-relative (/) links that should be root-rel based
"""
import sys
import os
import re
import json
from pathlib import Path
from urllib.parse import unquote

sys.stdout.reconfigure(encoding='utf-8')

# Load module download mapping
mapping_file = Path("scripts/module_download_map.json")
if not mapping_file.exists():
    print("ERROR: scripts/module_download_map.json not found! Run fix_module_downloads.py first.")
    sys.exit(1)

with open(mapping_file, 'r', encoding='utf-8') as f:
    module_map = json.load(f)

print(f"Loaded {len(module_map)} module download mappings")
successful_maps = {k: v for k, v in module_map.items() if v is not None}
print(f"  Successful: {len(successful_maps)}")

# Load URL rewrite map for images
rewrite_map = {}
if Path("scripts/url_rewrite_map.json").exists():
    with open("scripts/url_rewrite_map.json", 'r', encoding='utf-8') as f:
        rewrite_map = json.load(f)

def get_root_rel(html_file_path):
    """Get relative path to root from a given HTML file."""
    rel = Path(html_file_path).relative_to(Path("public"))
    depth = len(rel.parts) - 1  # -1 for index.html
    if depth == 0:
        return "./"
    return "../" * depth

def fix_module_link(match, root_rel):
    """Replace /modules/file_storage/download.php?... with local path."""
    full_match = match.group(0)
    href = match.group(1).replace('&amp;', '&')
    
    # Look up in mapping (try both encoded and decoded)
    local_path = module_map.get(href) or module_map.get(href.replace('&', '&amp;'))
    
    if local_path:
        # Convert absolute local path to root-relative
        # local_path is like /data/file_storage/FILENAME.pdf
        rel_path = root_rel + local_path.lstrip('/')
        return full_match.replace(match.group(1), rel_path)
    else:
        # Fall back to original site link
        fallback = f"https://www.hornyvadicov.sk{href}"
        return full_match.replace(match.group(1), fallback)

def fix_edownload_link(match, root_rel):
    """Replace /e_download.php?file=PATH links with direct file paths."""
    full_match = match.group(0)
    href_attr = match.group(1)  # the full href value
    file_path = match.group(2)  # the 'file' parameter value
    
    # Decode the path
    decoded = unquote(file_path.replace('&amp;', '&'))
    # Normalize: remove leading slash if present
    clean_path = decoded.lstrip('/')
    
    # Check if file exists
    local_file = Path("public") / clean_path
    if local_file.exists():
        rel_path = root_rel + clean_path
        return full_match.replace(href_attr, rel_path)
    else:
        # Fallback to original
        fallback = f"https://www.hornyvadicov.sk{href_attr}"
        return full_match.replace(href_attr, fallback)

def patch_html(content, html_file_path):
    """Apply all fixes to HTML content."""
    root_rel = get_root_rel(html_file_path)
    changes = 0
    
    # 1. Fix /modules/file_storage/download.php links
    def replace_module(m):
        nonlocal changes
        result = fix_module_link(m, root_rel)
        if result != m.group(0):
            changes += 1
        return result
    
    content = re.sub(
        r'(href|src)=["\'](/modules/file_storage/download\.php\?[^"\']*)["\']',
        lambda m: m.group(0)[:len(m.group(1))+2] + fix_module_link_href(m.group(2).replace('&amp;', '&'), root_rel) + m.group(0)[-1],
        content
    )
    
    # 2. Fix /e_download.php links
    # Pattern: href="/e_download.php?file=PATH&original=..."
    def replace_edownload(m):
        nonlocal changes
        href = m.group(1)
        # Extract file param
        file_match = re.search(r'file=([^&"\']+)', href)
        if not file_match:
            return m.group(0)
        file_path = unquote(file_match.group(1))
        clean_path = file_path.lstrip('/')
        local_file = Path("public") / clean_path
        if local_file.exists():
            rel_path = root_rel + clean_path
            changes += 1
            return m.group(0).replace(href, rel_path)
        else:
            # Fallback
            return m.group(0).replace(href, f"https://www.hornyvadicov.sk{href}")
    
    content = re.sub(r'href=["\'](?P<href>/e_download\.php\?[^"\']*)["\']',
                     lambda m: f'href="{replace_edownload_href(m.group("href"), root_rel)}"',
                     content)
    
    # 3. Fix remaining absolute hornyvadicov.sk links in content
    # These are absolute links that should point to our clone
    def replace_absolute(m):
        nonlocal changes
        path = m.group(1)  # e.g., /zverejnovanie/...
        # Check if this is a known page in our site
        if path.endswith('/') or '.' not in path.split('/')[-1]:
            local_dir = Path("public") / path.lstrip('/')
            if local_dir.exists():
                changes += 1
                return m.group(0).replace(
                    f"https://www.hornyvadicov.sk{path}",
                    root_rel + path.lstrip('/')
                )
        return m.group(0)
    
    content = re.sub(
        r'href=["\']https?://(?:www\.)?hornyvadicov\.sk(/[^"\']*)["\']',
        replace_absolute,
        content
    )
    
    return content, changes

def fix_module_link_href(href, root_rel):
    """Get local path for module link href."""
    local_path = module_map.get(href) or module_map.get(href.replace('&', '&amp;'))
    if local_path:
        return root_rel + local_path.lstrip('/')
    return f"https://www.hornyvadicov.sk{href}"

def replace_edownload_href(href, root_rel):
    """Get local path for e_download href."""
    file_match = re.search(r'file=([^&"\']+)', href)
    if not file_match:
        return f"https://www.hornyvadicov.sk{href}"
    file_path = unquote(file_match.group(1).replace('&amp;', '&'))
    clean_path = file_path.lstrip('/')
    local_file = Path("public") / clean_path
    if local_file.exists():
        return root_rel + clean_path
    return f"https://www.hornyvadicov.sk{href}"

# Process all HTML files
html_files = list(Path("public").rglob("*.html"))
print(f"\nPatching {len(html_files)} HTML files...")

total_changes = 0
patched_files = 0

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        original = f.read()
    
    # Fix module download links
    root_rel = get_root_rel(html_file)
    modified = original
    changes_in_file = 0
    
    # 1. /modules/file_storage/download.php links
    def replace_mod(m):
        global changes_in_file
        href_raw = m.group(2)
        href = href_raw.replace('&amp;', '&')
        local_path = module_map.get(href) or module_map.get(href.replace('&', '&amp;'))
        new_href = (root_rel + local_path.lstrip('/')) if local_path else f"https://www.hornyvadicov.sk{href}"
        if new_href != href_raw:
            changes_in_file += 1
        quote_char = m.group(0)[len(m.group(1))+1]
        return f'{m.group(1)}={quote_char}{new_href}{quote_char}'
    
    new_content = re.sub(
        r'(href|src)=(["\'])(/modules/file_storage/download\.php\?[^"\']*)\2',
        replace_mod,
        modified
    )
    changes_in_file_mod = modified.count('/modules/file_storage') - new_content.count('/modules/file_storage')
    modified = new_content
    
    # 2. /e_download.php links
    def replace_edl(m):
        href = m.group(1)
        result = replace_edownload_href(href, root_rel)
        return f'href="{result}"'
    
    new_content = re.sub(r'href="(/e_download\.php\?[^"]*)"', replace_edl, modified)
    changes_edl = modified.count('/e_download.php') - new_content.count('/e_download.php')
    modified = new_content
    
    # 3. Remaining hornyvadicov.sk absolute links pointing to known local pages
    def replace_abs(m):
        path = m.group(1)
        # Only replace if it's a path to a local page directory
        local_dir = Path("public") / path.strip('/').split('?')[0].split('#')[0]
        if local_dir.is_dir():
            return f'href="{root_rel}{path.lstrip("/")}"'
        return m.group(0)
    
    new_content = re.sub(
        r'href="https?://(?:www\.)?hornyvadicov\.sk(/[^"]*)"',
        replace_abs,
        modified
    )
    changes_abs = modified.count('hornyvadicov.sk') - new_content.count('hornyvadicov.sk')
    modified = new_content
    
    total_file_changes = changes_in_file_mod + changes_edl + changes_abs
    
    if modified != original:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(modified)
        patched_files += 1
        total_changes += total_file_changes
        print(f"[PATCHED] {html_file}: {total_file_changes} changes (mod:{changes_in_file_mod}, edl:{changes_edl}, abs:{changes_abs})")
    
print(f"\n=== DONE ===")
print(f"Patched files: {patched_files}")
print(f"Total changes: {total_changes}")
