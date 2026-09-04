import os
import re

for name, rel_path in [
    ('Uradna tabula', 'zverejnovanie/uradna-tabula-1/index.html'),
    ('Uznesenia OZ', 'samosprava/obecne-zastupitelstvo/uznesenia-oz/index.html'),
    ('Zapisnice OZ', 'samosprava/obecne-zastupitelstvo/zapisnice/index.html'),
    ('VZN', 'samosprava/vzn/index.html'),
    ('Volby a referendum', 'volby-a-referendum/index.html'),
    ('Archiv zmluv', 'zverejnovanie/zmluvy-faktury-objednavky/archiv-zfo/zmluvy/index.html')
]:
    p = os.path.join('public', rel_path)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            c = f.read()
        table_match = re.findall(r'<table[^>]*>', c)
        tr_match = re.findall(r'<tr[^>]*>', c)
        a_match = re.findall(r'<a\s+[^>]*href=', c)
        print(f'{name} ({rel_path}):')
        print(f'  Tables: {len(table_match)}, Rows: {len(tr_match)}, Links: {len(a_match)}')
        # Print sample snippet around first <tr> or table
        tbody = re.search(r'<tbody>(.*?)</tbody>', c, re.DOTALL)
        if tbody:
            first_tr = re.search(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL)
            if first_tr:
                text_clean = re.sub(r'<[^>]+>', ' ', first_tr.group(1))
                print('  Sample row:', ' '.join(text_clean.split())[:100])
        else:
            print('  No tbody found')
