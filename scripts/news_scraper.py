#!/usr/bin/env python3
"""
Douglas Vilar News - Scraper de Notícias Jurídicas
Executa diariamente às 04h via GitHub Actions
Busca notícias em 20+ fontes sobre:
- Direito Imobiliário
- Mercado Imobiliário  
- Direito do Trabalho
- Matérias replicadas em múltiplas mídias

Prioridade de fontes:
1. STJ, STF, TST
2. TJPR, TJSP, TJRS
3. Gazeta do Povo, Wall Street Journal, Jovem Pan News, Revista Oeste
4. Sites internacionais (Reuters, Bloomberg) - traduzidos

Autor: Douglas Vilar - OAB/PR 47.278
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import feedparser

# Timezone Brasil
BR_TZ = timezone(timedelta(hours=-3))

# ============================================================
# CONFIGURAÇÃO DAS FONTES
# ============================================================
SOURCES = {
    # ---- TRIBUNAIS SUPERIORES (Prioridade 1) ----
    "STJ": {
        "urls": [
            "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias.aspx",
        ],
        "rss": "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias-RSS.aspx",
        "keywords_imob": ["imóvel", "imobiliário", "locação", "despejo", "condomínio", "usucapião",
                          "registro de imóveis", "incorporação", "loteamento", "compromisso de compra",
                          "hipoteca", "alienação fiduciária", "ITBI", "propriedade"],
        "keywords_mercado": ["mercado imobiliário", "construção civil", "financiamento imobiliário",
                             "crédito habitacional", "Minha Casa", "FII", "fundo imobiliário"],
        "keywords_trabalho": ["trabalhista", "CLT", "empregado", "empregador", "rescisão",
                              "FGTS", "horas extras", "assédio", "demissão", "vínculo empregatício"],
        "priority": 1,
        "type": "tribunal"
    },
    "STF": {
        "urls": [
            "https://portal.stf.jus.br/noticias/listarNoticias.asp",
        ],
        "rss": "https://portal.stf.jus.br/noticias/rss.asp",
        "keywords_imob": ["imóvel", "propriedade", "desapropriação", "usucapião", "moradia",
                          "função social", "direito de propriedade"],
        "keywords_mercado": ["mercado imobiliário", "construção", "habitação", "urbanismo"],
        "keywords_trabalho": ["trabalhista", "trabalho", "empregado", "sindicato", "greve",
                              "terceirização", "pejotização"],
        "priority": 1,
        "type": "tribunal"
    },
    "TST": {
        "urls": [
            "https://www.tst.jus.br/noticias",
        ],
        "rss": "https://www.tst.jus.br/rssfeed/journal",
        "keywords_imob": ["imóvel", "imobiliário"],
        "keywords_mercado": ["construção civil", "mercado imobiliário"],
        "keywords_trabalho": ["trabalhista", "CLT", "empregado", "empregador", "rescisão",
                              "FGTS", "trabalho", "justa causa", "assédio moral", "horas extras",
                              "intervalo", "insalubridade", "periculosidade", "acidente de trabalho",
                              "estabilidade", "aviso prévio", "férias", "13o salário"],
        "priority": 1,
        "type": "tribunal"
    },

    # ---- TRIBUNAIS ESTADUAIS (Prioridade 2) ----
    "TJPR": {
        "urls": [
            "https://www.tjpr.jus.br/noticias",
        ],
        "keywords_imob": ["imóvel", "imobiliário", "condomínio", "locação", "despejo",
                          "usucapião", "registro", "incorporação"],
        "keywords_mercado": ["mercado imobiliário", "construção civil"],
        "keywords_trabalho": ["trabalhista", "trabalho"],
        "priority": 2,
        "type": "tribunal"
    },
    "TJSP": {
        "urls": [
            "https://www.tjsp.jus.br/Noticias/Noticias",
        ],
        "keywords_imob": ["imóvel", "imobiliário", "condomínio", "locação", "despejo",
                          "usucapião", "registro", "incorporação"],
        "keywords_mercado": ["mercado imobiliário", "construção civil"],
        "keywords_trabalho": ["trabalhista", "trabalho"],
        "priority": 2,
        "type": "tribunal"
    },
    "TJRS": {
        "urls": [
            "https://www.tjrs.jus.br/novo/noticia/",
        ],
        "keywords_imob": ["imóvel", "imobiliário", "condomínio", "locação"],
        "keywords_mercado": ["mercado imobiliário"],
        "keywords_trabalho": ["trabalhista", "trabalho"],
        "priority": 2,
        "type": "tribunal"
    },

    # ---- MÍDIA NACIONAL (Prioridade 3) ----
    "Gazeta do Povo": {
        "urls": [
            "https://www.gazetadopovo.com.br/economia/",
            "https://www.gazetadopovo.com.br/vida-e-cidadania/",
        ],
        "rss": "https://www.gazetadopovo.com.br/feed/",
        "keywords_imob": ["imóvel", "imobiliário", "condomínio", "locação", "aluguel",
                          "escritura", "registro", "ITBI", "IPTU"],
        "keywords_mercado": ["mercado imobiliário", "construtora", "incorporadora", "Selic",
                             "financiamento", "crédito imobiliário", "FII", "fundo imobiliário",
                             "venda de imóveis", "lançamento imobiliário"],
        "keywords_trabalho": ["CLT", "trabalhista", "demissão", "emprego", "reforma trabalhista"],
        "priority": 3,
        "type": "media"
    },
    "Jovem Pan News": {
        "urls": [
            "https://jovempan.com.br/noticias/economia",
            "https://jovempan.com.br/noticias/brasil",
        ],
        "keywords_imob": ["imóvel", "imobiliário", "moradia", "habitação"],
        "keywords_mercado": ["mercado imobiliário", "construção civil", "Selic", "financiamento"],
        "keywords_trabalho": ["CLT", "trabalhista", "emprego", "desemprego"],
        "priority": 3,
        "type": "media"
    },
    "Revista Oeste": {
        "urls": [
            "https://revistaoeste.com/economia/",
            "https://revistaoeste.com/brasil/",
        ],
        "keywords_imob": ["imóvel", "imobiliário", "propriedade"],
        "keywords_mercado": ["mercado imobiliário", "construção", "Selic"],
        "keywords_trabalho": ["trabalhista", "CLT", "emprego"],
        "priority": 3,
        "type": "media"
    },
    "Conjur": {
        "urls": [
            "https://www.conjur.com.br/",
        ],
        "rss": "https://www.conjur.com.br/rss.xml",
        "keywords_imob": ["imóvel", "imobiliário", "locação", "usucapião", "condomínio",
                          "despejo", "registro de imóveis", "incorporação"],
        "keywords_mercado": ["mercado imobiliário"],
        "keywords_trabalho": ["trabalhista", "CLT", "TST", "trabalho"],
        "priority": 3,
        "type": "media"
    },
    "Migalhas": {
        "urls": [
            "https://www.migalhas.com.br/quentes",
        ],
        "rss": "https://www.migalhas.com.br/rss/quentes",
        "keywords_imob": ["imóvel", "imobiliário", "locação", "condomínio", "usucapião"],
        "keywords_mercado": ["mercado imobiliário", "incorporação", "construção civil"],
        "keywords_trabalho": ["trabalhista", "CLT", "TST", "trabalho", "empregado"],
        "priority": 3,
        "type": "media"
    },
    "IRIB": {
        "urls": [
            "https://www.irib.org.br/noticias",
        ],
        "keywords_imob": ["registro", "imóvel", "imobiliário", "escritura", "matrícula",
                          "averbação", "usucapião", "retificação"],
        "keywords_mercado": ["mercado imobiliário"],
        "keywords_trabalho": [],
        "priority": 3,
        "type": "media"
    },
    "Secovi-SP": {
        "urls": [
            "https://www.secovi.com.br/noticias",
        ],
        "keywords_imob": ["imóvel", "imobiliário", "locação", "condomínio"],
        "keywords_mercado": ["mercado imobiliário", "venda", "lançamento", "locação",
                             "aluguel", "incorporação", "construção"],
        "keywords_trabalho": [],
        "priority": 3,
        "type": "media"
    },
    "InfoMoney": {
        "urls": [
            "https://www.infomoney.com.br/onde-investir/fundos-imobiliarios/",
        ],
        "keywords_imob": ["imóvel", "imobiliário"],
        "keywords_mercado": ["FII", "fundo imobiliário", "mercado imobiliário", "Selic",
                             "crédito imobiliário", "financiamento"],
        "keywords_trabalho": ["CLT", "trabalhista"],
        "priority": 3,
        "type": "media"
    },
    "Valor Econômico": {
        "urls": [
            "https://valor.globo.com/legislacao/",
        ],
        "keywords_imob": ["imóvel", "imobiliário", "propriedade"],
        "keywords_mercado": ["mercado imobiliário", "construção civil", "incorporação",
                             "financiamento imobiliário"],
        "keywords_trabalho": ["trabalhista", "reforma trabalhista", "emprego"],
        "priority": 3,
        "type": "media"
    },

    # ---- SITES INTERNACIONAIS (Prioridade 4) ----
    "Wall Street Journal": {
        "urls": [
            "https://www.wsj.com/real-estate",
        ],
        "keywords_imob": ["real estate", "property", "housing", "mortgage", "condominium",
                          "lease", "eviction", "tenant"],
        "keywords_mercado": ["real estate market", "housing market", "property market",
                             "construction", "REIT", "mortgage rates"],
        "keywords_trabalho": ["labor", "employment", "workers", "wage"],
        "priority": 4,
        "type": "international",
        "language": "en"
    },
    "Reuters": {
        "urls": [
            "https://www.reuters.com/business/finance/",
        ],
        "rss": "https://www.reuters.com/rssFeed/businessNews",
        "keywords_imob": ["real estate", "property", "housing"],
        "keywords_mercado": ["real estate market", "housing market", "construction",
                             "mortgage", "REIT"],
        "keywords_trabalho": ["labor", "employment", "workers"],
        "priority": 4,
        "type": "international",
        "language": "en"
    },
    "Bloomberg": {
        "urls": [
            "https://www.bloomberg.com/real-estate",
        ],
        "keywords_imob": ["real estate", "property", "housing"],
        "keywords_mercado": ["real estate market", "housing market", "property prices"],
        "keywords_trabalho": ["labor market", "employment"],
        "priority": 4,
        "type": "international",
        "language": "en"
    },
    "Financial Times": {
        "urls": [
            "https://www.ft.com/property",
        ],
        "keywords_imob": ["real estate", "property", "housing"],
        "keywords_mercado": ["real estate market", "property market", "housing prices"],
        "keywords_trabalho": ["labour", "employment"],
        "priority": 4,
        "type": "international",
        "language": "en"
    },
}

# ============================================================
# HEADERS PARA REQUESTS
# ============================================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# ============================================================
# FUNÇÕES DE SCRAPING
# ============================================================

def fetch_page(url, timeout=15):
    """Busca o conteúdo de uma URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, verify=True)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text
    except Exception as e:
        print(f"  [ERRO] Falha ao acessar {url}: {e}")
        return None


