import re

with open('public/zverejnovanie/uradna-tabula-1/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

for id_num in ['1430', '1429', '1428', '1431', '1423']:
    matches = re.findall(rf'href=["\']([^"\']*{id_num}[^"\']*)["\']', c)
    print(id_num, '->', matches)
