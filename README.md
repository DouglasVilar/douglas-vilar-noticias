# Douglas Vilar News - Blog de Notícias Jurídicas

## 📰 Sobre o Projeto

Blog automatizado de notícias jurídicas para **douglasvilar.com.br/noticias**, com curadoria focada em:

- **Direito Imobiliário** - Decisões judiciais, jurisprudência e legislação
- **Mercado Imobiliário** - Tendências, dados e análises do setor
- **Direito do Trabalho** - Atualizações trabalhistas e decisões dos tribunais

### 🔄 Automação Diária

O sistema busca notícias **automaticamente às 04h (horário de Brasília)** em mais de 20 fontes:

#### Prioridade 1 - Tribunais Superiores
- STJ (Superior Tribunal de Justiça)
- STF (Supremo Tribunal Federal)
- TST (Tribunal Superior do Trabalho)

#### Prioridade 2 - Tribunais Estaduais
- TJPR (Tribunal de Justiça do Paraná)
- TJSP (Tribunal de Justiça de São Paulo)
- TJRS (Tribunal de Justiça do Rio Grande do Sul)

#### Prioridade 3 - Mídia Nacional
- Gazeta do Povo
- Jovem Pan News
- Revista Oeste
- Conjur, Migalhas, IRIB, Secovi-SP, InfoMoney, Valor Econômico

#### Prioridade 4 - Sites Internacionais (traduzidos)
- Wall Street Journal
- Reuters
- Bloomberg
- Financial Times

### 📋 Publicação

- **2 matérias por dia**: 1 de Direito Imobiliário + 1 de Mercado Imobiliário
- **Assinadas por**: Douglas Vilar - OAB/PR 47.278
- **Com link da fonte original** para cada matéria
- **Data e hora** de publicação

### 🏗 Estrutura do Projeto

\`\`\`
douglas-vilar-noticias/
├── .github/
│   └── workflows/
│       └── daily-news.yml     # GitHub Actions (cron 04h)
├── data/
│   └── news.json              # Notícias (atualizado diariamente)
├── scripts/
│   └── news_scraper.py        # Script de busca e classificação
├── index.html                 # Página principal do blog
├── styles.css                 # Estilos (paleta douglasvilar.com.br)
├── app.js                     # Frontend JavaScript
├── news-loader.js             # Carregador auxiliar
├── requirements.txt           # Dependências Python
└── README.md                  # Este arquivo
\`\`\`

### 🎨 Design

Paleta de cores baseada em **douglasvilar.com.br**:
- Vermelho principal: \`#C41E24\`
- Texto escuro: \`#2D2D2D\`
- Fundo claro: \`#F5F6F8\`
- WhatsApp: \`#25D366\`

### 📞 Contato

**Douglas Vilar** - Advogado & Empresário
- 📱 (41) 98421-6639
- 💬 [WhatsApp](https://api.whatsapp.com/send?phone=5541984216639)
- 🌐 [douglasvilar.com.br](https://douglasvilar.com.br)
- OAB/PR 47.278

### 🚀 Como usar

1. Faça o deploy dos arquivos estáticos (index.html, styles.css, app.js) no seu servidor
2. Configure a pasta \`data/\` acessível publicamente
3. O GitHub Actions atualiza o \`news.json\` diariamente às 04h
4. A página carrega as notícias automaticamente do JSON

### ⚙ Execução Manual

Para executar o scraper manualmente:
1. Vá em **Actions** > **Douglas Vilar News - Busca Diária**
2. Clique em **Run workflow**

---

© 2025 Douglas Vilar - Todos os direitos reservados.
