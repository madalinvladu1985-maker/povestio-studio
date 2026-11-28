"""Povestio - bugetul de credite de voce pe toata luna.

Ideea: creditele ElevenLabs ramase se impart la clipurile ramase pana la resetare,
cu 10% rezerva. Fiecare slot primeste o tinta de lungime ALEATORIE (dar fixa pentru acel
slot, deci reproductibila), ca durata clipurilor sa varieze pe toata luna, nu sa scada spre final.
Bugetul se recalculeaza zilnic din soldul real, deci se autocorecteaza.
"""
from __future__ import annotations

import json
import random
from datetime import date, datetime, timezone
from pathlib import Path

RAD = Path(__file__).resolve().parent.parent
SLOTURI = ["07:30", "11:00", "14:30", "17:00", "20:30"]
SLOTURI_PE_NUMAR = {5: SLOTURI, 4: ["07:30", "11:00", "17:00", "20:30"], 3: ["07:30", "14:30", "20:30"]}
MIN_CLIPURI = 3                 # acordul lui Madalin (28.11): se poate cobori pana la 3 clipuri/zi ca sa ajunga creditele
CAR_CONFORT = 420               # sub media asta pe clip, mai bine mai putine clipuri (minimum 3) decat sa depasim bugetul


def _zi_incompleta(zi: date) -> bool:
    """Ieri s-au facut mai putine clipuri decat sloturi planificate -> semn ca s-a atins limita Claude."""
    d = RAD / "clipuri" / zi.isoformat()
    if not d.exists():
        return False
    plan = d / "numar_clipuri.txt"
    n_plan = int(plan.read_text().strip()) if plan.exists() else len(SLOTURI)
    gata = sum(1 for f in d.glob("AA_*.json") if (RAD / "publicat" / f.name).exists())
    return gata < n_plan
CREDIT_PE_CARACTER = 0.5        # eleven_flash_v2_5 prin API
CARACTERE_PE_SECUNDA = 16       # masurat pe vocea Corina (355 caractere ~ 22 s voce)
MIN_CAR, MAX_CAR = 400, 540     # stilul aprobat 27.11: clipuri de 35-40 s (~26-34 s de voce + logo)
MEDIE_OPTIMA_CAR = 470          # ~30 s de voce -> clip de ~37 s cu pauzele si logoul
REZERVA = 0.10


def _consum_luna(zi: date):
    """Credite consumate in luna calendaristica a zilei, din clipurile randate (spec + manifest)."""
    from povestio.voce import pentru_voce
    brand = json.loads((RAD / "brands" / "atentales" / "brand.json").read_text())
    tot = 0
    for d in (RAD / "clipuri").glob(f"{zi.year:04d}-{zi.month:02d}-*"):
        for f in d.glob("AA_*.json"):
            if not (RAD / "publicat" / f.name).exists():
                continue
            try:
                sc = json.loads(f.read_text()).get("scene", [])
            except Exception:
                continue
            tot += sum(len(pentru_voce(x.get("voce", ""), brand)) for x in sc) * CREDIT_PE_CARACTER
    # rerandari si teste: +15%
    return int(tot * 1.15)


def _sold():
    """Soldul real scris de workflow (publicat/elevenlabs.json); altfel valorile din brand."""
    f = RAD / "publicat" / "elevenlabs.json"
    if f.exists():
        d = json.loads(f.read_text())
        ramase = d["character_limit"] - d["character_count"]
        reset = datetime.fromtimestamp(d["next_character_count_reset_unix"], timezone.utc).date()
        return ramase, reset, "elevenlabs"
    b = json.loads((RAD / "brands" / "atentales" / "brand.json").read_text())
    azi = date.today()
    return b["voce"].get("buget_credite_luna", 30000) - _consum_luna(azi), None, "estimare din clipurile randate"


def tinte_zi(zi: date | str):
    zi = date.fromisoformat(zi) if isinstance(zi, str) else zi
    ramase, reset, sursa = _sold()
    if reset is None or reset <= zi:
        # fara data de resetare: considera sfarsitul lunii
        urm = date(zi.year + (zi.month == 12), zi.month % 12 + 1, 1)
        reset = urm
    zile = max(1, (reset - zi).days)
    # cate clipuri pe zi: 5, apoi 4, apoi minimum 3, ca fiecare clip sa aiba o lungime confortabila
    n = 5
    while n > MIN_CLIPURI and ramase * (1 - REZERVA) / (zile * n) / CREDIT_PE_CARACTER < CAR_CONFORT:
        n -= 1
    motiv = "credite suficiente" if n == 5 else "economie de credite ElevenLabs"
    from datetime import timedelta
    if n > MIN_CLIPURI and _zi_incompleta(zi - timedelta(days=1)):
        n -= 1; motiv = "ieri n-au ieșit toate clipurile (limita Claude) - o zi mai ușoară"
    sloturi = SLOTURI_PE_NUMAR[n]
    clipuri_ramase = zile * n
    medie = ramase * (1 - REZERVA) / clipuri_ramase          # credite / clip
    r_zi = random.Random(f"zi-{zi.isoformat()}")
    f_zi = r_zi.uniform(0.85, 1.15)                          # unele zile mai lungi, altele mai scurte
    out = []
    for s in sloturi:
        r = random.Random(f"slot-{zi.isoformat()}-{s}")
        f = r.uniform(0.90, 1.10)
        baza = min(medie / CREDIT_PE_CARACTER, MEDIE_OPTIMA_CAR)
        car = int(max(MIN_CAR, min(MAX_CAR, baza * f_zi * f)))
        out.append({"ora": s, "caractere_voce": car, "credite": round(car * CREDIT_PE_CARACTER),
                    "secunde_voce_aprox": round(car / CARACTERE_PE_SECUNDA)})
    return {"zi": zi.isoformat(), "numar_clipuri": n, "motiv_numar": motiv, "sursa_sold": sursa, "credite_ramase": ramase, "resetare": reset.isoformat(),
            "clipuri_ramase": clipuri_ramase, "medie_credite_pe_clip": round(medie), "sloturi": out,
            "total_zi_credite": sum(x["credite"] for x in out)}
