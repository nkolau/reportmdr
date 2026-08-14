import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

from core.validator import validate_uploaded_files
from core.processor import process_data
from core.plotter import create_bar_chart, create_pie_chart, create_distribution_chart
from core.analyzer import save_report_history, load_report_history, compare_with_previous
from export.pdf_generator import CyberReportPDF

# Configuração da página
st.set_page_config(
    page_title="Gerador de Relatórios de Cibersegurança",
    page_icon="🛡️",
    layout="wide"
)

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def load_clients():
    """Carrega clientes do arquivo JSON."""
    clients_file = os.path.join("config", "clients.json")
    if os.path.exists(clients_file):
        with open(clients_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"default": {"client_name": "Cliente Padrão", "company_name": "Sua Consultoria", "logo_path": "", "primary_color": "#1f77b4", "secondary_color": "#ff7f0e"}}


def save_clients(clients):
    """Salva clientes no arquivo JSON."""
    clients_file = os.path.join("config", "clients.json")
    os.makedirs(os.path.dirname(clients_file), exist_ok=True)
    with open(clients_file, 'w', encoding='utf-8') as f:
        json.dump(clients, f, indent=2, ensure_ascii=False)


def init_session_state():
    """Inicializa variáveis de sessão."""
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'client_selected' not in st.session_state:
        st.session_state.client_selected = 'default'
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = None
    if 'dataframes' not in st.session_state:
        st.session_state.dataframes = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'investigations' not in st.session_state:
        st.session_state.investigations = {}


# =============================================
# PÁGINAS
# =============================================

def page_select_client():
    """Etapa 1: Selecionar/Criar Cliente."""
    st.header("Gestão de Clientes")

    clients = load_clients()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Selecionar Cliente")
        client_names = list(clients.keys())

        if client_names:
            selected = st.selectbox(
                "Cliente",
                client_names,
                format_func=lambda x: clients[x].get('client_name', x)
            )
            st.session_state.client_selected = selected
            client = clients[selected]

            with st.expander("Editar Cliente", expanded=True):
                with st.form("edit_client"):
                    client['client_name'] = st.text_input("Nome do Cliente", value=client.get('client_name', ''))

                    # Upload de logo do cliente (persistente)
                    logo_file = st.file_uploader("Logo do Cliente", type=['png', 'jpg', 'jpeg'])
                    if logo_file:
                        logo_dir = os.path.join("data", "logos")
                        os.makedirs(logo_dir, exist_ok=True)
                        logo_path = os.path.join(logo_dir, f"{selected}_logo.png")
                        with open(logo_path, 'wb') as f:
                            f.write(logo_file.getbuffer())
                        client['logo_path'] = logo_path
                        st.success("Logo salvo!")
                    elif client.get('logo_path') and os.path.exists(client['logo_path']):
                        st.image(client['logo_path'], width=100, caption="Logo atual")

                    if st.form_submit_button("Salvar"):
                        clients[selected] = client
                        save_clients(clients)
                        st.success("Cliente atualizado!")
                        st.rerun()

    with col2:
        st.subheader("Novo Cliente")
        with st.form("new_client"):
            new_name = st.text_input("Identificador", placeholder="ex: empresa_abc")
            new_client_name = st.text_input("Nome do Cliente", placeholder="ex: Empresa ABC")

            # Upload de logo
            new_logo = st.file_uploader("Logo do Cliente", type=['png', 'jpg', 'jpeg'])

            if st.form_submit_button("Criar"):
                if new_name and new_client_name:
                    logo_path = ""
                    if new_logo:
                        logo_dir = os.path.join("data", "logos")
                        os.makedirs(logo_dir, exist_ok=True)
                        logo_path = os.path.join(logo_dir, f"{new_name}_logo.png")
                        with open(logo_path, 'wb') as f:
                            f.write(new_logo.getbuffer())

                    clients[new_name] = {
                        "client_name": new_client_name,
                        "logo_path": logo_path,
                        "primary_color": "#1a1a1a",
                        "secondary_color": "#8B0000",
                        "accent_color": "#808080",
                        "company_name": "NetsafeCorp",
                        "company_logo_path": "data/logos/netsafecorp_logo.png"
                    }
                    save_clients(clients)
                    st.success(f"Cliente '{new_client_name}' criado!")
                    st.rerun()


