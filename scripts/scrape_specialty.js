#!/usr/bin/env node
/**
 * scotland-sky — Scraper spécialisé pour LMDW (whisky.fr) et Jardin Vouvrillon
 * Délais longs + simulation navigateur réel pour contourner anti-bot
 */

const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DATA_FILE = path.join(__dirname, '..', 'data', 'prices.json');

const WHISKIES = [
  { name: "Ardbeg 10 ans",                   query: "ardbeg 10 ans",                   brand: "ardbeg",       mustContain: null },
  { name: "Lagavulin 16 ans",                query: "lagavulin 16 ans",                 brand: "lagavulin",    mustContain: null },
  { name: "Lagavulin 8 ans",                 query: "lagavulin 8 ans",                  brand: "lagavulin",    mustContain: null },
  { name: "Laphroaig 10 ans",                query: "laphroaig 10 ans",                 brand: "laphroaig",    mustContain: null },
  { name: "Caol Ila 12 ans",                 query: "caol ila 12 ans",                  brand: "caol ila",     mustContain: null },
  { name: "Bowmore 12 ans",                  query: "bowmore 12 ans",                   brand: "bowmore",      mustContain: null },
  { name: "Big Peat",                        query: "big peat whisky",                  brand: "big peat",     mustContain: null },
  { name: "Bunnahabhain 12 ans",             query: "bunnahabhain 12 ans",              brand: "bunnahabhain", mustContain: null },
  { name: "Highland Park 12 ans",            query: "highland park 12 ans",             brand: "highland park",mustContain: null },
  { name: "Talisker 10 ans",                 query: "talisker 10 ans",                  brand: "talisker",     mustContain: null },
  { name: "Kilchoman Machir Bay",            query: "kilchoman machir bay",             brand: "kilchoman",    mustContain: null },
  { name: "Kilchoman Sanaig",               query: "kilchoman sanaig",                 brand: "kilchoman",    mustContain: null },
  { name: "Caol Ila 12 ans Signatory",       query: "caol ila 12 signatory",            brand: "caol ila",     mustContain: "signatory" },
  { name: "Bunnahabhain Staoisha Signatory", query: "bunnahabhain staoisha signatory",  brand: "bunnahabhain", mustContain: "signatory" },
  { name: "Laphroaig 10 ans Signatory",      query: "laphroaig signatory",              brand: "laphroaig",    mustContain: "signatory" },
  { name: "Ardbeg Signatory",                query: "ardbeg signatory",                 brand: "ardbeg",       mustContain: "signatory" },
];

function parsePrice(text) {
  if (!text) return null;
  const m = text.replace(/\s/g, '').match(/(\d{2,3})[,\.](\d{2})/);
  if (m) {
    const val = parseFloat(`${m[1]}.${m[2]}`);
    if (val >= 18 && val <= 600) return val;
  }
  return null;
}

function matchesBrand(name, whisky) {
  if (!name) return false;
  const n = name.toLowerCase();
  if (!whisky.brand.toLowerCase().split(' ').every(w => n.includes(w))) return false;
  if (whisky.mustContain && !n.includes(whisky.mustContain.toLowerCase())) return false;
  if (!whisky.mustContain && n.includes('signatory')) return false;
  const ageMatch = whisky.query.match(/\b(\d+)\s*ans\b/);
  if (ageMatch && !n.includes(ageMatch[1])) return false;
  return true;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── JARDIN VOUVRILLON ────────────────────────────────────────────────────────
async function scrapeJardinVouvrillon(page, whiskies, data, today) {
  console.log('\n🟢 === Jardin Vouvrillon ===');

  // Page d'accueil d'abord pour avoir les cookies
  try {
    await page.goto('https://www.jardinvouvrillon.fr', { waitUntil: 'networkidle', timeout: 40000 });
    await sleep(3000);
    try { await page.click('[data-popin-close], .btn[data-dismiss], #didomi-notice-agree-button', { timeout: 3000 }); await sleep(1000); } catch {}
    console.log('  ✅ Page accueil chargée');
  } catch(e) {
    console.log('  ❌ Accueil inaccessible:', e.message.substring(0, 60));
    return;
  }

  for (const whisky of whiskies) {
    const entry = data.whiskies.find(w => w.name === whisky.name);
    if (!entry) continue;

    const q = encodeURIComponent(whisky.query);
    const url = `https://www.jardinvouvrillon.fr/recherche?controller=search&s=${q}`;
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 40000 });
      await sleep(4000 + Math.random() * 3000);

      const results = await page.evaluate(() => {
        const cards = document.querySelectorAll('.product-miniature, article.product-miniature');
        return Array.from(cards).slice(0, 12).map(card => {
          const nameEl = card.querySelector('.product-title a, h2, h3, .h3');
          const priceEl = card.querySelector('.price, .product-price, span[itemprop="price"]');
          const linkEl = card.querySelector('a[href]');
          return {
            name: nameEl?.textContent?.trim() || '',
            priceText: priceEl?.textContent?.trim() || '',
            url: linkEl?.href || '',
          };
        });
      });

      let found = false;
      for (const r of results) {
        if (!matchesBrand(r.name, whisky)) continue;
        const price = parsePrice(r.priceText);
        if (price) {
          console.log(`  ✅ ${whisky.name} : ${price}€`);
          const existing = entry.prices.find(p => p.date === today && p.supermarket === 'Jardin Vouvrillon');
          if (existing) { existing.price = price; existing.url = r.url; }
          else entry.prices.push({ date: today, price, supermarket: 'Jardin Vouvrillon', url: r.url || url });
          found = true;
          break;
        }
      }
      if (!found) console.log(`  ⚠️  ${whisky.name} : non trouvé (${results.length} résultats)`);
    } catch(e) {
      console.log(`  ❌ ${whisky.name} : ${e.message.split('\n')[0].substring(0,60)}`);
    }

    // Délai généreux entre chaque recherche
    await sleep(6000 + Math.random() * 4000);
  }
}

