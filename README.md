# Povestio Studio

**Povești video care vând, cât tu bei cafeaua.**

Povestio este un agent care, în fiecare zi, fără intervenția ta:

1. alege 3 produse din magazinul Shopify;
2. scrie câte o mică poveste emoțională pentru fiecare (atmosferă → produs → CTA);
3. generează vocea în română (ElevenLabs, cu Azure ca rezervă) și montează clipuri verticale 9:16;
4. le programează pe TikTok, Instagram Reels, Facebook Reels și YouTube Shorts prin Metricool,
   cu titluri, descrieri, hashtaguri și etichetele cerute de platforme.

## Cum funcționează

```
Claude (agent conținut, 06:30)  ──►  clipuri/<data>/*.json  ──►  GitHub Actions (randare)
                                                                     │
                                                                     ▼
Claude (agent publicare, 08:00) ◄──  publicat/*.json + GitHub Release (MP4, copertă, SRT)
          │
          ▼
       Metricool  ──►  TikTok · Instagram · Facebook · YouTube  (la orele din brand.json)
```

## Structura

| Folder / fișier | Rol |
|---|---|
| `studio.py` | comanda principală: `verifica`, `render`, `batch`, `release` |
| `povestio/` | motorul: voce, montaj, teme, filtrul de siguranță, imagini Shopify, muzică originală |
| `brands/<brand>/brand.json` | profilul brandului: magazin, slogan, culori, voce, ore de publicare |
| `brands/<brand>/logo.png` | (opțional) logo-ul afișat la final |
| `broll/<tema>/*.mp4` | (opțional) clipuri reale de atmosferă; fără ele, atmosfera e animată din cod |
| `clipuri/<data>/*.json` | scenariile zilei (scrise de agentul de conținut) |
| `publicat/*.json` | manifestele: status, linkuri, texte pe platforme |
| `docs/` | instrucțiunile celor doi agenți |

## Configurare (o singură dată)

1. **Depozit GitHub public** cu acest conținut (Actions este gratuit pe depozitele publice).
2. **Settings → Secrets and variables → Actions**:
   - Secret `ELEVENLABS_API_KEY` – cheia API ElevenLabs;
   - Variabilă `ELEVENLABS_VOICE_ID` – vocea aleasă din ElevenLabs (Voice Library);
   - (rezervă) Secret `AZURE_SPEECH_KEY` și variabila `AZURE_SPEECH_REGION` = `northeurope`.
3. **Metricool**: brand „Atent Ales” cu rețelele conectate; `blogId` se completează în `brand.json`.
4. Agenții programați se creează din Claude.

## Test local

```
pip install -r requirements.txt
python studio.py verifica clipuri/2026-11-27/AA_20261127_1_Vlateo_Perie4in1.json
python studio.py render   clipuri/2026-11-27/AA_20261127_1_Vlateo_Perie4in1.json --fara-voce
```

## Siguranță

- Filtrul `povestio/verificare.py` respinge automat: prețuri, reduceri, „cumpără acum”, garanții, superlative
  și orice formulare medicală. Un clip respins nu se randează și nu se publică.
- Postările sunt marcate ca generate cu AI (TikTok, Instagram, YouTube) și, pe TikTok, ca conținut comercial al propriului brand.
- Muzica este compusă din cod (originală), fără probleme de drepturi.
- Cheile se păstrează doar în GitHub Secrets, niciodată în cod.

Fonturi: Crimson Text și Inter (SIL Open Font License, vezi `fonts/`).
