"""Povestio - imaginile produsului, direct din pagina publică Shopify (/products/<handle>.json)."""
import io
from pathlib import Path

import requests
from PIL import Image


def imagini_produs(magazin, handle, indici, cache_dir):
    cache_dir = Path(cache_dir)
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
                src = imgs[k - 1]
                src += ("&" if "?" in src else "?") + "width=1100"
                Image.open(io.BytesIO(requests.get(src, timeout=60).content)).convert("RGB").save(dst)
            out.append(dst)
    if not out:
        raise RuntimeError(f"Nicio imagine găsită pentru {handle}")
    return out
