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
5. Pentru fiecare clip scrie un spec v4 (`versiune_motor: 4`) în `clipuri/<data>/AA_<data>_<HHMM>_<Nume>.json`.
   **STILUL STANDARD (aprobat de Mădălin pe 27.11): „poveste ilustrată în mișcare” + discursul educativ.** Model obligatoriu: `clipuri/demo/AA_DEMO_20261127_PerieIndreptat.json`. Vizual ca în clipul de referință @klastep (analizat în `verificari/ref_7711755734429469974/`): un singur personaj într-o singură poveste, ilustrații 2D care se mișcă (cameră + mici animații), etichete-card, pași numerotați, final cu brandul. Discursul rămâne al nostru: hook pe frică, greșeli/sfaturi, produsul doar la final, CTA legat de sfat, logo.
   - **Durată 35–40 s**: 6 scene + încheierea cu logo (automată). Vocea ~440–540 de caractere (respectă `tinta_caractere_voce` din `studio.py buget`).
   - **Scenele:**
     1. **Hook — DIFERIT la fiecare clip** (actualizat de Mădălin pe 27.11: nu folosi „Atenție” la clipuri consecutive și nu folosi hook-ul pe frică la rând; ideal fiecare clip din zi are alt tip de hook). Rotește între: întrebare sezonieră („Vine 1 Decembrie și grătarul e la tine?”), POV / self-care („Zece minute doar pentru tine.”), curiozitate („Secretul unui … care ține toată ziua”), mit vs adevăr („Credeai că … ? Nu chiar.”), listă („3 lucruri pe care le fac femeile organizate seara”), mini-poveste („Ana avea 15 minute până la ședință…”), întrebare directă („Și tu ai …?”), frică/greșeală (cel mult 1 clip pe zi). Personajul apare din primul cadru, într-un loc din viața reală. `efect: "intrebari"` doar la hook-urile-întrebare.
     2–4. **Câte un pas, sfat sau greșeală pe scenă**: eticheta variază după hook („PASUL 1/2/3”, „SFATUL 1”, „MIT” / „ADEVĂR”, „GREȘEALA 1”) în culori diferite (coral / albastru / teal). Titlu scurt cu marcaj galben + 1–2 etichete sus, la y≈500 și y≈620 (de exemplu „NU: …” albă și „DA: …” galbenă). Ilustrația arată personajul exact în acel moment. Produsul NU apare.
     5. **Rezumat** (eticheta „REȚINE”): ecran „Salvează clipul *pentru …*” sau „Trimite clipul *prietenei tale*” (alternează: salvările și distribuirile cresc reach-ul), `pasi` cu 3 cuvinte scurte (fără săgeți „→”, fontul nu le are), ilustrație cu personajul mulțumit, `efect: "sclipiri"`.
     6. **CTA** pe `decor: "hartie"`: poza reală a produsului + caseta CTA. CTA vocal ≤ 8 cuvinte, legat de sfat și de un fapt din fișă: „Găsește perii cu 14 trepte pe AtentAles.ro.” Numerele din CTA se scriu în litere în `voce` și în cifre în `subtitlu`.
   - **Publicul țintă: femei 25–45 de ani.** Gândește ca o creatoare care vorbește cu prietena ei: cald, direct („tu”), practic, fără ton de reclamă. Teme care prind: timp pentru tine, casă frumoasă și organizată, păr și îngrijire, gazdă relaxată, cadouri, ritualuri de dimineață și de seară, sezon (1 Decembrie, Crăciun, iarnă). Personajul principal e de obicei o femeie (vârste, coafuri, stiluri diferite de la clip la clip). Pe ecran și în descrieri: emoji cu măsură (1–2), întrebări care cer comentarii, îndemn la salvare sau trimitere.
   - **Vocea: altă voce feminină la fiecare clip.** Pune în spec `voce_id` din `brands/atentales/brand.json` → `voce.voci_feminine` (Corina, Jessica, Charlotte, Lily, Aria, Sarah), prin rotație, fără aceeași voce la două clipuri la rând (verifică ultimele clipuri din `clipuri/`). Toate au fost testate în română pe 27.11 (`verificari/mostre_voci/rezultate.json`).
   - **Mișcare**: fiecare scenă are `camera` cu `de`/`la` = [centru_x, centru_y, zoom], fracții din cadru, zoom între 1.0 și 1.3. Alternează apropierea cu depărtarea și ușoare deplasări laterale, ca la un desen animat filmat. `efect` (cel mult unul pe scenă): `intrebari` (hook), `picaturi` (apă/umezeală/ploaie), `sclipiri` (rezultat bun). `efect_poz` = [x, y] în pixeli pe cadrul de 1080×1920.
   - **Ilustrații AI** (aceeași persoană în tot clipul, alt personaj la fiecare clip, potrivit categoriei):
     - Stil fix în prompt: „A flat vector 2D animation-style illustration with soft gradients, in a warm palette of cream, teal, coral and soft pink… [personajul descris identic în toate scenele, cu aceleași haine]… She/He is in the lower half of the frame; the top third is a calm plain cream wall/sky with nothing on it, leaving space for a title. Vertical 9:16 composition. No text, no letters, no logos, no watermark.” Fără produse de brand în ilustrații: obiectele sunt generice („a plain unbranded …”).
     - **Prima opțiune: Gemini (Nano Banana), plătit din creditele Google AI Pro ale lui Mădălin (10 $/lună în Google Cloud).** Dacă secretul `GEMINI_API_KEY` există în GitHub: pune în fiecare scenă `ilustratie` (promptul, fără descrierea personajului), în spec `personaj_ai` (descrierea protagonistei, identică pentru tot clipul) și în `aspect` `{"fundal_ai": {"furnizor": "gemini", "model": "gemini-2.5-flash-image"}}` (modelul se poate schimba pe `gemini-nano-banana-2.1` după primul test, dacă e disponibil, pentru că e mai ieftin). Prima ilustrație cu protagonista devine automat referința pentru celelalte scene, ca să fie aceeași persoană. La scenele fără protagonistă pune `"fara_personaj": true`. Nu mai ai nevoie de Figma.
     - **A doua opțiune: dacă secretul `FAL_KEY` există** (după ce Mădălin îl adaugă): pune în fiecare scenă `ilustratie` (promptul) și în `aspect` `{"fundal_ai": {"model": "fal-ai/flux/schnell", "seed": <număr>}}` (modelul se poate schimba după primul test). Motorul le generează la randare.
     - **Dacă nu există nici `GEMINI_API_KEY`, nici `FAL_KEY`**: generează ilustrațiile cu Figma (`generate_image`, fișierul `2E6Xo9Rx3joDAQ27LGVPcl`, modelul `gemini-3.1-flash-lite-image`, 1080×1920), câte 4–5 pe clip (o ilustrație poate servi la două scene, cu altă `camera`). Pune URL-ul primit în `ilustratie_url`, iar în `aspect` `{"fundal_ai": {"model": "figma"}}`. URL-urile Figma expiră în 7 zile, deci clipul se randează în aceeași zi.
     - Dacă generarea nu merge (lipsă credite, eroare): clipul iese cu decorurile din cod (`baie`, `bucatarie`, `sufragerie`, `terasa`, `hartie`) și personajul desenat, iar Mădălin primește o singură notificare în raportul zilei.
     - Verifică fiecare ilustrație: fără text, fără logouri, mâini și față normale, același personaj. Altfel o regenerezi o dată.
   - **Vocea**: nu coborî `stabilitate` sub 0.5 (la 0.32 vocea a scos cuvinte fără sens). După randare, pune URL-urile MP4 în `verificari/cerere_voce.txt` și fă push. Workflow-ul „Povestio - verificare voce” scrie transcrierea în `verificari/<id>/transcriere.txt`. Dacă transcrierea are cuvinte fără sens față de text, șterge `publicat/<id>.json` și rerandează cu o formulare mai simplă.
   - Sfaturile sunt de bun-simț, general cunoscute și verificabile. Nicio afirmație medicală, de siguranță, de sănătate sau „științifică” fără sursă. Dacă nu ești sigur că un sfat e corect, nu-l folosi.
   - Despre produs, doar fapte din fișă. Caracteristica pomenită în CTA trebuie să răspundă unui sfat din clip; dacă fișa nu are una potrivită, CTA-ul devine „Vezi toate <categoria> pe AtentAles.ro.”
   - În descrieri: prima propoziție = hook-ul; apoi cele 3 sfaturi pe scurt; apoi CTA-ul. `firstCommentText` = întrebare despre obiceiul lor („Tu care dintre greșeli o faci?”).
   - `varianta.stil` = `poveste_ilustrata`; `mix_scene` = `ilustratii_miscatoare`; `hook_tip` = `frica_lista` sau `frica_greseala`.
   - **Încheiere cu logoul**: motorul adaugă automat ~2,2 s cu logoul Atent Ales și sloganul „Produse atent alese pentru casa ta.” Nu-l adăuga în spec.
   - Subtitrarea (deasupra descrierii TikTok), caseta CTA mai sus, vocea „de impact” și sunetul de la hook sunt activate implicit din `brands/atentales/brand.json` → `aspect`. Nu le suprascrie în spec. Nu pune elemente importante (etichete, pași) mai jos de y≈1480, unde le acoperă descrierea TikTok.
   - **Stare emoțională diferită la fiecare clip**: grabă, oboseală, frig, dorință de liniște, bucuria unui cadou, mândria lucrului bine făcut, curiozitate, nevoie de ordine, aventură etc.
   - **Prima scenă (coperta pe TikTok) trebuie să arate diferit la fiecare clip al zilei și față de ultimele clipuri publicate**: alt decor sau alt cadru în scena 1. Pe 27.11, uscătorul și trimmerul au avut aceeași copertă (baie + oglindă) și arătau ca același clip pe profil.
   - Decoruri disponibile: `bucatarie`, `bucatarie_cabluri`, `baie`, `hartie`. Pentru categorii fără decor potrivit, folosește `hartie` sau adaugă un decor nou în `povestio/planse.py`.
   - Voce totală 50–75 cuvinte (respectă `tinta_caractere_voce`); CTA vocal ≤ 8 cuvinte.
   - Fără preț, reduceri, stoc, garanții, superlative, afirmații medicale. Despre produs, doar fapte din `descriere`.
   - Poza: multe poze de pe site au text. Scrie handle-ul în `catalog/poze_cerere.txt`, push, apoi uită-te la `catalog/poze/<handle>.jpg` (planșă numerotată). Alege poza pe fundal alb în care produsul apare curat; dacă pe ea sunt și alte obiecte, setează `imagine_zona` [x0,y0,x1,y1] și `imagine_punct` [fx,fy] (fracții) ca să rămână doar produsul. Exemplu: clipul uscătorului din 27.11.
   - Texte pentru tiktok, instagram, facebook, threads, youtube (titlu ≤ 100 caractere). **Fiecare text (și descrierea YouTube, și textul Pinterest) se încheie cu propoziția „Conținut realizat cu ajutorul AI.”** (înaintea hashtagurilor). Motorul v4 pune automat și eticheta „Realizat cu AI” în colțul clipului, pe toată durata.
   - `varianta`: hook_tip, deschidere, mix_scene, categorie, stil, stare.
   - Rulează `python studio.py verifica <spec>`; corectează până trece.
6. Commit + push. Workflow-ul „Povestio - randare clipuri” randează cu vocea ElevenLabs și scrie `publicat/<id>.json` cu `video_url`, `coperta_url`.
7. Verifică fiecare clip: descarcă MP4 din release, extrage 4 cadre, verifică textul, poza produsului (fără text, fără alte obiecte), ilustrațiile și durata (35–40 s); verifică vocea prin transcriere (pasul 5). Dacă ceva e greșit, corectează spec-ul, șterge `publicat/<id>.json` și fă push ca să se rerandeze.
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
- Durata țintă 35–40 s (aprobat de Mădălin pe 27.11), cu o informație nouă la fiecare 5–6 s, ca retenția să nu scadă.

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
