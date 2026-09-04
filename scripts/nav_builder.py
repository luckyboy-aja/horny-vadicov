"""
nav_builder.py
Definuje presnú štruktúru hlavnej navigácie a generuje IDSK 3.0 mega-menu ribbon
zhodný 1:1 s originálnym sídlom www.hornyvadicov.sk
"""

MENUS = [
    {
        "title": "Obec",
        "href": "obec-2/o-obci/",
        "match_prefix": "obec-2",
        "items": [
            {"text": "O obci", "href": "obec-2/o-obci/"},
            {"text": "História", "href": "obec-2/historia/"},
            {"text": "Symboly obce", "href": "obec-2/symboly-obce/"},
            {"text": "Aktuality", "href": "obec-2/aktuality/"},
            {"text": "Tlačivá", "href": "obec-2/tlaciva/"},
            {"text": "Kalendár podujatí", "href": "obec-2/kalendar-podujati/"},
            {"text": "Fotogaléria", "href": "obec-2/fotogaleria/"},
            {"text": "Organizácie v obci", "href": "obec-2/organizacie-v-obci/"},
            {"text": "Cintorín", "href": "obec-2/cintorin/dokumenty/"},
            {"text": "Civilná ochrana", "href": "obec-2/civilna-ochrana/"},
            {"text": "Požiarna ochrana", "href": "obec-2/poziarna-ochrana/"},
            {"text": "Odpadové hospodárstvo", "href": "obec-2/odpadove-hospodarstvo-1/"},
            {"text": "Šport", "href": "obec-2/sport/"},
            {"text": "Knižnica", "href": "obec-2/kniznica/"},
            {"text": "Bytové domy A651, B652", "href": "obec-2/bytove-domy-a651-b652/"}
        ]
    },
    {
        "title": "Samospráva",
        "href": "samosprava/starostka-obce/",
        "match_prefix": "samosprava",
        "items": [
            {"text": "Starostka obce", "href": "samosprava/starostka-obce/"},
            {"text": "Obecné zastupiteľstvo", "href": "samosprava/obecne-zastupitelstvo/poslanci-oz/"},
            {"text": "Komisie OZ", "href": "samosprava/komisie-oz/ekonomicka-komisia/"},
            {"text": "Hlavný kontrolór obce", "href": "samosprava/hlavny-kontrolor-obce/"},
            {"text": "VZN", "href": "samosprava/vzn/"},
            {"text": "Smernice", "href": "samosprava/smernice/"},
            {"text": "GDPR – Infozákon", "href": "samosprava/gdpr-infozakon/"},
            {"text": "Dokumenty obce", "href": "samosprava/dokumenty-obce/"}
        ]
    },
    {
        "title": "Zverejňovanie",
        "href": "zverejnovanie/uradna-tabula-1/",
        "match_prefix": "zverejnovanie",
        "items": [
            {"text": "Úradná tabuľa", "href": "zverejnovanie/uradna-tabula-1/"},
            {"text": "Zmluvy, Faktúry, Objednávky", "href": "zverejnovanie/zmluvy-faktury-objednavky/"},
            {"text": "Verejné obstarávanie", "href": "zverejnovanie/verejne-obstaravanie/profil/"},
            {"text": "Hospodárenie", "href": "zverejnovanie/hospodarenie/rozpocet/"},
            {"text": "Dobropisy", "href": "zverejnovanie/dobropisy/"},
            {"text": "Ostatné dokumenty", "href": "zverejnovanie/ostatne-dokumenty/"},
            {"text": "Projekty", "href": "zverejnovanie/projekty/"}
        ]
    },
    {
        "title": "Voľby a Referendum",
        "href": "volby-a-referendum/",
        "match_prefix": "volby-a-referendum",
        "items": []
    },
    {
        "title": "Územný plán",
        "href": "uzemny-plan/",
        "match_prefix": "uzemny-plan",
        "items": [
            {"text": "1. Prieskumy a rozbory", "href": "uzemny-plan/1-prieskumy-a-rozbory/"}
        ]
    },
    {
        "title": "Kontakt",
        "href": "kontakt/uradne-hodiny/",
        "match_prefix": "kontakt",
        "items": [
            {"text": "Úradné hodiny", "href": "kontakt/uradne-hodiny/"},
            {"text": "Zamestnanci OcÚ", "href": "kontakt/zamestnanci-ocu/"},
            {"text": "Odkazy", "href": "kontakt/odkazy/"}
        ]
    },
    {
        "title": "Projekty",
        "href": "projekty/",
        "match_prefix": "projekty",
        "items": [
            {"text": "Zníženie energetickej náročnosti Materskej škôlky Horný Vadičov", "href": "projekty/znizenie-energetickej-narocnosti-materskej-skolky-horny-vadicov/"},
            {"text": "Stavebné úpravy materskej školy v Hornom Vadičove č. 515", "href": "projekty/stavebne-upravy-materskej-skoly-v-hornom-vadicove-c-515/"},
            {"text": "Národný projekt Podpora opatrovateľskej služby", "href": "projekty/narodny-projekt-podpora-opatrovatelskej-sluzby/"},
            {"text": "Rekonštrukcia športového ihriska pri ZŠ v obci Horný Vadičov", "href": "projekty/rekonstrukcia-sportoveho-ihriska-pri-zs-v-obci-horny-vadicov/"},
            {"text": "Rozhýbme seniorov v obci Horný Vadičov - Olympiáda starších", "href": "projekty/rozhybme-seniorov-v-obci-horny-vadicov-olympiada-starsich/"},
            {"text": "Zníženie energetickej náročnosti Kultúrno-informačného centra s knižnicou Horný Vadičov č. 798", "href": "projekty/znizenie-energetickej-narocnosti-kulturno-informacneho-centra-s-kniznicou-horny-vadicov-c-798/"},
            {"text": "Zníženie energetickej náročnosti objektu Obecného úradu Horný Vadičov", "href": "projekty/znizenie-energetickej-narocnosti-objektu-obecneho-uradu-horny-vadicov/"}
        ]
    }
]

