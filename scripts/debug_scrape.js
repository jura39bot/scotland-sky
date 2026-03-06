#!/usr/bin/env node
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

async function main() {
  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'fr-FR',
    viewport: { width: 1280, height: 900 },
  });

  const page = await context.newPage();
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  const url = 'https://www.carrefour.fr/p/whisky-ardbeg-10-ans-46-3002302622321';
  console.log('Chargement:', url);
  await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Screenshot
  await page.screenshot({ path: '/tmp/carrefour_debug.png', fullPage: false });
  console.log('Screenshot: /tmp/carrefour_debug.png');

  // Dump du HTML autour des prix
  const html = await page.content();
  const priceSection = html.match(/["\s]price["\s\-_][^<]{0,500}/gi)?.slice(0, 5) || [];
  console.log('\n=== Fragments contenant "price" ===');
  priceSection.forEach(f => console.log(f.substring(0, 200)));

  // Chercher tous les textes contenant des patterns de prix
  const prices = await page.evaluate(() => {
    const results = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while (node = walker.nextNode()) {
      const text = node.textContent.trim();
      if (/\d{2,3}[,\.]\d{2}/.test(text) && text.length < 30) {
        const parent = node.parentElement;
        results.push({ text, tag: parent.tagName, class: parent.className.substring(0, 80) });
      }
    }
    return results.slice(0, 20);
  });

  console.log('\n=== Textes avec pattern prix ===');
  prices.forEach(p => console.log(JSON.stringify(p)));

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
