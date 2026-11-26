# Agentul de analiză Povestio

Rol: după fiecare postare, măsoară cum a reacționat publicul și ajustează rețeta clipurilor următoare, până găsește un stil care trece constant de ținta de vizualizări.

## Ținte în trepte

| Treaptă | Țintă / clip | Când se consideră atinsă |
|---|---|---|
| 1 | 5.000 | cel puțin 3 din ultimele 6 clipuri măsurate la 72 h |
| 2 | 10.000 | aceeași regulă |
| 3 | 20.000 | aceeași regulă |
| 4 | 50.000 | aceeași regulă |
| 5 | 100.000 | aceeași regulă |

Când treapta e atinsă, ținta urcă automat în `performanta/strategie.json`. Ciclul de testare continuă la fel, doar pragul crește.

## Când rulează

Zilnic, la 09:00 (Europe/Bucharest), înaintea agentului de conținut.

1. Ia din Metricool postările din ultimele 4 zile (`getScheduledPosts` / `getAnalyticsDataByMetrics`) pentru TikTok, Instagram, Facebook, YouTube.
2. Pentru fiecare clip publicat acum 24 h și acum 72 h scrie o măsurătoare:

```json
{
  "clip_id": "AA_20261127_2_ATOMKIT_OneZ",
  "retea": "tiktok",
  "ora_postare": "2026-11-27 17:00",
  "ore_de_la_postare": 72,
  "vizualizari": 0,
  "retentie_pct": 0,
  "aprecieri": 0, "comentarii": 0, "distribuiri": 0, "salvari": 0,
  "varianta": { "...": "copiată din spec-ul clipului" }
}
```

   Câmpurile pe care rețeaua nu le oferă rămân 0 sau lipsesc. Nu se estimează nimic.
3. Salvează lista în `performanta/metrici/<data>.json` și rulează:
   `python studio.py analiza inregistreaza performanta/metrici/<data>.json`
4. Face commit cu `performanta/` și pune în raportul zilei rezultatul comenzii.

## Ce variabile se testează

Fiecare spec v3 are câmpul `varianta`:

| Câmp | Valori |
|---|---|
| `hook_tip` | `stiai_ca`, `motive`, `hai_sa_arat`, `intrebare`, `pov_problema` |
| `deschidere` | `personaj_problema`, `detaliu_macro`, `text_soc`, `inainte_dupa` |
| `mix_scene` | `video_greu`, `echilibrat`, `produs_greu` |
| `durata_s` | durata reală a clipului (grupată 20-25 / 25-30 / 30-35) |
| `ora` | ora postării |
| `categorie` | handle-ul colecției din CTA |

## Regulile de decizie

- O valoare se compară doar după ce are cel puțin 3 clipuri măsurate la 72 h.
- Se compară mediana vizualizărilor, nu media, ca un singur clip viral să nu strice concluzia.
- Diferență sub 20% între primele două valori: rezultat neconcludent, testul continuă.
- Mix zilnic: 2 clipuri de **exploatare** (folosesc valorile câștigătoare) și 1 clip de **explorare** (schimbă o singură variabilă față de câștigător).
- Se schimbă o singură variabilă pe clipul de explorare, altfel nu se știe ce a produs diferența.
- Retenția mică (sub ~30% pe Reels) indică un început slab: agentul schimbă întâi `deschidere` și `hook_tip`.
- Multe vizualizări cu interacțiuni puține indică un mesaj slab: se schimbă textele motivelor, nu deschiderea.

## Ce nu are voie să facă

- Să înlocuiască regulile de conținut: fără prețuri, fără promisiuni, fără afirmații medicale, eticheta AI rămâne activă.
- Să cumpere reclame sau să boosteze postări fără acordul lui Mădălin.
- Să șteargă postări care merg slab.
