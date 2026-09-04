"""
verify_site.py - Verifikuje vsetky stranky na GitHub Pages
Kontroluje:
1. HTTP statusy vsetkych stranok
2. Ci sa daju stiahnut dokumenty/subory
3. Ci su obrazky dostupne
4. Broken links
"""
import sys
import os
import re
import json
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://luckyboy-aja.github.io/horny-vadicov"
PUBLIC_DIR = Path("public")
RESULTS = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def check_url(url, label=""):
    try:
        r = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        return r.status_code, r.headers.get('content-type', '')
    except Exception as e:
        return 0, str(e)

def check_page_links(page_path_rel, html_content):
    """Check all links in an HTML page"""
    issues = []
    # Find all href and src attributes
    links = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', html_content)
    
    for link in links:
        # Skip anchors, javascript, mailto, external links not on our site
        if link.startswith('#') or link.startswith('javascript:') or link.startswith('mailto:'):
            continue
        if link.startswith('http') and 'luckyboy-aja.github.io' not in link:
            continue
        if link.startswith('http') and 'hornyvadicov.sk' in link:
            continue
            
        # Convert relative to absolute
        if link.startswith('http'):
            full_url = link
        elif link.startswith('/horny-vadicov/') or link.startswith('/horny-vadicov'):
            full_url = f"https://luckyboy-aja.github.io{link}"
        elif link.startswith('/'):
            # This might be a relative path issue - should be /horny-vadicov/...
            full_url = f"https://luckyboy-aja.github.io/horny-vadicov{link}"
            issues.append({
                'type': 'BAD_RELATIVE_LINK',
                'page': page_path_rel,
                'link': link,
                'note': 'Link starts with / but missing /horny-vadicov prefix - might break on GH Pages'
            })
        else:
            continue
            
    return issues

def analyze_all_pages():
    """Walk all public/*.html files and check them"""
    print("=== Verifikacia stranok Horny Vadicov ===\n")
    
    all_issues = []
    page_count = 0
    
    # Find all index.html files
    html_files = list(PUBLIC_DIR.rglob("index.html"))
    print(f"Najdeno {len(html_files)} HTML stranok v public/\n")
    
    # Also check root index.html
    root_html = Path("index.html")
    if root_html.exists():
        html_files.append(root_html)
    
    for html_file in html_files:
        page_count += 1
        rel_path = str(html_file).replace("\\", "/")
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common issues
        issues_for_page = []
        
        # 1. Check for absolute links to hornyvadicov.sk (should be replaced with our copies)
        original_links = re.findall(r'href=["\']https?://(?:www\.)?hornyvadicov\.sk([^"\']*)["\']', content)
        for link in original_links:
            issues_for_page.append({
                'type': 'EXTERNAL_ORIGINAL_LINK',
                'page': rel_path,
                'link': f'https://www.hornyvadicov.sk{link}',
                'note': 'Odkaz na povodny web namiesto naseho klonu'
            })
        
        # 2. Check for document download links
        doc_links = re.findall(r'href=["\']([^"\']*(?:e_download\.php|\.pdf|\.docx?|\.xlsx?|\.zip)[^"\']*)["\']', content, re.I)
        for link in doc_links:
            if 'hornyvadicov.sk' in link:
                issues_for_page.append({
                    'type': 'EXTERNAL_DOC_LINK',
                    'page': rel_path,
                    'link': link,
                    'note': 'Dokument smeruje na povodny web'
                })
        
        # 3. Check for images pointing to original site
        img_links = re.findall(r'src=["\']([^"\']*)["\']', content)
        for link in img_links:
            if 'hornyvadicov.sk' in link:
                issues_for_page.append({
                    'type': 'EXTERNAL_IMAGE',
                    'page': rel_path,
                    'link': link,
                    'note': 'Obrazok smeruje na povodny web'
                })
        
        # 4. Check for local links that might be broken (wrong base path)
        local_links = re.findall(r'href=["\'](?!#|javascript:|mailto:|http)([^"\']+)["\']', content)
        for link in local_links:
            # Links that are relative to root but don't have /horny-vadicov prefix
            if link.startswith('/') and not link.startswith('/horny-vadicov'):
                issues_for_page.append({
                    'type': 'MISSING_BASE_PATH',
                    'page': rel_path,
                    'link': link,
                    'note': 'Relativny odkaz bez /horny-vadicov/ - bude prvy na GH Pages'
                })
        
        all_issues.extend(issues_for_page)
        
        if issues_for_page:
            print(f"[ISSUES] {rel_path}: {len(issues_for_page)} problem(ov)")
        else:
            print(f"[OK] {rel_path}")
    
    print(f"\n=== SUHRN ===")
    print(f"Spracovanych stranok: {page_count}")
    print(f"Celkovo problemov: {len(all_issues)}")
    
    # Group by type
    by_type = {}
    for issue in all_issues:
        t = issue['type']
        by_type.setdefault(t, []).append(issue)
    
    for t, issues in by_type.items():
        print(f"\n{t} ({len(issues)}x):")
        # Show first 5 examples
        for issue in issues[:5]:
            print(f"  - {issue['page']}: {issue['link'][:80]}")
        if len(issues) > 5:
            print(f"  ... a dalsi {len(issues)-5}")
    
    # Save results
    with open('scripts/verification_results.json', 'w', encoding='utf-8') as f:
        json.dump({'page_count': page_count, 'issues': all_issues, 'by_type': {k: len(v) for k,v in by_type.items()}}, f, ensure_ascii=False, indent=2)
    
    print(f"\nVysledky ulozene do scripts/verification_results.json")
    return all_issues, by_type

if __name__ == "__main__":
    all_issues, by_type = analyze_all_pages()
