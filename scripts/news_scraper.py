#!/usr/bin/env python3
"""
Douglas Vilar News - Scraper de Noticias Juridicas v2.0
Executa diariamente as 04h via GitHub Actions
ABORDAGENS: RSS, Google News, APIs publicas, HTML scraping, feeds Atom

Fontes expandidas (30+):
  TRIBUNAIS: STJ, STF, TST, TJPR, TJSP, TJRS, TRT-9, TRT-2
  ORGAOS: CRECI-PR, COFECI, Senado Federal, Camara dos Deputados
  JURIDICO: Conjur, Migalhas, JOTA, IRIB, Secovi-SP
  MIDIA BR: Gazeta do Povo, Jovem Pan, Revista Oeste, InfoMoney, Valor
  INTERNACIONAL: Google News EN, Reuters RSS, BBC Business, CNBC RE
  IMOBILIARIO: FipeZap, CBIC, Abrainc, Sinduscon

Autor: Douglas Vilar - OAB/PR 47.278
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
import feedparser

BR_TZ = timezone(timedelta(hours=-3))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# ============================================================
# KEYWORDS POR CATEGORIA
# ============================================================
KW_IMOB = [
    "imovel", "imobiliario", "locacao", "despejo", "condominio", "usucapiao",
    "registro de imoveis", "incorporacao", "loteamento", "compromisso de compra",
    "hipoteca", "alienacao fiduciaria", "ITBI", "propriedade", "escritura",
    "matricula", "averbacao", "retificacao", "distrato imobiliario",
    "lei do inquilinato", "contrato de locacao", "fianca locaticia",
    "direito real", "posse", "desapropriacao", "regularizacao fundiaria",
    "usucapiao extrajudicial", "REURB", "direito imobiliario",
    "compra e venda de imovel", "promessa de compra", "corretagem",
    "vicio construtivo", "atraso na entrega", "incorporadora",
]

KW_MERCADO = [
    "mercado imobiliario", "construcao civil", "financiamento imobiliario",
    "credito habitacional", "Minha Casa", "FII", "fundo imobiliario",
    "Selic", "taxa de juros", "lancamento imobiliario", "venda de imoveis",
    "preco de imoveis", "FipeZap", "CBIC", "Abrainc", "Sinduscon",
    "credito imobiliario", "FGTS", "Casa Verde Amarela", "SFH", "SFI",
    "CRI", "LCI", "aluguel", "rentabilidade", "vacancia",
    "construtora", "incorporadora", "real estate market",
    "housing market", "property market", "mortgage rates", "REIT",
    "real estate", "property prices", "housing prices",
]

KW_TRABALHO = [
    "trabalhista", "CLT", "empregado", "empregador", "rescisao",
    "FGTS", "horas extras", "assedio", "demissao", "vinculo empregaticio",
    "justa causa", "aviso previo", "ferias", "13o salario",
    "insalubridade", "periculosidade", "acidente de trabalho",
    "estabilidade", "intervalo", "terceirizacao", "pejotizacao",
    "reforma trabalhista", "trabalho remoto", "teletrabalho",
    "sindicato", "convencao coletiva", "dissidio",
    "labor", "employment", "workers", "wage",
]


# ============================================================
# FONTES COM MULTIPLAS ABORDAGENS
# ============================================================

def get_rss_sources():
    """Fontes via RSS/Atom - mais confiavel."""
    return [
        # TRIBUNAIS
        {"name": "STJ", "url": "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias-RSS.aspx", "priority": 1, "type": "tribunal"},
        {"name": "STF", "url": "https://portal.stf.jus.br/noticias/rss.asp", "priority": 1, "type": "tribunal"},
        {"name": "TST", "url": "https://www.tst.jus.br/rssfeed/journal", "priority": 1, "type": "tribunal"},

        # JURIDICO
        {"name": "Conjur", "url": "https://www.conjur.com.br/rss.xml", "priority": 2, "type": "media"},
        {"name": "Migalhas", "url": "https://www.migalhas.com.br/rss/quentes", "priority": 2, "type": "media"},
        {"name": "JOTA", "url": "https://www.jota.info/feed", "priority": 2, "type": "media"},

        # SENADO E CAMARA
        {"name": "Senado Federal", "url": "https://www12.senado.leg.br/noticias/feed", "priority": 2, "type": "governo"},
        {"name": "Camara dos Deputados", "url": "https://www.camara.leg.br/noticias/rss/ultimas", "priority": 2, "type": "governo"},
        {"name": "Agencia Brasil", "url": "http://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml", "priority": 3, "type": "media"},

        # MIDIA BR
        {"name": "Gazeta do Povo", "url": "https://www.gazetadopovo.com.br/feed/", "priority": 3, "type": "media"},
        {"name": "InfoMoney", "url": "https://www.infomoney.com.br/feed/", "priority": 3, "type": "media"},
        {"name": "Valor Economico", "url": "https://pox.globo.com/rss/valor/", "priority": 3, "type": "media"},
        {"name": "Estadao", "url": "https://www.estadao.com.br/arc/outboundfeeds/rss/?outputType=xml", "priority": 3, "type": "media"},
        {"name": "Folha de SP", "url": "https://feeds.folha.uol.com.br/mercado/rss091.xml", "priority": 3, "type": "media"},

        # INTERNACIONAL
        {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews", "priority": 4, "type": "international", "lang": "en"},
        {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "priority": 4, "type": "international", "lang": "en"},
        {"name": "CNBC Real Estate", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=104723436", "priority": 4, "type": "international", "lang": "en"},
    ]


def get_google_news_queries():
    """Buscas no Google News RSS - abordagem alternativa poderosa."""
    queries = [
        # Direito Imobiliario
        '"direito imobiliario" OR "usucapiao" OR "registro de imoveis"',
        '"condominio" "decisao judicial"',
        '"incorporadora" "atraso entrega" OR "distrato"',
        '"locacao" "lei do inquilinato" OR "despejo"',
        '"CRECI" OR "COFECI" "imobiliario"',

        # Mercado Imobiliario
        '"mercado imobiliario" Brasil',
        '"fundo imobiliario" OR "FII" rentabilidade',
        '"financiamento imobiliario" OR "credito habitacional" Selic',
        '"lancamento imobiliario" OR "venda imoveis" 2026',
        '"CBIC" OR "Abrainc" OR "Sinduscon" mercado',

        # Direito do Trabalho
        '"direito do trabalho" OR "CLT" decisao TST',
        '"reforma trabalhista" OR "pejotizacao" OR "terceirizacao"',
        '"horas extras" OR "justa causa" OR "rescisao" trabalhista',

        # Internacional
        '"real estate market" Brazil OR "mercado imobiliario"',
        '"housing market" trends 2026',
    ]
    return queries


def get_html_sources():
    """Fontes via HTML scraping direto."""
    return [
        # CRECI e COFECI
        {"name": "COFECI", "urls": [
            "https://www.cofeci.gov.br/noticias",
            "https://www.cofeci.gov.br/",
        ], "priority": 2, "type": "orgao"},
        {"name": "CRECI-PR", "urls": [
            "https://www.crecipr.gov.br/noticias",
            "https://www.crecipr.gov.br/",
        ], "priority": 2, "type": "orgao"},
        {"name": "CRECI-SP", "urls": [
            "https://www.crecisp.gov.br/noticias",
        ], "priority": 3, "type": "orgao"},

        # TRIBUNAIS - HTML
        {"name": "TJPR", "urls": [
            "https://www.tjpr.jus.br/noticias",
        ], "priority": 2, "type": "tribunal"},
        {"name": "TJSP", "urls": [
            "https://www.tjsp.jus.br/Noticias/Noticias",
        ], "priority": 2, "type": "tribunal"},
        {"name": "TRT-9 (PR)", "urls": [
            "https://www.trt9.jus.br/portal/noticias.xhtml",
        ], "priority": 2, "type": "tribunal"},

        # IMOBILIARIO ESPECIALIZADO
        {"name": "IRIB", "urls": [
            "https://www.irib.org.br/noticias",
        ], "priority": 3, "type": "media"},
        {"name": "Secovi-SP", "urls": [
            "https://www.secovi.com.br/noticias",
        ], "priority": 3, "type": "media"},
        {"name": "CBIC", "urls": [
            "https://cbic.org.br/noticias/",
        ], "priority": 3, "type": "media"},
        {"name": "Abrainc", "urls": [
            "https://www.abrainc.org.br/noticias/",
        ], "priority": 3, "type": "media"},

        # MIDIA
        {"name": "Revista Oeste", "urls": [
            "https://revistaoeste.com/economia/",
        ], "priority": 3, "type": "media"},
        {"name": "Jovem Pan News", "urls": [
            "https://jovempan.com.br/noticias/economia",
        ], "priority": 3, "type": "media"},
    ]


# ============================================================
# FUNCOES DE BUSCA
# ============================================================

def fetch_url(url, timeout=20):
    """Busca URL com tratamento robusto."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, verify=True, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except Exception as e:
        print(f"    [ERRO] {url}: {type(e).__name__}: {str(e)[:100]}")
        return None


