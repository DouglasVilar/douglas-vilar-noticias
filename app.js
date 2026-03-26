/* ========================================
   DOUGLAS VILAR NEWS - APP.JS
   Frontend JavaScript para carregamento e filtro de notícias
   ======================================== */

// Configuração
const NEWS_PER_PAGE = 6;
let currentPage = 1;
let currentFilter = 'all';
let allNews = [];

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    loadNews();
    setupFilters();
    setupMobileMenu();
});

// Carregar notícias do JSON
async function loadNews() {
    try {
        const response = await fetch('data/news.json');
        if (!response.ok) throw new Error('Erro ao carregar notícias');
        allNews = await response.json();
        allNews.sort((a, b) => new Date(b.date) - new Date(a.date));
        renderNews();
    } catch (error) {
        console.error('Erro:', error);
        document.getElementById('news-container').innerHTML = `
            <div class="loading-state">
                <p>Nenhuma notícia disponível no momento.</p>
                <p style="font-size:13px;margin-top:8px;">As notícias são atualizadas diariamente às 04h.</p>
            </div>`;
    }
}

// Renderizar notícias
function renderNews() {
    const container = document.getElementById('news-container');
    const filtered = currentFilter === 'all' 
        ? allNews 
        : allNews.filter(n => n.category === currentFilter);
    
    const start = (currentPage - 1) * NEWS_PER_PAGE;
    const end = start + NEWS_PER_PAGE;
    const pageNews = filtered.slice(start, end);

    if (pageNews.length === 0) {
        container.innerHTML = `
            <div class="loading-state">
                <p>Nenhuma notícia encontrada nesta categoria.</p>
            </div>`;
        return;
    }

    container.innerHTML = pageNews.map(news => createNewsCard(news)).join('');
    renderPagination(filtered.length);
}

// Criar card de notícia
function createNewsCard(news) {
    const categoryLabels = {
        'direito-imobiliario': 'Direito Imobiliário',
        'mercado-imobiliario': 'Mercado Imobiliário',
        'direito-trabalho': 'Direito do Trabalho'
    };

    const dateObj = new Date(news.date);
    const formattedDate = dateObj.toLocaleDateString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric'
    });
    const formattedTime = dateObj.toLocaleTimeString('pt-BR', {
        hour: '2-digit', minute: '2-digit'
    });

    const translatedBadge = news.translated 
        ? '<span class="news-translated"><i class="fas fa-language"></i> Traduzido do inglês</span>' 
        : '';

    return `
    <article class="news-card" data-category="${news.category}">
        <div class="news-card-header">
            <div class="news-meta">
                <span class="news-category ${news.category}">${categoryLabels[news.category] || news.category}</span>
                <span class="news-date"><i class="far fa-calendar-alt"></i> ${formattedDate} às ${formattedTime}</span>
                <span class="news-source"><i class="fas fa-external-link-alt"></i> ${news.source}</span>
                ${translatedBadge}
            </div>
            <h3><a href="${news.sourceUrl}" target="_blank" rel="noopener">${news.title}</a></h3>
        </div>
        <div class="news-card-body">
            <p>${news.summary}</p>
        </div>
        <div class="news-card-footer">
            <div class="news-author">
                <span class="author-mini-avatar">DV</span>
                <span>Por <strong>Douglas Vilar</strong></span>
            </div>
            <a href="${news.sourceUrl}" target="_blank" class="news-link" rel="noopener">
                Ler matéria completa <i class="fas fa-arrow-right"></i>
            </a>
        </div>
        <div class="news-original-link">
            <i class="fas fa-link"></i> Fonte original: 
            <a href="${news.sourceUrl}" target="_blank" rel="noopener">${news.source}</a>
        </div>
    </article>`;
}

// Paginação
function renderPagination(totalItems) {
    const totalPages = Math.ceil(totalItems / NEWS_PER_PAGE);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';
    if (currentPage > 1) {
        html += '<button onclick="changePage(' + (currentPage - 1) + ')"><i class="fas fa-chevron-left"></i></button>';
    }
    for (let i = 1; i <= totalPages; i++) {
        html += '<button class="' + (i === currentPage ? 'active' : '') + '" onclick="changePage(' + i + ')">' + i + '</button>';
    }
    if (currentPage < totalPages) {
        html += '<button onclick="changePage(' + (currentPage + 1) + ')"><i class="fas fa-chevron-right"></i></button>';
    }
    pagination.innerHTML = html;
}

function changePage(page) {
    currentPage = page;
    renderNews();
    window.scrollTo({ top: document.querySelector('.news-feed').offsetTop - 100, behavior: 'smooth' });
}

// Filtros
function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            currentPage = 1;
            renderNews();
        });
    });

    document.querySelectorAll('.category-list a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const filter = link.dataset.filter;
            currentFilter = filter;
            currentPage = 1;
            document.querySelectorAll('.filter-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.filter === filter);
            });
            renderNews();
            window.scrollTo({ top: document.querySelector('.news-feed').offsetTop - 100, behavior: 'smooth' });
        });
    });
}

// Menu mobile
function setupMobileMenu() {
    // Auto-setup via onclick
}

function toggleMenu() {
    const menu = document.querySelector('.nav-menu');
    menu.classList.toggle('open');
}
