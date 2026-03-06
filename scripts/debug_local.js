#!/usr/bin/env node
const { chromium } = require('playwright-core');

async function main() {
  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'fr-FR', viewport: { width: 1280, height: 900 },
  });
  const page = await context.newPage();
  await page.addInitScript(() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); });

  // ── Carrefour : sélectionner Drive Lons puis chercher ──────────────────────
  console.log('=== Carrefour Drive Lons-le-Saunier ===');
  await page.goto('https://www.carrefour.fr/magasin/lons-le-saunier/drive', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2000);
  try { await page.click('#onetrust-accept-btn-handler', { timeout: 3000 }); await page.waitForTimeout(1000); } catch {}

  // Cliquer "Choisir ce drive"
  try {
    await page.click('button:has-text("Choisir ce drive")', { timeout: 5000 });
    await page.waitForTimeout(2000);
    console.log('✅ Drive Lons sélectionné');
  } catch(e) { console.log('❌ Bouton non trouvé:', e.message.substring(0,60)); }

  // Vérifier l'URL après sélection
  console.log('URL après sélection:', page.url());

  // Maintenant chercher ardbeg
  await page.goto('https://www.carrefour.fr/s?q=ardbeg+whisky&lang=fr_FR', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2000);

  const storeInPage = await page.evaluate(() => {
    const m = document.body.innerHTML.match(/"storeCode"\s*:\s*"([^"]+)"/);
    const m2 = document.body.innerHTML.match(/"sapStoreId"\s*:\s*"([^"]+)"/);
    const m3 = document.body.innerHTML.match(/STORE_VIRTUEL|DRIVE|store-\w+/);
    return { storeCode: m?.[1], sapStoreId: m2?.[1], storeType: m3?.[0] };
  });
  console.log('Store dans page recherche:', storeInPage);

  // Récupérer les cookies pour voir si un cookie de magasin est défini
  const cookies = await context.cookies();
  const storeCookies = cookies.filter(c => /store|magasin|shop/i.test(c.name));
  console.log('Cookies store:', storeCookies.map(c => `${c.name}=${c.value.substring(0,30)}`));

  // ── Intermarché : naviguer via le site et choisir Morez ───────────────────
  console.log('\n=== Intermarché Morez ===');
  await page.goto('https://www.intermarche.com/recherche?q=ardbeg+whisky', { waitUntil: 'networkidle', timeout: 25000 });
  await page.waitForTimeout(2000);
  try { await page.click('#popin_tc_privacy_button_2, #onetrust-accept-btn-handler', { timeout: 3000 }); await page.waitForTimeout(1000); } catch {}

  // Chercher bouton de sélection de magasin
  const itmMagasinBtn = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button, a, [class*="store"], [class*="magasin"]'));
    return btns.filter(b => /magasin|choisir|mon magasin|localisation/i.test(b.textContent || b.className))
               .map(b => ({ text: (b.textContent||'').trim().substring(0,50), class: b.className.substring(0,50) }))
               .slice(0, 5);
  });
  console.log('Boutons magasin ITM:', JSON.stringify(itmMagasinBtn));

  // Prix trouvés sans filtre magasin
  const prices = await page.evaluate(() => {
    const results = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while (node = walker.nextNode()) {
      const text = node.textContent.trim();
      if (/\d{2,3}[,\.]\d{2}/.test(text) && text.length < 20) {
        const parent = node.parentElement;
        results.push({ text, class: parent.className.substring(0, 60) });
      }
    }
    return results.slice(0, 10);
  });
  console.log('Prix trouvés ITM:', prices);

  await page.screenshot({ path: '/tmp/itm_search.png' });
  await browser.close();
}
main().catch(e => { console.error(e); process.exit(1); });
