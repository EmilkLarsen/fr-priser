"""BricoDépôt.fr (EUR, France — Kingfisher pro-warehouse) — sitemap-produits
sitemaps; URLs /p/<EAN13>/<slug> (EAN in URL!); clean ld+json Product."""
import re
from common import get, sitemap_urls, sane_price, valid_ean, first_str, ldjson_products, offer_from_ld, write_jsonl, scrape_urls

BASE = "https://www.bricodepot.fr"
OUT = "data/latest/bricodepot_fr.jsonl"
EAN_RE = re.compile(r"/p/(\d{8,14})/")


def fetch_url_list(limit=None):
    urls = []
    i = 1
    while True:
        try:
            xml = get(f"{BASE}/sitemaps/sitemap-produits-{i}.xml")
        except Exception:
            break
        us = [u for u in sitemap_urls(xml) if EAN_RE.search(u)]
        urls.extend(us)
        i += 1
        if i > 20 or (limit and len(urls) >= limit):
            break
    return urls[:limit] if limit else urls


def handle(u, html):
    rows = []
    for p in ldjson_products(html):
        off = offer_from_ld(p)
        if off:
            off["price"] = sane_price(off["price"])
        if not off or not off["price"]:
            continue
        em = EAN_RE.search(u)
        t = re.search(r"<title[^>]*>([^<]+)</title>", html)
        name = (t.group(1).split("|")[0].strip() if t else u.rsplit("/", 1)[-1])
        rows.append({
            "chain": "bricodepot_fr",
            "country": "fr",
            "currency": off["currency"],
            "sku": em.group(1) if em else None,
            "ean": em.group(1) if em else valid_ean(p.get("gtin13") or p.get("gtin")),
            "name": name,
            "url": u,
            "price": off["price"],
            "in_stock": off["in_stock"],
            "image": first_str(p.get("image")),
        })
        break
    return rows


def scrape(limit=None):
    return scrape_urls(fetch_url_list(limit), handle)


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = scrape(lim)
    write_jsonl(OUT, rows)
    print("bricodepot_fr: %d products -> %s" % (len(rows), OUT))