def fetch_rss(rss_url):
    """Busca e parseia um feed RSS."""
    try:
        feed = feedparser.parse(rss_url)
        return feed.entries if feed.entries else []
    except Exception as e:
        print(f"  [ERRO] Falha no RSS {rss_url}: {e}")
        return []


def extract_articles_from_html(html, base_url, source_name):
    """Extrai artigos de uma página HTML."""
    articles = []
    if not html:
        return articles

    soup = BeautifulSoup(html, 'html.parser')

    # Busca padrões comuns de artigos
    selectors = [
        'article', '.news-item', '.noticia', '.post', '.card',
        '.list-item', '.item-noticia', '.entry', '.news-card',
        'li.item', '.resultado', '.materia'
    ]

    for selector in selectors:
        items = soup.select(selector)
        for item in items[:10]:  # Máximo 10 por fonte
            title_el = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 15:
                continue

            link = None
            link_el = title_el if title_el.name == 'a' else title_el.find('a')
            if link_el and link_el.get('href'):
                href = link_el['href']
                if href.startswith('/'):
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)
                link = href

            summary = ""
            desc_el = item.find(['p', '.resumo', '.summary', '.excerpt', '.descricao'])
            if desc_el:
                summary = desc_el.get_text(strip=True)[:300]

            date_el = item.find(['time', '.data', '.date', 'span.date'])
            pub_date = None
            if date_el:
                date_text = date_el.get('datetime') or date_el.get_text(strip=True)
                pub_date = parse_date(date_text)

            articles.append({
                "title": title,
                "summary": summary,
                "url": link or base_url,
                "date": pub_date,
                "source": source_name,
            })

        if articles:
            break  # Usa o primeiro selector que funcionar

    return articles