// ── LA MAISON DU WHISKY (whisky.fr) ─────────────────────────────────────────
async function scrapeLMDW(page, whiskies, data, today) {
  console.log('\n🥃 === La Maison du Whisky (whisky.fr) ===');

  try {
    await page.goto('https://www.whisky.fr', { waitUntil: 'networkidle', timeout: 40000 });
    await sleep(3000);
    try { await page.click('#onetrust-accept-btn-handler', { timeout: 3000 }); await sleep(1000); } catch {}
    console.log('  ✅ Page accueil chargée');
  } catch(e) {
    console.log('  ❌ Accueil inaccessible:', e.message.substring(0, 60));
    return;
  }

  for (const whisky of whiskies) {
    const entry = data.whiskies.find(w => w.name === whisky.name);
    if (!entry) continue;

    const q = encodeURIComponent(whisky.query);
    const url = `https://www.whisky.fr/recherche.html?q=${q}`;
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 40000 });
      await sleep(4000 + Math.random() * 3000);

      const results = await page.evaluate(() => {
        const cards = document.querySelectorAll('.product-item, li.item, [class*="product-list"] li, .products li');
        return Array.from(cards).slice(0, 12).map(card => {
          const nameEl = card.querySelector('h2, h3, .product-name, [class*="name"], a');
          const priceEl = card.querySelector('[class*="price"]:not([class*="old"]), .price');
          const linkEl = card.querySelector('a[href]');
          return {
            name: nameEl?.textContent?.trim() || '',
            priceText: priceEl?.textContent?.trim() || '',
            url: linkEl?.href || '',
          };
        });
      });

      let found = false;
      for (const r of results) {
        if (!matchesBrand(r.name, whisky)) continue;
        const price = parsePrice(r.priceText);
        if (price) {
          console.log(`  ✅ ${whisky.name} : ${price}€`);
          const existing = entry.prices.find(p => p.date === today && p.supermarket === 'LMDW');
          if (existing) { existing.price = price; existing.url = r.url; }
          else entry.prices.push({ date: today, price, supermarket: 'LMDW', url: r.url || url });
          found = true;
          break;
        }
      }
      if (!found) console.log(`  ⚠️  ${whisky.name} : non trouvé (${results.length} résultats)`);
    } catch(e) {
      console.log(`  ❌ ${whisky.name} : ${e.message.split('\n')[0].substring(0,60)}`);
    }

    await sleep(8000 + Math.random() * 5000);
  }
}

// ── MAIN ─────────────────────────────────────────────────────────────────────
async function main() {
  const today = new Date().toISOString().split('T')[0];
  const data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));

  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: true,
    args: [
      '--no-sandbox', '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process',
    ],
  });

  // Contexte avec profil réaliste
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'fr-FR',
    viewport: { width: 1366, height: 768 },
    extraHTTPHeaders: {
      'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    },
  });

  const page = await context.newPage();
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    window.chrome = { runtime: {} };
  });

  // ── Jardin Vouvrillon d'abord ──
  await scrapeJardinVouvrillon(page, WHISKIES, data, today);

  // Pause entre les deux sites
  console.log('\n⏳ Pause 30 secondes entre les deux sites...');
  await sleep(30000);

  // ── LMDW ensuite ──
  await scrapeLMDW(page, WHISKIES, data, today);

  await browser.close();

  data.last_updated = today;
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));

  let found = 0;
  data.whiskies.forEach(w => { found += w.prices.filter(p => p.date === today && ['Jardin Vouvrillon','LMDW'].includes(p.supermarket)).length; });
  console.log(`\n✅ ${found} prix specialty collectés — ${today}`);

  execSync('python3 scripts/generate_page.py', { cwd: path.join(__dirname, '..'), stdio: 'inherit' });
}

main().catch(e => { console.error(e); process.exit(1); });
