"""Povestio v3 - montaj pe scene: clipuri cu personaje, produs animat, motive numerotate,
subtitrări cu impact și CTA spre categorie.

Tipuri de scenă (spec["scene"][i]["tip"]):
  video     - clip cu personaje (src = URL sau cale), de la secunda `din`
  titlu     - hook mare pe ecran, produsul se ridică din blat
  popup     - produsul apare și se ascunde în blat (motivul 1)
  functii   - produsul cu etichete pe funcții (motivul 2)
  wireless  - telefonul se încarcă pe produs, cu inele de încărcare (motivul 3)
  cta       - finalul: categoria + domeniul
Fiecare scenă: voce (textul rostit), ecran (titlul scenei, *cuvinte evidențiate*), durata_min.
"""
import hashlib
import math
import os
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import muzica, voce

W, H, FPS = 1080, 1920, 30
RAD = Path(__file__).resolve().parent.parent
F_BOLD = str(RAD / "fonts" / "Inter-SemiBold.otf")
F_MED = str(RAD / "fonts" / "Inter-Medium.otf")
F_SERIF_I = str(RAD / "fonts" / "CrimsonText-Italic.ttf")
GALBEN = (255, 214, 74)
ALB = (255, 255, 255)


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def ease_out_back(x):
    x = max(0.0, min(1.0, x)); c1 = 1.4; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ---------------------------------------------------------------- text cu impact
def text_impact(text, size, maxw=940, culoare=ALB, accent=GALBEN, cutie=False, font=F_BOLD, spatiere=1.15, fundal=False):
    """Text bold, centrat, cu *cuvinte evidențiate* în culoarea de accent (sau pe fundal galben)."""
    f = ImageFont.truetype(font, size)
    tokens = []
    for parte in re.split(r"(\*[^*]+\*)", text):
        if not parte: continue
        hl = parte.startswith("*")
        cuv = parte.strip("*").split()
        # punctuația lipită de cuvântul anterior (ex: "*roșu*." -> "roșu.")
        while cuv and tokens and not parte.startswith((" ", "*")) and re.fullmatch(r"[.,!?;:…]+", cuv[0]):
            w0, h0 = tokens.pop(); tokens.append((w0 + cuv.pop(0), h0))
        for w in cuv:
            tokens.append((w, hl))
    linii, cur, lw = [], [], 0
    sp = f.getlength(" ")
    for w, hl in tokens:
        wl = f.getlength(w)
        if cur and lw + sp + wl > maxw:
            linii.append(cur); cur, lw = [], 0
        cur.append((w, hl, wl)); lw += (sp if len(cur) > 1 else 0) + wl
    if cur: linii.append(cur)
    lh = int(size * spatiere); pad = 14
    im = Image.new("RGBA", (W, lh * len(linii) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(linii):
        tot = sum(x[2] for x in ln) + sp * (len(ln) - 1)
        x = (W - tot) / 2; y = 20 + i * lh
        for w, hl, wl in ln:
            if hl and cutie:
                d.rounded_rectangle([x - pad, y - 4, x + wl + pad, y + size * 1.08], 12, fill=accent + (255,))
                d.text((x, y), w, font=f, fill=(20, 20, 20, 255))
            else:
                d.text((x, y), w, font=f, fill=(accent if hl else culoare) + (255,), stroke_width=max(2, size // 22),
                       stroke_fill=(0, 0, 0, 200))
            x += wl + sp
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    if fundal:
        bb = im.getbbox()
        if bb:
            ImageDraw.Draw(out).rounded_rectangle([bb[0] - 28, bb[1] - 18, bb[2] + 28, bb[3] + 22], 26, fill=(0, 0, 0, 165))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.6)))
    out.alpha_composite(sh); out.alpha_composite(im)
    return out


def put(fr, layer, y, a=1.0, dx=0, dy=0, scale=1.0):
    if a <= 0.01: return
    l = layer
    if scale != 1.0:
        l = l.resize((max(1, int(l.width * scale)), max(1, int(l.height * scale))), Image.LANCZOS)
    if a < 0.999:
        l = l.copy(); l.putalpha(l.split()[3].point(lambda v: int(v * a)))
    fr.alpha_composite(l, (int((W - l.width) / 2 + dx), int(y + dy)))