def page_upload():
    """Etapa 2: Upload dos CSVs."""
    st.header("📁 Upload dos Arquivos CSV")

    st.info("""
    **Arquivos esperados** (nomes padronizados):
    - `Action_Cyber_Threats.csv`
    - `Top_10_Users.csv`
    - `Regras_exploit_prevention_-_Playbook_Trellix_Insights.csv`
    - `Top_10_Computers.csv`
    - `Top_10_regras_de_Prevencao_de_Exploracao_violadas.csv`
    """)

    uploaded_files = st.file_uploader(
        "Selecione os arquivos CSV",
        type=['csv'],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")

        with st.expander("📋 Arquivos"):
            for f in uploaded_files:
                st.write(f"- {f.name}")

        st.session_state.uploaded_files = uploaded_files

        if st.button("▶️ Processar Arquivos", type="primary"):
            st.session_state.step = 3
            st.rerun()


def page_process():
    """Etapa 3: Validação e Processamento."""
    st.header("🔍 Processamento dos Dados")

    if not st.session_state.uploaded_files:
        st.warning("Nenhum arquivo enviado. Volte para etapa 2.")
        if st.button("⬅️ Voltar"):
            st.session_state.step = 2
            st.rerun()
        return

    with st.spinner("Processando..."):
        dataframes, warnings, errors = validate_uploaded_files(st.session_state.uploaded_files)

    # Mostrar resultados
    for w in warnings:
        if w.startswith("✅"):
            st.success(w)
        else:
            st.warning(w)

    for e in errors:
        st.error(e)

    if dataframes:
        st.session_state.dataframes = dataframes

        if st.button("▶️ Gerar Análise", type="primary"):
            with st.spinner("Calculando métricas..."):
                processed = process_data(dataframes)

            st.session_state.processed_data = processed

            # Salvar histórico
            period = datetime.now().strftime('%Y-%m')
            save_report_history(
                st.session_state.client_selected,
                processed,
                list(dataframes.keys()),
                period
            )

            st.success("✅ Análise concluída!")
            st.session_state.step = 4
            st.rerun()


def page_analysis():
    """Etapa 4: Visualização da Análise."""
    st.header("📊 Análise dos Dados")

    if not st.session_state.processed_data:
        st.warning("Dados não processados. Execute etapa 3.")
        return

    data = st.session_state.processed_data

    # KPIs
    st.subheader("📈 Indicadores")

    kpi_data = []
    if 'total_events' in data:
        kpi_data.append(("Total de Eventos", data['total_events']))
    if 'total_actions' in data:
        kpi_data.append(("Ações do Antivírus", data['total_actions']))
    if 'total_computers' in data:
        kpi_data.append(("Computadores", data['total_computers']))
    if 'total_users' in data:
        kpi_data.append(("Usuários", data['total_users']))
    if 'total_violations' in data:
        kpi_data.append(("Violações de Regras", data['total_violations']))
    if 'total_playbook_events' in data:
        kpi_data.append(("Eventos do Playbook", data['total_playbook_events']))

    if kpi_data:
        cols = st.columns(min(4, len(kpi_data)))
        for i, (label, value) in enumerate(kpi_data):
            with cols[i % len(cols)]:
                st.metric(label, f"{value:,}")

    st.markdown("---")

    # ===== GRÁFICOS INTERATIVOS (Plotly para visualização) =====
    charts = data.get('charts', {})

    if charts:
        st.subheader("📊 Gráficos")

        # Criar tabs para cada gráfico
        chart_items = list(charts.items())

        # Mostrar em grid 2x2
        for i in range(0, len(chart_items), 2):
            col1, col2 = st.columns(2)

            with col1:
                if i < len(chart_items):
                    key, info = chart_items[i]

                    # Gráfico de barras interativo (Plotly)
                    fig_bar = create_bar_chart(
                        info['data'],
                        info['label_col'],
                        info['value_col'],
                        info['title']
                    )
                    if fig_bar:
                        st.plotly_chart(fig_bar, use_container_width=True)

                    # Gráfico de pizza interativo (Plotly)
                    fig_pie = create_pie_chart(
                        info['data'],
                        info['label_col'],
                        info['value_col'],
                        f"Distribuição - {info['title']}"
                    )
                    if fig_pie:
                        st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                if i + 1 < len(chart_items):
                    key, info = chart_items[i + 1]

                    fig_bar = create_bar_chart(
                        info['data'],
                        info['label_col'],
                        info['value_col'],
                        info['title']
                    )
                    if fig_bar:
                        st.plotly_chart(fig_bar, use_container_width=True)

                    fig_pie = create_pie_chart(
                        info['data'],
                        info['label_col'],
                        info['value_col'],
                        f"Distribuição - {info['title']}"
                    )
                    if fig_pie:
                        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # ===== TABELAS =====
    tables = data.get('tables', {})

    if tables:
        st.subheader("📋 Tabelas de Dados")

        table_names = list(tables.keys())
        if len(table_names) > 1:
            table_tabs = st.tabs(table_names)
            for tab, (name, df) in zip(table_tabs, tables.items()):
                with tab:
                    st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            name = table_names[0]
            st.dataframe(tables[name], use_container_width=True, hide_index=True)

    st.markdown("---")

    # ===== SEÇÃO DE INVESTIGAÇÃO DE COMPUTADORES =====
    if 'computers' in tables:
        st.subheader("🔍 Investigação de Computadores")
        st.info("Adicione notas de investigação para cada computador. Estas serão incluídas no relatório PDF.")

        df_computers = tables['computers']

        # Carregar investigações existentes
        if 'investigations' not in st.session_state:
            st.session_state.investigations = {}

        # Criar campos de texto para cada computador
        for _, row in df_computers.iterrows():
            computer = row['computer_name']
            events = row['event_count']

            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"**{computer}**")
                st.write(f"({events:,} eventos)")
            with col2:
                current_value = st.session_state.investigations.get(computer, '')
                new_value = st.text_area(
                    f"Investigação para {computer}",
                    value=current_value,
                    key=f"investigation_{computer}",
                    height=60,
                    placeholder="Descreva os resultados da investigação deste computador..."
                )
                st.session_state.investigations[computer] = new_value

    st.markdown("---")

    # ===== RECOMENDAÇÕES =====
    if data.get('recommendations'):
        st.subheader("💡 Recomendações")
        for rec in data['recommendations']:
            if rec.startswith("🔴"):
                st.error(rec)
            elif rec.startswith("🟡"):
                st.warning(rec)
            elif rec.startswith("💻") or rec.startswith("👤") or rec.startswith("🔧"):
                st.info(rec)
            else:
                st.write(f"- {rec}")

    # ===== NAVEGAÇÃO =====
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Voltar"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("📄 Gerar Relatório PDF ▶️", type="primary"):
            st.session_state.step = 5
            st.rerun()


