import os
import re
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

base_zfo = os.path.join('public', 'zverejnovanie', 'zmluvy-faktury-objednavky')
with open(os.path.join(base_zfo, 'index.html'), 'r', encoding='utf-8') as f:
    zmluvy_html = f.read()

# Template parts from zmluvy index.html
header_part = zmluvy_html.split('<div class="fso-content">')[0]
# Replace active tab in header for faktury
header_faktury = header_part.replace('class="nav-link active" role="tab" aria-selected="true">\n                        Zmluvy', 'class="nav-link" role="tab" aria-selected="false">\n                        Zmluvy')
header_faktury = re.sub(r'<a\s+href="[^"]*faktury\.html"[^>]*class="nav-link[^"]*"', '<a href="../faktury/" class="nav-link active" role="tab" aria-selected="true"', header_faktury)
header_faktury = re.sub(r'<a\s+href="[^"]*objednavky\.html"[^>]*class="nav-link[^"]*"', '<a href="../objednavky/" class="nav-link"', header_faktury)
header_faktury = header_faktury.replace('href="../../zverejnovanie/zmluvy-faktury-objednavky/" class="nav-link active"', 'href="../" class="nav-link"')
header_faktury = header_faktury.replace('../../', '../../../')

# Replace active tab in header for objednavky
header_objednavky = header_part.replace('class="nav-link active" role="tab" aria-selected="true">\n                        Zmluvy', 'class="nav-link" role="tab" aria-selected="false">\n                        Zmluvy')
header_objednavky = re.sub(r'<a\s+href="[^"]*faktury\.html"[^>]*class="nav-link[^"]*"', '<a href="../faktury/" class="nav-link"', header_objednavky)
header_objednavky = re.sub(r'<a\s+href="[^"]*objednavky\.html"[^>]*class="nav-link[^"]*"', '<a href="../objednavky/" class="nav-link active" role="tab" aria-selected="true"', header_objednavky)
header_objednavky = header_objednavky.replace('href="../../zverejnovanie/zmluvy-faktury-objednavky/" class="nav-link active"', 'href="../" class="nav-link"')
header_objednavky = header_objednavky.replace('../../', '../../../')

footer_part = zmluvy_html.split('</div>\n\n                                \n                </div>\n            </div>')[1]
footer_adj = footer_part.replace('../../', '../../../')

# 1. Fetch Faktury
print("Sťahujem kompletný archív faktúr (?page=all)...")
faktury_url = 'https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/faktury.html?page=all'
req = urllib.request.Request(faktury_url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
    faktury_live = resp.read().decode('utf-8', errors='ignore')

table_faktury_m = re.search(r'<table class="table[^"]*fso-table">.*?</table>', faktury_live, re.DOTALL)
if table_faktury_m:
    table_faktury = table_faktury_m.group(0)
    # Remove external links on detail (they only open empty detail)
    table_faktury = re.sub(r'<a\s+href="[^"]*faktura-[^"]*"[^>]*>(.*?)</a>', r'<span class="font-weight-bold">\1</span>', table_faktury)
    
    os.makedirs(os.path.join(base_zfo, 'faktury'), exist_ok=True)
    faktury_page = f"""{header_faktury}
        <div class="fso-content">
          <div class="table-responsive">
            {table_faktury}
          </div>
        </div>
      </div>
    </div>
{footer_adj}"""
    # Fix title
    faktury_page = re.sub(r'<title>.*?</title>', '<title>Faktúry | Zverejňovanie | Obec Horný Vadičov</title>', faktury_page)
    with open(os.path.join(base_zfo, 'faktury', 'index.html'), 'w', encoding='utf-8') as fp:
        fp.write(faktury_page)
    with open(os.path.join(base_zfo, 'faktury.html'), 'w', encoding='utf-8') as fp:
        fp.write(faktury_page.replace('../../../', '../../').replace('../', './'))
    print("  [OK] Faktúry vytvorené.")


# 2. Fetch Objednavky
print("Sťahujem kompletný archív objednávok (?page=all)...")
obj_url = 'https://www.hornyvadicov.sk/zverejnovanie/zmluvy-faktury-objednavky/objednavky.html?page=all'
req = urllib.request.Request(obj_url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
    obj_live = resp.read().decode('utf-8', errors='ignore')

table_obj_m = re.search(r'<table class="table[^"]*fso-table">.*?</table>', obj_live, re.DOTALL)
if table_obj_m:
    table_obj = table_obj_m.group(0)
    table_obj = re.sub(r'<a\s+href="[^"]*objednavka-[^"]*"[^>]*>(.*?)</a>', r'<span class="font-weight-bold">\1</span>', table_obj)
    
    os.makedirs(os.path.join(base_zfo, 'objednavky'), exist_ok=True)
    obj_page = f"""{header_objednavky}
        <div class="fso-content">
          <div class="table-responsive">
            {table_obj}
          </div>
        </div>
      </div>
    </div>
{footer_adj}"""
    obj_page = re.sub(r'<title>.*?</title>', '<title>Objednávky | Zverejňovanie | Obec Horný Vadičov</title>', obj_page)
    with open(os.path.join(base_zfo, 'objednavky', 'index.html'), 'w', encoding='utf-8') as fp:
        fp.write(obj_page)
    with open(os.path.join(base_zfo, 'objednavky.html'), 'w', encoding='utf-8') as fp:
        fp.write(obj_page.replace('../../../', '../../').replace('../', './'))
    print("  [OK] Objednávky vytvorené.")

# 3. Update tabs in zmluvy/index.html
new_zmluvy = zmluvy_html
new_zmluvy = re.sub(r'href="[^"]*faktury\.html"[^>]*', 'href="./faktury/" class="nav-link mr-1"', new_zmluvy)
new_zmluvy = re.sub(r'href="[^"]*objednavky\.html"[^>]*', 'href="./objednavky/" class="nav-link mr-1"', new_zmluvy)

with open(os.path.join(base_zfo, 'index.html'), 'w', encoding='utf-8') as fp:
    fp.write(new_zmluvy)
print("Navigačné záložky v zmluvy/index.html prepojené lokálne.")