def extract_articles_from_rss(entries, source_name):
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

        pub_date = None
        if entry.get('published_parsed'):
            from time import mktime
            pub_date = datetime.fromtimestamp(
                mktime(entry.published_parsed), tz=BR_TZ
            ).isoformat()

        articles.append({
            "title": title,
            "summary": summary,
            "url": link,
            "date": pub_date,
            "source": source_name,
        })

    return articles


def parse_date(date_str):
    """Tenta parsear uma string de data."""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
        "%d de %B de %Y",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str[:19], fmt)
            return dt.replace(tzinfo=BR_TZ).isoformat()
        except (ValueError, IndexError):
            continue
    return None


def classify_article(article, source_config):
    """Classifica um artigo com base nas keywords."""
    text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()

    # Conta matches por categoria
    scores = {
        'direito-imobiliario': 0,
        'mercado-imobiliario': 0,
        'direito-trabalho': 0,
    }

    for kw in source_config.get('keywords_imob', []):
        if kw.lower() in text:
            scores['direito-imobiliario'] += 1

    for kw in source_config.get('keywords_mercado', []):
        if kw.lower() in text:
            scores['mercado-imobiliario'] += 1

    for kw in source_config.get('keywords_trabalho', []):
        if kw.lower() in text:
            scores['direito-trabalho'] += 1

    # Retorna a categoria com maior score, ou None
    max_score = max(scores.values())
    if max_score == 0:
        return None

    for cat, score in scores.items():
        if score == max_score:
            return cat

    return None


