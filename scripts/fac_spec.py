"""Construiește un spec v4 dintr-un dict compact. Uz: python fac_spec.py clip.py"""
import json, sys, runpy, os
REPO = "/home/claude/povestio-studio"
cat = json.load(open(f"{REPO}/catalog/atentales.json"))
C = runpy.run_path(sys.argv[1])["CLIP"]
p = [x for x in cat["produse"] if x["handle"] == C["handle"]][0]
F = "https://www.figma.com/api/mcp/asset/{}.jpg"
cid = C["id"]; data = C["data"]; ora = C["ora"]
url_cat = f"https://atentales.ro/collections/{C['categorie']}"
def utm(r): return f"{url_cat}?utm_source={r}&utm_medium=short&utm_campaign=povestio&utm_content={cid}"
scene = []
for s in C["scene"]:
    s = dict(s)
    if "il" in s:
        s["ilustratie_url"] = F.format(s.pop("il")); s["ilustratie_personaj"] = False
    s.setdefault("decor", "hartie")
    scene.append(s)
cta_s = {"tip": "cta", "decor": "hartie", "ecran": C["cta_ecran"], "marime_ecran": 80,
         "produs": {"x": 540, "baza": 1170, "latime": 420, "inaltime_max": 640, "start": 0.2},
         "cta": {"sus": C["cta_sus"], "domeniu": "AtentAles.ro"}, "voce": C["cta_voce"], "durata_min": 3.0}
if C.get("subtitlu_cta"): cta_s["subtitlu"] = C["subtitlu_cta"]
scene.append(cta_s)
AI = "Conținut realizat cu ajutorul AI."
corp = C["text"]  # hook + sfaturi + CTA (fără AI, fără hashtaguri)
tags = C["hashtaguri"]
prod = {"handle": p["handle"], "url": p["url"], "imagine_url": p["imagini"][C.get("poza", 0)], "fapte_din_fisa": C["fapte"]}
for k in ("imagine_zona", "imagine_punct"):
    if k in C: prod[k] = C[k]
spec = {
 "id": cid, "brand": "atentales", "versiune_motor": 4,
 "unghi_marketing": C["unghi"], "stare_emotionala": C["stare_txt"],
 "produs": prod,
 "cta": {"sus": C["cta_sus"], "categorie": C["categorie_titlu"], "domeniu": "AtentAles.ro", "url_categorie": url_cat},
 "programare": {"data": data, "ora": ora},
 "tinta_caractere_voce": C["tinta"], "voce_id": C["voce_id"],
 "aspect": {"fundal_ai": {"model": "figma"}, "pasi_y": 1120},
 "scene": scene,
 "sursa_personaje": "ilustratii AI (Figma, gemini-3.1-flash-lite-image)",
 "personaj_descriere": C["personaj"],
 "varianta": {"hook_tip": C["hook_tip"], "deschidere": "personaj_situatie", "mix_scene": "ilustratii_miscatoare",
              "categorie": C["categorie"], "stil": "poveste_ilustrata", "stare": C["stare"]},
 "platforme": {
  "tiktok": {"text": f"{corp}\n{AI}\n{tags}"},
  "instagram": {"text": f"{corp}\n{AI}\n{tags}"},
  "facebook": {"text": f"{corp} {utm('facebook')}\n{AI}\n{tags}"},
  "threads": {"text": f"{corp}\n{AI}"},
  "youtube": {"titlu": C["titlu_yt"], "descriere": f"{corp} {utm('youtube')}\n{AI}"},
  "pinterest": {"text": f"{C['text_pin']} {AI}", "link": utm("pinterest")},
  "first_comment": C["comentariu"]},
 "titlu_scurt": C["titlu"],
}
out = f"{REPO}/clipuri/{data}/{cid}.json"
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(spec, open(out, "w"), ensure_ascii=False, indent=1)
print(out, "voce:", sum(len(s["voce"]) for s in scene), "ig:", len(spec["platforme"]["instagram"]["text"]))