def fetch_rss_feed(url):
    """Busca e parseia feed RSS/Atom."""
    try:
        feed = feedparser.parse(url, agent=HEADERS['User-Agent'])
        if feed.bozo and not feed.entries:
            print(f"    [AVISO] Feed com problemas: {url}")
            return []
        return feed.entries[:20]
    except Exception as e:
        print(f"    [ERRO] RSS {url}: {e}")
        return []


def fetch_google_news(query, num=10):
    """Busca via Google News RSS - funciona sem API key."""
    encoded = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        feed = feedparser.parse(url, agent=HEADERS['User-Agent'])
        articles = []
        for entry in feed.entries[:num]:
            title = entry.get('title', '').strip()
            # Google News coloca " - Fonte" no final do titulo
            source_match = re.search(r' - ([^-]+)$', title)
            source = source_match.group(1).strip() if source_match else 'Google News'
            clean_title = re.sub(r' - [^-]+$', '', title).strip()

            if len(clean_title) < 15:
                continue

            summary = ''
            if entry.get('summary'):
                soup = BeautifulSoup(entry.summary, 'html.parser')
                summary = soup.get_text(strip=True)[:300]

            pub_date = None
            if entry.get('published_parsed'):
                from time import mktime
                pub_date = datetime.fromtimestamp(
                    mktime(entry.published_parsed), tz=BR_TZ
                ).isoformat()

            articles.append({
                "title": clean_title,
                "summary": summary,
                "url": entry.get('link', ''),
                "date": pub_date,
                "source": source,
            })
        return articles
    except Exception as e:
        print(f"    [ERRO] Google News: {e}")
        return []


