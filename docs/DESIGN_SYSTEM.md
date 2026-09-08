# 🎨 Design System & Diretrizes do Agente Designer (MDR Reports)

Este documento documenta os padrões de UI/UX, paleta de cores, tipografia e componentes visuais utilizados na geração dos relatórios executivos de cibersegurança do projeto **`reportmdr`**.

---

## 🎭 1. Agente Especialista: `report_designer`

O agente **`report_designer`** é responsável por:
* Refinar a experiência visual dos relatórios em HTML e componentes Streamlit;
* Criar e padronizar paletas de cores (*Cyber Dark* e *Executive Light*);
* Desenvolver componentes visuais (Cards de KPI, Caixas de Enunciado, Gráficos Plotly, Tabelas Interativas e Cards de Investigação);
* Otimizar folhas de estilo de impressão (`@media print`) para geração de PDFs impecáveis.

---

## 🎨 2. Paleta de Cores e Tokens Visuais

| Token | Cor Hex | Uso / Aplicação |
| :--- | :--- | :--- |
| `--primary-brand` | `#8B0000` / `#DC2626` | Vinho / Cyber Red: Alertas críticos, capa e botões principais |
| `--accent-brand` | `#3B82F6` / `#06B6D4` | Azul / Ciano Tech: Métricas de rede, links e gráficos |
| `--status-success` | `#10B981` | Verde Esmeralda: Ações tomadas com sucesso, bloqueios e quarentenas limpas |
| `--status-warning` | `#F59E0B` | Âmbar: Alertas médios e investigações em andamento |
| `--bg-dark-page` | `#0B0F19` | Fundo principal da página no modo escuro |
| `--bg-dark-surface` | `#111827` | Superfície de containers e painéis no modo escuro |
| `--bg-dark-card` | `#1A2234` | Fundo de cards, tabelas e caixas no modo escuro |
| `--bg-light-page` | `#F1F5F9` | Fundo no modo claro |
| `--bg-light-surface`| `#FFFFFF` | Superfície no modo claro |

---

## 🔤 3. Tipografia

* **Fonte Principal (Textos e Títulos):** `'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif`
* **Fonte Monoespaçada (Hashes, IPs, Nomes de Hosts, Contagens):** `'JetBrains Mono', monospace`

---

## 🧩 4. Componentes Chave

### 💡 Caixas de Enunciado (*Executive Callouts*)
Cards com borda lateral esquerda destacada em vermelho/vinho, fundo translúcido e cabeçalho `💡 Contexto & Análise Técnica` posicionados estrategicamente antes de cada tabela/gráfico.

### 📊 Gráficos Plotly (Donut & Barras)
* Fundo transparente (`paper_bgcolor='rgba(0,0,0,0)'`);
* Paleta alinhada com as cores da marca e severidade;
* Legendas centralizadas e tooltips com contraste escuro.

### 📋 Tabelas Interativas
* Campo de busca em tempo real com filtro instantâneo via JavaScript;
* Cabeçalhos clicáveis para ordenação alfanumérica e numérica;
* Badges estilizados para exibição de volumes e eventos.

### 🖨️ Estilos de Impressão (`@media print`)
* Ocultação de elementos interativos (botões, barra de busca);
* Quebra de página forçada após a capa executiva;
* `page-break-inside: avoid` em seções e tabelas para evitar cortes indesejados.
