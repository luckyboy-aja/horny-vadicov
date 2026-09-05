import os
import re
import urllib.parse
from pathlib import Path

def full_disk_check():
    public_dir = Path("public")
    html_files = list(public_dir.rglob("index.html"))
    root_index = Path("index.html")
    
    print(f"Kontrolujem {len(html_files)} podstranok v public/ + root index.html...")
    
    missing_files = []
    external_old_domain = []
    total_refs = 0
    
    all_pages = html_files + ([root_index] if root_index.exists() else [])
    
    for html_path in all_pages:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        refs = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', content)
        for ref in refs:
            if ref.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            if ref.startswith("http://") or ref.startswith("https://"):
                if "hornyvadicov.sk" in ref:
                    external_old_domain.append((str(html_path), ref))
                continue
                
            total_refs += 1
            clean_ref = ref.split("?")[0].split("#")[0]
            clean_ref = urllib.parse.unquote(clean_ref)
            if not clean_ref:
                continue
                
            # For root index.html, paths starting with ./ or / resolve inside public/
            if html_path == root_index:
                stripped = clean_ref.lstrip('./').lstrip('/')
                target_path = (public_dir / stripped).resolve()
            else:
                target_path = (html_path.parent / clean_ref).resolve()
                
            if not target_path.exists() and not (target_path / "index.html").exists():
                missing_files.append((str(html_path), ref, str(target_path)))
                
    print(f"\n==========================================")
    print(f"Celkovo skontrolovaných interných odkazov a médií: {total_refs}")
    print(f"Odkazy na starý web (hornyvadicov.sk): {len(external_old_domain)}")
    print(f"Nenájdené / chybné lokálne súbory: {len(missing_files)}")
    print(f"==========================================")
    
    if external_old_domain:
        print("\nCHYBA - Nájdené odkazy na starý web:")
        for p, u in external_old_domain[:10]:
            print(f"  {p} -> {u}")
            
    if missing_files:
        print(f"\nNájdené chýbajúce súbory ({len(missing_files)}):")
        for p, r, t in missing_files[:25]:
            print(f"  {p} -> {r}\n    (cesta: {t})")
    else:
        print("\n100% PERFEKTNÉ: VŠETKY ODKAZY, OBRÁZKY, PRÍLOHY A DOKUMENTY EXISTUJÚ NA DISKU!")

if __name__ == "__main__":
    full_disk_check()
