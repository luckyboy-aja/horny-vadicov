import os
import re
import urllib.request
import ssl
import concurrent.futures

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

# Find all e_download.php references across all HTML files
edl_files = set()
for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
            matches = re.findall(r'href=["\'](?:https?://(?:www\.)?hornyvadicov\.sk)?/e_download\.php\?file=([^"\'&]+)', c)
            for m in matches:
                # clean path
                clean_path = m.lstrip('/')
                edl_files.add(clean_path)

print(f"Nájdených {len(edl_files)} unikátnych súborov cez e_download.php.")

# Download missing files to public/<clean_path>
def download_edl_file(rel_path):
    dest_path = os.path.join('public', rel_path.replace('/', os.sep))
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return rel_path, True, 'exists'
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    full_url = f"https://www.hornyvadicov.sk/{rel_path}"
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                data = resp.read()
            with open(dest_path, 'wb') as fp:
                fp.write(data)
            return rel_path, True, f"{len(data)} B"
        except Exception as e:
            if attempt == 2:
                return rel_path, False, str(e)

print("Sťahujem chýbajúce súbory...")
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
    results = list(executor.map(download_edl_file, edl_files))

ok_count = sum(1 for p, ok, msg in results if ok)
print(f"Stiahnutých/overených: {ok_count} / {len(edl_files)} súborov.")

# Rewrite /e_download.php?file=... to relative path in each HTML file
for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                content = fp.read()
            
            if 'e_download.php' in content:
                def repl_edl(match):
                    file_arg = match.group(1).lstrip('/')
                    # calculate relative path from p to public/file_arg
                    html_dir = os.path.dirname(p)
                    target_file = os.path.join('public', file_arg.replace('/', os.sep))
                    rel = os.path.relpath(target_file, html_dir).replace('\\', '/')
                    return f'href="{rel}"'
                
                content = re.sub(r'href=["\'](?:https?://(?:www\.)?hornyvadicov\.sk)?/e_download\.php\?file=([^"\'&]+)(?:&amp;[^"\']*)?["\']', repl_edl, content)
                with open(p, 'w', encoding='utf-8') as fp:
                    fp.write(content)

print("Všetky e_download.php odkazy prepísané na priame lokálne súbory.")
