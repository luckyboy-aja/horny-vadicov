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

      const countDirs = (dir) => {
        if (!fs.existsSync(dir)) return 0;
        return fs.readdirSync(dir, { withFileTypes: true }).filter(d => d.isDirectory()).length;
      };

      sendJson(res, 200, {
        status: 'ok',
        version: '1.0.0',
        mode: 'local',
        repo: 'luckyboy-aja/horny-vadicov',
        siteUrl: 'https://luckyboy-aja.github.io/horny-vadicov/',
        stats: {
          articlesCount: countDirs(aktualityPath),
          boardCount: countDirs(tabulaPath),
          vznCount: countDirs(vznPath),
          lastCheck: new Date().toISOString()
        }
      });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 2. Zoznam aktualít
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

  // 3. Vytvorenie novej aktuality
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

      // 1. Vygenerovanie podstránky aktuality (podľa vzorovej podstránky)
      const samplePagePath = path.join(PUBLIC_DIR, 'obec-2', 'aktuality', 'otvorenie-skolskeho-roka-2026-2027-605sk', 'index.html');
      let sampleHtml = '';
      if (fs.existsSync(samplePagePath)) {
        sampleHtml = fs.readFileSync(samplePagePath, 'utf-8');
      } else {
        sampleHtml = fs.readFileSync(path.join(PUBLIC_DIR, 'obec-2', 'aktuality', 'index.html'), 'utf-8');
      }

      // Extrahovanie hlavičky a pätičky
      const headerPart = sampleHtml.split('<div class="idsk-subpage-body editor_content">')[0];
      const footerPart = sampleHtml.split('</article>')[1] || sampleHtml.split('</main>')[1];

      // Úprava relatívnych ciest (z obec-2/aktuality do obec-2/aktuality/slug)
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

      // 2. Vloženie novej aktuality na začiatok zoznamu v index.html
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

      // Vložíme za začiatok kontajnera eventov
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

  // 4. Zoznam položiek úradnej tabule
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

      sendJson(res, 200, { notices: notices.slice(0, 50) });
    } catch (e) {
      sendJson(res, 500, { error: e.message });
    }
    return;
  }

  // 5. Vytvorenie nového oznamu na úradnej tabuli
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
  console.log(`  Obec Horný Vadičov - IDSK 3.0 CMS Server`);
  console.log(`  Spustený na: http://localhost:${PORT}`);
  console.log(`  Administrácia: http://localhost:${PORT}/admin/`);
  console.log(`=======================================================`);
});
