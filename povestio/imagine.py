"""Pregateste poza de produs pentru planse: descarcare + decupare fundal alb.
Daca fundalul nu e alb (poza de ambient), produsul se pune pe un card alb rotunjit."""
import hashlib
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageChops


def descarca(url, cache):
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    f = cache / ("img_" + hashlib.sha1(url.encode()).hexdigest()[:16] + ".img")
    if not f.exists():
        u = url if "width=" in url else url + ("&" if "?" in url else "?") + "width=1400"
        import time
        for i, pauza in enumerate((5, 15, 30, 60, 0)):
            try:  # CDN-ul Shopify mai dă 502 temporar: reîncercăm, apoi și fără parametrul width
                uu = u if i < 3 else url
                req = urllib.request.Request(uu, headers={"User-Agent": "Mozilla/5.0 Povestio"})
                f.write_bytes(urllib.request.urlopen(req, timeout=40).read())
                break
            except Exception:
                if not pauza:
                    raise
                time.sleep(pauza)
    return f


def pregateste(url, cache, zona=None, punct=None):
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    out = cache / ("dec_" + hashlib.sha1(f"{url}|{zona}|{punct}".encode()).hexdigest()[:16] + ".png")
    if out.exists():
        return out
    im = Image.open(descarca(url, cache)).convert("RGB")
    if zona:  # [x0, y0, x1, y1] ca fractiuni din poza
        W0, H0 = im.size
        im = im.crop((int(zona[0] * W0), int(zona[1] * H0), int(zona[2] * W0), int(zona[3] * H0)))
    w, h = im.size
    puncte = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    alb = sum(1 for p in puncte if min(im.getpixel(p)) > 232)
    if alb >= 6:
        marcat = im.copy()
        for p in puncte:
            if min(marcat.getpixel(p)) > 232:
                ImageDraw.floodfill(marcat, p, (255, 0, 255), thresh=28)
        r, g, b = marcat.split()
        fundal = ImageChops.multiply(ImageChops.multiply(r.point(lambda v: 255 if v == 255 else 0),
                                                         g.point(lambda v: 255 if v == 0 else 0)),
                                     b.point(lambda v: 255 if v == 255 else 0))
        alfa = ImageChops.invert(fundal).filter(ImageFilter.MinFilter(3))
        if punct:  # pastreaza doar obiectul care contine punctul (scoate restul pachetului)
            bin_ = alfa.point(lambda v: 255 if v > 20 else 0)
            ImageDraw.floodfill(bin_, (int(punct[0] * w), int(punct[1] * h)), 128, thresh=0)
            alfa = bin_.point(lambda v: 255 if v == 128 else 0)
        alfa = alfa.filter(ImageFilter.GaussianBlur(1.2))
        rez = im.convert("RGBA"); rez.putalpha(alfa)
        bb = alfa.point(lambda v: 255 if v > 20 else 0).getbbox()
        rez = rez.crop(bb) if bb else rez
    else:
        # poza de ambient: card alb cu colturi rotunjite
        k = 900 / max(w, h); im = im.resize((int(w * k), int(h * k)), Image.LANCZOS)
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, *im.size], radius=48, fill=255)
        card = Image.new("RGBA", (im.width + 36, im.height + 36), (255, 255, 255, 255))
        mc = Image.new("L", card.size, 0); ImageDraw.Draw(mc).rounded_rectangle([0, 0, *card.size], radius=64, fill=255)
        card.putalpha(mc); card.paste(im, (18, 18), m); rez = card
    rez.save(out)
    return out
