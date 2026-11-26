"""Povestio v4 - planse ilustrate (desen animat educativ).

Totul se deseneaza din cod (forme vectoriale cu contur de cerneala usor tremurat),
deci nu consuma credite AI si arata la fel la fiecare clip.
Se lucreaza la 2x si se micsoreaza, pentru margini netede.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAD = Path(__file__).resolve().parent.parent
FONT_TITLU = RAD / "fonts" / "Nunito-Variable.ttf"
FONT_MANA = RAD / "fonts" / "PatrickHand-Regular.ttf"

W, H = 1080, 1920
S = 2  # supersampling

HARTIE = (255, 246, 229)
CERNEALA = (31, 42, 68)
GALBEN = (255, 201, 60)
CORAL = (255, 107, 91)
TEAL = (46, 196, 182)
ALBASTRU = (77, 124, 254)
PIELE = (246, 196, 160)
PAR = (92, 58, 40)
ALB = (255, 255, 255)
GRI = (214, 207, 192)
LEMN = (222, 176, 120)


def font(cale, px, greutate=None):
    f = ImageFont.truetype(str(cale), int(px * S))
    if greutate is not None:
        f.set_variation_by_axes([greutate])
    return f


class Plansa:
    def __init__(self, seed=0, fundal=HARTIE):
        if fundal is None:   # strat transparent (personaj, produs, etichete)
            self.im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        else:
            self.im = Image.new("RGBA", (W * S, H * S), fundal + (255,))
        self.d = ImageDraw.Draw(self.im)
        self.r = random.Random(seed)
        if fundal is not None:
            self._caiet()

    # ---------- utilitare ----------
    def _p(self, x, y):
        return (x * S, y * S)

    def _caiet(self):
        """linii fine de caiet, ca fundal de plansa"""
        for y in range(160, H, 64):
            self.d.line([self._p(0, y), self._p(W, y)], fill=(240, 228, 205), width=2 * S)

    def tremur(self, pts, amp=2.2, pasi=6):
        out = []
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            for i in range(pasi):
                t = i / pasi
                out.append((x1 + (x2 - x1) * t + self.r.uniform(-amp, amp),
                            y1 + (y2 - y1) * t + self.r.uniform(-amp, amp)))
        out.append(pts[-1])
        return out

    def poligon(self, pts, fill, contur=CERNEALA, gros=7, umbra=True):
        pts = [*pts, pts[0]]
        if umbra:
            self.d.polygon([self._p(x + 10, y + 12) for x, y in pts], fill=(0, 0, 0, 0) if False else (236, 222, 196))
        self.d.polygon([self._p(x, y) for x, y in pts], fill=fill)
        self.linie(pts, contur, gros)

    def linie(self, pts, culoare=CERNEALA, gros=7, amp=2.0):
        tp = self.tremur(pts, amp)
        self.d.line([self._p(x, y) for x, y in tp], fill=culoare, width=int(gros * S), joint="curve")

    def drept(self, x, y, w, h, fill, gros=7, raza=24, umbra=True):
        if umbra:
            self.d.rounded_rectangle([self._p(x + 10, y + 12), self._p(x + w + 10, y + h + 12)],
                                     radius=raza * S, fill=(236, 222, 196))
        self.d.rounded_rectangle([self._p(x, y), self._p(x + w, y + h)], radius=raza * S,
                                 fill=fill, outline=CERNEALA, width=gros * S)

    def cerc(self, cx, cy, r, fill, gros=7, contur=CERNEALA):
        self.d.ellipse([self._p(cx - r, cy - r), self._p(cx + r, cy + r)], fill=fill,
                       outline=contur, width=int(gros * S) if gros else 0)

    def text(self, x, y, s, px, culoare=CERNEALA, f=FONT_TITLU, greutate=850, ancora="la"):
        self.d.text(self._p(x, y), s, font=font(f, px, greutate if f == FONT_TITLU else None),
                    fill=culoare, anchor=ancora)

    def titlu(self, y, randuri, px=92, latime=940, marker=True, text=True):
        """Randuri de titlu; cuvintele intre *...* primesc marcaj galben desenat."""
        f = font(FONT_TITLU, px, 900)
        for rand in randuri:
            bucati = rand.split("*")
            total = sum(f.getlength(b) for b in bucati) / S
            x = (W - total) / 2
            for i, b in enumerate(bucati):
                lw = f.getlength(b) / S
                if i % 2 == 1 and b and marker:
                    self.d.polygon([self._p(x - 14, y + px * 0.28), self._p(x + lw + 12, y + px * 0.18),
                                    self._p(x + lw + 18, y + px * 1.05), self._p(x - 10, y + px * 1.12)],
                                   fill=GALBEN)
                if text:
                    self.d.text(self._p(x, y), b, font=f, fill=CERNEALA)
                x += lw
            y += px * 1.22
        return y

    def eticheta(self, x, y, s, fill=CORAL, culoare=ALB, px=46, rot=-4):
        f = font(FONT_TITLU, px, 850)
        tw = f.getlength(s) / S
        strat = Image.new("RGBA", (int((tw + 80) * S), int((px + 50) * S)), (0, 0, 0, 0))
        dd = ImageDraw.Draw(strat)
        dd.rounded_rectangle([0, 0, strat.width - 1, strat.height - 1], radius=40 * S, fill=fill,
                             outline=CERNEALA, width=6 * S)
        dd.text((40 * S, 18 * S), s, font=f, fill=culoare)
        strat = strat.rotate(rot, expand=True, resample=Image.BICUBIC)
        self.im.alpha_composite(strat, (int(x * S), int(y * S)))

    def bula(self, x, y, w, h, s, px=50, coada="jos-stanga"):
        self.drept(x, y, w, h, ALB, gros=6, raza=46, umbra=False)
        if coada == "jos-stanga":
            c = [(x + 70, y + h - 4), (x + 40, y + h + 60), (x + 140, y + h - 4)]
        else:
            c = [(x + w - 140, y + h - 4), (x + w - 40, y + h + 60), (x + w - 70, y + h - 4)]
        self.d.polygon([self._p(*p) for p in c], fill=ALB)
        self.linie([c[0], c[1], c[2]], gros=6, amp=1)
        self.text(x + w / 2, y + h / 2, s, px, f=FONT_MANA, ancora="mm")

    def sageata(self, pts, culoare=CERNEALA, gros=7):
        self.linie(pts, culoare, gros)
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        a = math.atan2(y2 - y1, x2 - x1)
        for da in (2.6, -2.6):
            self.linie([(x2, y2), (x2 + 34 * math.cos(a + da), y2 + 34 * math.sin(a + da))], culoare, gros)

    def numar(self, cx, cy, n, fill=ALBASTRU):
        self.cerc(cx, cy, 46, fill, 6)
        self.text(cx, cy + 2, str(n), 56, ALB, ancora="mm")

    # ---------- personaj ----------
    def membru(self, pts, culoare, gros):
        self.d.line([self._p(x, y) for x, y in pts], fill=CERNEALA, width=int((gros + 12) * S), joint="curve")
        for x, y in (pts[0], pts[-1]):
            self.cerc(x, y, (gros + 12) / 2, CERNEALA, 0)
        self.d.line([self._p(x, y) for x, y in pts], fill=culoare, width=int(gros * S), joint="curve")
        for x, y in (pts[0], pts[-1]):
            self.cerc(x, y, gros / 2, culoare, 0)

    def brat(self, umar, cot, mana, k):
        self.membru([umar, cot], TEAL, 40 * k)
        self.membru([cot, mana], PIELE, 32 * k)
        self.cerc(mana[0], mana[1], 24 * k, PIELE, 6)

    def personaj(self, cx, baza, stare="trist", scala=1.0, obiect=None, ochi_inchisi=False):
        """Personaj fictiv desenat din forme simple. stare: trist / bucuros / surprins."""
        k = scala
        hy = baza - 500 * k
        us, ud = (cx - 105 * k, baza - 300 * k), (cx + 105 * k, baza - 300 * k)
        # brate in spate de corp (pozitii)
        if obiect == "telefon":
            bs = (us, (cx - 150 * k, baza - 190 * k), (cx - 120 * k, baza - 90 * k))
            bd = (ud, (cx + 175 * k, baza - 230 * k), (cx + 150 * k, baza - 400 * k))
        elif obiect == "brate_sus":
            bs = (us, (cx - 190 * k, baza - 400 * k), (cx - 230 * k, baza - 540 * k))
            bd = (ud, (cx + 190 * k, baza - 400 * k), (cx + 230 * k, baza - 540 * k))
        else:
            bs = (us, (cx - 150 * k, baza - 190 * k), (cx - 130 * k, baza - 80 * k))
            bd = (ud, (cx + 150 * k, baza - 190 * k), (cx + 130 * k, baza - 80 * k))
        # corp (bluza) cu umeri rotunjiti
        self.d.rounded_rectangle([self._p(cx - 135 * k + 10, baza - 340 * k + 12), self._p(cx + 135 * k + 10, baza + 12)],
                                 radius=int(80 * k * S), fill=(236, 222, 196))
        self.d.rounded_rectangle([self._p(cx - 135 * k, baza - 340 * k), self._p(cx + 135 * k, baza + 40 * k)],
                                 radius=int(80 * k * S), fill=TEAL, outline=CERNEALA, width=7 * S)
        # gat si decolteu
        self.d.rounded_rectangle([self._p(cx - 28 * k, baza - 400 * k), self._p(cx + 28 * k, baza - 320 * k)],
                                 radius=int(12 * k * S), fill=PIELE, outline=CERNEALA, width=6 * S)
        self.d.chord([self._p(cx - 55 * k, baza - 370 * k), self._p(cx + 55 * k, baza - 280 * k)], 0, 180,
                     fill=PIELE, outline=CERNEALA, width=6 * S)
        self.d.rectangle([self._p(cx - 55 * k, baza - 360 * k), self._p(cx + 55 * k, baza - 325 * k)], fill=PIELE)
        # par spate + coc
        self.d.ellipse([self._p(cx - 125 * k, hy - 130 * k), self._p(cx + 125 * k, hy + 150 * k)], fill=PAR,
                       outline=CERNEALA, width=7 * S)
        self.cerc(cx + 20 * k, hy - 150 * k, 52 * k, PAR, 7)
        # fata
        self.d.ellipse([self._p(cx - 100 * k, hy - 100 * k), self._p(cx + 100 * k, hy + 115 * k)], fill=PIELE,
                       outline=CERNEALA, width=7 * S)
        # breton lateral
        self.d.polygon([self._p(cx - 104 * k, hy - 10 * k), self._p(cx - 90 * k, hy - 85 * k), self._p(cx - 20 * k, hy - 112 * k),
                        self._p(cx + 70 * k, hy - 95 * k), self._p(cx + 104 * k, hy - 30 * k), self._p(cx + 20 * k, hy - 60 * k),
                        self._p(cx - 60 * k, hy - 30 * k)], fill=PAR)
        # ochi
        for dx in (-40, 40):
            if ochi_inchisi and stare != "bucuros":
                self.linie([(cx + (dx - 16) * k, hy + 18 * k), (cx + (dx + 16) * k, hy + 18 * k)], gros=6, amp=0.3)
            elif stare == "surprins":
                self.cerc(cx + dx * k, hy + 15 * k, 17 * k, ALB, 5)
                self.cerc(cx + dx * k, hy + 17 * k, 7 * k, CERNEALA, 0)
            elif stare == "bucuros":
                self.d.arc([self._p(cx + (dx - 16) * k, hy + 5 * k), self._p(cx + (dx + 16) * k, hy + 32 * k)],
                           200, 340, fill=CERNEALA, width=6 * S)
            else:
                self.cerc(cx + dx * k, hy + 18 * k, 10 * k, CERNEALA, 0)
                self.cerc(cx + (dx + 3) * k, hy + 14 * k, 3 * k, ALB, 0)
        # obraji
        for dx in (-62, 62):
            self.cerc(cx + dx * k, hy + 55 * k, 15 * k, (255, 170, 160), 0)
        # sprancene + gura
        if stare == "trist":
            self.linie([(cx - 62 * k, hy - 18 * k), (cx - 22 * k, hy - 30 * k)], gros=6, amp=0.5)
            self.linie([(cx + 22 * k, hy - 30 * k), (cx + 62 * k, hy - 18 * k)], gros=6, amp=0.5)
            self.d.arc([self._p(cx - 30 * k, hy + 62 * k), self._p(cx + 30 * k, hy + 100 * k)],
                       200, 340, fill=CERNEALA, width=6 * S)
        elif stare == "bucuros":
            self.d.chord([self._p(cx - 38 * k, hy + 45 * k), self._p(cx + 38 * k, hy + 100 * k)],
                         0, 180, fill=CORAL, outline=CERNEALA, width=5 * S)
        else:
            self.cerc(cx, hy + 78 * k, 15 * k, CORAL, 5)
        # brate
        self.brat(*bs, k)
        self.brat(*bd, k)
        if obiect == "telefon":
            self.telefon(bd[2][0] + 10 * k, bd[2][1] - 40 * k, k)
            self.cerc(bd[2][0], bd[2][1] + 20 * k, 24 * k, PIELE, 6)

    def telefon(self, cx, cy, k=1.0, baterie=1):
        self.drept(cx - 46 * k, cy - 82 * k, 92 * k, 164 * k, CERNEALA, gros=5, raza=16, umbra=False)
        self.drept(cx - 36 * k, cy - 70 * k, 72 * k, 140 * k, (236, 240, 255), gros=0, raza=10, umbra=False)
        # baterie
        self.drept(cx - 22 * k, cy - 16 * k, 40 * k, 24 * k, ALB, gros=4, raza=4, umbra=False)
        self.d.rectangle([self._p(cx - 18 * k, cy - 12 * k), self._p(cx - 12 * k, cy + 4 * k)], fill=CORAL)
        self.text(cx, cy + 34 * k, f"{baterie}%", 28 * k, CORAL, ancora="mm")

    # ---------- decor ----------
    def bucatarie(self, blat_y=1330, cabluri=True):
        # perete cu faianta
        for x in range(0, W, 120):
            for y in range(blat_y - 520, blat_y, 120):
                self.d.rounded_rectangle([self._p(x + 6, y + 6), self._p(x + 114, y + 114)], radius=10 * S,
                                         fill=(232, 241, 245))
        # frigider in dreapta
        self.drept(820, blat_y - 760, 230, 1000, (230, 236, 240), gros=7, raza=30)
        self.linie([(820, blat_y - 420), (1050, blat_y - 420)], gros=6)
        self.linie([(850, blat_y - 600), (850, blat_y - 500)], gros=10)
        # priza ascunsa dupa frigider
        self.drept(1040, blat_y - 300, 60, 80, ALB, gros=5, raza=10, umbra=False)
        # blat
        self.drept(-20, blat_y, W + 40, 70, LEMN, gros=7, raza=10)
        self.drept(-20, blat_y + 70, W + 40, H - blat_y, (186, 140, 96), gros=7, raza=0, umbra=False)
        if cabluri:
            for i, c in enumerate([CERNEALA, (90, 90, 90), CORAL]):
                pts = [(140 + i * 30, blat_y - 10)]
                for j in range(9):
                    pts.append((180 + j * 70 + self.r.uniform(-40, 40), blat_y - 30 - self.r.uniform(0, 60)))
                pts.append((1040, blat_y - 260))
                self.linie(pts, c, 9, amp=6)

    def produs(self, cale, cx, baza, latime):
        img = Image.open(cale).convert("RGBA")
        k = latime * S / img.width
        img = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
        # contur alb ca la sticker, ca produsul real sa se lege de ilustratie
        a = img.split()[3].filter(ImageFilter.MaxFilter(25))
        sticker = Image.new("RGBA", img.size, ALB + (0,))
        sticker.putalpha(a)
        x, y = int(cx * S - img.width / 2), int(baza * S - img.height)
        self.im.alpha_composite(sticker, (max(0, x), max(0, y)))
        self.im.alpha_composite(img, (max(0, x), max(0, y)))

    def finalizeaza(self):
        return self.im.resize((W, H), Image.LANCZOS)
