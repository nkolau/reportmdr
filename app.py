import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from core.validator import validate_uploaded_files, get_available_analyses
from core.processor import process_data
from core.plotter import create_bar_chart, create_pie_chart, create_distribution_chart
from export.html_generator import CyberReportHTML
from export.annual_html_generator import AnnualReportHTML
from core.config_manager import ConfigManager
from core.history_manager import HistoryManager

# Configuração da página Streamlit
st.set_page_config(
    page_title="Gerador & Editor de Relatórios MDR",
    page_icon="🛡️",
    layout="wide"
)

# =============================================
# FUNÇÕES AUXILIARES & DATAS
# =============================================

def set_step(step_number):
    """Atualiza a navegação de etapas de forma sincronizada."""
    st.session_state.target_step = step_number
    st.rerun()


def get_default_period():
    """Retorna o mês anterior no formato 'Mês/Ano' (ex: 'Agosto/2026')."""
    today = date.today()
    last_month = today - relativedelta(months=1)
    months_pt = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    return f"{months_pt[last_month.month - 1]}/{last_month.year}"


def load_clients():
    """Carrega clientes do arquivo JSON."""
    clients_file = os.path.join("config", "clients.json")
    if os.path.exists(clients_file):
        try:
            with open(clients_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "default": {
            "client_name": "Cliente Demonstração",
            "company_name": "NetsafeCorp",
            "logo_path": "",
            "company_logo_path": "data/logos/netsafecorp_logo.png",
            "primary_color": "#0f172a",
            "secondary_color": "#8B0000",
            "accent_color": "#3b82f6"
        }
    }


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
    if 'current_html_report' not in st.session_state:
        st.session_state.current_html_report = None


# =============================================
# PÁGINAS PRINCIPAIS
# =============================================

def page_select_client():
    """Etapa 1: Selecionar/Criar Cliente."""
    st.header("📋 Gestão de Clientes")

    clients = load_clients()
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Selecionar Cliente Existente")
        client_names = list(clients.keys())

        if client_names:
            selected = st.selectbox(
                "Cliente",
                client_names,
                format_func=lambda x: clients[x].get('client_name', x)
            )
            st.session_state.client_selected = selected
            client = clients[selected]

            with st.expander("✏️ Editar Dados do Cliente", expanded=True):
                with st.form("edit_client"):
                    client['client_name'] = st.text_input("Nome do Cliente", value=client.get('client_name', ''))
                    client['company_name'] = st.text_input("Nome da Consultoria / Empresa SOC", value=client.get('company_name', 'NetsafeCorp'))

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        client['primary_color'] = st.color_picker("Cor Primária (Fundo/Bordas)", value=client.get('primary_color', '#0f172a'))
                    with c2:
                        client['secondary_color'] = st.color_picker("Cor Secundária (Vinho/Destaque)", value=client.get('secondary_color', '#8B0000'))
                    with c3:
                        client['accent_color'] = st.color_picker("Cor de Acento (Azul/Ciano)", value=client.get('accent_color', '#3b82f6'))

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
                        st.image(client['logo_path'], width=120, caption="Logo Atual do Cliente")

                    if st.form_submit_button("💾 Salvar Alterações"):
                        clients[selected] = client
                        save_clients(clients)
                        st.success("✅ Dados do cliente atualizados!")
                        st.rerun()

    with col2:
        st.subheader("➕ Novo Cliente")
        with st.form("new_client"):
            new_id = st.text_input("Identificador (sem espaços)", placeholder="ex: cliente_xyz")
            new_client_name = st.text_input("Nome de Exibição", placeholder="ex: Grupo XYZ S.A.")
            new_logo = st.file_uploader("Logo do Cliente", type=['png', 'jpg', 'jpeg'], key="new_client_logo")

            if st.form_submit_button("✨ Criar Cliente"):
                if new_id and new_client_name:
                    logo_path = ""
                    if new_logo:
                        logo_dir = os.path.join("data", "logos")
                        os.makedirs(logo_dir, exist_ok=True)
                        logo_path = os.path.join(logo_dir, f"{new_id}_logo.png")
                        with open(logo_path, 'wb') as f:
                            f.write(new_logo.getbuffer())

                    clients[new_id] = {
                        "client_name": new_client_name,
                        "logo_path": logo_path,
                        "company_name": "NetsafeCorp",
                        "company_logo_path": "data/logos/netsafecorp_logo.png",
                        "primary_color": "#0f172a",
                        "secondary_color": "#8B0000",
                        "accent_color": "#3b82f6"
                    }
                    save_clients(clients)
                    st.success(f"✅ Cliente '{new_client_name}' cadastrado!")
                    st.session_state.client_selected = new_id
                    st.rerun()


