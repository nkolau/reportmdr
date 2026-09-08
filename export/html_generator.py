import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os
import json
import base64
import re
import html


class CyberReportHTML:
    def __init__(self, client_config=None, period_str=None, generation_date_str=None):
        self.client = client_config or {}
        self.period = period_str or self.get_last_month()
        self.generation_date = generation_date_str or datetime.now().strftime('%d/%m/%Y')

        # Cores padrão NetsafeCorp (Dark Mode Exclusivo)
        self.primary = self.client.get('primary_color', '#080c14')      # Slate Dark
        self.secondary = self.client.get('secondary_color', '#8B0000')  # Vinho / Cyber Red
        self.accent = self.client.get('accent_color', '#3b82f6')        # Azul Ciano Tech
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

    def get_last_month(self):
        """Retorna o mês anterior no formato 'Mês/Ano' (ex: 'Agosto/2026')."""
        today = date.today()
        last_month = today - relativedelta(months=1)
        months_pt = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return f"{months_pt[last_month.month - 1]}/{last_month.year}"

    @staticmethod
    def extract_metadata(html_content):
        """Extrai os metadados JSON embutidos em um relatório HTML exportado."""
        if not html_content:
            return None
        match = re.search(r'<script\s+id=["\']report-metadata["\']\s+type=["\']application/json["\']>(.*?)</script>', html_content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except Exception:
                pass
        return None

    @staticmethod
    def clean_emojis(text):
        """Remove qualquer caractere de emoji ou pictograma Unicode do texto."""
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

    def _serialize_data_for_metadata(self, data, investigations=None):
        """Prepara os dados do relatório para serialização segura em JSON."""
        meta_data = {
            'client': self.client,
            'period': self.period,
            'generation_date': self.generation_date,
            'total_events': data.get('total_events', 0),
            'total_actions': data.get('total_actions', 0),
            'total_computers': data.get('total_computers', 0),
            'total_users': data.get('total_users', 0),
            'total_violations': data.get('total_violations', 0),
            'total_playbook_events': data.get('total_playbook_events', 0),
            'enunciados': {k: self.clean_emojis(v) for k, v in data.get('enunciados', {}).items()},
            'investigations': {k: self.clean_emojis(v) for k, v in (investigations or {}).items()},
            'recommendations': [self.clean_emojis(r) for r in data.get('recommendations', [])],
            'tables': {},
            'charts_meta': {}
        }

        for name, df in data.get('tables', {}).items():
            if df is not None and isinstance(df, pd.DataFrame):
                meta_data['tables'][name] = df.to_dict(orient='records')

        for name, chart_info in data.get('charts', {}).items():
            if chart_info:
                df = chart_info.get('data')
                meta_data['charts_meta'][name] = {
                    'title': self.clean_emojis(chart_info.get('title', '')),
                    'enunciado': self.clean_emojis(chart_info.get('enunciado', '')),
                    'label_col': chart_info.get('label_col', ''),
                    'value_col': chart_info.get('value_col', ''),
                    'records': df.to_dict(orient='records') if (df is not None and isinstance(df, pd.DataFrame)) else []
                }

        return meta_data

    def generate(self, data, investigations=None, mom_deltas=None, recent_history=None):
        """Gera o relatório executivo completo em HTML."""
        if investigations is None:
            investigations = {}

        if not self.period:
            self.period = self.get_last_month()

        metadata_dict = self._serialize_data_for_metadata(data, investigations)
        metadata_json = json.dumps(metadata_dict, ensure_ascii=False, indent=2)

        html_parts = []
        html_parts.append(self._get_header_html(metadata_json))
        html_parts.append(self._get_top_navbar_html())
        html_parts.append(self._get_cover_html())
        html_parts.append(self._get_summary_html(data))
        html_parts.append(self._get_kpis_html(data, mom_deltas))

        # Se houver histórico recente disponível (>= 2 meses), renderizar gráfico de tendência
        if recent_history and len(recent_history) >= 2:
            html_parts.append(self._get_recent_evolution_html(recent_history))

        charts = data.get('charts', {})
        tables = data.get('tables', {})
        enunciados = data.get('enunciados', {})

        processed_table_keys = set()

        for chart_key, chart_info in charts.items():
            table_df = tables.get(chart_key)
            if table_df is None:
                for t_k, t_df in tables.items():
                    if t_df is not None and chart_info.get('data') is not None:
                        if list(t_df.columns) == list(chart_info['data'].columns):
                            table_df = t_df
                            processed_table_keys.add(t_k)
                            break
            else:
                processed_table_keys.add(chart_key)

            enunciado = chart_info.get('enunciado') or enunciados.get(chart_key, '')
            html_parts.append(self._get_chart_table_combo_html(chart_key, chart_info, table_df, enunciado))

        for table_key, table_df in tables.items():
            if table_key not in processed_table_keys and table_key != 'computers':
                enunciado = enunciados.get(table_key, '')
                html_parts.append(self._get_standalone_table_html(table_key, table_df, enunciado))

        if 'computers' in tables:
            html_parts.append(self._get_investigation_html(tables['computers'], investigations))

        if data.get('recommendations'):
            html_parts.append(self._get_recommendations_html(data['recommendations']))

        html_parts.append(self._get_footer_html())
        html_parts.append(self._get_scripts_html())

        return '\n'.join(html_parts)

    def _encode_image(self, path):
        """Converte imagem local para base64 seguro."""
        if path and os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    ext = os.path.splitext(path)[1].lstrip('.').lower()
                    mime = 'image/svg+xml' if ext == 'svg' else f'image/{ext}'
                    return f"data:{mime};base64,{base64.b64encode(f.read()).decode('utf-8')}"
            except Exception:
                pass
        return ""

    def _get_header_html(self, metadata_json):
        """Cabeçalho com CSS executivo moderno no modo escuro padrão."""
        safe_metadata_json = str(metadata_json).replace("</script>", "<\\/script>")
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Executivo de Cibersegurança - {html.escape(str(self.client_name))} ({html.escape(str(self.period))})</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    
    <!-- Metadados Estruturados Embutidos -->
    <script id="report-metadata" type="application/json">
{safe_metadata_json}
    </script>

    <style>
        :root {{
            --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            
            --primary-brand: {self.secondary};
            --accent-brand: {self.accent};
            
            /* Modo Escuro Executivo (Padrão Único) */
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
            --text-on-accent: #ffffff;
            
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

        /* Navbar Superior */
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
            background: rgba(139, 0, 0, 0.2);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .navbar-actions {{
            display: flex;
            align-items: center;
            gap: 12px;
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

        /* Capa Hero */
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
            background: radial-gradient(circle, rgba(139, 0, 0, 0.18) 0%, rgba(59, 130, 246, 0.05) 50%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }}

        .hero-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 35px;
        }}

        /* Bloco Dual de Logos (Netsafe | Cliente) */
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

        .logo-netsafe-wrap {{
            display: flex;
            align-items: center;
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

        .logo-client-wrap {{
            display: flex;
            align-items: center;
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
            color: #ef4444;
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
            max-width: 700px;
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
            background: var(--primary-brand);
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

        /* Caixa de Enunciado / Callout Executivo */
        .enunciado-callout {{
            background: var(--bg-callout);
            border-left: 4px solid var(--primary-brand);
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
            color: #ef4444;
            margin-bottom: 6px;
        }}

        .callout-icon-wrap {{
            width: 18px;
            height: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
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

        /* KPIs */
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
            transition: all 0.25s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .kpi-card:hover {{
            transform: translateY(-3px);
            border-color: var(--border-medium);
            box-shadow: var(--shadow-card);
        }}

        .kpi-card-glow {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-brand), transparent);
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
            background: rgba(139, 0, 0, 0.15);
            color: #ef4444;
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

        .kpi-mom-badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            font-weight: 700;
            font-family: var(--font-mono);
            padding: 3px 8px;
            border-radius: 4px;
            margin-top: 8px;
        }}

        .kpi-mom-badge svg {{
            width: 12px;
            height: 12px;
        }}

        .kpi-mom-badge.badge-positive {{
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.25);
        }}

        .kpi-mom-badge.badge-alert {{
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.25);
        }}

        .kpi-mom-badge.badge-neutral {{
            background: rgba(148, 163, 184, 0.12);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }}

        /* Combo Gráfico + Tabela */
        .chart-table-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            align-items: start;
        }}

        @media (max-width: 960px) {{
            .chart-table-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .chart-container-box {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 20px;
            position: relative;
        }}

        .box-header {{
            font-size: 13px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .box-icon-wrap {{
            width: 18px;
            height: 18px;
            color: #ef4444;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .box-icon-wrap svg {{
            width: 16px;
            height: 16px;
        }}

        /* Tabelas */
        .table-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            overflow: hidden;
        }}

        .table-toolbar {{
            padding: 12px 16px;
            background: rgba(0, 0, 0, 0.1);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }}

        .table-search-box {{
            position: relative;
            display: flex;
            align-items: center;
        }}

        .search-icon-svg {{
            position: absolute;
            left: 10px;
            width: 14px;
            height: 14px;
            color: var(--text-muted);
            pointer-events: none;
        }}

        .table-search-input {{
            background: var(--bg-surface);
            border: 1px solid var(--border-medium);
            border-radius: var(--radius-sm);
            padding: 6px 12px 6px 30px;
            font-size: 12px;
            color: var(--text-primary);
            outline: none;
            width: 220px;
            font-family: var(--font-sans);
        }}

        .table-search-input:focus {{
            border-color: var(--primary-brand);
        }}

        .table-responsive {{
            overflow-x: auto;
            max-height: 480px;
            overflow-y: auto;
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
            position: sticky;
            top: 0;
            z-index: 10;
            cursor: pointer;
            user-select: none;
        }}

        table.cyber-table thead th:hover {{
            color: var(--text-primary);
        }}

        .sort-caret {{
            display: inline-block;
            margin-left: 6px;
            width: 8px;
            height: 8px;
            opacity: 0.6;
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

        .badge-count {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(139, 0, 0, 0.15);
            color: #ef4444;
            font-family: var(--font-mono);
            font-weight: 600;
            font-size: 11px;
        }}

        /* Investigação */
        .investigation-grid {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .investigation-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 16px 20px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
            transition: all 0.2s ease;
        }}

        .investigation-card:hover {{
            border-color: var(--border-medium);
            transform: translateX(3px);
        }}

        .status-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-top: 4px;
            flex-shrink: 0;
        }}

        .dot-high {{
            background: #ef4444;
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
        }}

        .dot-medium {{
            background: #f59e0b;
            box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
        }}

        .dot-low {{
            background: #3b82f6;
        }}

        .dot-none {{
            background: #64748b;
        }}

        .inv-content {{
            flex: 1;
        }}

        .inv-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }}

        .inv-title-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .inv-device-icon {{
            width: 16px;
            height: 16px;
            color: var(--text-muted);
        }}

        .inv-computer-name {{
            font-weight: 700;
            font-size: 14px;
            color: var(--text-primary);
            font-family: var(--font-mono);
        }}

        .inv-event-count {{
            font-size: 12px;
            font-weight: 600;
            color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: var(--font-mono);
        }}

        .inv-description {{
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }}

        /* Recomendações */
        .recs-container {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .rec-item {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 16px 20px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
            font-size: 13.5px;
            line-height: 1.5;
        }}

        .rec-icon-badge {{
            width: 32px;
            height: 32px;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .rec-icon-badge svg {{
            width: 18px;
            height: 18px;
        }}

        .rec-item.priority-high {{
            border-left: 4px solid #ef4444;
            background: rgba(239, 68, 68, 0.04);
        }}

        .rec-item.priority-high .rec-icon-badge {{
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
        }}

        .rec-item.priority-medium {{
            border-left: 4px solid #f59e0b;
            background: rgba(245, 158, 11, 0.04);
        }}

        .rec-item.priority-medium .rec-icon-badge {{
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
        }}

        .rec-item.priority-info {{
            border-left: 4px solid #3b82f6;
            background: rgba(59, 130, 246, 0.04);
        }}

        .rec-item.priority-info .rec-icon-badge {{
            background: rgba(59, 130, 246, 0.15);
            color: #3b82f6;
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

        /* Impressão / Salvar PDF */
        @media print {{
            body {{
                background: #06090f !important;
                color: #f8fafc !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .report-wrapper {{
                max-width: 100% !important;
                margin: 0 !important;
                border: none !important;
                box-shadow: none !important;
                border-radius: 0 !important;
            }}
            .top-navbar, .table-toolbar, .btn-action {{
                display: none !important;
            }}
            .hero-cover {{
                background: #070a10 !important;
                color: white !important;
                page-break-after: always;
                min-height: 90vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            .report-section {{
                page-break-inside: avoid;
                padding: 30px 20px !important;
            }}
            .chart-table-grid {{
                grid-template-columns: 1fr !important;
            }}
        }}

        @media (max-width: 768px) {{
            .report-section {{
                padding: 30px 20px;
            }}
            .hero-cover {{
                padding: 40px 20px;
            }}
            .hero-title {{
                font-size: 26px;
            }}
            .hero-meta-grid {{
                grid-template-columns: 1fr 1fr;
            }}
            .hero-logos-dual {{
                flex-direction: column;
                gap: 10px;
                align-items: flex-start;
            }}
            .logo-vertical-divider {{
                display: none;
            }}
            .report-footer {{
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-wrapper">
"""

    def _get_top_navbar_html(self):
        """Barra de navegação superior focada em Dark Mode com botão de impressão/PDF."""
        return f"""
        <nav class="top-navbar">
            <div class="navbar-brand">
                <div class="brand-icon-wrap">
                    {self._get_icon_svg('shield')}
                </div>
                <span>{self.company_name}</span>
                <span class="navbar-badge">MDR Report</span>
            </div>
            <div class="navbar-actions">
                <button class="btn-action" onclick="window.print()">
                    {self._get_icon_svg('printer')}
                    <span>Imprimir / Salvar PDF</span>
                </button>
            </div>
        </nav>
        """

    def _get_cover_html(self):
        """Capa executiva com logos lado a lado separados por linha vertical."""
        # Logo da Netsafe (Branco)
        company_logo_html = ""
        company_logo_src = self._encode_image(self.company_logo)
        if company_logo_src:
            company_logo_html = f'<img src="{company_logo_src}" class="hero-logo-img" alt="{self.company_name}">'
        else:
            company_logo_html = f'<div style="font-size:20px;font-weight:800;letter-spacing:1px;color:#ffffff;">NET<span style="color:#ef4444;">S</span>AFE <span style="font-size:12px;color:#94a3b8;font-weight:500;">CORP</span></div>'

        # Logo do Cliente (à direita da linha vertical)
        client_logo_html = ""
        client_logo_src = self._encode_image(self.client_logo) if self.client_logo else ""
        if client_logo_src:
            client_logo_html = f'<img src="{client_logo_src}" class="hero-logo-img" alt="{self.client_name}">'
        else:
            client_logo_html = f'<div class="client-name-badge">{self.client_name}</div>'

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
                <div class="hero-category">Managed Detection and Response</div>
                <h1 class="hero-title">Relatório Executivo de Cibersegurança</h1>
                <p class="hero-subtitle">Consolidação mensal de telemetria, análise de vetores de ataque e investigações de endpoint.</p>
            </div>

            <div class="hero-meta-grid">
                <div class="hero-meta-item">
                    <div class="hero-meta-label">Cliente</div>
                    <div class="hero-meta-value">{self.client_name}</div>
                </div>
                <div class="hero-meta-item">
                    <div class="hero-meta-label">Período de Análise</div>
                    <div class="hero-meta-value">{self.period}</div>
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

    def _get_summary_html(self, data):
        """Sumário executivo sem emojis."""
        total_events = data.get('total_events', 0)
        total_computers = data.get('total_computers', 0)
        total_users = data.get('total_users', 0)

        month_name = self.period.split('/')[0] if '/' in self.period else self.period

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Sumário Executivo</h2>
                </div>
                <p class="section-subtitle">Visão macro da postura de segurança e telemetria capturada no período</p>
            </div>

            <div class="enunciado-callout" style="background: rgba(59, 130, 246, 0.05); border-left-color: #3b82f6;">
                <div class="enunciado-header" style="color: #3b82f6;">
                    <div class="callout-icon-wrap">{self._get_icon_svg('target')}</div>
                    <span>Objetivo do Documento</span>
                </div>
                <div class="enunciado-body">
                    Este relatório, elaborado pelo time especializado de <strong>MDR (Managed Detection and Response)</strong>, apresenta a análise detalhada dos eventos de segurança, regras de prevenção acionadas e incidentes observados no ambiente corporativo de <strong>{self.client_name}</strong> durante o mês de <strong>{month_name}</strong>.
                </div>
            </div>

            <p style="font-size:14px;color:var(--text-secondary);line-height:1.8;max-width:900px;">
                No período analisado, o ecossistema de defesa processou um total de <strong>{total_events:,}</strong> eventos de ameaça, abrangendo <strong>{total_computers}</strong> estações/servidores e <strong>{total_users}</strong> identidades de usuários. As seções a seguir detalham as métricas, comportamentos anômalos e recomendações técnicas para mitigação de riscos.
            </p>
        </section>
        """

    def _get_kpis_html(self, data, mom_deltas=None):
        """Cards de KPIs com SVGs próprios e badges de comparação MoM."""
        kpi_defs = [
            ('total_events', 'Total de Eventos', 'events', 'Métrica Geral'),
            ('total_actions', 'Ações do Antivírus', 'shield', 'Proteção Ativa'),
            ('total_computers', 'Endpoints Afetados', 'computer', 'Parque de Máquinas'),
            ('total_users', 'Usuários com Alertas', 'user', 'Identidades'),
            ('total_violations', 'Regras Violadas', 'alert', 'Exploit Prevention'),
            ('total_playbook_events', 'Eventos de Playbook', 'document', 'Trellix Insights')
        ]

        cards_html = ""
        for key, label, icon_type, badge_label in kpi_defs:
            if key in data:
                val = data[key]
                mom_html = ""
                if mom_deltas and key in mom_deltas:
                    d_info = mom_deltas[key]
                    pct = d_info.get('pct', 0)
                    dir_name = d_info.get('direction', 'neutral')
                    status = d_info.get('status', 'neutral')
                    
                    icon_svg = self._get_icon_svg('trend_' + dir_name)
                    sign = "+" if d_info.get('diff', 0) > 0 else ""
                    mom_html = f"""
                    <div class="kpi-mom-badge badge-{status}">
                        {icon_svg}
                        <span>{sign}{pct:.1f}% vs mês ant.</span>
                    </div>
                    """

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
                    {mom_html}
                </div>
                """

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Indicadores Principais (KPIs)</h2>
                </div>
                <p class="section-subtitle">Métricas consolidadas de detecção e resposta com comparativo mês a mês</p>
            </div>
            <div class="kpi-grid">
                {cards_html}
            </div>
        </section>
        """

    def _get_recent_evolution_html(self, recent_history):
        """Gráfico de linha de evolução temporal recente (últimos meses)."""
        if not recent_history or len(recent_history) < 2:
            return ""

        periods = [r.get('period', '') for r in recent_history]
        events = [r.get('metrics', {}).get('total_events', 0) for r in recent_history]
        actions = [r.get('metrics', {}).get('total_actions', 0) for r in recent_history]
        violations = [r.get('metrics', {}).get('total_violations', 0) for r in recent_history]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=periods,
            y=events,
            mode='lines+markers',
            name='Eventos Totais',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=7, color='#3b82f6'),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.08)'
        ))

        fig.add_trace(go.Scatter(
            x=periods,
            y=actions,
            mode='lines+markers',
            name='Ações Antivírus',
            line=dict(color='#10b981', width=2, dash='dot'),
            marker=dict(size=6, color='#10b981')
        ))

        fig.add_trace(go.Scatter(
            x=periods,
            y=violations,
            mode='lines+markers',
            name='Violações de Exploit',
            line=dict(color='#ef4444', width=2),
            marker=dict(size=6, color='#ef4444')
        ))

        fig.update_layout(
            height=320,
            margin=dict(l=15, r=15, t=25, b=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans, sans-serif', size=11, color='#94a3b8'),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.25,
                xanchor='center',
                x=0.5,
                font=dict(size=10)
            ),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.06)',
                showgrid=True
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.06)',
                showgrid=True,
                title='Eventos'
            )
        )

        chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Evolução Temporal Recente</h2>
                </div>
                <p class="section-subtitle">Comparativo histórico de eventos e respostas nos últimos períodos monitorados</p>
            </div>
            <div class="chart-container-box">
                {chart_html}
            </div>
        </section>
        """

    def _get_chart_table_combo_html(self, chart_key, chart_info, table_df, enunciado=""):
        """Seção combinada de gráfico, tabela e enunciado sem emojis."""
        df = chart_info.get('data')
        label_col = chart_info.get('label_col')
        value_col = chart_info.get('value_col')
        raw_title = chart_info.get('title', chart_key.replace('_', ' ').title())
        title = self.clean_emojis(raw_title)
        clean_enunciado = self.clean_emojis(enunciado)

        if df is None or df.empty:
            return ""

        df_top = df.nlargest(6, value_col) if len(df) > 6 else df
        colors = ['#dc2626', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#64748b']

        fig = px.pie(
            df_top,
            names=label_col,
            values=value_col,
            hole=0.6,
            color_discrete_sequence=colors
        )

        fig.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=10, b=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans, sans-serif', size=11, color='#94a3b8'),
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5,
                font=dict(size=10)
            )
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent',
            textfont=dict(size=10, color='white', family='Plus Jakarta Sans, sans-serif'),
            marker=dict(line=dict(color='#111827', width=2))
        )

        chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})
        table_html = self._render_table_html(table_df if table_df is not None else df, table_id=f"table_{chart_key}")

        enunciado_html = ""
        if clean_enunciado:
            enunciado_html = f"""
            <div class="enunciado-callout">
                <div class="enunciado-header">
                    <div class="callout-icon-wrap">{self._get_icon_svg('analytics')}</div>
                    <span>Contexto e Análise Técnica</span>
                </div>
                <div class="enunciado-body">{clean_enunciado}</div>
            </div>
            """

        return f"""
        <section class="report-section" id="section_{chart_key}">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">{title}</h2>
                </div>
                <p class="section-subtitle">Distribuição proporcional e detalhamento tabular</p>
            </div>

            {enunciado_html}

            <div class="chart-table-grid">
                <div class="chart-container-box">
                    <div class="box-header">
                        <div class="box-icon-wrap">{self._get_icon_svg('chart_pie')}</div>
                        <span>Distribuição Percentual</span>
                    </div>
                    {chart_html}
                </div>

                <div class="table-card">
                    <div class="table-toolbar">
                        <span style="font-size:12px;font-weight:600;color:var(--text-secondary);">Registros Detalhados</span>
                        <div class="table-search-box">
                            {self._get_icon_svg('search')}
                            <input type="text" class="table-search-input" placeholder="Filtrar registros..." onkeyup="filterTable('table_{chart_key}', this.value)">
                        </div>
                    </div>
                    <div class="table-responsive">
                        {table_html}
                    </div>
                </div>
            </div>
        </section>
        """

    def _get_standalone_table_html(self, table_key, table_df, enunciado=""):
        """Seção tabular sem gráfico associado."""
        if table_df is None or table_df.empty:
            return ""

        title = self.clean_emojis(table_key.replace('_', ' ').title())
        clean_enunciado = self.clean_emojis(enunciado)
        table_html = self._render_table_html(table_df, table_id=f"table_{table_key}")

        enunciado_html = ""
        if clean_enunciado:
            enunciado_html = f"""
            <div class="enunciado-callout">
                <div class="enunciado-header">
                    <div class="callout-icon-wrap">{self._get_icon_svg('analytics')}</div>
                    <span>Contexto e Análise Técnica</span>
                </div>
                <div class="enunciado-body">{clean_enunciado}</div>
            </div>
            """

        return f"""
        <section class="report-section" id="section_{table_key}">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">{title}</h2>
                </div>
                <p class="section-subtitle">Detalhamento dos dados registrados</p>
            </div>

            {enunciado_html}

            <div class="table-card">
                <div class="table-toolbar">
                    <span style="font-size:12px;font-weight:600;color:var(--text-secondary);">Registros Detalhados</span>
                    <div class="table-search-box">
                        {self._get_icon_svg('search')}
                        <input type="text" class="table-search-input" placeholder="Filtrar registros..." onkeyup="filterTable('table_{table_key}', this.value)">
                    </div>
                </div>
                <div class="table-responsive">
                    {table_html}
                </div>
            </div>
        </section>
        """

    def _render_table_html(self, df, table_id="table_default"):
        """Renderiza HTML de tabela com cabeçalhos amigáveis e indicadores de ordenação SVG."""
        if df is None or df.empty:
            return "<div style='padding:20px;text-align:center;color:var(--text-muted);'>Nenhum registro encontrado.</div>"

        col_labels = {
            'action_taken': 'Ação Tomada',
            'user_name': 'Usuário / Identidade',
            'computer_name': 'Computador / Host',
            'rule_name': 'Regra Acionada',
            'event_count': 'Total Eventos',
            'violation_count': 'Violações',
            'detection_count': 'Detecções'
        }

        tbl_html = f'<table class="cyber-table" id="{table_id}">\n<thead>\n<tr>\n'

        for col in df.columns:
            raw_display_name = col_labels.get(col, col.replace('_', ' ').title())
            display_name = html.escape(str(raw_display_name))
            tbl_html += f'<th onclick="sortTable(\'{table_id}\', {list(df.columns).index(col)})">{display_name} <span class="sort-caret">{self._get_icon_svg("sort")}</span></th>\n'

        tbl_html += '</tr>\n</thead>\n<tbody>\n'

        for _, row in df.iterrows():
            tbl_html += '<tr>\n'
            for col in df.columns:
                val = row[col]
                if isinstance(val, (int, float)):
                    if val == int(val):
                        display_val = f"{int(val):,}"
                    else:
                        display_val = f"{val:,.1f}"
                    tbl_html += f'<td class="td-numeric"><span class="badge-count">{display_val}</span></td>\n'
                else:
                    escaped_val = html.escape(self.clean_emojis(str(val)))
                    tbl_html += f'<td>{escaped_val}</td>\n'
            tbl_html += '</tr>\n'

        tbl_html += '</tbody>\n</table>'
        return tbl_html

    def _get_investigation_html(self, df_computers, investigations):
        """Seção de Investigação Forense / Endpoint."""
        if df_computers is None or df_computers.empty:
            return ""

        df_sorted = df_computers.copy()
        if 'event_count' in df_sorted.columns:
            df_sorted['event_count'] = pd.to_numeric(df_sorted['event_count'], errors='coerce').fillna(0)
            df_sorted = df_sorted.sort_values(by='event_count', ascending=False)

        cards = ""

        for idx, (_, row) in enumerate(df_sorted.iterrows(), 1):
            raw_comp = row.get('computer_name', f'Host-{idx}')
            clean_comp = self.clean_emojis(raw_comp)
            computer = html.escape(clean_comp)
            events = int(row.get('event_count', 0))
            raw_inv = investigations.get(raw_comp, '') or investigations.get(clean_comp, '')
            investigation_text = self.clean_emojis(raw_inv)

            if investigation_text:
                if idx <= 2:
                    dot_class = "dot-high"
                elif idx <= 6:
                    dot_class = "dot-medium"
                else:
                    dot_class = "dot-low"
                escaped_inv = html.escape(investigation_text)
            else:
                dot_class = "dot-none"
                escaped_inv = "Sem observações críticas adicionais registradas até a emissão deste relatório."

            cards += f"""
            <div class="investigation-card">
                <div class="status-dot {dot_class}"></div>
                <div class="inv-content">
                    <div class="inv-header">
                        <div class="inv-title-group">
                            <div class="inv-device-icon">{self._get_icon_svg('computer')}</div>
                            <span class="inv-computer-name">{computer}</span>
                        </div>
                        <span class="inv-event-count">{events:,} eventos</span>
                    </div>
                    <div class="inv-description">{escaped_inv}</div>
                </div>
            </div>
            """

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Investigação Detalhada de Endpoints</h2>
                </div>
                <p class="section-subtitle">Acompanhamento dos hosts com maior frequência de incidentes</p>
            </div>

            <div class="enunciado-callout">
                <div class="enunciado-header">
                    <div class="callout-icon-wrap">{self._get_icon_svg('shield')}</div>
                    <span>Diretriz de Triagem</span>
                </div>
                <div class="enunciado-body">
                    Abaixo constam as notas de investigação técnica emitidas pelos analistas do SOC/MDR para os computadores com maior incidência no período, classificando a criticidade e ações recomendadas.
                </div>
            </div>

            <div class="investigation-grid">
                {cards}
            </div>
        </section>
        """

    def _get_recommendations_html(self, recommendations):
        """Seção de Recomendações com Badges e SVGs próprios."""
        items = ""
        for raw_rec in recommendations:
            raw_rec_str = str(raw_rec)
            if "🔴" in raw_rec_str or "[ALTA]" in raw_rec_str.upper() or "CRITIC" in raw_rec_str.upper() or "ELEVADO" in raw_rec_str.upper():
                priority_class = "priority-high"
                icon_type = "alert"
            elif "🟡" in raw_rec_str or "[MÉDIA]" in raw_rec_str.upper() or "[MEDIA]" in raw_rec_str.upper() or "MODERADO" in raw_rec_str.upper():
                priority_class = "priority-medium"
                icon_type = "alert"
            else:
                priority_class = "priority-info"
                icon_type = "shield"

            clean_text = self.clean_emojis(raw_rec_str)
            clean_text = re.sub(r'^\[(ALTA|MÉDIA|MEDIA|BAIXA|INFO)\]\s*', '', clean_text, flags=re.IGNORECASE)
            escaped_text = html.escape(clean_text)

            items += f"""
            <div class="rec-item {priority_class}">
                <div class="rec-icon-badge">
                    {self._get_icon_svg(icon_type)}
                </div>
                <div>{escaped_text}</div>
            </div>
            """

        return f"""
        <section class="report-section">
            <div class="section-heading">
                <div class="section-title-wrap">
                    <div class="section-indicator"></div>
                    <h2 class="section-title">Recomendações e Próximos Passos</h2>
                </div>
                <p class="section-subtitle">Direcionamentos estratégicos baseados na análise do período</p>
            </div>
            <div class="recs-container">
                {items}
            </div>
        </section>
        """

    def _get_footer_html(self):
        """Rodapé formal do relatório."""
        company_logo_src = self._encode_image(self.company_logo)
        logo_html = f'<img src="{company_logo_src}" class="footer-logo-img" alt="{self.company_name}">' if company_logo_src else f'<strong>{self.company_name}</strong>'

        return f"""
        <footer class="report-footer">
            <div class="footer-left">
                {logo_html}
                <span>MDR Security Operations Center</span>
            </div>
            <div>
                Documento Estritamente Confidencial - Uso Exclusivo
            </div>
        </footer>
    </div>
        """

    def _get_scripts_html(self):
        """Scripts para busca em tabelas e ordenação."""
        return """
    <script>
        function filterTable(tableId, query) {
            const table = document.getElementById(tableId);
            if (!table) return;
            const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
            const q = query.toLowerCase();

            for (let i = 0; i < rows.length; i++) {
                const text = rows[i].innerText.toLowerCase();
                rows[i].style.display = text.includes(q) ? '' : 'none';
            }
        }

        function sortTable(tableId, colIndex) {
            const table = document.getElementById(tableId);
            if (!table) return;
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = Array.from(tbody.getElementsByTagName('tr'));
            
            const isAsc = table.getAttribute('data-sort-asc') !== 'true';
            table.setAttribute('data-sort-asc', isAsc ? 'true' : 'false');

            rows.sort((a, b) => {
                let cellA = a.getElementsByTagName('td')[colIndex].innerText.replace(/,/g, '').trim();
                let cellB = b.getElementsByTagName('td')[colIndex].innerText.replace(/,/g, '').trim();

                const numA = parseFloat(cellA);
                const numB = parseFloat(cellB);

                if (!isNaN(numA) && !isNaN(numB)) {
                    return isAsc ? numA - numB : numB - numA;
                }
                return isAsc ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            });

            rows.forEach(r => tbody.appendChild(r));
        }
    </script>
</body>
</html>
"""

    def _get_icon_svg(self, icon_type):
        """Biblioteca de ícones vetoriais SVG customizados."""
        icons = {
            'shield': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
            'events': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="8" rx="0.5"/><rect x="12" y="7" width="3" height="11" rx="0.5"/><rect x="17" y="13" width="3" height="5" rx="0.5"/></svg>',
            'computer': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M2 20h20M8 16v4M16 16v4"/></svg>',
            'user': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
            'alert': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 20h20L12 2z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            'document': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
            'target': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
            'analytics': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
            'chart_pie': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
            'printer': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>',
            'search': '<svg class="search-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
            'sort': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="7 15 12 20 17 15"/><polyline points="7 9 12 4 17 9"/></svg>',
            'trend_up': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
            'trend_down': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>',
            'trend_neutral': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>'
        }
        return icons.get(icon_type, icons['shield'])
