import os
import re
import json

targets = set()
by_file = {}

for root, dirs, files in os.walk('public'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
            matches = re.findall(r'href=["\'](https://www\.hornyvadicov\.sk/[^"\'#?]+(?:\?[^"\']*)?)["\']', c)
            if matches:
                by_file[p] = matches
                for m in matches:
                    targets.add(m)

print(f"Total unique target URLs on hornyvadicov.sk: {len(targets)}")

categorized = {
    'aktuality': [],
    'uradna_tabula': [],
    'vzn': [],
    'pozvanky': [],
    'zapisnice_uznesenia_module': [],
    'faktury_objednavky_current': [],
    'archiv_zfo': [],
    'ostatne_dokumenty': [],
    'dobropisy': [],
    'fotogaleria': [],
    'other': []
}

for t in sorted(targets):
    if '/obec-2/aktuality/' in t:
        categorized['aktuality'].append(t)
    elif '/zverejnovanie/uradna-tabula-1/' in t:
        categorized['uradna_tabula'].append(t)
    elif '/samosprava/vzn/' in t:
        categorized['vzn'].append(t)
    elif '/pozvanky-na-zasadnutie-oz-1/' in t:
        categorized['pozvanky'].append(t)
    elif '/modules/file_storage/' in t:
        categorized['zapisnice_uznesenia_module'].append(t)
    elif '/archiv-zfo/' in t:
        categorized['archiv_zfo'].append(t)
    elif any(x in t for x in ['faktury.html', 'objednavky.html', 'faktura-', 'objednavka-']):
        categorized['faktury_objednavky_current'].append(t)
    elif '/ostatne-dokumenty/' in t:
        categorized['ostatne_dokumenty'].append(t)
    elif '/dobropisy/' in t:
        categorized['dobropisy'].append(t)
    elif '/fotogaleria/' in t:
        categorized['fotogaleria'].append(t)
    else:
        categorized['other'].append(t)

print("\nBreakdown by category:")
for cat, items in categorized.items():
    print(f"  {cat:30s}: {len(items)} unique URLs")

with open('scripts/all_external_targets.json', 'w', encoding='utf-8') as fp:
    json.dump(categorized, fp, ensure_ascii=False, indent=2)

print("\nSaved to scripts/all_external_targets.json")
