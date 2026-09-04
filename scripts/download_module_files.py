import os
import re
import urllib.request
import ssl
import concurrent.futures
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

storage_dir = os.path.join('public', 'data', 'file_storage')
os.makedirs(storage_dir, exist_ok=True)

# 1. Find all module links in HTML files
all_html_files = []
module_links = set()
for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            all_html_files.append(p)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
            matches = re.findall(r'href=["\'](https://www\.hornyvadicov\.sk/modules/file_storage/download\.php\?[^"\']+|/modules/file_storage/download\.php\?[^"\']+)["\']', c)
            for m in matches:
                # normalize to full url
                full_u = m if m.startswith('http') else 'https://www.hornyvadicov.sk' + m
                module_links.add((m, full_u))

print(f"Nájdených {len(module_links)} unikátnych odkazov na modules/file_storage.")

# 2. Download files and map to local filename
url_to_local = {}

def download_module_file(item):
    orig_href, full_url = item
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            # check Content-Disposition or content type for filename
            cd = resp.headers.get('Content-Disposition', '')
            fname = None
            if 'filename=' in cd:
                fname_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';\r\n]+)', cd)
                if fname_match:
                    fname = urllib.parse.unquote(fname_match.group(1).strip('"\''))
            if not fname:
                # fallback from query param file=
                file_param = re.search(r'file=([^&]+)', full_url)
                raw_name = file_param.group(1).replace('%7C', '_').replace('|', '_') if file_param else 'file'
                fname = f"{raw_name}.pdf"
            
            # sanitize filename
            fname = re.sub(r'[\\/*?:"<>|]', '_', fname)
            dest_path = os.path.join(storage_dir, fname)
            
            data = resp.read()
            with open(dest_path, 'wb') as out_fp:
                out_fp.write(data)
            
            return orig_href, fname, True, len(data)
    except Exception as e:
        return orig_href, None, False, str(e)

print("Sťahujem súbory modulov...")
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(download_module_file, module_links))

success_map = {}
for orig_href, fname, ok, info in results:
    if ok:
        success_map[orig_href] = fname
        print(f"  [OK] {fname} ({info} B)")
    else:
        print(f"  [FAIL] {orig_href} -> {info}")

print(f"\nÚspešne stiahnutých: {len(success_map)} / {len(module_links)}")

# 3. Rewrite links in all HTML files
replaced_count = 0
for p in all_html_files:
    with open(p, 'r', encoding='utf-8') as fp:
        content = fp.read()
    
    modified = False
    for orig_href, fname in success_map.items():
        if orig_href in content:
            # calculate relative path from this HTML file to public/data/file_storage/fname
            html_dir = os.path.dirname(p)
            rel_to_file = os.path.relpath(os.path.join(storage_dir, fname), html_dir).replace('\\', '/')
            content = content.replace(f'href="{orig_href}"', f'href="{rel_to_file}"')
            content = content.replace(f"href='{orig_href}'", f"href='{rel_to_file}'")
            modified = True
            replaced_count += 1
            
    if modified:
        with open(p, 'w', encoding='utf-8') as fp:
            fp.write(content)

print(f"Prepísaných {replaced_count} výskytov odkazov v HTML súboroch.")
