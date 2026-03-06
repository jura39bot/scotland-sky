#!/usr/bin/env python3
"""
Génère index.html avec :
- Carte des distilleries d'Islay (Leaflet.js)
- Tableau des prix les plus bas par whisky
- Graphique d'évolution des prix (Chart.js) avec numéros dans les bulles
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

def best_prices(w):
    by_shop = defaultdict(list)
    for p in w["prices"]:
        by_shop[p["supermarket"]].append(p["price"])
    return {shop: min(prices) for shop, prices in by_shop.items()}

def time_series(w):
    by_date = defaultdict(list)
    for p in w["prices"]:
        by_date[p["date"]].append(p["price"])
    return {d: min(prices) for d, prices in sorted(by_date.items())}

COLORS = [
    "#e63946","#2a9d8f","#e9c46a","#f4a261","#264653",
    "#6a4c93","#1982c4","#8ac926","#ff595e","#6a994e",
    "#a8dadc","#457b9d","#e76f51","#52b788","#f72585",
    "#b5838d","#ffb703","#023047","#219ebc","#fb8500",
]

DASH_PATTERNS = [
    [], [5,5], [10,5], [5,2], [10,3,2,3],
    [2,2], [15,5], [5,10], [3,3], [8,3,3,3],
    [], [5,5], [10,5], [5,2], [10,3,2,3],
    [2,2], [15,5], [5,10], [3,3], [8,3,3,3],
]

DISTILLERIES = [
    {"name": "Ardbeg",         "lat": 55.6400, "lon": -6.1079, "ppm": 50},
    {"name": "Lagavulin",      "lat": 55.6358, "lon": -6.1264, "ppm": 35},
    {"name": "Laphroaig",      "lat": 55.6383, "lon": -6.1478, "ppm": 40},
    {"name": "Bowmore",        "lat": 55.7567, "lon": -6.2893, "ppm": 25},
    {"name": "Caol Ila",       "lat": 55.8644, "lon": -6.1074, "ppm": 35},
    {"name": "Bunnahabhain",   "lat": 55.8956, "lon": -6.1214, "ppm": 2 },
    {"name": "Bruichladdich",  "lat": 55.7603, "lon": -6.3606, "ppm": 0 },
    {"name": "Port Charlotte", "lat": 55.7381, "lon": -6.3783, "ppm": 40},
    {"name": "Kilchoman",      "lat": 55.7839, "lon": -6.4536, "ppm": 50},
    {"name": "Ardnahoe",       "lat": 55.9064, "lon": -6.1183, "ppm": 0 },
    {"name": "Highland Park",  "lat": 58.9853, "lon": -2.9604, "ppm": 20},
    {"name": "Talisker",       "lat": 57.2998, "lon": -6.3577, "ppm": 25},
]

DIST_COLORS = ["#e63946","#2a9d8f","#e9c46a","#f4a261","#264653",
               "#6a4c93","#1982c4","#8ac926","#ff595e","#6a994e","#a8dadc","#457b9d"]

markers_js = "\n".join([
    f"""L.circleMarker([{d['lat']}, {d['lon']}], {{
        radius: {max(8, d['ppm']//5 + 6)},
        color: '{DIST_COLORS[i]}',
        fillColor: '{DIST_COLORS[i]}',
        fillOpacity: 0.8,
        weight: 2
    }}).addTo(map).bindPopup('<b>{d['name']}</b><br>Tourbe : {d['ppm']} ppm');"""
    for i, d in enumerate(DISTILLERIES)
])

# Tableau des meilleurs prix
rows = []
for idx, w in enumerate(whiskies):
    bp = best_prices(w)
    # best_prices_with_url : pour chaque shop, prix min + URL associée
    def best_with_url(w):
        by_shop = {}
        for p in w["prices"]:
            shop = p["supermarket"]
            if shop not in by_shop or p["price"] < by_shop[shop]["price"]:
                by_shop[shop] = {"price": p["price"], "url": p.get("url", "")}
        return by_shop

    bpu = best_with_url(w)
    best_shop = min(bpu, key=lambda s: bpu[s]["price"]) if bpu else None
    best_price = f"{bpu[best_shop]['price']:.2f}€" if best_shop else "N/A"
    best_url   = bpu[best_shop]["url"] if best_shop else ""

    # Tous les liens disponibles (un par source)
    all_links = ""
    shop_icons = {"Carrefour": "🔵", "Intermarché": "🔴", "Cdiscount": "🟠", "Jardin Vouvrillon": "🟢", "LMDW": "🥃"}
    for shop, info in sorted(bpu.items(), key=lambda x: x[1]["price"]):
        icon = shop_icons.get(shop, "🔗")
        price_str = f'{info["price"]:.2f}€'
        if info["url"]:
            title = f'{shop} — {price_str}'
            all_links += f'<a href="{info["url"]}" target="_blank" style="text-decoration:none;margin-right:4px" title="{title}">{icon} {price_str}</a> '
        else:
            all_links += f'<span style="color:#666;margin-right:4px">{icon} {price_str}</span> '

    age_str = f"{w['age']} ans" if w.get("age") else "NAS"
    num = idx + 1
    color = COLORS[idx % len(COLORS)]
    rows.append(f"""<tr>
        <td><span style="display:inline-block;min-width:22px;height:22px;border-radius:50%;background:{color};color:#fff;text-align:center;line-height:22px;font-weight:bold;font-size:.8rem;margin-right:6px">{num}</span><b>{w['name']}</b></td>
        <td>{w['distillery']}</td>
        <td>{w['region']}</td>
        <td>{age_str}</td>
        <td>{w['ppm']} ppm</td>
        <td class="price">{best_price}</td>
        <td>{best_shop or 'N/A'}</td>
        <td>{all_links if all_links else '<span style="color:#555">—</span>'}</td>
    </tr>""")

# Graphique Chart.js — datasets
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
        backgroundColor: '{color}33',
        borderDash: {DASH_PATTERNS[i % len(DASH_PATTERNS)]},
        tension: 0.3,
        pointRadius: 13,
        pointHoverRadius: 15,
        pointBackgroundColor: '{color}',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointLabel: {num}
    }}""")

all_labels = sorted(set(
    d for w in whiskies for d in time_series(w).keys()
))

# Légende numérotée latérale
legend_items = "".join([
    f'<li><span class="legend-num" style="background:{COLORS[i % len(COLORS)]}">{i+1}</span> {w["name"]}</li>'
    for i, w in enumerate(whiskies)
])

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
  header h1 {{ font-size: 2rem; }}
  header p {{ color: #aaa; margin-top: .3rem; }}
  .container {{ max-width: 1300px; margin: 0 auto; padding: 2rem; }}
  h2 {{ color: #e9c46a; margin: 2rem 0 1rem; font-size: 1.4rem; border-left: 4px solid #e63946; padding-left: .8rem; }}
  #map {{ height: 450px; border-radius: 12px; margin-bottom: 2rem; border: 2px solid #e63946; }}
  table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; overflow: hidden; }}
  th {{ background: #e63946; color: white; padding: .8rem; text-align: left; font-size: .9rem; }}
  td {{ padding: .6rem .8rem; border-bottom: 1px solid #2a2a4e; font-size: .9rem; }}
  tr:hover td {{ background: #2a2a4e; }}
  .price {{ font-weight: bold; color: #e9c46a; font-size: 1.05rem; }}
  .chart-wrap {{ display: flex; gap: 1.5rem; align-items: flex-start; margin-top: 1rem; }}
  .chart-box {{ background: #16213e; border-radius: 12px; padding: 1.5rem; flex: 1; }}
  .chart-legend {{ min-width: 210px; background: #16213e; border-radius: 10px; padding: .8rem; }}
  .chart-legend ul {{ padding: 0; }}
  .chart-legend li {{ list-style: none; padding: .35rem .2rem; font-size: .88rem; border-bottom: 1px solid #2a2a4e; display: flex; align-items: center; gap: .5rem; }}
  .legend-num {{ display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; border-radius: 50%; font-weight: bold; font-size: .82rem; color: #fff; flex-shrink: 0; }}
  .tag-sig {{ font-size: .7rem; background: #6a4c93; color: #fff; border-radius: 4px; padding: 1px 4px; margin-left: 2px; }}
  footer {{ text-align: center; padding: 2rem; color: #666; font-size: .85rem; margin-top: 2rem; }}
</style>
</head>
<body>
<header>
  <h1>🥃 Scotland Sky</h1>
  <p>Tracker de prix — whiskies écossais tourbés</p>
  <p style="font-size:.82rem;color:#888;margin-top:.3rem">Sources : Carrefour Drive Lons-le-Saunier 🔵 · Intermarché Morez 🔴 · Cdiscount 🟠 · Jardin Vouvrillon 🟢 · whisky.fr (LMDW) 🥃 &nbsp;|&nbsp; MAJ : {last_updated}</p>
</header>
<div class="container">

  <h2>🗺️ Carte des Distilleries</h2>
  <div id="map"></div>

  <h2>🛒 Prix les plus bas par whisky</h2>
  <table>
    <thead><tr>
      <th>#&nbsp; Whisky</th><th>Distillerie</th><th>Région</th>
      <th>Âge</th><th>Tourbe</th><th>Prix min</th><th>Source</th><th>Commander</th>
    </tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>

  <h2>📈 Évolution des prix</h2>
  <div class="chart-wrap">
    <div class="chart-box">
      <canvas id="priceChart" height="380"></canvas>
    </div>
    <div class="chart-legend">
      <p style="color:#e9c46a;font-weight:bold;margin-bottom:.5rem;font-size:.9rem">Légende</p>
      <ul>{legend_items}</ul>
    </div>
  </div>

</div>
<footer>
  🍷 Depuis Morez (Jura) — <a href="https://github.com/jura39bot/scotland-sky" style="color:#e63946">GitHub</a>
</footer>

<script>
// ── Plugin : numéro dans chaque bulle ──────────────────────────────────────
const numberInBubbles = {{
  id: 'numberInBubbles',
  afterDatasetsDraw(chart) {{
    const ctx = chart.ctx;
    chart.data.datasets.forEach((ds, i) => {{
      const meta = chart.getDatasetMeta(i);
      if (meta.hidden) return;
      const num = String(i + 1);
      ctx.save();
      ctx.font = 'bold ' + (num.length > 1 ? '8' : '9') + 'px sans-serif';
      ctx.fillStyle = '#fff';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      meta.data.forEach(pt => {{ ctx.fillText(num, pt.x, pt.y); }});
      ctx.restore();
    }});
  }}
}};

// ── Carte ──────────────────────────────────────────────────────────────────
var map = L.map('map').setView([55.75, -6.3], 9);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '© OpenStreetMap'
}}).addTo(map);
{markers_js}
map.fitBounds(L.latLngBounds([55.6, -6.6], [56.1, -5.9]));

// ── Graphique ──────────────────────────────────────────────────────────────
var ctx = document.getElementById('priceChart').getContext('2d');
Chart.register(numberInBubbles);
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {json.dumps(all_labels)},
    datasets: [{','.join(datasets)}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      numberInBubbles: {{}},
      legend: {{
        labels: {{
          color: '#eee',
          font: {{ size: 11 }},
          boxWidth: 20,
          padding: 10
        }}
      }},
      title: {{
        display: true,
        text: 'Prix les plus bas / semaine (€)',
        color: '#e9c46a',
        font: {{ size: 15 }}
      }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '#aaa' }}, grid: {{ color: '#2a2a4e' }} }},
      y: {{
        ticks: {{ color: '#aaa', callback: v => v + '€' }},
        grid: {{ color: '#2a2a4e' }}
      }}
    }}
  }}
}});
</script>
</body>
</html>"""

OUT_FILE.write_text(html, encoding="utf-8")
print(f"✅ index.html généré — {len(whiskies)} whiskies")
