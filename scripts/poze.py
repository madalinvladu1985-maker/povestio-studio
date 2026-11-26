"""Face o plansa cu toate pozele unui produs (pentru alegerea pozei curate)."""
import json, sys, urllib.request, io
from pathlib import Path
from PIL import Image, ImageDraw
cat = json.load(open("catalog/atentales.json"))
for h in Path("catalog/poze_cerere.txt").read_text().split():
    p = next(x for x in cat["produse"] if x["handle"] == h)
    ims = []
    for u in p["imagini"]:
        r = urllib.request.urlopen(urllib.request.Request(u + "&width=400", headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
        ims.append(Image.open(io.BytesIO(r.read())).convert("RGB"))
    c = Image.new("RGB", (410 * len(ims), 440), "white"); d = ImageDraw.Draw(c)
    for i, im in enumerate(ims):
        im.thumbnail((400, 400)); c.paste(im, (i * 410, 40)); d.text((i * 410 + 10, 10), str(i), fill="red")
    Path("catalog/poze").mkdir(exist_ok=True); c.save(f"catalog/poze/{h}.jpg", quality=80)
