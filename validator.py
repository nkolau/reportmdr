import pandas as pd
import unicodedata
from io import BytesIO
import os
import json


class ConfigManager:
    def __init__(self):
        self.config_file = os.path.join("config", "dynamic_config.json")
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"files": {}}
        return {"files": {}}

    def get_all_configs(self):
        return self.config.get("files", {})

    def get_file_patterns(self):
        """Retorna lista de palavras-chave para cada tipo de arquivo."""
        patterns = {}
        for file_pattern, config in self.get_all_configs().items():
            patterns[file_pattern] = {
                "keywords": config.get("keywords", []),
                "columns": config.get("columns", {}),
                "description": config.get("description", "")
            }
        return patterns


def remove_accents(text):
    """Remove acentos de uma string."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])


def normalize_filename(filename):
    """Normaliza nome do arquivo para comparação."""
    filename_clean = filename.lower()

    # Remover prefixos comuns
    for prefix in ["rem__", "rem_", "ens_", "ens__", "copia_de_", "cópia_de_", "copy_of_"]:
        filename_clean = filename_clean.replace(prefix, "")

    # Remover extensão
    filename_clean = filename_clean.replace(".csv", "")

    # Remover acentos
    filename_no_accents = remove_accents(filename_clean)

    # Substituir underscores e hífens por espaços
    filename_normalized = filename_no_accents.replace("_", " ").replace("-", " ")

    return filename_normalized


def identify_file_type(filename, file_patterns):
    """
    Identifica o tipo de arquivo baseado nas palavras-chave configuradas.
    """
    filename_normalized = normalize_filename(filename)

    print(f"\n🔍 Identificando: {filename}")
    print(f"   Normalizado: {filename_normalized}")

    best_match = None
    best_score = 0
    best_matched = []

    for file_pattern, config in file_patterns.items():
        keywords = config.get("keywords", [])

        if not keywords:
            continue

        matched = 0
        matched_keywords = []

        for keyword in keywords:
            keyword_clean = remove_accents(keyword.lower())
            if keyword_clean in filename_normalized:
                matched += 1
                matched_keywords.append(keyword)

        if matched > 0:
            score = matched / len(keywords)
            print(f"   {file_pattern}: {matched}/{len(keywords)} keywords ({score:.0%}) - {matched_keywords}")

            if score > best_score:
                best_score = score
                best_match = file_pattern
                best_matched = matched_keywords

    # ACEITAR QUALQUER MATCH (pelo menos 1 keyword)
    if best_match and best_score > 0:
        print(f"   ✅ Identificado como: {best_match}")
        return best_match, file_patterns[best_match]

    print(f"   ❌ NÃO RECONHECIDO")
    return None, None


def find_matching_column(df_columns, possible_names):
    """
    Encontra a primeira coluna do DataFrame que corresponde a qualquer
    um dos nomes possíveis.
    """
    # Match exato
    for name in possible_names:
        if name in df_columns:
            return name

    # Match case-insensitive
    for name in possible_names:
        for col in df_columns:
            if col.lower() == name.lower():
                return col

    # Match parcial
    for name in possible_names:
        for col in df_columns:
            if name.lower() in col.lower() or col.lower() in name.lower():
                return col

    return None


def validate_uploaded_files(uploaded_files):
    """
    Valida e carrega os arquivos CSV enviados.
    Usa configuração dinâmica do ConfigManager.

    Returns:
        dataframes: Dict com DataFrames processados
        found_files: Dict com informações dos arquivos
        warnings: Lista de avisos
        errors: Lista de erros
    """
    config_manager = ConfigManager()
    file_patterns = config_manager.get_file_patterns()

    if not file_patterns:
        warnings = ["⚠️ Nenhuma configuração de arquivo encontrada. Configure os CSVs primeiro."]
        return {}, {}, warnings, []

    found_files = {}
    unrecognized = []
    dataframes = {}
    warnings = []
    errors = []

    # Identificar cada arquivo
    for file in uploaded_files:
        filename = file.name
        file_pattern, config = identify_file_type(filename, file_patterns)

        if file_pattern:
            found_files[file_pattern] = {
                "file": file,
                "config": config,
                "original_name": filename
            }
            print(f"✅ Identificado: {filename} → {file_pattern}")
        else:
            unrecognized.append(filename)

    if unrecognized:
        warnings.append(f"⚠️ {len(unrecognized)} arquivo(s) não reconhecido(s): {', '.join(unrecognized)}")

    if not found_files:
        errors.append("❌ Nenhum arquivo reconhecido foi enviado.")
        return {}, {}, warnings, errors

    # Processar cada arquivo
    for file_pattern, file_info in found_files.items():
        file = file_info["file"]
        config = file_info["config"]
        original_name = file_info["original_name"]
        column_mapping = config.get("columns", {})

        try:
            # Tentar múltiplos encodings
            df = None
            for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                for sep in [',', ';', '\t']:
                    try:
                        file.seek(0)
                        df = pd.read_csv(file, encoding=encoding, sep=sep)
                        if len(df.columns) >= 1:
                            break
                    except:
                        continue
                if df is not None and len(df.columns) >= 1:
                    break

            if df is None or len(df.columns) < 1:
                errors.append(f"❌ Não foi possível ler {original_name}.")
                continue

            # Limpar nomes das colunas
            df.columns = [col.strip() for col in df.columns]

            print(f"\n📊 Processando {original_name}:")
            print(f"   Colunas: {list(df.columns)}")
            print(f"   Mapeamento configurado: {column_mapping}")

            # Mapear colunas
            actual_mapping = {}
            missing_mappings = []

            for standard_name, csv_names in column_mapping.items():
                found_col = find_matching_column(df.columns, csv_names)
                if found_col:
                    actual_mapping[standard_name] = found_col
                    print(f"   ✓ {standard_name} ← {found_col}")
                else:
                    missing_mappings.append(standard_name)
                    print(f"   ✗ {standard_name} não encontrado")

            if missing_mappings and not actual_mapping:
                warnings.append(
                    f"⚠️ {original_name}: nenhuma coluna esperada encontrada."
                )
                # Usar DataFrame como está
                dataframes[file_pattern] = df
                continue

            if actual_mapping:
                # Selecionar e renomear colunas
                available_cols = [c for c in actual_mapping.values() if c in df.columns]
                if available_cols:
                    df_mapped = df[available_cols].copy()
                    rename_dict = {v: k for k, v in actual_mapping.items() if v in df.columns}
                    df_mapped.rename(columns=rename_dict, inplace=True)
                    dataframes[file_pattern] = df_mapped
                    print(f"   ✅ Colunas mapeadas: {list(df_mapped.columns)}")
                else:
                    dataframes[file_pattern] = df
            else:
                dataframes[file_pattern] = df

        except Exception as e:
            errors.append(f"❌ Erro ao processar {original_name}: {str(e)}")

    # Resumo
    if dataframes:
        descriptions = []
        for fp in dataframes.keys():
            if fp in file_patterns:
                descriptions.append(file_patterns[fp].get("description", fp))
            else:
                descriptions.append(fp)
        warnings.insert(0, f"✅ {len(dataframes)} arquivo(s) processado(s): {', '.join(descriptions)}")

    return dataframes, found_files, warnings, errors


def get_available_analyses(dataframes):
    """Retorna lista de análises disponíveis."""
    available = []

    for file_pattern, df in dataframes.items():
        if df is not None and not df.empty:
            available.append({
                "type": file_pattern,
                "name": file_pattern.replace('_', ' ').title(),
                "description": f"{len(df)} registros processados"
            })

    return available
