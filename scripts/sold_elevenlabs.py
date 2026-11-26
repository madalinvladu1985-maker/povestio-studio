"""Scrie soldul de caractere ElevenLabs in publicat/elevenlabs.json (fara cheie in fisier)."""
import json, os, urllib.request
from pathlib import Path
k = os.environ.get("ELEVENLABS_API_KEY")
if not k:
    raise SystemExit("fara cheie")
r = urllib.request.urlopen(urllib.request.Request("https://api.elevenlabs.io/v1/user/subscription",
                                                  headers={"xi-api-key": k}), timeout=30)
d = json.load(r)
keep = {x: d.get(x) for x in ("tier", "character_count", "character_limit", "next_character_count_reset_unix", "status")}
Path("publicat").mkdir(exist_ok=True)
Path("publicat/elevenlabs.json").write_text(json.dumps(keep, indent=1))
print(keep)
