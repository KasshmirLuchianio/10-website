# Pipeline hero — Blender face mișcarea, AI-ul face imaginea

**Nu trebuie să știi Blender.** Nu deschizi interfața, nu atingi noduri, nu pui
lumini. Scripturile de aici construiesc singure scena. Tu rulezi o comandă și
primești fișiere.

Împărțirea muncii:

| Cine | Ce face | De ce |
|---|---|---|
| **Blender** | geometria, camera, mișcarea, timing-ul | e singurul care ține cadrele identice între ele |
| **Tu, în Higgsfield** | cum arată — material, lumină, atmosferă | e singurul care face imaginea să pară fotografie |

## Instalare, o singură dată

Descarci Blender de pe blender.org (gratuit) și îl instalezi. Atât. Nu îl
deschizi niciodată. Ca să poți scrie `blender` în terminal:

- **Windows**: adaugi `C:\Program Files\Blender Foundation\Blender 4.x` în PATH,
  sau folosești calea completă între ghilimele în loc de `blender`.
- **macOS**: `alias blender="/Applications/Blender.app/Contents/MacOS/Blender"`

## Pasul 1 — cadrul-ancoră (5 minute)

Scoți un singur cadru din mijlocul mișcării, la rezoluție dublă, randat frumos:

```bash
blender -b -P blender/service-auto_engine.py -- --still-only --engine cycles
```

Iese `render/service-auto/ancora_frame0062.png`. Ăsta e punctul tău de plecare.

## Pasul 2 — îl faci fotoreal (tu, în Higgsfield)

Duci cadrul în Nano Banana Pro și iterezi până arată exact cum vrei: metal uzat,
urme de ulei, lumină de atelier, praf, ce vrei tu. **Nu-ți pasă de mișcare aici**
— e o poză, ai voie să o refaci de douăzeci de ori.

Ce iese de aici e **referința de stil**. De ea depinde tot restul.

## Pasul 3 — secvența de mișcare (20-40 de minute de randare)

```bash
blender -b -P blender/service-auto_engine.py -a
```

Ies trei foldere:

- `beauty/` — randarea propriu-zisă, 90 de cadre. Asta e **driving video**-ul.
- `depth/` — harta de adâncime. Spune AI-ului ce e aproape și ce e departe.
- `normal/` — orientarea suprafețelor. Îl împiedică să-și inventeze altă geometrie.

Le lipești într-un mp4:

```bash
ffmpeg -framerate 30 -i render/service-auto/beauty/%04d.png -c:v libx264 -crf 16 drive.mp4
```

## Pasul 4 — video-to-video (tu, în Higgsfield)

Dai `drive.mp4` ca sursă și cadrul aprobat de la pasul 2 ca referință de stil.

**Regula de aur: promptul descrie doar materialul și lumina. Niciodată mișcarea.**
Dacă scrii „camera se apropie", modelul inventează propria apropiere peste a ta
și se bat cap în cap. Mișcarea vine din clip, aia e toată ideea.

Testează pe **10 cadre înainte să dai drumul la 90** — economisești credite și
afli din prima dacă rețeta ține.

## Pasul 5 — înapoi în site

```bash
ffmpeg -i final.mp4 -vsync 0 tmp/%04d.png
ffmpeg -i tmp/%04d.png -vf scale=1600:-1 -c:v libwebp -q:v 74 -compression_level 6 \
       service-auto/hero/frames/motor_%04d.webp
```

Ținta: **sub 4 MB pentru toată secvența**. Le copiezi în `<nișă>/hero/frames/` și
gata — pagina le găsește singură. Dacă lipsesc, site-ul rămâne un hero clasic și
nu se vede nimic stricat.

## Testul de acceptare

Înainte să pui cadrele în site: le deschizi în pagină și **derulezi foarte încet,
înainte și înapoi, de trei ori.** Dacă textura „fierbe" — dacă zgârieturile de pe
metal își schimbă poziția de la un cadru la altul — ai pierdut. Scazi puterea de
transformare în Higgsfield și reiei.

Un clip care arată impecabil la 30fps poate fi complet inutilizabil scrubuit.

## Opțional: HDRI

Dacă pui un fișier `.hdr` de atelier în `blender/hdri/` și îl dai scriptului,
metalul începe să reflecte un spațiu real în loc de un studio gol. E cel mai mare
salt de realism pentru cel mai mic efort — și înseamnă că AI-ul are mai puțin de
inventat, deci driftează mai puțin.

```bash
blender -b -P blender/service-auto_engine.py -a -- --hdri blender/hdri/atelier.hdr
```

HDRI-uri gratuite: polyhaven.com, categoria „indoor" sau „studio".

## Reguli care nu se negociază

- **Zero motion blur.** Cadrele se scrubuiesc; blurul la oprire arată ca o eroare.
- **Sampling fix, nu adaptiv.** Diferența de zgomot între cadre se citește ca palpăire.
- **Camera se mișcă puțin.** Peste ~25° de rotație, creierul citește „video" în loc
  de „controlez eu". Un travelling scurt bate un orbit spectaculos.
- **Fundal transparent.** Culoarea o pune CSS-ul, ca să vinzi același hero la trei
  clienți cu trei culori de brand, fără să re-randezi.

## Cadre de test

`_testframes.py` generează o secvență de verificare cu aceeași coregrafie, fără
Blender și fără AI, ca să testezi scroll-ul și greutatea paginii. Nu e artă finală.

```bash
python3 blender/_testframes.py
```
