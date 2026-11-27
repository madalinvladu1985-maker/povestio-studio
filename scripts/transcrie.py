"""Transcrie vocea clipurilor (faster-whisper) ca să verificăm pronunția. Rulează în GitHub Actions.
Intrare: verificari/cerere_voce.txt (câte un URL de MP4 pe linie). Ieșire: verificari/voce_<nume>.txt"""
from pathlib import Path
import urllib.request
from faster_whisper import WhisperModel

RAD = Path(__file__).resolve().parent.parent
urls = [l.strip() for l in (RAD / "verificari/cerere_voce.txt").read_text().splitlines() if l.strip().startswith("http")]
m = WhisperModel("medium", device="cpu", compute_type="int8")
for u in urls:
    nume = u.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    f = Path("/tmp") / (nume + ".mp4"); urllib.request.urlretrieve(u, f)
    segs, _ = m.transcribe(str(f), language="ro", word_timestamps=True, vad_filter=False)
    rand = []
    for s in segs:
        rand.append(f"[{s.start:5.2f}-{s.end:5.2f}] {s.text.strip()}")
        rand.append("    " + " ".join(f"{w.word.strip()}({w.start:.2f},p={w.probability:.2f})" for w in s.words))
    (RAD / "verificari" / f"voce_{nume}.txt").write_text("\n".join(rand) + "\n", encoding="utf-8")
    print(nume, "ok")
