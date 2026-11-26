"""Povestio - bucla de invatare din performanta clipurilor.

Flux:
  1. Agentul de analiza citeste metricile din Metricool la 24 h si 72 h dupa postare
     si le scrie intr-un fisier JSON (vezi docs/AGENT_ANALIZA.md).
  2. `studio.py analiza inregistreaza <metrici.json>` le adauga in performanta/istoric.json.
  3. `studio.py analiza actualizeaza` recalculeaza ce variante castiga, urca tinta
     de vizualizari cand e atinsa si scrie performanta/strategie.json.
  4. Agentul de continut citeste strategie.json si construieste clipurile zilei:
     2 clipuri "exploatare" (stilul castigator) + 1 clip "explorare" (variabila noua).
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

RADACINA = Path(__file__).resolve().parent.parent
DIR_PERF = RADACINA / "performanta"
F_ISTORIC = DIR_PERF / "istoric.json"
F_STRATEGIE = DIR_PERF / "strategie.json"

# Trepte de tinta: dupa 5k -> 10k -> 20k -> 50k -> 100k
TREPTE = [5000, 10000, 20000, 50000, 100000]

# Dimensiunile pe care agentul le testeaza (trebuie sa existe in spec la "varianta")
DIMENSIUNI = ["hook_tip", "deschidere", "mix_scene", "durata", "ora", "categorie", "retea"]

# Reguli statistice minime (sa nu decidem pe 1-2 clipuri)
MIN_CLIPURI_PE_VALOARE = 3
FEREASTRA_TINTA = 6          # ultimele N clipuri masurate la 72 h
PRAG_ATINS = 3               # cel putin 3 din ultimele 6 trec de tinta


def _citeste(f: Path, implicit):
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return implicit


def _scrie(f: Path, date):
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(date, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def strategie_implicita() -> dict:
    return {
        "tinta_vizualizari": TREPTE[0],
        "trepte": TREPTE,
        "tinta_atinsa_la": {},
        "mix_zilnic": {"exploatare": 2, "explorare": 1},
        "castigatori": {},
        "de_testat": {
            "hook_tip": ["stiai_ca", "motive", "hai_sa_arat", "intrebare", "pov_problema"],
            "deschidere": ["personaj_problema", "detaliu_macro", "text_soc", "inainte_dupa"],
            "mix_scene": ["video_greu", "echilibrat", "produs_greu"],
            "durata": ["20-25", "25-30", "30-35"],
            "ora": ["12:00", "17:00", "20:00"],
        },
        "observatii": [],
        "actualizat": None,
    }


def _durata_bucket(sec: float | None) -> str | None:
    if sec is None:
        return None
    if sec < 25:
        return "20-25"
    if sec < 30:
        return "25-30"
    return "30-35"


def scor(m: dict) -> float:
    """Scor compus: vizualizarile conteaza cel mai mult, dar retentia si
    distribuirile arata DE CE un clip creste (algoritmii le folosesc)."""
    v = m.get("vizualizari", 0) or 0
    ret = (m.get("retentie_pct") or 0) / 100            # 0..1
    interact = (m.get("aprecieri", 0) + 2 * m.get("comentarii", 0)
                + 3 * m.get("distribuiri", 0) + 3 * m.get("salvari", 0))
    rata_int = interact / v if v else 0
    return round(v * (1 + ret) * (1 + 5 * rata_int), 1)


def inregistreaza(fisier_metrici: Path) -> int:
    """Adauga/actualizeaza intrari. Format: lista de obiecte
    {clip_id, retea, ora_postare, ore_de_la_postare, vizualizari, retentie_pct,
     aprecieri, comentarii, distribuiri, salvari, varianta{...}}"""
    noi = json.loads(Path(fisier_metrici).read_text(encoding="utf-8"))
    if isinstance(noi, dict):
        noi = [noi]
    ist = _citeste(F_ISTORIC, [])
    index = {(e["clip_id"], e["retea"], e.get("ore_de_la_postare")): i for i, e in enumerate(ist)}
    for m in noi:
        m = dict(m)
        m["scor"] = scor(m)
        m["inregistrat"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cheie = (m["clip_id"], m["retea"], m.get("ore_de_la_postare"))
        if cheie in index:
            ist[index[cheie]] = m
        else:
            ist.append(m)
    _scrie(F_ISTORIC, ist)
    return len(noi)


def _valori(e: dict) -> dict:
    var = dict(e.get("varianta") or {})
    var.setdefault("retea", e.get("retea"))
    if "durata" not in var:
        var["durata"] = _durata_bucket(var.get("durata_s"))
    if "ora" not in var and e.get("ora_postare"):
        var["ora"] = e["ora_postare"][-5:]
    return var


def actualizeaza() -> dict:
    ist = _citeste(F_ISTORIC, [])
    st = _citeste(F_STRATEGIE, strategie_implicita())
    # doar masuratorile mature (72 h) intra in decizie
    mature = [e for e in ist if (e.get("ore_de_la_postare") or 0) >= 72]

    castigatori, observatii = {}, []
    for dim in DIMENSIUNI:
        grupuri: dict[str, list[float]] = {}
        for e in mature:
            val = _valori(e).get(dim)
            if val:
                grupuri.setdefault(str(val), []).append(e["vizualizari"])
        valide = {k: v for k, v in grupuri.items() if len(v) >= MIN_CLIPURI_PE_VALOARE}
        if not valide:
            continue
        medii = {k: statistics.median(v) for k, v in valide.items()}
        best = max(medii, key=medii.get)
        castigatori[dim] = {"valoare": best, "mediana_vizualizari": medii[best],
                            "esantion": len(valide[best]),
                            "toate": {k: [round(m), len(valide[k])] for k, m in medii.items()}}
        if len(medii) > 1:
            al_doilea = sorted(medii.values())[-2]
            if al_doilea and medii[best] / al_doilea < 1.2:
                observatii.append(f"{dim}: diferenta sub 20% — inca neconcludent, continua testul.")

    # urcarea tintei
    tinta = st["tinta_vizualizari"]
    ultimele = sorted(mature, key=lambda e: e.get("inregistrat", ""))[-FEREASTRA_TINTA:]
    peste = sum(1 for e in ultimele if e["vizualizari"] >= tinta)
    if len(ultimele) >= FEREASTRA_TINTA and peste >= PRAG_ATINS:
        st["tinta_atinsa_la"][str(tinta)] = datetime.now(timezone.utc).date().isoformat()
        urm = [t for t in TREPTE if t > tinta]
        if urm:
            st["tinta_vizualizari"] = urm[0]
            observatii.append(f"Tinta {tinta} atinsa ({peste}/{len(ultimele)}). Noua tinta: {urm[0]}.")
    else:
        observatii.append(f"Tinta {tinta}: {peste}/{len(ultimele)} din ultimele clipuri mature au trecut-o "
                          f"(e nevoie de {PRAG_ATINS}/{FEREASTRA_TINTA}).")

    st["castigatori"] = castigatori
    st["observatii"] = observatii
    st["clipuri_mature"] = len(mature)
    st["actualizat"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _scrie(F_STRATEGIE, st)
    return st


def raport() -> str:
    st = _citeste(F_STRATEGIE, strategie_implicita())
    r = [f"Tinta curenta: {st['tinta_vizualizari']} vizualizari / clip",
         f"Clipuri mature analizate: {st.get('clipuri_mature', 0)}"]
    for dim, c in st.get("castigatori", {}).items():
        r.append(f"  {dim}: {c['valoare']} (mediana {round(c['mediana_vizualizari'])}, n={c['esantion']})")
    r += [f"  * {o}" for o in st.get("observatii", [])]
    return "\n".join(r)
