import json

with open('scripts/all_external_targets.json', 'r', encoding='utf-8') as f:
    cats = json.load(f)

for cat in ['ostatne_dokumenty', 'dobropisy', 'other']:
    print(f"\n--- {cat} ({len(cats[cat])}) ---")
    for u in cats[cat]:
        print(" ", u)
