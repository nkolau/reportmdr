import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import json
import base64
import re
import html


class AnnualReportHTML:
    """Gerador do Relatório Anual Consolidado de Cibersegurança e MDR."""

    def __init__(self, client_config=None, year=None, generation_date_str=None):
        self.client = client_config or {}
        self.year = int(year) if year else datetime.now().year
        self.generation_date = generation_date_str or datetime.now().strftime('%d/%m/%Y')

        # Cores padrão NetsafeCorp (Dark Mode Exclusivo)
        self.primary = self.client.get('primary_color', '#06090f')
        self.secondary = self.client.get('secondary_color', '#8B0000')
        self.accent = self.client.get('accent_color', '#3b82f6')
        self.company_name = self.client.get('company_name', 'NetsafeCorp')
        self.client_name = self.client.get('client_name', 'Cliente')

        # Logos
        self.company_logo = self.client.get('company_logo_path') or 'data/logos/netsafecorp_logo.png'
        if 'LOGONSC.png' in str(self.company_logo) or not os.path.exists(self.company_logo):
            if os.path.exists('data/logos/netsafecorp_logo.png'):
                self.company_logo = 'data/logos/netsafecorp_logo.png'
            elif os.path.exists('data/logos/netsafecorp_logo_white.png'):
                self.company_logo = 'data/logos/netsafecorp_logo_white.png'

        self.client_logo = self.client.get('logo_path', '')

    def _encode_image(self, path):
        if path and os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    ext = os.path.splitext(path)[1].lstrip('.').lower()
                    mime = 'image/svg+xml' if ext == 'svg' else f'image/{ext}'
                    return f"data:{mime};base64,{base64.b64encode(f.read()).decode('utf-8')}"
            except Exception:
                pass
        return ""

    @staticmethod
    def clean_emojis(text):
        if not text:
            return ""
        emoji_pattern = re.compile(
            "["
            "\U0001F1E0-\U0001F1FF"
            "\U0001F300-\U0001F5FF"
            "\U0001F600-\U0001F64F"
            "\U0001F680-\U0001F6FF"
            "\U0001F700-\U0001F77F"
            "\U0001F780-\U0001F7FF"
            "\U0001F800-\U0001F8FF"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FA6F"
            "\U0001FA70-\U0001FAFF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U00002600-\U000026FF"
            "\U00002300-\U000023FF"
            "]+",
            flags=re.UNICODE
        )
        cleaned = emoji_pattern.sub('', str(text))
        return re.sub(r'\s+', ' ', cleaned).strip()

    def generate(self, annual_data, strategic_notes=None):
        """Gera o HTML consolidado do Relatório Anual."""
        if not annual_data:
            return "<div style='color:white;padding:20px;'>Sem dados anuais para gerar o relatório.</div>"

        html_parts = []
        html_parts.append(self._get_header_html(annual_data))
        html_parts.append(self._get_top_navbar_html())
        html_parts.append(self._get_cover_html(annual_data))
        html_parts.append(self._get_summary_html(annual_data))
        html_parts.append(self._get_annual_kpis_html(annual_data))
        html_parts.append(self._get_timeline_chart_html(annual_data))
        html_parts.append(self._get_monthly_matrix_table_html(annual_data))
        html_parts.append(self._get_recurrent_threats_html(annual_data))
        html_parts.append(self._get_strategic_conclusions_html(annual_data, strategic_notes))
        html_parts.append(self._get_footer_html())
        html_parts.append(self._get_scripts_html())

        return '\n'.join(html_parts)

    def _get_header_html(self, annual_data):
        metadata_json = json.dumps({
            'type': 'annual_report',
            'client': self.client,
            'year': self.year,
            'generation_date': self.generation_date,
            'annual_data': {
                'total_annual_events': annual_data.get('total_annual_events', 0),
                'total_annual_actions': annual_data.get('total_annual_actions', 0),
                'total_annual_violations': annual_data.get('total_annual_violations', 0),
                'avg_monthly_events': annual_data.get('avg_monthly_events', 0),
                'unique_computers_count': annual_data.get('unique_computers_count', 0),
                'num_months_registered': annual_data.get('num_months_registered', 0)
            }
        }, ensure_ascii=False, indent=2)

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Anual Consolidado de Cibersegurança {self.year} - {self.client_name}</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    
    <script id="report-metadata" type="application/json">
{metadata_json}
    </script>

    <style>
        :root {{
            --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            
            --primary-brand: {self.secondary};
            --accent-brand: {self.accent};
            
            --bg-page: #06090f;
            --bg-surface: #0c121e;
            --bg-card: #141d2e;
            --bg-card-hover: #1c273d;
            --bg-callout: rgba(139, 0, 0, 0.08);
            
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-medium: rgba(255, 255, 255, 0.15);
            --border-accent: rgba(220, 38, 38, 0.4);
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --badge-bg: rgba(255, 255, 255, 0.06);
            --shadow-card: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
            
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: var(--font-sans);
            background-color: var(--bg-page);
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}

        .report-wrapper {{
            max-width: 1200px;
            margin: 20px auto 40px;
            background: var(--bg-surface);
            box-shadow: var(--shadow-card);
            border-radius: var(--radius-lg);
            overflow: hidden;
            border: 1px solid var(--border-subtle);
        }}

        /* Navbar */
        .top-navbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 28px;
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(12px);
        }}

        .navbar-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 700;
            font-size: 15px;
            letter-spacing: 0.5px;
        }}

        .brand-icon-wrap {{
            width: 28px;
            height: 28px;
            border-radius: var(--radius-sm);
            background: rgba(220, 38, 38, 0.15);
            color: #ef4444;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .brand-icon-wrap svg {{
            width: 16px;
            height: 16px;
        }}

        .navbar-badge {{
            display: inline-flex;
            align-items: center;
            padding: 3px 9px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .btn-action {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            font-size: 12.5px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid var(--primary-brand);
            background: var(--primary-brand);
            color: white;
            transition: all 0.2s ease;
        }}

        .btn-action svg {{
            width: 15px;
            height: 15px;
        }}

        .btn-action:hover {{
            background: #a11010;
            transform: translateY(-1px);
        }}

        /* Capa */
        .hero-cover {{
            position: relative;
            background: linear-gradient(135deg, #070a10 0%, #111827 50%, #090e18 100%);
            padding: 65px 50px 55px;
            color: white;
            border-bottom: 1px solid var(--border-subtle);
            overflow: hidden;
        }}

        .hero-cover::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(139, 0, 0, 0.12) 50%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }}

        .hero-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 35px;
        }}

        .hero-logos-dual {{
            display: inline-flex;
            align-items: center;
            gap: 22px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 12px 22px;
            border-radius: var(--radius-md);
            backdrop-filter: blur(10px);
        }}

        .hero-logo-img {{
            height: 44px;
            max-width: 190px;
            object-fit: contain;
            filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5));
        }}

        .logo-vertical-divider {{
            width: 1.5px;
            height: 38px;
            background: rgba(255, 255, 255, 0.22);
            border-radius: 1px;
        }}

        .client-name-badge {{
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 0.5px;
            padding: 4px 10px;
            border-radius: var(--radius-sm);
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .hero-title-container {{
            margin-bottom: 35px;
        }}

        .hero-category {{
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2.5px;
            color: #3b82f6;
            margin-bottom: 10px;
        }}

        .hero-title {{
            font-size: 34px;
            font-weight: 800;
            letter-spacing: -0.5px;
            line-height: 1.2;
            color: #ffffff;
            margin-bottom: 10px;
        }}

        .hero-subtitle {{
            font-size: 15.5px;
            font-weight: 400;
            color: #94a3b8;
            max-width: 750px;
        }}

        .hero-meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            padding-top: 25px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .hero-meta-item {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 14px 18px;
            border-radius: var(--radius-md);
            backdrop-filter: blur(8px);
        }}

        .hero-meta-label {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #94a3b8;
            margin-bottom: 4px;
        }}

        .hero-meta-value {{
            font-size: 15px;
            font-weight: 700;
            color: #ffffff;
        }}

        /* Seções */
        .report-section {{
            padding: 45px 50px;
            border-bottom: 1px solid var(--border-subtle);
        }}

        .report-section:last-of-type {{
            border-bottom: none;
        }}

        .section-heading {{
            margin-bottom: 24px;
        }}

        .section-title-wrap {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 6px;
        }}

        .section-indicator {{
            width: 4px;
            height: 22px;
            background: var(--accent-brand);
            border-radius: 2px;
        }}

        .section-title {{
            font-size: 21px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.3px;
        }}

        .section-subtitle {{
            font-size: 13px;
            color: var(--text-muted);
            padding-left: 16px;
        }}

        /* Callout */
        .enunciado-callout {{
            background: var(--bg-callout);
            border-left: 4px solid var(--accent-brand);
            border-radius: 0 var(--radius-md) var(--radius-md) 0;
            padding: 18px 22px;
            margin-bottom: 28px;
            border-top: 1px solid var(--border-subtle);
            border-right: 1px solid var(--border-subtle);
            border-bottom: 1px solid var(--border-subtle);
            position: relative;
        }}

        .enunciado-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11.5px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: #3b82f6;
            margin-bottom: 6px;
        }}

        .callout-icon-wrap svg {{
            width: 16px;
            height: 16px;
        }}

        .enunciado-body {{
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.6;
        }}

        /* KPIs Anuais */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 18px;
        }}

        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 22px 20px;
            position: relative;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .kpi-card-glow {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, var(--accent-brand), transparent);
        }}

        .kpi-top-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }}

        .kpi-icon-wrap {{
            width: 38px;
            height: 38px;
            border-radius: var(--radius-sm);
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .kpi-icon-wrap svg {{
            width: 20px;
            height: 20px;
        }}

        .kpi-badge {{
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 12px;
            background: var(--badge-bg);
            color: var(--text-muted);
        }}

        .kpi-number {{
            font-size: 28px;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -0.5px;
            line-height: 1.1;
            font-family: var(--font-sans);
        }}

        .kpi-title {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 6px;
        }}

        /* Gráfico Timeline */
        .chart-box {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 24px;
            margin-bottom: 25px;
        }}

        /* Tabelas */
        .table-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            overflow: hidden;
            margin-top: 15px;
        }}

        table.cyber-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12.5px;
            text-align: left;
        }}

        table.cyber-table thead th {{
            background: rgba(0, 0, 0, 0.25);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-medium);
        }}

        table.cyber-table tbody td {{
            padding: 11px 16px;
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-primary);
            vertical-align: middle;
        }}

        table.cyber-table tbody tr:hover {{
            background-color: var(--bg-card-hover);
        }}

        table.cyber-table tbody tr:last-child td {{
            border-bottom: none;
        }}

        .td-numeric {{
            text-align: right;
            font-family: var(--font-mono);
            font-weight: 500;
        }}

        .badge-month {{
            font-weight: 700;
            color: #ffffff;
        }}

        .badge-count {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            font-family: var(--font-mono);
            font-weight: 600;
            font-size: 11px;
        }}

        .badge-red {{
            background: rgba(220, 38, 38, 0.15);
            color: #ef4444;
        }}

        /* Recurrent threats grid */
        .recurrent-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }}

        @media (max-width: 960px) {{
            .recurrent-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Rodapé */
        .report-footer {{
            background: var(--bg-surface);
            border-top: 1px solid var(--border-subtle);
            padding: 30px 50px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
        }}

        .footer-left {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .footer-logo-img {{
            height: 26px;
            object-fit: contain;
        }}

        @media print {{
            body {{
                background: #06090f !important;
                color: #f8fafc !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .top-navbar, .btn-action {{
                display: none !important;
            }}
            .hero-cover {{
                page-break-after: always;
            }}
            .report-section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-wrapper">
"""

    def _get_top_navbar_html(self):
        return f"""
        <nav class="top-navbar">
            <div class="navbar-brand">
                <div class="brand-icon-wrap">
                    {self._get_icon_svg('shield')}
                </div>
                <span>{self.company_name}</span>
                <span class="navbar-badge">Relatório Anual {self.year}</span>
            </div>
            <div class="navbar-actions">
                <button class="btn-action" onclick="window.print()">
                    {self._get_icon_svg('printer')}
                    <span>Imprimir / Salvar PDF</span>
                </button>
            </div>
        </nav>
        """

    def _get_cover_html(self, annual_data):
        company_logo_html = ""
        company_logo_src = self._encode_image(self.company_logo)
        if company_logo_src:
            company_logo_html = f'<img src="{company_logo_src}" class="hero-logo-img" alt="{self.company_name}">'
        else:
            company_logo_html = f'<div style="font-size:20px;font-weight:800;letter-spacing:1px;color:#ffffff;">NET<span style="color:#ef4444;">S</span>AFE <span style="font-size:12px;color:#94a3b8;font-weight:500;">CORP</span></div>'

        client_logo_html = ""
        client_logo_src = self._encode_image(self.client_logo) if self.client_logo else ""
        if client_logo_src:
            client_logo_html = f'<img src="{client_logo_src}" class="hero-logo-img" alt="{self.client_name}">'
        else:
            client_logo_html = f'<div class="client-name-badge">{self.client_name}</div>'

        num_months = annual_data.get('num_months_registered', 0)

        return f"""
        <header class="hero-cover">
            <div class="hero-header">
                <div class="hero-logos-dual">
                    <div class="logo-netsafe-wrap">
                        {company_logo_html}
                    </div>
                    <div class="logo-vertical-divider"></div>
                    <div class="logo-client-wrap">
                        {client_logo_html}
                    </div>
                </div>
            </div>

            <div class="hero-title-container">
                <div class="hero-category">Annual Security Briefing - MDR</div>
                <h1 class="hero-title">Relatório Anual Consolidado de Cibersegurança</h1>
                <p class="hero-subtitle">Visão macro de 12 meses: consolidação de telemetria, análise de tendências de ameaça e postura estratégica anual ({self.year}).</p>
            </div>

            <div class="hero-meta-grid">
                <div class="hero-meta-item">
                    <div class="hero-meta-label">Cliente</div>
                    <div class="hero-meta-value">{self.client_name}</div>
                </div>
                <div class="hero-meta-item">
                    <div class="hero-meta-label">Ano de Referência</div>
                    <div class="hero-meta-value">{self.year} ({num_months} meses avaliados)</div>
                </div>
                <div class="hero-meta-item">
                    <div class="hero-meta-label">Data de Emissão</div>
                    <div class="hero-meta-value">{self.generation_date}</div>
                </div>
                <div class="hero-meta-item">
                    <div class="hero-meta-label">Classificação</div>
                    <div class="hero-meta-value">Confidencial (TLP:AMBER)</div>
                </div>
            </div>
        </header>
        """

    def _get_summary_html(self, annual_data):
        total_events = annual_data.get('total_annual_events', 0)
        avg_events = annual_data.get('avg_monthly_events', 0)
        unique_comp = annual_data.get('unique_computers_count', 0)
        num_months = annual_data.get('num_months_registered', 0)

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Sumário Executivo Anual</h2>
                </div>
                <p class="section-subtitle">Consolidação das operações do SOC e governança de ameaças no ano de {self.year}</p>
            </div>

            <div class="enunciado-callout">
                <div class="enunciado-header">
                    <div class="callout-icon-wrap">{self._get_icon_svg('target')}</div>
                    <span>Propósito Estratégico Anual</span>
                </div>
                <div class="enunciado-body">
                    Este documento consolida a evolução de segurança cibernética da organização <strong>{self.client_name}</strong> ao longo do ano de <strong>{self.year}</strong>. Fornece uma visão holística de {num_months} meses monitorados pelo time de <strong>MDR/SOC</strong>, destacando a efetividade das ações de contenção e o comportamento dos vetores de ameaça.
                </div>
            </div>

            <p style="font-size:14px;color:var(--text-secondary);line-height:1.8;max-width:950px;">
                Durante o ano de <strong>{self.year}</strong>, foram processados <strong>{total_events:,}</strong> eventos totais de segurança, representando uma média operacional de <strong>{avg_events:,}</strong> eventos por mês. As operações de resposta a incidentes engajaram <strong>{unique_comp}</strong> computadores distintos no parque de máquinas corporativo.
            </p>
        </section>
        """

    def _get_annual_kpis_html(self, annual_data):
        kpi_defs = [
            ('total_annual_events', 'Total de Eventos no Ano', 'events', 'Acumulado 12M'),
            ('avg_monthly_events', 'Média Mensal de Eventos', 'analytics', 'Média Operacional'),
            ('total_annual_actions', 'Ações de Antivírus no Ano', 'shield', 'Proteção Ativa'),
            ('unique_computers_count', 'Endpoints Atendidos no Ano', 'computer', 'Parque Único'),
            ('total_annual_violations', 'Violações no Ano', 'alert', 'Exploit Prevention'),
            ('total_annual_playbook', 'Eventos Playbook Insights', 'document', 'Trellix Insights')
        ]

        cards_html = ""
        for key, label, icon_type, badge_label in kpi_defs:
            val = annual_data.get(key, 0)
            cards_html += f"""
            <div class="kpi-card">
                <div class="kpi-card-glow"></div>
                <div class="kpi-top-row">
                    <div class="kpi-icon-wrap">
                        {self._get_icon_svg(icon_type)}
                    </div>
                    <span class="kpi-badge">{badge_label}</span>
                </div>
                <div class="kpi-number">{val:,}</div>
                <div class="kpi-title">{label}</div>
            </div>
            """

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Indicadores Anuais Consolidados (KPIs)</h2>
                </div>
                <p class="section-subtitle">Métricas acumuladas e médias operacionais do ano</p>
            </div>
            <div class="kpi-grid">
                {cards_html}
            </div>
        </section>
        """

    def _get_timeline_chart_html(self, annual_data):
        timeline = annual_data.get('timeline', [])
        if not timeline:
            return ""

        # Usar meses com dados para evitar queda artificial a 0 em meses futuros não transcorridos
        active_timeline = [t for t in timeline if t.get('has_data')]
        chart_data = active_timeline if active_timeline else timeline

        months = [t['month_name'][:3] for t in chart_data]
        events = [t['total_events'] for t in chart_data]
        actions = [t['total_actions'] for t in chart_data]
        violations = [t['total_violations'] for t in chart_data]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=months,
            y=events,
            mode='lines+markers',
            name='Eventos Totais',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='#3b82f6'),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.08)'
        ))

        fig.add_trace(go.Scatter(
            x=months,
            y=actions,
            mode='lines+markers',
            name='Ações Antivírus',
            line=dict(color='#10b981', width=2, dash='dot'),
            marker=dict(size=6, color='#10b981')
        ))

        fig.add_trace(go.Scatter(
            x=months,
            y=violations,
            mode='lines+markers',
            name='Violações de Exploit',
            line=dict(color='#ef4444', width=2),
            marker=dict(size=6, color='#ef4444')
        ))

        fig.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=30, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans, sans-serif', size=11, color='#94a3b8'),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.25,
                xanchor='center',
                x=0.5
            ),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.06)',
                showgrid=True
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.06)',
                showgrid=True,
                title='Volume de Ocorrências'
            )
        )

        chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Evolução Temporal Mês a Mês ({self.year})</h2>
                </div>
                <p class="section-subtitle">Tendência de volume de eventos, ações de defesa e violações ao longo do ano</p>
            </div>

            <div class="chart-box">
                {chart_html}
            </div>
        </section>
        """

    def _get_monthly_matrix_table_html(self, annual_data):
        timeline = annual_data.get('timeline', [])
        active_months = [t for t in timeline if t.get('has_data')]

        if not active_months:
            return ""

        rows_html = ""
        for m in active_months:
            month_label = html.escape(f"{m['month_name']}/{self.year}")
            rows_html += f"""
            <tr>
                <td class="badge-month">{month_label}</td>
                <td class="td-numeric"><span class="badge-count">{m['total_events']:,}</span></td>
                <td class="td-numeric"><span class="badge-count">{m['total_actions']:,}</span></td>
                <td class="td-numeric">{m['total_computers']:,}</td>
                <td class="td-numeric">{m['total_users']:,}</td>
                <td class="td-numeric"><span class="badge-count badge-red">{m['total_violations']:,}</span></td>
                <td class="td-numeric">{m['total_playbook_events']:,}</td>
            </tr>
            """

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Matriz Consolidada dos Meses Monitorados</h2>
                </div>
                <p class="section-subtitle">Detalhamento quantitativo mês a mês do ano de {self.year}</p>
            </div>

            <div class="table-card">
                <table class="cyber-table">
                    <thead>
                        <tr>
                            <th>Mês / Período</th>
                            <th style="text-align:right;">Eventos Totais</th>
                            <th style="text-align:right;">Ações Antivírus</th>
                            <th style="text-align:right;">Endpoints</th>
                            <th style="text-align:right;">Usuários</th>
                            <th style="text-align:right;">Violações</th>
                            <th style="text-align:right;">Playbook</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </section>
        """

    def _get_recurrent_threats_html(self, annual_data):
        top_comp = annual_data.get('top_recurrent_computers', [])
        top_rules = annual_data.get('top_recurrent_rules', [])

        comp_rows = ""
        for i, c in enumerate(top_comp[:8], 1):
            c_name = html.escape(self.clean_emojis(str(c['name'])))
            comp_rows += f"""
            <tr>
                <td style="font-family:var(--font-mono);font-weight:600;">{c_name}</td>
                <td class="td-numeric"><span class="badge-count">{c['months_count']} meses</span></td>
                <td class="td-numeric">{c['total_events']:,}</td>
            </tr>
            """

        rules_rows = ""
        for i, r in enumerate(top_rules[:8], 1):
            r_name = html.escape(self.clean_emojis(str(r['name'])))
            rules_rows += f"""
            <tr>
                <td>{r_name}</td>
                <td class="td-numeric"><span class="badge-count badge-red">{r['months_count']} meses</span></td>
                <td class="td-numeric">{r['total_events']:,}</td>
            </tr>
            """

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Ameaças e Endpoints Mais Recorrentes do Ano</h2>
                </div>
                <p class="section-subtitle">Identificação de padrões persistentes observados durante o período de 12 meses</p>
            </div>

            <div class="recurrent-grid">
                <div class="table-card">
                    <div style="padding:14px 18px;font-weight:700;font-size:13px;border-bottom:1px solid var(--border-subtle);color:var(--text-primary);">
                        Top Endpoints Recorrentes no Ano
                    </div>
                    <table class="cyber-table">
                        <thead>
                            <tr>
                                <th>Host / Endpoint</th>
                                <th style="text-align:right;">Meses Ativo</th>
                                <th style="text-align:right;">Total Eventos</th>
                            </tr>
                        </thead>
                        <tbody>
                            {comp_rows if comp_rows else '<tr><td colspan="3" style="text-align:center;">Sem dados registrados.</td></tr>'}
                        </tbody>
                    </table>
                </div>

                <div class="table-card">
                    <div style="padding:14px 18px;font-weight:700;font-size:13px;border-bottom:1px solid var(--border-subtle);color:var(--text-primary);">
                        Top Regras / Técnicas Recorrentes no Ano
                    </div>
                    <table class="cyber-table">
                        <thead>
                            <tr>
                                <th>Nome da Regra</th>
                                <th style="text-align:right;">Meses Ativa</th>
                                <th style="text-align:right;">Total Violações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rules_rows if rules_rows else '<tr><td colspan="3" style="text-align:center;">Sem dados registrados.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
        """

    def _get_strategic_conclusions_html(self, annual_data, strategic_notes=None):
        default_notes = [
            "Manutenção da postura de segurança com estabilidade nos principais limiares de detecção ao longo dos 12 meses.",
            "Recomenda-se realizar varredura de integridade e revisão de privilégios nos endpoints identificados no topo do ranking anual de recorrência.",
            "Avaliar refinamento (tuning) das regras de exploit prevention mais acionadas para reduzir falsos positivos e aumentar a eficácia de bloqueio preventivo.",
            "Continuidade do monitoramento 24x7 pelo time de MDR com foco em inteligência proativa de ameaças para o próximo ciclo anual."
        ]

        notes = strategic_notes if strategic_notes else default_notes

        items = ""
        for note in notes:
            clean_n = html.escape(self.clean_emojis(note))
            items += f"""
            <div style="display:flex;align-items:flex-start;gap:14px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:16px 20px;border-left:4px solid #3b82f6;">
                <div style="color:#3b82f6;margin-top:2px;">{self._get_icon_svg('shield')}</div>
                <div style="font-size:13.5px;color:var(--text-secondary);line-height:1.6;">{clean_n}</div>
            </div>
            """

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Diretrizes Estratégicas e Próximos Passos ({self.year + 1})</h2>
                </div>
                <p class="section-subtitle">Recomendações corporativas baseadas na consolidação anual</p>
            </div>
            <div style="display:flex;flex-direction:column;gap:12px;">
                {items}
            </div>
        </section>
        """

    def _get_footer_html(self):
        company_logo_src = self._encode_image(self.company_logo)
        logo_html = f'<img src="{company_logo_src}" class="footer-logo-img" alt="{self.company_name}">' if company_logo_src else f'<strong>{self.company_name}</strong>'

        return f"""
        <footer class="report-footer">
            <div class="footer-left">
                {logo_html}
                <span>MDR Security Operations Center - Análise Anual</span>
            </div>
            <div>
                Documento Estritamente Confidencial - Uso Exclusivo da Diretoria
            </div>
        </footer>
    </div>
        """

    def _get_scripts_html(self):
        return "</body></html>"

    def _get_icon_svg(self, icon_type):
        icons = {
            'shield': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
            'events': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="8" rx="0.5"/><rect x="12" y="7" width="3" height="11" rx="0.5"/><rect x="17" y="13" width="3" height="5" rx="0.5"/></svg>',
            'computer': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M2 20h20M8 16v4M16 16v4"/></svg>',
            'user': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
            'alert': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 20h20L12 2z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            'document': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
            'target': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
            'analytics': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
            'printer': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>'
        }
        return icons.get(icon_type, icons['shield'])
