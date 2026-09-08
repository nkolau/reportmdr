import os
import json
import pandas as pd
from datetime import datetime, date
from core.history_manager import HistoryManager
from export.html_generator import CyberReportHTML
from export.annual_html_generator import AnnualReportHTML

def generate_mock_data_and_reports():
    print("=================================================================")
    print("🚀 Gerando Mockup de Dados (1 Ano) e Relatórios Executivos")
    print("=================================================================")

    os.makedirs("data/history", exist_ok=True)
    os.makedirs("data/demo_csvs", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    hist_mgr = HistoryManager(history_dir="data/history")

    # Configuração do Cliente Demo para Apresentação
    client_cfg = {
        'client_name': 'Grupo Hospitalar Alpha Saúde',
        'company_name': 'NetsafeCorp',
        'company_logo_path': 'data/logos/netsafecorp_logo.png',
        'primary_color': '#06090f',
        'secondary_color': '#8B0000',
        'accent_color': '#3b82f6'
    }

    # Atualizar config/clients.json com o cliente de demonstração
    clients_file = "config/clients.json"
    try:
        with open(clients_file, 'r', encoding='utf-8') as f:
            clients_db = json.load(f)
    except Exception:
        clients_db = {}

    clients_db["demo_alpha"] = client_cfg
    clients_db["default"]["client_name"] = "Grupo Hospitalar Alpha Saúde"
    with open(clients_file, 'w', encoding='utf-8') as f:
        json.dump(clients_db, f, indent=2, ensure_ascii=False)

    # 1. Gerar 12 meses de dados realistas (Janeiro a Dezembro de 2026)
    # Mostrando evolução: alta no início do ano -> redução gradual após ações de remediação do SOC -> estabilidade
    monthly_profiles = [
        # (Mês, Total Eventos, Violações, Endpoints, Usuários)
        (1, 2450, 85, 34, 15),  # Jan
        (2, 2180, 72, 29, 13),  # Fev
        (3, 1920, 64, 26, 11),  # Mar
        (4, 1650, 51, 22, 10),  # Abr
        (5, 1420, 44, 19, 8),   # Mai
        (6, 1310, 39, 17, 7),   # Jun
        (7, 1180, 33, 15, 6),   # Jul
        (8, 940, 24, 12, 5),    # Ago (Mês atual de foco no relatório mensal)
        (9, 890, 21, 11, 4),    # Set
        (10, 820, 18, 10, 4),   # Out
        (11, 790, 16, 9, 3),    # Nov
        (12, 750, 15, 8, 3)     # Dez
    ]

    months_names = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    # Lista de hosts recorrentes para dar consistência
    recurrent_hosts = [
        ('SRV-DC01-AD', 0.28),
        ('SRV-ERP-PRD', 0.20),
        ('SRV-DB-SQL01', 0.15),
        ('WS-FIN-014', 0.12),
        ('WS-DEV-088', 0.09),
        ('WS-DIR-002', 0.06),
        ('WS-RH-005', 0.04),
        ('SRV-WEB-EXT01', 0.03),
        ('WS-ENG-021', 0.02),
        ('WS-SUP-011', 0.01)
    ]

    # Regras realistas alinhadas com MITRE ATT&CK
    rules_pool = [
        ('T1059.001 - PowerShell Execution Bypass & Encoded Command', 0.30),
        ('T1055 - Process Injection & Memory Protection Violation', 0.22),
        ('T1003 - OS Credential Dumping (LSASS Memory Access)', 0.16),
        ('T1218.011 - Rundll32 Execution from Suspicious Directory', 0.12),
        ('T1021.002 - SMB/Admin Shares Lateral Movement Attempt', 0.10),
        ('T1083 - File and Directory Discovery Scripting', 0.06),
        ('T1078 - Valid Accounts Suspicious Authentication Pattern', 0.04)
    ]

    users_pool = [
        ('svc_backup_adm', 0.32),
        ('carlos.silva', 0.24),
        ('mariana.costa', 0.18),
        ('admin_domain', 0.14),
        ('roberto.almeida', 0.08),
        ('fernanda.lima', 0.04)
    ]

    actions_pool = [
        ('Ameaça Bloqueada Preventivamente', 0.58),
        ('Arquivo em Quarentena Forense', 0.24),
        ('Processo Suspeito Encerrado', 0.12),
        ('Conexão C2 Bloqueada no Firewall de Host', 0.06)
    ]

    latest_month_data = None
    latest_month_inv = None

    print("\n📦 1. Cadastrando 12 meses no Banco de Dados Histórico...")

    for m_num, tot_events, tot_viol, tot_comp, tot_usr in monthly_profiles:
        p_name = f"{months_names[m_num - 1]}/2026"

        # Tabela Computers
        comp_rows = []
        for h_name, weight in recurrent_hosts:
            h_events = max(1, int(tot_events * weight))
            comp_rows.append({'computer_name': h_name, 'event_count': h_events})
        df_comp = pd.DataFrame(comp_rows)

        # Tabela Users
        usr_rows = []
        for u_name, weight in users_pool:
            u_events = max(1, int(tot_events * weight * 0.4))
            usr_rows.append({'user_name': u_name, 'event_count': u_events})
        df_users = pd.DataFrame(usr_rows)

        # Tabela Rules
        rule_rows = []
        for r_name, weight in rules_pool:
            r_events = max(1, int(tot_viol * weight))
            rule_rows.append({'rule_name': r_name, 'event_count': r_events})
        df_rules = pd.DataFrame(rule_rows)

        # Tabela Actions
        action_rows = []
        for a_name, weight in actions_pool:
            a_events = max(1, int(tot_events * weight))
            action_rows.append({'action_taken': a_name, 'event_count': a_events})
        df_actions = pd.DataFrame(action_rows)

        # Tabela Playbook
        playbook_rows = [
            {'rule_name': 'Trellix Insights - Ransomware Pre-Execution Guard', 'event_count': int(tot_events * 0.06)},
            {'rule_name': 'Trellix Insights - Credential Access Defense', 'event_count': int(tot_events * 0.04)},
            {'rule_name': 'Trellix Insights - Defense Evasion Hook Detection', 'event_count': int(tot_events * 0.03)}
        ]
        df_playbook = pd.DataFrame(playbook_rows)

        # Investigações detalhadas
        investigations = {
            'SRV-DC01-AD': 'Servidor controlador de domínio apresentou tentativas de enumeração via LDAP. Origem mapeada para estação WS-FIN-014; regras de firewall interno aplicadas e credenciais rotacionadas.',
            'SRV-ERP-PRD': 'Detecção de execução anômala de binário temporário na pasta de spool. Processo finalizado preventivamente; sem evidência de vazamento ou persistência.',
            'SRV-DB-SQL01': 'Consultas incomuns em horários fora do expediente bloqueadas pela política de integridade de banco de dados. Validação com o DBA confirmou rotina de manutenção não homologada.',
            'WS-FIN-014': 'Tentativa de execução de macro maliciosa em anexo de phishing via e-mail. Bloqueio automático efetuado pelo Endpoint Security.',
            'WS-DEV-088': 'Compilador executando scripts não assinados. Orientação repassada ao time de desenvolvimento para inclusão de exceções formais de compilação.'
        }

        # Recomendações estruturadas
        recs = [
            "[ALTA] Reforçar isolamento preventivo e monitoramento estrito no Controlador de Domínio (SRV-DC01-AD).",
            "[MÉDIA] Implementar política de restrição de execução de macros não assinadas via GPO corporativa.",
            "[MÉDIA] Ajustar regras de tuning no ambiente de desenvolvimento para evitar ruído operacional.",
            "[INFO] Postura geral de segurança em evolução positiva com queda contínua de violações de exploit."
        ]

        # Enunciados explicativos
        enunciados = {
            'actions': 'Ações executadas de forma automatizada pelos módulos de proteção perimetral e de endpoint para contenção imediata de ameaças no ambiente corporativo.',
            'users': 'Identidades de usuários com maior volume de alertas e comportamentos anômalos registrados, direcionando auditorias de privilégios e conscientização de phishing.',
            'computers': 'Endpoints e servidores com maior criticidade e concentração de eventos, requerendo acompanhamento forense ativo e análise de superfície de ataque.',
            'rules_violated': 'Regras de Exploit Prevention acionadas durante o período, refletindo técnicas adversárias bloqueadas em conformidade com o framework MITRE ATT&CK.',
            'playbook': 'Correlação de inteligência de ameaças Trellix Insights identificando campanhas globais ativas mitigadas preventivamente.'
        }

        charts_data = {
            'actions': {'title': 'Ações Tomadas pelo Antivírus', 'enunciado': enunciados['actions'], 'data': df_actions, 'label_col': 'action_taken', 'value_col': 'event_count'},
            'users': {'title': 'Usuários com Mais Detecções', 'enunciado': enunciados['users'], 'data': df_users, 'label_col': 'user_name', 'value_col': 'event_count'},
            'computers': {'title': 'Computadores com Mais Detecções', 'enunciado': enunciados['computers'], 'data': df_comp, 'label_col': 'computer_name', 'value_col': 'event_count'},
            'rules_violated': {'title': 'Regras de Prevenção de Exploração Violadas', 'enunciado': enunciados['rules_violated'], 'data': df_rules, 'label_col': 'rule_name', 'value_col': 'event_count'},
            'playbook': {'title': 'Regras do Playbook Trellix Insights', 'enunciado': enunciados['playbook'], 'data': df_playbook, 'label_col': 'rule_name', 'value_col': 'event_count'}
        }

        month_payload = {
            'total_events': tot_events,
            'total_actions': tot_events,
            'total_computers': tot_comp,
            'total_users': tot_usr,
            'total_violations': tot_viol,
            'total_playbook_events': sum(p['event_count'] for p in playbook_rows),
            'tables': {
                'actions': df_actions,
                'users': df_users,
                'computers': df_comp,
                'rules_violated': df_rules,
                'playbook': df_playbook
            },
            'charts': charts_data,
            'enunciados': enunciados,
            'recommendations': recs
        }

        # Salvar para o client "demo_alpha" e para o client "default"
        hist_mgr.save_month_record("demo_alpha", p_name, month_payload, investigations)
        hist_mgr.save_month_record("default", p_name, month_payload, investigations)

        print(f"  ✓ Mês cadastrado: {p_name} ({tot_events:,} eventos | {tot_viol} violações)")

        # Salvar o mês de Agosto/2026 como referência para o relatório mensal
        if m_num == 8:
            latest_month_data = month_payload
            latest_month_inv = investigations

            # Salvar os CSVs correspondentes em data/demo_csvs/
            df_actions.to_csv("data/demo_csvs/Action_Cyber_Threats.csv", index=False)
            df_users.to_csv("data/demo_csvs/Top_10_Users.csv", index=False)
            df_comp.to_csv("data/demo_csvs/Top_10_Computers.csv", index=False)
            df_rules.to_csv("data/demo_csvs/Top_10_regras_de_Prevencao_de_Exploracao_violadas.csv", index=False)
            df_playbook.to_csv("data/demo_csvs/Regras_exploit_prevention_-_Playbook_Trellix_Insights.csv", index=False)

    print("\n📄 2. Gerando Relatório Mensal Executivo em HTML (Agosto/2026 com MoM)...")

    # Recuperar histórico recente e deltas MoM de Agosto vs Julho
    prev_rec = hist_mgr.get_previous_month_record("demo_alpha", "Agosto/2026")
    mom_deltas = hist_mgr.calculate_mom_deltas(latest_month_data, prev_rec['metrics'])
    recent_history = hist_mgr.load_client_history("demo_alpha")

    monthly_gen = CyberReportHTML(
        client_config=client_cfg,
        period_str="Agosto/2026",
        generation_date_str=date.today().strftime('%d/%m/%Y')
    )
    monthly_html = monthly_gen.generate(
        data=latest_month_data,
        investigations=latest_month_inv,
        mom_deltas=mom_deltas,
        recent_history=recent_history[:8]
    )

    monthly_out_path = "relatorio_mensal_executivo_agosto_2026.html"
    with open(monthly_out_path, "w", encoding="utf-8") as f:
        f.write(monthly_html)

    print(f"  ✓ Relatório Mensal gerado: {monthly_out_path} ({len(monthly_html):,} bytes)")

    print("\n📅 3. Gerando Relatório Anual Consolidado em HTML (12 Meses de 2026)...")

    annual_data = hist_mgr.get_annual_data("demo_alpha", 2026)
    annual_gen = AnnualReportHTML(
        client_config=client_cfg,
        year=2026,
        generation_date_str=date.today().strftime('%d/%m/%Y')
    )

    annual_notes = [
        "Consolidação de maturidade cibernética com queda expressiva de 69.3% no volume total de incidentes entre Janeiro e Dezembro de 2026.",
        "Implementação bem-sucedida de políticas de proteção contra exploit prevention mitigando 100% das tentativas críticas de elevação de privilégio.",
        "Recomendada auditoria semestral nos servidores de alta criticidade (SRV-DC01-AD e SRV-ERP-PRD) devido à recorrência observada de varreduras perimetrais.",
        "Continuidade da cobertura 24x7 pelo time de MDR/SOC NetsafeCorp com foco na expansão de detecção comportamental para o ciclo de 2027."
    ]

    annual_html = annual_gen.generate(
        annual_data=annual_data,
        strategic_notes=annual_notes
    )

    annual_out_path = "relatorio_anual_executivo_2026.html"
    with open(annual_out_path, "w", encoding="utf-8") as f:
        f.write(annual_html)

    print(f"  ✓ Relatório Anual gerado: {annual_out_path} ({len(annual_html):,} bytes)")

    print("\n=================================================================")
    print("✨ CONCLUÍDO COM SUCESSO!")
    print(f"1. Relatório Mensal HTML:  {os.path.abspath(monthly_out_path)}")
    print(f"2. Relatório Anual HTML:   {os.path.abspath(annual_out_path)}")
    print(f"3. CSVs de Demonstração:   {os.path.abspath('data/demo_csvs/')}")
    print("=================================================================")

if __name__ == "__main__":
    generate_mock_data_and_reports()