def extract_from_rss_entries(entries, source_name):
    """Extrai artigos de entradas RSS."""
    articles = []
    for entry in entries[:15]:
        title = entry.get('title', '').strip()
        if not title or len(title) < 15:
            continue

        link = entry.get('link', '')
        summary = ''
        if entry.get('summary'):
            soup = BeautifulSoup(entry.summary, 'html.parser')
            summary = soup.get_text(strip=True)[:300]
        elif entry.get('description'):
            soup = BeautifulSoup(entry.description, 'html.parser')
            summary = soup.get_text(strip=True)[:300]

        pub_date = None
        if entry.get('published_parsed'):
            from time import mktime
            try:
                pub_date = datetime.fromtimestamp(
                    mktime(entry.published_parsed), tz=BR_TZ
                ).isoformat()
            except:
                pass
        elif entry.get('updated_parsed'):
            from time import mktime
            try:
                pub_date = datetime.fromtimestamp(
                    mktime(entry.updated_parsed), tz=BR_TZ
                ).isoformat()
            except:
                pass

        articles.append({
            "title": title,
            "summary": summary,
            "url": link,
            "date": pub_date,
            "source": source_name,
        })
    return articles


def extract_from_html(html, base_url, source_name):
    """Extrai artigos de HTML com multiplos seletores."""
    articles = []
    if not html:
        return articles

    soup = BeautifulSoup(html, 'html.parser')

    selectors = [
        'article',
        '.news-item', '.noticia', '.post', '.card-body',
        '.list-item', '.item-noticia', '.entry',
        '.news-card', '.materia', '.resultado',
        'li.item', '.listagem-noticias li',
        '.views-row', '.td-block-span',
        '.noticias-lista .item', '.lista-noticias .item',
        '.elementor-post', '.blog-post',
        'div[class*="noticia"]', 'div[class*="news"]',
        'div[class*="post"]',
    ]

    for selector in selectors:
        try:
            items = soup.select(selector)
        except:
            continue

        for item in items[:10]:
            title_el = item.find(['h1', 'h2', 'h3', 'h4'])
            if not title_el:
                link_el = item.find('a')
                if link_el and len(link_el.get_text(strip=True)) > 15:
                    title_el = link_el
                else:
                    continue

            title = title_el.get_text(strip=True)
            if len(title) < 15 or len(title) > 500:
                continue

            link = None
            if title_el.name == 'a':
                link = title_el.get('href', '')
            else:
                a_tag = title_el.find('a') or item.find('a')
                if a_tag:
                    link = a_tag.get('href', '')

            if link and link.startswith('/'):
                link = urljoin(base_url, link)
            elif link and not link.startswith('http'):
                link = urljoin(base_url, link)

            summary = ""
            for p_sel in ['p', '.resumo', '.summary', '.excerpt', '.descricao', '.texto', 'span.description']:
                desc = item.find(p_sel) if not '.' in p_sel else item.select_one(p_sel)
                if desc and desc != title_el:
                    summary = desc.get_text(strip=True)[:300]
                    if len(summary) > 20:
                        break

            articles.append({
                "title": title,
                "summary": summary,
                "url": link or base_url,
                "date": None,
                "source": source_name,
            })

        if articles:
            break

    return articles


