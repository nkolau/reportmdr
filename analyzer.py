import json
import os
from datetime import datetime


def save_report_history(client_name, metrics, dataframes_keys, period):
    """Salva histórico do relatório."""
    import json
    import os

    history_dir = "data/history"
    os.makedirs(history_dir, exist_ok=True)

    history_file = os.path.join(history_dir, f"{client_name}_history.json")

    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    entry = {
        'date': datetime.now().isoformat(),
        'period': period,
        'metrics': {},
        'files': dataframes_keys
    }

    for k, v in metrics.items():
        if isinstance(v, (int, float, str, bool)):
            entry['metrics'][k] = v

    history.append(entry)

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def load_report_history(client_name):
    """Carrega histórico de relatórios do cliente."""
    history_file = os.path.join("data/history", f"{client_name}_history.json")
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def compare_with_previous(current_metrics, history):
    """Compara métricas atuais com relatório anterior."""
    if len(history) < 2:
        return None

    previous = history[-2]  # Penúltimo relatório
    prev_metrics = previous.get('metrics', {})

    comparison = {}
    for key in ['total_events', 'total_computers', 'total_users', 'total_violations']:
        if key in current_metrics and key in prev_metrics:
            curr = current_metrics[key]
            prev = prev_metrics[key]
            if prev > 0:
                change = ((curr - prev) / prev) * 100
                comparison[key] = {
                    'current': curr,
                    'previous': prev,
                    'change_percent': round(change, 1)
                }

    return comparison if comparison else None
