# Genereaza spec v4 dintr-un fisier .py cu dict C (vezi exemplele din rularea 27.11). Folosire: python scripts/spec_din_py.py clip.py
import json, sys, copy
sys.path.insert(0, '.')
from povestio.voce import pentru_voce
BR = json.load(open('brands/atentales/brand.json'))
AI = "Conținut realizat cu ajutorul AI."


def car(scene):
    return sum(len(pentru_voce(s.get("voce", ""), BR)) for s in scene)


def utm(url, retea, cid):
    return f"{url}?utm_source={retea}&utm_medium=short&utm_campaign=povestio&utm_content={cid}"


def spec(c):
    cid = c["id"]
    p = c["produs"]
    s = {
        "id": cid, "brand": "atentales", "versiune_motor": 4,
        "unghi_marketing": c["unghi"], "stare_emotionala": c["stare"],
        "tinta_caractere_voce": c["tinta"],
        "produs": p,
        "cta": {"sus": "Vezi toate", "categorie": c["cat_titlu"], "domeniu": "AtentAles.ro",
                "url_categorie": c["cat_url"]},
        "programare": {"data": c["data"], "ora": c["ora"]},
        "scene": c["scene"],
        "platforme": {
            "tiktok": {"text": c["tt"] + "\n" + AI + "\n" + c["tags"]},
            "instagram": {"text": c["ig"] + "\n" + AI + "\n" + c["tags"]},
            "facebook": {"text": c["fb"] + "\n" + utm(c["cat_url"], "facebook", cid) + "\n" + AI},
            "threads": {"text": c["th"] + "\n" + AI},
            "youtube": {"titlu": c["yt_titlu"],
                        "descriere": c["yt_desc"] + " " + utm(c["cat_url"], "youtube", cid) + " " + AI,
                        "tags": c["yt_tags"]},
            "pinterest": {"titlu": c["scurt"], "text": c["pin"] + " " + AI,
                          "link": utm(c["cat_url"], "pinterest", cid)},
        },
        "titlu_scurt": c["scurt"],
        "prim_comentariu": c["comentariu"],
        "youtube_categorie": c.get("yt_cat", "HOWTO_STYLE"),
        "sursa_personaje": "personaj fictiv desenat din cod (Povestio planșe)",
        "varianta": c["varianta"],
    }
    return s


if __name__ == "__main__":
    import importlib.util
    spec_mod = importlib.util.spec_from_file_location("clip", sys.argv[1])
    m = importlib.util.module_from_spec(spec_mod); spec_mod.loader.exec_module(m)
    s = spec(m.C)
    print(cid := s["id"], "caractere voce:", car(s["scene"]), "tinta:", s["tinta_caractere_voce"],
          "cuvinte:", len(" ".join(x["voce"] for x in s["scene"]).split()))
    out = f"clipuri/{m.C['data']}/{cid}.json"
    json.dump(s, open(out, "w"), ensure_ascii=False, indent=2)
    print(out)
