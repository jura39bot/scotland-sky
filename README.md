# 🥃 Scotland Sky — Whiskies Tourbés Tracker

> Veille prix des **whiskies écossais tourbés** dans les supermarchés français en ligne  
> Carte interactive des distilleries d'Islay (Écosse)  
> **Mise à jour automatique chaque lundi**

🗺️ **[👉 Ouvrir le tracker](https://jura39bot.github.io/scotland-sky/)**

---

## 🏭 Distilleries suivies

| Distillerie | Région | Tourbe (ppm) | Style |
|-------------|--------|--------------|-------|
| **Ardbeg** | Islay | ~50 ppm | Fumé intense, maritime, complexe |
| **Lagavulin** | Islay | ~35 ppm | Fumé puissant, tourbe douce |
| **Laphroaig** | Islay | ~40 ppm | Médicinal, iodé, tourbe franche |
| **Caol Ila** | Islay | ~35 ppm | Fumé propre, citron, maritime |
| **Bowmore** | Islay | ~25 ppm | Fumé doux, floral, fruité |
| **Bunnahabhain** | Islay | ~2 ppm | Maritime, peu tourbé |
| **Port Charlotte** | Islay | ~40 ppm | Fumé expressif |
| **Kilchoman** | Islay | ~50 ppm | Jeune, agricole, fumé |
| **Highland Park** | Orkney | ~20 ppm | Tourbé délicat, bruyère |
| **Talisker** | Skye | ~25 ppm | Poivré, maritime, fumé |
| **Big Peat** | Islay (blend) | ~55 ppm | Assemblage Islay tourbé |

---

## 🛒 Supermarchés suivis

- **Carrefour** — [carrefour.fr](https://www.carrefour.fr)
- **Intermarché** — [intermarche.com](https://www.intermarche.com)

---

## 📊 Données

- `data/prices.json` — Historique des prix collectés
- `index.html` — Page web générée automatiquement

---

## 🔄 Mise à jour automatique

Le script `scripts/collect_prices.py` tourne chaque **lundi à 6h UTC** via GitHub Actions.  
Il scrape les prix et met à jour `data/prices.json` + `index.html`.

Pour forcer une mise à jour : **Actions → Weekly Whisky Price Update → Run workflow**

---

*Tracker créé depuis Morez (Jura) 🍷*