def generate_article_id(title, date):
    """Gera um ID único para o artigo."""
    content = f"{title}_{date}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


# ============================================================
# FUNÇÃO PRINCIPAL DE BUSCA
# ============================================================

def scrape_all_sources():
    """Busca notícias em todas as fontes configuradas."""
    all_articles = []
    today = datetime.now(BR_TZ).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  DOUGLAS VILAR NEWS - Scraper de Notícias")
    print(f"  Data: {today} | Horário: {datetime.now(BR_TZ).strftime('%H:%M')}")
    print(f"{'='*60}\n")

    # Ordena fontes por prioridade
    sorted_sources = sorted(SOURCES.items(), key=lambda x: x[1].get('priority', 99))

    for source_name, config in sorted_sources:
        print(f"\n[{config.get('priority', '?')}] Buscando em: {source_name}...")

        source_articles = []

        # Tenta RSS primeiro
        if config.get('rss'):
            print(f"  -> Via RSS: {config['rss']}")
            entries = fetch_rss(config['rss'])
            if entries:
                source_articles.extend(
                    extract_articles_from_rss(entries, source_name)
                )
                print(f"  -> {len(entries)} entradas RSS encontradas")

        # Busca via HTML
        for url in config.get('urls', []):
            print(f"  -> Via HTML: {url}")
            html = fetch_page(url)
            if html:
                articles = extract_articles_from_html(html, url, source_name)
                source_articles.extend(articles)
                print(f"  -> {len(articles)} artigos extraídos")

        # Classifica e filtra
        classified = 0
        for article in source_articles:
            category = classify_article(article, config)
            if category:
                article['category'] = category
                article['translated'] = config.get('language') == 'en'
                article['source_type'] = config.get('type', 'media')
                article['priority'] = config.get('priority', 99)

                if not article.get('date'):
                    article['date'] = datetime.now(BR_TZ).isoformat()

                article['id'] = generate_article_id(
                    article['title'], today
                )

                all_articles.append(article)
                classified += 1

        print(f"  -> {classified} artigos classificados para publicação")

    return all_articles


