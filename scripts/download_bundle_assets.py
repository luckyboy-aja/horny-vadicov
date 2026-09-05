import os
import requests

assets = [
    ('/bundles/ocelot/images/multipage_sk.png', 'public/data/cache_images/multipage_sk.png'),
    ('/bundles/ocelot/images/qr_android_sk.png', 'public/data/cache_images/qr_android_sk.png'),
    ('/bundles/ocelot/images/qr_ios_sk.png', 'public/data/cache_images/qr_ios_sk.png'),
    ('/bundles/ocelot/images/qr_huawei_sk.png', 'public/data/cache_images/qr_huawei_sk.png'),
    ('/bundles/ocelot/images/banner_logo_sk.png', 'public/data/cache_images/banner_logo_sk.png'),
    ('/data/headerfooter/footer_texts/textsk3_1.png', 'public/data/cache_images/textsk3_1.png'),
    ('/data/editor/mini12sk_2.jpg', 'public/data/cache_images/mini12sk_2.jpg'),
    ('/data/editor/mini12sk_1.png', 'public/data/cache_images/mini12sk_1.png'),
    ('/data/editor/mini12sk_1.pdf', 'public/data/file_storage/mini12sk_1.pdf'),
]

os.makedirs('public/data/cache_images', exist_ok=True)
os.makedirs('public/data/file_storage', exist_ok=True)

for remote_path, local_path in assets:
    url = f"https://www.hornyvadicov.sk{remote_path}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(r.content)
            print(f"Downloaded {url} -> {local_path} ({len(r.content)} bytes)")
        else:
            print(f"Status {r.status_code} for {url}")
    except Exception as e:
        print(f"Error {url}: {e}")

# Also copy banner_logo_sk.png as evt_unknown.jpg as safe fallback if any page still references it
if os.path.exists('public/data/cache_images/banner_logo_sk.png'):
    with open('public/data/cache_images/banner_logo_sk.png', 'rb') as f:
        content = f.read()
    with open('public/data/cache_images/evt_unknown.jpg', 'wb') as f:
        f.write(content)
    print("Created fallback public/data/cache_images/evt_unknown.jpg")
