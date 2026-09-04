import os
import requests
import lxml.html
from lxml import etree

test_urls = [
    'https://www.hornyvadicov.sk/obec-2/historia/',
    'https://www.hornyvadicov.sk/samosprava/starostka-obce/',
    'https://www.hornyvadicov.sk/zverejnovanie/uradna-tabula-1/stavebne-konanie/'
]

headers = {'User-Agent': 'Mozilla/5.0'}

for url in test_urls:
    r = requests.get(url, headers=headers, timeout=10)
    doc = lxml.html.fromstring(r.content)
    
    # Title
    h1 = doc.xpath('//h1/text()')
    title = h1[0].strip() if h1 else 'Bez názvu'
    
    # Breadcrumbs
    breadcrumbs = [b.strip() for b in doc.xpath('//ol[contains(@class, "breadcrumb")]//li//text()') if b.strip()]
    
    # Content node
    content_node = doc.xpath('//div[contains(@class, "gcm-main")]')
    content_html = ""
    if content_node:
        content_html = lxml.html.tostring(content_node[0], encoding='unicode')
        
    print(f"URL: {url}")
    print(f"  Title: {title}")
    print(f"  Breadcrumbs: {' > '.join(breadcrumbs)}")
    print(f"  Content length: {len(content_html)} chars")
    print(f"  Text snippet: {content_node[0].text_content().strip()[:100]}...\n")
