#!/usr/bin/env python3
"""Static site generator for Blueprint Construction Services.

Reads src/photos (the 1500px source set) and writes a dependency-free
site to site/. Images are resized and encoded as AVIF, WebP, and JPEG.
No network calls. Requires Pillow, cwebp, and avifenc.
"""

from __future__ import annotations

import html
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PHOTO_DIR = SRC / "photos"
FONT_DIR = SRC / "fonts"
OUT = ROOT / "site"
IMG_OUT = OUT / "assets" / "img"

ORIGIN = "https://blueprintottawa.com"
EMAIL = "info@blueprintbuilds.com"
MAILTO = f"mailto:{EMAIL}"
GA_ID = "UA-26098310-1"
WIDTHS = (640, 960, 1500)

# Photos omitted on purpose:
# 30 is a byte-identical copy of 25 (Castle Heights semi).
# 32 is a byte-identical copy of 20 (the night-time semi).
# 12 is a near-duplicate of 14 (same rooftop lounge).
# 19 is a near-duplicate of the Beechwood stair (31).
IMAGES = {
    "hintonburg": {
        "file": "03_image-asset.jpeg",
        "title": "Rendering of a 10-unit low-rise in Hintonburg",
        "alt": "Architectural rendering of a narrow 10-unit low-rise on a residential street in Hintonburg, Ottawa, a project in progress.",
    },
    "westboro": {
        "file": "27_06_image-asset_jpeg.jpg",
        "title": "Rendering of a Westboro semi-detached house",
        "alt": "Architectural rendering of a modern semi-detached house in Westboro, Ottawa, with dark wood cladding and large windows, a project in progress.",
    },
    "heritage-ncc": {
        "file": "01_Heritage_Restoration__7C_NCC.jpg",
        "title": "Heritage stone house restored for the NCC",
        "alt": "Stone heritage house with decorative bargeboard and a white porch, restored for the National Capital Commission in Ottawa in 2024.",
    },
    "beechwood-living": {
        "file": "21_07_Semi-Detach___Beechwood.jpg",
        "title": "Beechwood semi living room",
        "alt": "Living and dining room in a Beechwood semi-detached home, with a light sofa, black chairs, a round coffee table, and a linear fireplace.",
    },
    "beechwood-exterior": {
        "file": "23_Semi-Detach__7C_Beechwood.jpg",
        "title": "Beechwood semi-detached homes at twilight",
        "alt": "Pair of modern semi-detached homes on Beechwood at twilight, with stone and stucco walls, lit windows, and garage doors in the snow.",
    },
    "beechwood-kitchen": {
        "file": "28_Semi-Detach__7C_Beechwood.jpg",
        "title": "Beechwood semi kitchen",
        "alt": "Kitchen in a Beechwood semi-detached home, with a walnut island, white counters, a wall oven, and three globe pendant lights.",
    },
    "beechwood-bath": {
        "file": "29_Semi-Detach__7C_Beechwood.jpg",
        "title": "Beechwood semi bathroom",
        "alt": "Bathroom in a Beechwood semi-detached home, with a freestanding tub, a wood vanity, and a walk-in shower.",
    },
    "beechwood-stair": {
        "file": "31_Semi-Detach__7C_Beechwood.jpg",
        "title": "Beechwood semi staircase",
        "alt": "Light wood staircase with metal balusters in a Beechwood semi-detached home, looking through to the living room.",
    },
    "beacon": {
        "file": "18_Commercial_Build__7C_Beacon_Lite.jpg",
        "title": "Beacon Lite commercial building at night",
        "alt": "Beacon Lite commercial building at night, brick above a stone base, with a lit sign and wet pavement, built in 2021.",
    },
    "navan": {
        "file": "02_02_Custom_Home___Navan.jpg",
        "title": "Custom home in Navan",
        "alt": "Custom two-storey home in Navan with pale stone cladding, black windows, and a covered entry, photographed at sunset in 2020.",
    },
    "castle-semi": {
        "file": "25_Semi-Detach__7C_Castle_Heights.jpg",
        "title": "Semi-detached home in Castle Heights",
        "alt": "Semi-detached home in Castle Heights, Ottawa, with stone, dark brick, a wood entry canopy, and garage doors, built in 2019.",
    },
    "dalhousie": {
        "file": "24_Heritage_Restoration__7C_Dalhousie.jpg",
        "title": "Heritage building restoration in Dalhousie",
        "alt": "Corner brick heritage building in Dalhousie, Ottawa, wrapped in scaffolding during a 2019 restoration.",
    },
    "orleans-exterior": {
        "file": "22_Commercial_Development__7C_Orleans.jpg",
        "title": "Commercial plaza in Orléans",
        "alt": "Single-storey commercial plaza in Orléans with a pale facade, black awnings, and a landscaped parking edge, finished in 2018.",
    },
    "orleans-reception": {
        "file": "11_Interior__7C_Orleans.jpg",
        "title": "Orléans commercial reception",
        "alt": "Reception and waiting area in an Orléans commercial interior, with a grey desk, a blue chair, and a backlit spine panel.",
    },
    "orleans-hall": {
        "file": "10_Interior__7C_Orleans.jpg",
        "title": "Orléans commercial hallway",
        "alt": "Waiting area and hallway in an Orléans commercial interior, with blue chairs, grey partitions, and a wall-mounted screen.",
    },
    "new-ed-multi": {
        "file": "04_FullSizeRender.jpg",
        "title": "Multi-unit building in New Edinburgh",
        "alt": "Narrow multi-unit residential building in New Edinburgh, stone and metal cladding, photographed at dusk in 2016.",
    },
    "castle-multi": {
        "file": "16_01_Multi-Unit___Castle_Heights.jpg",
        "title": "Multi-unit building in Castle Heights",
        "alt": "Four-storey multi-unit residential building in Castle Heights, Ottawa, with recessed balconies and metal cladding, photographed in snow in 2015.",
    },
    "vanier": {
        "file": "20_Custom_Semi-Detach__7C_Ottawa.jpg",
        "title": "Semi-detached homes in Vanier North",
        "alt": "Pair of semi-detached homes at night in Vanier North, Ottawa, with stone, red brick, and two garage doors, built in 2013.",
    },
    "rideau-living": {
        "file": "07_virtual-tour-42535-25.jpg",
        "title": "Rideau Gardens addition living space",
        "alt": "Open living space in a Rideau Gardens addition, with wide hardwood floors and black-framed sliding doors to a deck, 2009.",
    },
    "rideau-stair": {
        "file": "05_virtual-tour-42535-08.jpg",
        "title": "Rideau Gardens stair",
        "alt": "Open-riser staircase with wood treads and a black steel and glass rail in a Rideau Gardens home addition.",
    },
    "rideau-loft": {
        "file": "06_virtual-tour-42535-40.jpg",
        "title": "Rideau Gardens upper landing",
        "alt": "Upper landing in a Rideau Gardens addition, with a built-in desk under a large window and a glass guardrail.",
    },
    "rooftop-lounge": {
        "file": "14_04_IMG_0496_JPG.jpg",
        "title": "New Edinburgh rooftop lounge",
        "alt": "Rooftop lounge in New Edinburgh at dusk, with a fire pit, Adirondack chairs, a sofa, and a glazed pavilion.",
    },
    "rooftop-dining": {
        "file": "15_03_IMG_0498_JPG.jpg",
        "title": "New Edinburgh rooftop dining deck",
        "alt": "Rooftop dining deck in New Edinburgh at dusk, with string lights, a picnic table, lounge chairs, a hot tub, and a grill.",
    },
    "interior-kitchen": {
        "file": "08_virtual-tour-290211-08.jpg",
        "title": "Residential kitchen with a stone island",
        "alt": "White residential kitchen with a stone waterfall island, double wall ovens, and slim pendant lights.",
    },
    "interior-living": {
        "file": "09_virtual-tour-290211-02.jpg",
        "title": "Residential living room with a fireplace",
        "alt": "Unfurnished living room with pale wood floors, a stone fireplace wall, and sliding doors to a balcony.",
    },
    "living-room": {
        "file": "13_05_IMG_8005_jpg.jpg",
        "title": "Furnished residential living room",
        "alt": "Furnished living room with a grey sectional, a white coffee table, a fireplace, and light wood floors.",
    },
    "steel": {
        "file": "17_Steel_Building_Construction.png",
        "title": "Building under construction in green sheathing",
        "alt": "Two-storey building under construction, wrapped in green sheathing, beside a steel industrial bay.",
    },
    "yves": {
        "file": "26_Yves_Eggleston.jpg",
        "title": "Yves Eggleston",
        "alt": "Yves Eggleston, owner of Blueprint Construction Services in Ottawa.",
    },
}

