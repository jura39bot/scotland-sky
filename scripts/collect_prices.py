#!/usr/bin/env python3
"""
scotland-sky — Collecte des prix des whiskies tourbés écossais
Sources : Nicolas, Système U, La Maison du Whisky
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

# Liste des whiskies à tracker avec leurs URLs par caviste
WHISKIES = [
    {
        "name": "Ardbeg 10 ans",
        "distillery": "Ardbeg",
        "age": 10,
        "region": "Islay",
        "ppm": 50,
        "abv": 46,
        "sources": {
            "Nicolas": "https://www.nicolas.com/en/LIQUORS/WHISKY/Ardbeg-10-Years-Old/p/264221.html",
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
            "Nicolas": "https://www.nicolas.com/en/LIQUORS/WHISKY/WHISKY-MALTS/LAGAVULIN-16-ANS/p/144491.html",
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
            "Nicolas": "https://www.nicolas.com/en/LIQUORS/WHISKY/WHISKY-MALTS/LAPHROAIG-QUARTER-CASK/p/447623.html",
        }
    },
    {
        "name": "Caol Ila Moch",
        "distillery": "Caol Ila",
        "age": None,
        "region": "Islay",
        "ppm": 35,
        "abv": 43,
        "sources": {
            "Nicolas": "https://www.nicolas.com/en/LIQUORS/CAOL-ILA-MOCH/p/466323.html",
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
            "Nicolas": "https://www.nicolas.com/en/LIQUORS/BOWMORE-12-ANS-ISLAY-SINGLE-MALT/p/502784.html",
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
            "Nicolas": "https://www.nicolas.com/en/LIQUORS/HIGHLAND-PARK-12-ANS-/p/492452.html",
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
            "Nicolas": "https://www.nicolas.com/en/LIQUORS/TALISKER-10-ANS-/p/144462.html",
        }
    },
    {
        "name": "Bunnahabhain Stiuireadair",
        "distillery": "Bunnahabhain",
        "age": None,
        "region": "Islay",
        "ppm": 2,
        "abv": 46.3,
        "sources": {
            "Nicolas": "https://www.nicolas.com/en/LIQUORS/BUNNAHABHAIN-STIUIREADAIR-/p/486178.html",
        }
    },
]


def fetch_price_nicolas(url: str) -> float | None:
    """Extrait le prix depuis une page Nicolas.com."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        # Nicolas : span avec itemprop="price" ou class contenant "price"
        price_tag = soup.find("span", {"itemprop": "price"})
        if not price_tag:
            price_tag = soup.find("span", class_=re.compile("price", re.I))
        if price_tag:
            content = price_tag.get("content") or price_tag.get_text(strip=True)
            # Nettoyer : "57,€90" → "57.90"
            content = re.sub(r'[^\d,\.]', '', content.replace("€", ","))
            # Format "57,90" ou "57€90"
            m = re.search(r'(\d{2,3})[,\.](\d{2})', content)
            if m:
                return float(f"{m.group(1)}.{m.group(2)}")
    except Exception:
        pass
    return None


FETCHERS = {
    "Nicolas": fetch_price_nicolas,
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
