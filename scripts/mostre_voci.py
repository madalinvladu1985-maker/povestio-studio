"""Genereaza aceeasi fraza in romana cu mai multe voci feminine ElevenLabs si le noteaza dupa transcriere (claritate)."""
import json, os, subprocess, urllib.request
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
K = os.environ["ELEVENLABS_API_KEY"]
VOCI = {"Corina (actuala)": "gbLy9ep70G3JW53cTzFC", "Sarah": "EXAVITQu4vr4xnSDxMaL", "Laura": "FGY2WhTYpPnrIDTdsKH5",
        "Alice": "Xb7hH8MSUJpSbSDYk0k2", "Matilda": "XrExE9yKIg1WjnnlVkGX", "Jessica": "cgSgspJ2msm6clMCkdW9",
        "Lily": "pFZP5JQG7iQjIQuC4Bku", "Charlotte": "XB0fDUnXU5powFXDhCwa", "Aria": "9BWtsMINqrJLrRacOk9x"}
TEXT = "Seara asta e doar despre tine. Lasă telefonul deoparte, aprinde o lumină caldă și fă-ți un ceai. Găsește aparate de masaj pe Atent Ales punct ro."
out = Path("verificari/mostre_voci"); out.mkdir(parents=True, exist_ok=True)
m = WhisperModel("medium", device="cpu", compute_type="int8")
rez = []
for nume, vid in VOCI.items():
    body = json.dumps({"text": TEXT, "model_id": "eleven_flash_v2_5", "language_code": "ro",
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.25, "speed": 1.0}}).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
                                   data=body, headers={"xi-api-key": K, "Content-Type": "application/json"}), timeout=60)
        f = out / (nume.split()[0].lower() + ".mp3"); f.write_bytes(r.read())
    except Exception as e:
        rez.append({"nume": nume, "id": vid, "eroare": str(e)}); continue
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(f), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(a, language="ro", word_timestamps=True)
    cuv = [w for s in segs for w in s.words]
    rez.append({"nume": nume, "id": vid, "fisier": f.name, "claritate": round(float(np.mean([w.probability for w in cuv])), 3),
                "transcriere": " ".join(w.word.strip() for w in cuv), "durata_s": round(len(a) / 16000, 1)})
    print(rez[-1])
(out / "rezultate.json").write_text(json.dumps(sorted(rez, key=lambda x: -x.get("claritate", 0)), ensure_ascii=False, indent=1))
