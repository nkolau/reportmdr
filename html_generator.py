import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import os
import base64


class CyberReportHTML:
    def __init__(self, client_config, period_str=None):
        self.client = client_config
        self.period = period_str

        # Cores NetsafeCorp
        self.primary = client_config.get('primary_color', '#1a1a1a')  # Preto
        self.secondary = client_config.get('secondary_color', '#8B0000')  # Vinho
        self.accent = client_config.get('accent_color', '#808080')  # Cinza

        # Logo da empresa
        self.company_logo = client_config.get('company_logo_path', '')
        self.client_logo = client_config.get('logo_path', '')

    def get_last_month(self):
        """Retorna o mês passado no formato 'Março/2025'."""
        today = date.today()
        last_month = today - relativedelta(months=1)
        months_pt = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return f"{months_pt[last_month.month - 1]}/{last_month.year}"

    def generate(self, data, investigations=None):
        """Gera o relatório completo em HTML."""
        if investigations is None:
            investigations = {}

        # Determinar período
        if not self.period:
            self.period = self.get_last_month()

        html_parts = []

        html_parts.append(self._get_header_html())
        html_parts.append(self._get_cover_html())
        html_parts.append(self._get_summary_html(data))
        html_parts.append(self._get_kpis_html(data))

        # Gráficos e tabelas
        charts = data.get('charts', {})
        tables = data.get('tables', {})

        for chart_name, chart_info in charts.items():
            html_parts.append(self._get_chart_table_combo_html(chart_info, tables))

        # Investigação
        if 'computers' in tables:
            html_parts.append(self._get_investigation_html(
                tables['computers'], investigations
            ))

        # Recomendações
        if data.get('recommendations'):
            html_parts.append(self._get_recommendations_html(data['recommendations']))

        # Fechamento
        html_parts.append(self._get_footer_html())

        return '\n'.join(html_parts)

    def _get_header_html(self):
        """CSS refinado com identidade NetsafeCorp."""
        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório de Cibersegurança</title>
            <style>
                :root {{
                    --primary: {self.primary};
                    --secondary: {self.secondary};
                    --accent: {self.accent};
                    --primary-light: {self._lighten_color(self.primary, 30)};
                    --secondary-light: {self._lighten_color(self.secondary, 30)};
                    --bg-page: #f5f5f5;
                    --bg-white: #ffffff;
                    --text-primary: #1a1a1a;
                    --text-secondary: #4a4a4a;
                    --text-muted: #757575;
                    --border-light: #e0e0e0;
                    --border-medium: #bdbdbd;
                    --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
                    --shadow-md: 0 4px 12px rgba(0,0,0,0.12);
                    --radius-lg: 12px;
                    --radius-md: 8px;
                    --radius-sm: 4px;

                }}

                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: 'Inter', 'Segoe UI', 'DejaVu Sans', -apple-system, sans-serif;
                    background: var(--bg-page);
                    color: var(--text-primary);
                    line-height: 1.6;
                    -webkit-font-smoothing: antialiased;
                }}

                .report-container {{
                    max-width: 1100px;
                    margin: 0 auto;
                    background: var(--bg-white);
                    box-shadow: var(--shadow-md);
                }}

                /* ===== CAPA ===== */
                .cover {{
                    background: linear-gradient(135deg, var(--primary) 0%, #2d2d2d 100%);
                    color: white;
                    padding: 80px 60px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                    min-height: 600px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }}

                .cover-accent {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 8px;
                    height: 100%;
                    background: var(--secondary);
                }}

                .cover-pattern {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-image:
                        radial-gradient(circle at 80% 20%, rgba(139,0,0,0.15) 0%, transparent 50%),
                        radial-gradient(circle at 20% 80%, rgba(128,128,128,0.1) 0%, transparent 50%);
                    pointer-events: none;
                }}

                .cover-logo {{
                    width: 120px;
                    height: 120px;
                    margin-bottom: 40px;
                    position: relative;
                    z-index: 1;
                }}

                .cover-logo img {{
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }}

                .cover-title {{
                    font-size: 32px;
                    font-weight: 300;
                    letter-spacing: 4px;
                    text-transform: uppercase;
                    position: relative;
                    z-index: 1;
                }}

                .cover-subtitle {{
                    font-size: 15px;
                    font-weight: 300;
                    opacity: 0.85;
                    margin-top: 10px;
                    letter-spacing: 2px;
                    position: relative;
                    z-index: 1;
                }}

                .cover-divider {{
                    width: 60px;
                    height: 3px;
                    background: var(--secondary);
                    margin: 25px auto;
                    position: relative;
                    z-index: 1;
                }}

                .cover-info {{
                    margin-top: 30px;
                    position: relative;
                    z-index: 1;
                    min-width: 350px;
                }}

                .cover-info-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 12px 0;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                    font-size: 13px;
                }}

                .cover-info-row:last-child {{
                    border-bottom: none;
                }}

                .cover-info-label {{
                    font-weight: 500;
                    opacity: 0.7;
                    letter-spacing: 1px;
                    font-size: 11px;
                    text-transform: uppercase;
                }}

                .cover-info-value {{
                    font-weight: 500;
                }}

                /* ===== SEÇÕES ===== */
                .section {{
                    padding: 50px 45px;
                    border-bottom: 1px solid var(--border-light);
                }}

                .section:last-child {{
                    border-bottom: none;
                }}

                .section-header {{
                    margin-bottom: 30px;
                }}

                .section-title {{
                    font-size: 22px;
                    font-weight: 600;
                    color: var(--text-primary);
                    letter-spacing: -0.5px;
                    border-left: 4px solid var(--secondary);
                    padding-left: 15px;
                }}

                .section-subtitle {{
                    color: var(--text-muted);
                    font-size: 13px;
                    margin-top: 6px;
                    padding-left: 19px;
                }}

                /* ===== KPIs ===== */
                .kpi-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                    margin-top: 20px;
                }}

                .kpi-card {{
                    background: var(--bg-white);
                    border: 1px solid var(--border-light);
                    border-radius: var(--radius-md);
                    padding: 24px 20px;
                    text-align: center;
                    transition: all 0.2s ease;
                    position: relative;
                }}

                .kpi-card:hover {{
                    border-color: var(--secondary);
                    box-shadow: var(--shadow-md);
                }}

                .kpi-card::after {{
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 40px;
                    height: 3px;
                    background: var(--secondary);
                    border-radius: 2px;
                }}

                .kpi-icon {{
                    width: 36px;
                    height: 36px;
                    margin: 0 auto 14px;
                    color: var(--secondary);
                }}

                .kpi-value {{
                    font-size: 30px;
                    font-weight: 600;
                    color: var(--text-primary);
                    letter-spacing: -1px;
                    line-height: 1.2;
                }}

                .kpi-label {{
                    font-size: 11px;
                    color: var(--text-muted);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    font-weight: 500;
                    margin-top: 6px;
                }}

                /* ===== GRÁFICO DE PIZZA ===== */
                .pie-chart-container {
                    background: var(--bg-page);
                    border-radius: var(--radius-sm);
                    padding: 20px;
                    margin-bottom: 25px;
                }

                .chart-box-title {
                    font-size: 13px;
                    font-weight: 600;
                    color: var(--text-secondary);
                    margin-bottom: 10px;
                    text-align: center;
                }

                /* ===== TABELAS ===== */
                .table-wrapper {{
                    overflow-x: auto;
                    margin-top: 15px;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }}

                thead th {{
                    background: var(--primary);
                    color: white;
                    font-weight: 500;
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    padding: 12px 14px;
                    text-align: left;
                    border-bottom: 2px solid var(--secondary);
                }}

                tbody td {{
                    padding: 10px 14px;
                    border-bottom: 1px solid var(--border-light);
                    color: var(--text-primary);
                }}

                tbody tr:hover {{
                    background: #fafafa;
                }}

                tbody tr:last-child td {{
                    border-bottom: none;
                }}

                .table-numeric {{
                    text-align: right;
                    font-variant-numeric: tabular-nums;
                }}

                /* ===== INVESTIGAÇÃO ===== */
                .investigation-list {{
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    margin-top: 20px;
                }}

                .investigation-item {{
                    background: var(--bg-white);
                    border: 1px solid var(--border-light);
                    border-radius: var(--radius-sm);
                    padding: 16px 18px;
                    display: flex;
                    align-items: flex-start;
                    gap: 14px;
                }}

                .investigation-status {{
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    margin-top: 5px;
                    flex-shrink: 0;
                }}

                .status-top {{
                    background: #38a169;
                }}

                .status-medium {{
                    background: #f59e0b;
                }}

                .status-low {{
                    background: #1a1a1a;
                }}

                .status-none {{
                    background: #a0aec0;
                }}

                .investigation-content {{
                    flex: 1;
                }}

                .investigation-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 4px;
                }}

                .investigation-name {{
                    font-weight: 600;
                    font-size: 13px;
                }}

                .investigation-count {{
                    font-size: 11px;
                    color: var(--text-muted);
                    font-variant-numeric: tabular-nums;
                }}

                .investigation-text {{
                    font-size: 12px;
                    color: var(--text-secondary);
                    line-height: 1.5;
                }}

                /* ===== RECOMENDAÇÕES ===== */
                .recommendations-list {{
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    margin-top: 20px;
                }}

                .recommendation-item {{
                    display: flex;
                    align-items: flex-start;
                    gap: 12px;
                    padding: 14px 16px;
                    border-radius: var(--radius-sm);
                    font-size: 13px;
                    line-height: 1.5;
                }}

                .recommendation-item.priority-high {{
                    background: #fef2f2;
                    border-left: 3px solid var(--secondary);
                }}

                .recommendation-item.priority-medium {{
                    background: #fffbeb;
                    border-left: 3px solid #f59e0b;
                }}

                .recommendation-item.priority-info {{
                    background: #f5f5f5;
                    border-left: 3px solid var(--accent);
                }}

                .recommendation-indicator {{
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    margin-top: 6px;
                    flex-shrink: 0;
                }}

                .priority-high .recommendation-indicator {{
                    background: var(--secondary);
                }}

                .priority-medium .recommendation-indicator {{
                    background: #f59e0b;
                }}

                .priority-info .recommendation-indicator {{
                    background: var(--accent);
                }}

                /* ===== RODAPÉ ===== */
                .report-footer {{
                    background: var(--primary);
                    color: rgba(255,255,255,0.8);
                    padding: 25px 45px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }}

                .footer-logo {{
                    height: 30px;
                }}

                .footer-logo img {{
                    height: 100%;
                }}

                .footer-text {{
                    font-size: 11px;
                    letter-spacing: 0.5px;
                }}

                @media (max-width: 768px) {{
                    .section {{
                        padding: 30px 20px;
                    }}
                    .cover {{
                        padding: 60px 30px;
                        min-height: 400px;
                    }}
                    .cover-title {{
                        font-size: 24px;
                        letter-spacing: 3px;
                    }}
                    .charts-row {{
                        grid-template-columns: 1fr;
                    }}
                    .report-footer {{
                        flex-direction: column;
                        gap: 10px;
                    }}
                }}

                @media print {{
                    body {{
                        background: white;
                    }}
                    .report-container {{
                        box-shadow: none;
                    }}
                    .section {{
                        page-break-inside: avoid;
                    }}
                    .cover {{
                        min-height: 100vh;
                    }}
                    /* ===== GRÁFICO DE PIZZA ===== */
                    .pie-chart-container {
                        background: var(--bg-page);
                        border-radius: var(--radius-sm);
                        padding: 20px;
                        margin-bottom: 25px;
                    }

                    .chart-box-title {
                        font-size: 13px;
                        font-weight: 600;
                        color: var(--text-secondary);
                        margin-bottom: 10px;
                        text-align: center;
                    }
                }}
            </style>
        </head>
        <body>
            <div class="report-container">
        """

    def _lighten_color(self, hex_color, amount):
        """Clareia uma cor hexadecimal."""
        hex_color = hex_color.lstrip('#')
        r = min(255, int(hex_color[0:2], 16) + amount)
        g = min(255, int(hex_color[2:4], 16) + amount)
        b = min(255, int(hex_color[4:6], 16) + amount)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _get_icon_svg(self, icon_type):
        """Ícones SVG minimalistas."""
        icons = {
            'shield': '''
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
            ''',
            'events': '''
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M3 3v18h18"/>
                    <rect x="7" y="10" width="3" height="8" rx="0.5"/>
                    <rect x="12" y="7" width="3" height="11" rx="0.5"/>
                    <rect x="17" y="13" width="3" height="5" rx="0.5"/>
                </svg>
            ''',
            'computer': '''
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="4" y="4" width="16" height="12" rx="1"/>
                    <path d="M8 20h8M12 16v4"/>
                </svg>
            ''',
            'user': '''
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="8" r="4"/>
                    <path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>
                </svg>
            ''',
            'alert': '''
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M12 3l10 18H2L12 3z"/>
                    <path d="M12 10v4"/>
                </svg>
            ''',
            'document': '''
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 3H7a1 1 0 00-1 1v16a1 1 0 001 1h10a1 1 0 001-1V8l-4-5z"/>
                    <path d="M14 3v5h5"/>
                </svg>
            ''',
        }
        return icons.get(icon_type, icons['document'])

    def _get_cover_html(self):
        """Capa com logo da NetsafeCorp."""
        # Logo da empresa
        company_logo_html = ""
        if self.company_logo and os.path.exists(self.company_logo):
            company_logo_html = f'<img src="data:image/png;base64,{self._encode_image(self.company_logo)}" alt="Logo">'
        else:
            company_logo_html = '<span style="font-size:50px;font-weight:300;">N</span>'

        return f"""
        <div class="cover">
            <div class="cover-accent"></div>
            <div class="cover-pattern"></div>
            <div class="cover-logo">
                {company_logo_html}
            </div>
            <div class="cover-title">Relatório de Cibersegurança</div>
            <div class="cover-subtitle">Análise de Ameaças e Detecções</div>
            <div class="cover-divider"></div>
            <div class="cover-info">
                <div class="cover-info-row">
                    <span class="cover-info-label">Cliente</span>
                    <span class="cover-info-value">{self.client.get('client_name', 'N/D')}</span>
                </div>
                <div class="cover-info-row">
                    <span class="cover-info-label">Período</span>
                    <span class="cover-info-value">{self.period}</span>
                </div>
                <div class="cover-info-row">
                    <span class="cover-info-label">Data</span>
                    <span class="cover-info-value">{datetime.now().strftime('%d/%m/%Y')}</span>
                </div>
                <div class="cover-info-row">
                    <span class="cover-info-label">Serviço</span>
                    <span class="cover-info-value">MDR - Monitoramento e Detecção</span>
                </div>
            </div>
        </div>
        """

    def _encode_image(self, path):
        """Converte imagem para base64."""
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _get_summary_html(self, data):
        """Sumário executivo com padrão NetsafeCorp."""
        total_events = data.get('total_events', 0)
        total_computers = data.get('total_computers', 0)
        total_users = data.get('total_users', 0)

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-title">Sumário Executivo</div>
                <div class="section-subtitle">Visão geral do período analisado</div>
            </div>
            <p style="font-size:14px;line-height:1.8;color:var(--text-secondary);max-width:850px;">
                Este relatório elaborado pelo time técnico de MDR se propõe a ampliar as informações
                coletadas a nível de segurança no ambiente <strong>{self.client.get('client_name', '')}</strong>,
                garantindo uma visão mais aprofundada de regras, incidentes e atividades possivelmente maliciosas.
            </p>
            <p style="font-size:14px;line-height:1.8;color:var(--text-secondary);max-width:850px;margin-top:15px;">
                Durante o mês de <strong>{self.period.split('/')[0]}</strong> houve
                <strong>{total_events:,}</strong> eventos totais, em
                <strong>{total_computers}</strong> computadores, e
                <strong>{total_users}</strong> usuários.
            </p>
        </div>
        """

    def _get_kpis_html(self, data):
        """KPIs com ícones SVG."""
        kpi_items = []

        metrics = [
            ('total_events', 'Total de Eventos', 'events'),
            ('total_actions', 'Ações do Antivírus', 'shield'),
            ('total_computers', 'Computadores', 'computer'),
            ('total_users', 'Usuários', 'user'),
            ('total_violations', 'Violações', 'alert'),
            ('total_playbook_events', 'Eventos Playbook', 'document'),
        ]

        for key, label, icon in metrics:
            if key in data:
                kpi_items.append((label, data[key], icon))

        kpi_cards = ""
        for label, value, icon in kpi_items:
            kpi_cards += f"""
            <div class="kpi-card">
                <div class="kpi-icon">{self._get_icon_svg(icon)}</div>
                <div class="kpi-value">{value:,}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-title">Indicadores Principais</div>
                <div class="section-subtitle">Métricas consolidadas do período</div>
            </div>
            <div class="kpi-grid">
                {kpi_cards}
            </div>
        </div>
        """

    def _get_chart_table_combo_html(self, chart_info, tables):
    """Combina gráfico de pizza e tabela."""
    df = chart_info.get('data')
    label_col = chart_info.get('label_col')
    value_col = chart_info.get('value_col')
    title = chart_info.get('title', '')

    if df is None or df.empty:
        return ""

    # Limitar para top 6 para melhor visibilidade
    df_pie = df.nlargest(6, value_col)

    # Gráfico de pizza
    pie_fig = px.pie(
        df_pie,
        names=label_col,
        values=value_col,
        hole=0.55,
        color_discrete_sequence=[self.secondary, self.accent, '#4a4a4a', '#8b0000', '#666666', '#999999']
    )

    pie_fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', size=10, color='#4a4a4a'),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.15,
            xanchor='center',
            x=0.5,
            font=dict(size=9)
        )
    )

    pie_fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=9, color='white'),
        marker=dict(line=dict(color='white', width=1))
    )

    pie_html = pie_fig.to_html(full_html=False, include_plotlyjs='cdn')

    # Tabela correspondente
    table_html = ""
    for table_name, table_df in tables.items():
        if table_df is not None and not table_df.empty:
            if list(table_df.columns) == list(df.columns):
                table_html = self._generate_table_html(table_df)
                break

    # Título em português
    title_pt = self._translate_title(title)

    return f"""
    <div class="section">
        <div class="section-header">
            <div class="section-title">{title_pt}</div>
            <div class="section-subtitle">Distribuição percentual e dados detalhados</div>
        </div>

        <div class="pie-chart-container">
            <div class="chart-box-title">Distribuição Percentual</div>
            {pie_html}
        </div>

        <div class="table-wrapper">
            {table_html}
        </div>
    </div>
    """

    def _translate_title(self, title):
        """Traduz títulos para português."""
        translations = {
            'Ações Tomadas pelo Antivírus': 'Ações Tomadas pelo Antivírus',
            'Top 10 Usuários com Mais Detecções': 'Usuários com Mais Detecções',
            'Top 10 Computadores com Mais Detecções': 'Computadores com Mais Detecções',
            'Regras do Playbook Trellix': 'Regras do Playbook',
            'Top 10 Regras de Prevenção Violadas': 'Regras de Prevenção Violadas',
        }
        return translations.get(title, title)

    def _generate_table_html(self, df):
        """Gera HTML de tabela com cabeçalhos em português."""
        if df is None or df.empty:
            return ""

        # Mapear colunas para português
        col_translations = {
            'action_taken': 'Ação Tomada',
            'user_name': 'Usuário',
            'computer_name': 'Computador',
            'rule_name': 'Regra',
            'event_count': 'Eventos',
            'violation_count': 'Violações',
            'detection_count': 'Detecções',
        }

        html = '<table>\n<thead>\n<tr>\n'

        for col in df.columns:
            display_name = col_translations.get(col, col.replace('_', ' ').title())
            html += f'<th>{display_name}</th>\n'

        html += '</tr>\n</thead>\n<tbody>\n'

        for _, row in df.iterrows():
            html += '<tr>\n'
            for i, col in enumerate(df.columns):
                value = row[col]
                if isinstance(value, (int, float)):
                    if value == int(value):
                        display = f'{int(value):,}'
                    else:
                        display = f'{value:,.1f}'
                    css_class = 'table-numeric'
                else:
                    display = str(value)
                    css_class = ''

                html += f'<td class="{css_class}">{display}</td>\n'
            html += '</tr>\n'

        html += '</tbody>\n</table>'

        return html

    def _get_investigation_html(self, df_computers, investigations):
        """Investigação com ranking por cores."""
        if df_computers is None or df_computers.empty:
            return ""

        items = ""

        # Ordenar por eventos
        df_sorted = df_computers.sort_values(by='event_count', ascending=False)

        for idx, (_, row) in enumerate(df_sorted.iterrows(), 1):
            computer = row['computer_name']
            events = row['event_count']
            investigation = investigations.get(computer, '')

            # Determinar status
            if investigation:
                if idx <= 2:
                    status_class = 'status-top'
                elif idx <= 7:
                    status_class = 'status-medium'
                else:
                    status_class = 'status-low'
                investigation_text = investigation
            else:
                status_class = 'status-none'
                investigation_text = 'Sem investigação registrada'

            items += f"""
            <div class="investigation-item">
                <div class="investigation-status {status_class}"></div>
                <div class="investigation-content">
                    <div class="investigation-header">
                        <span class="investigation-name">{computer}</span>
                        <span class="investigation-count">{events:,} eventos</span>
                    </div>
                    <div class="investigation-text">{investigation_text}</div>
                </div>
            </div>
            """

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-title">Investigação de Computadores</div>
                <div class="section-subtitle">Análise detalhada dos equipamentos afetados</div>
            </div>
            <div class="investigation-list">
                {items}
            </div>
        </div>
        """

    def _get_recommendations_html(self, recommendations):
        """Recomendações com prioridade visual."""
        items = ""

        for rec in recommendations:
            if rec.startswith("🔴"):
                priority = 'priority-high'
                rec_text = rec.replace("🔴", "").strip()
            elif rec.startswith("🟡"):
                priority = 'priority-medium'
                rec_text = rec.replace("🟡", "").strip()
            else:
                priority = 'priority-info'
                for emoji in ['💻', '👤', '🔧', '📌']:
                    rec_text = rec.replace(emoji, '').strip()

            items += f"""
            <div class="recommendation-item {priority}">
                <div class="recommendation-indicator"></div>
                <div>{rec_text}</div>
            </div>
            """

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-title">Recomendações</div>
                <div class="section-subtitle">Ações sugeridas baseadas na análise</div>
            </div>
            <div class="recommendations-list">
                {items}
            </div>
        </div>
        """

    def _get_footer_html(self):
        """Rodapé com logo da NetsafeCorp."""
        footer_logo = ""
        if self.company_logo and os.path.exists(self.company_logo):
            footer_logo = f'<img src="data:image/png;base64,{self._encode_image(self.company_logo)}" alt="NetsafeCorp">'

        return f"""
        <footer class="report-footer">
            <div class="footer-logo">{footer_logo}</div>
            <div class="footer-text">Documento Confidencial - Uso exclusivo do cliente autorizado</div>
        </footer>
        """
