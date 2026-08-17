import pandas as pd
import numpy as np


def process_data(dataframes):
    """
    Processa os DataFrames e calcula métricas.
    Adaptado para trabalhar com qualquer configuração dinâmica.
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

    # Processar cada DataFrame disponível
    for file_pattern, df in dataframes.items():
        if df is None or df.empty:
            continue

        # Identificar o tipo baseado no padrão
        pattern_lower = file_pattern.lower()

        # Determinar colunas de label e valor
        label_col = None
        value_col = None

        # Procurar colunas de valor (event_count, violation_count, detection_count)
        for col in df.columns:
            if 'count' in col.lower() or 'event' in col.lower() or 'violation' in col.lower() or 'detection' in col.lower():
                value_col = col
                break

        # Procurar colunas de label
        for col in df.columns:
            if col != value_col:
                label_col = col
                break

        if label_col is None or value_col is None:
            # Tentar usar primeira e segunda coluna
            if len(df.columns) >= 2:
                label_col = df.columns[0]
                value_col = df.columns[1]
            elif len(df.columns) == 1:
                label_col = df.columns[0]
                df['count'] = 1
                value_col = 'count'

        # Calcular totais
        if value_col and value_col in df.columns:
            total = int(df[value_col].sum())
        else:
            total = len(df)

        # Identificar tipo para métricas específicas
        if 'user' in pattern_lower:
            results['total_users'] = len(df)
            results['tables']['users'] = df
            title = 'Usuários com Mais Detecções'
        elif 'computer' in pattern_lower or 'maquina' in pattern_lower or 'equipment' in pattern_lower:
            results['total_computers'] = len(df)
            results['tables']['computers'] = df
            title = 'Computadores com Mais Detecções'
        elif 'regra' in pattern_lower and 'violad' in pattern_lower:
            results['total_rules_violated'] = len(df)
            results['tables']['rules_violated'] = df
            title = 'Regras de Prevenção Violadas'
        elif 'regra' in pattern_lower or 'playbook' in pattern_lower:
            results['total_rules'] = len(df)
            results['tables']['playbook'] = df
            title = 'Regras do Playbook e Personalizadas'
        elif 'acao' in pattern_lower or 'action' in pattern_lower:
            results['total_actions'] = total
            results['tables']['actions'] = df
            title = 'Ações Tomadas pelo Antivírus'
        elif 'threat' in pattern_lower or 'ameaca' in pattern_lower:
            results['total_threats'] = total
            results['tables']['threats'] = df
            title = 'Ameaças Detectadas'
        else:
            # Tipo genérico
            results['tables'][file_pattern] = df
            title = file_pattern.replace('_', ' ').title()

        # Adicionar ao total de eventos
        results['total_events'] += total

        # Adicionar gráfico
        results['charts'][file_pattern] = {
            'title': title,
            'data': df,
            'label_col': label_col,
            'value_col': value_col
        }

        print(f"✅ Processado: {title} ({total} eventos)")

    # Gerar recomendações
    recommendations = []

    if results.get('total_events', 0) > 1000:
        recommendations.append("🔴 Volume total de eventos elevado - recomenda-se análise detalhada")
    elif results.get('total_events', 0) > 100:
        recommendations.append("🟡 Volume de eventos moderado - manter monitoramento")

    if results.get('total_computers', 0) > 0:
        computers_df = results['tables'].get('computers')
        if computers_df is not None and not computers_df.empty:
            value_col = [c for c in computers_df.columns if 'count' in c.lower() or 'event' in c.lower()]
            if value_col:
                top_computer = computers_df.iloc[0]
                recommendations.append(f"💻 Computador com mais detecções: {top_computer[computers_df.columns[0]]} ({top_computer[value_col[0]]} eventos)")

    results['recommendations'] = recommendations

    return results
