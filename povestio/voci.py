"""Povestio - alegerea vocii pe clip.

Reguli (Mădălin, 28.11.2026):
- beauty, păr și alte produse dedicate femeilor -> voce feminină, de fiecare dată alta;
- prizele încorporabile -> voce masculină, de fiecare dată alta;
- celelalte categorii completează ziua astfel încât fiecare zi să aibă și voci feminine, și masculine;
- nicio voce nu se repetă în aceeași zi și se evită vocea folosită la ultimul clip de ieri.
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

RAD = Path(__file__).resolve().parent.parent
FEMININ_PREFIX = ("beauty", "par-", "aparate-coafat", "ingrijire-par")
FEMININ_EXACT: set[str] = set()   # alte categorii dedicate femeilor se adaugă aici
MASCULIN_EXACT = {"casa-bucatarie-prize", "electronice-prize"}


def gen_categorie(cat: str) -> str | None:
    if cat in MASCULIN_EXACT:
        return "m"
    if cat in FEMININ_EXACT or cat.startswith(FEMININ_PREFIX):
        return "f"
    return None


def _voci(brand):
    v = brand["voce"]
    return {"f": v["voci_feminine"], "m": v["voci_masculine"]}


def _folosite(zi: date):
    """vocile folosite in ziua data (din spec-urile existente)"""
    out = []
    for f in sorted((RAD / "clipuri" / zi.isoformat()).glob("AA_*.json")):
        try:
            out.append(json.loads(f.read_text()).get("voce_id"))
        except Exception:
            pass
    return [x for x in out if x]


def alege(zi: str | date, categorii: list[str], brand: dict):
    zi = date.fromisoformat(zi) if isinstance(zi, str) else zi
    voci = _voci(brand)
    r = random.Random(f"voci-{zi.isoformat()}")
    genuri = [gen_categorie(c) for c in categorii]
    # completeaza categoriile neutre ca ziua sa fie mixta (cel putin 2 si 2 la 5 clipuri)
    minim = 2 if len(categorii) >= 4 else 1
    for g in ("f", "m"):
        lipsa = minim - genuri.count(g)
        libere = [i for i, x in enumerate(genuri) if x is None]
        r.shuffle(libere)
        for i in libere[:max(0, lipsa)]:
            genuri[i] = g
    for i, x in enumerate(genuri):
        if x is None:
            genuri[i] = r.choice("fm")
    ieri = _folosite(zi - timedelta(days=1))
    deja = set(_folosite(zi))
    pool = {g: [v for v in voci[g]] for g in "fm"}
    for g in "fm":
        r.shuffle(pool[g])
        # vocile folosite azi sau la ultimul clip de ieri merg la coada
        pool[g].sort(key=lambda v: (v["id"] in deja, ieri[-1:] == [v["id"]]))
    out = []
    for c, g in zip(categorii, genuri):
        v = pool[g].pop(0) if pool[g] else r.choice(voci[g])
        out.append({"categorie": c, "gen": "feminin" if g == "f" else "masculin", "voce": v["nume"], "voce_id": v["id"]})
    return out
