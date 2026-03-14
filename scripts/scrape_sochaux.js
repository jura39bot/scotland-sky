const { chromium } = require('playwright-core');

async function main() {
  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    locale: 'fr-FR',
  });

  await page.goto('https://www.foot-direct.com/equipe/fc-sochaux-montbeliard', 
    { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);

  const matches = await page.evaluate(() => {
    // Chercher les éléments de matchs
    const rows = document.querySelectorAll('[class*="match"], [class*="result"], [class*="fixture"], tr');
    const results = [];
    rows.forEach(row => {
      const text = row.textContent?.trim();
      if (text && text.length > 10 && text.length < 200) {
        results.push(text.replace(/\s+/g, ' '));
      }
    });
    return results.slice(0, 50);
  });
  
  console.log('=== Matches trouvés ===');
  matches.forEach(m => console.log(m));
  
  await page.screenshot({ path: '/tmp/sochaux_results.png' });
  await browser.close();
}
main().catch(e => { console.error(e); process.exit(1); });
