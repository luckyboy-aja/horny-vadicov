import os
import re

storage_dir = os.path.join('public', 'data', 'file_storage')
zapisnice_path = os.path.join('public', 'samosprava', 'obecne-zastupitelstvo', 'zapisnice', 'index.html')

files_to_split = [
    ('DVT_B020_230303_1702.MP3', 'DVT_B020_230303_1702_cast1.MP3', 'DVT_B020_230303_1702_cast2.MP3', '03.03.2023'),
    ('DVT_D010_110830_2327.mp3', 'DVT_D010_110830_2327_cast1.mp3', 'DVT_D010_110830_2327_cast2.mp3', '30.08.2011')
]

with open(zapisnice_path, 'r', encoding='utf-8') as fp:
    html = fp.read()

for orig_name, part1_name, part2_name, date_label in files_to_split:
    orig_path = os.path.join(storage_dir, orig_name)
    if not os.path.exists(orig_path):
        continue
    
    file_size = os.path.getsize(orig_path)
    if file_size < 90 * 1024 * 1024:
        continue
    
    print(f"Splitting {orig_name} ({file_size / (1024*1024):.2f} MB)...")
    with open(orig_path, 'rb') as fp:
        data = fp.read()
    
    half = len(data) // 2
    # Find next MP3 sync word (0xFF followed by 0xE0-0xFF)
    split_pos = half
    for i in range(half, half + 100000):
        if data[i] == 0xFF and (data[i+1] & 0xE0) == 0xE0:
            split_pos = i
            break
            
    part1_data = data[:split_pos]
    part2_data = data[split_pos:]
    
    part1_path = os.path.join(storage_dir, part1_name)
    part2_path = os.path.join(storage_dir, part2_name)
    
    with open(part1_path, 'wb') as fp:
        fp.write(part1_data)
    with open(part2_path, 'wb') as fp:
        fp.write(part2_data)
        
    print(f"  Created {part1_name}: {len(part1_data) / (1024*1024):.2f} MB")
    print(f"  Created {part2_name}: {len(part2_data) / (1024*1024):.2f} MB")
    
    # Remove original large file to keep git under 100MB
    os.remove(orig_path)
    print(f"  Removed {orig_name}")
    
    # Update link in HTML
    # Replace single link with part1 and part2 links
    old_snippet = f'href="../../../data/file_storage/{orig_name}"'
    if old_snippet in html:
        # replace with part 1 link and add part 2
        html = html.replace(
            f'href="../../../data/file_storage/{orig_name}" target="_blank" rel="noopener noreferrer" target="_self" download="{orig_name}">Zvukový záznam zo zasadnutia Obecného zastupiteľstva v Hornom Vadičove zo dňa {date_label}',
            f'href="../../../data/file_storage/{part1_name}" target="_blank" rel="noopener noreferrer" download="{part1_name}">Zvukový záznam zo zasadnutia OZ dňa {date_label} (1. časť)</a></h2>\n<h2><a class="link-small" href="../../../data/file_storage/{part2_name}" target="_blank" rel="noopener noreferrer" download="{part2_name}">Zvukový záznam zo zasadnutia OZ dňa {date_label} (2. časť)'
        )
        html = html.replace(orig_name, part1_name)

with open(zapisnice_path, 'w', encoding='utf-8') as fp:
    fp.write(html)

print("Updated zapisnice/index.html successfully.")
