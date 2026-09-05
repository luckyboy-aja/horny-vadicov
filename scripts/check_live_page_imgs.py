import requests
import re

r = requests.get('https://www.hornyvadicov.sk/mobilna-aplikacia/')
imgs = re.findall(r'<img [^>]*src=[\'"]([^\'"]+)[\'"]', r.text)
for img in imgs:
    print('Original img:', img)
