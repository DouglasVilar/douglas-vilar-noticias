/* ========================================
   DOUGLAS VILAR NEWS - NEWS LOADER
   Carregador auxiliar de notícias com cache e fallback
   ======================================== */

const NewsLoader = {
    cacheKey: 'dv_news_cache',
    cacheDuration: 30 * 60 * 1000, // 30 minutos

    // Busca notícias com cache
    async fetchNews() {
        // Tenta cache primeiro
        const cached = this.getFromCache();
        if (cached) {
            console.log('[NewsLoader] Usando cache local');
            return cached;
        }

        // Busca do servidor
        try {
            const response = await fetch('data/news.json?t=' + Date.now());
            if (!response.ok) throw new Error('HTTP ' + response.status);
            const data = await response.json();
            this.setCache(data);
            return data;
        } catch (error) {
            console.warn('[NewsLoader] Erro ao carregar:', error.message);
            return this.getFallbackNews();
        }
    },

    // Cache local
    getFromCache() {
        try {
            const raw = localStorage.getItem(this.cacheKey);
            if (!raw) return null;
            const { data, timestamp } = JSON.parse(raw);
            if (Date.now() - timestamp > this.cacheDuration) return null;
            return data;
        } catch {
            return null;
        }
    },

    setCache(data) {
        try {
            localStorage.setItem(this.cacheKey, JSON.stringify({
                data,
                timestamp: Date.now()
            }));
        } catch { /* Storage full */ }
    },

    // Notícias de fallback
    getFallbackNews() {
        return [{
            id: 'fallback-1',
            title: 'Acompanhe as novidades do Direito Imobiliário e Mercado Imobiliário',
            summary: 'Fique por dentro das principais decisões judiciais, tendências do mercado e análises especializadas. As notícias são atualizadas diariamente às 04h da manhã, com curadoria de mais de 20 fontes jurídicas e econômicas.',
            category: 'direito-imobiliario',
            source: 'Douglas Vilar News',
            sourceUrl: 'https://douglasvilar.com.br/noticias',
            date: new Date().toISOString(),
            author: 'Douglas Vilar',
            translated: false
        }];
    },

    // Formata data para exibição
    formatDate(dateStr) {
        const d = new Date(dateStr);
        return d.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric'
        });
    },

    // Formata hora
    formatTime(dateStr) {
        const d = new Date(dateStr);
        return d.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
};

// Exporta
window.NewsLoader = NewsLoader;
