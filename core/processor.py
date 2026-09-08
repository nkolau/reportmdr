import pandas as pd
import numpy as np
import os
import json


def _get_file_configs():
    """Carrega as configurações e enunciados dos arquivos cadastrados."""
    mapping_file = os.path.join("config", "file_mapping.json")
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("file_configs", {})
        except Exception:
            pass
    return {}


def _sum_events(df, col='event_count'):
    if df is None or df.empty or col not in df.columns:
        return 0
    return int(pd.to_numeric(df[col], errors='coerce').fillna(0).sum())


def process_data(dataframes):
    """
    Processa os DataFrames e calcula métricas, associando títulos e enunciados.

    Args:
        dataframes: Dict com DataFrames carregados (chaves normalizadas em lowercase sem extensão)

    Returns:
        results: Dict com métricas, enunciados e dados processados
    """
    file_configs = _get_file_configs()

    results = {
        'total_events': 0,
        'total_computers': 0,
        'total_users': 0,
        'total_rules': 0,
        'charts': {},
        'tables': {},
        'enunciados': {},
        'recommendations': []
    }

    # Helper para recuperar enunciado do arquivo
    def find_file_meta(csv_pattern, default_title, default_enunciado):
        cfg = file_configs.get(csv_pattern, {})
        return {
            'title': cfg.get('title', default_title),
            'enunciado': cfg.get('enunciado', default_enunciado)
        }

    # 1. Action_Cyber_Threats
    df_actions = dataframes.get('action_cyber_threats')
    if df_actions is not None and not df_actions.empty:
        meta = find_file_meta(
            'Action_Cyber_Threats.csv',
            'Ações Tomadas pelo Antivírus',
            'Distribuição das ações automáticas e preventivas executadas pela plataforma de proteção nos endpoints. Demonstra a eficácia da contenção e resposta em tempo real contra ameaças bloqueadas, limpas ou mantidas em quarentena.'
        )
        total_actions = _sum_events(df_actions)
        results['total_actions'] = total_actions
        results['total_events'] += total_actions
        results['tables']['actions'] = df_actions
        results['enunciados']['actions'] = meta['enunciado']
        results['charts']['actions'] = {
            'title': meta['title'],
            'enunciado': meta['enunciado'],
            'data': df_actions,
            'label_col': 'action_taken',
            'value_col': 'event_count'
        }

    # 2. Top_10_Users
    df_users = dataframes.get('top_10_users')
    if df_users is not None and not df_users.empty:
        meta = find_file_meta(
            'Top_10_Users.csv',
            'Usuários com Mais Detecções',
            'Identificação dos usuários e identidades com maior incidência de eventos de segurança no período. Permite priorizar ações de conscientização corporativa, auditoria de credenciais e verificação de comportamentos anômalos.'
        )
        total_user_events = _sum_events(df_users)
        results['total_user_events'] = total_user_events
        results['total_users'] = len(df_users)
        results['tables']['users'] = df_users
        results['enunciados']['users'] = meta['enunciado']
        results['charts']['users'] = {
            'title': meta['title'],
            'enunciado': meta['enunciado'],
            'data': df_users,
            'label_col': 'user_name',
            'value_col': 'event_count'
        }

    # 3. Top_10_Computers
    df_computers = dataframes.get('top_10_computers')
    if df_computers is not None and not df_computers.empty:
        meta = find_file_meta(
            'Top_10_Computers.csv',
            'Computadores com Mais Detecções',
            'Endpoints e estações de trabalho que registraram o maior volume de alertas no período. Essencial para direcionamento de varreduras forenses aprofundadas, investigação de persistência e isolamento preventivo.'
        )
        total_computer_events = _sum_events(df_computers)
        results['total_computer_events'] = total_computer_events
        results['total_computers'] = len(df_computers)
        results['tables']['computers'] = df_computers
        results['enunciados']['computers'] = meta['enunciado']
        results['charts']['computers'] = {
            'title': meta['title'],
            'enunciado': meta['enunciado'],
            'data': df_computers,
            'label_col': 'computer_name',
            'value_col': 'event_count'
        }

    # 4. Regras Playbook
    df_playbook = dataframes.get('regras_exploit_prevention_-_playbook_trellix_insights')
    if df_playbook is not None and not df_playbook.empty:
        meta = find_file_meta(
            'Regras_exploit_prevention_-_Playbook_Trellix_Insights.csv',
            'Regras do Playbook Trellix Insights',
            'Mapeamento das técnicas de ataque e regras de inteligência de ameaças correlacionadas no ambiente, fornecendo visibilidade estratégica de táticas adversárias alinhadas à matriz MITRE ATT&CK.'
        )
        total_playbook_events = _sum_events(df_playbook)
        results['total_playbook_events'] = total_playbook_events
        results['total_playbook_rules'] = len(df_playbook)
        results['tables']['playbook'] = df_playbook
        results['enunciados']['playbook'] = meta['enunciado']
        results['charts']['playbook'] = {
            'title': meta['title'],
            'enunciado': meta['enunciado'],
            'data': df_playbook,
            'label_col': 'rule_name',
            'value_col': 'event_count'
        }

    # 5. Regras Violadas
    df_rules_violated = dataframes.get('top_10_regras_de_prevencao_de_exploracao_violadas')
    if df_rules_violated is not None and not df_rules_violated.empty:
        meta = find_file_meta(
            'Top_10_regras_de_Prevencao_de_Exploracao_violadas.csv',
            'Regras de Prevenção de Exploração Violadas',
            'Regras de proteção avançada contra exploits e técnicas de evasão que foram acionadas no parque de máquinas. Indica tentativas ativas de exploração de vulnerabilidades e direciona o refinamento (tuning) das políticas de segurança.'
        )
        total_violations = _sum_events(df_rules_violated)
        results['total_violations'] = total_violations
        results['total_rules_violated'] = len(df_rules_violated)
        results['tables']['rules_violated'] = df_rules_violated
        results['enunciados']['rules_violated'] = meta['enunciado']
        results['charts']['rules_violated'] = {
            'title': meta['title'],
            'enunciado': meta['enunciado'],
            'data': df_rules_violated,
            'label_col': 'rule_name',
            'value_col': 'event_count'
        }

    # Processar quaisquer outros dataframes customizados
    standard_keys = {
        'action_cyber_threats', 'top_10_users', 'top_10_computers',
        'regras_exploit_prevention_-_playbook_trellix_insights',
        'top_10_regras_de_prevencao_de_exploracao_violadas'
    }

    for key, df in dataframes.items():
        if key not in standard_keys and df is not None and not df.empty:
            # Encontrar matching em file_configs
            matched_cfg = {}
            for pattern, cfg in file_configs.items():
                if pattern.replace('.csv', '').lower() == key:
                    matched_cfg = cfg
                    break

            t_title = matched_cfg.get('title', key.replace('_', ' ').title())
            t_enunciado = matched_cfg.get('enunciado', f"Dados consolidados de {t_title} no período.")

            # Identificar colunas para gráfico se possível
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = [c for c in df.columns if c not in num_cols]

            results['tables'][key] = df
            results['enunciados'][key] = t_enunciado

            if num_cols and cat_cols:
                results['charts'][key] = {
                    'title': t_title,
                    'enunciado': t_enunciado,
                    'data': df,
                    'label_col': cat_cols[0],
                    'value_col': num_cols[0]
                }

    # Fallback inteligente para total_events se df_actions não foi enviado
    if results['total_events'] == 0:
        if results.get('total_computer_events', 0) > 0:
            results['total_events'] = results['total_computer_events']
        elif results.get('total_violations', 0) > 0:
            results['total_events'] = results['total_violations']
        elif results.get('total_user_events', 0) > 0:
            results['total_events'] = results['total_user_events']

    # Gerar recomendações dinâmicas
    recommendations = []

    if results.get('total_events', 0) > 1000:
        recommendations.append("[ALTA] Volume total de eventos elevado - recomenda-se análise detalhada e acompanhamento de incidentes.")
    elif results.get('total_events', 0) > 100:
        recommendations.append("[MÉDIA] Volume de eventos moderado - manter rotina de monitoramento ativo nos endpoints.")
    else:
        recommendations.append("[INFO] Volume de eventos controlado dentro dos limiares de segurança operacionais.")

    if results.get('total_computers', 0) > 0 and df_computers is not None and not df_computers.empty:
        df_comp_sorted = df_computers.copy()
        if 'event_count' in df_comp_sorted.columns:
            df_comp_sorted['event_count'] = pd.to_numeric(df_comp_sorted['event_count'], errors='coerce').fillna(0)
            df_comp_sorted = df_comp_sorted.sort_values(by='event_count', ascending=False)
        top_computer = df_comp_sorted.iloc[0]
        recommendations.append(
            f"[ALTA] Computador com maior criticidade: {top_computer['computer_name']} "
            f"({int(top_computer['event_count'])} eventos) - avaliar necessidade de varredura forense e isolamento preventivo."
        )

    if results.get('total_users', 0) > 0 and df_users is not None and not df_users.empty:
        df_users_sorted = df_users.copy()
        if 'event_count' in df_users_sorted.columns:
            df_users_sorted['event_count'] = pd.to_numeric(df_users_sorted['event_count'], errors='coerce').fillna(0)
            df_users_sorted = df_users_sorted.sort_values(by='event_count', ascending=False)
        top_user = df_users_sorted.iloc[0]
        recommendations.append(
            f"[MÉDIA] Usuário com maior volume de alertas: {top_user['user_name']} "
            f"({int(top_user['event_count'])} eventos) - validar autenticidade das sessões e revisar privilégios de acesso."
        )

    if results.get('total_violations', 0) > 0 and df_rules_violated is not None and not df_rules_violated.empty:
        df_rules_sorted = df_rules_violated.copy()
        if 'event_count' in df_rules_sorted.columns:
            df_rules_sorted['event_count'] = pd.to_numeric(df_rules_sorted['event_count'], errors='coerce').fillna(0)
            df_rules_sorted = df_rules_sorted.sort_values(by='event_count', ascending=False)
        top_rule = df_rules_sorted.iloc[0]
        recommendations.append(
            f"[MÉDIA] Regra mais violada: {top_rule['rule_name']} "
            f"({int(top_rule['event_count'])} violações) - analisar padrões de tráfego/execução para possível refinamento (tuning)."
        )

    results['recommendations'] = recommendations

    return results

