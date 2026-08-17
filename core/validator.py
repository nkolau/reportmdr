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

            # Verificar colunas
            expected_cols = column_mapping.get(filename, {})
            if expected_cols:
                actual_cols = list(expected_cols.values())
                missing_cols = [c for c in actual_cols if c not in df.columns]

                if missing_cols:
                    warnings.append(
                        f"⚠️ {filename}: colunas não encontradas: {', '.join(missing_cols)}"
                    )
                    continue

                # Renomear colunas para nomes padronizados
                rename_dict = {v: k for k, v in expected_cols.items()}
                df = df.rename(columns=rename_dict)

            # Limpar dados
            df = df.dropna(how='all')

            # Garantir que event_count é numérico
            if 'event_count' in df.columns:
                df['event_count'] = pd.to_numeric(df['event_count'], errors='coerce')
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
