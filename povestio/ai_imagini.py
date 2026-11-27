"""Povestio - ilustratii AI pentru fundalul scenelor (fal.ai, platit pe consum).

Produsul NU e generat de AI: poza reala se pune peste ilustratie in render4.
Fara FAL_KEY sau la orice eroare se intoarce None, iar scena se deseneaza ca inainte.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path

import requests
from PIL import Image

STIL = ("flat vector editorial illustration, warm cozy palette (cream, teal, coral, mustard), soft shadows, "
        "clean shapes, vertical 9:16 composition, the top third of the image is a calm plain light cream wall "
        "with nothing in it (space for a title), no text, no letters, no logos, no brand names, no watermark")


def _cache(cache_dir, cheie):
    return Path(cache_dir) / ("ai_" + hashlib.sha1(cheie.encode("utf-8")).hexdigest()[:20] + ".png")


def prompt_scena(sc, personaj_desc):
    p = sc.get("ilustratie", "")
    if sc.get("ilustratie_personaj", True) and personaj_desc:
        p = f"{p}. Main character: {personaj_desc}"
    return f"{p}. {STIL}"


def genereaza(sc, cfg, cache_dir, personaj_desc=""):
    """Intoarce calea unei imagini 1080x1920 sau None."""
    if not sc.get("ilustratie"):
        return None
    key = os.environ.get("FAL_KEY")
    model = cfg.get("model", "fal-ai/flux/schnell")
    prompt = prompt_scena(sc, personaj_desc)
    out = _cache(cache_dir, f"{model}|{prompt}|{cfg.get('seed', 7)}")
    if out.exists():
        return out
    if not key:
        print("[ai_imagini] FAL_KEY lipseste - folosesc desenul obisnuit")
        return None
    body = {"prompt": prompt, "image_size": {"width": 768, "height": 1360}, "num_images": 1,
            "seed": cfg.get("seed", 7), "enable_safety_checker": True}
    body.update(cfg.get("parametri", {}))
    try:
        r = requests.post(f"https://fal.run/{model}", json=body, timeout=180,
                          headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
        if r.status_code != 200:
            print(f"[ai_imagini] {model} {r.status_code}: {r.text[:300]}")
            return None
        url = r.json()["images"][0]["url"]
        im = Image.open(io.BytesIO(requests.get(url, timeout=90).content)).convert("RGB")
    except Exception as e:  # reteaua sau formatul raspunsului: revenim la desen
        print(f"[ai_imagini] eroare: {e}")
        return None
    # acopera exact 1080x1920 (taie marginile daca raportul difera)
    W, H = 1080, 1920
    k = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * k + 0.5), int(im.height * k + 0.5)), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    im.crop((x0, y0, x0 + W, y0 + H)).save(out)
    jurnal = Path(cache_dir) / "ai_imagini_jurnal.jsonl"
    with jurnal.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"model": model, "fisier": out.name}) + "\n")
    return out
