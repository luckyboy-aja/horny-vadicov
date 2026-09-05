import requests
import re

r = requests.get('https://www.hornyvadicov.sk/uzemny-plan/1-prieskumy-a-rozbory/')
for m in re.finditer(r'href=[\'"]([^\'"]+)[\'"][^>]*>([^<]+)</a>', r.text):
    href = m.group(1)
    text = m.group(2).strip()
    if 'pdf' in href.lower() or 'download' in href.lower():
        print(f"{text} -> {href}")
        # test downloading
        full_url = requests.compat.urljoin('https://www.hornyvadicov.sk/uzemny-plan/1-prieskumy-a-rozbory/', href)
        head = requests.head(full_url)
        print(f"  Head status: {head.status_code}")
