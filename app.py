import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

from core.validator import validate_uploaded_files, get_available_analyses
from core.processor import process_data
from core.plotter import create_bar_chart, create_pie_chart, create_distribution_chart
from export.pdf_generator import CyberReportPDF
from export.html_generator import CyberReportHTML
from core.config_manager import ConfigManager

# Configuração da página
st.set_page_config(
    page_title="Gerador de Relatórios de Cibersegurança",
    page_icon="🛡️",
    layout="wide"
)

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def page_configuration():
    """Etapa: Configuração de Arquivos CSV."""
    st.header("⚙️ Configuração de Arquivos CSV")

    # Usar ConfigManager importado
    config_manager = ConfigManager()
    configs = config_manager.get_all_configs()

    # ===== LISTAR CONFIGURAÇÕES EXISTENTES =====
    st.subheader("📄 Arquivos Configurados")

    if configs:
        for file_pattern, config in configs.items():
            with st.expander(f"📄 {file_pattern}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Descrição:** {config.get('description', 'N/A')}")
                    st.markdown(f"**Palavras-chave:** {', '.join(config.get('keywords', []))}")
                    st.markdown("**Mapeamento de Colunas:**")

                    for standard_name, csv_names in config.get('columns', {}).items():
                        st.write(f"- `{standard_name}` ← `{', '.join(csv_names)}`")

                with col2:
                    if st.button("🗑️ Remover", key=f"remove_{file_pattern}"):
                        config_manager.remove_file_config(file_pattern)
                        st.success("✅ Removido!")
                        st.rerun()
    else:
        st.info("Nenhum arquivo configurado ainda.")

    st.markdown("---")

    # ===== ADICIONAR NOVO ARQUIVO =====
    st.subheader("➕ Adicionar Novo Arquivo CSV")

    tab1, tab2 = st.tabs(["📤 Upload para Auto-detecção", "✍️ Configuração Manual"])

    with tab1:
        st.markdown("Faça upload de um CSV de exemplo para auto-detectar as colunas.")

        uploaded_file = st.file_uploader("Arquivo CSV de exemplo", type='csv', key='config_upload')

        if uploaded_file:
            suggestions, columns = config_manager.auto_suggest(uploaded_file)
            suggested_keywords = config_manager.suggest_keywords(uploaded_file.name)

            st.success(f"✅ Arquivo analisado! {len(columns)} coluna(s) encontrada(s).")

            # Mostrar sugestões
            st.markdown("### 🔍 Sugestões Automáticas")
            st.markdown(f"**Palavras-chave sugeridas:** {', '.join(suggested_keywords)}")

            with st.form("auto_config_form"):
                file_pattern = st.text_input(
                    "Nome padrão do arquivo",
                    value=uploaded_file.name
                )

                description = st.text_input(
                    "Descrição (opcional)",
                    placeholder="ex: Top 10 Ameaças Detectadas"
                )

                keywords_input = st.text_input(
                    "Palavras-chave (separadas por vírgula)",
                    value=', '.join(suggested_keywords),
                    help="Usadas para identificar automaticamente o arquivo"
                )

                st.markdown("### 📊 Mapeamento de Colunas")
                st.markdown("Confirme ou ajuste o mapeamento:")

                column_mapping = {}

                for col in columns:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Coluna no CSV:** `{col}`")

                    with col2:
                        standard_options = [
                            'Ignorar',
                            'user_name',
                            'computer_name',
                            'rule_name',
                            'action_taken',
                            'event_count',
                            'violation_count',
                            'severity',
                            'date',
                            'status',
                            'category'
                        ]

                        default_index = 0
                        if col in suggestions:
                            standard_name = suggestions[col]
                            if standard_name in standard_options:
                                default_index = standard_options.index(standard_name)

                        selected = st.selectbox(
                            "Mapear para:",
                            standard_options,
                            index=default_index,
                            key=f"auto_map_{col}"
                        )

                        if selected != 'Ignorar':
                            column_mapping[selected] = [col]

                if st.form_submit_button("💾 Salvar Configuração"):
                    if file_pattern and keywords_input and column_mapping:
                        keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
                        config_manager.add_file_config(
                            file_pattern,
                            keywords,
                            column_mapping,
                            description
                        )
                        st.success("✅ Configuração salva com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos obrigatórios!")

    with tab2:
        st.markdown("Configure manualmente sem fazer upload.")

        with st.form("manual_config_form"):
            file_pattern = st.text_input(
                "Nome padrão do arquivo",
                placeholder="ex: Novo_Arquivo.csv"
            )

            description = st.text_input(
                "Descrição (opcional)",
                placeholder="ex: Dados de firewall"
            )

            keywords_input = st.text_input(
                "Palavras-chave (separadas por vírgula)",
                placeholder="ex: firewall, security, logs"
            )

            st.markdown("### 📊 Mapeamento de Colunas")
            st.markdown("Adicione manualmente o mapeamento:")

            num_cols = st.number_input(
                "Quantidade de colunas para mapear",
                min_value=1,
                max_value=10,
                value=2
            )

            column_mapping = {}

            for i in range(int(num_cols)):
                st.markdown(f"**Coluna {i+1}:**")
                col1, col2 = st.columns(2)

                with col1:
                    standard_name = st.text_input(
                        "Nome padrão (interno)",
                        placeholder="ex: event_count",
                        key=f"manual_std_{i}"
                    )

                with col2:
                    csv_names = st.text_input(
                        "Nomes no CSV (separados por vírgula)",
                        placeholder="ex: Total Eventos, Count",
                        key=f"manual_csv_{i}"
                    )

                if standard_name and csv_names:
                    column_mapping[standard_name] = [
                        name.strip() for name in csv_names.split(',') if name.strip()
                    ]

            if st.form_submit_button("💾 Salvar Configuração"):
                if file_pattern and keywords_input and column_mapping:
                    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
                    config_manager.add_file_config(
                        file_pattern,
                        keywords,
                        column_mapping,
                        description
                    )
                    st.success("✅ Configuração salva!")
                    st.rerun()
                else:
                    st.error("Preencha todos os campos!")


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

