import os
import re

ZAPISNICE_PATH = 'public/samosprava/obecne-zastupitelstvo/zapisnice/index.html'

with open(ZAPISNICE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Find each file-row block that contains an audio element
# e.g.:
# <a ... href="(../../../data/file_storage/[^"]+)" ...>
# ...
# <audio controls src="(https://www\.hornyvadicov\.sk/modules/file_storage/download\.php\?[^"]+)"

pattern = re.compile(
    r'(<a [^>]*href=[\'"]([^\'"]+data/file_storage/[^\'"]+)[\'"][^>]*>[\s\S]*?<audio [^>]*src=[\'"])(https://www\.hornyvadicov\.sk/modules/file_storage/download\.php\?[^\'"]+)([\'"])',
    re.MULTILINE
)

def replacer(m):
    prefix = m.group(1)
    file_href = m.group(2)
    old_url = m.group(3)
    suffix = m.group(4)
    print(f"Replacing audio src {old_url} with {file_href}")
    return f"{prefix}{file_href}{suffix}"

new_content, count = pattern.subn(replacer, content)
print(f"Total replaced audio src: {count}")

with open(ZAPISNICE_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)
