import sys
import os
import re
import json
import urllib.request
import xml.etree.ElementTree as ET
import requests
import lxml.html
from urllib.parse import urljoin, urlparse

sys.stdout.reconfigure(encoding='utf-8')

SITEMAP_URL = 'https://www.hornyvadicov.sk/sitemap.xml'
BASE_URL = 'https://www.hornyvadicov.sk'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("1. Načítavam sitemap.xml...")
r = requests.get(SITEMAP_URL, headers=headers, timeout=15)
tree = ET.fromstring(r.content)
urls = [loc.text.strip() for loc in tree.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]

print(f"Nájdených {len(urls)} URL adries.")

scraped_pages = []
all_images = set()
all_documents = set()

for idx, url in enumerate(urls, 1):
    try:
        path = urlparse(url).path
        print(f"[{idx}/{len(urls)}] Sťahujem: {path} ...")
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        
        doc = lxml.html.fromstring(resp.text)
        
        # 1. Názov stránky
        h1 = doc.xpath('//h1/text()')
        title = h1[0].strip() if h1 else ''
        if not title:
            t = doc.xpath('//title/text()')
            title = t[0].split('-')[0].strip() if t else 'Obec Horný Vadičov'
            
        # 2. Drobky (Breadcrumbs)
        breadcrumb_nodes = doc.xpath('//ol[contains(@class, "breadcrumb")]//li')
        breadcrumbs = []
        for b in breadcrumb_nodes:
            b_text = b.text_content().strip()
            b_link = b.xpath('.//a/@href')
            link = b_link[0] if b_link else ''
            if b_text:
                breadcrumbs.append({'text': b_text, 'link': link})
                
        # 3. Bočné menu danej sekcie (Submenu)
        submenu_items = []
        submenu_nodes = doc.xpath('//nav[@id="submenu"]//li')
        for item in submenu_nodes:
            a = item.xpath('.//a')
            if a:
                item_text = a[0].text_content().strip()
                item_href = a[0].get('href', '')
                is_active = 'active' in item.get('class', '') or 'active' in a[0].get('class', '')
                if item_text and item_href:
                    submenu_items.append({
                        'text': item_text,
                        'href': item_href,
                        'active': is_active
                    })
                    
        # 4. Hlavný obsah (gcm-main alebo editor_content)
        main_nodes = doc.xpath('//div[contains(@class, "gcm-main")]')
        content_html = ""
        if main_nodes:
            # Odstránime prípadný h1 z obsahu, aby sme ho nezdvojovali
            for h in main_nodes[0].xpath('.//h1'):
                h.drop_tree()
            content_html = lxml.html.tostring(main_nodes[0], encoding='unicode')
        else:
            editor = doc.xpath('//div[contains(@class, "editor_content")]')
            if editor:
                content_html = lxml.html.tostring(editor[0], encoding='unicode')

        # 5. Vyhľadanie obrázkov a dokumentov v obsahu
        imgs = re.findall(r'src=[\'"]([^\'"]+)[\'"]', content_html)
        for img in imgs:
            if img.startswith('/'):
                all_images.add(img)
                
        docs = re.findall(r'href=[\'"]([^\'"]*(?:e_download\.php|\.pdf|\.docx?|\.xlsx?)[^\'"]*)[\'"]', content_html, re.I)
        for d in docs:
            if d.startswith('/'):
                all_documents.add(d)

        scraped_pages.append({
            'url': url,
            'path': path,
            'title': title,
            'breadcrumbs': breadcrumbs,
            'submenu': submenu_items,
            'content_html': content_html
        })
    except Exception as e:
        print(f"  Chyba pri {url}: {e}")

output_file = 'scripts/scraped_data.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'pages': scraped_pages,
        'images': list(all_images),
        'documents': list(all_documents)
    }, f, ensure_ascii=False, indent=2)

print("\n--- Hotovo ---")
print(f"Úspešne spracovaných stránok: {len(scraped_pages)}")
print(f"Nájdených unikátnych obrázkov v obsahu: {len(all_images)}")
print(f"Nájdených unikátnych dokumentov/príloh v obsahu: {len(all_documents)}")
print(f"Dáta uložené v {output_file}")