def classify_article(title, summary):
    """Classifica artigo por categoria usando keywords."""
    text = (title + ' ' + summary).lower()
    # Remove acentos simples para matching
    import unicodedata
    text_norm = unicodedata.normalize('NFD', text)
    text_norm = text_norm.encode('ascii', 'ignore').decode('ascii').lower()

    scores = {'direito-imobiliario': 0, 'mercado-imobiliario': 0, 'direito-trabalho': 0}

    for kw in KW_IMOB:
        kw_norm = unicodedata.normalize('NFD', kw).encode('ascii', 'ignore').decode('ascii').lower()
        if kw_norm in text_norm:
            scores['direito-imobiliario'] += 2
        elif kw.lower() in text:
            scores['direito-imobiliario'] += 2

    for kw in KW_MERCADO:
        kw_norm = unicodedata.normalize('NFD', kw).encode('ascii', 'ignore').decode('ascii').lower()
        if kw_norm in text_norm:
            scores['mercado-imobiliario'] += 2
        elif kw.lower() in text:
            scores['mercado-imobiliario'] += 2

    for kw in KW_TRABALHO:
        kw_norm = unicodedata.normalize('NFD', kw).encode('ascii', 'ignore').decode('ascii').lower()
        if kw_norm in text_norm:
            scores['direito-trabalho'] += 2
        elif kw.lower() in text:
            scores['direito-trabalho'] += 2

    max_score = max(scores.values())
    if max_score == 0:
        return None
    for cat, score in scores.items():
        if score == max_score:
            return cat
    return None


def gen_id(title, date_str):
    content = f"{title}_{date_str}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


# ============================================================
# MAIN SCRAPER
# ============================================================

