import re
import os

for path, title in [
    ('public/obec-2/aktuality/index.html', 'Aktuality'),
    ('public/obec-2/fotogaleria/index.html', 'Fotogaleria'),
    ('public/samosprava/obecne-zastupitelstvo/uznesenia-oz/index.html', 'Uznesenia OZ'),
    ('public/samosprava/obecne-zastupitelstvo/zapisnice/index.html', 'Zapisnice OZ'),
    ('public/volby-a-referendum/index.html', 'Volby a referendum')
]:
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    
    # Find all articles/cards/rows
    articles = re.findall(r'<div class="item[^"]*"', c)
    if not articles:
        articles = re.findall(r'<article[^>]*>', c)
    if not articles:
        articles = re.findall(r'<tr[^>]*id="[^"]*"', c)
    if not articles:
        # check headings or titles
        articles = re.findall(r'<h3 class="[^"]*heading[^"]*"|<h2 class="[^"]*heading[^"]*"', c)
        
    print(f'{title} ({path}): found {len(articles)} items with pattern')
    # find sample content snippet
    main = re.search(r'<div class="module_content">(.*?)</div>\s*</div>\s*</div>', c, re.DOTALL)
    if main:
        print('  Snippet:', main.group(1)[:200].replace('\n', ' '))
    else:
        print('  No module_content found')
