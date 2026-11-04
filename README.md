# Horse.uk s.r.o. — webový maketu

Prémiový vizuálny maketu verejného webu a admin UI v slovenčine. **Bez backendu** — žiadne falošné ceny, adresy, mená zamestnancov, diplomy, recenzie ani právne firemné údaje. Všetok obsah je editovateľný placeholder.

## Stack (táto fáza)

- Statické **HTML / CSS / JS** (bez build kroku)
- Fonty: [Cormorant Garamond](https://fonts.google.com/specimen/Cormorant+Garamond) + [Outfit](https://fonts.google.com/specimen/Outfit)
- Štruktúra URL pripravená na Apache / FORPSI (`DirectoryIndex`, `.htaccess` stub)
- `lang="sk"` + komentáre / admin texty pripravené na budúce **RU / EN** (i18n)

## Ako spustiť lokálne

```bash
# z koreňa repozitára
python3 -m http.server 8080
# alebo
npx --yes serve -p 8080
```

Otvorte [http://localhost:8080](http://localhost:8080).

## GitHub Pages (náhľad)

Cieľová URL projektu: [https://nexoraads111-cloud.github.io/horse-uk.sk/](https://nexoraads111-cloud.github.io/horse-uk.sk/)

Zapnutie (vyžaduje admin práva na repo — Settings → Pages):

1. **Source:** Deploy from a branch → Branch `main` → folder `/` (root), Save  
   **alebo** Source: **GitHub Actions** (workflow `.github/workflows/pages.yml`).
2. Počkajte na zelený deploy; potom otvorte URL vyššie.

Odkazy v HTML sú relatívne (fungujú pod `/horse-uk.sk/`). `site.js` doplní trailing slash na project Pages, aby sa nerozbili assety.

| Cesta | Stránka |
|-------|---------|
| `/` | Domov |
| `/sluzby/` | Služby (vzorky) |
| `/tim/` | Tím (prázdne sloty rolí) |
| `/objednat/` | Rezervačný formulár (client-side validácia) |
| `/pravne/...` | Právne shelly |
| `/admin/` | Login + dashboard shelly |

## Čo je maketu vs. budúci backend

| Maketu (teraz) | Budúci FORPSI (PHP / MySQL) |
|----------------|-----------------------------|
| Statické stránky a UI shelly | `index.php`, šablóny, includes |
| Rezervácia: validácia + success UI | Zápis do DB, e-mail, sloty z adminu |
| Admin: navigovateľný shell, disabled write | Session auth, CRUD, upload médií |
| Žiadne verejné write API | Chránené admin endpointy |
| Placeholdery textov / kontaktov | Tabuľky `pages`, `services`, `team`, `contacts` |
| Štatistiky bez čísel | Reálne metriky / analytika |

Odporúčaná cesta: zachovať HTML štruktúru a postupne nahradiť obsah PHP partials + MySQL, hostované na FORPSI.

## SEO (základ)

- `<title>` + meta description na verejných stránkach
- Čisté URL (priečinky + `index.html`)
- `robots.txt` (admin `Disallow`)
- `sitemap.xml` stub (doména `https://horse-uk.sk` — upravte podľa finálnej domény)

## Obsah a fotografie

Verejné stránky majú slovenské texty o starostlivosti o zdravie koní (bez cien, falošných licencií, recenzií a medicínskych garancií). Fotografie sú v `assets/img/photos/`. Tím obsahuje iba role a neutrálne popisy — bez vymyslených mien.

## Poznámky k dizajnu

Moderný minimal premium: biela, dark navy, grafit, svetlá sivá, champagne akcent. Brand-first full-bleed hero, bez card clutteru v hero, 2–3 zámerné motion (hero rise-in, scroll reveal, cookie banner).
