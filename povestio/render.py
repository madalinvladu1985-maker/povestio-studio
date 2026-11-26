"""Povestio - motorul de montaj: atmosferă -> produs -> CTA, voce sincronizată, muzică originală."""
import math
import os
import random
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import muzica, voce
from .shopify import imagini_produs
from .teme import BOKEH, TEME

W, H, FPS = 1080, 1920, 30
RADACINA = Path(__file__).resolve().parent.parent
FONTS = RADACINA / "fonts"
F_SERIF_I = str(FONTS / "CrimsonText-Italic.ttf")
F_SERIF = str(FONTS / "CrimsonText-SemiBold.ttf")
F_SANS = str(FONTS / "Inter-Medium.otf")
F_SANS_SB = str(FONTS / "Inter-SemiBold.otf")


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def env(t, a, b, fin=0.6, fout=0.5):
    if t < a or t > b: return 0.0
    return min(ease((t - a) / fin), ease((b - t) / fout))


def text_layer(lines, font_path, size, color=(255, 246, 232), spacing=1.18, maxw=900):
    font = ImageFont.truetype(font_path, size)
    out = []
    for ln in lines:
        cur = ""
        for w_ in ln.split(" "):
            test = (cur + " " + w_).strip()
            if font.getlength(test) <= maxw: cur = test
            else: out.append(cur); cur = w_
        out.append(cur)
    lh = int(size * spacing)
    im = Image.new("RGBA", (W, lh * len(out) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(out):
        d.text(((W - font.getlength(ln)) / 2, 20 + i * lh), ln, font=font, fill=tuple(color) + (255,))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.8)))
    base = Image.new("RGBA", im.size, (0, 0, 0, 0)); base.alpha_composite(sh); base.alpha_composite(im)
    return base


def put(frame, layer, y, alpha, dy=0):
    if alpha <= 0.01: return
    l = layer
    if alpha < 0.999:
        l = layer.copy(); l.putalpha(layer.split()[3].point(lambda v: int(v * alpha)))
    frame.alpha_composite(l, (0, int(y + dy)))


def _grad(c):
    top, mid, bot = [np.array(x, float) for x in c]
    y = np.linspace(0, 1, H)[:, None]
    g = np.where(y < 0.55, top + (mid - top) * (y / 0.55), mid + (bot - mid) * ((y - 0.55) / 0.45))
    return np.repeat(g[:, None, :], W, axis=1).reshape(H, W, 3)


_yy, _xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1 - 0.55 * (((_xx - W / 2) / (W * 0.75)) ** 2 + ((_yy - H * 0.45) / (H * 0.7)) ** 2), 0.35, 1)[..., None]
del _yy, _xx