def select_daily_articles(articles):
    """Seleciona as 2 melhores matérias do dia."""
    # Ordena por prioridade da fonte
    articles.sort(key=lambda x: x.get('priority', 99))

    selected = []

    # 1 matéria de Direito Imobiliário
    for art in articles:
        if art['category'] == 'direito-imobiliario' and len(selected) < 1:
            selected.append(art)
            break

    # 1 matéria de Mercado Imobiliário
    for art in articles:
        if art['category'] == 'mercado-imobiliario' and art not in selected:
            selected.append(art)
            break

    # Se não achou mercado, tenta direito do trabalho ou outra imobiliária
    if len(selected) < 2:
        for art in articles:
            if art not in selected:
                selected.append(art)
                if len(selected) >= 2:
                    break

    # Formata para publicação
    now = datetime.now(BR_TZ)
    for art in selected:
        art['author'] = 'Douglas Vilar'
        art['sourceUrl'] = art.pop('url', '')
        art['source'] = art.get('source', 'Fonte')
        if not art.get('date') or art['date'] is None:
            art['date'] = now.isoformat()

        # Remove campos internos
        for key in ['source_type', 'priority']:
            art.pop(key, None)

    return selected


def update_news_json(new_articles):
    """Atualiza o arquivo data/news.json com novas matérias."""
    news_file = Path(__file__).parent.parent / 'data' / 'news.json'

    # Carrega existentes
    existing = []
    if news_file.exists():
        try:
            with open(news_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing = []

    # Evita duplicatas por ID
    existing_ids = {a.get('id') for a in existing}
    for art in new_articles:
        if art.get('id') not in existing_ids:
            existing.insert(0, art)

    # Mantém últimos 60 dias (30 artigos por dia = ~60 artigos)
    existing = existing[:120]

    # Salva
    news_file.parent.mkdir(parents=True, exist_ok=True)
    with open(news_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] {len(new_articles)} novas matérias adicionadas")
    print(f"[OK] Total de matérias no arquivo: {len(existing)}")
    print(f"[OK] Arquivo salvo em: {news_file}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("Iniciando busca de notícias...")

    # Busca em todas as fontes
    all_articles = scrape_all_sources()

    if not all_articles:
        print("\n[AVISO] Nenhuma matéria relevante encontrada hoje.")
        print("Usando matéria placeholder...")
        now = datetime.now(BR_TZ)
        all_articles = [{
            "id": now.strftime("%Y-%m-%d") + "-placeholder",
            "title": "Acompanhe as novidades do Direito Imobiliário",
            "summary": "Fique por dentro das principais decisões judiciais e tendências do mercado imobiliário. Notícias atualizadas diariamente às 04h.",
            "category": "direito-imobiliario",
            "source": "Douglas Vilar News",
            "url": "https://douglasvilar.com.br/noticias",
            "date": now.isoformat(),
            "translated": False,
            "priority": 1,
            "source_type": "media"
        }]

    # Seleciona as 2 melhores do dia
    daily = select_daily_articles(all_articles)

    print(f"\nMatérias selecionadas para hoje:")
    for i, art in enumerate(daily, 1):
        print(f"  {i}. [{art['category']}] {art['title'][:80]}...")
        print(f"     Fonte: {art['source']} | Traduzido: {art.get('translated', False)}")

    # Atualiza o JSON
    update_news_json(daily)

    print(f"\n{'='*60}")
    print(f"  Busca finalizada com sucesso!")
    print(f"  Matérias publicadas: {len(daily)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
