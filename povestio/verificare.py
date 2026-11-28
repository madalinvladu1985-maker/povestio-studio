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


# Hashtaguri pe care TikTok le-a eliminat sau care sunt asociate frecvent cu conținut restricționat
# (masaj/spa/răsfăț sunt folosite pentru servicii pentru adulți și sunt filtrate). Se completează
# ori de câte ori o platformă elimină un hashtag (vezi docs/AGENT_ZILNIC.md).
HASHTAGURI_INTERZISE = {
    "rasfat", "rasfatat", "rasfataturi", "rasfatpersonal", "masaj", "masajrelaxant", "masaje", "massage",
    "spa", "spaacasa", "sexy", "hot", "body", "bodycare", "intim", "intime", "nud", "lenjerie",
    "slabire", "dieta", "detox", "fyp", "foryou", "foryoupage", "viral", "pentrutine", "xyzbca",
}
MAX_HASHTAGURI = 5


def verifica_hashtaguri(spec):
    erori = []
    for retea, d in spec.get("platforme", {}).items():
        if isinstance(d, str):
            d = {"text": d}
        txt = d.get("text", "") + " " + d.get("descriere", "")
        if re.search(r"#(\s|$)", txt):
            erori.append(f"{retea}: există un „#” gol în text.")
        tags = re.findall(r"#(\S+)", txt)
        for t in tags:
            curat = t.strip(".,!?;:").lower()
            if not re.fullmatch(r"[a-z0-9]+", curat):
                erori.append(f"{retea}: hashtagul #{t} are diacritice sau caractere speciale; folosește doar a-z și cifre.")
            elif curat in HASHTAGURI_INTERZISE:
                erori.append(f"{retea}: hashtagul #{curat} e pe lista neagră (eliminat/restricționat de platforme). Înlocuiește-l.")
        if len(tags) > MAX_HASHTAGURI:
            erori.append(f"{retea}: {len(tags)} hashtaguri; maximum {MAX_HASHTAGURI}.")
        for t in d.get("tags", []):
            if re.sub(r"\s", "", t.lower()) in HASHTAGURI_INTERZISE:
                erori.append(f"{retea}: eticheta „{t}” e pe lista neagră.")
    return erori


def verifica_v3(spec, brand):
    erori, avert = [], []
    sc = spec.get("scene", [])
    if len(sc) < 4:
        erori.append("Clipul v3 are nevoie de cel puțin 4 scene.")
    voce_tot = " ".join(s.get("voce", "") for s in sc)
    n = len(voce_tot.split())
    if n < 45 or n > 100:
        avert.append(f"Voiceover de {n} cuvinte (ținta v3: 55–90).")
    tinta = spec.get("tinta_caractere_voce")
    if tinta:
        from povestio.voce import pentru_voce
        car = sum(len(pentru_voce(s.get("voce", ""), brand)) for s in sc)
        if car > tinta * 1.15:
            erori.append(f"Vocea are {car} caractere, peste bugetul slotului ({tinta}, +15% toleranță). Scurtează textul.")
        elif car < tinta * 0.80:
            avert.append(f"Vocea are {car} caractere, mult sub ținta slotului ({tinta}).")
    if not sc or sc[-1].get("tip") != "cta":
        erori.append("Ultima scenă trebuie să fie CTA-ul.")
    elif len(sc[-1].get("voce", "").split()) > 8:
        erori.append("CTA-ul are mai mult de 8 cuvinte.")
    for i, s in enumerate(sc):
        if s.get("tip") == "video" and (not s.get("src") or "PLACEHOLDER" in s.get("src", "")):
            erori.append(f"Scena {i + 1}: lipsește clipul video (src).")
    p = spec.get("produs", {})
    if not p.get("decupaje") and not p.get("imagine_url"):
        erori.append("Lipsesc imaginile decupate ale produsului.")
    texte = [voce_tot] + [s.get("ecran", "") + " " + s.get("subtitlu", "") + " " + s.get("nota", "") + " " + s.get("bula", "") + " " + s.get("eticheta", "") + " " + " ".join([e if isinstance(e, str) else e.get("text", "") for e in s.get("etichete", [])] + s.get("pasi", [])) for s in sc]
    plat = spec.get("platforme", {})
    for k in ("tiktok", "instagram", "facebook"):
        if k in plat:
            texte.append(plat[k].get("text", ""))
            if len(plat[k].get("text", "")) > LIMITE[k]:
                erori.append(f"Textul pentru {k} depășește {LIMITE[k]} caractere.")
    yt = plat.get("youtube", {})
    if yt:
        texte += [yt.get("titlu", ""), yt.get("descriere", "")]
        if not yt.get("titlu") or len(yt.get("titlu", "")) > LIMITE["youtube_titlu"]:
            erori.append("Titlul YouTube lipsește sau depășește 100 de caractere.")
    erori += verifica_hashtaguri(spec)
    tot = "\n".join(texte)
    for t in _gaseste(INTERZISE_GENERAL, tot):
        erori.append(f"Formulare interzisă (vânzare agresivă/promisiune): {t}")
    if brand.get("fara_afirmatii_medicale", True):
        for t in _gaseste(INTERZISE_MEDICAL, tot):
            erori.append(f"Formulare cu caracter medical: {t}")
    return erori, avert


def verifica(spec, brand):
    if spec.get("versiune_motor") in (3, 4):
        return verifica_v3(spec, brand)
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
    if not p.get("handle") or not (p.get("imagini") or p.get("imagini_url")):
        erori.append("Lipsește produsul (handle/imagini).")
    return erori, avert
