# Agentul zilnic Povestio — Atent Ales (5 clipuri/zi, publicare automată)

Autorizare dată de Mădălin pe 27.11.2026, în chat: agentul creează și **publică fără aprobarea lui** 5 clipuri pe zi pe conturile Atent Ales din Metricool, până când el spune „stop” sau trimite o modificare.

## Orele de publicare (Europe/Bucharest)
07:30 · 11:00 · 14:30 · 17:00 · 20:30 — câte un clip, fiecare din altă categorie.

## Pași la fiecare rulare
0. Verifică în Metricool (`getScheduledPosts`, blogId 8391098) ce sloturi ale zilei au deja o postare programată și nu le dubla. Fă clipuri doar pentru sloturile libere (de ex. pe 27.11 slotul de 07:30 e deja ocupat de clipul uscătorului).
1. `git pull` în repo `madalinvladu1985-maker/povestio-studio`.
2. Catalog: `catalog/atentales.json` (actualizat zilnic de workflow-ul „Povestio catalog”; pentru reîmprospătare, scrie data în `catalog/cerere.txt` și fă push).
3. Analiză: rulează `python studio.py analiza` și citește `performanta/strategie.json` (vezi `docs/AGENT_ANALIZA.md`). Dacă există metrici noi în Metricool pentru clipurile publicate acum 24 h / 72 h, înregistrează-le întâi.
4. Alege 5 categorii diferite, aleatoriu, din lista de rotație de mai jos, evitând categoriile folosite în ultimele 2 zile (vezi `clipuri/`). În fiecare categorie alege aleatoriu un produs `disponibil` cu imagini.
5. Pentru fiecare clip scrie un spec v4 (`versiune_motor: 4`) în `clipuri/<data>/AA_<data>_<HHMM>_<Nume>.json`, după modelul `clipuri/2026-11-27/AA_20261127_0730_Uscator1800.json`:
   - 5 scene: hook („Știai că…?” / „Uite N motive…” / „Hai să-ți arăt…” / întrebare) → problemă cu personajul → explicație educativă → funcții (doar din fișa produsului) → CTA spre categorie.
   - **Stare emoțională diferită la fiecare clip**: grabă, oboseală, frig, dorință de liniște, bucuria unui cadou, mândria lucrului bine făcut, curiozitate, nevoie de ordine, aventură etc.
   - Decoruri disponibile: `bucatarie`, `bucatarie_cabluri`, `baie`, `hartie`. Pentru categorii fără decor potrivit, folosește `hartie` sau adaugă un decor nou în `povestio/planse.py`.
   - Voce totală 50–75 cuvinte; CTA vocal ≤ 8 cuvinte, de forma „Vezi toate <categoria> pe AtentAles.ro.”
   - Fără preț, reduceri, stoc, garanții, superlative, afirmații medicale. Doar fapte din `descriere`.
   - Poza: multe poze de pe site au text. Scrie handle-ul în `catalog/poze_cerere.txt`, push, apoi uită-te la `catalog/poze/<handle>.jpg` (planșă numerotată). Alege poza pe fundal alb în care produsul apare curat; dacă pe ea sunt și alte obiecte, setează `imagine_zona` [x0,y0,x1,y1] și `imagine_punct` [fx,fy] (fracții) ca să rămână doar produsul. Exemplu: clipul uscătorului din 27.11.
   - Texte pentru tiktok, instagram, facebook, threads, youtube (titlu ≤ 100 caractere).
   - `varianta`: hook_tip, deschidere, mix_scene, categorie, stil, stare.
   - Rulează `python studio.py verifica <spec>`; corectează până trece.
6. Commit + push. Workflow-ul „Povestio - randare clipuri” randează cu vocea ElevenLabs și scrie `publicat/<id>.json` cu `video_url`, `coperta_url`.
7. Verifică fiecare clip: descarcă MP4 din release, extrage 4 cadre, verifică textul, poza produsului (fără text, fără alte obiecte) și durata (20–35 s). Dacă ceva e greșit, corectează spec-ul, șterge `publicat/<id>.json` și fă push ca să se rerandeze.
8. Publicare în Metricool, brandul **Atent Ales, blogId 8391098** (NU Vlateo 6257903): `createScheduledPost` la ora slotului, o singură postare pentru toate rețelele, cu:
   - `text` = textul pentru Instagram (≤ 500 caractere, ca să treacă și pe Threads);
   - `tiktokData.title` este obligatoriu (titlu scurt, ≤ 90 caractere);
   - `facebookData.title` = același titlu scurt;
   - fără `videoThumbnailUrl` (poate respinge toată postarea);
   - providers: tiktok, instagram (REEL), facebook (REEL), youtube (short, madeForKids false, category potrivită), threads.
   - **Pinterest, ca postare separată** la aceeași oră: același MP4, `pinterestData` cu `boardId` "267823577779759925" (panoul „Idei pentru casă”), `pinTitle` = titlul scurt, `pinLink` = URL-ul categoriei din CTA, `pinNewFormat` true, `isAiGenerated` true, `isAiGeneratedPerson` false; text ≤ 500 caractere, fără hashtaguri.
   - eticheta AI: `tiktokData.isAigc`, `instagramData.isAiGenerated`, `youtubeData.isAiGeneratedContent` = true; `tiktokData.commercialContentOwnBrand` = true.
   - `videoThumbnailUrl` = `coperta_url` doar acolo unde e acceptat.
   - Un slot deja trecut nu se programează în trecut: mută clipul la următorul slot liber al zilei.
9. Raport scurt către Mădălin (notificare): ce clipuri, ce categorii, ce ore, ce a reieșit din analiză.

## Dacă ceva nu merge
- Brandul Atent Ales nu există în Metricool: randează clipurile, nu publica pe alte branduri, anunță-l.
- Un clip pică verificarea sau randarea: nu-l publica, înlocuiește-l cu alt produs.
- Nu publica niciodată pe brandul Vlateo.

## Rotația categoriilor
par-perii-stylere, par-uscatoare, par-placi, par-ondulatoare, par-seturi, casa-cafea, casa-electrocasnice, casa-bucatarie-prize, electronice-prize, sport-outdoor-siguranta, sport-outdoor-camping, sport-outdoor-pescuit, confort-masaj, beauty-manichiura, beauty-epilare
