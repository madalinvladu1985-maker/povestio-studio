"""Povestio - imaginile produsului.
Preferat: linkuri directe CDN Shopify în spec (produs.imagini_url) - merg și când magazinul e protejat cu parolă.
Rezervă: pagina publică /products/<handle>.json (doar pentru magazine deschise)."""
import hashlib
import io
from pathlib import Path

import requests
from PIL import Image


def _descarca(src, dst):
    src += ("&" if "?" in src else "?") + "width=1100"
    r = requests.get(src, timeout=60)
    r.raise_for_status()
    Image.open(io.BytesIO(r.content)).convert("RGB").save(dst)


def imagini_produs(magazin, produs, cache_dir):
    cache_dir = Path(cache_dir)
    urls = produs.get("imagini_url") or []
    if urls:
        out = []
        for u in urls:
            dst = cache_dir / ("img_" + hashlib.sha1(u.encode()).hexdigest()[:16] + ".png")
            if not dst.exists():
                _descarca(u, dst)
            out.append(dst)
        return out
    handle, indici = produs["handle"], produs.get("imagini", [1, 2, 3])
    cai = [cache_dir / f"{handle}_{k}.png" for k in indici]
    if all(p.exists() for p in cai):
        return cai
    r = requests.get(f"https://{magazin}/products/{handle}.json", timeout=30)
    r.raise_for_status()
    imgs = [i["src"] for i in r.json()["product"]["images"]]
    out = []
    for k, dst in zip(indici, cai):
        if 1 <= k <= len(imgs):
            if not dst.exists():
                _descarca(imgs[k - 1], dst)
            out.append(dst)
    if not out:
        raise RuntimeError(f"Nicio imagine găsită pentru {handle}")
    return out
