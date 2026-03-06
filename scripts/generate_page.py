#!/usr/bin/env python3
"""
Génère index.html avec :
- Carte des distilleries d'Islay (Leaflet.js)
- Tableau des prix les plus bas par whisky
- Graphique d'évolution des prix (Chart.js)
"""

import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "prices.json"
OUT_FILE  = BASE_DIR / "index.html"

data = json.loads(DATA_FILE.read_text())
whiskies = data["whiskies"]
last_updated = data["last_updated"]

# ── Prix les plus bas (toutes dates confondues, par whisky) ──────────────────
def best_prices(w):
    """Retourne dict supermarket → prix min."""
    by_shop = defaultdict(list)
    for p in w["prices"]:
        by_shop[p["supermarket"]].append(p["price"])
    return {shop: min(prices) for shop, prices in by_shop.items()}

# ── Séries temporelles pour Chart.js ─────────────────────────────────────────
def time_series(w):
    by_date = defaultdict(list)
    for p in w["prices"]:
        by_date[p["date"]].append(p["price"])
    return {d: min(prices) for d, prices in sorted(by_date.items())}

COLORS = [
    "#e63946","#2a9d8f","#e9c46a","#f4a261","#264653",
    "#6a4c93","#1982c4","#8ac926","#ff595e","#6a994e",
]

# ── Distilleries Islay (coordonnées GPS) ─────────────────────────────────────
DISTILLERIES = [
    {"name": "Ardbeg",        "lat": 55.6400, "lon": -6.1079, "ppm": 50, "color": "#e63946"},
    {"name": "Lagavulin",     "lat": 55.6358, "lon": -6.1264, "ppm": 35, "color": "#2a9d8f"},
    {"name": "Laphroaig",     "lat": 55.6383, "lon": -6.1478, "ppm": 40, "color": "#e9c46a"},
    {"name": "Bowmore",       "lat": 55.7567, "lon": -6.2893, "ppm": 25, "color": "#f4a261"},
    {"name": "Caol Ila",      "lat": 55.8644, "lon": -6.1074, "ppm": 35, "color": "#264653"},
    {"name": "Bunnahabhain",  "lat": 55.8956, "lon": -6.1214, "ppm": 2,  "color": "#6a4c93"},
    {"name": "Bruichladdich", "lat": 55.7603, "lon": -6.3606, "ppm": 0,  "color": "#1982c4"},
    {"name": "Port Charlotte", "lat": 55.7381, "lon": -6.3783, "ppm": 40, "color": "#8ac926"},
    {"name": "Kilchoman",     "lat": 55.7839, "lon": -6.4536, "ppm": 50, "color": "#ff595e"},
    {"name": "Ardnahoe",      "lat": 55.9064, "lon": -6.1183, "ppm": 0,  "color": "#6a994e"},
    {"name": "Highland Park", "lat": 58.9853, "lon": -2.9604, "ppm": 20, "color": "#a8dadc"},
    {"name": "Talisker",      "lat": 57.2998, "lon": -6.3577, "ppm": 25, "color": "#457b9d"},
]

# ── Build HTML ────────────────────────────────────────────────────────────────
markers_js = "\n".join([
    f"""L.circleMarker([{d['lat']}, {d['lon']}], {{
        radius: {max(8, d['ppm']//5 + 6)},
        color: '{d['color']}',
        fillColor: '{d['color']}',
        fillOpacity: 0.8,
        weight: 2
    }}).addTo(map).bindPopup('<b>{d['name']}</b><br>Tourbe : {d['ppm']} ppm');"""
    for d in DISTILLERIES
])

# Tableau des meilleurs prix
rows = []
for w in whiskies:
    bp = best_prices(w)
    best_shop = min(bp, key=bp.get) if bp else "N/A"
    best_price = f"{bp[best_shop]:.2f}€" if bp else "N/A"
    age_str = f"{w['age']} ans" if w.get("age") else "NAS"
    rows.append(f"""<tr>
        <td><b>{w['name']}</b></td>
        <td>{w['distillery']}</td>
        <td>{w['region']}</td>
        <td>{age_str}</td>
        <td>{w['ppm']} ppm</td>
        <td class="price">{best_price}</td>
        <td>{best_shop}</td>
    </tr>""")

DASH_PATTERNS = [[], [5,5], [10,5], [5,2], [10,3,2,3], [2,2], [15,5], [5,10], [3,3], [8,3,3,3]]

