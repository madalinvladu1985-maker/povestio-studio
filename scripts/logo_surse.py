"""Descarca sursele de logo Atent Ales (avatar Metricool + logo din header-ul site-ului) in brands/atentales/logo_surse/."""
import re
import sys
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent.parent / "brands" / "atentales" / "logo_surse"
OUT.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 Povestio"}
surse = {"metricool_avatar.png": "https://static.metricool.com/brand-avatar/8391098/202611/61af766d-1b5a-4d6b-ae18-207c9372f294.png"}
try:
    html = requests.get("https://atentales.ro/", headers=H, timeout=30).text
    (OUT / "site.html.txt").write_text(html[:200000], encoding="utf-8")
    gasite = re.findall(r'(?:src|srcset)="([^"]*?(?:logo|Logo|LOGO)[^"\s,]*)', html)
    gasite += re.findall(r'<img[^>]+class="[^"]*logo[^"]*"[^>]+src="([^"]+)"', html)
    for i, u in enumerate(dict.fromkeys(gasite)):
        u = u.split(" ")[0]
        if u.startswith("//"):
            u = "https:" + u
        u = re.sub(r"([?&])width=\d+", r"\1width=1200", u) if "width=" in u else u + ("&" if "?" in u else "?") + "width=1200"
        surse[f"site_logo_{i}{Path(u.split('?')[0]).suffix or '.png'}"] = u
    for m in re.findall(r'<link[^>]+rel="(?:icon|shortcut icon|apple-touch-icon)"[^>]+href="([^"]+)"', html):
        u = ("https:" + m) if m.startswith("//") else m
        surse[f"favicon{Path(u.split('?')[0]).suffix or '.png'}"] = u
except Exception as e:
    print("site:", e)
for nume, url in surse.items():
    try:
        r = requests.get(url, headers=H, timeout=30)
        r.raise_for_status()
        (OUT / nume).write_bytes(r.content)
        print("ok", nume, url, len(r.content))
    except Exception as e:
        print("esuat", nume, url, e, file=sys.stderr)
