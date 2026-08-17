import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.ticker as mticker
from fpdf import FPDF
import os
from datetime import datetime
import tempfile
import shutil
import pandas as pd
import numpy as np


class CyberReportPDF(FPDF):
    def __init__(self, client_config, period_str):
        super().__init__('P', 'mm', 'A4')
        self.client = client_config
        self.period = period_str

        # Cores
        self.primary = self.hex_to_rgb(client_config.get('primary_color', '#1f77b4'))
        self.secondary = self.hex_to_rgb(client_config.get('secondary_color', '#ff7f0e'))
        self.accent = self.hex_to_rgb(client_config.get('secondary_color', '#ff7f0e'))

        # Cores derivadas
        self.light_primary = tuple(min(255, c + 40) for c in self.primary)
        self.dark_primary = tuple(max(0, c - 40) for c in self.primary)

        # Configurar margens
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=25)

        # Fonte Unicode
        self.font_name = 'DejaVu'
        self.font_loaded = self.setup_fonts()

        # Logo
        self.logo_path = client_config.get('logo_path', '')

        # Contador de páginas para sumário
        self.toc_entries = []

    def setup_fonts(self):
        """Configura fontes Unicode."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
            "fonts/DejaVuSans.ttf",
            "C:/Windows/Fonts/DejaVuSans.ttf",
            "/Library/Fonts/DejaVuSans.ttf",
        ]

        self.font_path = None

        for path in font_paths:
            if os.path.exists(path):
                self.font_path = path
                break

        if self.font_path and os.path.exists(self.font_path):
            try:
                self.add_font('DejaVu', '', self.font_path, uni=True)

                bold_path = self.font_path.replace('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf')
                if os.path.exists(bold_path):
                    self.add_font('DejaVu', 'B', bold_path, uni=True)
                else:
                    self.add_font('DejaVu', 'B', self.font_path, uni=True)

                italic_path = self.font_path.replace('DejaVuSans.ttf', 'DejaVuSans-Oblique.ttf')
                if os.path.exists(italic_path):
                    self.add_font('DejaVu', 'I', italic_path, uni=True)
                else:
                    self.add_font('DejaVu', 'I', self.font_path, uni=True)

                print(f"✅ Fonte DejaVu carregada: {self.font_path}")
                return True
            except Exception as e:
                print(f"⚠️ Erro ao carregar DejaVu: {e}")

        self.font_name = 'Helvetica'
        return False

    def hex_to_rgb(self, hex_color):
        """Converte cor hexadecimal para RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def clean_text(self, text):
        """Limpa texto para compatibilidade com a fonte."""
        if not isinstance(text, str):
            return str(text)

        if self.font_loaded:
            return text

        replacements = {
            'ç': 'c', 'Ç': 'C', 'ã': 'a', 'Ã': 'A', 'õ': 'o', 'Õ': 'O',
            'á': 'a', 'Á': 'A', 'à': 'a', 'À': 'A', 'â': 'a', 'Â': 'A',
            'é': 'e', 'É': 'E', 'ê': 'e', 'Ê': 'E', 'í': 'i', 'Í': 'I',
            'ó': 'o', 'Ó': 'O', 'ô': 'o', 'Ô': 'O', 'ú': 'u', 'Ú': 'U',
            'ü': 'u', 'Ü': 'U', '•': '-', '🔴': '[CRITICO]', '🟡': '[ATENCAO]',
            '💻': '[PC]', '👤': '[USER]', '🔧': '[REGRA]', '✅': '[OK]',
            '⚠️': '[AVISO]', '❌': '[ERRO]',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = text.encode('ascii', 'ignore').decode('ascii')
        return text

    # =============================================
    # MÉTODOS DE ESTILIZAÇÃO
    # =============================================

    def add_section_title(self, title, subtitle=None):
        """Adiciona título de seção estilizado."""
        self.ln(5)

        # Barra colorida lateral
        x_start = 15
        y_start = self.get_y()
        self.set_fill_color(*self.primary)
        self.rect(x_start, y_start, 4, 10, 'F')

        # Título
        self.set_x(x_start + 8)
        self.set_font(self.font_name, 'B', 16)
        self.set_text_color(*self.dark_primary)
        title_clean = self.clean_text(title)
        self.cell(0, 10, title_clean, ln=True)

        # Linha decorativa
        self.set_draw_color(*self.primary)
        self.set_line_width(0.5)
        self.line(x_start + 8, self.get_y(), 195, self.get_y())

        # Subtítulo
        if subtitle:
            self.ln(2)
            self.set_x(x_start + 8)
            self.set_font(self.font_name, 'I', 10)
            self.set_text_color(120)
            subtitle_clean = self.clean_text(subtitle)
            self.cell(0, 6, subtitle_clean, ln=True)

        self.ln(5)

    def add_info_box(self, text, color=None, title=None):
        """Adiciona caixa de informação destacada."""
        if color is None:
            color = self.primary

        x_start = 15
        y_start = self.get_y()

        # Fundo da caixa
        self.set_fill_color(245, 245, 245)

        # Calcular altura necessária
        self.set_font(self.font_name, '', 9)
        lines = self.multi_cell(170, 6, self.clean_text(text), dry_run=True, output='LINES')
        box_height = max(20, len(lines) * 6 + 15)

        # Desenhar caixa
        self.set_draw_color(*color)
        self.set_line_width(0.3)
        self.rect(x_start, y_start, 180, box_height, 'DF')

        # Barra lateral colorida
        self.set_fill_color(*color)
        self.rect(x_start, y_start, 3, box_height, 'F')

        # Título da caixa
        self.set_xy(x_start + 8, y_start + 3)
        if title:
            self.set_font(self.font_name, 'B', 10)
            self.set_text_color(*color)
            self.cell(0, 6, self.clean_text(title), ln=True)
            self.set_xy(x_start + 8, y_start + 11)

        # Texto
        self.set_font(self.font_name, '', 9)
        self.set_text_color(50)
        self.multi_cell(165, 6, self.clean_text(text))

        self.set_y(y_start + box_height + 5)

    def add_divider(self):
        """Adiciona linha divisória estilizada."""
        y = self.get_y()
        x_center = 105

        # Linha central
        self.set_draw_color(*self.primary)
        self.set_line_width(0.3)
        self.line(15, y, 195, y)

        # Círculo central
        self.set_fill_color(*self.primary)
        self.ellipse(x_center - 2, y - 2, 4, 4, 'F')

        self.ln(8)

    # =============================================
    # PÁGINAS DO RELATÓRIO
    # =============================================

    def header(self):
        """Cabeçalho das páginas internas."""
        if self.page_no() <= 1:
            return

        # Fundo do cabeçalho
        self.set_fill_color(*self.primary)
        self.rect(0, 0, 210, 18, 'F')

        # Logo (se existir)
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, x=8, y=2, h=14)
            except:
                pass

        # Título do relatório
        self.set_xy(25, 3)
        self.set_font(self.font_name, 'B', 9)
        self.set_text_color(255, 255, 255)
        header_text = self.clean_text(f"{self.client.get('client_name', 'Cliente')}")
        self.cell(0, 6, header_text, align='L')

        # Período
        self.set_xy(25, 10)
        self.set_font(self.font_name, '', 7)
        self.set_text_color(230, 230, 230)
        period_text = self.clean_text(f"Período: {self.period}")
        self.cell(0, 5, period_text, align='L')

        # Número da página
        self.set_xy(180, 6)
        self.set_font(self.font_name, 'B', 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, str(self.page_no()), align='R')

        self.set_y(22)

    def footer(self):
        """Rodapé das páginas internas."""
        if self.page_no() <= 1:
            return

        self.set_y(-20)

        # Linha
        self.set_draw_color(*self.primary)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())

        # Texto do rodapé
        self.set_y(-16)
        self.set_font(self.font_name, 'I', 7)
        self.set_text_color(100)

        footer_text = self.clean_text(
            f"{self.client.get('company_name', 'Consultoria')} | Confidencial | Página {self.page_no()}/{{nb}}"
        )
        self.cell(0, 5, footer_text, align='C')

    def add_cover_page(self):
        """Capa profissional com design moderno."""
        self.add_page()

        # ===== FUNDO =====
        # Fundo principal
        self.set_fill_color(*self.primary)
        self.rect(0, 0, 210, 297, 'F')

        # Círculos decorativos
        self.set_fill_color(*self.light_primary)
        self.ellipse(150, -20, 100, 100, 'F')
        self.ellipse(-30, 200, 80, 80, 'F')
        self.set_fill_color(*self.dark_primary)
        self.ellipse(180, 150, 60, 60, 'F')

        # ===== LOGO (se existir) =====
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, x=55, y=20, w=100)
            except:
                pass

        # ===== TÍTULO =====
        self.set_text_color(255, 255, 255)
        self.set_font(self.font_name, 'B', 32)
        self.ln(60)
        self.cell(0, 14, 'RELATÓRIO DE', align='C', ln=True)
        self.cell(0, 14, 'CIBERSEGURANÇA', align='C', ln=True)

        # ===== LINHA DECORATIVA =====
        self.ln(8)
        y_line = self.get_y()
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.8)
        self.line(70, y_line, 140, y_line)
        self.set_fill_color(255, 255, 255)
        self.ellipse(103, y_line - 2, 4, 4, 'F')

        # ===== INFORMAÇÕES =====
        self.ln(15)
        self.set_font(self.font_name, '', 14)

        # Caixa de informações
        info_y = self.get_y()
        box_width = 140
        box_x = (210 - box_width) / 2
        box_height = 55

        # Fundo semi-transparente (simulado)
        self.set_fill_color(*self.dark_primary)
        self.rect(box_x, info_y, box_width, box_height, 'F')

        # Borda
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.3)
        self.rect(box_x, info_y, box_width, box_height, 'D')

        # Informações dentro da caixa
        self.set_text_color(255, 255, 255)
        self.set_xy(box_x + 5, info_y + 5)
        self.set_font(self.font_name, 'B', 11)
        client_name = self.clean_text(f"Cliente: {self.client.get('client_name', 'N/D')}")
        self.cell(box_width - 10, 8, client_name, align='C', ln=True)

        self.set_xy(box_x + 5, info_y + 16)
        self.set_font(self.font_name, '', 10)
        period_text = self.clean_text(f"Período: {self.period}")
        self.cell(box_width - 10, 8, period_text, align='C', ln=True)

        self.set_xy(box_x + 5, info_y + 27)
        self.set_font(self.font_name, '', 10)
        date_text = f"Data de Geração: {datetime.now().strftime('%d/%m/%Y')}"
        self.cell(box_width - 10, 8, date_text, align='C', ln=True)

        self.set_xy(box_x + 5, info_y + 38)
        self.set_font(self.font_name, 'I', 9)
        service_text = self.clean_text(f"Serviço: Monitoramento de Segurança")
        self.cell(box_width - 10, 8, service_text, align='C', ln=True)

        # ===== EMPRESA =====
        self.ln(box_height + 25)
        self.set_font(self.font_name, 'B', 16)
        self.set_text_color(255, 255, 255)
        company = self.clean_text(self.client.get('company_name', ''))
        self.cell(0, 10, company, align='C', ln=True)

        # ===== RODAPÉ DA CAPA =====
        self.set_y(280)
        self.set_font(self.font_name, 'I', 8)
        self.set_text_color(200, 200, 200)
        self.cell(0, 5, 'Documento Confidencial', align='C', ln=True)
        self.cell(0, 5, 'Uso exclusivo do cliente autorizado', align='C', ln=True)

    def add_table_of_contents(self, sections):
        """Adiciona sumário estilizado."""
        self.add_page()
        self.add_section_title('Sumário', 'Navegue pelo conteúdo deste relatório')

        self.ln(5)

        for i, (section_title, page_num) in enumerate(sections):
            y = self.get_y()

            # Número da seção
            self.set_font(self.font_name, 'B', 12)
            self.set_text_color(*self.primary)
            self.cell(10, 10, f"{i+1:02d}", align='L')

            # Título da seção
            self.set_font(self.font_name, '', 11)
            self.set_text_color(60)
            section_clean = self.clean_text(section_title)
            self.cell(140, 10, section_clean, align='L')

            # Linha pontilhada
            x_dots_start = 170
            x_dots_end = 185
            y_dots = y + 5
            self.set_draw_color(180)
            self.set_line_width(0.2)
            for x in range(int(x_dots_start), int(x_dots_end), 3):
                self.line(x, y_dots, x + 1, y_dots)

            # Número da página
            self.set_font(self.font_name, 'B', 11)
            self.set_text_color(*self.primary)
            self.cell(0, 10, str(page_num), align='R', ln=True)

            # Linha separadora
            if i < len(sections) - 1:
                self.set_draw_color(230)
                self.line(15, self.get_y(), 195, self.get_y())
                self.ln(2)

    def add_summary_section(self, summary_text, highlights=None):
        """Sumário executivo com destaques."""
        self.add_page()
        self.add_section_title('Sumário Executivo', 'Visão geral do período analisado')

        # Texto principal
        self.set_font(self.font_name, '', 10)
        self.set_text_color(40)
        summary_clean = self.clean_text(summary_text)
        self.multi_cell(0, 6, summary_clean)

        self.ln(5)

        # Destaques
        if highlights:
            self.add_info_box(
                "Principais destaques do período:\n\n" + "\n".join(f"• {h}" for h in highlights),
                color=self.secondary,
                title="📌 Destaques"
            )

    def add_kpi_section(self, kpis):
        """Seção de KPIs com cards estilizados."""
        self.add_page()
        self.add_section_title('Indicadores Principais', 'Métricas consolidadas do período')

        kpi_items = list(kpis.items())

        # Configuração dos cards
        cards_per_row = 2
        card_width = 85
        card_height = 30
        gap_x = 10
        gap_y = 5
        start_x = 15

        for i, (label, value) in enumerate(kpi_items):
            row = i // cards_per_row
            col = i % cards_per_row

            x = start_x + col * (card_width + gap_x)
            y = self.get_y() + row * (card_height + gap_y)

            # ===== CARD =====
            # Sombra (simulada com retângulo cinza deslocado)
            self.set_fill_color(220, 220, 220)
            self.rect(x + 2, y + 2, card_width, card_height, 'F')

            # Fundo do card
            self.set_fill_color(255, 255, 255)
            self.rect(x, y, card_width, card_height, 'F')

            # Borda superior colorida
            self.set_fill_color(*self.primary)
            self.rect(x, y, card_width, 4, 'F')

            # Borda
            self.set_draw_color(200)
            self.set_line_width(0.2)
            self.rect(x, y, card_width, card_height, 'D')

            # Valor
            self.set_xy(x + 5, y + 7)
            self.set_font(self.font_name, 'B', 18)
            self.set_text_color(*self.primary)
            display_value = f"{value:,}" if isinstance(value, (int, float)) else str(value)
            self.cell(card_width - 10, 12, display_value, align='C')

            # Label
            self.set_xy(x + 5, y + 21)
            self.set_font(self.font_name, '', 8)
            self.set_text_color(100)
            label_clean = self.clean_text(label)
            self.cell(card_width - 10, 6, label_clean, align='C')

        # Avançar posição Y
        total_rows = (len(kpi_items) + cards_per_row - 1) // cards_per_row
        self.ln(total_rows * (card_height + gap_y) + 10)

    def create_matplotlib_bar_chart(self, df, label_col, value_col, title, color):
        """Cria gráfico de barras estilizado com Matplotlib."""
        if df is None or df.empty:
            return None

        # Ordenar
        df_sorted = df.sort_values(by=value_col, ascending=True).tail(15)

        # Criar figura
        fig, ax = plt.subplots(figsize=(10, max(4, len(df_sorted) * 0.4)))

        # Cores
        color_rgb = tuple(c/255 for c in self.primary)

        # Criar barras com gradiente
        bars = ax.barh(df_sorted[label_col], df_sorted[value_col],
                       color=color_rgb, edgecolor='white', linewidth=0.5, alpha=0.85)

        # Adicionar gradiente
        for bar, value in zip(bars, df_sorted[value_col]):
            bar.set_color(tuple(min(1, c + 0.1) for c in color_rgb))

        # Configurar eixos
        ax.set_xlabel('Número de Eventos', fontsize=9, fontweight='bold', color='#333333')
        ax.set_title(title, fontsize=13, fontweight='bold', color='#1a1a1a', pad=15)

        # Estilizar eixos
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        ax.tick_params(colors='#666666', labelsize=8)

        # Adicionar valores nas barras
        for i, v in enumerate(df_sorted[value_col]):
            ax.text(v, i, f'  {v:,}', va='center', fontsize=8,
                   fontweight='bold', color='#333333')

        # Grid
        ax.xaxis.grid(True, linestyle='--', alpha=0.3, color='#cccccc')
        ax.set_axisbelow(True)

        # Fundo
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        plt.tight_layout()
        return fig

    def create_matplotlib_pie_chart(self, df, label_col, value_col, title, color):
        """Cria gráfico de pizza estilizado com Matplotlib."""
        if df is None or df.empty:
            return None

        # Limitar a 10 itens para legibilidade
        df_plot = df.nlargest(10, value_col)

        # Paleta de cores
        colors = plt.cm.Set3(np.linspace(0, 1, len(df_plot)))

        fig, ax = plt.subplots(figsize=(9, 7))

        # Criar pizza
        wedges, texts, autotexts = ax.pie(
            df_plot[value_col],
            labels=None,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            pctdistance=0.75,
            textprops={'fontsize': 9, 'color': '#333333'}
        )

        # Estilizar porcentagens
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)

        # Legenda
        ax.legend(
            wedges,
            df_plot[label_col],
            title="Legenda",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=8,
            title_fontsize=9
        )

        # Título
        ax.set_title(title, fontsize=13, fontweight='bold', color='#1a1a1a', pad=15)

        # Fundo
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        plt.tight_layout()
        return fig

    def add_chart_section(self, title, chart_data):
        """Adiciona seção com gráficos estilizados."""
        self.add_page()
        self.add_section_title(title, 'Análise gráfica dos dados')

        df = chart_data.get('data')
        label_col = chart_data.get('label_col')
        value_col = chart_data.get('value_col')

        if df is None or df.empty:
            self.set_font(self.font_name, 'I', 10)
            self.set_text_color(128)
            self.cell(0, 8, 'Sem dados disponíveis.', ln=True)
            return

        tmpdir = tempfile.mkdtemp()

        # Gráfico de barras
        bar_fig = self.create_matplotlib_bar_chart(
            df, label_col, value_col, title, self.primary
        )

        if bar_fig:
            bar_path = os.path.join(tmpdir, "bar.png")
            bar_fig.savefig(bar_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(bar_fig)

            if os.path.exists(bar_path):
                self.image(bar_path, x=20, w=170)
                self.ln(8)

        # Gráfico de pizza (se poucos itens)
        if len(df) <= 15:
            self.ln(5)
            pie_fig = self.create_matplotlib_pie_chart(
                df, label_col, value_col, f"Distribuição Percentual", self.primary
            )

            if pie_fig:
                pie_path = os.path.join(tmpdir, "pie.png")
                pie_fig.savefig(pie_path, dpi=150, bbox_inches='tight', facecolor='white')
                plt.close(pie_fig)

                if os.path.exists(pie_path):
                    self.image(pie_path, x=30, w=150)

        shutil.rmtree(tmpdir, ignore_errors=True)
        self.ln(5)

    def add_table_section(self, title, df):
        """Tabela estilizada com cores alternadas."""
        self.add_page()
        self.add_section_title(title, 'Dados detalhados')

        if df is None or df.empty:
            self.set_font(self.font_name, 'I', 10)
            self.set_text_color(128)
            self.cell(0, 8, 'Sem dados disponíveis.', ln=True)
            return

        available_width = 180
        num_cols = len(df.columns)
        col_width = available_width / num_cols

        # ===== CABEÇALHO =====
        header_y = self.get_y()
        self.set_fill_color(*self.primary)
        self.rect(15, header_y, available_width, 10, 'F')

        self.set_font(self.font_name, 'B', 9)
        self.set_text_color(255, 255, 255)
        self.set_xy(15, header_y + 2)

        for col in df.columns:
            header = self.clean_text(str(col)[:30])
            self.cell(col_width, 7, header, align='C')
        self.ln(10)

        # ===== DADOS =====
        self.set_font(self.font_name, '', 8)

        for idx, (_, row) in enumerate(df.iterrows()):
            # Alternar cores
            if idx % 2 == 0:
                self.set_fill_color(250, 250, 250)
            else:
                self.set_fill_color(255, 255, 255)

            y_row = self.get_y()
            self.rect(15, y_row, available_width, 8, 'F')

            # Borda inferior
            self.set_draw_color(230)
            self.set_line_width(0.1)
            self.line(15, y_row + 8, 15 + available_width, y_row + 8)

            self.set_xy(15, y_row + 1)
            self.set_text_color(50)

            for i, col in enumerate(df.columns):
                value = row[col]
                if isinstance(value, (int, float)):
                    display = f"{value:,.0f}" if value == int(value) else f"{value:,.1f}"
                else:
                    display = self.clean_text(str(value)[:40])

                align = 'C' if i > 0 else 'L'
                self.cell(col_width, 6, display, align=align)
            self.ln(8)

        self.ln(5)

    def add_recommendations_section(self, recommendations):
        """Recomendações com ícones e cores."""
        self.add_page()
        self.add_section_title('Recomendações', 'Ações sugeridas baseadas na análise')

        for rec in recommendations:
            rec_clean = self.clean_text(rec)

            # Determinar cor baseada no prefixo
            if rec.startswith("🔴"):
                color = (220, 50, 50)
                icon = "!"
            elif rec.startswith("🟡"):
                color = (230, 150, 20)
                icon = "!"
            elif rec.startswith("💻") or rec.startswith("👤"):
                color = self.primary
                icon = "i"
            elif rec.startswith("🔧"):
                color = self.secondary
                icon = "i"
            else:
                color = self.primary
                icon = "i"

            # Caixa de recomendação
            y_start = self.get_y()

            # Fundo
            self.set_fill_color(252, 252, 252)
            self.set_draw_color(*color)
            self.set_line_width(0.2)

            # Calcular altura
            self.set_font(self.font_name, '', 9)
            lines = self.multi_cell(165, 6, rec_clean, dry_run=True, output='LINES')
            box_height = max(15, len(lines) * 6 + 8)

            self.rect(15, y_start, 180, box_height, 'DF')

            # Barra lateral
            self.set_fill_color(*color)
            self.rect(15, y_start, 4, box_height, 'F')

            # Ícone
            self.set_xy(23, y_start + (box_height - 8) / 2)
            self.set_font(self.font_name, 'B', 11)
            self.set_text_color(*color)
            self.cell(8, 8, icon, align='C')

            # Texto
            self.set_xy(33, y_start + 4)
            self.set_font(self.font_name, '', 9)
            self.set_text_color(50)
            self.multi_cell(155, 6, rec_clean)

            self.set_y(y_start + box_height + 3)

        self.ln(5)

    def add_computer_investigation_section(self, df_computers, investigations):
        """Seção de investigação de computadores estilizada."""
        self.add_page()
        self.add_section_title('Investigação de Computadores',
                              'Análise detalhada dos equipamentos afetados')

        if df_computers is None or df_computers.empty:
            self.set_font(self.font_name, 'I', 10)
            self.set_text_color(128)
            self.cell(0, 8, 'Sem dados de computadores disponíveis.', ln=True)
            return

        col_widths = [65, 30, 85]
        available_width = sum(col_widths)

        # Cabeçalho
        header_y = self.get_y()
        self.set_fill_color(*self.primary)
        self.rect(15, header_y, available_width, 12, 'F')

        self.set_font(self.font_name, 'B', 9)
        self.set_text_color(255, 255, 255)
        self.set_xy(15, header_y + 2)
        self.cell(col_widths[0], 8, 'Computador', align='C')
        self.cell(col_widths[1], 8, 'Eventos', align='C')
        self.cell(col_widths[2], 8, 'Investigação', align='C')
        self.ln(12)

        # Dados
        self.set_font(self.font_name, '', 8)

        for idx, (_, row) in enumerate(df_computers.iterrows()):
            computer = self.clean_text(str(row.get('computer_name', ''))[:35])
            events = row.get('event_count', 0)
            computer_key = row.get('computer_name', '')
            investigation = self.clean_text(
                investigations.get(computer_key, '')[:60]
            )

            # Alternar cores
            if idx % 2 == 0:
                self.set_fill_color(250, 250, 250)
            else:
                self.set_fill_color(255, 255, 255)

            y_row = self.get_y()

            # Calcular altura necessária para investigação
            self.set_font(self.font_name, '', 8)
            if investigation:
                lines = self.multi_cell(col_widths[2] - 4, 6, investigation,
                                       dry_run=True, output='LINES')
                row_height = max(10, len(lines) * 6 + 4)
            else:
                row_height = 10

            # Fundo
            self.rect(15, y_row, available_width, row_height, 'F')

            # Borda
            self.set_draw_color(230)
            self.line(15, y_row + row_height, 15 + available_width, y_row + row_height)

            # Computador
            self.set_xy(15, y_row + 2)
            self.set_font(self.font_name, 'B', 8)
            self.set_text_color(50)
            self.cell(col_widths[0], 6, computer, align='C')

            # Eventos
            self.set_font(self.font_name, '', 8)
            self.cell(col_widths[1], 6, f"{events:,}", align='C')

            # Investigação
            if investigation:
                self.set_font(self.font_name, '', 7)
                self.multi_cell(col_widths[2] - 4, 6, investigation, align='L')
            else:
                self.set_font(self.font_name, 'I', 7)
                self.set_text_color(180)
                self.cell(col_widths[2], 6, 'Sem investigação registrada', align='L')
                self.set_text_color(50)

            self.set_y(y_row + row_height)

        self.ln(5)

    def get_pdf_bytes(self):
        """Gera o PDF e retorna como bytes."""
        pdf_content = self.output(dest='S')

        if isinstance(pdf_content, bytearray):
            return bytes(pdf_content)
        elif isinstance(pdf_content, str):
            return pdf_content.encode('latin-1')
        elif isinstance(pdf_content, bytes):
            return pdf_content
        else:
            return bytes(pdf_content)
