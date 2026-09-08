import pandas as pd
import json
import os


def load_file_mapping():
    """Carrega o mapeamento de arquivos esperados."""
    mapping_file = os.path.join("config", "file_mapping.json")
    with open(mapping_file, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_uploaded_files(uploaded_files):
    """
    Valida e carrega os arquivos CSV enviados.

    Args:
        uploaded_files: Lista de arquivos do Streamlit

    Returns:
        dataframes: Dict com DataFrames processados
        warnings: Lista de avisos
        errors: Lista de erros
    """
    mapping = load_file_mapping()
    expected_files = mapping["expected_files"]
    column_mapping = mapping["column_mapping"]

    found_files = {}
    warnings = []
    errors = []

    # Mapear arquivos enviados pelo nome
    for file in uploaded_files:
        filename = file.name
        if filename in expected_files:
            found_files[filename] = file
        else:
            warnings.append(f"⚠️ Arquivo não reconhecido (ignorado): {filename}")

    # Verificar arquivos faltantes
    missing = [f for f in expected_files if f not in found_files]
    if missing:
        warnings.append(f"⚠️ Arquivos não enviados: {', '.join(missing)}")

    if not found_files:
        errors.append("❌ Nenhum arquivo esperado foi enviado.")
        return {}, warnings, errors

    # Processar cada arquivo
    dataframes = {}
    for filename, file in found_files.items():
        try:
            # Ler CSV
            file.seek(0)
            df = pd.read_csv(file, encoding='utf-8')

            # Verificar colunas usando file_configs (com suporte a sinônimos) e column_mapping
            file_cfgs = mapping.get("file_configs", {}).get(filename, {})
            configured_cols = file_cfgs.get("columns", {})
            rename_dict = {}

            if configured_cols:
                # configured_cols pode ser {'std_col': ['Possivel1', 'Possivel2']}
                for std_name, possibilities in configured_cols.items():
                    if isinstance(possibilities, str):
                        possibilities = [possibilities]
                    matched_col = None
                    for p in possibilities:
                        # Busca case-insensitive e strip
                        for actual_c in df.columns:
                            if actual_c.strip().lower() == p.strip().lower():
                                matched_col = actual_c
                                break
                        if matched_col:
                            break
                    if not matched_col:
                        # Tentar o próprio standard name
                        for actual_c in df.columns:
                            if actual_c.strip().lower() == std_name.strip().lower():
                                matched_col = actual_c
                                break

                    if matched_col:
                        rename_dict[matched_col] = std_name

            # Fallback para column_mapping legado se necessário
            if not rename_dict:
                expected_cols = column_mapping.get(filename, {})
                for std_k, exp_v in expected_cols.items():
                    for actual_c in df.columns:
                        if actual_c.strip().lower() == exp_v.strip().lower():
                            rename_dict[actual_c] = std_k
                            break

            if rename_dict:
                df = df.rename(columns=rename_dict)

            # Limpar dados
            df = df.dropna(how='all')

            # Garantir que event_count é numérico (suportando strings formatadas com vírgula)
            if 'event_count' in df.columns:
                cleaned_series = df['event_count'].astype(str).str.replace(',', '').str.strip()
                df['event_count'] = pd.to_numeric(cleaned_series, errors='coerce')
                df = df.dropna(subset=['event_count'])
                df['event_count'] = df['event_count'].astype(int)

            # Identificar tipo do arquivo
            file_key = filename.replace('.csv', '').lower()
            dataframes[file_key] = df

            print(f"✅ Processado: {filename} ({len(df)} linhas)")

        except Exception as e:
            errors.append(f"❌ Erro ao processar {filename}: {str(e)}")

    if dataframes:
        warnings.insert(0, f"✅ {len(dataframes)} arquivo(s) processado(s) com sucesso.")

    return dataframes, warnings, errors


def get_available_analyses(dataframes):
    """Retorna lista de análises disponíveis com base nos DataFrames carregados."""
    analyses = []
    if not dataframes:
        return analyses

    analysis_mapping = {
        'action_cyber_threats': 'Ações do Antivírus',
        'top_10_users': 'Top 10 Usuários',
        'top_10_computers': 'Top 10 Computadores',
        'regras_exploit_prevention_-_playbook_trellix_insights': 'Regras do Playbook Trellix',
        'top_10_regras_de_prevencao_de_exploracao_violadas': 'Regras Violadas'
    }

    for key in dataframes.keys():
        if key in analysis_mapping:
            analyses.append(analysis_mapping[key])
        else:
            analyses.append(key.replace('_', ' ').title())

    return analyses

