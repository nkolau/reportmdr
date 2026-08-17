import json
import os
import pandas as pd


class ConfigManager:
    def __init__(self):
        self.config_file = os.path.join("config", "dynamic_config.json")
        self.config = self.load_config()

    def load_config(self):
        """Carrega configuração dinâmica."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"files": {}}
        return {"files": {}}

    def save_config(self):
        """Salva configuração."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def add_file_config(self, file_pattern, keywords, column_mapping, description=""):
        """Adiciona nova configuração de arquivo."""
        self.config["files"][file_pattern] = {
            "keywords": keywords,
            "columns": column_mapping,
            "description": description
        }
        self.save_config()

    def remove_file_config(self, file_pattern):
        """Remove configuração de arquivo."""
        if file_pattern in self.config["files"]:
            del self.config["files"][file_pattern]
            self.save_config()
            return True
        return False

    def update_file_config(self, file_pattern, keywords, column_mapping, description=""):
        """Atualiza configuração existente."""
        if file_pattern in self.config["files"]:
            self.config["files"][file_pattern] = {
                "keywords": keywords,
                "columns": column_mapping,
                "description": description
            }
            self.save_config()
            return True
        return False

    def get_all_configs(self):
        """Retorna todas as configurações."""
        return self.config.get("files", {})

    def get_config(self, file_pattern):
        """Retorna configuração específica."""
        return self.config.get("files", {}).get(file_pattern)

    def auto_suggest(self, uploaded_file):
        """
        Analisa CSV e sugere mapeamento de colunas.
        Retorna (suggestions, df_columns)
        """
        try:
            df = pd.read_csv(uploaded_file)
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='latin1')

        suggestions = {}

        for col in df.columns:
            col_lower = col.lower().strip()

            # Heurísticas de detecção
            if any(kw in col_lower for kw in ['user', 'usuario', 'usuário', 'target user']):
                suggestions[col] = 'user_name'
            elif any(kw in col_lower for kw in ['computer', 'maquina', 'máquina', 'host', 'system name']):
                suggestions[col] = 'computer_name'
            elif any(kw in col_lower for kw in ['rule', 'regra', 'analyzer']):
                suggestions[col] = 'rule_name'
            elif any(kw in col_lower for kw in ['action', 'acao', 'ação']):
                suggestions[col] = 'action_taken'
            elif any(kw in col_lower for kw in ['event', 'count', 'number', 'quantidade', 'threat']):
                suggestions[col] = 'event_count'
            elif any(kw in col_lower for kw in ['severity', 'severidade', 'gravidade', 'severidad']):
                suggestions[col] = 'severity'
            elif any(kw in col_lower for kw in ['date', 'data']):
                suggestions[col] = 'date'
            elif any(kw in col_lower for kw in ['status', 'estado']):
                suggestions[col] = 'status'
            elif any(kw in col_lower for kw in ['category', 'categoria', 'tipo']):
                suggestions[col] = 'category'

        return suggestions, df.columns.tolist()

    def suggest_keywords(self, filename):
        """Sugere palavras-chave baseado no nome do arquivo."""
        import unicodedata

        # Remover acentos e normalizar
        nfkd = unicodedata.normalize('NFKD', filename.lower())
        clean = ''.join([c for c in nfkd if not unicodedata.combining(c)])

        # Remover extensão e prefixos
        clean = clean.replace('.csv', '')
        for prefix in ['rem__', 'rem_', 'ens_', 'copia_de_']:
            clean = clean.replace(prefix, '')

        # Separar em palavras
        words = clean.replace('_', ' ').replace('-', ' ').split()

        # Filtrar palavras relevantes (remover stopwords)
        stopwords = ['top', '10', 'with', 'the', 'most', 'of', 'de', 'do', 'da']
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords[:5] if keywords else [clean[:20]]
