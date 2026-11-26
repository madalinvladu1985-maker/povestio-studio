"""Povestio - filtrul de siguranță: verifică scenariul și textele înainte de randare și publicare.
O eroare oprește clipul (nu se publică). Un avertisment se notează în manifest."""
import re

INTERZISE_GENERAL = [
    r"\bcump[aă]r[aă] acum\b", r"\bultimele buc[aă]ți\b", r"\bstoc limitat\b", r"\bgarantat\b",
    r"\bgaran[tț]ie\b", r"\b\d+[.,]?\d*\s?(lei|ron|€|eur)\b", r"\breducere\b", r"\bpromo[tț]ie\b",
    r"\b100\s?%", r"\bcel mai bun\b", r"\bnr\.?\s?1\b",
]
INTERZISE_MEDICAL = [
    r"\bvindec", r"\btrateaz", r"\btratament", r"\belimin[aă] durerea\b", r"\bdurere", r"\bboal",
    r"\bterapie\b", r"\bterapeutic", r"\bmedical", r"\bdiagnost", r"\bremediu\b", r"\bsciatic",
    r"\bhernie\b", r"\bartrit", r"\breumatism", r"\binflama",
]
LIMITE = {
    "tiktok": 2200,
    "instagram": 2200,
    "facebook": 2200,
    "youtube_titlu": 100,
    "youtube_descriere": 5000,
}


def _gaseste(tipare, text):
    return [t for t in tipare if re.search(t, text, flags=re.IGNORECASE)]


def verifica(spec, brand):
    erori, avert = [], []
    replici = spec.get("replici", [])
    if not replici:
        erori.append("Clipul nu are replici.")
    voce = " ".join(r["text"] for r in replici)
    cuvinte = len(voce.split())
    if cuvinte < 35 or cuvinte > 75:
        avert.append(f"Voiceover de {cuvinte} cuvinte (ținta: 45–65).")
    finale = [r for r in replici if r.get("scena") == "final"]
    if len(finale) != 1:
        erori.append("Trebuie exact o replică finală (CTA).")
    elif len(finale[0]["text"].split()) > 8:
        erori.append("CTA-ul are mai mult de 8 cuvinte.")
    if not any(r.get("scena") == "produs" for r in replici):
        erori.append("Lipsește replica despre produs.")
    if sum(1 for r in replici if r.get("scena", "atmosfera") == "atmosfera") < 2:
        avert.append("Atmosfera are mai puțin de 2 replici.")

    toate = [voce]
    plat = spec.get("platforme", {})
    for k in ("tiktok", "instagram", "facebook"):
        if k in plat:
            toate.append(plat[k].get("text", ""))
            if len(plat[k].get("text", "")) > LIMITE[k]:
                erori.append(f"Textul pentru {k} depășește {LIMITE[k]} caractere.")
    yt = plat.get("youtube", {})
    if yt:
        toate += [yt.get("titlu", ""), yt.get("descriere", "")]
        if not yt.get("titlu"):
            erori.append("Lipsește titlul YouTube.")
        if len(yt.get("titlu", "")) > LIMITE["youtube_titlu"]:
            erori.append("Titlul YouTube depășește 100 de caractere.")
    text_total = "\n".join(toate)

    for t in _gaseste(INTERZISE_GENERAL, text_total):
        erori.append(f"Formulare interzisă (vânzare agresivă/promisiune): {t}")
    if brand.get("fara_afirmatii_medicale", True):
        for t in _gaseste(INTERZISE_MEDICAL, text_total):
            erori.append(f"Formulare cu caracter medical: {t}")
    for t in brand.get("cuvinte_interzise", []):
        if re.search(t, text_total, flags=re.IGNORECASE):
            erori.append(f"Cuvânt interzis de brand: {t}")

    p = spec.get("produs", {})
    if not p.get("handle") or not p.get("imagini"):
        erori.append("Lipsește produsul (handle/imagini).")
    return erori, avert