def run_scraper():
    today = datetime.now(BR_TZ)
    today_str = today.strftime("%Y-%m-%d")
    all_found = []

    print(f"\n{'='*60}")
    print(f"  DOUGLAS VILAR NEWS - Scraper v2.0")
    print(f"  Data: {today_str} | Hora: {today.strftime('%H:%M')}")
    print(f"  Fontes: RSS + Google News + HTML (30+)")
    print(f"{'='*60}")

    # ---- ABORDAGEM 1: RSS FEEDS ----
    print(f"\n--- ABORDAGEM 1: RSS FEEDS ---")
    for src in get_rss_sources():
        print(f"  [{src['priority']}] RSS: {src['name']}...")
        entries = fetch_rss_feed(src['url'])
        if entries:
            arts = extract_from_rss_entries(entries, src['name'])
            print(f"    -> {len(entries)} entradas, {len(arts)} artigos")
            for a in arts:
                cat = classify_article(a['title'], a['summary'])
                if cat:
                    a['category'] = cat
                    a['translated'] = src.get('lang') == 'en'
                    a['priority'] = src['priority']
                    all_found.append(a)
        else:
            print(f"    -> 0 entradas")

    # ---- ABORDAGEM 2: GOOGLE NEWS RSS ----
    print(f"\n--- ABORDAGEM 2: GOOGLE NEWS ---")
    for query in get_google_news_queries():
        short_q = query[:50] + '...' if len(query) > 50 else query
        print(f"  Buscando: {short_q}")
        arts = fetch_google_news(query, num=8)
        print(f"    -> {len(arts)} resultados")
        for a in arts:
            cat = classify_article(a['title'], a['summary'])
            if cat:
                a['category'] = cat
                a['translated'] = False
                a['priority'] = 3
                all_found.append(a)

    # ---- ABORDAGEM 3: HTML SCRAPING ----
    print(f"\n--- ABORDAGEM 3: HTML SCRAPING ---")
    for src in get_html_sources():
        print(f"  [{src['priority']}] HTML: {src['name']}...")
        for url in src.get('urls', []):
            html = fetch_url(url)
            if html:
                arts = extract_from_html(html, url, src['name'])
                print(f"    -> {url}: {len(arts)} artigos")
                for a in arts:
                    cat = classify_article(a['title'], a['summary'])
                    if cat:
                        a['category'] = cat
                        a['translated'] = False
                        a['priority'] = src['priority']
                        all_found.append(a)

    # ---- DEDUPLICACAO ----
    print(f"\n--- RESULTADOS ---")
    print(f"  Total bruto: {len(all_found)}")

    seen_titles = set()
    unique = []
    for a in all_found:
        title_key = re.sub(r'[^a-zA-Z0-9]', '', a['title'].lower())[:60]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique.append(a)

    print(f"  Apos deduplicacao: {len(unique)}")

    # ---- SELECAO DAS MELHORES ----
    unique.sort(key=lambda x: x.get('priority', 99))

    selected = []

    # 1 materia de Direito Imobiliario
    for a in unique:
        if a['category'] == 'direito-imobiliario':
            selected.append(a)
            break

    # 1 materia de Mercado Imobiliario
    for a in unique:
        if a['category'] == 'mercado-imobiliario' and a not in selected:
            selected.append(a)
            break

    # Se faltou, pega qualquer uma
    if len(selected) < 2:
        for a in unique:
            if a not in selected:
                selected.append(a)
                if len(selected) >= 2:
                    break

    # Formata para publicacao
    now = datetime.now(BR_TZ)
    for a in selected:
        a['author'] = 'Douglas Vilar'
        a['sourceUrl'] = a.pop('url', '')
        a['id'] = gen_id(a['title'], today_str)
        if not a.get('date'):
            a['date'] = now.isoformat()
        a.pop('priority', None)

    print(f"\n  Materias selecionadas:")
    for i, a in enumerate(selected, 1):
        print(f"    {i}. [{a['category']}] {a['title'][:80]}...")
        print(f"       Fonte: {a['source']} | Link: {a.get('sourceUrl', '')[:60]}...")

    return selected


def update_json(new_articles):
    news_file = Path(__file__).parent.parent / 'data' / 'news.json'
    existing = []
    if news_file.exists():
        try:
            with open(news_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            existing = []

    existing_ids = {a.get('id') for a in existing}
    added = 0
    for a in new_articles:
        if a.get('id') not in existing_ids:
            existing.insert(0, a)
            added += 1

    existing = existing[:120]

    news_file.parent.mkdir(parents=True, exist_ok=True)
    with open(news_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\n  [OK] {added} novas materias adicionadas")
    print(f"  [OK] Total no arquivo: {len(existing)}")
    print(f"  [OK] Salvo em: {news_file}")


def main():
    selected = run_scraper()
    if not selected:
        now = datetime.now(BR_TZ)
        selected = [{
            "id": now.strftime("%Y-%m-%d") + "-placeholder",
            "title": "Acompanhe as novidades do Direito Imobiliario",
            "summary": "Noticias atualizadas diariamente as 04h com curadoria de mais de 30 fontes.",
            "category": "direito-imobiliario",
            "source": "Douglas Vilar News",
            "sourceUrl": "https://douglasvilar.com.br/noticias",
            "date": now.isoformat(),
            "author": "Douglas Vilar",
            "translated": False,
        }]
    update_json(selected)
    print(f"\n{'='*60}")
    print(f"  Busca finalizada com sucesso!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
