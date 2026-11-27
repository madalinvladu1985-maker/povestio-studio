"""Test Gemini API: cheia exista? ce modele de imagine sunt disponibile? genereaza 1 imagine de proba."""
import base64, json, os, urllib.request
from pathlib import Path
out = Path("verificari/test_gemini"); out.mkdir(parents=True, exist_ok=True)
rez = {}
k = os.environ.get("GEMINI_API_KEY")
if not k:
    rez["cheie"] = "LIPSESTE secretul GEMINI_API_KEY"
else:
    rez["cheie"] = "exista"
    try:
        m = json.load(urllib.request.urlopen(f"https://generativelanguage.googleapis.com/v1beta/models?key={k}&pageSize=200", timeout=30))
        rez["modele_imagine"] = [x["name"] for x in m.get("models", []) if "image" in x["name"] or "banana" in x["name"] or "imagen" in x["name"]]
    except Exception as e:
        rez["eroare_modele"] = str(e)
    prompt = ("A flat vector 2D animation-style illustration with soft gradients, warm palette of cream, teal and coral. "
              "A woman in her early thirties with a short auburn bob and a mustard sweater smiles in a cozy kitchen. "
              "Top third is a plain cream wall. Vertical 9:16. No text, no logos.")
    for model in ["gemini-nano-banana-2.1", "gemini-2.5-flash-image", "gemini-3.1-flash-image"]:
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                           "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "9:16"}}}).encode()
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={k}",
                data=body, headers={"Content-Type": "application/json"}), timeout=120))
            img = None
            for c in r.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    d = p.get("inline_data") or p.get("inlineData")
                    if d: img = d["data"]
            if img:
                (out / f"{model}.png").write_bytes(base64.b64decode(img)); rez[model] = "OK"
            else:
                rez[model] = "fara imagine: " + json.dumps(r)[:300]
        except urllib.error.HTTPError as e:
            rez[model] = f"HTTP {e.code}: {e.read().decode()[:300]}"
        except Exception as e:
            rez[model] = str(e)[:300]
(out / "rezultat.json").write_text(json.dumps(rez, ensure_ascii=False, indent=1))
print(json.dumps(rez, ensure_ascii=False, indent=1))