def page_upload():
    """Etapa 2: Upload dos CSVs."""
    st.header("📁 Upload dos Arquivos CSV de Telemetria")

    config_mgr = ConfigManager()
    configs = config_mgr.get_all_configs()

    st.markdown("Envie os arquivos CSV do período para geração do relatório executivo:")
    
    with st.expander("📋 Arquivos esperados / configurados", expanded=False):
        for pattern, cfg in configs.items():
            st.markdown(f"- **`{pattern}`**: {cfg.get('title', pattern)} — *{cfg.get('description', '')}*")

    uploaded_files = st.file_uploader(
        "Selecione os arquivos CSV",
        type=['csv'],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
        with st.expander("Arquivos selecionados", expanded=True):
            for f in uploaded_files:
                st.write(f"📄 `{f.name}`")

        st.session_state.uploaded_files = uploaded_files

        if st.button("▶️ Processar Arquivos", type="primary", use_container_width=True):
            set_step(3)


def page_process():
    """Etapa 3: Validação e Processamento."""
    st.header("🔍 Validação e Processamento dos Dados")

    if not st.session_state.get('uploaded_files'):
        st.warning("⚠️ Nenhum arquivo enviado. Retorne à etapa anterior.")
        if st.button("⬅️ Voltar para Upload"):
            set_step(2)
        return

    with st.spinner("🔍 Validando formato dos arquivos e colunas..."):
        dataframes, warnings, errors = validate_uploaded_files(st.session_state.uploaded_files)

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

        with st.expander("👁️ Prévia dos Dados Processados", expanded=False):
            for pattern, df in dataframes.items():
                st.markdown(f"**📄 {pattern}** ({len(df)} registros)")
                st.dataframe(df.head(5), use_container_width=True)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Revalidar"):
                st.rerun()
        with col2:
            if st.button("▶️ Consolidar Métricas e Ir para Análise", type="primary"):
                with st.spinner("⚙️ Processando métricas e associando enunciados..."):
                    processed = process_data(dataframes)
                st.session_state.processed_data = processed

                st.success("✅ Métricas e enunciados consolidados!")
                set_step(4)


def page_analysis():
    """Etapa 4: Análise & Investigação."""
    st.header("📊 Análise das Métricas e Investigações")

    if not st.session_state.get('processed_data'):
        st.warning("⚠️ Dados ainda não processados. Execute a etapa de processamento.")
        return

    data = st.session_state.processed_data

    # Indicadores
    st.subheader("📈 Resumo dos Indicadores")
    kpis = [
        ("Total de Eventos", data.get('total_events', 0)),
        ("Ações do Antivírus", data.get('total_actions', 0)),
        ("Computadores", data.get('total_computers', 0)),
        ("Usuários", data.get('total_users', 0)),
        ("Violações", data.get('total_violations', 0)),
        ("Eventos Playbook", data.get('total_playbook_events', 0))
    ]

    cols = st.columns(len(kpis))
    for i, (lbl, val) in enumerate(kpis):
        with cols[i]:
            st.metric(lbl, f"{val:,}")

    # Visualização de Gráficos Rápidos no Dashboard
    charts = data.get('charts', {})
    if charts:
        st.markdown("---")
        st.subheader("📊 Distribuição Visual das Ocorrências")
        c_keys = list(charts.keys())
        for i in range(0, len(c_keys), 2):
            col_left, col_right = st.columns(2)
            c1_key = c_keys[i]
            c1_item = charts[c1_key]
            with col_left:
                fig1 = create_pie_chart(
                    c1_item.get('data'),
                    c1_item.get('label_col'),
                    c1_item.get('value_col'),
                    c1_item.get('title')
                )
                if fig1:
                    st.plotly_chart(fig1, use_container_width=True)

            if i + 1 < len(c_keys):
                c2_key = c_keys[i + 1]
                c2_item = charts[c2_key]
                with col_right:
                    fig2 = create_pie_chart(
                        c2_item.get('data'),
                        c2_item.get('label_col'),
                        c2_item.get('value_col'),
                        c2_item.get('title')
                    )
                    if fig2:
                        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Investigação de Computadores
    tables = data.get('tables', {})
    if 'computers' in tables:
        st.subheader("🔍 Investigação de Computadores (Endpoints)")
        st.info("Insira observações técnicas e parecer forense para cada endpoint. Elas serão destacadas no relatório exportado.")

        df_comp = tables['computers']
        if 'investigations' not in st.session_state:
            st.session_state.investigations = {}

        for _, row in df_comp.iterrows():
            comp_name = row['computer_name']
            events = row['event_count']

            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"**💻 {comp_name}**")
                st.caption(f"{events:,} eventos registrados")
            with col2:
                curr_val = st.session_state.investigations.get(comp_name, '')
                new_val = st.text_area(
                    f"Parecer para {comp_name}",
                    value=curr_val,
                    key=f"inv_{comp_name}",
                    placeholder="Ex: Host apresentou detecções repetitivas de PowerShell. Varredura completa realizada; credenciais rotacionadas.",
                    height=70
                )
                st.session_state.investigations[comp_name] = new_val

    st.markdown("---")

    # Recomendações
    st.subheader("💡 Recomendações Geradas")
    recs = data.get('recommendations', [])
    for r in recs:
        r_str = str(r)
        if "[ALTA]" in r_str.upper() or r_str.startswith("🔴"):
            st.error(r)
        elif "[MÉDIA]" in r_str.upper() or "[MEDIA]" in r_str.upper() or r_str.startswith("🟡"):
            st.warning(r)
        else:
            st.info(r)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Voltar"):
            set_step(3)
    with col2:
        if st.button("📄 Prosseguir para Exportação ▶️", type="primary"):
            set_step(5)


