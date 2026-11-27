"""Analiza clipuri (ale noastre sau de referinta): transcriere voce + cadre + date audio. Ruleaza in GitHub Actions.
Intrare: verificari/cerere_voce.txt (cate un URL pe linie: MP4 direct sau link TikTok/YouTube).
Iesire: verificari/<nume>/transcriere.txt, cadre.jpg (planșă cu cadre la 1,5 s), info.txt"""
import json
import subprocess
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from PIL import Image, ImageDraw

RAD = Path(__file__).resolve().parent.parent
urls = [l.strip() for l in (RAD / "verificari/cerere_voce.txt").read_text().splitlines() if l.strip().startswith("http")]
m = WhisperModel("medium", device="cpu", compute_type="int8")
for u in urls:
    if "tiktok.com" in u or "youtube.com" in u or "youtu.be" in u:
        nume = "ref_" + u.split("/video/")[-1].split("?")[0] if "/video/" in u else "ref_" + str(abs(hash(u)))[:10]
        f = Path("/tmp") / f"{nume}.mp4"
        subprocess.run(["yt-dlp", "-f", "mp4/best", "-o", str(f), u], check=True)
    else:
        nume = u.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        f = Path("/tmp") / f"{nume}.mp4"
        subprocess.run(["curl", "-sL", "-o", str(f), u], check=True)
    out = RAD / "verificari" / nume; out.mkdir(parents=True, exist_ok=True)
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(f), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, info = m.transcribe(audio, language="ro", word_timestamps=True)
    rand = []
    for s in segs:
        rand.append(f"[{s.start:5.2f}-{s.end:5.2f}] {s.text.strip()}")
        rand.append("    " + " ".join(f"{w.word.strip()}({w.start:.2f},p={w.probability:.2f})" for w in s.words))
    (out / "transcriere.txt").write_text("\n".join(rand) + "\n", encoding="utf-8")
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(f)],
                                   capture_output=True, text=True).stdout)
    dur = float(pr["format"]["duration"])
    # volum pe secunde (ca să vedem muzică / pauze / ritm)
    sec = [float(np.sqrt(np.mean(audio[i:i + 16000] ** 2)) + 1e-9) for i in range(0, len(audio), 16000)]
    (out / "info.txt").write_text(json.dumps({"durata_s": dur, "video": [s for s in pr["streams"] if s["codec_type"] == "video"][0].get("width"),
                                              "inaltime": [s for s in pr["streams"] if s["codec_type"] == "video"][0].get("height"),
                                              "rms_db_pe_secunda": [round(20 * np.log10(x), 1) for x in sec]}, indent=1), encoding="utf-8")
    # planse cu cadre la fiecare 1,5 s (cate 12 pe planșă)
    ts = [round(x * 1.5, 1) for x in range(int(dur / 1.5) + 1)]
    cadre = []
    for t in ts:
        p = Path("/tmp") / f"{nume}_{t}.jpg"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", str(f), "-frames:v", "1", "-vf", "scale=270:-2", str(p)])
        if p.exists():
            im = Image.open(p).convert("RGB"); d = ImageDraw.Draw(im); d.rectangle([0, 0, 60, 22], fill="black"); d.text((4, 4), f"{t}s", fill="white")
            cadre.append(im)
    for k in range(0, len(cadre), 12):
        bucata = cadre[k:k + 12]; w, h = bucata[0].size
        pl = Image.new("RGB", (w * 6 + 25, h * 2 + 5), "white")
        for j, im in enumerate(bucata):
            pl.paste(im, ((j % 6) * (w + 5), (j // 6) * (h + 5)))
        pl.save(out / f"cadre_{k // 12 + 1}.jpg", quality=85)
    print(nume, "ok", dur)
