import os
import re
import urllib.request
import ssl
import concurrent.futures
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

base_dir = os.path.join('public', 'obec-2', 'fotogaleria')
storage_dir = os.path.join('public', 'data', 'fotogaleria')
os.makedirs(storage_dir, exist_ok=True)

with open(os.path.join(base_dir, 'index.html'), 'r', encoding='utf-8') as f:
    gal_index_html = f.read()

# Find all album links
album_matches = re.findall(r'<a\s+href=["\'](https://www\.hornyvadicov\.sk/obec-2/fotogaleria/([^"\'?]+)(?:\?[^"\']*)?)["\']', gal_index_html)
print(f"Nájdených {len(album_matches)} albumov.")

header_part = gal_index_html.split('<div class="idsk-subpage-body editor_content">')[0]
footer_part = gal_index_html.split('</article>')[1]

def make_safe_slug(filename):
    clean = filename.replace('.html', '')
    id_m = re.search(r'-(\d+)sk$', clean)
    item_id = id_m.group(1) if id_m else ''
    short_slug = clean[:50].rstrip('-')
    if item_id and not short_slug.endswith(item_id):
        short_slug = f"{short_slug}-{item_id}"
    return short_slug

# Set of all images to download across all albums
all_photos_to_download = set()
album_data_list = []

print("Načítavam zoznam fotiek pre jednotlivé albumy...")
for full_url, filename in album_matches:
    short_slug = make_safe_slug(filename)
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            live_html = resp.read().decode('utf-8', errors='ignore')
            
        h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', live_html)
        title = h1_m.group(1).strip() if h1_m else short_slug
        
        date_m = re.search(r'<span class="event-info-value[^"]*event-date">(.*?)</span>', live_html)
        date_str = date_m.group(1).strip() if date_m else ''
        
        # Perex / description
        perex_m = re.search(r'<p class="event-perex">(.*?)</p>', live_html, re.DOTALL)
        perex_str = perex_m.group(1).strip() if perex_m else ''
        
        # Photo IDs
        raw_photos = re.findall(r'href=["\']/evt_image\.php\?img=(\d+)["\']', live_html)
        photo_ids = list(dict.fromkeys(raw_photos))
        
        for pid in photo_ids:
            all_photos_to_download.add(pid)
            
        album_data_list.append({
            'full_url': full_url,
            'short_slug': short_slug,
            'title': title,
            'date': date_str,
            'perex': perex_str,
            'photo_ids': photo_ids
        })
    except Exception as e:
        print(f"Chyba albumu {full_url}: {e}")

print(f"Spracovaných {len(album_data_list)} albumov.")
print(f"Spolu na stiahnutie: {len(all_photos_to_download)} fotiek.")

# Download all photos concurrently
def download_single_photo(pid):
    fname = f"img_{pid}.jpg"
    dest_path = os.path.join(storage_dir, fname)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return pid, True
    
    url = f"https://www.hornyvadicov.sk/evt_image.php?img={pid}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                data = resp.read()
            with open(dest_path, 'wb') as fp:
                fp.write(data)
            return pid, True
        except Exception:
            time.sleep(1)
    return pid, False

print("Sťahujem fotky (15 vlákien)...")
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    photo_results = list(executor.map(download_single_photo, all_photos_to_download))

dl_ok = sum(1 for pid, ok in photo_results if ok)
print(f"Úspešne stiahnutých {dl_ok} / {len(all_photos_to_download)} fotiek.")

# Generate album subpages
print("Generujem IDSK 3.0 stránky fotoalbumov...")
album_map = {}
for alb in album_data_list:
    short_slug = alb['short_slug']
    title = alb['title']
    date_str = alb['date']
    perex_str = alb['perex']
    photo_ids = alb['photo_ids']
    
    dest_dir = os.path.join(base_dir, short_slug)
    os.makedirs(dest_dir, exist_ok=True)
    dest_html = os.path.join(dest_dir, 'index.html')
    
    header_adj = header_part.replace('../../', '../../../')
    footer_adj = footer_part.replace('../../', '../../../')
    
    header_adj = re.sub(r'<title>.*?</title>', f'<title>{title} | Fotogaléria | Obec Horný Vadičov</title>', header_adj)
    header_adj = re.sub(r'<h1 class="idsk-subpage-content__title">.*?</h1>', f'<h1 class="idsk-subpage-content__title">{title}</h1>', header_adj)
    
    photos_grid = '<div class="row mt-4">\n'
    for pid in photo_ids:
        rel_img = f"../../../data/fotogaleria/img_{pid}.jpg"
        photos_grid += f'''  <div class="col-6 col-md-4 col-lg-3 mb-4">
    <div class="card h-100 shadow-sm border-0" style="overflow: hidden; border-radius: 8px;">
      <a href="{rel_img}" target="_blank" rel="noopener noreferrer" title="Zväčšiť fotografiu">
        <img src="{rel_img}" alt="{title}" class="img-fluid w-100" style="height: 180px; object-fit: cover; transition: transform 0.2s;" loading="lazy">
      </a>
    </div>
  </div>\n'''
    photos_grid += '</div>\n'
    
    album_page_html = f"""{header_adj}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-album-meta mb-4 text-muted" style="font-size: 0.95rem; color: #555; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem;">
              <span><strong>Dátum:</strong> {date_str}</span>
              <span class="ml-3">· <strong>Počet fotografií:</strong> {len(photo_ids)}</span>
            </div>
            
            {f'<p class="lead mb-4">{perex_str}</p>' if perex_str else ''}
            
            {photos_grid}

            <div class="mt-5 pt-3 border-top">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
                Späť do Fotogalérie
              </a>
            </div>
          </div>
        </article>
{footer_adj}"""
    
    with open(dest_html, 'w', encoding='utf-8') as out_fp:
        out_fp.write(album_page_html)
        
    album_map[alb['full_url']] = f"./{short_slug}/"

# Rewrite links in main fotogaleria index.html
new_gal_html = gal_index_html
for u, local_href in album_map.items():
    new_gal_html = new_gal_html.replace(f'href="{u}"', f'href="{local_href}"')
    new_gal_html = new_gal_html.replace(f"href='{u}'", f"href='{local_href}'")

with open(os.path.join(base_dir, 'index.html'), 'w', encoding='utf-8') as fp:
    fp.write(new_gal_html)

print(f"Všetkých {len(album_map)} albumov fotogalérie vygenerovaných a prepojených!")
