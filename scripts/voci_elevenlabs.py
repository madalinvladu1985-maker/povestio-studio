"""Listeaza vocile ElevenLabs (cont + biblioteca partajata, feminine, romana) in verificari/voci.json."""
import json, os, urllib.request, urllib.parse
from pathlib import Path
k = os.environ["ELEVENLABS_API_KEY"]
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"xi-api-key": k}), timeout=30))
out = {"cont": [], "partajate_ro_feminine": []}
for v in get("https://api.elevenlabs.io/v1/voices").get("voices", []):
    out["cont"].append({"id": v["voice_id"], "nume": v["name"], "categorie": v.get("category"), "etichete": v.get("labels"),
                        "limbi": [x.get("language") for x in (v.get("verified_languages") or [])]})
try:
    q = urllib.parse.urlencode({"language": "ro", "gender": "female", "page_size": 30, "sort": "usage_character_count_1y"})
    for v in get("https://api.elevenlabs.io/v1/shared-voices?" + q).get("voices", []):
        out["partajate_ro_feminine"].append({"id": v["voice_id"], "public_owner_id": v.get("public_owner_id"), "nume": v["name"],
                                             "accent": v.get("accent"), "varsta": v.get("age"), "descriere": (v.get("description") or "")[:160],
                                             "folosire": v.get("use_case"), "utilizari_1an": v.get("usage_character_count_1y")})
except Exception as e:
    out["eroare_partajate"] = str(e)
Path("verificari").mkdir(exist_ok=True)
Path("verificari/voci.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(len(out["cont"]), len(out["partajate_ro_feminine"]))