def page_export():
    """Etapa 5: Exportação do Relatório."""
    st.header("📄 Geração do Relatório")

    if not st.session_state.processed_data:
        st.warning("Dados não processados.")
        return

    data = st.session_state.processed_data
    clients = load_clients()
    client = clients.get(st.session_state.client_selected, {})

    period = datetime.now().strftime('%B/%Y')

    st.info(f"""
    **Relatório para:**
    - Cliente: {client.get('client_name', 'N/D')}
    - Empresa: {client.get('company_name', 'N/D')}
    - Período: {period}
    """)

    # ===== OPÇÕES DE EXPORTAÇÃO =====
    st.subheader("📤 Formato de Exportação")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🌐 HTML (Recomendado)")
        st.markdown("*Visual moderno e interativo*")

        if st.button("🔄 Gerar HTML", type="primary"):
            with st.spinner("Gerando relatório HTML..."):
                try:
                    from export.html_generator import CyberReportHTML

                    html_generator = CyberReportHTML(client, period)
                    html_content = html_generator.generate(
                        data,
                        st.session_state.investigations
                    )

                    # Salvar HTML
                    filename = f"relatorio_{client.get('client_name', 'cliente')}_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
                    filename = filename.replace(' ', '_')

                    st.success("✅ Relatório HTML gerado!")
                    st.download_button(
                        "📥 Baixar HTML",
                        data=html_content.encode('utf-8'),
                        file_name=filename,
                        mime="text/html"
                    )

                    # Preview
                    with st.expander("👁️ Visualizar Relatório", expanded=True):
                        st.components.v1.html(html_content, height=600, scrolling=True)

                except Exception as e:
                    st.error(f"Erro ao gerar HTML: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

    with col2:
        st.markdown("### 📄 PDF (Tradicional)")
        st.markdown("*Para impressão e compartilhamento*")

        if st.button("🔄 Gerar PDF"):
            with st.spinner("Gerando relatório PDF..."):
                try:
                    pdf = CyberReportPDF(client, period)
                    # ... (código existente do PDF)
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")


# =============================================
# APLICAÇÃO PRINCIPAL
# =============================================

def main():
    init_session_state()

    # Sidebar
    st.sidebar.title("🛡️ Cyber Report")
    st.sidebar.markdown("---")

    steps = {
        1: "📋 Clientes",
        2: "📁 Upload",
        3: "🔍 Processar",
        4: "📊 Análise",
        5: "📄 Relatório"
    }

    step = st.sidebar.radio("Etapas", list(steps.keys()), format_func=lambda x: steps[x])
    st.session_state.step = step

    st.sidebar.markdown("---")
    st.sidebar.info("Gerador de relatórios de cibersegurança")

    # Renderizar página
    if step == 1:
        page_select_client()
    elif step == 2:
        page_upload()
    elif step == 3:
        page_process()
    elif step == 4:
        page_analysis()
    elif step == 5:
        page_export()


if __name__ == "__main__":
    main()