def page_export():
    """Etapa 5: Geração e Exportação do Relatório."""
    st.header("📄 Geração do Relatório Executivo")

    if not st.session_state.get('processed_data'):
        st.warning("⚠️ Nenhum dado processado.")
        return

    data = st.session_state.processed_data
    clients = load_clients()
    client = clients.get(st.session_state.client_selected, {})

    # Período sempre padrão para o mês anterior
    default_period = get_default_period()
    default_date = datetime.now().strftime('%d/%m/%Y')

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        period_input = st.text_input(
            "📅 Período de Análise (Mês Anterior)",
            value=default_period,
            help="Configurado automaticamente para o mês anterior à data de execução."
        )
    with col_p2:
        date_input = st.text_input(
            "🗓️ Data de Emissão do Relatório",
            value=default_date
        )

    st.info(f"Gerando relatório para **{client.get('client_name', 'Cliente')}** | Período: **{period_input}** | Data: **{date_input}**")

    # Exportação HTML
    st.subheader("🌐 Exportação em HTML Executivo")
    st.markdown("*Layout moderno Dark Executivo, sem emojis, badges de tendência MoM e tabelas com busca interativa.*")

    hist_manager = HistoryManager()
    prev_record = hist_manager.get_previous_month_record(st.session_state.client_selected, period_input)
    prev_metrics = prev_record.get('metrics', {}) if prev_record else None
    mom_deltas = hist_manager.calculate_mom_deltas(data, prev_metrics) if prev_metrics else None

    if prev_record:
        st.info(f"📈 **Comparativo Histórico Identificado:** Encontrado registro anterior de **{prev_record.get('period')}** para cálculo de variações MoM.")

    if st.button("✨ Gerar Relatório HTML", type="primary", use_container_width=True):
        with st.spinner("Gerando HTML de alta fidelidade e persistindo no histórico..."):
            try:
                # Salvar registro do mês atual no histórico
                hist_manager.save_month_record(
                    client_id=st.session_state.client_selected,
                    period_str=period_input,
                    processed_data=data,
                    investigations=st.session_state.investigations
                )

                # Carregar histórico recente para gráficos de tendência
                recent_history = hist_manager.load_client_history(st.session_state.client_selected)

                html_gen = CyberReportHTML(
                    client_config=client,
                    period_str=period_input,
                    generation_date_str=date_input
                )
                html_content = html_gen.generate(
                    data=data,
                    investigations=st.session_state.investigations,
                    mom_deltas=mom_deltas,
                    recent_history=recent_history[-6:] if recent_history else None
                )
                st.session_state.current_html_report = html_content

                filename = f"relatorio_mdr_{client.get('client_name', 'cliente')}_{period_input.replace('/', '_')}.html"
                filename = filename.replace(' ', '_').lower()

                st.success("✅ Relatório HTML gerado e salvo no histórico com sucesso!")

                st.download_button(
                    label="📥 Baixar Relatório HTML",
                    data=html_content.encode('utf-8'),
                    file_name=filename,
                    mime="text/html",
                    use_container_width=True
                )

                with st.expander("👁️ Visualizar Relatório Gerado", expanded=True):
                    st.components.v1.html(html_content, height=650, scrolling=True)

            except Exception as e:
                st.error(f"Erro ao gerar HTML: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def page_modify_html():
    """Etapa 6: Importar e Modificar Relatório HTML existente."""
    st.header("✏️ Modificar Relatório HTML")
    st.markdown("""
    Importe um relatório HTML gerado anteriormente (ou carregue o relatório da sessão atual) 
    para modificar pontualmente **enunciados, títulos, dados de cabeçalho, notas de investigação ou recomendações**.
    """)

    uploaded_html = st.file_uploader("Faça upload do arquivo .html do relatório", type=['html', 'htm'])

    html_source = None
    if uploaded_html is not None:
        html_source = uploaded_html.read().decode('utf-8')
    elif st.session_state.get('current_html_report'):
        st.info("💡 Você possui um relatório recém-gerado na sessão atual. Você pode editá-lo diretamente abaixo ou fazer upload de outro arquivo.")
        if st.checkbox("Usar relatório da sessão atual", value=True):
            html_source = st.session_state.current_html_report

    if not html_source:
        st.info("Envie um arquivo HTML acima para iniciar as modificações.")
        return

    # Extrair metadados embutidos
    meta = CyberReportHTML.extract_metadata(html_source)

    if not meta:
        st.warning("⚠️ Não foi possível extrair metadados automáticos deste HTML. Você pode editar os campos preenchendo as informações abaixo.")
        meta = {
            'client': {'client_name': 'Cliente', 'company_name': 'NetsafeCorp'},
            'period': get_default_period(),
            'generation_date': datetime.now().strftime('%d/%m/%Y'),
            'total_events': 0,
            'total_actions': 0,
            'total_computers': 0,
            'total_users': 0,
            'total_violations': 0,
            'enunciados': {},
            'investigations': {},
            'recommendations': []
        }

    st.success("✅ Relatório carregado para edição!")

    tab_header, tab_kpi, tab_enunciados, tab_inv, tab_recs = st.tabs([
        "📋 Dados Gerais",
        "📊 Indicadores (KPIs)",
        "💡 Enunciados & Títulos",
        "🔍 Investigações",
        "💡 Recomendações"
    ])

    with tab_header:
        col1, col2 = st.columns(2)
        with col1:
            edit_client_name = st.text_input("Nome do Cliente", value=meta.get('client', {}).get('client_name', ''))
            edit_company_name = st.text_input("Nome da Empresa / SOC", value=meta.get('client', {}).get('company_name', 'NetsafeCorp'))
        with col2:
            edit_period = st.text_input("Período (ex: Agosto/2026)", value=meta.get('period', get_default_period()))
            edit_date = st.text_input("Data de Emissão", value=meta.get('generation_date', datetime.now().strftime('%d/%m/%Y')))

    with tab_kpi:
        st.markdown("Ajuste os valores dos cartões de métricas se necessário:")
        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_events = st.number_input("Total de Eventos", value=int(meta.get('total_events', 0)), step=1)
            kpi_actions = st.number_input("Ações do Antivírus", value=int(meta.get('total_actions', 0)), step=1)
        with col2:
            kpi_computers = st.number_input("Computadores Monitorados", value=int(meta.get('total_computers', 0)), step=1)
            kpi_users = st.number_input("Usuários com Detecção", value=int(meta.get('total_users', 0)), step=1)
        with col3:
            kpi_violations = st.number_input("Violações de Regras", value=int(meta.get('total_violations', 0)), step=1)
            kpi_playbook = st.number_input("Eventos de Playbook", value=int(meta.get('total_playbook_events', 0)), step=1)

    with tab_enunciados:
        st.markdown("Edite o texto do enunciado explicativo para cada seção do relatório:")
        charts_meta = meta.get('charts_meta', {})
        enunciados_dict = meta.get('enunciados', {})

        updated_enunciados = {}
        updated_titles = {}

        all_keys = list(set(list(charts_meta.keys()) + list(enunciados_dict.keys()) + ['actions', 'users', 'computers', 'playbook', 'rules_violated']))
        
        section_display_names = {
            'actions': 'Ações Tomadas pelo Antivírus',
            'users': 'Usuários com Mais Detecções',
            'computers': 'Computadores com Mais Detecções',
            'playbook': 'Regras do Playbook Trellix Insights',
            'rules_violated': 'Regras de Prevenção Violadas'
        }

        for k in all_keys:
            default_t = charts_meta.get(k, {}).get('title') or section_display_names.get(k, k.replace('_', ' ').title())
            default_e = charts_meta.get(k, {}).get('enunciado') or enunciados_dict.get(k, '')

            with st.expander(f"Seção: {default_t}", expanded=True):
                new_t = st.text_input(f"Título da Seção ({k})", value=default_t, key=f"edit_t_{k}")
                new_e = st.text_area(f"Enunciado / Contexto ({k})", value=default_e, key=f"edit_e_{k}", height=80)
                updated_titles[k] = new_t
                updated_enunciados[k] = new_e

    with tab_inv:
        st.markdown("Edite as notas de investigação forense para cada endpoint:")
        curr_invs = meta.get('investigations', {})
        updated_invs = {}

        # Obter lista de computadores a partir das tabelas ou investigações existentes
        comp_records = meta.get('tables', {}).get('computers', [])
        comp_names = [r.get('computer_name') for r in comp_records if 'computer_name' in r] if comp_records else list(curr_invs.keys())
        if not comp_names:
            comp_names = list(curr_invs.keys())

        if comp_names:
            for comp in comp_names:
                inv_text = curr_invs.get(comp, '')
                new_inv = st.text_area(f"💻 {comp}", value=inv_text, key=f"edit_inv_{comp}", height=70)
                updated_invs[comp] = new_inv
        else:
            st.info("Nenhum computador cadastrado. Você pode adicionar um manualmente:")
            new_comp = st.text_input("Nome do Computador")
            new_note = st.text_area("Nota de Investigação")
            if new_comp and new_note:
                updated_invs[new_comp] = new_note

    with tab_recs:
        st.markdown("Edite ou adicione recomendações estratégicas:")
        curr_recs = meta.get('recommendations', [])
        recs_text = "\n".join(curr_recs)
        new_recs_text = st.text_area(
            "Recomendações (uma por linha - use [ALTA] para Alta prioridade, [MÉDIA] para Média, [INFO] para Informativa):",
            value=recs_text,
            height=150
        )
        updated_recs = [line.strip() for line in new_recs_text.split('\n') if line.strip()]

    st.markdown("---")

    if st.button("🔄 Aplicar Modificações e Gerar Novo HTML", type="primary", use_container_width=True):
        # Reconstruir objeto de dados com as modificações
        reconstructed_client = meta.get('client', {})
        reconstructed_client['client_name'] = edit_client_name
        reconstructed_client['company_name'] = edit_company_name

        reconstructed_data = {
            'total_events': kpi_events,
            'total_actions': kpi_actions,
            'total_computers': kpi_computers,
            'total_users': kpi_users,
            'total_violations': kpi_violations,
            'total_playbook_events': kpi_playbook,
            'enunciados': updated_enunciados,
            'recommendations': updated_recs,
            'tables': {},
            'charts': {}
        }

        # Reconstruir DataFrames das tabelas
        for t_name, records in meta.get('tables', {}).items():
            if records:
                reconstructed_data['tables'][t_name] = pd.DataFrame(records)

        for c_name, c_info in meta.get('charts_meta', {}).items():
            records = c_info.get('records', [])
            c_df = pd.DataFrame(records) if records else reconstructed_data['tables'].get(c_name)
            reconstructed_data['charts'][c_name] = {
                'title': updated_titles.get(c_name, c_info.get('title', c_name)),
                'enunciado': updated_enunciados.get(c_name, c_info.get('enunciado', '')),
                'label_col': c_info.get('label_col', ''),
                'value_col': c_info.get('value_col', ''),
                'data': c_df
            }

        # Carregar dados históricos e MoM se existirem
        hist_mgr = HistoryManager()
        client_key = st.session_state.get('client_selected', edit_client_name)
        prev_record = hist_mgr.get_previous_month_record(client_key, edit_period)
        mom_deltas = hist_mgr.calculate_mom_deltas(reconstructed_data, prev_record.get('metrics', {})) if prev_record else {}

        all_records = hist_mgr.load_client_history(client_key)
        m_idx, y_idx = hist_mgr.parse_period(edit_period)
        recent_history = [
            r for r in all_records
            if (r.get('year', 0) < y_idx) or (r.get('year', 0) == y_idx and r.get('month', 0) <= m_idx)
        ][-4:]

        # Gerar novo HTML
        new_gen = CyberReportHTML(
            client_config=reconstructed_client,
            period_str=edit_period,
            generation_date_str=edit_date
        )
        new_html = new_gen.generate(
            data=reconstructed_data,
            investigations=updated_invs,
            mom_deltas=mom_deltas,
            recent_history=recent_history
        )

        st.session_state.current_html_report = new_html

        st.success("✅ Relatório HTML atualizado com sucesso!")

        mod_filename = f"relatorio_modificado_{edit_client_name}_{edit_period.replace('/', '_')}.html"
        mod_filename = mod_filename.replace(' ', '_').lower()

        st.download_button(
            label="📥 Baixar Relatório HTML Modificado",
            data=new_html.encode('utf-8'),
            file_name=mod_filename,
            mime="text/html",
            use_container_width=True
        )

        with st.expander("👁️ Prévia do Relatório Modificado", expanded=True):
            st.components.v1.html(new_html, height=650, scrolling=True)


def page_annual_report():
    """Etapa 6: Relatório Anual & Gestão da Base Histórica."""
    st.header("📅 Relatório Anual Consolidado & Histórico")
    st.markdown("""
    Consolide os dados de telemetria dos **12 meses do ano** para gerar o **Relatório Anual Executivo de Cibersegurança**.
    """)

    clients = load_clients()
    client_keys = list(clients.keys())
    if not client_keys:
        st.warning("Nenhum cliente cadastrado.")
        return

    hist_manager = HistoryManager()

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_client = st.selectbox(
            "Selecione o Cliente",
            client_keys,
            format_func=lambda x: clients[x].get('client_name', x),
            key="annual_client_select"
        )
    with col2:
        current_year = date.today().year
        selected_year = st.selectbox(
            "Ano de Referência",
            [current_year, current_year - 1, current_year - 2],
            index=0,
            key="annual_year_select"
        )

    client_cfg = clients.get(selected_client, {})
    annual_data = hist_manager.get_annual_data(selected_client, selected_year)

    tab_overview, tab_manage_months, tab_export = st.tabs([
        "📊 Painel Anual Consolidado",
        "🗂️ Gestão de Meses Cadastrados",
        "📄 Exportar Relatório Anual HTML"
    ])

    with tab_overview:
        if not annual_data or annual_data.get('num_months_registered', 0) == 0:
            st.info(f"Nenhum mês registrado para o cliente **{client_cfg.get('client_name')}** no ano de **{selected_year}**.")
            st.markdown("💡 *Dica: Processe e gere os relatórios mensais normais para preencher a base automaticamente.*")
        else:
            num_m = annual_data['num_months_registered']
            st.subheader(f"Resumo Anual de {selected_year} ({num_m} meses registrados)")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Eventos no Ano", f"{annual_data['total_annual_events']:,}")
            k2.metric("Média Mensal", f"{annual_data['avg_monthly_events']:,}")
            k3.metric("Endpoints Atendidos", f"{annual_data['unique_computers_count']}")
            k4.metric("Violações no Ano", f"{annual_data['total_annual_violations']:,}")

            st.markdown("---")
            st.subheader("📈 Tendência Temporal dos 12 Meses")
            timeline = annual_data['timeline']
            df_time = pd.DataFrame([
                {
                    'Mês': t['month_name'][:3],
                    'Eventos': t['total_events'],
                    'Ações': t['total_actions'],
                    'Violações': t['total_violations']
                }
                for t in timeline
            ])
            st.line_chart(df_time.set_index('Mês'))

            st.markdown("---")
            c_comp, c_rules = st.columns(2)
            with c_comp:
                st.subheader("💻 Top Endpoints Recorrentes")
                if annual_data.get('top_recurrent_computers'):
                    df_c = pd.DataFrame(annual_data['top_recurrent_computers'])
                    df_c.columns = ['Host', 'Meses de Atividade', 'Total Eventos']
                    st.dataframe(df_c, use_container_width=True)
                else:
                    st.caption("Sem dados de endpoints.")

            with c_rules:
                st.subheader("🛡️ Top Regras Violadas no Ano")
                if annual_data.get('top_recurrent_rules'):
                    df_r = pd.DataFrame(annual_data['top_recurrent_rules'])
                    df_r.columns = ['Regra', 'Meses de Incidência', 'Total Eventos']
                    st.dataframe(df_r, use_container_width=True)
                else:
                    st.caption("Sem dados de regras.")

    with tab_manage_months:
        st.subheader("Meses Registrados na Base de Dados")
        history = hist_manager.load_client_history(selected_client)
        year_history = [r for r in history if r.get('year') == selected_year]

        if year_history:
            for r in year_history:
                with st.expander(f"🗓️ {r.get('period')} (Atualizado em: {r.get('updated_at', '')[:10]})"):
                    m = r.get('metrics', {})
                    col_m1, col_m2, col_m3, col_del = st.columns([1, 1, 1, 1])
                    col_m1.markdown(f"**Eventos:** {m.get('total_events', 0):,}")
                    col_m2.markdown(f"**Violações:** {m.get('total_violations', 0):,}")
                    col_m3.markdown(f"**Endpoints:** {m.get('total_computers', 0):,}")
                    with col_del:
                        if st.button("🗑️ Excluir Mês", key=f"del_{r.get('period')}"):
                            hist_manager.delete_month_record(selected_client, r.get('period'))
                            st.success(f"Mês {r.get('period')} excluído!")
                            st.rerun()
        else:
            st.info("Nenhum mês cadastrado para este ano.")

    with tab_export:
        st.subheader("Gerar e Baixar Relatório Anual Consolidado (HTML)")
        if not annual_data or annual_data.get('num_months_registered', 0) == 0:
            st.warning("⚠️ É necessário ter pelo menos 1 mês registrado para gerar o relatório anual.")
        else:
            st.markdown("Insira diretrizes estratégicas anuais ou parecer do SOC para o próximo ciclo:")
            n1 = st.text_input("Diretriz 1", value="Manutenção da postura de segurança e estabilidade operacional ao longo do ano.")
            n2 = st.text_input("Diretriz 2", value="Execução de varreduras forenses preventivas nos hosts mais recorrentes.")
            n3 = st.text_input("Diretriz 3", value="Refinamento contínuo das regras de prevenção a exploits no ambiente corporativo.")
            n4 = st.text_input("Diretriz 4", value="Continuidade do monitoramento 24x7 pelo time de MDR com inteligência de ameaças.")
            strategic_notes = [n1, n2, n3, n4]

            if st.button("✨ Gerar Relatório Anual HTML", type="primary", use_container_width=True):
                with st.spinner("Compilando dados de 12 meses e gerando HTML anual..."):
                    try:
                        annual_gen = AnnualReportHTML(
                            client_config=client_cfg,
                            year=selected_year
                        )
                        annual_html = annual_gen.generate(
                            annual_data=annual_data,
                            strategic_notes=strategic_notes
                        )

                        filename = f"relatorio_anual_{client_cfg.get('client_name', 'cliente')}_{selected_year}.html"
                        filename = filename.replace(' ', '_').lower()

                        st.success("✅ Relatório Anual gerado com sucesso!")
                        st.download_button(
                            label="📥 Baixar Relatório Anual HTML",
                            data=annual_html.encode('utf-8'),
                            file_name=filename,
                            mime="text/html",
                            use_container_width=True
                        )

                        with st.expander("👁️ Visualizar Relatório Anual Gerado", expanded=True):
                            st.components.v1.html(annual_html, height=750, scrolling=True)

                    except Exception as e:
                        st.error(f"Erro ao gerar Relatório Anual: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())


def page_configuration():
    """Etapa 8: Configuração de Arquivos CSV e Enunciados Padrão."""
    st.header("⚙️ Configuração de Arquivos CSV e Enunciados")

    config_manager = ConfigManager()
    configs = config_manager.get_all_configs()

    # Listar configurações existentes
    st.subheader("📄 Arquivos e Enunciados Cadastrados")

    if configs:
        for file_pattern, config in configs.items():
            with st.expander(f"📄 {file_pattern} — {config.get('title', file_pattern)}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Título da Seção:** `{config.get('title', 'N/A')}`")
                    st.markdown(f"**Descrição:** {config.get('description', 'N/A')}")
                    st.markdown(f"**💡 Enunciado Padrão:** *{config.get('enunciado', 'N/A')}*")
                    st.markdown(f"**Palavras-chave:** `{', '.join(config.get('keywords', []))}`")
                    st.markdown("**Mapeamento de Colunas:**")

                    for standard_name, csv_names in config.get('columns', {}).items():
                        st.write(f"- `{standard_name}` ← `{csv_names if isinstance(csv_names, str) else ', '.join(csv_names)}`")

                with col2:
                    if st.button("🗑️ Remover", key=f"remove_{file_pattern}"):
                        config_manager.remove_file_config(file_pattern)
                        st.success("✅ Configuração removida!")
                        st.rerun()
    else:
        st.info("Nenhum arquivo configurado ainda.")

    st.markdown("---")

    # Adicionar novo arquivo
    st.subheader("➕ Adicionar Novo Arquivo CSV com Enunciado")

    tab1, tab2 = st.tabs(["📤 Upload para Auto-detecção", "✍️ Configuração Manual"])

    with tab1:
        st.markdown("Faça upload de um CSV de exemplo para auto-detectar as colunas e sugerir palavras-chave.")
        uploaded_file = st.file_uploader("Arquivo CSV de exemplo", type='csv', key='config_upload')

        if uploaded_file:
            suggestions, columns = config_manager.auto_suggest(uploaded_file)
            st.markdown(f"**Arquivo sugerido:** `{suggestions.get('file_pattern', 'N/A')}`")

            with st.form("auto_config_form"):
                file_pattern = st.text_input("Padrão do Arquivo", value=suggestions.get('file_pattern', ''))
                title_input = st.text_input("Título Formal da Seção", value=suggestions.get('title', ''))
                description = st.text_input("Descrição", value=suggestions.get('description', ''))
                enunciado_input = st.text_area(
                    "💡 Enunciado / Contexto Explicativo",
                    value=suggestions.get('enunciado', ''),
                    help="Texto executivo inserido no topo da seção no relatório HTML."
                )
                keywords_str = st.text_input(
                    "Palavras-chave (separadas por vírgula)",
                    value=', '.join(suggestions.get('keywords', []))
                )

                st.markdown("### 📊 Mapeamento de Colunas")
                column_mapping = {}
                options = ['(Ignorar)', 'event_count', 'computer_name', 'user_name', 'rule_name', 'action_taken', 'timestamp']
                for col in columns:
                    std_suggested = suggestions.get('columns', {}).get(col, '(Ignorar)')
                    default_idx = options.index(std_suggested) if std_suggested in options else 0
                    std_name = st.selectbox(
                        f"Mapear coluna '{col}' para:",
                        options,
                        index=default_idx,
                        key=f"col_map_{col}"
                    )
                    if std_name != '(Ignorar)':
                        column_mapping[std_name] = [col]

                if st.form_submit_button("💾 Salvar Configuração"):
                    if file_pattern and keywords_str:
                        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                        config_manager.add_file_config(
                            file_pattern=file_pattern,
                            keywords=keywords,
                            column_mapping=column_mapping,
                            description=description,
                            title=title_input,
                            enunciado=enunciado_input
                        )
                        st.success("✅ Configuração e Enunciado salvos com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos obrigatórios!")

    with tab2:
        st.markdown("Configure manualmente sem necessidade de upload.")
        with st.form("manual_config_form"):
            file_pattern = st.text_input("Nome do arquivo (ex: Top_Threats.csv)")
            title_input = st.text_input("Título Formal da Seção", placeholder="ex: Top Ameaças Críticas")
            description = st.text_input("Descrição breve", placeholder="ex: Dados de bloqueio perimetral")
            enunciado_input = st.text_area(
                "💡 Enunciado / Contexto Explicativo",
                placeholder="Insira a explicação executiva deste gráfico/tabela para inclusão no HTML..."
            )
            keywords_input = st.text_input("Palavras-chave (separadas por vírgula)", placeholder="threats, bloqueios, perimeter")

            st.markdown("### 📊 Mapeamento de Colunas")
            num_cols = st.number_input("Quantidade de colunas a mapear", min_value=1, max_value=10, value=2)

            column_mapping = {}
            for i in range(int(num_cols)):
                c1, c2 = st.columns(2)
                with c1:
                    std_name = st.text_input("Nome Padrão Interno", placeholder="ex: event_count", key=f"man_std_{i}")
                with c2:
                    csv_name = st.text_input("Nome da Coluna no CSV", placeholder="ex: Total Eventos", key=f"man_csv_{i}")
                if std_name and csv_name:
                    column_mapping[std_name] = [csv_name.strip()]

            if st.form_submit_button("💾 Salvar Configuração Manual"):
                if file_pattern and keywords_input and column_mapping:
                    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
                    config_manager.add_file_config(
                        file_pattern=file_pattern,
                        keywords=keywords,
                        column_mapping=column_mapping,
                        description=description,
                        title=title_input,
                        enunciado=enunciado_input
                    )
                    st.success("✅ Configuração manual salva!")
                    st.rerun()
                else:
                    st.error("Preencha os campos obrigatórios!")


# =============================================
# APLICAÇÃO PRINCIPAL
# =============================================

def main():
    init_session_state()

    # Sidebar
    st.sidebar.title("🛡️ Cyber Report MDR")
    st.sidebar.markdown("---")

    steps = {
        1: "📋 Clientes",
        2: "📁 Upload CSV",
        3: "🔍 Processar Dados",
        4: "📊 Análise & Métricas",
        5: "📄 Gerar Relatório Mensal",
        6: "📅 Relatório Anual & Histórico",
        7: "✏️ Modificar HTML",
        8: "⚙️ Configurações"
    }

    # Sincronizar navegação requisitada por botões internos
    if 'target_step' in st.session_state:
        target = st.session_state.pop('target_step')
        st.session_state.step = target
        st.session_state.nav_radio = target

    step_keys = list(steps.keys())
    current_step = st.session_state.get('step', 1)
    current_idx = step_keys.index(current_step) if current_step in step_keys else 0

    def _on_nav_change():
        st.session_state.step = st.session_state.nav_radio

    step = st.sidebar.radio(
        "Navegação",
        step_keys,
        index=current_idx,
        format_func=lambda x: steps[x],
        key="nav_radio",
        on_change=_on_nav_change
    )

    st.session_state.step = step
    st.sidebar.markdown("---")
    st.sidebar.caption(f"🗓️ Período Padrão: **{get_default_period()}**")
    st.sidebar.info("Plataforma de Relatórios de Cibersegurança & MDR")

    # Renderizar página selecionada
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
        page_annual_report()
    elif step == 7:
        page_modify_html()
    elif step == 8:
        page_configuration()


if __name__ == "__main__":
    main()
