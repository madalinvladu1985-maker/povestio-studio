"""Povestio - generarea vocii. Furnizori: ElevenLabs (principal), Azure Speech (rezervă), fara (test)."""
import hashlib
import io
import os
import wave
from pathlib import Path

import numpy as np
import requests

SR = 24000

PRONUNTII_IMPLICITE = {
    "AtentAles.ro": "Atent Ales punct ro",
    "AtentAles": "Atent Ales",
}


class EroareVoce(Exception):
    pass


def pentru_voce(text, brand):
    """Înlocuiește cuvintele greu de citit (domenii, branduri) cu forma rostită.
    Textul de pe ecran și subtitrările rămân neschimbate."""
    p = dict(PRONUNTII_IMPLICITE)
    p.update(brand.get("pronuntii", {}))
    for cuv in sorted(p, key=len, reverse=True):
        text = text.replace(cuv, p[cuv])
    return text


def _cache(cache_dir, cheie):
    h = hashlib.sha1(cheie.encode("utf-8")).hexdigest()[:20]
    return Path(cache_dir) / f"voce_{h}.npy"


def elevenlabs(text, brand):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise EroareVoce("ELEVENLABS_API_KEY lipsește")
    cfg = brand.get("voce", {})
    voice_id = cfg.get("voce_id_clip") or os.environ.get("ELEVENLABS_VOICE_ID") or cfg.get("elevenlabs_voice_id")
    if not voice_id:
        raise EroareVoce("ELEVENLABS_VOICE_ID lipsește")
    model = cfg.get("elevenlabs_model", "eleven_flash_v2_5")
    body = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": cfg.get("stabilitate", 0.55),
            "similarity_boost": cfg.get("similaritate", 0.75),
            "style": cfg.get("stil", 0.15),
            "speed": cfg.get("viteza", 0.95),
        },
    }
    if "flash" in model or "turbo" in model:
        body["language_code"] = "ro"
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        params={"output_format": "pcm_24000"},
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json=body, timeout=90,
    )
    if r.status_code != 200:
        raise EroareVoce(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    return np.frombuffer(r.content, dtype=np.int16).copy()


def azure(text, brand):
    key = os.environ.get("AZURE_SPEECH_KEY")
    if not key:
        raise EroareVoce("AZURE_SPEECH_KEY lipsește")
    cfg = brand.get("voce", {})
    regiune = os.environ.get("AZURE_SPEECH_REGION", cfg.get("azure_regiune", "northeurope"))
    voce = cfg.get("azure_voce", "ro-RO-AlinaNeural")
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    ssml = (f'<speak version="1.0" xml:lang="ro-RO"><voice name="{voce}">'
            f'<prosody rate="{cfg.get("azure_viteza", "-6%")}">{esc}</prosody></voice></speak>')
    r = requests.post(
        f"https://{regiune}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml.encode("utf-8"), timeout=60,
        headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm", "User-Agent": "Povestio"},
    )
    if r.status_code != 200:
        raise EroareVoce(f"Azure {r.status_code}: {r.text[:300]}")
    with wave.open(io.BytesIO(r.content)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).copy()


def estimata(text, brand):
    """Pentru test fără voce: liniște cu durata estimată (2,3 cuvinte/s)."""
    return np.zeros(int(SR * max(1.2, len(text.split()) / 2.3)), dtype=np.int16)


FURNIZORI = {"elevenlabs": elevenlabs, "azure": azure, "fara": estimata}


def genereaza(text, brand, cache_dir, ordine=None):
    """Încearcă furnizorii în ordine; păstrează rezultatul în cache. Întoarce (samples, furnizor)."""
    rostit = pentru_voce(text, brand)
    ordine = ordine or brand.get("voce", {}).get("ordine", ["elevenlabs", "azure"])
    erori = []
    for nume in ordine:
        f = _cache(cache_dir, f"{nume}|{rostit}|{brand.get('voce', {})}")
        if f.exists():
            return np.load(f), nume
        try:
            s = FURNIZORI[nume](rostit, brand)
            if nume != "fara":
                np.save(f, s)
            return s, nume
        except EroareVoce as e:
            erori.append(str(e))
    raise EroareVoce("Niciun furnizor de voce nu a mers: " + " | ".join(erori))
