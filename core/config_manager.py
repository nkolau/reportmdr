import json
import os
import re
import pandas as pd


class ConfigManager:
    """Gerenciador de configurações de arquivos CSV e seus enunciados."""

    DEFAULT_CONFIG_PATH = os.path.join("config", "file_mapping.json")

    STANDARD_COLUMN_HINTS = {
        'action_taken': ['action', 'taken', 'acao', 'resultado', 'status_action'],
        'user_name': ['user', 'usuario', 'target_user', 'username', 'login', 'account'],
        'computer_name': ['computer', 'system', 'host', 'hostname', 'computador', 'device', 'maquina'],
        'rule_name': ['rule', 'regra', 'analyzer_rule', 'policy', 'signature', 'threat_name'],
        'event_count': ['event', 'count', 'total', 'number_of', 'eventos', 'ocorrencias', 'qtd', 'quantidade'],
        'violation_count': ['violation', 'violacao', 'violations', 'infracao'],
        'severity': ['severity', 'severidade', 'nivel', 'level', 'criticidade', 'priority'],
        'date': ['date', 'data', 'timestamp', 'time', 'hora', 'datetime'],
        'status': ['status', 'estado', 'state', 'situacao'],
        'category': ['category', 'categoria', 'tipo', 'type', 'classe']
    }

    def __init__(self, config_path=None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._ensure_config_file()
        self.config = self._load()

    def _ensure_config_file(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        if not os.path.exists(self.config_path):
            initial_data = {
                "expected_files": [],
                "file_configs": {},
                "column_mapping": {}
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)

    def _load(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "file_configs" not in data:
                    data["file_configs"] = {}
                return data
        except Exception:
            return {"expected_files": [], "file_configs": {}, "column_mapping": {}}

    def _save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get_all_configs(self):
        """Retorna todas as configurações de arquivos disponíveis."""
        return self.config.get("file_configs", {})

    def get_config(self, file_pattern):
        """Retorna a configuração de um arquivo específico."""
        return self.config.get("file_configs", {}).get(file_pattern, {})

    def add_file_config(self, file_pattern, keywords, column_mapping, description="", title="", enunciado=""):
        """Adiciona ou atualiza a configuração de um arquivo CSV."""
        if not file_pattern:
            return False

        if "file_configs" not in self.config:
            self.config["file_configs"] = {}
        if "expected_files" not in self.config:
            self.config["expected_files"] = []
        if "column_mapping" not in self.config:
            self.config["column_mapping"] = {}

        if file_pattern not in self.config["expected_files"]:
            self.config["expected_files"].append(file_pattern)

        # Se título não fornecido, gera um a partir do padrão
        if not title:
            base = file_pattern.replace(".csv", "").replace("_", " ").replace("-", " ")
            title = base.title()

        # Configuração rica
        self.config["file_configs"][file_pattern] = {
            "title": title,
            "description": description or f"Arquivo {file_pattern}",
            "enunciado": enunciado or f"Dados consolidados de {title} referentes ao período avaliado.",
            "keywords": keywords if isinstance(keywords, list) else [k.strip() for k in keywords.split(",") if k.strip()],
            "columns": column_mapping
        }

        # Simplificação para column_mapping legado
        legacy_map = {}
        for std_col, csv_list in column_mapping.items():
            if isinstance(csv_list, list) and csv_list:
                legacy_map[std_col] = csv_list[0]
            elif isinstance(csv_list, str):
                legacy_map[std_col] = csv_list
        self.config["column_mapping"][file_pattern] = legacy_map

        self._save()
        return True

    def remove_file_config(self, file_pattern):
        """Remove a configuração de um arquivo."""
        if file_pattern in self.config.get("expected_files", []):
            self.config["expected_files"].remove(file_pattern)
        if file_pattern in self.config.get("file_configs", {}):
            del self.config["file_configs"][file_pattern]
        if file_pattern in self.config.get("column_mapping", {}):
            del self.config["column_mapping"][file_pattern]
        self._save()
        return True

    def suggest_keywords(self, filename):
        """Gera palavras-chave a partir do nome do arquivo."""
        clean = re.sub(r'\.csv$', '', filename, flags=re.IGNORECASE)
        tokens = re.split(r'[_\-\s\.]+', clean)
        keywords = [t.lower() for t in tokens if len(t) >= 2 and not t.isdigit()]
        return list(dict.fromkeys(keywords))

    def auto_suggest(self, uploaded_file):
        """Lê as primeiras linhas de um CSV e sugere metadados e mapeamento de colunas."""
        filename = getattr(uploaded_file, 'name', 'Novo_Arquivo.csv')
        clean_name = re.sub(r'\.csv$', '', filename, flags=re.IGNORECASE)
        suggested_title = clean_name.replace('_', ' ').replace('-', ' ').title()
        suggested_keywords = self.suggest_keywords(filename)

        meta_suggestions = {
            'file_pattern': filename,
            'title': suggested_title,
            'description': f"Arquivo de telemetria para {suggested_title}",
            'enunciado': f"Consolidação dos dados de {suggested_title} registrados no ambiente corporativo durante o período avaliado.",
            'keywords': suggested_keywords,
            'columns': {}
        }

        columns = []
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, nrows=5)
            columns = list(df.columns)
            uploaded_file.seek(0)

            for col in columns:
                col_lower = str(col).lower().replace(' ', '_').replace('-', '_')
                matched = False
                for std_name, hints in self.STANDARD_COLUMN_HINTS.items():
                    if any(hint in col_lower for hint in hints):
                        meta_suggestions['columns'][col] = std_name
                        meta_suggestions[col] = std_name
                        matched = True
                        break
                if not matched:
                    if 'count' in col_lower or 'total' in col_lower or 'qtd' in col_lower or 'sum' in col_lower:
                        meta_suggestions['columns'][col] = 'event_count'
                        meta_suggestions[col] = 'event_count'
                    elif 'name' in col_lower or 'nome' in col_lower:
                        meta_suggestions['columns'][col] = 'user_name'
                        meta_suggestions[col] = 'user_name'
        except Exception:
            pass

        return meta_suggestions, columns
