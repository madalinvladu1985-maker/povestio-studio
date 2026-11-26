# Povestio – Agentul de publicare (rulează zilnic, după randare)

Misiunea: iei clipurile randate (`publicat/*.json` cu `status: "gata_de_programat"`) și le programezi în Metricool
pe toate rețelele brandului, la ora din `programare`. Apoi marchezi manifestul ca programat.

## Pași

1. `git pull`. Citește `brands/<brand>/brand.json` → `publicare` (blogId Metricool, rețele, etichete).
2. Pentru fiecare manifest cu `status: "gata_de_programat"` și data de azi sau din viitor:
   - verifică din nou textele cu regulile din `povestio/verificare.py` (fără prețuri, promisiuni, termeni medicali);
   - verifică în Shopify că produsul (`produs.handle`) e încă disponibil la vânzare; dacă nu, marchează `status: "anulat_stoc"` și nu programa;
   - programează cu `createScheduledPost` (Metricool), câte o postare cu toate rețelele:
     - `media`: [`video_url`]; `videoThumbnailUrl`: `coperta_url`;
     - `publicationDate`: data + ora din `programare`, fusul `Europe/Bucharest`;
     - TikTok: `tiktokData` cu `isAigc: true`, `commercialContentOwnBrand: true`, `privacyOption: "PUBLIC_TO_EVERYONE"`, `title` scurt; text = `platforme.tiktok.text`;
     - Instagram: `instagramData` cu `type: "REEL"`, `isAiGenerated: true`, `showReelOnFeed: true`; text = `platforme.instagram.text`;
     - Facebook: `facebookData` cu `type: "REEL"`; text = `platforme.facebook.text`;
     - YouTube: `youtubeData` cu `type: "short"`, `title` = `platforme.youtube.titlu`, `madeForKids: false`, `isAiGeneratedContent: true`, `privacy: "public"`, `tags`; text = `platforme.youtube.descriere`;
     - dacă rețelele au texte diferite, creează câte o postare pe rețea, cu textul ei.
   - notează în manifest: `status: "programat"`, `metricool` (plannerUrl-urile), `programat_la`.
3. Commit + push cu mesajul `Povestio: programare <data>`.
4. Rezumat pentru proprietar: ce s-a programat, unde și la ce oră; ce a fost respins sau anulat și de ce.

## Reguli

- Publici doar manifeste cu status `gata_de_programat`. Nu modifici textele decât ca să elimini o formulare interzisă.
- Dacă Metricool întoarce o eroare, nu reîncerca la nesfârșit: o singură reîncercare, apoi notează eroarea în manifest și în rezumat.
- Nu programa nimic în trecut.
