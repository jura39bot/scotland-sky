#!/usr/bin/env python3
"""
scotland-sky — Collecte des prix des whiskies tourbés écossais
Sources : Carrefour, Intermarché
Fréquence : hebdomadaire (GitHub Actions, chaque lundi 6h)
"""

import json
import re
import time
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "prices.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Liste des whiskies à tracker avec leurs URLs par supermarché
WHISKIES = [
    {
        "name": "Ardbeg 10 ans",
        "distillery": "Ardbeg",
        "age": 10,
        "region": "Islay",
        "ppm": 50,
        "abv": 46,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-ardbeg-10-ans-46-3002302622321",
            "Intermarché": "https://www.intermarche.com/produit/ardbeg-10-ans/3002302622321",
        }
    },
    {
        "name": "Lagavulin 16 ans",
        "distillery": "Lagavulin",
        "age": 16,
        "region": "Islay",
        "ppm": 35,
        "abv": 43,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-islay-single-malt-16-ans-d-age-lagavulin-5000281005409",
        }
    },
    {
        "name": "Lagavulin 8 ans",
        "distillery": "Lagavulin",
        "age": 8,
        "region": "Islay",
        "ppm": 35,
        "abv": 48,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-single-malt-scotch-8-ans-480-lagavulin-5000281050553",
        }
    },
    {
        "name": "Laphroaig 10 ans",
        "distillery": "Laphroaig",
        "age": 10,
        "region": "Islay",
        "ppm": 40,
        "abv": 40,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-islay-single-malt-scotch-10-ans-40-laphroaig-5010019000163",
            "Intermarché": "https://www.intermarche.com/produit/islay-single-malt-scotch-whisky-select/5010019637604",
        }
    },
    {
        "name": "Caol Ila 12 ans",
        "distillery": "Caol Ila",
        "age": 12,
        "region": "Islay",
        "ppm": 35,
        "abv": 43,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-ecossais-single-malt-12-ans-caol-ila-5000281016290",
        }
    },
    {
        "name": "Bowmore 12 ans",
        "distillery": "Bowmore",
        "age": 12,
        "region": "Islay",
        "ppm": 25,
        "abv": 40,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-ecossais-single-malt-12-ans-bowmore",
            "Intermarché": "https://www.intermarche.com/produit/bowmore-12-ans",
        }
    },
    {
        "name": "Big Peat",
        "distillery": "Douglas Laing (blend Islay)",
        "age": None,
        "region": "Islay",
        "ppm": 55,
        "abv": 46,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-blended-big-peat-5014218776256",
        }
    },
    {
        "name": "Highland Park 12 ans",
        "distillery": "Highland Park",
        "age": 12,
        "region": "Orkney",
        "ppm": 20,
        "abv": 40,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-highland-park-12-ans",
            "Intermarché": "https://www.intermarche.com/produit/highland-park-12-ans",
        }
    },
    {
        "name": "Talisker 10 ans",
        "distillery": "Talisker",
        "age": 10,
        "region": "Skye",
        "ppm": 25,
        "abv": 45.8,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-talisker-10-ans",
            "Intermarché": "https://www.intermarche.com/produit/talisker-10-ans",
        }
    },
    {
        "name": "Bunnahabhain 12 ans",
        "distillery": "Bunnahabhain",
        "age": 12,
        "region": "Islay",
        "ppm": 2,
        "abv": 46.3,
        "sources": {
            "Carrefour": "https://www.carrefour.fr/p/whisky-bunnahabhain-12-ans",
        }
    },
]


def fetch_price_carrefour(url: str) -> float | None:
    """Tente d'extraire le prix depuis une page Carrefour."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        # Carrefour : balise <span> avec attribut data-testid contenant "price"
        price_tag = soup.find("span", {"data-testid": re.compile("price", re.I)})
        if not price_tag:
            # Fallback : chercher le pattern de prix (ex: "44,90 €")
            text = soup.get_text()
            m = re.search(r'(\d{2,3}[,\.]\d{2})\s*€', text)
            if m:
                return float(m.group(1).replace(",", "."))
        else:
            return float(price_tag.get_text(strip=True).replace(",", ".").replace("€", "").strip())
    except Exception:
        pass
    return None


def fetch_price_intermarche(url: str) -> float | None:
    """Tente d'extraire le prix depuis une page Intermarché."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        price_tag = soup.find("span", class_=re.compile("price", re.I))
        if price_tag:
            m = re.search(r'(\d{2,3}[,\.]\d{2})', price_tag.get_text())
            if m:
                return float(m.group(1).replace(",", "."))
    except Exception:
        pass
    return None


FETCHERS = {
    "Carrefour": fetch_price_carrefour,
    "Intermarché": fetch_price_intermarche,
}


def collect():
    today = date.today().isoformat()
    data = json.loads(DATA_FILE.read_text())
    updated = 0

    for whisky_def in WHISKIES:
        name = whisky_def["name"]
        # Trouver ou créer l'entrée dans data
        entry = next((w for w in data["whiskies"] if w["name"] == name), None)
        if entry is None:
            entry = {
                "name": name,
                "distillery": whisky_def["distillery"],
                "age": whisky_def["age"],
                "region": whisky_def["region"],
                "ppm": whisky_def["ppm"],
                "abv": whisky_def["abv"],
                "prices": [],
            }
            data["whiskies"].append(entry)

        for supermarket, url in whisky_def["sources"].items():
            fetcher = FETCHERS.get(supermarket)
            if not fetcher:
                continue
            price = fetcher(url)
            time.sleep(2)  # politesse
            if price:
                entry["prices"].append({
                    "date": today,
                    "price": price,
                    "supermarket": supermarket,
                    "url": url,
                })
                print(f"✅ {name} @ {supermarket} : {price}€")
                updated += 1
            else:
                print(f"⚠️  {name} @ {supermarket} : prix non trouvé")

    data["last_updated"] = today
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\n✅ {updated} prix collectés — {today}")


if __name__ == "__main__":
    collect()
