import os
import sys
import io
import html
import pandas as pd
import numpy as np
from datetime import date

from core.config_manager import ConfigManager
from core.history_manager import HistoryManager
from core.processor import process_data
from core.validator import validate_uploaded_files
from export.html_generator import CyberReportHTML
from export.annual_html_generator import AnnualReportHTML

print("🧪 Iniciando Bateria de Testes de Remediação...")

# 1. Teste de parse_period para virada de ano em Janeiro
hm = HistoryManager()
m, y = hm.parse_period("")
print(f"1. Fallback de período vazio: Mês {m}, Ano {y}")
assert 1 <= m <= 12
assert y >= 2025

# 2. Teste de conversão numérica com vírgulas e NaN
raw_val = hm._safe_int("1,500")
assert raw_val == 1500, f"Esperado 1500, obtido {raw_val}"
nan_val = hm._safe_int(np.nan, default=0)
assert nan_val == 0, f"Esperado 0, obtido {nan_val}"
none_val = hm._safe_int(None, default=10)
assert none_val == 10, f"Esperado 10, obtido {none_val}"
print("2. Conversões seguras de números: OK")

# 3. Teste de fallback de total_events e ordenação decrescente de Top Items
mock_unsorted_comp = pd.DataFrame({
    'computer_name': ['WS-LOW-EVENT', 'SRV-CRITICAL-HIGH', 'WS-MID-EVENT'],
    'event_count': [1, 9500, 320]
})
mock_dfs = {
    'top_10_computers': mock_unsorted_comp
}
res_proc = process_data(mock_dfs)
assert res_proc['total_events'] == 9821, f"Esperado 9821, obtido {res_proc['total_events']}"
# Verificar se recomendação pegou a máquina crítica de 9500 eventos e não a de 1 evento
rec_text = " ".join(res_proc['recommendations'])
assert "SRV-CRITICAL-HIGH" in rec_text, f"SRV-CRITICAL-HIGH não encontrada em: {rec_text}"
assert "9500" in rec_text, f"9500 eventos não encontrados em: {rec_text}"
print("3. Fallback de total_events e ordenação decrescente de criticidade: OK")

# 4. Teste de auto_suggest em ConfigManager
cfg_mgr = ConfigManager()
class MockUploadedFile:
    def __init__(self, name, content):
        self.name = name
        self.buffer = io.BytesIO(content.encode('utf-8'))
    def seek(self, pos):
        self.buffer.seek(pos)
    def read(self, *args):
        return self.buffer.read(*args)

mock_csv = MockUploadedFile(
    "Firewall_Threat_Blocks.csv",
    "Host IP,Target User,Blocked Events\n192.168.1.1,admin,120\n"
)
suggestions, columns = cfg_mgr.auto_suggest(mock_csv)
assert suggestions['file_pattern'] == "Firewall_Threat_Blocks.csv"
assert suggestions['title'] == "Firewall Threat Blocks"
assert "Firewall Threat Blocks" in suggestions['enunciado']
assert "event_count" in suggestions['columns'].values() or "user_name" in suggestions['columns'].values()
print("4. Auto-sugestão rica de novo arquivo CSV: OK")

# 5. Teste de validação flexível de colunas com sinônimos em validator.py
mock_user_csv = MockUploadedFile(
    "Top_10_Users.csv",
    "User Name,Event Count\njohn.doe,250\nmary.smith,180\n"
)
dataframes, warnings, errors = validate_uploaded_files([mock_user_csv])
assert 'top_10_users' in dataframes, f"Falha ao validar Top_10_Users com sinônimos. Erros: {errors}"
df_loaded = dataframes['top_10_users']
assert 'user_name' in df_loaded.columns
assert 'event_count' in df_loaded.columns
assert df_loaded['event_count'].iloc[0] == 250
print("5. Validação com sinônimos e renomeação padronizada: OK")

# 6. Teste de Blindagem contra XSS e sanitização de HTML
dangerous_comp = pd.DataFrame({
    'computer_name': ['<script>alert(1)</script>', 'SRV-<BACKUP>&DATA'],
    'event_count': [500, 200]
})
dangerous_dfs = {
    'action_cyber_threats': pd.DataFrame({
        'action_taken': ['<Exploit Blocked>', 'Cleaned'],
        'event_count': [500, 200]
    }),
    'top_10_computers': dangerous_comp
}
proc_danger = process_data(dangerous_dfs)
danger_inv = {
    '<script>alert(1)</script>': 'Host injetou tag <img src=x onerror=alert(1)> detectada.',
    'SRV-<BACKUP>&DATA': 'Servidor com caracteres < e &.'
}
html_gen = CyberReportHTML(client_config={'client_name': 'Cliente <Test> & Co'})
rendered_html = html_gen.generate(proc_danger, investigations=danger_inv)

# Verificar que nenhum script bruto foi renderizado
assert '<script>alert(1)</script>' not in rendered_html
assert '&lt;script&gt;alert(1)&lt;/script&gt;' in rendered_html
assert '&lt;Exploit Blocked&gt;' in rendered_html
assert '&lt;img src=x onerror=alert(1)&gt;' in rendered_html
print("6. Blindagem de HTML contra injeção e XSS: OK")

# 7. Teste de segurança no embutimento do bloco <script id="report-metadata">
danger_rec = ['[ALTA] Detecção de payload contendo </script><script>alert("hack")</script> no endpoint.']
proc_danger['recommendations'] = danger_rec
rendered_with_closing_script = html_gen.generate(proc_danger, investigations=danger_inv)
assert '</script><script>alert("hack")</script>' not in rendered_with_closing_script
extracted_meta = CyberReportHTML.extract_metadata(rendered_with_closing_script)
assert extracted_meta is not None, "Falha ao extrair metadados sanitizados"
print("7. Fechamento seguro de tag no bloco de metadados JSON: OK")

# 8. Teste de timeline parcial no Relatório Anual
annual_data_partial = hm.get_annual_data('demo_alpha', 2026)
ann_gen = AnnualReportHTML(client_config={'client_name': 'Alpha Corp'}, year=2026)
ann_html = ann_gen.generate(annual_data_partial)
assert len(ann_html) > 1000
print("8. Geração segura de Relatório Anual: OK")

print("\n🎉 TODOS OS 8 TESTES DE REMEDIAÇÃO PASSARAM COM SUCESSO!")
