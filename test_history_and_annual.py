import os
import sys
import pandas as pd
from datetime import datetime

from core.history_manager import HistoryManager
from export.html_generator import CyberReportHTML
from export.annual_html_generator import AnnualReportHTML

def test_history_and_annual():
    print("=== 1. Testando HistoryManager & Persistência ===")
    hist_mgr = HistoryManager(history_dir="data/history")
    client_id = "test_client_alfa"

    # Criar dados simulados para 3 meses: Junho/2026, Julho/2026, Agosto/2026
    months_data = [
        {
            'period': 'Junho/2026',
            'data': {
                'total_events': 1500,
                'total_actions': 1500,
                'total_computers': 25,
                'total_users': 10,
                'total_violations': 60,
                'total_playbook_events': 120,
                'tables': {
                    'computers': pd.DataFrame({'computer_name': ['SRV-DC01', 'WS-FIN02'], 'event_count': [500, 300]}),
                    'rules_violated': pd.DataFrame({'rule_name': ['Exploit Generic', 'PowerShell Obfuscation'], 'event_count': [40, 20]})
                },
                'recommendations': ['Manter monitoramento']
            }
        },
        {
            'period': 'Julho/2026',
            'data': {
                'total_events': 1200,
                'total_actions': 1200,
                'total_computers': 20,
                'total_users': 8,
                'total_violations': 45,
                'total_playbook_events': 90,
                'tables': {
                    'computers': pd.DataFrame({'computer_name': ['SRV-DC01', 'WS-DEV01'], 'event_count': [400, 250]}),
                    'rules_violated': pd.DataFrame({'rule_name': ['Exploit Generic', 'Cmd Hijack'], 'event_count': [30, 15]})
                },
                'recommendations': ['Revisar regras']
            }
        },
        {
            'period': 'Agosto/2026',
            'data': {
                'total_events': 950,
                'total_actions': 950,
                'total_computers': 16,
                'total_users': 6,
                'total_violations': 32,
                'total_playbook_events': 75,
                'tables': {
                    'computers': pd.DataFrame({'computer_name': ['SRV-DC01', 'WS-HR03'], 'event_count': [350, 180]}),
                    'rules_violated': pd.DataFrame({'rule_name': ['Exploit Generic', 'Script Injection'], 'event_count': [22, 10]})
                },
                'recommendations': ['Tuning preventivo']
            }
        }
    ]

    for m in months_data:
        record = hist_mgr.save_month_record(
            client_id=client_id,
            period_str=m['period'],
            processed_data=m['data']
        )
        print(f"Salvo {record['period']}: {record['metrics']['total_events']} eventos.")

    print("\n=== 2. Testando Variações MoM (Agosto vs Julho) ===")
    prev = hist_mgr.get_previous_month_record(client_id, 'Agosto/2026')
    assert prev is not None, "Registro anterior não encontrado!"
    print(f"Mês anterior identificado: {prev['period']}")

    deltas = hist_mgr.calculate_mom_deltas(months_data[2]['data'], prev['metrics'])
    print("Deltas calculados:")
    for k, v in deltas.items():
        print(f" - {k}: {v['prev_value']} -> {v['curr_value']} ({v['diff']}) = {v['pct']}% [{v['direction']} / {v['status']}]")

    assert deltas['total_events']['pct'] < 0, "Deveria ser queda percentual nos eventos"

    print("\n=== 3. Testando Geração de Relatório Mensal com MoM ===")
    client_cfg = {
        'client_name': 'Alfa Corp',
        'company_name': 'NetsafeCorp',
        'company_logo_path': 'data/logos/netsafecorp_logo.png'
    }

    recent_hist = hist_mgr.load_client_history(client_id)
    html_gen = CyberReportHTML(client_config=client_cfg, period_str='Agosto/2026')
    monthly_html = html_gen.generate(
        data=months_data[2]['data'],
        mom_deltas=deltas,
        recent_history=recent_hist
    )
    assert 'kpi-mom-badge' in monthly_html, "Badge MoM não encontrada no HTML mensal!"
    assert 'Evolução Temporal Recente' in monthly_html, "Seção de evolução recente não encontrada!"
    print(f"HTML Mensal gerado com sucesso ({len(monthly_html)} bytes) contendo badges MoM e gráfico temporal!")

    print("\n=== 4. Testando Consolidação Anual (2026) ===")
    annual_data = hist_mgr.get_annual_data(client_id, 2026)
    assert annual_data is not None, "Dados anuais não encontrados!"
    print(f"Meses avaliados no ano: {annual_data['num_months_registered']}")
    print(f"Total Acumulado de Eventos: {annual_data['total_annual_events']}")
    print(f"Média Mensal de Eventos: {annual_data['avg_monthly_events']}")
    print(f"Top Endpoints Recorrentes: {[c['name'] for c in annual_data['top_recurrent_computers']]}")

    annual_gen = AnnualReportHTML(client_config=client_cfg, year=2026)
    annual_html = annual_gen.generate(annual_data=annual_data)
    
    with open('data/test_annual_report.html', 'w', encoding='utf-8') as f:
        f.write(annual_html)

    print(f"Relatório Anual HTML gerado com sucesso ({len(annual_html)} bytes)!")

    print("\n=== 5. Validando 0 Emojis no Relatório Anual ===")
    import re
    emoji_pattern = re.compile(
        '['
        '\U0001F1E0-\U0001F1FF'
        '\U0001F300-\U0001F5FF'
        '\U0001F600-\U0001F64F'
        '\U0001F680-\U0001F6FF'
        '\U0001F700-\U0001F77F'
        '\U0001F780-\U0001F7FF'
        '\U0001F800-\U0001F8FF'
        '\U0001F900-\U0001F9FF'
        '\U0001FA00-\U0001FA6F'
        '\U0001FA70-\U0001FAFF'
        '\U00002702-\U000027B0'
        '\U000024C2-\U0001F251'
        '\U00002600-\U000026FF'
        '\U00002300-\U000023FF'
        ']+',
        flags=re.UNICODE
    )
    matches = emoji_pattern.findall(annual_html)
    print(f"Total de emojis no Relatório Anual: {len(matches)}")
    assert len(matches) == 0, f"Emojis encontrados: {matches}"

    print("\n✅ TODOS OS TESTES PASSARAM COM SUCESSO!")

if __name__ == '__main__':
    test_history_and_annual()
