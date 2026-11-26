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
CREDIT_PE_CARACTER = 0.5        # eleven_flash_v2_5 prin API
CARACTERE_PE_SECUNDA = 16       # masurat pe vocea Corina (355 caractere ~ 22 s voce)
MIN_CAR, MAX_CAR = 240, 520     # ~15 s ... ~32 s de voce
MEDIE_OPTIMA_CAR = 380          # ~24 s de voce: tinta de retentie; nu lungim clipurile doar pentru ca avem credite
REZERVA = 0.10


def _sold():
    """Soldul real scris de workflow (publicat/elevenlabs.json); altfel valorile din brand."""
    f = RAD / "publicat" / "elevenlabs.json"
    if f.exists():
        d = json.loads(f.read_text())
        ramase = d["character_limit"] - d["character_count"]
        reset = datetime.fromtimestamp(d["next_character_count_reset_unix"], timezone.utc).date()
        return ramase, reset, "elevenlabs"
    b = json.loads((RAD / "brands" / "atentales" / "brand.json").read_text())
    return b["voce"].get("buget_credite_luna", 30000), None, "estimare"


def tinte_zi(zi: date | str):
    zi = date.fromisoformat(zi) if isinstance(zi, str) else zi
    ramase, reset, sursa = _sold()
    if reset is None or reset <= zi:
        # fara data de resetare: considera sfarsitul lunii
        urm = date(zi.year + (zi.month == 12), zi.month % 12 + 1, 1)
        reset = urm
    zile = max(1, (reset - zi).days)
    clipuri_ramase = zile * len(SLOTURI)
    medie = ramase * (1 - REZERVA) / clipuri_ramase          # credite / clip
    r_zi = random.Random(f"zi-{zi.isoformat()}")
    f_zi = r_zi.uniform(0.85, 1.15)                          # unele zile mai lungi, altele mai scurte
    out = []
    for s in SLOTURI:
        r = random.Random(f"slot-{zi.isoformat()}-{s}")
        f = r.uniform(0.70, 1.30)
        baza = min(medie / CREDIT_PE_CARACTER, MEDIE_OPTIMA_CAR)
        car = int(max(MIN_CAR, min(MAX_CAR, baza * f_zi * f)))
        out.append({"ora": s, "caractere_voce": car, "credite": round(car * CREDIT_PE_CARACTER),
                    "secunde_voce_aprox": round(car / CARACTERE_PE_SECUNDA)})
    return {"zi": zi.isoformat(), "sursa_sold": sursa, "credite_ramase": ramase, "resetare": reset.isoformat(),
            "clipuri_ramase": clipuri_ramase, "medie_credite_pe_clip": round(medie), "sloturi": out,
            "total_zi_credite": sum(x["credite"] for x in out)}
