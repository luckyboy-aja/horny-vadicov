import requests
import lxml.html

url = 'https://www.hornyvadicov.sk/obec-2/historia/'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
r.encoding = 'utf-8'
doc = lxml.html.fromstring(r.text)

h1 = doc.xpath('//h1/text()')
title = h1[0].strip() if h1 else 'Bez názvu'
print('Decoded title:', title)

# Check main content
main = doc.xpath('//div[contains(@class, "gcm-main")]')
if main:
    # Remove breadcrumbs from main if inside
    print('Found main, text length:', len(main[0].text_content()))
    # Check if there are images
    imgs = main[0].xpath('.//img/@src')
    print('Found images:', len(imgs), imgs[:3])
    # Check if there are links
    links = main[0].xpath('.//a/@href')
    print('Found links:', len(links), links[:3])