# Gallery order. slug set means a project page.
PROJECTS = [
    {
        "id": "hintonburg",
        "slug": None,
        "heading": "10-unit low-rise · Hintonburg",
        "meta": "In progress · Ottawa",
        "note": "Architectural rendering of a low-rise still in progress.",
        "cover": "hintonburg",
    },
    {
        "id": "westboro",
        "slug": None,
        "heading": "Semi-detach · Westboro",
        "meta": "In progress · Ottawa",
        "note": "Architectural rendering of a semi-detached house in progress.",
        "cover": "westboro",
    },
    {
        "id": "new-edinburgh-roof",
        "slug": "rooftop-new-edinburgh",
        "heading": "Rooftop terrace · New Edinburgh",
        "meta": "Residential · Ottawa",
        "note": "A finished rooftop lounge and dining deck.",
        "cover": "rooftop-lounge",
        "kicker": "Residential · Ottawa",
        "lede": "A rooftop terrace in New Edinburgh: a lounge with a fire pit and a glazed pavilion, and a dining deck with string lights, a hot tub, and a grill.",
        "description": "Rooftop terrace in New Edinburgh by Blueprint Construction: a lounge with a fire pit and a dining deck with string lights and a hot tub.",
        "images": [("rooftop-lounge", "wide"), ("rooftop-dining", "wide")],
    },
    {
        "id": "heritage-ncc",
        "slug": None,
        "heading": "Heritage · NCC",
        "meta": "Heritage restoration · Ottawa · 2024",
        "note": "Stone house restored for the National Capital Commission.",
        "cover": "heritage-ncc",
    },
    {
        "id": "beechwood",
        "slug": "semi-detach-beechwood",
        "heading": "Semi-Detach · Beechwood",
        "meta": "Residential · Ottawa · 2022",
        "note": "A pair of semis on Beechwood, from the envelope through the interiors.",
        "cover": "beechwood-exterior",
        "kicker": "Residential · Ottawa · 2022",
        "lede": "A pair of thoughtfully finished semis on Beechwood — solid envelope, refined interiors, and the day-to-day site oversight that keeps a neighbourhood build on track.",
        "description": "Semi-detached homes on Beechwood, Ottawa, built by Blueprint Construction in 2022. Exterior, living room, kitchen, bathroom, and stair.",
        "images": [
            ("beechwood-living", "wide"),
            ("beechwood-exterior", "cell"),
            ("beechwood-kitchen", "cell"),
            ("beechwood-bath", "cell"),
            ("beechwood-stair", "cell"),
        ],
    },
    {
        "id": "beacon",
        "slug": None,
        "heading": "Commercial · Beacon Lite",
        "meta": "Commercial · Ottawa · 2021",
        "note": "A two-storey commercial building, photographed at night.",
        "cover": "beacon",
    },
    {
        "id": "navan",
        "slug": None,
        "heading": "Custom home · Navan",
        "meta": "Residential · Navan · 2020",
        "note": "A two-storey custom home in pale stone and black windows.",
        "cover": "navan",
    },
    {
        "id": "castle-semi",
        "slug": None,
        "heading": "Semi-detach · Castle Heights",
        "meta": "Residential · Ottawa · 2019",
        "note": "Stone and dark brick, with a wood canopy at the entry.",
        "cover": "castle-semi",
    },
    {
        "id": "dalhousie",
        "slug": None,
        "heading": "Heritage · Dalhousie",
        "meta": "Heritage restoration · Ottawa · 2019",
        "note": "A corner brick building during restoration, under scaffolding.",
        "cover": "dalhousie",
    },
    {
        "id": "orleans",
        "slug": "commercial-orleans",
        "heading": "Commercial development · Orléans",
        "meta": "Commercial · Ottawa · 2018",
        "note": "A single-storey plaza and two of its tenant interiors.",
        "cover": "orleans-exterior",
        "kicker": "Commercial · Ottawa · 2018",
        "lede": "A commercial plaza in Orléans, finished in 2018, with tenant interiors that include a reception desk and a waiting hallway.",
        "description": "Commercial plaza in Orléans built by Blueprint Construction in 2018, including the exterior and two tenant interiors.",
        "images": [
            ("orleans-exterior", "wide"),
            ("orleans-reception", "cell"),
            ("orleans-hall", "cell"),
        ],
    },
    {
        "id": "new-ed-multi",
        "slug": None,
        "heading": "Multi-unit · New Edinburgh",
        "meta": "Multi-unit · Ottawa · 2016",
        "note": "A narrow multi-unit building in stone and metal cladding.",
        "cover": "new-ed-multi",
    },
    {
        "id": "castle-multi",
        "slug": None,
        "heading": "Multi-unit · Castle Heights",
        "meta": "Multi-unit · Ottawa · 2015",
        "note": "A four-storey residential building with recessed balconies.",
        "cover": "castle-multi",
    },
    {
        "id": "vanier",
        "slug": None,
        "heading": "Semi-detach · Vanier North",
        "meta": "Residential · Ottawa · 2013",
        "note": "A pair of semis in stone and red brick, photographed at night.",
        "cover": "vanier",
    },
    {
        "id": "rideau",
        "slug": "rideau-gardens",
        "heading": "Addition · Rideau Gardens",
        "meta": "Residential · Ottawa · 2009",
        "note": "An addition and renovation: living space, stair, and an upper landing.",
        "cover": "rideau-living",
        "kicker": "Residential · Ottawa · 2009",
        "lede": "An addition and renovation in Rideau Gardens from 2009: an open living space opening to a deck, a new stair, and an upper landing with a built-in desk.",
        "description": "Home addition and renovation in Rideau Gardens, Ottawa, by Blueprint Construction in 2009. Living space, staircase, and upper landing.",
        "images": [
            ("rideau-living", "wide"),
            ("rideau-stair", "cell"),
            ("rideau-loft", "cell"),
        ],
    },
    {
        "id": "residential-interior",
        "slug": "residential-interior",
        "heading": "Residential interior",
        "meta": "Residential · Ottawa",
        "note": "A white kitchen and an open living room from the same home.",
        "cover": "interior-kitchen",
        "kicker": "Residential · Ottawa",
        "lede": "A finished residential interior: a white kitchen with a stone island, and an open living room with a fireplace and doors to a balcony.",
        "description": "Residential interior by Blueprint Construction: a white kitchen with a stone island and an open living room with a fireplace.",
        "images": [("interior-kitchen", "wide"), ("interior-living", "wide")],
    },
    {
        "id": "living-room",
        "slug": None,
        "heading": "Residential living room",
        "meta": "Residential · Ottawa",
        "note": "A furnished living room with a fireplace and light wood floors.",
        "cover": "living-room",
    },
    {
        "id": "steel",
        "slug": None,
        "heading": "Building in progress",
        "meta": "In progress",
        "note": "A two-storey frame wrapped in sheathing, beside a steel bay.",
        "cover": "steel",
    },
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def url_for(depth: int, target: str) -> str:
    prefix = "../" * depth
    if target == "home":
        return prefix or "./"
    return f"{prefix}{target}/"


def asset(depth: int, path: str) -> str:
    return f"{'../' * depth}{path}"


def encode_one(task: tuple) -> dict:
    image_id, src, widths = task
    im = Image.open(src).convert("RGB")
    ow, oh = im.size
    made = {"avif": [], "webp": [], "jpg": []}
    for width in widths:
        if width > ow:
            continue
        height = round(oh * (width / ow))
        frame = im if width == ow else im.resize((width, height), Image.Resampling.LANCZOS)
        stem = IMG_OUT / f"{image_id}-{width}"
        png = stem.with_suffix(".tmp.png")
        frame.save(png, format="PNG", optimize=True)
        jpg = stem.with_suffix(".jpg")
        webp = stem.with_suffix(".webp")
        avif = stem.with_suffix(".avif")
        frame.save(jpg, format="JPEG", quality=76, optimize=True, progressive=True, subsampling=2)
        subprocess.run(
            ["cwebp", "-quiet", "-q", "74", "-m", "4", str(png), "-o", str(webp)],
            check=True,
        )
        subprocess.run(
            [
                "avifenc",
                "-s",
                "6",
                "--min",
                "26",
                "--max",
                "36",
                "-a",
                "cq-level=30",
                str(png),
                str(avif),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        png.unlink()
        rel_base = f"assets/img/{image_id}-{width}"
        made["jpg"].append((width, f"{rel_base}.jpg"))
        made["webp"].append((width, f"{rel_base}.webp"))
        made["avif"].append((width, f"{rel_base}.avif"))
    return {"id": image_id, "width": ow, "height": oh, "variants": made}


def picture(image: dict, depth: int, sizes: str, eager: bool = False) -> str:
    prefix = "../" * depth

    def srcset(fmt: str) -> str:
        return ", ".join(f"{prefix}{path} {width}w" for width, path in image["variants"][fmt])

    jpgs = image["variants"]["jpg"]
    # A mid-size JPEG is the fallback src for browsers without srcset.
    fallback = jpgs[min(1, len(jpgs) - 1)][1]
    loading = "eager" if eager else "lazy"
    fetch = ' fetchpriority="high"' if eager else ""
    alt = esc(image["alt"])
    return (
        "<picture>"
        f'<source type="image/avif" srcset="{srcset("avif")}" sizes="{sizes}">'
        f'<source type="image/webp" srcset="{srcset("webp")}" sizes="{sizes}">'
        f'<img src="{prefix}{fallback}" srcset="{srcset("jpg")}" sizes="{sizes}" '
        f'alt="{alt}" width="{image["width"]}" height="{image["height"]}" '
        f'loading="{loading}" decoding="async"{fetch}>'
        "</picture>"
    )


def chrome(depth: int, current: str) -> str:
    home = url_for(depth, "home")
    gallery = url_for(depth, "gallery")
    contact = url_for(depth, "contact")

    def item(href: str, label: str, key: str) -> str:
        current_attr = ' aria-current="page"' if current == key else ""
        return f'<a href="{href}"{current_attr}>{label}</a>'

    return f"""<a class="skip" href="#content">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="{home}">Blueprint Construction Services<span>Ottawa builder since 2005</span></a>
    <nav class="nav" aria-label="Primary">
      {item(home, "Home", "home")}
      {item(gallery, "Projects", "projects")}
      {item(contact, "Contact", "contact")}
    </nav>
  </div>
</header>"""


def footer(depth: int) -> str:
    return f"""<footer>
  <div class="wrap site-footer">
    <div>Blueprint Construction Services · Ottawa builder since 2005</div>
    <div><a href="{MAILTO}">{EMAIL}</a></div>
  </div>
</footer>"""


def head(
    *,
    depth: int,
    title: str,
    description: str,
    canonical_path: str,
    og_image: dict,
    og_type: str = "website",
    noindex: bool = False,
    jsonld: str | None = None,
) -> str:
    canonical = ORIGIN + canonical_path
    jpg = og_image["variants"]["jpg"][-1][1]
    og_url = f"{ORIGIN}/{jpg}"
    robots = "noindex, follow" if noindex else "index, follow"
    preload = "\n".join(
        [
            f'<link rel="preload" href="{asset(depth, "assets/fonts/libre-baskerville-700.woff2")}" as="font" type="font/woff2" crossorigin>',
            f'<link rel="preload" href="{asset(depth, "assets/fonts/source-sans-3-400.woff2")}" as="font" type="font/woff2" crossorigin>',
        ]
    )
    ld = f'\n<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="{robots}">
<meta property="og:site_name" content="Blueprint Construction">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:image" content="{og_url}">
<meta property="og:image:alt" content="{esc(og_image["alt"])}">
<meta property="og:image:width" content="{og_image["width"]}">
<meta property="og:image:height" content="{og_image["height"]}">
<meta property="og:locale" content="en_CA">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{og_url}">
<meta name="twitter:image:alt" content="{esc(og_image["alt"])}">
<meta name="theme-color" content="#F5F0E6">
<link rel="icon" href="{asset(depth, "favicon.svg")}" type="image/svg+xml">
<link rel="icon" href="{asset(depth, "favicon.ico")}" sizes="32x32">
<link rel="apple-touch-icon" href="{asset(depth, "apple-touch-icon.png")}">
{preload}
<link rel="stylesheet" href="{asset(depth, "assets/styles.css")}">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>{ld}
</head>"""


def cta() -> str:
    return f"""<section class="cta-band">
  <div class="wrap">
    <h2>Every successful project starts with an honest conversation.</h2>
    <p>Let’s see if we’re the right fit. Write to <a class="mail" href="{MAILTO}">{EMAIL}</a>.</p>
    <a class="btn" href="{MAILTO}">Start a conversation</a>
  </div>
</section>"""


def render_home(images: dict) -> str:
    title = "Blueprint Construction | Ottawa builder since 2005"
    description = (
        "Open-book construction management in Ottawa. Fixed management fee, costs billed at cost, "
        "budgets within 5%. Custom homes, multi-unit, and commercial — from design and permits to occupancy."
    )
    depth = 0
    mag = [
        ("beechwood-living", "big", "gallery/semi-detach-beechwood/", "Semi-Detach · Beechwood · 2022", "(max-width: 860px) 100vw, 640px", True),
        ("heritage-ncc", "sm", "gallery/#heritage-ncc", "Heritage · NCC · 2024", "(max-width: 860px) 100vw, 420px", False),
        ("beacon", "sm", "gallery/#beacon", "Commercial · Beacon Lite · 2021", "(max-width: 860px) 100vw, 420px", False),
    ]
    cards = []
    for image_id, size, href, caption, sizes, eager in mag:
        cards.append(
            f'<a class="mag-card {size}" href="{href}">'
            f"<figure>{picture(images[image_id], depth, sizes, eager=eager)}"
            f"<figcaption>{esc(caption)}</figcaption></figure></a>"
        )
    jsonld = (
        '{"@context":"https://schema.org","@type":"GeneralContractor",'
        '"name":"Blueprint Construction Services","url":"https://blueprintottawa.com/",'
        f'"email":"{EMAIL}","foundingDate":"2005",'
        '"areaServed":{"@type":"City","name":"Ottawa"},'
        '"description":"Open-book construction management in Ottawa since 2005. '
        'Custom homes, multi-unit, and commercial work, from design and permits to occupancy."}'
    )
    body = f"""{chrome(depth, "home")}
<main id="content">
  <section class="hero">
    <div class="wrap">
      <p class="hero-kicker">Ottawa builder since 2005</p>
      <h1>Built on transparency. Driven by integrity.</h1>
      <p class="hero-lead">Custom homes, multi-unit, and commercial — from design and permits through to occupancy. Open-book pricing. Fixed management fee.</p>
      <div class="btn-row">
        <a class="btn" href="gallery/">See our work</a>
        <a class="btn btn-ghost" href="{MAILTO}">Email Yves</a>
      </div>
    </div>
  </section>

  <section class="section" aria-label="Featured projects">
    <div class="wrap">
      <h2 class="section-title">Selected work</h2>
      <p class="section-intro">A quiet portfolio of Ottawa builds — residential, heritage, and commercial — shaped by staying small and showing up on site.</p>
      <div class="mag">
        {''.join(cards)}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap about">
      {picture(images["yves"], depth, "(max-width: 860px) 100vw, 480px")}
      <div class="prose">
        <p class="eyebrow">About</p>
        <h2 class="section-title">Hi, I’m Yves Eggleston</h2>
        <p>Whether it’s a custom home, a multi-unit building, or a commercial space, I can help you take your project from the design and permit stages all the way to occupancy.</p>
        <p>My journey in construction began in <strong>2005</strong>. I only take on a limited number of projects at a time and by staying small, I can focus on your project. I’m on-site in person to keep an eye on every detail, ensuring that the work happening behind the walls is just as solid as the work you see on the outside.</p>
        <p>I believe in a fully open-book approach: a fixed management fee, and every receipt, discount, and quote shared with you directly. Everything is billed at cost. No hidden markups, no surprises.</p>
        <p>I’ve lived in Ottawa my whole life. I’m a proud husband and a father of two, and I treat every project with the same care I’d put into my own home.</p>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <p class="eyebrow">A reputation built on staying put</p>
      <h2 class="section-title">Twenty years of consistency.</h2>
      <div class="prose">
        <p>I’m proud to say I’ve been doing this right since 2005. I’ve never walked away from a project or left a client hanging. I’ve never had to shut down only to reopen under a different name, and I’ve never been involved in litigation. I’ve had the same email address for over 20 years.</p>
        <p>Construction isn’t always perfect, and not every project goes exactly to plan, but I will always stand by your side and get us to the finish line. Because of this, I’ve never had to do much advertising. You won’t see Blueprint signs on front lawns or find us on social media. I’ve always believed that if you do the right thing, word-of-mouth is the only marketing you need.</p>
      </div>
    </div>
  </section>

  <section class="section process">
    <div class="wrap">
      <h2 class="section-title">How we work</h2>
      <p class="section-intro">An adaptable process — step in for a roadblock, or manage the whole job.</p>
      <ol>
        <li><h3>Feasibility</h3><p>Site, numbers, and what you actually want — before drawings that don’t fit the budget.</p></li>
        <li><h3>Design &amp; permits</h3><p>Steer drawings, engineering, and permits; flag what paper plans miss.</p></li>
        <li><h3>A budget you can trust</h3><p>Trusted trade quotes near the end of design, then a clear final budget.</p></li>
        <li><h3>Build &amp; timeline</h3><p>Day-to-day site run: trades, inspections, suppliers, a timeline you can plan around.</p></li>
        <li><h3>After-care</h3><p>Small issues show up after handover. We don’t disappear.</p></li>
        <li><h3>Financing</h3><p>Relationships with private lenders who have financed Blueprint jobs before.</p></li>
      </ol>
    </div>
  </section>

  {cta()}
</main>
{footer(depth)}"""
    return head(
        depth=depth,
        title=title,
        description=description,
        canonical_path="/",
        og_image=images["beechwood-living"],
        jsonld=jsonld,
    ) + f"\n<body>\n{body}\n</body>\n</html>\n"


def render_gallery(images: dict) -> str:
    depth = 1
    title = "Projects | Blueprint Construction"
    description = (
        "Ottawa projects by Blueprint Construction since 2005: custom homes, semi-detached houses, "
        "multi-unit buildings, heritage restoration, and commercial work."
    )
    cards = []
    for project in PROJECTS:
        cover = images[project["cover"]]
        media = picture(cover, depth, "(max-width: 860px) 100vw, 540px", eager=project is PROJECTS[0])
        text = (
            f'<h2>{esc(project["heading"])}</h2>'
            f'<p class="meta">{esc(project["meta"])}</p>'
            f'<p class="note">{esc(project["note"])}</p>'
        )
        if project["slug"]:
            inner = (
                f'<a class="work-link" href="{project["slug"]}/">'
                f"{media}{text}<span class=\"more\">View project</span></a>"
            )
        else:
            inner = f"<figure>{media}</figure>{text}"
        cards.append(f'<article class="work-card" id="{project["id"]}">{inner}</article>')
    body = f"""{chrome(depth, "projects")}
<main id="content">
  <section class="hero">
    <div class="wrap">
      <p class="hero-kicker">Ottawa builder since 2005</p>
      <h1>Projects</h1>
      <p class="hero-lead">A quiet portfolio of Ottawa builds — residential, heritage, and commercial — shaped by staying small and showing up on site.</p>
    </div>
  </section>
  <section class="section flush-top">
    <div class="wrap">
      <div class="work-grid">
        {''.join(cards)}
      </div>
    </div>
  </section>
  {cta()}
</main>
{footer(depth)}"""
    # inline style padding-top:0 is a one-off; keep it in CSS instead.
    return head(
        depth=depth,
        title=title,
        description=description,
        canonical_path="/gallery/",
        og_image=images["beechwood-exterior"],
    ) + f"\n<body>\n{body}\n</body>\n</html>\n"


def render_project(project: dict, images: dict) -> str:
    depth = 2
    title = f'{project["heading"]} | Blueprint Construction'
    sizes = {
        "wide": "(max-width: 860px) 100vw, 1120px",
        "cell": "(max-width: 860px) 100vw, 540px",
    }
    figures = []
    for index, (image_id, role) in enumerate(project["images"]):
        figures.append(
            f'<figure class="{role}">{picture(images[image_id], depth, sizes[role], eager=index == 0)}</figure>'
        )
    body = f"""{chrome(depth, "projects")}
<main id="content">
  <section class="project-hero">
    <div class="wrap">
      <a class="back-link" href="../">All projects</a>
      <p class="project-meta">{esc(project["kicker"])}</p>
      <h1>{esc(project["heading"])}</h1>
      <p class="project-lede">{esc(project["lede"])}</p>
      <div class="project-grid">
        {''.join(figures)}
      </div>
      <div class="prose follow"><p>Interested in a similar build? <a href="{MAILTO}">{EMAIL}</a></p></div>
    </div>
  </section>
</main>
{footer(depth)}"""
    return head(
        depth=depth,
        title=title,
        description=project["description"],
        canonical_path=f'/gallery/{project["slug"]}/',
        og_image=images[project["images"][0][0]],
        og_type="article",
    ) + f"\n<body>\n{body}\n</body>\n</html>\n"


def render_contact(images: dict) -> str:
    depth = 1
    title = "Contact | Blueprint Construction"
    description = (
        "Talk with Yves Eggleston at Blueprint Construction. Email info@blueprintbuilds.com. "
        "Open-book construction management in Ottawa since 2005."
    )
    body = f"""{chrome(depth, "contact")}
<main id="content">
  <section class="hero">
    <div class="wrap">
      <p class="hero-kicker">Contact</p>
      <h1>Honest advice. Solid foundations.</h1>
      <p class="hero-lead">Let’s see if we’re the right fit. The only way to reach Blueprint is by email.</p>
      <a class="btn" href="{MAILTO}">Email Yves</a>
    </div>
  </section>
  <section class="section flush-top">
    <div class="wrap about">
      <div class="wide-photo">{picture(images["steel"], depth, "(max-width: 860px) 100vw, 520px")}</div>
      <div class="prose">
        <h2 class="section-title">Why communication is everything</h2>
        <p>I’ve seen it happen too often in this industry: poor communication is where projects fall apart.</p>
        <p>When a contractor goes quiet, it creates a domino effect. Trades get the wrong instructions, suppliers miss delivery windows, and avoidable errors start piling up. I refuse to work that way. I limit the number of projects I take on so that I can be your point of contact. Because I’m not spread thin between a dozen sites, I have the time to oversee every trade, double-check every supplier order, and catch the small details before they become big delays.</p>
        <p>I make it a point to get back to you quickly, even on evenings and weekends, because a fast answer today prevents a costly mistake tomorrow. Being a trusted partner means more than doing the work. It means being available to talk about it.</p>
        <p><a href="{MAILTO}">{EMAIL}</a></p>
      </div>
    </div>
  </section>
</main>
{footer(depth)}"""
    return head(
        depth=depth,
        title=title,
        description=description,
        canonical_path="/contact/",
        og_image=images["steel"],
    ) + f"\n<body>\n{body}\n</body>\n</html>\n"


def render_home_redirect() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blueprint Construction | Ottawa builder since 2005</title>
<link rel="canonical" href="{ORIGIN}/">
<meta name="robots" content="noindex, follow">
<meta http-equiv="refresh" content="0; url=../">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
</head>
<body>
<p><a href="../">Blueprint Construction</a></p>
</body>
</html>
"""


def sitemap(images: dict) -> str:
    def image_xml(image_id: str) -> str:
        image = images[image_id]
        loc = f'{ORIGIN}/{image["variants"]["jpg"][-1][1]}'
        return (
            "    <image:image>\n"
            f"      <image:loc>{esc(loc)}</image:loc>\n"
            f"      <image:title>{esc(image['title'])}</image:title>\n"
            f"      <image:caption>{esc(image['alt'])}</image:caption>\n"
            "    </image:image>\n"
        )

    pages = {
        "/": ["beechwood-living", "heritage-ncc", "beacon", "yves"],
        "/gallery/": [project["cover"] for project in PROJECTS],
        "/contact/": ["steel"],
    }
    urls = []
    for path, ids in pages.items():
        block = [f"  <url>\n    <loc>{ORIGIN}{path}</loc>\n    <lastmod>2026-11-06</lastmod>\n"]
        for image_id in ids:
            block.append(image_xml(image_id))
        block.append("  </url>")
        urls.append("".join(block))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def write_favicon_copies() -> None:
    for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png"):
        shutil.copyfile(SRC / name, OUT / name)


def check_output() -> None:
    banned = [
        "613-262-2442",
        "6132622442",
        "+1613",
        "tel:",
        "yves@",
        "Make it stand out",
        "maps.google",
        "<form",
        "CNAME",
        "Whatever it is, the way you tell your story",
    ]
    html_files = list(OUT.rglob("*.html"))
    blob = "\n".join(path.read_text() for path in html_files)
    blob += (OUT / "sitemap.xml").read_text()
    blob += (OUT / "robots.txt").read_text()
    for term in banned:
        if term.lower() in blob.lower():
            raise SystemExit(f"Forbidden string in output: {term}")
    sitemap_text = (OUT / "sitemap.xml").read_text()
    if "/home" in sitemap_text:
        raise SystemExit("sitemap lists /home")
    for required in (f"{ORIGIN}/<", f"{ORIGIN}/gallery/<", f"{ORIGIN}/contact/<"):
        # loc tags
        pass
    for path in ("/", "/gallery/", "/contact/"):
        if f"<loc>{ORIGIN}{path}</loc>" not in sitemap_text:
            raise SystemExit(f"sitemap missing {path}")
    titles = set()
    descriptions = set()
    for path in html_files:
        text = path.read_text()
        if 'rel="canonical"' not in text:
            raise SystemExit(f"missing canonical: {path}")
        if path.name == "index.html" and path.parent.name == "home":
            continue
        if "name=\"description\"" not in text:
            raise SystemExit(f"missing description: {path}")
        if "og:title" not in text or GA_ID not in text:
            raise SystemExit(f"missing og or analytics: {path}")
        title = text.split("<title>", 1)[1].split("</title>", 1)[0]
        desc = text.split('name="description" content="', 1)[1].split('"', 1)[0]
        if title in titles:
            raise SystemExit(f"duplicate title: {title}")
        if desc in descriptions:
            raise SystemExit(f"duplicate description: {desc}")
        titles.add(title)
        descriptions.add(desc)
        if 'alt=""' in text:
            raise SystemExit(f"empty alt in {path}")
    home = (OUT / "index.html").read_text()
    if "<title>Blueprint Construction | Ottawa builder since 2005</title>" not in home:
        raise SystemExit("home title mismatch")


def directory_size(path: Path, suffix: str | None = None) -> int:
    total = 0
    for file in path.rglob("*"):
        if file.is_file() and (suffix is None or file.suffix == suffix):
            total += file.stat().st_size
    return total


def main() -> None:
    for tool in ("cwebp", "avifenc"):
        if shutil.which(tool) is None:
            raise SystemExit(f"missing {tool}")
    if IMG_OUT.exists():
        shutil.rmtree(IMG_OUT)
    IMG_OUT.mkdir(parents=True)
    tasks = []
    for image_id, spec in IMAGES.items():
        src = PHOTO_DIR / spec["file"]
        if not src.exists():
            raise SystemExit(f"missing photo {src}")
        with Image.open(src) as im:
            width = im.size[0]
        widths = tuple(w for w in WIDTHS if w <= width) or (width,)
        if width not in widths:
            widths = widths + (width,)
        tasks.append((image_id, str(src), widths))
    encoded = {}
    with ProcessPoolExecutor(max_workers=4) as pool:
        for result in pool.map(encode_one, tasks):
            spec = IMAGES[result["id"]]
            result["alt"] = spec["alt"]
            result["title"] = spec["title"]
            encoded[result["id"]] = result

    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC / "styles.css", OUT / "assets" / "styles.css")
    font_out = OUT / "assets" / "fonts"
    font_out.mkdir(parents=True, exist_ok=True)
    for font in FONT_DIR.glob("*.woff2"):
        shutil.copyfile(font, font_out / font.name)
    write_favicon_copies()
    (OUT / ".nojekyll").write_text("")
    (OUT / "index.html").write_text(render_home(encoded))
    gallery = OUT / "gallery"
    gallery.mkdir(exist_ok=True)
    (gallery / "index.html").write_text(render_gallery(encoded))
    for project in PROJECTS:
        if not project["slug"]:
            continue
        dest = gallery / project["slug"]
        dest.mkdir(exist_ok=True)
        (dest / "index.html").write_text(render_project(project, encoded))
    contact = OUT / "contact"
    contact.mkdir(exist_ok=True)
    (contact / "index.html").write_text(render_contact(encoded))
    home_redirect = OUT / "home"
    home_redirect.mkdir(exist_ok=True)
    (home_redirect / "index.html").write_text(render_home_redirect())
    (OUT / "sitemap.xml").write_text(sitemap(encoded))
    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: https://blueprintottawa.com/sitemap.xml\n"
    )
    check_output()

    original = sum(p.stat().st_size for p in PHOTO_DIR.iterdir() if p.is_file())
    shipped = directory_size(IMG_OUT)
    avif = directory_size(IMG_OUT, ".avif")
    webp = directory_size(IMG_OUT, ".webp")
    jpeg = directory_size(IMG_OUT, ".jpg")
    print(f"source photos: {original} bytes ({original/1024/1024:.2f} MiB) across {len(list(PHOTO_DIR.iterdir()))} files")
    print(f"shipped images: {shipped} bytes ({shipped/1024/1024:.2f} MiB)")
    print(f"  avif {avif} ({avif/1024:.0f} KiB)")
    print(f"  webp {webp} ({webp/1024:.0f} KiB)")
    print(f"  jpeg {jpeg} ({jpeg/1024:.0f} KiB)")
    print(f"encoded {len(encoded)} unique photographs")
    print(f"pages: {len(list(OUT.rglob('*.html')))}")


if __name__ == "__main__":
    main()
