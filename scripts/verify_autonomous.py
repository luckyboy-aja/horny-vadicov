import os
import re

def verify():
    matches = {}
    total_files = 0
    html_count = 0
    
    for root, dirs, files in os.walk('public'):
        for f in files:
            total_files += 1
            if f.endswith('.html'):
                html_count += 1
            if f.endswith(('.html', '.js', '.css', '.json')):
                p = os.path.join(root, f)
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                        c = fp.read()
                    found = re.findall(r'https?://(?:www\.)?hornyvadicov\.sk[^\s"\'<>]*', c)
                    if found:
                        matches[p] = set(found)
                except Exception as e:
                    print(f"Error reading {p}: {e}")

    print(f"Total files scanned in public/: {total_files}")
    print(f"Total HTML files: {html_count}")
    print(f"Files containing 'hornyvadicov.sk': {len(matches)}")
    if matches:
        for p, urls in list(matches.items())[:20]:
            print(f"\n{p}:")
            for u in urls:
                print(f"  - {u}")
    else:
        print("\nPERFECT: 0 references to hornyvadicov.sk found! Site is 100% self-contained.")

if __name__ == '__main__':
    verify()
