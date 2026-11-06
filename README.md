# Blueprint Construction Services

Static site for Blueprint Construction Services, an Ottawa builder since 2005. The design is direction A, editorial minimal. Copy and photographs come from the public site at blueprintottawa.com.

This repository does not change that live site, its DNS, or its domain. There is no CNAME file.

## Pages

- `/` Home. Title: Blueprint Construction | Ottawa builder since 2005
- `/gallery/` Projects, plus a page for each group of photographs that belong together
- `/contact/` Email only, [info@blueprintbuilds.com](mailto:info@blueprintbuilds.com). No phone, street address, or form
- `/home/` redirects to `/` and is omitted from the sitemap

Navigation is Home, Projects, Contact.

Canonical links, Open Graph URLs, and the sitemap use `https://blueprintottawa.com/...` so they are correct after a later domain cutover. Paths in the HTML are relative, so the same files work at the domain root and at `https://code-yves.github.io/blueprint-site/`.

## Preview

GitHub Actions publishes the `site/` directory to GitHub Pages on every push to `main`. The preview is not the live domain.

## Rebuild

```bash
python3 src/build.py
python3 -m http.server -d site 8080
```

The generator needs Python 3, Pillow, `cwebp`, and `avifenc`. The browser has no runtime dependencies. Fonts are subset and self-hosted (Libre Baskerville and Source Sans 3, SIL Open Font License; see `src/fonts/`).

## Analytics

The measurement ID copied from the live site is `UA-26098310-1`.

## Images

The source folder has 32 files, 5.41 MiB, at about 1500 pixels wide. Two files were byte-identical duplicates of other files, and two more were near-duplicates, so the site publishes 28 photographs.

| Set | Size |
| --- | --- |
| Original 32 files | 5.41 MiB |
| Originals actually used (28) | 4.97 MiB |
| Largest AVIF rendition of each photo | 1.61 MiB |
| Largest WebP rendition | 2.32 MiB |
| Largest JPEG rendition | 3.84 MiB |

A current browser downloads one format. The full-size AVIF set is about 68% smaller than the 28 source files it replaces. Each photo is also stored at 640 and 960 pixels, in AVIF, WebP, and JPEG, for `srcset`. Images below the first screen are lazy-loaded. EXIF is stripped, so location data from the camera is not published.

The live gallery used one photograph twice, once as Castle Heights (2019) and once as Riverview Park (2014). It is published once, as Castle Heights. A night-time semi was likewise filed as both Vanier North (2013) and a generic Ottawa semi; it is published once, as Vanier North.