def pastila(text, size=40, fond=(18, 18, 22), culoare=ALB, punct=GALBEN):
    f = ImageFont.truetype(F_BOLD, size)
    tw = f.getlength(text); h = int(size * 1.9); w = int(tw + size * 2.2)
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + w, 10 + h], h // 2, fill=fond + (235,), outline=punct + (255,), width=3)
    d.ellipse([10 + size * 0.55, 10 + h / 2 - size * 0.22, 10 + size * 0.99, 10 + h / 2 + size * 0.22], fill=punct + (255,))
    d.text((10 + size * 1.35, 10 + (h - size * 1.2) / 2), text, font=f, fill=culoare + (255,))
    return im


# ---------------------------------------------------------------- fundal de studio
def _studio():
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(-1, 1, W)[None, :]
    r = np.sqrt((x * 0.9) ** 2 + ((y - 0.42) * 1.6) ** 2)
    base = np.clip(1 - r, 0, 1) ** 1.5
    c1 = np.array([46, 50, 58], float); c0 = np.array([10, 11, 14], float)
    img = c0 + (c1 - c0) * base[..., None]
    return img


STUDIO = _studio()
BLAT_Y = 1240  # linia blatului


def _blat():
    """Blat de piatră deschisă, în perspectivă, cu textură fină."""
    rng = np.random.default_rng(3)
    h = H - BLAT_Y
    yy = np.linspace(0, 1, h)[:, None]
    base = (188 - 40 * yy) * np.ones((h, W))
    noise = rng.normal(0, 1, (h // 4 + 1, W // 4 + 1))
    noise = np.kron(noise, np.ones((4, 4)))[:h, :W]
    vein = np.sin(np.linspace(0, 9, W)[None, :] + yy * 14 + noise * 0.4) * 6
    g = np.clip(base + noise * 4 + vein, 0, 255)
    arr = np.stack([g * 0.98, g * 0.99, g * 1.0], -1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    d.line([0, 1, W, 1], fill=(235, 235, 238, 255), width=3)  # muchia blatului
    sh = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([0, 0, W, 40], fill=(0, 0, 0, 60))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    return im


BLAT = _blat()


def fundal_studio(t, lumina=1.0):
    fr = Image.fromarray(np.clip(STUDIO * lumina, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # lumină caldă care se mișcă lent în spate
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    cx = W / 2 + 160 * math.sin(t * 0.35); cy = 640 + 40 * math.cos(t * 0.3)
    g.ellipse([cx - 420, cy - 420, cx + 420, cy + 420], fill=(255, 190, 110, 38))
    fr.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    fr.alpha_composite(BLAT, (0, BLAT_Y))
    return fr


# ---------------------------------------------------------------- produsul
class Produs:
    def __init__(self, cale_decupat, latime=1080, baza_frac=0.93):
        im = Image.open(cale_decupat).convert("RGBA")
        bb = im.getbbox(); im = im.crop(bb)
        s = latime / im.width
        self.im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        self.baza = int(self.im.height * baza_frac)  # unde atinge blatul (de sus)

    def punct(self, fx, fy, y_blat=BLAT_Y):
        """Coordonate absolute pentru un punct relativ din imagine (produs complet ridicat)."""
        return (W - self.im.width) / 2 + fx * self.im.width, y_blat - self.baza + fy * self.im.height

    def deseneaza(self, fr, ridicare=1.0, x=0, umbra=True, y_blat=BLAT_Y):
        """ridicare 0 = complet ascuns în blat, 1 = complet ieșit."""
        im = self.im; h = im.height
        y0 = y_blat - self.baza + int((1 - ridicare) * self.baza * 0.92)
        vizibil = max(0, y_blat - y0 + 20)
        if vizibil <= 0: return
        crop = im.crop((0, 0, im.width, min(h, vizibil)))
        if umbra:
            sh = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse([W / 2 - 360, 70, W / 2 + 360, 150], fill=(0, 0, 0, int(140 * ridicare)))
            fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)), (0, y_blat - 110))
        # gaura din blat
        go = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
        ImageDraw.Draw(go).ellipse([W / 2 - 250, 20, W / 2 + 250, 90], fill=(12, 12, 14, 255))
        fr.alpha_composite(go.filter(ImageFilter.GaussianBlur(2)), (0, y_blat - 45))
        fr.alpha_composite(crop, (int((W - im.width) / 2 + x), y0))


# ---------------------------------------------------------------- clipuri video
class Clip:
    def __init__(self, src, din, durata, cache):
        cale = self._local(src, cache)
        self.p = subprocess.Popen([ffmpeg_exe(), "-v", "error", "-ss", f"{din:.2f}", "-i", str(cale), "-t", f"{durata + 0.5:.2f}",
                                   "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.ultim = None

    @staticmethod
    def _local(src, cache):
        if not str(src).startswith("http"):
            p = Path(src)
            return p if p.is_absolute() else RAD / p
        dst = Path(cache) / ("clip_" + hashlib.sha1(src.encode()).hexdigest()[:16] + ".mp4")
        if not dst.exists():
            r = requests.get(src, timeout=180); r.raise_for_status(); dst.write_bytes(r.content)
        return dst

    def cadru(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            self.ultim = Image.frombuffer("RGB", (W, H), b, "raw", "RGB", 0, 1).convert("RGBA")
        return self.ultim.copy() if self.ultim else Image.new("RGBA", (W, H), (0, 0, 0, 255))

    def inchide(self):
        self.p.kill()


def vigneta_jos():
    g = np.linspace(0, 1, H)[:, None]
    a = (np.clip((g - 0.55) / 0.45, 0, 1) ** 1.4 * 200 + np.clip((0.18 - g) / 0.18, 0, 1) * 120)
    arr = np.zeros((H, W, 4), np.uint8); arr[..., 3] = np.repeat(a, W, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


VIG = vigneta_jos()


# ---------------------------------------------------------------- montaj
def randeaza(spec, brand, iesire, cache, ordine_voce=None):
    iesire, cache = Path(iesire), Path(cache)
    iesire.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
    nume = spec["id"]; sr = voce.SR
    acc = tuple(brand.get("culoare_accent_v3", GALBEN))

    # 1) vocea pe scene -> cronologie
    scene, audio, t, furn = [], [np.zeros(int(sr * 0.3), np.int16)], 0.3, set()
    for sc in spec["scene"]:
        v, f = voce.genereaza(sc["voce"], brand, cache, ordine_voce); furn.add(f)
        d = len(v) / sr; pauza = sc.get("pauza", 0.25)
        dur = max(d + pauza, sc.get("durata_min", 0))
        scene.append(dict(sc, start=t, end=t + dur, v_end=t + d))
        audio += [v, np.zeros(int(sr * (dur - d)), np.int16)]
        t += dur
    durata = t + 0.4
    vox = np.concatenate(audio); vox = np.pad(vox, (0, max(0, int(sr * durata) - len(vox))))

    # 2) resurse
    prod = {}
    for k, cale in spec.get("produs", {}).get("decupaje", {}).items():
        opt = {}
        if isinstance(cale, dict):
            opt = {x: cale[x] for x in ("latime", "baza_frac") if x in cale}; cale = cale["cale"]
        prod[k] = Produs(RAD / cale if not str(cale).startswith("/") else cale, **opt)
    erou = prod.get("erou")
    prod_cta = Produs(RAD / spec["produs"]["decupaje"]["erou"] if isinstance(spec["produs"]["decupaje"]["erou"], str)
                      else RAD / spec["produs"]["decupaje"]["erou"]["cale"], latime=760) if erou else None
    clipuri = {}
    for i, sc in enumerate(scene):
        if sc["tip"] == "video":
            clipuri[i] = Clip(sc["src"], sc.get("din", 0), sc["end"] - sc["start"], cache)
    ecrane = {i: text_impact(sc["ecran"], sc.get("marime_ecran", 76), cutie=True, accent=acc) for i, sc in enumerate(scene) if sc.get("ecran")}
    subt = {i: text_impact(sc.get("subtitlu", sc["voce"]), 50, maxw=880, accent=acc, font=F_BOLD, fundal=True) for i, sc in enumerate(scene)}
    etichete = {i: [pastila(e) for e in sc.get("etichete", [])] for i, sc in enumerate(scene)}
    nota = {i: text_impact(sc["nota"], 32, font=F_MED, culoare=(210, 210, 210)) for i, sc in enumerate(scene) if sc.get("nota")}
    cta = spec.get("cta", {})
    cta_l = {
        "sus": text_impact(cta.get("sus", "Vezi toate"), 64, font=F_MED),
        "categorie": text_impact("*" + cta.get("categorie", "") + "*", 96, cutie=True, accent=acc),
        "domeniu": text_impact(cta.get("domeniu", brand.get("domeniu_public", "")), 110),
        "slogan": text_impact(brand.get("slogan", ""), 40, font=F_MED, culoare=acc),
    }
    numar = {i: text_impact(str(sc["numar"]), 220, culoare=acc) for i, sc in enumerate(scene) if sc.get("numar")}

    def scena_la(t):
        for i, sc in enumerate(scene):
            if t < sc["end"]: return i, sc
        return len(scene) - 1, scene[-1]

    def cadru(t):
        i, sc = scena_la(t); lt = t - sc["start"]; D = sc["end"] - sc["start"]; tip = sc["tip"]
        if tip == "video":
            fr = clipuri[i].cadru()
            fr.alpha_composite(VIG)
            if i in ecrane:
                put(fr, ecrane[i], 230, ease(lt / 0.3), scale=0.9 + 0.1 * ease_out_back(lt / 0.45))
        elif tip == "cta":
            fr = fundal_studio(t, 0.85)
            if prod_cta: prod_cta.deseneaza(fr, ridicare=ease(lt / 0.9))
            put(fr, cta_l["sus"], 200, ease((lt - 0.1) / 0.4), dy=20 * (1 - ease(lt / 0.5)))
            put(fr, cta_l["categorie"], 300, ease((lt - 0.3) / 0.4), scale=0.85 + 0.15 * ease_out_back((lt - 0.3) / 0.5))
            put(fr, cta_l["domeniu"], 450, ease((lt - 0.6) / 0.4), dy=20 * (1 - ease((lt - 0.6) / 0.5)))
            put(fr, cta_l["slogan"], 590, ease((lt - 0.9) / 0.4))
        else:
            fr = fundal_studio(t)
            p = prod.get(sc.get("produs", "erou"))
            if tip == "titlu":
                if p: p.deseneaza(fr, ridicare=ease_out_back((lt - 0.4) / 1.2) if lt > 0.4 else 0.0)
            elif tip == "popup":
                # urcă, stă, coboară, urcă din nou
                ph = lt / max(D, 0.1)
                r = ease(ph / 0.22) if ph < 0.45 else (1 - ease((ph - 0.45) / 0.18) if ph < 0.68 else ease((ph - 0.72) / 0.2))
                if p: p.deseneaza(fr, ridicare=r)
            elif tip == "functii":
                if p: p.deseneaza(fr, ridicare=1.0)
                poz = sc.get("pozitii_etichete", [(-250, 760), (260, 860), (-260, 980), (250, 1080)])
                for k, (et, (x, y)) in enumerate(zip(etichete[i], poz)):
                    a = ease((lt - 0.35 - k * 0.45) / 0.3)
                    if a > 0:
                        e = et.copy(); e.putalpha(e.split()[3].point(lambda v, a=a: int(v * a)))
                        fr.alpha_composite(e, (int(W / 2 + x - e.width / 2), int(y - e.height / 2 + 15 * (1 - a))))
            elif tip == "wireless":
                p2 = prod.get(sc.get("produs", "wireless")) or p
                if p2: p2.deseneaza(fr, ridicare=1.0)
                # inele de încărcare care pornesc din centrul plăcii wireless
                cx, cy = p2.punct(*sc.get("placa", (0.5, 0.37))) if p2 else (W / 2, 820)
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
                for k in range(3):
                    ph = ((lt * 0.8) + k / 3) % 1.0
                    rr = 40 + 260 * ph; al = int(220 * (1 - ph))
                    d.ellipse([cx - rr, cy - rr * 0.32, cx + rr, cy + rr * 0.32], outline=(90, 255, 170, al), width=6)
                fr.alpha_composite(ov.filter(ImageFilter.GaussianBlur(1.5)))
            if i in numar:
                put(fr, numar[i], 70, ease(lt / 0.3), scale=0.75 * (0.8 + 0.2 * ease_out_back(lt / 0.4)))
            if i in ecrane:
                put(fr, ecrane[i], 230 if i not in numar else 300, ease((lt - 0.1) / 0.3),
                    dy=24 * (1 - ease(lt / 0.45)))
            if i in nota:
                put(fr, nota[i], 1262, ease((lt - 0.8) / 0.4))
        # subtitrarea vocii (jos)
        if tip != "cta":
            a = min(ease((t - sc["start"]) / 0.2), ease((sc["v_end"] + 0.25 - t) / 0.2))
            put(fr, subt[i], 1500 if tip != "video" else 1420, a)
        # tranziție scurtă între scene (flash alb discret)
        if lt < 0.12 and i > 0:
            fl = Image.new("RGBA", (W, H), (255, 255, 255, int(110 * (1 - lt / 0.12))))
            fr.alpha_composite(fl)
        if t > durata - 0.4:
            fr = Image.blend(fr, Image.new("RGBA", (W, H), (0, 0, 0, 255)), ease((t - (durata - 0.4)) / 0.4))
        return fr

    ff = ffmpeg_exe()
    tmp_v = cache / f"{nume}_v3.tmp.mp4"
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                             "-pix_fmt", "yuv420p", str(tmp_v)], stdin=subprocess.PIPE)
    nf = int(round(durata * FPS)); coperta = None
    t_cop = next((s["start"] + 1.6 for s in scene if s["tip"] == "titlu"), durata / 2)
    for k in range(nf):
        fr = cadru(k / FPS).convert("RGB")
        if coperta is None and k / FPS >= t_cop: coperta = fr.copy()
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    for c in clipuri.values(): c.inchide()
    if proc.wait() != 0: raise RuntimeError("ffmpeg a eșuat la video")

    mus = muzica.genereaza(durata, 44100)
    mus_wav = cache / f"{nume}_muzica.wav"; muzica.scrie_wav(mus_wav, mus, 44100)
    voc_wav = cache / f"{nume}_voce.wav"
    with wave.open(str(voc_wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(vox.tobytes())
    vol_m = brand.get("volum_muzica", 0.22) if furn - {"fara"} else 0.8
    mp4 = iesire / f"{nume}.mp4"; tmpf = iesire / f"{nume}.tmp.mp4"
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(tmp_v), "-i", str(voc_wav), "-i", str(mus_wav),
                        "-filter_complex", f"[1:a]aresample=44100[v];[2:a]volume={vol_m}[m];[v][m]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                        "-shortest", "-movflags", "+faststart", str(tmpf)])
    if r.returncode != 0: raise RuntimeError("ffmpeg a eșuat la sunet")
    os.replace(tmpf, mp4); tmp_v.unlink(missing_ok=True)
    jpg = iesire / f"{nume}.jpg"; (coperta or cadru(durata / 2).convert("RGB")).save(jpg, quality=90)

    def ts(x):
        ms = int(round(x * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    srt = iesire / f"{nume}.srt"
    srt.write_text("\n".join(f"{i}\n{ts(s['start'])} --> {ts(s['v_end'] + 0.2)}\n{s['voce']}\n" for i, s in enumerate(scene, 1)), encoding="utf-8")
    return {"mp4": mp4, "jpg": jpg, "srt": srt, "durata": round(durata, 1), "voce": sorted(furn), "tema": "v3"}
