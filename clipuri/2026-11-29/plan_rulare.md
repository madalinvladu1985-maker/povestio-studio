# Plan 29.11 (scris la rularea de 28.11 13:13)

Creditele Figma s-au terminat după clipurile 07:30 și 11:00. Rularea de 02:13 continuă cu:

| Slot | Categorie | Produs (handle) | Voce | Hook | Protagonistă / decor scena 1 | Poza |
|---|---|---|---|---|---|---|
| 14:30 | beauty-epilare | trimmer-electric-2-in-1-pentru-femei-bikini-si-fata-reincarcabil | Charlotte | mit_adevar (petrecerea de Sf. Andrei) | ~28 ani, păr negru lung drept, halat lavandă; dormitor, rochie verde-smarald | poza 0, `imagine_zona` [0, 0.05, 0.5, 1] (fără cutie și capul rotund) |
| 17:00 | beauty-ingrijire-ten | aparat-de-masaj-facial-cu-role-360-si-microcurent | Aria | lista („3 reguli pentru ritualul de duminică seara”) | altă protagonistă; dormitor/măsuță cu lumânări | poza 0 (curată) |
| 20:30 | par-perii-stylere | styler-de-par-7-in-1-110-000-rpm-2-seruri | Sarah | mini_poveste (o oră până la petrecere) | altă protagonistă; hol / oglindă | poza 0, `imagine_zona` [0, 0.45, 0.95, 1] (fără cutie și seruri) |

Sfaturi trimmer (din fișă): fără apăsare, pe piele curată; capul potrivit zonei; după folosire clătești capul și îl lași să se usuce complet.
Sfaturi aparat facial (din fișă): pe piele curată; împreună cu serul sau crema obișnuită; după curățare îl pui pe bază, să se scurgă apa.
Sfaturi styler: începi cu treapta mică de temperatură (3 trepte); șuvițe subțiri; capul potrivit pentru bucle / drept / volum.
Aparatul de vidat și ser-ul Biotinix au fost excluse: toate pozele au alte obiecte sau text.

## Stare la 28.11 13:40
- 07:30 DistribuitorAuto (Lily) și 11:00 MicrofoaneLavaliera (Corina): randate, voce verificată, programate în Metricool (+ Pinterest).
- Ajutor: `python scripts/fac_spec.py scripts/clipuri_compacte/<fisier>.py` construiește spec-ul complet (texte, UTM, eticheta AI) dintr-un dict compact; vezi exemplele din `scripts/clipuri_compacte/`.
- Atenție la voce: scrie „întâi Decembrie” în `voce` (cifra „1” a fost citită „unie”) și pune `subtitlu` cu cifra; nu începe vocea cu „POV” (citit „Piovi”).
