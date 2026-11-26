#!/usr/bin/env python3
"""
Povestio Studio - povești video care vând, cât tu bei cafeaua.

Comenzi:
  python studio.py verifica clipuri/2026-11-27/AA_01.json   verifică scenariul (fără randare)
  python studio.py render   clipuri/2026-11-27/AA_01.json   randează un clip
  python studio.py batch                                    randează toate clipurile noi
  python studio.py release                                  urcă clipurile randate în GitHub Release
Opțiuni: --fara-voce  (test fără ElevenLabs/Azure)

Fluxul complet: clipuri/<data>/*.json  ->  iesire/*.mp4  ->  publicat/<id>.json (manifest pentru Metricool)
"""
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

RAD = Path(__file__).resolve().parent
sys.path.insert(0, str(RAD))

from povestio.verificare import verifica  # noqa: E402

CLIPURI, IESIRE, PUBLICAT, CACHE = RAD / "clipuri", RAD / "iesire", RAD / "publicat", RAD / "cache"


def brand_de(spec):
    b = spec.get("brand", "atentales")
    p = RAD / "brands" / b / "brand.json"
    if not p.exists():
        sys.exit(f"Lipsește profilul de brand: {p}")
    d = json.loads(p.read_text(encoding="utf-8")); d["id"] = b
    return d


def citeste(cale):
    return json.loads(Path(cale).read_text(encoding="utf-8"))


def scrie_manifest(id_, date_):
    PUBLICAT.mkdir(exist_ok=True)
    (PUBLICAT / f"{id_}.json").write_text(json.dumps(date_, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_verifica(cale):
    spec = citeste(cale); erori, avert = verifica(spec, brand_de(spec))
    for e in erori: print("EROARE:", e)
    for a in avert: print("Atenție:", a)
    print("OK" if not erori else "RESPINS")
    return not erori


def proceseaza(cale, fara_voce=False):
    from povestio.render import randeaza as randeaza_v2
    from povestio.render3 import randeaza as randeaza_v3
    spec = citeste(cale); brand = brand_de(spec)
    erori, avert = verifica(spec, brand)
    baza = {"id": spec["id"], "brand": brand["id"], "spec": str(Path(cale).relative_to(RAD)),
            "programare": spec.get("programare", {}), "platforme": spec.get("platforme", {}),
            "produs": spec.get("produs", {}), "actualizat": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if erori:
        scrie_manifest(spec["id"], {**baza, "status": "respins", "erori": erori, "avertismente": avert})
        print(f"[{spec['id']}] RESPINS: {erori}")
        return False
    try:
        if spec.get("versiune_motor") == 4:
            from povestio.render4 import randeaza as rnd
        else:
            rnd = randeaza_v3 if spec.get("versiune_motor") == 3 else randeaza_v2
        rez = rnd(spec, brand, IESIRE, CACHE, ["fara"] if fara_voce else None)
    except Exception as e:  # o eroare la un clip nu le oprește pe celelalte
        scrie_manifest(spec["id"], {**baza, "status": "eroare_randare", "erori": [str(e)]})
        print(f"[{spec['id']}] EROARE la randare: {e}")
        return False
    scrie_manifest(spec["id"], {**baza, "status": "randat", "avertismente": avert, "durata_s": rez["durata"],
                                "voce": rez["voce"], "tema": rez["tema"],
                                "fisiere": {k: rez[k].name for k in ("mp4", "jpg", "srt")}})
    print(f"[{spec['id']}] randat: {rez['mp4'].name} ({rez['durata']} s, voce: {rez['voce']})")
    return True


def cmd_batch(fara_voce=False):
    noi = []
    for p in sorted(CLIPURI.rglob("*.json")):
        try:
            id_ = citeste(p)["id"]
        except Exception as e:
            print(f"Fișier invalid {p}: {e}"); continue
        m = PUBLICAT / f"{id_}.json"
        if not m.exists() or citeste(m).get("status") in ("eroare_randare",):
            noi.append(p)
    if not noi:
        print("Niciun clip nou."); return
    for p in noi:
        proceseaza(p, fara_voce)


def cmd_release():
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        sys.exit("GITHUB_REPOSITORY lipsește (comanda rulează în GitHub Actions).")
    for m in sorted(PUBLICAT.glob("*.json")):
        d = citeste(m)
        if d.get("status") != "randat":
            continue
        tag = "clipuri-" + d.get("programare", {}).get("data", date.today().isoformat())
        if subprocess.run(["gh", "release", "view", tag], capture_output=True).returncode != 0:
            subprocess.run(["gh", "release", "create", tag, "--title", f"Povestio {tag[8:]}",
                            "--notes", "Clipuri generate automat de Povestio."], check=True)
        fis = [str(IESIRE / d["fisiere"][k]) for k in ("mp4", "jpg", "srt")]
        subprocess.run(["gh", "release", "upload", tag, *fis, "--clobber"], check=True)
        url = f"https://github.com/{repo}/releases/download/{tag}"
        d.update(status="gata_de_programat", video_url=f"{url}/{d['fisiere']['mp4']}",
                 coperta_url=f"{url}/{d['fisiere']['jpg']}", srt_url=f"{url}/{d['fisiere']['srt']}",
                 actualizat=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        m.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{d['id']}] publicat în release {tag}")


if __name__ == "__main__":
    a = sys.argv[1:]
    fara = "--fara-voce" in a
    a = [x for x in a if x != "--fara-voce"]
    if not a:
        sys.exit(__doc__)
    if a[0] == "verifica":
        sys.exit(0 if cmd_verifica(a[1]) else 1)
    elif a[0] == "render":
        sys.exit(0 if proceseaza(Path(a[1]).resolve(), fara) else 1)
    elif a[0] == "batch":
        cmd_batch(fara)
    elif a[0] == "release":
        cmd_release()
    elif a[0] == "buget":
        from povestio.buget import tinte_zi
        from datetime import date as _d
        print(json.dumps(tinte_zi(a[1] if len(a) > 1 else _d.today().isoformat()), ensure_ascii=False, indent=1))
    elif a[0] == "analiza":
        from povestio import analiza
        sub = a[1] if len(a) > 1 else "raport"
        if sub == "inregistreaza":
            print(f"{analiza.inregistreaza(Path(a[2]))} masuratori inregistrate")
            analiza.actualizeaza()
        elif sub == "actualizeaza":
            analiza.actualizeaza()
        print(analiza.raport())
    else:
        sys.exit(__doc__)
