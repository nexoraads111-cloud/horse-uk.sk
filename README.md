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

## Poznámky k dizajnu

Moderný minimal premium: biela, dark navy, grafit, svetlá sivá, champagne akcent. Brand-first full-bleed hero, bez card clutteru v hero, 2–3 zámerné motion (hero rise-in, scroll reveal, cookie banner).
