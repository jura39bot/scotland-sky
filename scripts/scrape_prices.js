#!/usr/bin/env node
/**
 * scotland-sky — Collecte des vrais prix via Playwright + Chrome
 * Sources : Carrefour Drive Lons-le-Saunier, Intermarché Morez, Cdiscount, LMDW
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
  { name: "Kilchoman Machir Bay",             query: "kilchoman machir bay",             brand: "kilchoman",    mustContain: null },
  { name: "Kilchoman Sanaig",                query: "kilchoman sanaig",                 brand: "kilchoman",    mustContain: null },
  // Signatory — mustContain obligatoire : filtre les résultats sans "signatory" dans le nom
  { name: "Caol Ila 12 ans Signatory",       query: "caol ila signatory vintage",       brand: "caol ila",     mustContain: "signatory" },
  { name: "Bunnahabhain Staoisha Signatory", query: "bunnahabhain staoisha signatory",  brand: "bunnahabhain", mustContain: "signatory" },
  { name: "Laphroaig 10 ans Signatory",      query: "laphroaig signatory vintage",      brand: "laphroaig",    mustContain: "signatory" },
  { name: "Ardbeg Signatory",                query: "ardbeg signatory vintage",         brand: "ardbeg",       mustContain: "signatory" },
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

/**
 * Vérifie que le nom du produit correspond au whisky recherché :
 * - La marque (brand) doit être présente
 * - Si mustContain (ex: "signatory") → doit être dans le nom
 * - Si PAS mustContain → "signatory" ne doit PAS être dans le nom (évite les faux positifs)
 */
function matchesBrand(name, whisky) {
  if (!name) return false;
  const n = name.toLowerCase();
  // Marque présente ?
  if (!whisky.brand.toLowerCase().split(' ').every(w => n.includes(w))) return false;
  // Whisky Signatory : le mot "signatory" doit être dans le nom retourné
  if (whisky.mustContain && !n.includes(whisky.mustContain.toLowerCase())) {
    console.log(`  ↳ Rejeté (pas "${whisky.mustContain}" dans "${name}")`);
    return false;
  }
  // Whisky normal : rejeter si le nom contient "signatory" (c'est un autre produit)
  if (!whisky.mustContain && n.includes('signatory')) {
    console.log(`  ↳ Rejeté (signatory trouvé dans "${name}" mais on veut la version normale)`);
    return false;
  }
  return true;
}

// ── CARREFOUR (Drive Lons-le-Saunier, cookie FRONTAL_STORE=840010) ───────────
async function searchCarrefour(page, whisky) {
  const q = encodeURIComponent(whisky.query);
  const url = `https://www.carrefour.fr/s?q=${q}&lang=fr_FR`;
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
    await page.waitForTimeout(2000);
    try { await page.click('#onetrust-accept-btn-handler', { timeout: 2000 }); } catch {}

    const results = await page.evaluate(() => {
      const cards = document.querySelectorAll('[class*="product-list-card"], article[class*="product"]');
      return Array.from(cards).slice(0, 8).map(card => {
        const nameEl = card.querySelector('[class*="title"], [class*="name"], h2, h3');
        const priceInt = card.querySelector('[class*="integer"], [class*="price-amount"]');
        const perLitreEl = card.querySelector('[class*="per-unit"]');
        const linkEl = card.querySelector('a[href]');
        return {
          name: nameEl?.textContent?.trim() || '',
          priceText: priceInt?.textContent?.trim() || '',
          perLitre: perLitreEl?.textContent?.trim() || '',
          url: linkEl?.href || '',
        };
      });
    });

    for (const r of results) {
      if (!matchesBrand(r.name, whisky)) continue;
      let price = parsePrice(r.priceText);
      if (!price && r.perLitre) {
        const perL = parsePrice(r.perLitre);
        if (perL) price = Math.round(perL * 0.7 * 100) / 100;
      }
      if (price) {
        console.log(`✅ ${whisky.name} @ Carrefour : ${price}€`);
        return { price, url: r.url || url };
      }
    }
    console.log(`⚠️  ${whisky.name} @ Carrefour : non trouvé`);
    return null;
  } catch (e) {
    console.log(`❌ ${whisky.name} @ Carrefour : ${e.message.split('\n')[0]}`);
    return null;
  }
}

