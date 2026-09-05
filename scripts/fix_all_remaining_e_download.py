import os
import re
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
            if 'e_download.php' in c:
                def repl(m):
                    full_match = m.group(0)
                    file_path = m.group(1).lstrip('/')
                    # download file if not present
                    local_dest = os.path.join('public', file_path.replace('/', os.sep))
                    if not os.path.exists(local_dest) or os.path.getsize(local_dest) == 0:
                        os.makedirs(os.path.dirname(local_dest), exist_ok=True)
                        try:
                            req = urllib.request.Request(f"https://www.hornyvadicov.sk/{file_path}", headers=headers)
                            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                                data = resp.read()
                            with open(local_dest, 'wb') as df:
                                df.write(data)
                            print(f"Downloaded {file_path}")
                        except Exception as e:
                            print(f"Could not download {file_path}: {e}")
                    
                    # Compute relative path from current HTML directory to public/<file_path>
                    # Current html directory relative to 'public'
                    curr_rel_dir = os.path.relpath(os.path.dirname(p), 'public')
                    if curr_rel_dir == '.':
                        rel_link = file_path
                    else:
                        depth = len(curr_rel_dir.replace('\\', '/').split('/'))
                        rel_link = ('../' * depth) + file_path
                    return f'href="{rel_link}"'

                new_c = re.sub(r'href=[\'"][^\'"]*e_download\.php\?file=([^"\'&]+)[^\'"]*[\'"]', repl, c)
                if new_c != c:
                    with open(p, 'w', encoding='utf-8') as fp:
                        fp.write(new_c)
                    print(f"Fixed e_download in {p}")
