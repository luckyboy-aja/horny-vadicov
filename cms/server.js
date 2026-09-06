import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');
const PUBLIC_DIR = path.join(ROOT_DIR, 'public');
const PORT = process.env.PORT || 3001;

// Pomocné funkcie pre generovanie slugov a bezpečné názvy
function slugify(text) {
  return text
    .toString()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 70);
}

// MIME typy pre statické súbory
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.pdf': 'application/pdf',
  '.mp3': 'audio/mpeg'
};

// Parsovanie JSON body
function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
      if (body.length > 50 * 1024 * 1024) { // limit 50MB
        reject(new Error('Payload too large'));
      }
    });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (err) {
        reject(err);
      }
    });
    req.on('error', reject);
  });
}

// CORS a JSON odpoveď
function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  });
  res.end(JSON.stringify(data));
}

// Statický súborový server
function serveStatic(req, res, filePath) {
  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('404 Nenájdené');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    res.writeHead(200, {
      'Content-Type': contentType,
      'Content-Length': stats.size,
      'Access-Control-Allow-Origin': '*'
    });
    fs.createReadStream(filePath).pipe(res);
  });
}

// Rekurzívne vyhľadávanie všetkých HTML stránok v public/
function scanAllPages(dir = PUBLIC_DIR, baseRel = '') {
  let results = [];
  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    // Ignorujeme systémové, admin a build priečinky
    if (entry.name === 'admin' || entry.name === 'dist' || entry.name === 'node_modules' || entry.name === 'src' || entry.name === '.git') {
      continue;
    }

    const fullPath = path.join(dir, entry.name);
    const relPath = baseRel ? `${baseRel}/${entry.name}` : entry.name;

    if (entry.isDirectory()) {
      results = results.concat(scanAllPages(fullPath, relPath));
    } else if (entry.name === 'index.html') {
      try {
        const content = fs.readFileSync(fullPath, 'utf-8');
        const stats = fs.statSync(fullPath);

        // Extrahovanie názvu
        const h1Match = content.match(/<h1[^>]*class=["'][^"']*idsk-subpage-content__title[^"']*["'][^>]*>([\s\S]*?)<\/h1>/i)
          || content.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
        const titleMatch = content.match(/<title>([\s\S]*?)<\/title>/i);

        let title = '';
        if (h1Match) {
          title = h1Match[1].replace(/<[^>]+>/g, '').trim();
        } else if (titleMatch) {
          title = titleMatch[1].replace(/\|[\s\S]*$/, '').replace(/<[^>]+>/g, '').trim();
        } else {
          title = relPath.replace(/\/index\.html$/, '');
        }

        // Určenie sekcie podľa cesty
        let section = 'Hlavná stránka';
        const parts = relPath.split('/');
        if (parts[0] === 'obec-2' || parts[0] === 'covid-19' || parts[0] === 'mobilna-aplikacia') {
          section = parts[1] === 'aktuality' ? 'Aktuality' : (parts[1] === 'fotogaleria' ? 'Fotogaléria' : 'Obec');
        } else if (parts[0] === 'samosprava') {
          section = parts[1] === 'vzn' ? 'VZN' : (parts[1]?.includes('obecne-zastupitelstvo') ? 'Zastupiteľstvo OZ' : 'Samospráva');
        } else if (parts[0] === 'zverejnovanie') {
          section = parts[1] === 'uradna-tabula-1' ? 'Úradná tabuľa' : 'Zverejňovanie';
        } else if (parts[0] === 'projekty') {
          section = 'Projekty';
        } else if (parts[0] === 'volby-a-referendum') {
          section = 'Voľby a referendum';
        } else if (parts[0] === 'uzemny-plan') {
          section = 'Územný plán';
        } else if (parts[0] === 'kontakt-1' || parts[0] === 'kontakt' || parts[0] === 'contact') {
          section = 'Kontakt';
        } else if (parts[0] === 'en') {
          section = 'English';
        }

        const url = '/' + relPath.replace(/index\.html$/, '');

        results.push({
          path: relPath,
          url: url,
          title: title || 'Stránka bez názvu',
          section: section,
          size: stats.size,
          modified: stats.mtime.toISOString()
        });
      } catch (err) {
        console.warn(`Chyba pri čítaní stránky ${relPath}:`, err.message);
      }
    }
  }

  return results;
}

// Vytvorenie servera
const server = http.createServer(async (req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost:' + PORT}`);
  const pathname = parsedUrl.pathname;

  // OPTIONS pre CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
    res.end();
    return;
  }

  // --- API ENDPOINTY ---

  // 1. Stav systému a štatistiky
  if (pathname === '/api/status' && req.method === 'GET') {
    try {
      const aktualityPath = path.join(PUBLIC_DIR, 'obec-2', 'aktuality');
      const tabulaPath = path.join(PUBLIC_DIR, 'zverejnovanie', 'uradna-tabula-1');
      const vznPath = path.join(PUBLIC_DIR, 'samosprava', 'vzn');
      const ozPath = path.join(PUBLIC_DIR, 'samosprava', 'obecne-zastupitelstvo', 'pozvanky-na-zasadnutie-oz-1');

      const countDirs = (dir) => {
        if (!fs.existsSync(dir)) return 0;
        return fs.readdirSync(dir, { withFileTypes: true }).filter(d => d.isDirectory()).length;
      };

      const allPages = scanAllPages();

      sendJson(res, 200, {
        status: 'ok',
        version: '2.0.0',
        mode: 'local',
        repo: 'luckyboy-aja/horny-vadicov',
        siteUrl: 'https://luckyboy-aja.github.io/horny-vadicov/',
        stats: {
          pagesCount: allPages.length,
          articlesCount: countDirs(aktualityPath),
          boardCount: countDirs(tabulaPath),
          vznCount: countDirs(vznPath),
          meetingsCount: countDirs(ozPath),
          lastCheck: new Date().toISOString()
        }
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 2. Zoznam VŠETKÝCH podstránok webu (Pages API - WordPress štýl)
  if (pathname === '/api/pages' && req.method === 'GET') {
    try {
      const pages = scanAllPages();
      sendJson(res, 200, { pages, total: pages.length });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 3. Načítanie obsahu konkrétnej stránky na editáciu
  if (pathname === '/api/pages/content' && req.method === 'GET') {
    try {
      const reqPath = parsedUrl.searchParams.get('path');
      if (!reqPath) {
        sendJson(res, 400, { error: 'Chýba parameter path.' });
        return;
      }

      // Bezpečnostná kontrola: nesmie ísť mimo PUBLIC_DIR
      const normalizedPath = path.normalize(reqPath).replace(/^(\.\.(\/|\\|$))+/, '');
      const fullPath = path.join(PUBLIC_DIR, normalizedPath);

      if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isFile()) {
        sendJson(res, 404, { error: 'Stránka sa nenašla.' });
        return;
      }

      const rawHtml = fs.readFileSync(fullPath, 'utf-8');

      // Extrahovanie názvu
      const h1Match = rawHtml.match(/<h1[^>]*class=["'][^"']*idsk-subpage-content__title[^"']*["'][^>]*>([\s\S]*?)<\/h1>/i)
        || rawHtml.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
      const title = h1Match ? h1Match[1].replace(/<[^>]+>/g, '').trim() : '';

      // Extrahovanie editovateľného tela stránky
      let bodyHtml = '';
      if (rawHtml.includes('class="idsk-subpage-body editor_content"')) {
        const parts = rawHtml.split(/<div[^>]*class=["']idsk-subpage-body editor_content["'][^>]*>/i);
        if (parts.length > 1) {
          const afterOpen = parts[1];
          // Telo končí pred </article> alebo </main>
          const closingIndex = afterOpen.indexOf('</article>');
          if (closingIndex !== -1) {
            bodyHtml = afterOpen.substring(0, closingIndex);
            // Odstránime posledný uzatvárací </div>
            const lastDiv = bodyHtml.lastIndexOf('</div>');
            if (lastDiv !== -1) bodyHtml = bodyHtml.substring(0, lastDiv);
          } else {
            bodyHtml = afterOpen;
          }
        }
      } else if (rawHtml.includes('<article class="idsk-subpage-content">')) {
        const artPart = rawHtml.split('<article class="idsk-subpage-content">')[1];
        bodyHtml = artPart.split('</article>')[0];
      } else {
        // Fallback pre hlavnú stránku alebo neštandardné stránky
        const mainMatch = rawHtml.match(/<main[^>]*>([\s\S]*?)<\/main>/i);
        bodyHtml = mainMatch ? mainMatch[1] : rawHtml;
      }

      sendJson(res, 200, {
        path: normalizedPath,
        title: title || 'Bez názvu',
        bodyHtml: bodyHtml.trim(),
        fullHtml: rawHtml
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 4. Uloženie upraveného obsahu stránky
  if (pathname === '/api/pages/save' && req.method === 'POST') {
    try {
      const body = await parseBody(req);
      const { path: reqPath, title, bodyHtml, fullHtml } = body;

      if (!reqPath) {
        sendJson(res, 400, { error: 'Chýba parameter path.' });
        return;
      }

      const normalizedPath = path.normalize(reqPath).replace(/^(\.\.(\/|\\|$))+/, '');
      const fullPath = path.join(PUBLIC_DIR, normalizedPath);

      if (!fs.existsSync(fullPath)) {
        sendJson(res, 404, { error: 'Stránka sa nenašla.' });
        return;
      }

      let updatedHtml = '';

      if (fullHtml) {
        // Priame uloženie plného HTML (ak používateľ editoval priamy kód)
        updatedHtml = fullHtml;
      } else {
        const existingHtml = fs.readFileSync(fullPath, 'utf-8');

        // 1. Aktualizácia názvu v <title> a <h1>
        let withTitle = existingHtml;
        if (title) {
          withTitle = withTitle
            .replace(/<title>[\s\S]*?<\/title>/i, `<title>${title} | Obec Horný Vadičov (IDSK 3.0)</title>`)
            .replace(/(<h1[^>]*class=["'][^"']*idsk-subpage-content__title[^"']*["'][^>]*>)[\s\S]*?(<\/h1>)/i, `$1${title}$2`);
        }

        // 2. Aktualizácia editovateľného tela stránky
        if (bodyHtml !== undefined) {
          if (withTitle.includes('class="idsk-subpage-body editor_content"')) {
            const regex = /(<div[^>]*class=["']idsk-subpage-body editor_content["'][^>]*>)[\s\S]*?(<\/article>)/i;
            withTitle = withTitle.replace(regex, `$1\n${bodyHtml}\n          </div>\n        $2`);
          } else {
            // Ak stránka nemala wrapper, nahradíme hlavný obsah
            const mainRegex = /(<main[^>]*>)[\s\S]*?(<\/main>)/i;
            if (mainRegex.test(withTitle)) {
              withTitle = withTitle.replace(mainRegex, `$1\n<div class="idsk-container py-4">\n${bodyHtml}\n</div>\n$2`);
            }
          }
        }
        updatedHtml = withTitle;
      }

      fs.writeFileSync(fullPath, updatedHtml, 'utf-8');

      sendJson(res, 200, {
        success: true,
        message: 'Stránka bola úspešne uložená a zmeny sú okamžite aktívne.',
        path: normalizedPath
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 5. Vytvorenie novej podstránky (WordPress-like Add New Page)
  if (pathname === '/api/pages/create' && req.method === 'POST') {
    try {
      const body = await parseBody(req);
      const { section, title, slug: customSlug, contentHtml } = body;

      if (!title) {
        sendJson(res, 400, { error: 'Názov stránky je povinný.' });
        return;
      }

      const validSection = (section || 'obec-2').toLowerCase().trim();
      const slug = customSlug ? slugify(customSlug) : slugify(title);
      const newPageDir = path.join(PUBLIC_DIR, validSection, slug);
      fs.mkdirSync(newPageDir, { recursive: true });

      // Použijeme vzorovú podstránku
      const templatePath = path.join(PUBLIC_DIR, 'obec-2', 'o-obci', 'index.html');
      let templateHtml = fs.readFileSync(templatePath, 'utf-8');

      // Vypočítame relatívnu hĺbku (napr. obec-2/nova-stranka -> ../../)
      const relDepth = '../../';

      // Úprava hlavičky a navigácie
      let newHtml = templateHtml
        .replace(/<title>[\s\S]*?<\/title>/i, `<title>${title} | Obec Horný Vadičov (IDSK 3.0)</title>`)
        .replace(/(<h1[^>]*class=["'][^"']*idsk-subpage-content__title[^"']*["'][^>]*>)[\s\S]*?(<\/h1>)/i, `$1${title}$2`);

      // Nahradenie tela stránky
      if (newHtml.includes('class="idsk-subpage-body editor_content"')) {
        const regex = /(<div[^>]*class=["']idsk-subpage-body editor_content["'][^>]*>)[\s\S]*?(<\/article>)/i;
        newHtml = newHtml.replace(regex, `$1\n<div class="idsk-article-content" style="font-size: 1.1rem; line-height: 1.7;">\n${contentHtml || '<p>Obsah stránky pripravujeme...</p>'}\n</div>\n          </div>\n        $2`);
      }

      const destFile = path.join(newPageDir, 'index.html');
      fs.writeFileSync(destFile, newHtml, 'utf-8');

      const relPath = `${validSection}/${slug}/index.html`;

      sendJson(res, 200, {
        success: true,
        message: 'Nová stránka bola úspešne vytvorená a publikovaná!',
        path: relPath,
        url: `/${validSection}/${slug}/`
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 6. Zoznam aktualít
  if (pathname === '/api/aktuality' && req.method === 'GET') {
    try {
      const aktualityIndexPath = path.join(PUBLIC_DIR, 'obec-2', 'aktuality', 'index.html');
      const html = fs.readFileSync(aktualityIndexPath, 'utf-8');
      
      const articles = [];
      const regex = /<a\s+href=["']\.\/([^"']+)["'][^>]*class="event-link"[^>]*>([\s\S]*?)<\/a>/g;
      let match;
      while ((match = regex.exec(html)) !== null) {
        const slug = match[1].replace(/\/$/, '');
        const block = match[2];
        const titleM = block.match(/<h3 class="event-name">([\s\S]*?)<\/h3>/);
        const dateM = block.match(/<span class="event-info-value event-date">([\s\S]*?)<\/span>/);
        const perexM = block.match(/<p class="event-perex">([\s\S]*?)<\/p>/);
        const imgM = block.match(/<img\s+src=["']([^"']+)["']/);

        articles.push({
          slug,
          title: titleM ? titleM[1].trim() : slug,
          date: dateM ? dateM[1].trim() : '',
          perex: perexM ? perexM[1].trim() : '',
          image: imgM ? imgM[1] : '',
          url: `/obec-2/aktuality/${slug}/`
        });
      }

      sendJson(res, 200, { articles });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 7. Vytvorenie novej aktuality
  if (pathname === '/api/aktuality' && req.method === 'POST') {
    try {
      const body = await parseBody(req);
      const { title, date, perex, contentHtml, imageBase64, imageFileName } = body;

      if (!title || !contentHtml) {
        sendJson(res, 400, { error: 'Názov a obsah sú povinné polia.' });
        return;
      }

      const dateStr = date || new Date().toLocaleDateString('sk-SK');
      const slug = slugify(title) + '-' + Date.now().toString().slice(-4);
      const articleDir = path.join(PUBLIC_DIR, 'obec-2', 'aktuality', slug);
      fs.mkdirSync(articleDir, { recursive: true });

      // Uloženie obrázka ak bol nahraný
      let imgRelPath = '../../data/cache_images/default_news.jpg';
      let imgSubpageRelPath = '../../../data/cache_images/default_news.jpg';
      if (imageBase64 && imageFileName) {
        const imgExt = path.extname(imageFileName) || '.jpg';
        const imgSafeName = `aktuality_${slug}${imgExt}`;
        const imgDestPath = path.join(PUBLIC_DIR, 'data', 'cache_images', imgSafeName);
        const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');
        fs.writeFileSync(imgDestPath, Buffer.from(base64Data, 'base64'));
        imgRelPath = `../../data/cache_images/${imgSafeName}`;
        imgSubpageRelPath = `../../../data/cache_images/${imgSafeName}`;
      }

      // Vygenerovanie podstránky aktuality
      const samplePagePath = path.join(PUBLIC_DIR, 'obec-2', 'aktuality', 'otvorenie-skolskeho-roka-2026-2027-605sk', 'index.html');
      let sampleHtml = '';
      if (fs.existsSync(samplePagePath)) {
        sampleHtml = fs.readFileSync(samplePagePath, 'utf-8');
      } else {
        sampleHtml = fs.readFileSync(path.join(PUBLIC_DIR, 'obec-2', 'aktuality', 'index.html'), 'utf-8');
      }

      const headerPart = sampleHtml.split('<div class="idsk-subpage-body editor_content">')[0];
      const footerPart = sampleHtml.split('</article>')[1] || sampleHtml.split('</main>')[1];

      let finalHeader = headerPart
        .replace(/<title>[\s\S]*?<\/title>/, `<title>${title} | Aktuality | Obec Horný Vadičov (IDSK 3.0)</title>`)
        .replace(/<h1 class="idsk-subpage-content__title">[\s\S]*?<\/h1>/, `<h1 class="idsk-subpage-content__title">${title}</h1>`);

      const newArticleHtml = `<!DOCTYPE html>
<html lang="sk">
${finalHeader.split('<!DOCTYPE html>')[1] || finalHeader}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-article-meta mb-4 text-muted" style="font-size: 0.95rem; color: #555; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
              <span><strong>Dátum zverejnenia:</strong> ${dateStr}</span>
            </div>
            
            ${imageBase64 ? `<div class="mb-4" style="text-align: center; margin-bottom: 1.5rem;"><img src="${imgSubpageRelPath}" alt="${title}" style="max-width: 100%; max-height: 480px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"></div>` : ''}

            <div class="idsk-article-content" style="font-size: 1.1rem; line-height: 1.7;">
              ${contentHtml}
            </div>

            <div class="mt-5 pt-4" style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid #e0e0e0;">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; padding: 0.5rem 1rem; background: #e0e0e0; color: #0b0c0c; border-radius: 4px; font-weight: 700;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
                Späť na zoznam aktualít
              </a>
            </div>
          </div>
        </article>
      </div>
    </div>
  </main>
${footerPart || '</body></html>'}`;

      fs.writeFileSync(path.join(articleDir, 'index.html'), newArticleHtml, 'utf-8');

      // Vloženie novej aktuality na začiatok zoznamu v index.html
      const aktualityIndexPath = path.join(PUBLIC_DIR, 'obec-2', 'aktuality', 'index.html');
      let aktualityIndex = fs.readFileSync(aktualityIndexPath, 'utf-8');

      const newCardMarkup = `
        <a href="./${slug}/" class="event-link">
            <div class="event event-message row readable_item">
                <div class="col-4 col-lg-3 pr-0">
                    <img src="${imgRelPath}" alt="${title}" class="event-imgage img-fluid mb-3 mb-sm-0" loading="lazy" style="max-height: 140px; object-fit: cover;">
                </div>
                <div class="col-8 col-lg-9 px-3 px-sm-6">
                    <h3 class="event-name">${title}</h3>
                    <div class="event-info">
                        <span class="event-info-name event-date">Dátum:</span>
                        <span class="event-info-value event-date">${dateStr}</span>
                    </div>
                    <p class="event-perex">${perex || title}</p>
                </div>
            </div>
        </a>`;

      if (aktualityIndex.includes('<div class="events-list">')) {
        aktualityIndex = aktualityIndex.replace('<div class="events-list">', `<div class="events-list">${newCardMarkup}`);
      } else if (aktualityIndex.includes('class="event-link"')) {
        aktualityIndex = aktualityIndex.replace(/(<a\s+href=["']\.\/[^"']+["'][^>]*class="event-link")/, `${newCardMarkup}\n$1`);
      }
      fs.writeFileSync(aktualityIndexPath, aktualityIndex, 'utf-8');

      sendJson(res, 200, {
        success: true,
        slug,
        url: `/obec-2/aktuality/${slug}/`,
        message: 'Aktualita bola úspešne vytvorená a publikovaná.'
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 8. Zmazanie aktuality
  if (pathname.startsWith('/api/aktuality/') && req.method === 'DELETE') {
    try {
      const slug = pathname.replace('/api/aktuality/', '').replace(/\/$/, '');
      const articleDir = path.join(PUBLIC_DIR, 'obec-2', 'aktuality', slug);

      if (fs.existsSync(articleDir)) {
        fs.rmSync(articleDir, { recursive: true, force: true });
      }

      // Odstránenie zo zoznamu v index.html
      const aktualityIndexPath = path.join(PUBLIC_DIR, 'obec-2', 'aktuality', 'index.html');
      let aktualityIndex = fs.readFileSync(aktualityIndexPath, 'utf-8');
      const regex = new RegExp(`<a\\s+href=["']\\.\\/${slug}\\/["'][^>]*class="event-link"[^>]*>[\\s\\S]*?<\\/a>`, 'gi');
      aktualityIndex = aktualityIndex.replace(regex, '');
      fs.writeFileSync(aktualityIndexPath, aktualityIndex, 'utf-8');

      sendJson(res, 200, { success: true, message: 'Aktualita bola zmazaná.' });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 9. Zoznam položiek úradnej tabule
  if (pathname === '/api/uradna-tabula' && req.method === 'GET') {
    try {
      const tabulaIndexPath = path.join(PUBLIC_DIR, 'zverejnovanie', 'uradna-tabula-1', 'index.html');
      const html = fs.readFileSync(tabulaIndexPath, 'utf-8');
      
      const notices = [];
      const regex = /<a\s+class="item-href"\s+href=["']\.\/([^"']+)["'][^>]*>([\s\S]*?)<\/a>/g;
      let match;
      while ((match = regex.exec(html)) !== null) {
        const slug = match[1].replace(/\/$/, '');
        const block = match[2];
        const titleM = block.match(/<span class="item-name">([\s\S]*?)<\/span>/) || [null, slug];
        const datesM = block.match(/<span class="item-date[^"]*">([\s\S]*?)<\/span>/g) || [];

        notices.push({
          slug,
          title: titleM[1].trim(),
          dates: datesM.map(d => d.replace(/<[^>]+>/g, '').trim()).join(' · '),
          url: `/zverejnovanie/uradna-tabula-1/${slug}/`
        });
      }

      sendJson(res, 200, { notices });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 10. Vytvorenie nového oznamu na úradnej tabuli
  if (pathname === '/api/uradna-tabula' && req.method === 'POST') {
    try {
      const body = await parseBody(req);
      const { title, category, dateFrom, dateTo, fileBase64, fileName, description } = body;

      if (!title) {
        sendJson(res, 400, { error: 'Názov oznamu je povinný.' });
        return;
      }

      const slug = slugify(title) + '-' + Date.now().toString().slice(-4);
      const noticeDir = path.join(PUBLIC_DIR, 'zverejnovanie', 'uradna-tabula-1', slug);
      fs.mkdirSync(noticeDir, { recursive: true });

      let attachedFileRelPath = '';
      let attachedFileSubpagePath = '';
      if (fileBase64 && fileName) {
        const safeFileName = `${slug}_${fileName.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
        const fileDest = path.join(PUBLIC_DIR, 'data', 'uredni_deska', safeFileName);
        const base64Data = fileBase64.replace(/^data:[^;]+;base64,/, '');
        fs.writeFileSync(fileDest, Buffer.from(base64Data, 'base64'));
        attachedFileRelPath = `../../data/uredni_deska/${safeFileName}`;
        attachedFileSubpagePath = `../../../data/uredni_deska/${safeFileName}`;
      }

      const dFrom = dateFrom || new Date().toLocaleDateString('sk-SK');
      const dTo = dateTo || new Date(Date.now() + 15 * 86400000).toLocaleDateString('sk-SK');

      // Vzorová podstránka úradnej tabule
      const sampleNoticePath = path.join(PUBLIC_DIR, 'zverejnovanie', 'uradna-tabula-1', 'stavebne-konanie', 'index.html');
      let sampleHtml = fs.readFileSync(sampleNoticePath, 'utf-8');

      const headerPart = sampleHtml.split('<div class="idsk-subpage-body editor_content">')[0];
      const footerPart = sampleHtml.split('</article>')[1] || sampleHtml.split('</main>')[1];

      let finalHeader = headerPart
        .replace(/<title>[\s\S]*?<\/title>/, `<title>${title} | Úradná tabuľa | Obec Horný Vadičov (IDSK 3.0)</title>`)
        .replace(/<h1 class="idsk-subpage-content__title">[\s\S]*?<\/h1>/, `<h1 class="idsk-subpage-content__title">${title}</h1>`);

      const noticeHtml = `<!DOCTYPE html>
<html lang="sk">
${finalHeader.split('<!DOCTYPE html>')[1] || finalHeader}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-notice-meta mb-4" style="background: #f3f4f6; padding: 1rem; border-left: 4px solid var(--idsk-color-primary, #003366); margin-bottom: 1.5rem;">
              <div><strong>Kategória:</strong> ${category || 'Úradná tabuľa'}</div>
              <div><strong>Vyvesené dňa:</strong> ${dFrom}</div>
              <div><strong>Dátum zvesenia:</strong> ${dTo}</div>
            </div>

            <div class="idsk-notice-body" style="font-size: 1.05rem; line-height: 1.6; margin-bottom: 2rem;">
              ${description ? `<p>${description}</p>` : '<p>Zverejnenie dokumentu v zmysle platnej legislatívy.</p>'}
            </div>

            ${attachedFileSubpagePath ? `
            <div class="idsk-attachment-card" style="border: 1px solid #d1d5db; padding: 1.25rem; border-radius: 6px; background: #fafafa; display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
              <div style="display: flex; align-items: center; gap: 0.75rem;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="#dc2626"><path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/></svg>
                <div>
                  <strong>${fileName || 'Priložený dokument.pdf'}</strong>
                  <div style="font-size: 0.85rem; color: #6b7280;">Oficiálny zverejnený dokument na úradnej tabuli</div>
                </div>
              </div>
              <a href="${attachedFileSubpagePath}" target="_blank" rel="noopener noreferrer" class="idsk-button" style="display: inline-flex; align-items: center; gap: 0.5rem; background: var(--idsk-color-primary, #003366); color: #fff; padding: 0.5rem 1rem; border-radius: 4px; text-decoration: none; font-weight: 600;">
                Stiahnuť PDF
              </a>
            </div>` : ''}

            <div class="mt-5 pt-3" style="border-top: 1px solid #e5e7eb; padding-top: 1.5rem;">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; padding: 0.5rem 1rem; background: #e5e7eb; color: #111; border-radius: 4px; font-weight: 600;">
                ← Späť na Úradnú tabuľu
              </a>
            </div>
          </div>
        </article>
      </div>
    </div>
  </main>
${footerPart || '</body></html>'}`;

      fs.writeFileSync(path.join(noticeDir, 'index.html'), noticeHtml, 'utf-8');

      // Aktualizácia indexu úradnej tabule
      const tabulaIndexPath = path.join(PUBLIC_DIR, 'zverejnovanie', 'uradna-tabula-1', 'index.html');
      let tabulaIndex = fs.readFileSync(tabulaIndexPath, 'utf-8');

      const newRowMarkup = `
        <div class="ed-item">
          <a class="item-href" href="./${slug}/">
            <span class="item-name">${title}</span>
            <div class="item-dates">
              <span class="item-date item-date-from">Vyvesené: ${dFrom}</span>
              <span class="item-date item-date-to">Zvesenie: ${dTo}</span>
            </div>
          </a>
        </div>`;

      if (tabulaIndex.includes('class="item-href"')) {
        tabulaIndex = tabulaIndex.replace(/(<div class="ed-item">|<a\s+class="item-href")/, `${newRowMarkup}\n$1`);
        fs.writeFileSync(tabulaIndexPath, tabulaIndex, 'utf-8');
      }

      sendJson(res, 200, {
        success: true,
        slug,
        url: `/zverejnovanie/uradna-tabula-1/${slug}/`,
        message: 'Oznam bol úspešne vyvesený na úradnú tabuľu.'
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 11. Zmazanie/zvesenie položky z úradnej tabule
  if (pathname.startsWith('/api/uradna-tabula/') && req.method === 'DELETE') {
    try {
      const slug = pathname.replace('/api/uradna-tabula/', '').replace(/\/$/, '');
      const noticeDir = path.join(PUBLIC_DIR, 'zverejnovanie', 'uradna-tabula-1', slug);

      if (fs.existsSync(noticeDir)) {
        fs.rmSync(noticeDir, { recursive: true, force: true });
      }

      const tabulaIndexPath = path.join(PUBLIC_DIR, 'zverejnovanie', 'uradna-tabula-1', 'index.html');
      let tabulaIndex = fs.readFileSync(tabulaIndexPath, 'utf-8');
      const regex = new RegExp(`(<div class="ed-item">\\s*)?<a class="item-href" href="\\.\\/${slug}\\/"[\\s\\S]*?<\\/a>(\\s*<\\/div>)?`, 'gi');
      tabulaIndex = tabulaIndex.replace(regex, '');
      fs.writeFileSync(tabulaIndexPath, tabulaIndex, 'utf-8');

      sendJson(res, 200, { success: true, message: 'Oznam bol z úradnej tabule odstránený.' });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 12. Správa VZN (Zoznam)
  if (pathname === '/api/vzn' && req.method === 'GET') {
    try {
      const vznIndexPath = path.join(PUBLIC_DIR, 'samosprava', 'vzn', 'index.html');
      const html = fs.readFileSync(vznIndexPath, 'utf-8');

      const vznList = [];
      const regex = /<div class="item">[\s\S]*?<a class="item-href" href=["']\.\/([^"']+)["'][^>]*>([\s\S]*?)<\/a>[\s\S]*?<div class="item-data">([\s\S]*?)<\/div>[\s\S]*?<\/div>/g;
      let match;
      while ((match = regex.exec(html)) !== null) {
        const slug = match[1].replace(/\/$/, '');
        const title = match[2].trim();
        const dateBlock = match[3];
        const dateFromM = dateBlock.match(/Vyvesené:\s*([^<]+)/i);
        const dateToM = dateBlock.match(/zvesenia:\s*([^<]+)/i);

        vznList.push({
          slug,
          title,
          dateFrom: dateFromM ? dateFromM[1].trim() : '',
          dateTo: dateToM ? dateToM[1].trim() : '',
          url: `/samosprava/vzn/${slug}/`
        });
      }

      sendJson(res, 200, { vzn: vznList, total: vznList.length });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 13. Pridanie nového VZN s PDF
  if (pathname === '/api/vzn' && req.method === 'POST') {
    try {
      const body = await parseBody(req);
      const { title, number, year, dateApproved, dateEffective, fileBase64, fileName, description } = body;

      if (!title) {
        sendJson(res, 400, { error: 'Názov VZN je povinný.' });
        return;
      }

      const slug = slugify(title) + '-' + Date.now().toString().slice(-4);
      const vznDir = path.join(PUBLIC_DIR, 'samosprava', 'vzn', slug);
      fs.mkdirSync(vznDir, { recursive: true });

      let attachedFileRelPath = '';
      let attachedFileSubpagePath = '';
      if (fileBase64 && fileName) {
        const safeFileName = `${slug}_${fileName.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
        const fileDest = path.join(PUBLIC_DIR, 'data', 'vzn', safeFileName);
        const base64Data = fileBase64.replace(/^data:[^;]+;base64,/, '');
        fs.writeFileSync(fileDest, Buffer.from(base64Data, 'base64'));
        attachedFileRelPath = `../../data/vzn/${safeFileName}`;
        attachedFileSubpagePath = `../../../data/vzn/${safeFileName}`;
      }

      const dApp = dateApproved || new Date().toLocaleDateString('sk-SK');
      const dEff = dateEffective || new Date(Date.now() + 15 * 86400000).toLocaleDateString('sk-SK');

      // Vzorová podstránka VZN
      const sampleVznPath = path.join(PUBLIC_DIR, 'samosprava', 'vzn', 'vzn-c-1-2026-o-podmienkach-posudzovania-odkazanost-1392', 'index.html');
      let sampleHtml = '';
      if (fs.existsSync(sampleVznPath)) {
        sampleHtml = fs.readFileSync(sampleVznPath, 'utf-8');
      } else {
        sampleHtml = fs.readFileSync(path.join(PUBLIC_DIR, 'samosprava', 'vzn', 'index.html'), 'utf-8');
      }

      const headerPart = sampleHtml.split('<div class="idsk-subpage-body editor_content">')[0];
      const footerPart = sampleHtml.split('</article>')[1] || sampleHtml.split('</main>')[1];

      let finalHeader = headerPart
        .replace(/<title>[\s\S]*?<\/title>/, `<title>${title} | VZN | Obec Horný Vadičov (IDSK 3.0)</title>`)
        .replace(/<h1 class="idsk-subpage-content__title">[\s\S]*?<\/h1>/, `<h1 class="idsk-subpage-content__title">${title}</h1>`);

      const vznHtml = `<!DOCTYPE html>
<html lang="sk">
${finalHeader.split('<!DOCTYPE html>')[1] || finalHeader}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-notice-meta mb-4" style="background: #f3f4f6; padding: 1.25rem; border-left: 4px solid var(--idsk-color-primary, #003366); margin-bottom: 1.5rem; border-radius: 4px;">
              <div><strong>Názov:</strong> ${title}</div>
              ${number ? `<div><strong>Číslo VZN:</strong> ${number}</div>` : ''}
              <div><strong>Schválené dňa:</strong> ${dApp}</div>
              <div><strong>Nadobudnutie účinnosti:</strong> ${dEff}</div>
            </div>

            <div class="idsk-notice-body" style="font-size: 1.05rem; line-height: 1.6; margin-bottom: 2rem;">
              ${description ? `<p>${description}</p>` : '<p>Všeobecne záväzné nariadenie obce Horný Vadičov prijaté obecným zastupiteľstvom.</p>'}
            </div>

            ${attachedFileSubpagePath ? `
            <div class="idsk-attachment-card" style="border: 1px solid #d1d5db; padding: 1.25rem; border-radius: 6px; background: #fafafa; display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
              <div style="display: flex; align-items: center; gap: 0.75rem;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="#dc2626"><path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/></svg>
                <div>
                  <strong>${fileName || 'Plné znenie VZN.pdf'}</strong>
                  <div style="font-size: 0.85rem; color: #6b7280;">Oficiálny dokument vo formáte PDF</div>
                </div>
              </div>
              <a href="${attachedFileSubpagePath}" target="_blank" rel="noopener noreferrer" class="idsk-button" style="display: inline-flex; align-items: center; gap: 0.5rem; background: var(--idsk-color-primary, #003366); color: #fff; padding: 0.5rem 1rem; border-radius: 4px; text-decoration: none; font-weight: 600;">
                Stiahnuť PDF
              </a>
            </div>` : ''}

            <div class="mt-5 pt-3" style="border-top: 1px solid #e5e7eb; padding-top: 1.5rem;">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; padding: 0.5rem 1rem; background: #e5e7eb; color: #111; border-radius: 4px; font-weight: 600;">
                ← Späť na zoznam VZN
              </a>
            </div>
          </div>
        </article>
      </div>
    </div>
  </main>
${footerPart || '</body></html>'}`;

      fs.writeFileSync(path.join(vznDir, 'index.html'), vznHtml, 'utf-8');

      // Prepnutie do zoznamu VZN
      const vznIndexPath = path.join(PUBLIC_DIR, 'samosprava', 'vzn', 'index.html');
      let vznIndex = fs.readFileSync(vznIndexPath, 'utf-8');

      const newVznCardMarkup = `
        <div class="item">
            <div class="item-heading">
                <a class="item-href" href="./${slug}/" target="_blank" rel="noopener noreferrer">${title}</a>
            </div>
            <div class="item-data">
                <span class="item-date item-date-from">Schválené: ${dApp}</span>
                <span class="item-date item-date-to">Účinnosť: ${dEff}</span>
            </div>
        </div>`;

      if (vznIndex.includes('<div class="card-body">')) {
        vznIndex = vznIndex.replace('<div class="card-body">', `<div class="card-body">\n${newVznCardMarkup}`);
        fs.writeFileSync(vznIndexPath, vznIndex, 'utf-8');
      }

      sendJson(res, 200, {
        success: true,
        slug,
        url: `/samosprava/vzn/${slug}/`,
        message: 'VZN bolo úspešne publikované na webe!'
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 14. Zasadnutia obecného zastupiteľstva (OZ Pozvánky)
  if (pathname === '/api/zasadnutia' && req.method === 'GET') {
    try {
      const ozIndexPath = path.join(PUBLIC_DIR, 'samosprava', 'obecne-zastupitelstvo', 'pozvanky-na-zasadnutie-oz-1', 'index.html');
      const html = fs.readFileSync(ozIndexPath, 'utf-8');

      const meetings = [];
      const regex = /<div class="item">[\s\S]*?<a class="item-href" href=["']\.\/([^"']+)["'][^>]*>([\s\S]*?)<\/a>[\s\S]*?<div class="item-data">([\s\S]*?)<\/div>[\s\S]*?<\/div>/g;
      let match;
      while ((match = regex.exec(html)) !== null) {
        const slug = match[1].replace(/\/$/, '');
        const title = match[2].trim();
        const dates = match[3].replace(/<[^>]+>/g, '').trim();

        meetings.push({
          slug,
          title,
          dates,
          url: `/samosprava/obecne-zastupitelstvo/pozvanky-na-zasadnutie-oz-1/${slug}/`
        });
      }

      sendJson(res, 200, { meetings, total: meetings.length });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 15. Pridanie novej pozvánky na zasadnutie OZ
  if (pathname === '/api/zasadnutia' && req.method === 'POST') {
    try {
      const body = await parseBody(req);
      const { title, date, location, program, fileBase64, fileName } = body;

      if (!title) {
        sendJson(res, 400, { error: 'Názov pozvánky na zasadnutie OZ je povinný.' });
        return;
      }

      const slug = slugify(title) + '-' + Date.now().toString().slice(-4);
      const ozDir = path.join(PUBLIC_DIR, 'samosprava', 'obecne-zastupitelstvo', 'pozvanky-na-zasadnutie-oz-1', slug);
      fs.mkdirSync(ozDir, { recursive: true });

      let attachedFileSubpagePath = '';
      if (fileBase64 && fileName) {
        const safeFileName = `${slug}_${fileName.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
        const fileDest = path.join(PUBLIC_DIR, 'data', 'pozvanky', safeFileName);
        const base64Data = fileBase64.replace(/^data:[^;]+;base64,/, '');
        fs.writeFileSync(fileDest, Buffer.from(base64Data, 'base64'));
        attachedFileSubpagePath = `../../../../data/pozvanky/${safeFileName}`;
      }

      const dStr = date || new Date().toLocaleDateString('sk-SK');

      // Vzorová podstránka
      const sampleOzPath = path.join(PUBLIC_DIR, 'samosprava', 'obecne-zastupitelstvo', 'pozvanky-na-zasadnutie-oz-1', 'pozvanka-na-neplanovane-zasadnutie-oz-obce-horny-v-1424', 'index.html');
      let sampleHtml = '';
      if (fs.existsSync(sampleOzPath)) {
        sampleHtml = fs.readFileSync(sampleOzPath, 'utf-8');
      } else {
        sampleHtml = fs.readFileSync(path.join(PUBLIC_DIR, 'samosprava', 'obecne-zastupitelstvo', 'pozvanky-na-zasadnutie-oz-1', 'index.html'), 'utf-8');
      }

      const headerPart = sampleHtml.split('<div class="idsk-subpage-body editor_content">')[0];
      const footerPart = sampleHtml.split('</article>')[1] || sampleHtml.split('</main>')[1];

      let finalHeader = headerPart
        .replace(/<title>[\s\S]*?<\/title>/, `<title>${title} | Obecné zastupiteľstvo | Obec Horný Vadičov (IDSK 3.0)</title>`)
        .replace(/<h1 class="idsk-subpage-content__title">[\s\S]*?<\/h1>/, `<h1 class="idsk-subpage-content__title">${title}</h1>`);

      const meetingHtml = `<!DOCTYPE html>
<html lang="sk">
${finalHeader.split('<!DOCTYPE html>')[1] || finalHeader}
          <div class="idsk-subpage-body editor_content">
            <div class="idsk-notice-meta mb-4" style="background: #f3f4f6; padding: 1.25rem; border-left: 4px solid var(--idsk-color-primary, #003366); margin-bottom: 1.5rem; border-radius: 4px;">
              <div><strong>Udalosť:</strong> ${title}</div>
              <div><strong>Dátum a čas konania:</strong> ${dStr}</div>
              <div><strong>Miesto:</strong> ${location || 'Zasadačka Obecného úradu Horný Vadičov'}</div>
            </div>

            <div class="idsk-notice-body" style="font-size: 1.05rem; line-height: 1.6; margin-bottom: 2rem;">
              <h2 style="font-size: 1.3rem; margin-bottom: 1rem;">Program rokovania:</h2>
              ${program ? program : '<ol><li>Otvorenie zasadnutia</li><li>Určenie zapisovateľa a overovateľov zápisnice</li><li>Schválenie programu rokovania</li><li>Rôzne a diskusia</li><li>Záver</li></ol>'}
            </div>

            ${attachedFileSubpagePath ? `
            <div class="idsk-attachment-card" style="border: 1px solid #d1d5db; padding: 1.25rem; border-radius: 6px; background: #fafafa; display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
              <div style="display: flex; align-items: center; gap: 0.75rem;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="#dc2626"><path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/></svg>
                <div>
                  <strong>${fileName || 'Pozvánka s programom.pdf'}</strong>
                  <div style="font-size: 0.85rem; color: #6b7280;">Oficiálna pozvánka vo formáte PDF</div>
                </div>
              </div>
              <a href="${attachedFileSubpagePath}" target="_blank" rel="noopener noreferrer" class="idsk-button" style="display: inline-flex; align-items: center; gap: 0.5rem; background: var(--idsk-color-primary, #003366); color: #fff; padding: 0.5rem 1rem; border-radius: 4px; text-decoration: none; font-weight: 600;">
                Stiahnuť PDF
              </a>
            </div>` : ''}

            <div class="mt-5 pt-3" style="border-top: 1px solid #e5e7eb; padding-top: 1.5rem;">
              <a href="../" class="idsk-button idsk-button--secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; padding: 0.5rem 1rem; background: #e5e7eb; color: #111; border-radius: 4px; font-weight: 600;">
                ← Späť na zoznam pozvánok
              </a>
            </div>
          </div>
        </article>
      </div>
    </div>
  </main>
${footerPart || '</body></html>'}`;

      fs.writeFileSync(path.join(ozDir, 'index.html'), meetingHtml, 'utf-8');

      // Vloženie do indexu
      const ozIndexPath = path.join(PUBLIC_DIR, 'samosprava', 'obecne-zastupitelstvo', 'pozvanky-na-zasadnutie-oz-1', 'index.html');
      let ozIndex = fs.readFileSync(ozIndexPath, 'utf-8');

      const newOzCardMarkup = `
        <div class="item">
            <div class="item-heading">
                <a class="item-href" href="./${slug}/" target="_blank" rel="noopener noreferrer">${title}</a>
            </div>
            <div class="item-data">
                <span class="item-date item-date-from">Vyvesené: ${new Date().toLocaleDateString('sk-SK')}</span>
                <span class="item-date item-date-to">Zasadnutie: ${dStr}</span>
            </div>
        </div>`;

      if (ozIndex.includes('<div class="card-body">')) {
        ozIndex = ozIndex.replace('<div class="card-body">', `<div class="card-body">\n${newOzCardMarkup}`);
        fs.writeFileSync(ozIndexPath, ozIndex, 'utf-8');
      }

      sendJson(res, 200, {
        success: true,
        slug,
        url: `/samosprava/obecne-zastupitelstvo/pozvanky-na-zasadnutie-oz-1/${slug}/`,
        message: 'Pozvánka na zasadnutie OZ bola úspešne vyvesená!'
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 16. Knižnica médií (Media Library - zoznam súborov)
  if (pathname === '/api/media' && req.method === 'GET') {
    try {
      const mediaList = [];
      const scanDirs = [
        { dir: path.join(PUBLIC_DIR, 'data', 'cache_images'), folderName: 'cache_images', type: 'image' },
        { dir: path.join(PUBLIC_DIR, 'data', 'uredni_deska'), folderName: 'uredni_deska', type: 'document' },
        { dir: path.join(PUBLIC_DIR, 'data', 'vzn'), folderName: 'vzn', type: 'document' },
        { dir: path.join(PUBLIC_DIR, 'data', 'pozvanky'), folderName: 'pozvanky', type: 'document' },
        { dir: path.join(PUBLIC_DIR, 'data', 'fotogaleria'), folderName: 'fotogaleria', type: 'image' }
      ];

      for (const item of scanDirs) {
        if (!fs.existsSync(item.dir)) continue;
        const files = fs.readdirSync(item.dir, { withFileTypes: true });
        for (const file of files) {
          if (file.isFile()) {
            const ext = path.extname(file.name).toLowerCase();
            const stats = fs.statSync(path.join(item.dir, file.name));
            mediaList.push({
              name: file.name,
              folder: item.folderName,
              type: ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'].includes(ext) ? 'image' : (ext === '.pdf' ? 'pdf' : (ext === '.mp3' ? 'audio' : 'other')),
              url: `/data/${item.folderName}/${file.name}`,
              size: stats.size,
              modified: stats.mtime.toISOString()
            });
          }
        }
      }

      // Zoradíme od najnovších
      mediaList.sort((a, b) => new Date(b.modified) - new Date(a.modified));

      sendJson(res, 200, { media: mediaList.slice(0, 100), total: mediaList.length });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 17. Upload nového média do knižnice
  if (pathname === '/api/media/upload' && req.method === 'POST') {
    try {
      const body = await parseBody(req);
      const { fileName, fileBase64, folder } = body;

      if (!fileName || !fileBase64) {
        sendJson(res, 400, { error: 'Chýba súbor alebo názov.' });
        return;
      }

      const targetFolder = ['cache_images', 'uredni_deska', 'vzn', 'pozvanky', 'fotogaleria'].includes(folder) ? folder : 'cache_images';
      const destDir = path.join(PUBLIC_DIR, 'data', targetFolder);
      fs.mkdirSync(destDir, { recursive: true });

      const safeName = Date.now() + '_' + fileName.replace(/[^a-zA-Z0-9._-]/g, '_');
      const destPath = path.join(destDir, safeName);

      const base64Data = fileBase64.replace(/^data:[^;]+;base64,/, '');
      fs.writeFileSync(destPath, Buffer.from(base64Data, 'base64'));

      sendJson(res, 200, {
        success: true,
        message: 'Súbor bol úspešne nahraný do knižnice médií!',
        name: safeName,
        url: `/data/${targetFolder}/${safeName}`
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 18. Fotogaléria (Zoznam albumov)
  if (pathname === '/api/fotogaleria' && req.method === 'GET') {
    try {
      const fotoDir = path.join(PUBLIC_DIR, 'data', 'fotogaleria');
      const albums = [];
      if (fs.existsSync(fotoDir)) {
        const entries = fs.readdirSync(fotoDir, { withFileTypes: true });
        for (const entry of entries) {
          if (entry.isDirectory()) {
            const albumPath = path.join(fotoDir, entry.name);
            const photos = fs.readdirSync(albumPath).filter(f => /\.(jpe?g|png|webp)$/i.test(f));
            albums.push({
              slug: entry.name,
              name: entry.name.replace(/[-_]/g, ' '),
              photoCount: photos.length,
              cover: photos.length > 0 ? `/data/fotogaleria/${entry.name}/${photos[0]}` : null
            });
          }
        }
      }
      sendJson(res, 200, { albums, total: albums.length });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // --- STATICKÉ SÚBORY A CMS FRONTEND ---

  // /admin alebo /admin/ -> serve public/admin/index.html
  if (pathname === '/admin' || pathname === '/admin/') {
    serveStatic(req, res, path.join(PUBLIC_DIR, 'admin', 'index.html'));
    return;
  }

  // Akékoľvek súbory v /admin/*
  if (pathname.startsWith('/admin/')) {
    const relFile = pathname.replace('/admin/', '');
    const localFile = path.join(PUBLIC_DIR, 'admin', relFile);
    if (fs.existsSync(localFile) && fs.statSync(localFile).isFile()) {
      serveStatic(req, res, localFile);
      return;
    }
  }

  // Všeobecné servovanie z public/
  let reqPath = path.join(PUBLIC_DIR, pathname);
  if (fs.existsSync(reqPath)) {
    if (fs.statSync(reqPath).isDirectory()) {
      const indexFile = path.join(reqPath, 'index.html');
      if (fs.existsSync(indexFile)) {
        serveStatic(req, res, indexFile);
        return;
      }
    } else {
      serveStatic(req, res, reqPath);
      return;
    }
  }

  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('404 Stránka alebo súbor sa nenašiel.');
});

server.listen(PORT, () => {
  console.log(`=======================================================`);
  console.log(`  Obec Horný Vadičov - WordPress-like IDSK 3.0 CMS Server`);
  console.log(`  Spustený na: http://localhost:${PORT}`);
  console.log(`  Administrácia: http://localhost:${PORT}/admin/`);
  console.log(`=======================================================`);
});
