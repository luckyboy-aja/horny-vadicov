import os
import shutil

renames = [
    (
        'public/samosprava/vzn/navrh-vzn-c-1-2026-o-podmienkach-posudzovania-odkazanosti-na-socialnu-sluzbu-podmienkach-poskytovania-opatrovatelskej-sluzby-odlahcovacej-sluzby-o-sposobe-a-vyske-uhrady-za-opatrovatelsku-sluzbu-odlahcovaciu-sluzbu-1389',
        'public/samosprava/vzn/navrh-vzn-c-1-2026-o-podmienkach-posudzovania-1389',
        'public/samosprava/vzn/index.html'
    ),
    (
        'public/samosprava/vzn/vzn-c-1-2026-o-podmienkach-posudzovania-odkazanosti-na-socialnu-sluzbu-podmienkach-poskytovania-opatrovatelskej-sluzby-odlahcovacej-sluzby-o-sposobe-a-vyske-uhrady-za-opatrovatelsku-sluzbu-odlahcovaciu-sluzbu-1392',
        'public/samosprava/vzn/vzn-c-1-2026-o-podmienkach-posudzovania-1392',
        'public/samosprava/vzn/index.html'
    ),
    (
        'public/zverejnovanie/uradna-tabula-1/uznesenie-vlady-slovenskej-republiky-c-148-z-25-marca-2025-k-navrhu-na-vyhlasenie-mimoriadnej-situacie-v-suvislosti-s-vyskytom-vysoko-nakazliveho-virusu-slintacky-a-krivacky-na-uzemi-slovenskej-republiky-1341',
        'public/zverejnovanie/uradna-tabula-1/uznesenie-vlady-sr-c-148-mimoriadna-situacia-1341',
        'public/zverejnovanie/uradna-tabula-1/index.html'
    )
]

for old_dir, new_dir, index_file in renames:
    old_base = os.path.basename(old_dir)
    new_base = os.path.basename(new_dir)
    if os.path.exists(old_dir):
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        os.rename(old_dir, new_dir)
        print(f"Renamed {old_base} -> {new_base}")
    
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            c = f.read()
        if old_base in c:
            c = c.replace(old_base, new_base)
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(c)
            print(f"Updated reference in {index_file}")

print("Done renaming long directories.")
