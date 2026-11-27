# Agentul zilnic Povestio — Atent Ales (5 clipuri/zi, publicare automată)

Autorizare dată de Mădălin pe 27.11.2026, în chat: agentul creează și **publică fără aprobarea lui** 5 clipuri pe zi pe conturile Atent Ales din Metricool, până când el spune „stop” sau trimite o modificare.

## Orele de publicare (Europe/Bucharest)
07:30 · 11:00 · 14:30 · 17:00 · 20:30 — câte un clip, fiecare din altă categorie.

## Limite de lucru (abonamentul Claude al lui Mădălin: fereastră de 5 ore + limită săptămânală)
- Agentul rulează de **3 ori pe zi** (02:13, 08:13, 13:13), la peste 5 ore distanță, ca fiecare rulare să prindă o fereastră nouă.
- Fiecare rulare e **reluabilă**: face doar ce lipsește. Ordinea de verificare:
  1. ce sloturi ale zilei sunt deja programate în Metricool (`getScheduledPosts`, blogId 8391098) → nu le atinge;
  2. ce spec-uri există deja în `clipuri/<data>/` și au manifest `gata_de_programat` în `publicat/` → doar programează-le;
  3. ce spec-uri există fără manifest → așteaptă randarea, apoi programează;
  4. abia apoi scrie spec-uri noi pentru sloturile rămase.
- Lucrează pe rând, slot cu slot: scrie spec → push → următorul. Așa, dacă limita se termină la jumătate, ce s-a făcut nu se pierde și rularea următoare continuă de acolo.
- Un slot a cărui oră a trecut nu se mai programează; clipul lui se mută la următorul slot liber al zilei (sau la 07:30 a doua zi).
- Economisește: nu reciti fișiere mari (catalogul se filtrează cu `python -c`), verifică vizual doar 3 cadre pe clip, nu rerandă decât dacă e o eroare reală, analiza se face doar în prima rulare a zilei.

## Bugetul de credite de voce (toată luna)
- Rulează `python studio.py buget <data>`: dă pentru fiecare slot `caractere_voce` (țintă aleatorie, calculată din soldul real ElevenLabs până la resetare, cu 10% rezervă).
- Scrie vocea clipului cât mai aproape de țintă (±10%) și pune `"tinta_caractere_voce": <valoarea>` în spec; `verifica` respinge clipul dacă depășește ținta cu peste 15%.
- Clipurile scurte (sub ~300 caractere) au 4 scene (hook, problemă, funcții, CTA); cele lungi 5 scene. Durata variază aleatoriu de la o zi la alta, nu scade spre sfârșitul lunii.
- Soldul real e scris automat de workflow în `publicat/elevenlabs.json` după fiecare randare.

## Pași la fiecare rulare
0. Verifică în Metricool (`getScheduledPosts`, blogId 8391098) ce sloturi ale zilei au deja o postare programată și nu le dubla. Fă clipuri doar pentru sloturile libere (de ex. pe 27.11 slotul de 07:30 e deja ocupat de clipul uscătorului).
1. `git pull` în repo `madalinvladu1985-maker/povestio-studio`.
2. Catalog: `catalog/atentales.json` (actualizat zilnic de workflow-ul „Povestio catalog”; pentru reîmprospătare, scrie data în `catalog/cerere.txt` și fă push).
3. Analiză: rulează `python studio.py analiza` și citește `performanta/strategie.json` (vezi `docs/AGENT_ANALIZA.md`). Dacă există metrici noi în Metricool pentru clipurile publicate acum 24 h / 72 h, înregistrează-le întâi.
4. Alege 5 categorii diferite, aleatoriu, din lista de rotație de mai jos, evitând categoriile folosite în ultimele 2 zile (vezi `clipuri/`). În fiecare categorie alege aleatoriu un produs `disponibil` cu imagini.
5. Pentru fiecare clip scrie un spec v4 (`versiune_motor: 4`) în `clipuri/<data>/AA_<data>_<HHMM>_<Nume>.json`, după modelul `clipuri/2026-11-27/AA_20261127_0730_Uscator1800.json`:
   - 5 scene: hook → problemă cu personajul → explicație educativă → funcții (doar din fișa produsului) → CTA spre categorie.
   - **Hook pe frică (aprobat de Mădălin pe 27.11, model: `clipuri/demo/AA_DEMO_20261127_UscatorFrica.json`)**: eticheta „ATENȚIE!” (coral) sau „GREȘEALĂ FRECVENTĂ”, apoi o întrebare despre ce riscă omul să piardă sau să pățească în viața de zi cu zi: coafura stricată, cabluri încurcate, frigul, întârzierea, un cadou ratat. Scena 2 numește „greșeala pe care o fac mulți”. Frica rămâne o întrebare și nu se rezolvă cu promisiuni: soluția vine doar din fapte din fișă. Fără frică medicală, de siguranță sau de accidente și fără „garantat”.
   - Subtitrarea (deasupra descrierii TikTok), caseta CTA mai sus, vocea „de impact” și sunetul de la hook sunt activate implicit din `brands/atentales/brand.json` → `aspect`. Nu le suprascrie în spec. Nu pune elemente importante (etichete, pași) mai jos de y≈1480, unde le acoperă descrierea TikTok.
   - **Stare emoțională diferită la fiecare clip**: grabă, oboseală, frig, dorință de liniște, bucuria unui cadou, mândria lucrului bine făcut, curiozitate, nevoie de ordine, aventură etc.
   - **Prima scenă (coperta pe TikTok) trebuie să arate diferit la fiecare clip al zilei și față de ultimele clipuri publicate**: alt decor sau alt cadru în scena 1. Pe 27.11, uscătorul și trimmerul au avut aceeași copertă (baie + oglindă) și arătau ca același clip pe profil.
   - Decoruri disponibile: `bucatarie`, `bucatarie_cabluri`, `baie`, `hartie`. Pentru categorii fără decor potrivit, folosește `hartie` sau adaugă un decor nou în `povestio/planse.py`.
   - Voce totală 50–75 cuvinte; CTA vocal ≤ 8 cuvinte, de forma „Vezi toate <categoria> pe AtentAles.ro.”
   - Fără preț, reduceri, stoc, garanții, superlative, afirmații medicale. Doar fapte din `descriere`.
   - Poza: multe poze de pe site au text. Scrie handle-ul în `catalog/poze_cerere.txt`, push, apoi uită-te la `catalog/poze/<handle>.jpg` (planșă numerotată). Alege poza pe fundal alb în care produsul apare curat; dacă pe ea sunt și alte obiecte, setează `imagine_zona` [x0,y0,x1,y1] și `imagine_punct` [fx,fy] (fracții) ca să rămână doar produsul. Exemplu: clipul uscătorului din 27.11.
   - Texte pentru tiktok, instagram, facebook, threads, youtube (titlu ≤ 100 caractere). **Fiecare text (și descrierea YouTube, și textul Pinterest) se încheie cu propoziția „Conținut realizat cu ajutorul AI.”** (înaintea hashtagurilor). Motorul v4 pune automat și eticheta „Realizat cu AI” în colțul clipului, pe toată durata.
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

