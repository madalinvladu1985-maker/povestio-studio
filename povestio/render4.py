"""Povestio v4 - clip din planse ilustrate animate (desen animat educativ).

Fiecare scena: decor desenat + personaj fictiv + titlu cu marcaj galben + elemente
care apar pe rand (bula, produs care urca din blat, etichete, pasi, CTA).
Straturile statice se deseneaza o singura data; pe cadru se fac doar mutari si opacitati.
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from povestio import ai_imagini, muzica, voce
from povestio.planse import (ALB, ALBASTRU, CERNEALA, CORAL, FONT_TITLU, GALBEN, H, LEMN, TEAL, W, Plansa,
                             font)
from povestio.render3 import ease, ease_out_back, ffmpeg_exe

RAD = Path(__file__).resolve().parent.parent
FPS = 30
CULORI = {"albastru": ALBASTRU, "coral": CORAL, "teal": TEAL, "galben": GALBEN}
BLAT_Y = 1330
TRANZ = 0.35


# ---------- straturi decupate (imagine, x, y) ----------
def decupeaza(im):
    b = im.getbbox()
    if not b:
        return None
    return (im.crop(b), b[0], b[1])


def strat(fn, seed=0):
    p = Plansa(seed, fundal=None)
    fn(p)
    return decupeaza(p.finalizeaza())


def pune(fr, st, dx=0.0, dy=0.0, a=1.0, s=1.0):
    if st is None or a <= 0.01:
        return
    im, x, y = st
    if s != 1.0:
        s = max(s, 0.05)
        nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
        x, y = x + (im.width - nw) / 2, y + (im.height - nh) / 2
        im = im.resize((nw, nh), Image.BILINEAR)
    if a < 1.0:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    x, y = int(round(x + dx)), int(round(y + dy))
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(im.width, W - x), min(im.height, H - y)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    fr.alpha_composite(im.crop((cx0, cy0, cx1, cy1)), (x + cx0, y + cy0))


def taie_sus(st, y_limita):
    """pastreaza doar partea stratului de deasupra liniei y_limita (pentru produsul care iese din blat)"""
    return st


# ---------- subtitrari pe fraze ----------
LEGATURI = {"și", "iar", "când", "dar", "pentru", "ca", "că"}


def _rupe(cuv, max_cuv):
    if len(cuv) <= max_cuv:
        return [" ".join(cuv)]
    mij = len(cuv) / 2
    # cel mai bun punct: inaintea unui cuvant de legatura, cat mai aproape de mijloc
    cand = [i for i in range(2, len(cuv) - 1) if cuv[i].lower() in LEGATURI]
    i = min(cand, key=lambda i: abs(i - mij)) if cand else int(round(mij))
    return _rupe(cuv[:i], max_cuv) + _rupe(cuv[i:], max_cuv)


def fraze(text, max_cuv=6):
    bucati = [b.strip() for b in re.split(r"(?<=[.:;!?…])\s+", text) if b.strip()]
    out = []
    for b in bucati:
        grup = []
        for x in re.split(r"(?<=,)\s+", b):
            if grup and len(grup) + len(x.split()) > max_cuv:
                out += _rupe(grup, max_cuv); grup = []
            grup += x.split()
        if grup:
            out += _rupe(grup, max_cuv)
    # o bucata prea lata pentru ecran (peste ~34 caractere) se imparte in doua
    rez = []
    for b in out:
        cuv = b.split()
        if len(b) > 34 and len(cuv) > 1:
            k = min(range(1, len(cuv)), key=lambda i: abs(len(" ".join(cuv[:i])) - len(b) / 2))
            rez += [" ".join(cuv[:k]), " ".join(cuv[k:])]
        else:
            rez.append(b)
    return rez


def strat_eticheta_ai(text="Realizat cu AI"):
    """Eticheta permanenta, discreta, in coltul din dreapta sus (transparenta AI)."""
    f = font(FONT_TITLU, 30, 800)
    tw = f.getlength(text) / 2
    lat, inalt = int(tw + 44), 52
    im = Image.new("RGBA", (lat * 2, inalt * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=inalt, fill=CERNEALA + (190,))
    d.text((im.width / 2, im.height / 2 + 1), text, font=f, fill=ALB, anchor="mm")
    im = im.resize((lat, inalt), Image.LANCZOS)
    return (im, W - lat - 36, 40)


def strat_subtitlu(text, y=1720, accent=False):
    """Subtitrare pe pastilă închisă. y = marginea de sus a pastilei.
    1720 = jos (vechi, acoperit de descrierea TikTok); ~1345 = deasupra descrierii, spre centru."""
    f = font(FONT_TITLU, 54 if accent else 50, 900 if accent else 850)
    tw = f.getlength(text) / 2
    lat = min(int(tw + 80), 1000)
    inalt = 124 if accent else 120
    im = Image.new("RGBA", (lat * 2, inalt * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=inalt, fill=CERNEALA + (240,),
                        outline=(GALBEN + (255,)) if accent else None, width=8 if accent else 0)
    d.text((im.width / 2, im.height / 2 + 2), text, font=f, fill=GALBEN if accent else ALB, anchor="mm")
    im = im.resize((lat, inalt), Image.LANCZOS)
    return (im, (W - lat) // 2, int(y))


def strat_outro(brand_id, slogan):
    """Cadrul final: logoul brandului centrat + slogan, pe fundal crem."""
    fr = Image.new("RGBA", (W, H), (255, 250, 242, 255))
    lp = RAD / "brands" / brand_id / "logo.png"
    logo = None
    if lp.exists():
        logo = Image.open(lp).convert("RGBA")
        k = 860 / logo.width
        logo = logo.resize((860, int(logo.height * k)), Image.LANCZOS)
    sl = None
    if slogan:
        f = font(FONT_TITLU, 46, 800)  # fontul e la scară 2x, ca la subtitrări
        tw = int(f.getlength(slogan)) + 60
        sl = Image.new("RGBA", (tw, 200), (0, 0, 0, 0))
        ImageDraw.Draw(sl).text((tw / 2, 100), slogan, font=f, fill=CERNEALA + (255,), anchor="mm")
        sl = sl.resize((tw // 2, 100), Image.LANCZOS)
    return fr, logo, sl


def deseneaza_outro(o, lt):
    fr, logo, sl = o
    fr = fr.copy()
    if logo is not None:
        s = 0.8 + 0.2 * ease_out_back(lt / 0.6)
        pune(fr, (logo, (W - logo.width) // 2, 760), a=ease(lt / 0.35), s=s)
    if sl is not None:
        pune(fr, (sl, (W - sl.width) // 2, 1040), a=ease((lt - 0.5) / 0.4), dy=20 * (1 - ease((lt - 0.5) / 0.5)))
    return fr


def sunet_impact(sr=44100, dur=0.9):
    """Lovitură scurtă + suflu, generate din cod (fără licențe), pentru primul cadru al hook-ului."""
    n = int(sr * dur); t = np.arange(n) / sr
    frecv = 38 + 70 * np.exp(-t * 18)
    boom = np.sin(2 * np.pi * np.cumsum(frecv) / sr) * np.exp(-t * 5.5)
    rng = np.random.default_rng(7)
    zg = rng.standard_normal(n)
    zg = np.convolve(zg, np.ones(24) / 24, mode="same") * np.exp(-((t - 0.08) ** 2) / 0.004)
    return (0.9 * boom + 0.35 * zg).astype(np.float32)


# ---------- construirea unei scene ----------
def construieste(sc, idx, produs_cale):
    L = {}
    decor = sc.get("decor", "hartie")
    pb = Plansa(idx + 1)
    if decor.startswith("bucatarie"):
        pb.bucatarie(BLAT_Y, cabluri=(decor == "bucatarie_cabluri"))
    elif decor == "baie":
        pb.baie(BLAT_Y)
    elif decor == "sufragerie":
        pb.sufragerie(BLAT_Y)
    elif decor == "terasa":
        pb.terasa(BLAT_Y)
    L["fundal"] = pb.finalizeaza()
    if sc.get("_ai_cfg"):
        cale_ai = ai_imagini.genereaza(sc, sc["_ai_cfg"], sc["_ai_cache"], sc.get("_ai_pers", ""))
        if cale_ai:
            L["fundal"] = Image.open(cale_ai).convert("RGBA"); L["fundal_ai"] = True
            if sc.get("ilustratie_personaj", True):
                sc = {k: v for k, v in sc.items() if k != "personaj"}  # personajul e deja in ilustratie
            if sc.get("produs", {}).get("din_blat"):
                sc = dict(sc, produs=dict(sc["produs"], din_blat=False))
            L["sc"] = sc

    ytit = 250 if sc.get("eticheta") else 200
    if sc.get("eticheta"):
        c = CULORI.get(sc.get("culoare_eticheta", "albastru"), ALBASTRU)
        L["eticheta"] = strat(lambda p: p.eticheta(60, 110, sc["eticheta"], c))
    if sc.get("ecran"):
        rand = sc["ecran"].split("\n")
        px = sc.get("marime_ecran", 92)
        L["marker"] = strat(lambda p: p.titlu(ytit, rand, px=px, text=False))
        L["titlu"] = [strat(lambda p, r=r, k=k: p.titlu(ytit + k * px * 1.22, [r], px=px, marker=False))
                      for k, r in enumerate(rand)]

    pers = sc.get("personaj")
    if pers:
        args = dict(cx=pers.get("x", 380), baza=BLAT_Y, stare=pers.get("stare", "trist"),
                    obiect=pers.get("obiect"))
        L["pers"] = strat(lambda p: p.personaj(**args))
        L["pers_clipit"] = strat(lambda p: p.personaj(**args, ochi_inchisi=True))

    if sc.get("bula"):
        b = sc["bula"]
        L["bula"] = strat(lambda p: p.bula(470, 560, 440, 150, b, 44))

    pr = sc.get("produs")
    if pr:
        L["produs"] = strat(lambda p: p.produs(produs_cale, pr.get("x", 540), pr.get("baza", 1250), pr.get("latime", 620), pr.get("inaltime_max", 620)))
        if pr.get("din_blat"):
            # blatul desenat in fata produsului, ca sa para ca iese din el
            yb = pr.get("baza", 1250) - 40
            L["blat_fata"] = strat(lambda p: (p.drept(-20, yb, W + 40, 60, LEMN, gros=7, raza=10, umbra=False),
                                              p.drept(-20, yb + 60, W + 40, 70, (186, 140, 96), gros=7, raza=0, umbra=False)))
            L["fundal_jos"] = Plansa(idx + 50).finalizeaza().crop((0, yb + 130, W, H))
            L["fundal_jos_y"] = yb + 130

    L["etichete"] = []
    for e in sc.get("etichete", []):
        cx, cy, lat = e.get("x", 540), e["y"], e.get("latime", 460)
        fond = GALBEN if e.get("accent") else ALB
        L["etichete"].append(strat(lambda p, e=e, cx=cx, cy=cy, lat=lat, fond=fond: (
            p.drept(cx - lat / 2, cy, lat, 96, fond, gros=6, raza=48),
            p.text(cx, cy + 48, e["text"], 44, ancora="mm"),
            e.get("sageata") and p.sageata([(cx, cy + 96), (cx + 5, cy + 200)], CERNEALA, 6))))

    L["pasi"] = []
    culori_pasi = [ALBASTRU, TEAL, CORAL, GALBEN]
    for k, txt in enumerate(sc.get("pasi", [])):
        n = len(sc["pasi"])
        cx = W / 2 + (k - (n - 1) / 2) * 350
        L["pasi"].append(strat(lambda p, k=k, cx=cx, txt=txt: (
            p.numar(cx, sc.get("_pasi_y", 1530), k + 1, culori_pasi[k % 4]),
            p.text(cx, sc.get("_pasi_y", 1530) + 70, txt, 44, ancora="ma", greutate=800))))

    if sc.get("tip") == "cta":
        cta = sc.get("cta", {})
        y0 = sc.get("_cta_y", 1480)
        L["cta_cutie"] = strat(lambda p: (p.drept(90, y0, 900, 250, ALB, gros=7, raza=40),
                                          p.text(540, y0 + 50, cta.get("sus", ""), 50, ancora="ma")))
        L["cta_domeniu"] = strat(lambda p: p.eticheta(330, y0 + 130, cta.get("domeniu", "AtentAles.ro"), GALBEN, CERNEALA, 58, rot=-2))
    return L


def deseneaza(L, sc, lt, D, t):
    sc = L.get("sc", sc)
    if L.get("fundal_ai"):
        # mișcare lentă de cameră peste ilustrație (zoom 1.00 -> 1.07, ușor în sus)
        z = 1.0 + 0.07 * min(max(lt / max(D, 0.1), 0), 1)
        f = L["fundal"]; cw, ch = int(W / z), int(H / z)
        x0 = (W - cw) // 2; y0 = int((H - ch) * 0.45)
        fr = f.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)
    else:
        fr = L["fundal"].copy()
    # titlu si eticheta
    pune(fr, L.get("eticheta"), a=ease(lt / 0.2), s=0.6 + 0.4 * ease_out_back(lt / 0.4))
    for k, st in enumerate(L.get("titlu", [])):
        t0 = 0.15 + k * 0.22
        if k == len(L["titlu"]) - 1 and L.get("marker"):
            # marcajul galben se "pictează" de la stânga la dreapta, sub ultimul rând
            pass
        pune(fr, st, a=ease((lt - t0) / 0.3), dy=30 * (1 - ease((lt - t0) / 0.4)))
    if L.get("marker"):
        mk = L["marker"]; pr = ease((lt - 0.55) / 0.45)
        if pr > 0:
            im, x, y = mk
            w = max(1, int(im.width * pr))
            fr.alpha_composite(im.crop((0, 0, w, im.height)), (x, y))
            # titlul trebuie să rămână peste marcaj
            for k, st in enumerate(L.get("titlu", [])):
                t0 = 0.15 + k * 0.22
                pune(fr, st, a=ease((lt - t0) / 0.3), dy=30 * (1 - ease((lt - t0) / 0.4)))

    # produs
    if L.get("produs"):
        prc = sc["produs"]
        if prc.get("din_blat"):
            r = ease_out_back((lt - prc.get("start", 0.3)) / 1.0) if lt > prc.get("start", 0.3) else 0.0
            pune(fr, L["produs"], dy=520 * (1 - r))
            fr.alpha_composite(L["fundal_jos"], (0, L["fundal_jos_y"]))
            pune(fr, L["blat_fata"])
        else:
            st0 = prc.get("start", 0.2)
            pune(fr, L["produs"], a=ease((lt - st0) / 0.3), s=0.85 + 0.15 * ease_out_back((lt - st0) / 0.5),
                 dy=4 * math.sin(t * 2.2))

    # personaj: respiră, clipește, sare de bucurie
    if L.get("pers"):
        p = sc["personaj"]
        bob = 6 * math.sin(2 * math.pi * 0.7 * t)
        if p.get("stare") == "bucuros":
            bob = -26 * abs(math.sin(2 * math.pi * 0.9 * t))
        clipit = (t % 3.1) < 0.13
        intrare = p.get("intrare", False)
        dy = 420 * (1 - ease_out_back(lt / 0.7)) if intrare else 0
        pune(fr, L["pers_clipit"] if clipit else L["pers"], dy=bob + dy)

    if L.get("bula"):
        b0 = sc.get("bula_start", 0.6)
        pune(fr, L["bula"], a=ease((lt - b0) / 0.2), s=0.5 + 0.5 * ease_out_back((lt - b0) / 0.4))

    n = len(L["etichete"])
    for k, st in enumerate(L["etichete"]):
        t0 = 0.6 + k * min(0.6, (D - 1.6) / max(n, 1))
        pune(fr, st, a=ease((lt - t0) / 0.2), s=0.6 + 0.4 * ease_out_back((lt - t0) / 0.4))
    n = len(L["pasi"])
    for k, st in enumerate(L["pasi"]):
        t0 = 1.0 + k * min(0.9, (D - 1.8) / max(n, 1))
        pune(fr, st, a=ease((lt - t0) / 0.2), s=0.5 + 0.5 * ease_out_back((lt - t0) / 0.45))

    if L.get("cta_cutie"):
        pune(fr, L["cta_cutie"], a=ease((lt - 0.5) / 0.3), dy=200 * (1 - ease((lt - 0.5) / 0.5)))
        pune(fr, L["cta_domeniu"], a=ease((lt - 1.0) / 0.2), s=0.5 + 0.5 * ease_out_back((lt - 1.0) / 0.45))
    return fr


def randeaza(spec, brand, iesire, cache, ordine_voce=None):
    iesire, cache = Path(iesire), Path(cache)
    iesire.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
    nume = spec["id"]; sr = voce.SR
    # aspect: setările brandului, suprascrise de spec (ex. clip demonstrativ)
    aspect = {**brand.get("aspect", {}), **spec.get("aspect", {})}
    if spec.get("voce_setari"):
        brand = {**brand, "voce": {**brand.get("voce", {}), **spec["voce_setari"]}}
    sub_y = aspect.get("subtitlu_y", 1720)

    # 1) vocea pe scene -> cronologie
    scene, audio, t, furn = [], [np.zeros(int(sr * 0.3), np.int16)], 0.3, set()
    for sc in spec["scene"]:
        v, f = voce.genereaza(sc["voce"], brand, cache, ordine_voce); furn.add(f)
        d = len(v) / sr; pauza = sc.get("pauza", 0.35)
        dur = max(d + pauza, sc.get("durata_min", 0))
        extra = {k: aspect[a] for k, a in (("_cta_y", "cta_y"), ("_pasi_y", "pasi_y")) if a in aspect}
        if aspect.get("fundal_ai"):
            extra.update(_ai_cfg=aspect["fundal_ai"], _ai_cache=str(cache), _ai_pers=spec.get("personaj_ai", ""))
        scene.append(dict(sc, **extra, start=t, end=t + dur, v_end=t + d))
        audio += [v, np.zeros(int(sr * (dur - d)), np.int16)]
        t += dur
    durata = t + 0.6
    outro_cfg = aspect.get("outro_logo")
    t_outro = None
    if outro_cfg:
        t_outro = durata
        durata += float(outro_cfg.get("durata", 2.2))
        outro = strat_outro(brand.get("id", spec.get("brand", "")), outro_cfg.get("slogan", ""))
    vox = np.concatenate(audio); vox = np.pad(vox, (0, max(0, int(sr * durata) - len(vox))))

    # 2) straturi
    dec = spec["produs"].get("decupaje", {})
    if dec.get("erou"):
        pc = dec["erou"]
        produs_cale = RAD / (pc if isinstance(pc, str) else pc["cale"])
    else:
        from povestio.imagine import pregateste
        produs_cale = pregateste(spec["produs"]["imagine_url"], cache, spec["produs"].get("imagine_zona"),
                                 spec["produs"].get("imagine_punct"))
    straturi = [construieste(sc, i, produs_cale) for i, sc in enumerate(scene)]

    # subtitrari: fraze scurte, cronometrate proportional cu lungimea lor
    eticheta_ai = strat_eticheta_ai(brand.get("eticheta_ai", "Realizat cu AI"))
    subt = []
    for sc in scene:
        fz = fraze(sc.get("subtitlu", sc["voce"]))
        tot = sum(len(x) for x in fz); t0 = sc["start"]
        for x in fz:
            d = (sc["v_end"] - sc["start"]) * len(x) / tot
            acc = aspect.get("subtitlu_accent_hook", False) and sc.get("tip") == "hook"
            subt.append((t0, t0 + d, sc.get("tip") == "cta", strat_subtitlu(x, sub_y, acc), x)); t0 += d

    def cadru_scena(i, lt):
        sc = scene[i]
        return deseneaza(straturi[i], sc, lt, sc["end"] - sc["start"], sc["start"] + lt)

    def cadru(t):
        if t_outro is not None and t >= t_outro:
            lt = t - t_outro
            fr = deseneaza_outro(outro, lt)
            if lt < 0.35:  # trecere lină din ultima scenă
                fr = Image.blend(cadru_continut(t_outro - 0.01), fr, ease(lt / 0.35))
            pune(fr, eticheta_ai)
            return fr
        return cadru_continut(t)

    def cadru_continut(t):
        i = next((k for k, s in enumerate(scene) if t < s["end"]), len(scene) - 1)
        sc = scene[i]; lt = t - sc["start"]
        fr = cadru_scena(i, lt)
        if i > 0 and lt < TRANZ:
            # tranziție tip pagină: scena nouă intră din dreapta peste cea veche
            e = ease(lt / TRANZ)
            vechi = cadru_scena(i - 1, scene[i - 1]["end"] - scene[i - 1]["start"])
            baza = Image.new("RGBA", (W, H))
            baza.alpha_composite(vechi.crop((int(W * e * 0.35), 0, W, H)), (0, 0))
            x = int(W * (1 - e))
            umbra = Image.new("RGBA", (30, H), (0, 0, 0, 60))
            if x > 30:
                baza.alpha_composite(umbra, (x - 30, 0))
            baza.alpha_composite(fr.crop((0, 0, W - x, H)), (x, 0))
            fr = baza
        for (a, b, e_cta, st, _) in subt:
            if a <= t < b + 0.15 and not e_cta:
                pune(fr, st, a=min(ease((t - a) / 0.12), 1.0))
        pune(fr, eticheta_ai)
        if t_outro is None and t > durata - 0.4:
            fr = Image.blend(fr, Image.new("RGBA", (W, H), (255, 246, 229, 255)), ease((t - (durata - 0.4)) / 0.4))
        return fr

    ff = ffmpeg_exe()
    tmp_v = cache / f"{nume}_v4.tmp.mp4"
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                             "-pix_fmt", "yuv420p", str(tmp_v)], stdin=subprocess.PIPE)
    nf = int(round(durata * FPS)); coperta = None
    t_cop = scene[0]["start"] + 1.4
    for k in range(nf):
        fr = cadru(k / FPS).convert("RGB")
        if coperta is None and k / FPS >= t_cop:
            coperta = fr.copy()
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg a eșuat la video")

    mus = muzica.genereaza(durata, 44100)
    if aspect.get("sunet_hook"):
        imp = sunet_impact(44100); i0 = int(44100 * 0.05)
        mus = mus.astype(np.float32); seg = mus[i0:i0 + len(imp)]
        k = float(aspect.get("sunet_hook_volum", 0.55)) / max(brand.get("volum_muzica", 0.22), 0.05)
        seg += (imp[:len(seg), None] if seg.ndim == 2 else imp[:len(seg)]) * k
    mus_wav = cache / f"{nume}_muzica.wav"; muzica.scrie_wav(mus_wav, mus, 44100)
    voc_wav = cache / f"{nume}_voce.wav"
    with wave.open(str(voc_wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(vox.tobytes())
    vol_m = brand.get("volum_muzica", 0.22) if furn - {"fara"} else 0.8
    # voce „de impact”: mai prezentă și mai apăsată (compresie + puțin bas tăiat + câștig)
    filtru_voce = (",highpass=f=90,acompressor=threshold=-22dB:ratio=4:attack=4:release=90:makeup=3,"
                   "equalizer=f=3000:t=q:w=1.2:g=3,volume=1.15") if aspect.get("voce_impact") else ""
    mp4 = iesire / f"{nume}.mp4"; tmpf = iesire / f"{nume}.tmp.mp4"
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(tmp_v), "-i", str(voc_wav), "-i", str(mus_wav),
                        "-filter_complex", f"[1:a]aresample=44100{filtru_voce}[v];[2:a]volume={vol_m}[m];[v][m]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                        "-shortest", "-movflags", "+faststart", str(tmpf)])
    if r.returncode != 0:
        raise RuntimeError("ffmpeg a eșuat la sunet")
    os.replace(tmpf, mp4); tmp_v.unlink(missing_ok=True)
    jpg = iesire / f"{nume}.jpg"; (coperta or cadru(1.5).convert("RGB")).save(jpg, quality=90)

    def ts(x):
        ms = int(round(x * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    srt = iesire / f"{nume}.srt"
    srt.write_text("\n".join(f"{i}\n{ts(a)} --> {ts(b + 0.15)}\n{x}\n" for i, (a, b, _, _, x) in enumerate(subt, 1)),
                   encoding="utf-8")
    return {"mp4": mp4, "jpg": jpg, "srt": srt, "durata": round(durata, 1), "voce": sorted(furn), "tema": "v4_planse"}
