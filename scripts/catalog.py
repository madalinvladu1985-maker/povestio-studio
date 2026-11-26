"""Descarca catalogul public al magazinului (produse + colectii) in catalog/<brand>.json."""
import html, json, re, sys, time, urllib.request
from pathlib import Path

DOMENIU = sys.argv[1] if len(sys.argv) > 1 else "atentales.ro"
BRAND = sys.argv[2] if len(sys.argv) > 2 else "atentales"
UA = {"User-Agent": "Mozilla/5.0 Povestio-catalog"}


def get(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            err = e; time.sleep(3 + 4 * i)
    raise err


def text(h):
    h = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", h or "")
    return re.sub(r"\n\s*\n+", "\n", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def toate(path, cheie):
    out, p = [], 1
    while True:
        d = get(f"https://{DOMENIU}{path}{'&' if '?' in path else '?'}limit=250&page={p}")[cheie]
        if not d: return out
        out += d; p += 1


colectii = [c for c in toate("/collections.json", "collections") if c.get("products_count", 1)]
produse = {p["handle"]: p for p in toate("/products.json", "products")}
membri = {}
for c in colectii:
    try:
        for p in toate(f"/collections/{c['handle']}/products.json", "products"):
            membri.setdefault(p["handle"], []).append(c["handle"])
    except Exception as e:
        print("colectie sarita:", c["handle"], e)
    time.sleep(0.6)
cat = {"domeniu": DOMENIU, "actualizat": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "colectii": [{"handle": c["handle"], "titlu": c["title"], "produse": c.get("products_count")} for c in colectii],
       "produse": [{
           "handle": h, "titlu": p["title"], "brand": p.get("vendor"), "tip": p.get("product_type"),
           "taguri": p.get("tags"), "colectii": membri.get(h, []),
           "disponibil": any(v.get("available") for v in p.get("variants", [])),
           "descriere": text(p.get("body_html"))[:4000],
           "imagini": [i["src"] for i in p.get("images", [])][:8],
           "url": f"https://{DOMENIU}/products/{h}"} for h, p in produse.items()]}
Path("catalog").mkdir(exist_ok=True)
Path(f"catalog/{BRAND}.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(cat["colectii"]), "colectii,", len(cat["produse"]), "produse")