# Graphique Chart.js
datasets = []
for i, w in enumerate(whiskies):
    ts = time_series(w)
    if not ts:
        continue
    values = list(ts.values())
    color = COLORS[i % len(COLORS)]
    num = i + 1
    datasets.append(f"""{{
        label: '{num}. {w["name"]}',
        data: {values},
        borderColor: '{color}',
        backgroundColor: '{color}22',
        borderDash: {DASH_PATTERNS[i % len(DASH_PATTERNS)]},
        tension: 0.3,
        pointRadius: 7,
        pointBackgroundColor: '{color}',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
    }}""")

all_labels = sorted(set(
    d for w in whiskies for d in time_series(w).keys()
))

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>🥃 Scotland Sky — Whiskies Tourbés</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; }}
  header {{ background: #16213e; padding: 1.5rem 2rem; border-bottom: 3px solid #e63946; }}
  header h1 {{ font-size: 2rem; }} header p {{ color: #aaa; margin-top: .3rem; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
  h2 {{ color: #e9c46a; margin: 2rem 0 1rem; font-size: 1.4rem; border-left: 4px solid #e63946; padding-left: .8rem; }}
  #map {{ height: 450px; border-radius: 12px; margin-bottom: 2rem; border: 2px solid #e63946; }}
  table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; overflow: hidden; }}
  th {{ background: #e63946; color: white; padding: .8rem; text-align: left; }}
  td {{ padding: .7rem .8rem; border-bottom: 1px solid #2a2a4e; }}
  tr:hover td {{ background: #2a2a4e; }}
  .price {{ font-weight: bold; color: #e9c46a; font-size: 1.1rem; }}
  .chart-box {{ background: #16213e; border-radius: 12px; padding: 1.5rem; margin-top: 2rem; }}
  .chart-wrap {{ display: flex; gap: 1.5rem; align-items: flex-start; }}
  .chart-legend {{ min-width: 200px; background: #16213e; border-radius: 10px; padding: 1rem; }}
  .chart-legend li {{ list-style: none; padding: .4rem .3rem; font-size: .92rem; border-bottom: 1px solid #2a2a4e; display: flex; align-items: center; gap: .5rem; }}
  .legend-num {{ display: inline-block; min-width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; font-weight: bold; font-size: .85rem; color: #fff; flex-shrink: 0; }}
  footer {{ text-align: center; padding: 2rem; color: #666; font-size: .85rem; }}
</style>
</head>
<body>
<header>
  <h1>🥃 Scotland Sky</h1>
  <p>Tracker de prix des whiskies écossais tourbés — Carrefour &amp; Intermarché</p>
  <p style="margin-top:.5rem;font-size:.85rem;color:#888">Mise à jour : {last_updated}</p>
</header>
<div class="container">

  <h2>🗺️ Carte des Distilleries</h2>
  <div id="map"></div>

  <h2>🛒 Prix les plus bas par whisky</h2>
  <table>
    <thead><tr>
      <th>Whisky</th><th>Distillerie</th><th>Région</th>
      <th>Âge</th><th>Tourbe</th><th>Prix min</th><th>Supermarché</th>
    </tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>

  <h2>📈 Évolution des prix</h2>
  <div class="chart-wrap">
    <div class="chart-box" style="flex:1">
      <canvas id="priceChart" height="400"></canvas>
    </div>
    <ul class="chart-legend">
      {''.join([
        f'<li><span class="legend-num" style="background:{COLORS[i % len(COLORS)]}">{i+1}</span> {w["name"]}</li>'
        for i, w in enumerate(whiskies)
      ])}
    </ul>
  </div>

</div>
<footer>
  🍷 Tracker créé depuis Morez (Jura) — <a href="https://github.com/jura39bot/scotland-sky" style="color:#e63946">GitHub</a>
</footer>

<script>
var map = L.map('map').setView([55.75, -6.3], 9);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '© OpenStreetMap'
}}).addTo(map);
{markers_js}

// Zoom sur les îles d'Écosse
var bounds = L.latLngBounds([55.6, -6.6], [56.1, -5.9]);
map.fitBounds(bounds);

// Chart.js
var ctx = document.getElementById('priceChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {json.dumps(all_labels)},
    datasets: [{','.join(datasets)}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ labels: {{ color: '#eee' }} }},
      title: {{ display: true, text: 'Prix les plus bas / semaine (€)', color: '#e9c46a', font: {{ size: 16 }} }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '#aaa' }}, grid: {{ color: '#2a2a4e' }} }},
      y: {{ ticks: {{ color: '#aaa', callback: v => v + '€' }}, grid: {{ color: '#2a2a4e' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

OUT_FILE.write_text(html, encoding="utf-8")
print(f"✅ index.html généré — {len(whiskies)} whiskies")

if __name__ == "__main__":
    pass
