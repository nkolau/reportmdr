import pandas as pd
import numpy as np


def process_data(dataframes):
    """
    Processa os DataFrames e calcula métricas.

    Args:
        dataframes: Dict com DataFrames carregados

    Returns:
        results: Dict com métricas e dados processados
    """
    results = {
        'total_events': 0,
        'total_computers': 0,
        'total_users': 0,
        'total_rules': 0,
        'charts': {},
        'tables': {},
        'recommendations': []
    }

    # 1. Action_Cyber_Threats
    df_actions = dataframes.get('action_cyber_threats')
    if df_actions is not None and not df_actions.empty:
        total_actions = int(df_actions['event_count'].sum())
        results['total_actions'] = total_actions
        results['total_events'] += total_actions
        results['tables']['actions'] = df_actions
        results['charts']['actions'] = {
            'title': 'Ações Tomadas pelo Antivírus',
            'data': df_actions,
            'label_col': 'action_taken',
            'value_col': 'event_count'
        }

    # 2. Top_10_Users
    df_users = dataframes.get('top_10_users')
    if df_users is not None and not df_users.empty:
        total_user_events = int(df_users['event_count'].sum())
        results['total_user_events'] = total_user_events
        results['total_users'] = len(df_users)
        results['tables']['users'] = df_users
        results['charts']['users'] = {
            'title': 'Top 10 Usuários com Mais Detecções',
            'data': df_users,
            'label_col': 'user_name',
            'value_col': 'event_count'
        }

    # 3. Top_10_Computers
    df_computers = dataframes.get('top_10_computers')
    if df_computers is not None and not df_computers.empty:
        total_computer_events = int(df_computers['event_count'].sum())
        results['total_computer_events'] = total_computer_events
        results['total_computers'] = len(df_computers)
        results['tables']['computers'] = df_computers
        results['charts']['computers'] = {
            'title': 'Top 10 Computadores com Mais Detecções',
            'data': df_computers,
            'label_col': 'computer_name',
            'value_col': 'event_count'
        }

    # 4. Regras Playbook
    df_playbook = dataframes.get('regras_exploit_prevention_-_playbook_trellix_insights')
    if df_playbook is not None and not df_playbook.empty:
        total_playbook_events = int(df_playbook['event_count'].sum())
        results['total_playbook_events'] = total_playbook_events
        results['total_playbook_rules'] = len(df_playbook)
        results['tables']['playbook'] = df_playbook
        results['charts']['playbook'] = {
            'title': 'Regras do Playbook Trellix',
            'data': df_playbook,
            'label_col': 'rule_name',
            'value_col': 'event_count'
        }

    # 5. Regras Violadas
    df_rules_violated = dataframes.get('top_10_regras_de_prevencao_de_exploracao_violadas')
    if df_rules_violated is not None and not df_rules_violated.empty:
        total_violations = int(df_rules_violated['event_count'].sum())
        results['total_violations'] = total_violations
        results['total_rules_violated'] = len(df_rules_violated)
        results['tables']['rules_violated'] = df_rules_violated
        results['charts']['rules_violated'] = {
            'title': 'Top 10 Regras de Prevenção Violadas',
            'data': df_rules_violated,
            'label_col': 'rule_name',
            'value_col': 'event_count'
        }

    # Gerar recomendações
    recommendations = []

    if results.get('total_events', 0) > 1000:
        recommendations.append("🔴 Volume total de eventos elevado - recomenda-se análise detalhada")
    elif results.get('total_events', 0) > 100:
        recommendations.append("🟡 Volume de eventos moderado - manter monitoramento")

    if results.get('total_computers', 0) > 0:
        top_computer = df_computers.iloc[0] if not df_computers.empty else None
        if top_computer is not None:
            recommendations.append(
                f"💻 Computador com mais detecções: {top_computer['computer_name']} "
                f"({top_computer['event_count']} eventos) - requer investigação"
            )

    if results.get('total_users', 0) > 0:
        top_user = df_users.iloc[0] if not df_users.empty else None
        if top_user is not None:
            recommendations.append(
                f"👤 Usuário com mais detecções: {top_user['user_name']} "
                f"({top_user['event_count']} eventos) - verificar credenciais"
            )

    if results.get('total_violations', 0) > 0:
        top_rule = df_rules_violated.iloc[0] if not df_rules_violated.empty else None
        if top_rule is not None:
            recommendations.append(
                f"🔧 Regra mais violada: {top_rule['rule_name']} "
                f"({top_rule['event_count']} violações) - avaliar tuning"
            )

    results['recommendations'] = recommendations

    return results