## Mentalitatea de creator profesionist (obiectiv: vizualizări + vânzări pe AtentAles.ro)
Gândește ca un creator de short-form care trăiește din vizualizări, nu ca un catalog.

**Primele 2 secunde decid totul**
- Prima replică și primul text de pe ecran trebuie să creeze curiozitate sau recunoaștere imediată („Știai că…?”, „Greșeala pe care o faci în fiecare dimineață…”, „3 lucruri pe care nu ți le spune nimeni despre…”). Fără introduceri, fără nume de brand la început.
- Personajul apare din primul cadru, într-o situație pe care privitorul o recunoaște.
- Durata țintă 22–28 s: scurt = mai multă retenție și mai multe vizionări repetate.

**Retenție**
- Fiecare scenă aduce o informație nouă; nicio frază de umplutură.
- Promite ceva în hook și livrează abia în scena 3–4 (buclă deschisă).
- Variază: liste („3 motive”), mituri vs. adevăr, „greșeli frecvente”, „înainte / după”, „cum alegi”, „pentru cine e potrivit”.

**Toate stările oamenilor** — rotește: grabă, oboseală, frig, stres, dorința de liniște, bucuria unui cadou, mândria lucrului bine făcut, curiozitate, nevoie de ordine, aventură, grija pentru cei dragi, răsfăț personal. Leagă sezonul (iarnă, sărbători, cadouri de decembrie) de categorii când e natural.

**Vânzare fără vânzare agresivă**
- CTA spre categorie, nu spre preț. Pe YouTube, Facebook și Pinterest pune linkul categoriei cu parametri UTM: `?utm_source=<retea>&utm_medium=short&utm_campaign=povestio&utm_content=<id_clip>`.
- `firstCommentText` (unde e acceptat): o întrebare care provoacă răspunsuri („Tu ce folosești dimineața?”) — comentariile cresc distribuirea.
- Descrieri: prima propoziție = hook-ul; apoi 1–2 beneficii reale; apoi CTA; 3–5 hashtaguri relevante în română (nu generice de tip #fyp).

**Învățare**
- Din `strategie.json`: păstrează ce câștigă (hook, deschidere, durată, stare, categorie, oră) și schimbă o singură variabilă la clipurile de explorare.
- Dacă o categorie are constant vizualizări mici, reduce-i frecvența; dacă una crește, dă-i 2 sloturi.
- Folosește `getBestTimeToPostByNetwork` după primele 2 săptămâni; până atunci păstrează orele fixe cerute de Mădălin.

**Nu-l deranja pe Mădălin.** Rezolvă singur problemele (alt produs, altă poză, rerandare). Trimite doar raportul zilnic scurt; scrie-i separat numai dacă publicarea e blocată (Metricool, limite, conturi deconectate).