def save_report_history(client_name, metrics, dataframes_keys, period):
    """Salva histórico do relatório gerado."""
    history_dir = "data/history"
    os.makedirs(history_dir, exist_ok=True)

    history_file = os.path.join(history_dir, f"{client_name}_history.json")

    # Carregar histórico existente
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    # Criar entrada
    entry = {
        'date': datetime.now().isoformat(),
        'period': period,
        'metrics': {},
        'files': dataframes_keys
    }

    # Copiar métricas serializáveis
    for k, v in metrics.items():
        if isinstance(v, (int, float, str, bool)):
            entry['metrics'][k] = v

    history.append(entry)

    # Salvar
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return history


def load_report_history(client_name):
    """Carrega histórico de relatórios do cliente."""
    history_file = os.path.join("data/history", f"{client_name}_history.json")
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

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

    if 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
        st.warning("⚠️ Nenhum arquivo enviado. Volte para a etapa 2.")
        if st.button("⬅️ Voltar para Upload", key="btn_voltar_upload_vazio"):
            st.session_state.step = 2
            st.rerun()
        return

    with st.spinner("🔍 Analisando arquivos..."):
        dataframes, found_files, warnings, errors = validate_uploaded_files(
            st.session_state.uploaded_files
        )

    for w in warnings:
        if w.startswith("✅"):
            st.success(w)
        elif w.startswith("⚠️"):
            st.warning(w)
        else:
            st.info(w)

    for e in errors:
        st.error(e)

    if dataframes:
        st.session_state.dataframes = dataframes

        st.success(f"✅ {len(dataframes)} arquivo(s) processado(s) com sucesso!")

        for pattern, df in dataframes.items():
            with st.expander(f"📄 {pattern} ({len(df)} linhas)"):
                st.dataframe(df.head(10), use_container_width=True)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Revalidar", key="btn_revalidar"):
                st.rerun()
        with col2:
            if st.button("▶️ Processar Dados e Gerar Análise",
                        key="btn_processar_analise",
                        type="primary"):
                with st.spinner("⚙️ Processando..."):
                    processed = process_data(dataframes)

                st.session_state.processed_data = processed

                save_report_history(
                    st.session_state.client_selected,
                    processed,
                    list(dataframes.keys()),
                    datetime.now().strftime('%Y-%m')
                )

                st.success("✅ Dados processados com sucesso!")
                st.session_state.step = 4
                st.rerun()
    else:
        st.error("❌ Nenhum arquivo pôde ser processado.")
        if st.button("⬅️ Voltar para Upload", key="btn_voltar_upload_erro"):
            st.session_state.step = 2
            st.rerun()

def page_analysis():
    """Etapa 4: Visualização da Análise."""
    st.header("📊 Análise dos Dados")

    if not st.session_state.processed_data:
        st.warning("⚠️ Dados não processados. Execute a etapa 3.")
        return

    data = st.session_state.processed_data

    # Debug
    st.write("Debug - Dados processados:")
    st.write(f"Total eventos: {data.get('total_events', 'N/D')}")
    st.write(f"Charts: {list(data.get('charts', {}).keys())}")
    st.write(f"Tables: {list(data.get('tables', {}).keys())}")

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
        kpi_data.append(("Violações", data['total_violations']))

    if kpi_data:
        cols = st.columns(min(4, len(kpi_data)))
        for i, (label, value) in enumerate(kpi_data):
            with cols[i % len(cols)]:
                st.metric(label, f"{value:,}")
    else:
        st.info("Nenhuma métrica disponível.")

    # Tabelas
    tables = data.get('tables', {})
    if tables:
        st.subheader("📋 Dados Processados")
        for name, df in tables.items():
            with st.expander(f"📄 {name} ({len(df)} registros)"):
                st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma tabela disponível.")

    # Navegação
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Voltar", key="btn_voltar_analysis"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("📄 Gerar Relatório ▶️", type="primary"):
            st.session_state.step = 5
            st.rerun()

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

    # ===== DEFINIÇÃO DAS ETAPAS =====
    steps = {
        1: "📋 Clientes",
        2: "📁 Upload",
        3: "🔍 Processar",
        4: "📊 Análise",
        5: "📄 Relatório",
        6: "⚙️ Configuração"
    }

    step = st.sidebar.radio(
        "Etapas",
        list(steps.keys()),
        format_func=lambda x: steps[x]
    )

    st.session_state.step = step

    st.sidebar.markdown("---")
    st.sidebar.info("Gerador de relatórios de cibersegurança")

    # ===== RENDERIZAR PÁGINA =====
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
    elif step == 6:
        page_configuration()

if __name__ == "__main__":
    main()