// ── INTERMARCHÉ (Morez 03737) ────────────────────────────────────────────────
async function searchIntermarche(page, whisky) {
  const q = encodeURIComponent(whisky.query);
  const url = `https://www.intermarche.com/recherche?q=${q}`;
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
    await page.waitForTimeout(2000);
    try { await page.click('#popin_tc_privacy_button_2, #onetrust-accept-btn-handler', { timeout: 2000 }); } catch {}

    const results = await page.evaluate(() => {
      const cards = document.querySelectorAll('[class*="product"], article');
      return Array.from(cards).slice(0, 8).map(card => {
        const nameEl = card.querySelector('[class*="title"], [class*="name"], h2, h3');
        const priceEl = card.querySelector('[class*="price"]');
        const linkEl = card.querySelector('a[href]');
        return {
          name: nameEl?.textContent?.trim() || '',
          priceText: priceEl?.textContent?.trim() || '',
          url: linkEl?.href || '',
        };
      });
    });

    for (const r of results) {
      if (!matchesBrand(r.name, whisky)) continue;
      const price = parsePrice(r.priceText);
      if (price) {
        console.log(`✅ ${whisky.name} @ Intermarché : ${price}€`);
        return { price, url: r.url || url };
      }
    }
    console.log(`⚠️  ${whisky.name} @ Intermarché : non trouvé`);
    return null;
  } catch (e) {
    console.log(`❌ ${whisky.name} @ Intermarché : ${e.message.split('\n')[0]}`);
    return null;
  }
}

// ── CDISCOUNT ────────────────────────────────────────────────────────────────
async function searchCdiscount(page, whisky) {
  const q = encodeURIComponent(whisky.query + ' whisky');
  const url = `https://www.cdiscount.com/search/10/${q}.html`;
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
    await page.waitForTimeout(2000);
    try { await page.click('#footer_tc_privacy_button_2, #onetrust-accept-btn-handler', { timeout: 2000 }); } catch {}

    const results = await page.evaluate(() => {
      const cards = document.querySelectorAll('.prdtBId, [class*="product-item"], article');
      return Array.from(cards).slice(0, 8).map(card => {
        const nameEl = card.querySelector('h2, h3, [class*="title"], [class*="name"], a');
        const priceEl = card.querySelector('[class*="price"], [class*="Price"]');
        const linkEl = card.querySelector('a[href]');
        return {
          name: nameEl?.textContent?.trim() || '',
          priceText: priceEl?.textContent?.trim() || '',
          url: linkEl?.href || '',
        };
      });
    });

    for (const r of results) {
      if (!matchesBrand(r.name, whisky)) continue;
      const price = parsePrice(r.priceText);
      if (price) {
        console.log(`✅ ${whisky.name} @ Cdiscount : ${price}€`);
        return { price, url: r.url || url };
      }
    }
    console.log(`⚠️  ${whisky.name} @ Cdiscount : non trouvé`);
    return null;
  } catch (e) {
    console.log(`❌ ${whisky.name} @ Cdiscount : ${e.message.split('\n')[0]}`);
    return null;
  }
}

// ── JARDIN VOUVRILLON ────────────────────────────────────────────────────────
async function searchJardinVouvrillon(page, whisky) {
  const q = encodeURIComponent(whisky.query);
  const url = `https://www.jardinvouvrillon.fr/recherche?controller=search&s=${q}`;
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
    await page.waitForTimeout(2000);
    try { await page.click('#onetrust-accept-btn-handler, .btn-primary[data-role="popin-close"]', { timeout: 2000 }); } catch {}

    const results = await page.evaluate(() => {
      // PrestaShop standard selectors
      const cards = document.querySelectorAll('.product-miniature, article.product-miniature, .product-container');
      return Array.from(cards).slice(0, 10).map(card => {
        const nameEl = card.querySelector('.product-title, h2, h3, .h3');
        const priceEl = card.querySelector('.price, .product-price, span[itemprop="price"]');
        const linkEl = card.querySelector('a[href]');
        return {
          name: nameEl?.textContent?.trim() || '',
          priceText: priceEl?.textContent?.trim() || '',
          url: linkEl?.href || '',
        };
      });
    });

    for (const r of results) {
      if (!matchesBrand(r.name, whisky)) continue;
      const price = parsePrice(r.priceText);
      if (price) {
        console.log(`✅ ${whisky.name} @ Jardin Vouvrillon : ${price}€`);
        return { price, url: r.url || url };
      }
    }
    console.log(`⚠️  ${whisky.name} @ Jardin Vouvrillon : non trouvé`);
    return null;
  } catch (e) {
    console.log(`❌ ${whisky.name} @ Jardin Vouvrillon : ${e.message.split('\n')[0]}`);
    return null;
  }
}

