# 10 site-uri de nișă — portofoliu de vânzare

Zece site-uri complete, fiecare pe alt domeniu de activitate, plus o pagină-index de unde
se deschid toate. Ideea: trimiți clientului **un singur link**, el deschide exemplul din
domeniul lui, îl vede funcționând pe telefon și îți spune da sau nu. Fără prezentări lungi.

## Ce conține

| Folder | Nișă | Brand demo | Domeniu propus |
|---|---|---|---|
| `service-auto/` | Service auto | Motorline | motorline.ro |
| `instalator/` | Instalator / urgențe | AquaFix | aquafix.ro |
| `restaurant/` | Restaurant | Casa Verde | casaverde.ro |
| `magazin-haine/` | Magazin de haine | NORD Studio | nordstudio.ro |
| `cafenea/` | Cafenea | Bloom Coffee | bloomcoffee.ro |
| `mobila/` | Mobilă la comandă | LEMNA | lemna.ro |
| `constructii/` | Firmă de construcții | TERRA Construct | terraconstruct.ro |
| `avocat/` | Cabinet de avocatură | Ionescu & Asociații | ionescu-asociatii.ro |
| `stomatolog/` | Clinică stomatologică | Dental Nord | dentalnord.ro |
| `salon/` | Salon de înfrumusețare | LUMEN Beauty | lumenbeauty.ro |

`index.html` din rădăcină este pagina de portofoliu: cele 10 exemple, ce include fiecare
site, pachetele de preț, întrebări frecvente și butoanele de contact.

## Cum sunt construite

Fiecare site este **un singur fișier `index.html`**, cu CSS-ul și JS-ul incluse. Fără
framework, fără build, fără dependențe. Se copiază oriunde și funcționează.

Ce are fiecare:

- design mobile-first, testat de la 320 px în sus
- navigație lipită sus, buton de sunat / WhatsApp mereu la vedere
- secțiune de servicii cu prețuri reale, orientative
- formular de programare / cerere ofertă (momentan doar validare + mesaj de confirmare)
- program, adresă, spațiu pentru hartă
- meta tag-uri de SEO și date structurate `schema.org` pentru firme locale
- animații de apariție la scroll, dezactivate automat la `prefers-reduced-motion`
- fonturi Google, restul graficii din CSS — zero imagini de descărcat

## Publicare

Merge direct pe GitHub Pages, Netlify, Vercel sau orice găzduire clasică prin FTP.
Pentru GitHub Pages: Settings → Pages → branch-ul acesta, folder `/` (root).
Fișierul `.nojekyll` e deja adăugat.

Adresele vor fi de forma `.../service-auto/`, `.../instalator/` etc. Când un exemplu
devine site real, se mută folderul pe domeniul lui.

## De personalizat înainte de prima trimitere

1. **`index.html`, secțiunea contact** — numărul de WhatsApp e `40700000000`, pune-l pe al tău.
2. **`index.html`, secțiunea prețuri** — sumele (1.900 / 3.400 / 5.900 lei) sunt puse ca punct
   de plecare; ajustează-le cum vinzi tu.
3. **Datele de contact din exemple** — telefoanele, adresele și CUI-urile sunt fictive,
   inclusiv firmele. Dacă vrei să fii sigur că nimeni nu sună aiurea, lasă-le așa.

## Ce mai lipsește pentru un site livrat pe bune

- formularele trebuie legate la un serviciu de email (Formspree, Web3Forms, o funcție serverless)
- harta Google Maps se pune ca `iframe` în locul casetei gri
- pozele reale înlocuiesc plăcile colorate din galerii
- textele legale: termeni, confidențialitate, ANPC / SOL pentru magazine
