import os

for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
            if 'https://www.hornyvadicov.sk/' in c or 'http://www.hornyvadicov.sk/' in c:
                # calculate rel path to root
                rel_dir = os.path.relpath('public', os.path.dirname(p)).replace('\\', '/')
                rel_root = (rel_dir + '/') if rel_dir and rel_dir != '.' else './'
                
                c = c.replace('href="https://www.hornyvadicov.sk/"', f'href="{rel_root}"')
                c = c.replace("href='https://www.hornyvadicov.sk/'", f"href='{rel_root}'")
                c = c.replace('href="http://www.hornyvadicov.sk/"', f'href="{rel_root}"')
                c = c.replace("href='http://www.hornyvadicov.sk/'", f"href='{rel_root}'")
                
                with open(p, 'w', encoding='utf-8') as fp:
                    fp.write(c)

print("Root breadcrumb links fixed.")