// ── LA MAISON DU WHISKY (whisky.fr) ─────────────────────────────────────────
async function searchLMDW(page, whisky) {
  const q = encodeURIComponent(whisky.query);
  const url = `https://www.whisky.fr/recherche.html?q=${q}`;
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
    await page.waitForTimeout(2000);
    try { await page.click('#onetrust-accept-btn-handler, [class*="cookie"] button', { timeout: 2000 }); } catch {}

    const results = await page.evaluate(() => {
      const cards = document.querySelectorAll('.product-item, [class*="product"], article, li[class*="item"]');
      return Array.from(cards).slice(0, 10).map(card => {
        const nameEl = card.querySelector('h2, h3, [class*="name"], [class*="title"], a');
        const priceEl = card.querySelector('[class*="price"], [class*="Price"]');
        const linkEl = card.querySelector('a[href]');
        return {
          name: nameEl?.textContent?.trim() || '',
          priceText: priceEl?.textContent?.trim() || '',
          url: linkEl?.href ? (linkEl.href.startsWith('http') ? linkEl.href : 'https://www.whisky.fr' + linkEl.getAttribute('href')) : '',
        };
      });
    });

    for (const r of results) {
      if (!matchesBrand(r.name, whisky)) continue;
      const price = parsePrice(r.priceText);
      if (price) {
        console.log(`✅ ${whisky.name} @ LMDW : ${price}€`);
        return { price, url: r.url || url };
      }
    }
    console.log(`⚠️  ${whisky.name} @ LMDW : non trouvé`);
    return null;
  } catch (e) {
    console.log(`❌ ${whisky.name} @ LMDW : ${e.message.split('\n')[0]}`);
    return null;
  }
}

// ── MAIN ─────────────────────────────────────────────────────────────────────
async function main() {
  const today = new Date().toISOString().split('T')[0];
  const data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  let updated = 0;

  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled'],
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'fr-FR',
    viewport: { width: 1280, height: 900 },
  });

  // ── Cookie Drive Carrefour Lons-le-Saunier ──────────────────────────────
  await context.addCookies([{
    name: 'FRONTAL_STORE', value: '840010',
    domain: '.carrefour.fr', path: '/',
  }]);

  // ── Intermarché : initialiser magasin Morez (03737) ─────────────────────
  const itmPage = await context.newPage();
  try {
    await itmPage.goto('https://www.intermarche.com/magasins/03737/morez-39400/infos-pratiques',
      { waitUntil: 'domcontentloaded', timeout: 15000 });
    await itmPage.waitForTimeout(1500);
    try { await itmPage.click('button:has-text("Choisir"), button:has-text("Sélectionner")', { timeout: 3000 }); } catch {}
    console.log('✅ Magasin Intermarché Morez initialisé');
  } catch(e) { console.log('⚠️  Init ITM Morez:', e.message.substring(0,60)); }
  await itmPage.close();

  const page = await context.newPage();
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  const SOURCES = [
    { name: 'Carrefour',         fn: searchCarrefour },
    { name: 'Intermarché',       fn: searchIntermarche },
    { name: 'Cdiscount',         fn: searchCdiscount },
    { name: 'Jardin Vouvrillon', fn: searchJardinVouvrillon },
    { name: 'LMDW',              fn: searchLMDW },
  ];

  for (const whisky of WHISKIES) {
    const entry = data.whiskies.find(w => w.name === whisky.name);
    if (!entry) { console.log(`⚠️  Entrée "${whisky.name}" absente du JSON`); continue; }

    for (const src of SOURCES) {
      const result = await src.fn(page, whisky);
      if (result) {
        const existing = entry.prices.find(p => p.date === today && p.supermarket === src.name);
        if (existing) { existing.price = result.price; existing.url = result.url; }
        else entry.prices.push({ date: today, price: result.price, supermarket: src.name, url: result.url });
        updated++;
      }
      await page.waitForTimeout(800 + Math.random() * 700);
    }
  }

  await browser.close();
  data.last_updated = today;
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
  console.log(`\n✅ ${updated} prix collectés — ${today}`);

  execSync('python3 scripts/generate_page.py', { cwd: path.join(__dirname, '..'), stdio: 'inherit' });
}

main().catch(e => { console.error(e); process.exit(1); });
