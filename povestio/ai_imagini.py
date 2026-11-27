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


def _acopera(im, W=1080, H=1920):
    """acopera exact 1080x1920 (taie marginile daca raportul difera)"""
    k = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * k + 0.5), int(im.height * k + 0.5)), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x0, y0, x0 + W, y0 + H))


def prompt_scena(sc, personaj_desc):
    p = sc.get("ilustratie", "")
    if sc.get("ilustratie_personaj", True) and personaj_desc:
        p = f"{p}. Main character: {personaj_desc}"
    return f"{p}. {STIL}"


def _gemini(prompt, cfg, referinta=None):
    """Gemini API (Nano Banana), plătit din creditele Google Cloud incluse în Google AI Pro."""
    import base64
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    model = cfg.get("model", "gemini-2.5-flash-image")
    parts = []
    if referinta and Path(referinta).exists():
        parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(Path(referinta).read_bytes()).decode()}})
        prompt = ("Use the attached image only as the reference for the main character: keep the same person, face, hair, "
                  "clothes and the same illustration style. New scene: " + prompt)
    parts.append({"text": prompt})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "9:16"}}}
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                      params={"key": key}, json=body, timeout=180)
    if r.status_code != 200:
        print(f"[ai_imagini] gemini {model} {r.status_code}: {r.text[:300]}")
        return None
    for c in r.json().get("candidates", []):
        for part in c.get("content", {}).get("parts", []):
            d = part.get("inline_data") or part.get("inlineData")
            if d and d.get("data"):
                return Image.open(io.BytesIO(base64.b64decode(d["data"]))).convert("RGB")
    print("[ai_imagini] gemini: raspuns fara imagine")
    return None


def genereaza(sc, cfg, cache_dir, personaj_desc="", referinta=None):
    """Intoarce calea unei imagini 1080x1920 sau None."""
    if sc.get("ilustratie_url"):  # ilustratie deja generata (ex. demo), doar o descarcam
        out = _cache(cache_dir, "url|" + sc["ilustratie_url"])
        if not out.exists():
            try:
                r = requests.get(sc["ilustratie_url"], timeout=90)
                r.raise_for_status()
                _acopera(Image.open(io.BytesIO(r.content)).convert("RGB")).save(out)
            except Exception as e:
                print(f"[ai_imagini] descarcare esuata: {e}")
                return None
        return out
    if not sc.get("ilustratie"):
        return None
    prompt = prompt_scena(sc, personaj_desc)
    if cfg.get("furnizor") == "gemini":
        out = _cache(cache_dir, f"gemini|{cfg.get('model')}|{prompt}|{referinta}")
        if out.exists():
            return out
        try:
            im = _gemini(prompt, cfg, referinta if cfg.get("referinta_personaj", True) else None)
        except Exception as e:
            print(f"[ai_imagini] gemini eroare: {e}"); im = None
        if im is None:
            return None
        _acopera(im).save(out)
        return out
    key = os.environ.get("FAL_KEY")
    model = cfg.get("model", "fal-ai/flux/schnell")
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
    _acopera(im).save(out)
    jurnal = Path(cache_dir) / "ai_imagini_jurnal.jsonl"
    with jurnal.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"model": model, "fisier": out.name}) + "\n")
    return out