class Fundal:
    """Fundal animat al temei; folosește un clip b-roll dacă există în broll/<tema>/."""

    def __init__(self, tema, seed, durata):
        self.T = TEME.get(tema, TEME["iarna_seara"])
        self.rng = random.Random(seed)
        self.g_rece, self.g_cald = _grad(self.T["grad_rece"]), _grad(self.T["grad_cald"])
        pal = BOKEH[self.T.get("bokeh", "cald")]
        self.bokeh = []
        for _ in range(24):
            r = self.rng.uniform(28, 95); s = int(r * 2 + 8)
            im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); c = s / 2
            ImageDraw.Draw(im).ellipse([c - r, c - r, c + r, c + r], fill=self.rng.choice(pal) + (255,))
            self.bokeh.append(dict(x=self.rng.uniform(-50, W + 50), y=self.rng.uniform(150, H * 0.75),
                                   spr=im.filter(ImageFilter.GaussianBlur(r * 0.09 + 1.5)),
                                   ph=self.rng.uniform(0, 6.28), sp=self.rng.uniform(0.15, 0.5),
                                   a=self.rng.uniform(0.25, 0.6), dx=self.rng.uniform(-6, 6)))
        self.part = [dict(x=self.rng.uniform(0, W), y=self.rng.uniform(-H, H), z=self.rng.random(),
                          ph=self.rng.uniform(0, 6.28)) for _ in range(220)]
        self._fl = {}
        self.fereastra = self._fereastra() if self.T.get("fereastra") else None
        self.ceata = self._ceata() if self.T.get("particule") == "ceata" else None
        self.raze = self._raze() if self.T.get("raze") else None
        self.broll = self._broll(tema, durata)

    # --- b-roll ---------------------------------------------------------------
    def _broll(self, tema, durata):
        d = RADACINA / "broll" / tema
        clipuri = sorted(d.glob("*.mp4")) if d.exists() else []
        if not clipuri:
            return None
        src = self.rng.choice(clipuri)
        proc = subprocess.Popen([ffmpeg_exe(), "-v", "error", "-stream_loop", "-1", "-i", str(src),
                                 "-t", f"{durata + 1:.2f}", "-vf",
                                 f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self._ultim = None
        return proc

    def _cadru_broll(self):
        b = self.broll.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            self._ultim = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        return self._ultim

    # --- elemente desenate ------------------------------------------------------
    def _fereastra(self):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = (18, 14, 16, 235)
        for box in ([0, 0, W, 90], [0, H - 260, W, H], [0, 0, 70, H], [W - 70, 0, W, H],
                    [W / 2 - 22, 0, W / 2 + 22, H], [0, H * 0.42 - 20, W, H * 0.42 + 20]):
            d.rectangle(box, fill=c)
        return im.filter(ImageFilter.GaussianBlur(2))

    def _ceata(self):
        im = Image.new("RGBA", (W * 2, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for i in range(14):
            y = self.rng.uniform(H * 0.35, H * 0.85); x = self.rng.uniform(0, W * 2)
            d.ellipse([x - 500, y - 70, x + 500, y + 70], fill=(235, 238, 235, 70))
        return im.filter(ImageFilter.GaussianBlur(45))

    def _raze(self):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for i in range(5):
            x = 150 + i * 170
            d.polygon([(x, -50), (x + 90, -50), (x + 520, H), (x + 300, H)], fill=(255, 236, 200, 26))
        return im.filter(ImageFilter.GaussianBlur(40))

    def _flake(self, r):
        r = max(1, int(r))
        if r not in self._fl:
            s = r * 4 + 4
            im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
            ImageDraw.Draw(im).ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r], fill=(255, 255, 255, 230))
            self._fl[r] = im.filter(ImageFilter.GaussianBlur(max(0.6, r * 0.35)))
        return self._fl[r]

    def _ghirlanda(self, t, alpha):
        pal = BOKEH["cald"]
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        pts = [(i / 60 * (W + 200) - 100, 330 + 120 * math.sin(i / 60 * math.pi) + 6 * math.sin(t * 1.3 + i * 0.3)) for i in range(61)]
        d.line(pts, fill=(30, 22, 18, int(200 * alpha)), width=3)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
        for i in range(0, 61, 4):
            x, y = pts[i]; tw = 0.65 + 0.35 * math.sin(t * 2.2 + i); c = pal[i % len(pal)]
            g.ellipse([x - 26, y - 6, x + 26, y + 46], fill=c + (int(120 * tw * alpha),))
            d.ellipse([x - 9, y + 6, x + 9, y + 30], fill=c + (int(255 * alpha),))
        glow = glow.filter(ImageFilter.GaussianBlur(18)); glow.alpha_composite(im)
        return glow

    # --- cadru ----------------------------------------------------------------
    def cadru(self, t, caldura, part_amt, fereastra=0.0, ghirlanda=0.0, intunecare=0.0):
        if self.broll is not None:
            arr = self._cadru_broll()
            base = arr.astype(float) * (0.62 - 0.25 * intunecare) if arr is not None else self.g_rece
            fr = Image.fromarray(np.clip(base * VIG, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        else:
            g = self.g_rece * (1 - caldura) + self.g_cald * caldura
            fr = Image.fromarray(np.clip(g * VIG * (1 - intunecare), 0, 255).astype(np.uint8), "RGB").convert("RGBA")
            if self.raze is not None:
                fr.alpha_composite(self.raze)
            for b in self.bokeh:
                a = b["a"] * (0.7 + 0.3 * math.sin(t * b["sp"] * 2 + b["ph"])) * (0.55 + 0.45 * caldura) * (1 - intunecare)
                if a > 0.02:
                    s = b["spr"]; l = s.copy(); l.putalpha(s.split()[3].point(lambda v, a=a: int(v * a)))
                    x = b["x"] + b["dx"] * t + 14 * math.sin(t * b["sp"] + b["ph"]); y = b["y"] - 6 * t * b["sp"]
                    fr.alpha_composite(l, (int(x - s.width / 2), int(y - s.height / 2)))
            if self.ceata is not None:
                off = int((t * 25) % W)
                fr.alpha_composite(self.ceata.crop((off, 0, off + W, H)))
        if ghirlanda > 0.01 and self.T.get("ghirlanda"):
            fr.alpha_composite(self._ghirlanda(t, ghirlanda))
        tip = self.T.get("particule")
        if tip in ("zapada", "praf"):
            for f in self.part:
                if f["z"] > part_amt: continue
                z = f["z"]
                if tip == "zapada":
                    r = 1.5 + 6.5 * (1 - z) ** 1.6; y = (f["y"] + (60 + 220 * (1 - z)) * t) % (H + 100) - 50
                    x = (f["x"] + 30 * math.sin(t * 0.8 + f["ph"]) + 15 * t) % W; a = 0.35 + 0.6 * (1 - z)
                else:
                    if z > 0.45: continue
                    r = 1 + 3 * (1 - z); y = (f["y"] - (8 + 20 * (1 - z)) * t) % (H + 100) - 50
                    x = (f["x"] + 40 * math.sin(t * 0.3 + f["ph"])) % W; a = 0.25 + 0.4 * (1 - z)
                fl = self._flake(r)
                l = fl.copy(); l.putalpha(fl.split()[3].point(lambda v, a=a: int(v * a)))
                fr.alpha_composite(l, (int(x - fl.width / 2), int(y - fl.height / 2)))
        if fereastra > 0.01 and self.fereastra is not None:
            wl = self.fereastra.copy(); wl.putalpha(self.fereastra.split()[3].point(lambda v: int(v * fereastra)))
            fr.alpha_composite(wl)
        return fr

    def inchide(self):
        if self.broll is not None:
            self.broll.kill()


def randeaza(spec, brand, iesire, cache, ordine_voce=None):
    """Randează un clip. Întoarce dict cu căile fișierelor și informații pentru manifest."""
    iesire, cache = Path(iesire), Path(cache)
    iesire.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
    nume = spec["id"]; tema = spec.get("tema", brand.get("tema_implicita", "iarna_seara"))
    T = TEME.get(tema, TEME["iarna_seara"]); culoare_text = T["text"]

    # 1) vocea, replică cu replică -> cronologie exactă
    sr = voce.SR
    segs, audio, t, furnizori = [], [np.zeros(int(sr * 0.6), np.int16)], 0.6, set()
    n_img = len(spec["produs"].get("imagini_url") or spec["produs"].get("imagini") or [1])
    min_prod = 2.3 * n_img + 0.4  # timp minim pe ecran pentru imaginile produsului
    replici = spec["replici"]
    ultim_prod = max([i for i, r in enumerate(replici) if r.get("scena") == "produs"], default=-1)
    start_prod = None
    for idx, s in enumerate(replici):
        v, furn = voce.genereaza(s["text"], brand, cache, ordine_voce)
        furnizori.add(furn)
        d = len(v) / sr; p = s.get("pauza", 0.4)
        if s.get("scena") == "produs" and start_prod is None:
            start_prod = t
        if idx == ultim_prod and start_prod is not None:
            p = max(p, min_prod - (t + d - start_prod))
        segs.append(dict(s, start=t, end=t + d))
        audio += [v, np.zeros(int(sr * p), np.int16)]
        t += d + p
    durata = t + spec.get("coada", 1.2)
    vox = np.concatenate(audio); vox = np.pad(vox, (0, max(0, int(sr * durata) - len(vox))))

    def zona(tip):
        z = [s for s in segs if s.get("scena") == tip]
        return (z[0]["start"], z[-1]["end"]) if z else None
    z_prod, z_fin = zona("produs"), zona("final")
    t_prod = z_prod[0] - 0.3 if z_prod else durata
    t_fin = z_fin[0] - 0.2 if z_fin else durata

    # 2) imagini și texte
    magazin = brand["magazin_shopify"]
    poze = [Image.open(p).convert("RGB") for p in imagini_produs(magazin, spec["produs"], cache)]
    acc = tuple(brand.get("culoare_accent", [255, 200, 140]))
    titlu = text_layer([spec["produs"]["titlu_ecran"]], F_SERIF, 88, culoare_text)
    benef = text_layer([spec["produs"].get("beneficiu_ecran", "")], F_SANS, 40, (255, 236, 214), maxw=980)
    cta1 = text_layer([spec["cta"]["linia1"]], F_SERIF_I, 92, culoare_text)
    cta2 = text_layer([spec["cta"]["linia2"]], F_SANS_SB, 120, (255, 255, 255))
    cta3 = text_layer([brand.get("slogan", "")], F_SANS, 40, acc)
    strat = {id(s): text_layer([s.get("ecran", s["text"])], F_SERIF_I, 84 if s.get("scena") != "produs" else 62, culoare_text) for s in segs}
    logo = None
    lp = RADACINA / "brands" / brand["id"] / "logo.png"
    if lp.exists():
        logo = Image.open(lp).convert("RGBA"); logo.thumbnail((360, 160))
    n = len(poze)
    F = Fundal(tema, nume, durata)

    def cadru(t):
        if t < t_prod:  # atmosferă
            p = t / max(1, t_prod)
            fr = F.cadru(t, 0.15 + 0.6 * ease((p - 0.2) / 0.3) - 0.35 * ease((p - 0.55) / 0.2),
                         0.55 + 0.45 * ease((p - 0.55) / 0.15), 1 - ease((t - 3.2) / 1.2),
                         ease((p - 0.28) / 0.08) * (1 - ease((p - 0.52) / 0.06)), 0.25 * ease((p - 0.85) / 0.1))
            if t < 0.6: fr = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), fr, ease(t / 0.6))
            for s in segs:
                if s.get("scena", "atmosfera") == "atmosfera":
                    put(fr, strat[id(s)], 780, env(t, s["start"] - 0.25, s["end"] + 0.35, 0.5, 0.35),
                        dy=18 * (1 - ease((t - s["start"] + 0.25) / 0.8)))
            return fr
        if t < t_fin:  # produs
            lt = t - t_prod; dur = t_fin - t_prod; seg = dur / n
            fr = F.cadru(t, 0.75, 0.35, 0, 0, 0.15)
            i = min(n - 1, int(lt / seg)); li = lt - i * seg; img = poze[i]
            CW = 900; ch0 = int(img.height * CW / img.width); z = 1.0 + 0.06 * (li / seg)
            card = img.resize((int(CW * z), int(ch0 * z)), Image.LANCZOS)
            ox, oy = (card.width - CW) // 2, (card.height - ch0) // 2
            card = card.crop((ox, oy, ox + CW, oy + ch0))
            mask = Image.new("L", card.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, CW, ch0], 36, fill=255)
            a = ease(li / 0.45) if i > 0 else ease(lt / 0.6)
            a_sh = 1.0 if i > 0 else a
            x0, y0 = (W - CW) // 2, 400
            sh = Image.new("RGBA", (CW + 120, ch0 + 120), (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle([60, 70, CW + 60, ch0 + 70], 40, fill=(0, 0, 0, int(150 * a_sh)))
            fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)), (x0 - 60, y0 - 60))
            if i > 0 and a < 1:  # trecere directă: imaginea anterioară rămâne dedesubt
                prev = poze[i - 1].resize((CW, int(poze[i - 1].height * CW / poze[i - 1].width)), Image.LANCZOS)
                prev = prev.resize((CW, ch0), Image.LANCZOS).convert("RGBA"); prev.putalpha(mask)
                fr.alpha_composite(prev, (x0, y0))
            cA = card.convert("RGBA"); cA.putalpha(mask.point(lambda v, a=a: int(v * a)))
            fr.alpha_composite(cA, (x0, y0))
            put(fr, titlu, 170, env(lt, 0.1, dur + 1, 0.6), dy=14 * (1 - ease(lt / 0.8)))
            put(fr, benef, y0 + ch0 + 210, env(lt, 1.2, dur + 1, 0.6))
            for s in segs:
                if s.get("scena") == "produs":
                    put(fr, strat[id(s)], y0 + ch0 + 40, env(t, s["start"] - 0.2, s["end"] + 0.3, 0.4, 0.3))
            if t > t_fin - 0.5:
                fr = Image.blend(fr, Image.new("RGBA", (W, H), (12, 8, 8, 255)), ease((t - (t_fin - 0.5)) / 0.5) * 0.6)
            return fr
        lt = t - t_fin; dur = durata - t_fin  # final
        fr = F.cadru(t, 0.6, 0.45, 0, 0, 0.45)
        fr = Image.blend(Image.new("RGBA", (W, H), (12, 8, 8, 255)), fr, 0.4 + 0.6 * ease(lt / 0.6))
        if logo is not None:
            la = logo.copy(); al = env(lt, 0.1, dur + 1, 0.6)
            la.putalpha(logo.split()[3].point(lambda v, a=al: int(v * a)))
            fr.alpha_composite(la, ((W - la.width) // 2, 560))
        put(fr, cta1, 760, env(lt, 0.1, dur + 1, 0.6), dy=16 * (1 - ease(lt / 0.8)))
        put(fr, cta2, 880, env(lt, 0.3, dur + 1, 0.6), dy=16 * (1 - ease((lt - 0.2) / 0.8)))
        al = env(lt, 0.8, dur + 1, 0.6)
        ImageDraw.Draw(fr).line([W / 2 - 140, 1060, W / 2 + 140, 1060], fill=acc + (int(220 * al),), width=3)
        put(fr, cta3, 1080, al)
        if t > durata - 0.6:
            fr = Image.blend(fr, Image.new("RGBA", (W, H), (0, 0, 0, 255)), ease((t - (durata - 0.6)) / 0.6))
        return fr

    # 3) video
    ff = ffmpeg_exe()
    tmp_v = cache / f"{nume}_video.tmp.mp4"
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                             "-pix_fmt", "yuv420p", str(tmp_v)], stdin=subprocess.PIPE)
    nf = int(round(durata * FPS))
    t_coperta = (t_prod + t_fin) / 2 + 0.6 if z_prod else durata / 2
    coperta = None
    for k in range(nf):
        fr = cadru(k / FPS).convert("RGB")
        if coperta is None and k / FPS >= t_coperta:
            coperta = fr.copy()
        proc.stdin.write(fr.tobytes())
    proc.stdin.close(); F.inchide()
    if proc.wait() != 0: raise RuntimeError("ffmpeg a eșuat la video")

    # 4) sunet: voce + muzică originală
    mus = muzica.genereaza(durata, 44100)
    mus_wav = cache / f"{nume}_muzica.wav"; muzica.scrie_wav(mus_wav, mus, 44100)
    voc_wav = cache / f"{nume}_voce.wav"
    with wave.open(str(voc_wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(vox.tobytes())
    vol_m = brand.get("volum_muzica", 0.22) if furnizori - {"fara"} else 0.8
    mp4 = iesire / f"{nume}.mp4"; tmpf = iesire / f"{nume}.tmp.mp4"
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(tmp_v), "-i", str(voc_wav), "-i", str(mus_wav),
                        "-filter_complex", f"[1:a]aresample=44100[v];[2:a]volume={vol_m}[m];[v][m]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                        "-shortest", "-movflags", "+faststart", str(tmpf)])
    if r.returncode != 0: raise RuntimeError("ffmpeg a eșuat la sunet")
    os.replace(tmpf, mp4); tmp_v.unlink(missing_ok=True)
    jpg = iesire / f"{nume}.jpg"
    (coperta or cadru(durata / 2).convert("RGB")).save(jpg, quality=90)

    # 5) subtitrări
    def ts(x):
        ms = int(round(x * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    srt = iesire / f"{nume}.srt"
    srt.write_text("\n".join(f"{i}\n{ts(s['start'])} --> {ts(s['end'] + 0.2)}\n{s['text']}\n" for i, s in enumerate(segs, 1)), encoding="utf-8")
    return {"mp4": mp4, "jpg": jpg, "srt": srt, "durata": round(durata, 1), "voce": sorted(furnizori), "tema": tema}
