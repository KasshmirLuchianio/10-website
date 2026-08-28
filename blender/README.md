# Pipeline hero hypermotion — Blender → site

Fiecare hero e o **secvență de cadre randate în Blender**, redate pe un canvas
legat de scroll. Nu e video și nu e 3D în browser: sunt imagini, iar degetul
utilizatorului decide ce cadru se vede. De aceea merge identic pe orice telefon
și se poate derula înainte și înapoi fără sacadare.

## Pașii

**1. Randezi scena**

```bash
blender -b -P blender/service-auto_engine.py -a
# sau cu parametri:
blender -b -P blender/service-auto_engine.py -a -- --out //render/motor/ --frames 90
```

Scriptul construiește scena de la zero de fiecare dată — nu ai nevoie de niciun
`.blend` pregătit. Ies 90 de PNG-uri cu alpha, 1600×1000.

**2. Le encodezi pentru web**

```bash
ffmpeg -i render/motor/%04d.png -vf scale=1600:-1 \
       -c:v libwebp -q:v 74 -compression_level 6 \
       service-auto/hero/frames/motor_%04d.webp
```

Ținta: **sub 4 MB pentru toată secvența**. Dacă depășești, scazi întâi
rezoluția, apoi calitatea, și abia la final numărul de cadre — sub 60 de cadre
se vede saltul la scroll lent.

**3. Le pui în site**

Le copiezi în `<nișă>/hero/frames/`. Atât. Player-ul din pagină verifică singur
dacă primul cadru există: dacă da, pornește heroul cu scroll; dacă nu, pagina
rămâne un hero clasic și nu se vede nimic stricat.

## Pasul opțional: fotoreal prin Higgsfield

Randarea din Blender e curată, dar e evident CGI. Pentru clienții premium,
treci secvența prin **video-to-video**, unde mișcarea din clipul-sursă e
păstrată și doar aspectul se schimbă:

1. Lipești cadrele într-un mp4: `ffmpeg -framerate 30 -i %04d.png -c:v libx264 -crf 16 drive.mp4`
2. Îl dai ca driving video în Kling O1 Edit sau Seedance (skill-urile `kling-o1-edit`,
   `seedance-footage-vfx`), cu prompt de material și lumină — nu de mișcare.
   Mișcarea vine din Blender, aia e ideea.
3. Extragi cadrele înapoi: `ffmpeg -i out.mp4 -vsync 0 %04d.png` și reiei pasul 2 de sus.

Verifică la scrub lent: dacă apar palpăiri de textură între cadre vecine, scazi
denoise-ul sau crești numărul de pași. Un video care arată bine la 30fps poate
fi inutilizabil scrubuit cadru cu cadru.

## Reguli care nu se negociază

- **Zero motion blur.** Cadrele se scrubuiesc; blurul la oprire arată ca o eroare.
- **Sampling fix, nu adaptiv.** Diferența de zgomot între cadre se citește ca palpăire.
- **Camera se mișcă puțin.** Peste ~25° de rotație, creierul citește „video" în loc
  de „controlez eu". Un travelling scurt bate un orbit spectaculos.
- **Fundal transparent.** Culoarea o pune CSS-ul, ca să o poți schimba pe fiecare
  client fără să re-randezi.

## Cadre de test

`_testframes.py` generează o secvență de verificare cu aceeași coregrafie, ca să
poți testa scroll-ul, încadrarea și greutatea paginii înainte să pornești Blender.
Nu e artă finală — o suprascrii cu randările reale.

```bash
python3 blender/_testframes.py
```