def render_navigation_markup(root_rel, current_path=""):
    """
    Vygeneruje prístupné IDSK 3.0 mega-menu ribbon s presnou štruktúrou 1:1.
    """
    curr_clean = current_path.strip('/')
    lines = []
    lines.append('        <ul class="idsk-nav__list" id="navList">')
    
    for m in MENUS:
        is_active = False
        if curr_clean:
            if m["match_prefix"] and curr_clean.startswith(m["match_prefix"]):
                is_active = True
        elif not curr_clean and m["title"] == "Obec":
            is_active = True
            
        active_cls = " is-active" if is_active else ""
        cat_url = root_rel + m["href"]
        
        if m["items"]:
            lines.append('          <li class="idsk-nav__item">')
            lines.append(f'            <a href="{cat_url}" class="idsk-nav__link{active_cls}">')
            lines.append(f'              <span>{m["title"]}</span>')
            lines.append('              <svg class="idsk-nav__arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 10l5 5 5-5z"/></svg>')
            lines.append('            </a>')
            lines.append('            <div class="idsk-nav__dropdown">')
            lines.append('              <div class="idsk-nav__dropdown-container">')
            for item in m["items"]:
                item_url = root_rel + item["href"]
                item_active = ""
                item_clean = item["href"].strip('/')
                if curr_clean and item_clean in curr_clean:
                    item_active = " is-active"
                lines.append(f'                <a href="{item_url}" class="idsk-nav__dropdown-link{item_active}">{item["text"]}</a>')
            lines.append('              </div>')
            lines.append('            </div>')
            lines.append('          </li>')
        else:
            lines.append('          <li class="idsk-nav__item">')
            lines.append(f'            <a href="{cat_url}" class="idsk-nav__link{active_cls}">')
            lines.append(f'              <span>{m["title"]}</span>')
            lines.append('            </a>')
            lines.append('          </li>')
            
    lines.append('        </ul>')
    return '\n'.join(lines)

if __name__ == "__main__":
    print(render_navigation_markup("./", "zverejnovanie/uradna-tabula-1/stavebne-konanie/"))
