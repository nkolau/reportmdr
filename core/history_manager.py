import os
import json
import re
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd


class HistoryManager:
    """Gerenciador de persistência histórica e cálculos de tendências MoM e Anuais."""

    MONTHS_PT = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    MONTH_MAP = {
        'janeiro': 1, 'jan': 1, '01': 1, '1': 1,
        'fevereiro': 2, 'fev': 2, '02': 2, '2': 2,
        'março': 3, 'marco': 3, 'mar': 3, '03': 3, '3': 3,
        'abril': 4, 'abr': 4, '04': 4, '4': 4,
        'maio': 5, 'mai': 5, '05': 5, '5': 5,
        'junho': 6, 'jun': 6, '06': 6, '6': 6,
        'julho': 7, 'jul': 7, '07': 7, '7': 7,
        'agosto': 8, 'ago': 8, '08': 8, '8': 8,
        'setembro': 9, 'set': 9, '09': 9, '9': 9,
        'outubro': 10, 'out': 10, '10': 10,
        'novembro': 11, 'nov': 11, '11': 11,
        'dezembro': 12, 'dez': 12, '12': 12
    }

    def __init__(self, history_dir=None):
        self.history_dir = history_dir or os.path.join("data", "history")
        os.makedirs(self.history_dir, exist_ok=True)

    def _get_history_file(self, client_id):
        safe_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(client_id)).lower()
        return os.path.join(self.history_dir, f"{safe_id}_history.json")

    @staticmethod
    def _safe_int(val, default=0):
        try:
            if val is None or pd.isna(val):
                return default
            if isinstance(val, str):
                clean_str = val.replace(',', '').strip()
                return int(float(clean_str))
            return int(float(val))
        except (ValueError, TypeError):
            return default

    def parse_period(self, period_str):
        """Converte uma string de período como 'Agosto/2026' em (month_int, year_int)."""
        today = date.today()
        last = today - relativedelta(months=1)

        if not period_str:
            return last.month, last.year

        period_clean = str(period_str).strip().lower()
        parts = re.split(r'[/_\-\s]+', period_clean)

        month_num = None
        year_num = None

        for p in parts:
            if p.isdigit():
                if len(p) == 4:
                    year_num = int(p)
                elif int(p) in range(1, 13) and month_num is None:
                    month_num = int(p)
            elif p in self.MONTH_MAP:
                month_num = self.MONTH_MAP[p]

        if not year_num:
            year_num = last.year
        if not month_num:
            month_num = last.month

        return month_num, year_num

    def format_period(self, month_int, year_int):
        """Retorna 'Mês/Ano' formatado em português."""
        if 1 <= month_int <= 12:
            return f"{self.MONTHS_PT[month_int - 1]}/{year_int}"
        return f"{month_int}/{year_int}"

    def load_client_history(self, client_id):
        """Carrega todos os registros históricos do cliente ordenados cronologicamente."""
        filepath = self._get_history_file(client_id)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        # Filtrar apenas entradas válidas com ano e mês
                        valid_history = [
                            item for item in history
                            if isinstance(item, dict) and ('year' in item or 'period' in item)
                        ]
                        for item in valid_history:
                            if 'year' not in item or 'month' not in item:
                                m, y = self.parse_period(item.get('period', ''))
                                item['year'] = y
                                item['month'] = m
                        # Ordenar por ano e mês
                        valid_history.sort(key=lambda x: (x.get('year', 0), x.get('month', 0)))
                        return valid_history
            except Exception:
                pass
        return []

    def save_client_history(self, client_id, history):
        """Salva lista de histórico do cliente."""
        filepath = self._get_history_file(client_id)
        history.sort(key=lambda x: (x.get('year', 0), x.get('month', 0)))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def save_month_record(self, client_id, period_str, processed_data, investigations=None):
        """Salva ou atualiza os dados consolidados de um mês no histórico."""
        m_num, y_num = self.parse_period(period_str)
        canonical_period = self.format_period(m_num, y_num)

        history = self.load_client_history(client_id)

        # Extrair métricas principais com conversão segura
        metrics = {
            'total_events': self._safe_int(processed_data.get('total_events', 0)),
            'total_actions': self._safe_int(processed_data.get('total_actions', 0)),
            'total_computers': self._safe_int(processed_data.get('total_computers', 0)),
            'total_users': self._safe_int(processed_data.get('total_users', 0)),
            'total_violations': self._safe_int(processed_data.get('total_violations', 0)),
            'total_playbook_events': self._safe_int(processed_data.get('total_playbook_events', 0))
        }

        # Extrair Top Computers (ordenando decrescente por event_count)
        top_computers = []
        df_comp = processed_data.get('tables', {}).get('computers')
        if df_comp is not None and isinstance(df_comp, pd.DataFrame) and not df_comp.empty:
            df_comp_sorted = df_comp.copy()
            if 'event_count' in df_comp_sorted.columns:
                df_comp_sorted['event_count'] = pd.to_numeric(df_comp_sorted['event_count'], errors='coerce').fillna(0)
                df_comp_sorted = df_comp_sorted.sort_values(by='event_count', ascending=False)
            for _, r in df_comp_sorted.head(10).iterrows():
                top_computers.append({
                    'name': str(r.get('computer_name', '')),
                    'events': self._safe_int(r.get('event_count', 0))
                })

        # Extrair Top Users (ordenando decrescente por event_count)
        top_users = []
        df_users = processed_data.get('tables', {}).get('users')
        if df_users is not None and isinstance(df_users, pd.DataFrame) and not df_users.empty:
            df_users_sorted = df_users.copy()
            if 'event_count' in df_users_sorted.columns:
                df_users_sorted['event_count'] = pd.to_numeric(df_users_sorted['event_count'], errors='coerce').fillna(0)
                df_users_sorted = df_users_sorted.sort_values(by='event_count', ascending=False)
            for _, r in df_users_sorted.head(10).iterrows():
                top_users.append({
                    'name': str(r.get('user_name', '')),
                    'events': self._safe_int(r.get('event_count', 0))
                })

        # Extrair Top Rules (ordenando decrescente por event_count)
        top_rules = []
        df_rules = processed_data.get('tables', {}).get('rules_violated')
        if df_rules is not None and isinstance(df_rules, pd.DataFrame) and not df_rules.empty:
            df_rules_sorted = df_rules.copy()
            if 'event_count' in df_rules_sorted.columns:
                df_rules_sorted['event_count'] = pd.to_numeric(df_rules_sorted['event_count'], errors='coerce').fillna(0)
                df_rules_sorted = df_rules_sorted.sort_values(by='event_count', ascending=False)
            for _, r in df_rules_sorted.head(10).iterrows():
                top_rules.append({
                    'name': str(r.get('rule_name', '')),
                    'events': self._safe_int(r.get('event_count', 0))
                })

        record = {
            'period': canonical_period,
            'year': y_num,
            'month': m_num,
            'updated_at': datetime.now().isoformat(),
            'metrics': metrics,
            'top_computers': top_computers,
            'top_users': top_users,
            'top_rules': top_rules,
            'investigations': investigations or {},
            'recommendations': processed_data.get('recommendations', [])
        }

        # Atualizar ou adicionar
        found = False
        for i, item in enumerate(history):
            if item.get('year') == y_num and item.get('month') == m_num:
                history[i] = record
                found = True
                break

        if not found:
            history.append(record)

        self.save_client_history(client_id, history)
        return record

    def get_previous_month_record(self, client_id, current_period_str):
        """Busca o registro do mês imediatamente anterior ao período informado."""
        m_num, y_num = self.parse_period(current_period_str)
        history = self.load_client_history(client_id)

        # Calcular mês/ano anterior cronológico
        if m_num == 1:
            target_m = 12
            target_y = y_num - 1
        else:
            target_m = m_num - 1
            target_y = y_num

        for item in history:
            if item.get('year') == target_y and item.get('month') == target_m:
                return item

        # Fallback: pega o último registro cronologicamente menor que o atual
        candidates = [
            item for item in history
            if (item.get('year', 0) < y_num) or (item.get('year', 0) == y_num and item.get('month', 0) < m_num)
        ]
        return candidates[-1] if candidates else None

    def calculate_mom_deltas(self, current_metrics, previous_metrics):
        """
        Calcula as variações percentuais e direcionais MoM (Month-over-Month).
        Retorna dicionário com delta_pct, delta_abs, direction ('up', 'down', 'neutral', 'good_down', 'bad_up').
        """
        if not previous_metrics:
            return {}

        deltas = {}
        for key in ['total_events', 'total_actions', 'total_computers', 'total_users', 'total_violations', 'total_playbook_events']:
            curr_val = current_metrics.get(key, 0)
            prev_val = previous_metrics.get(key, 0)

            diff = curr_val - prev_val
            if prev_val > 0:
                pct = ((curr_val - prev_val) / prev_val) * 100.0
            elif curr_val > 0:
                pct = 100.0
            else:
                pct = 0.0

            # Para métricas de segurança (eventos, violações), aumento geralmente é alerta e queda é positivo
            is_risk_metric = key in ['total_events', 'total_violations', 'total_computers', 'total_users']

            if abs(diff) == 0:
                direction = 'neutral'
                status = 'neutral'
            elif diff > 0:
                direction = 'up'
                status = 'alert' if is_risk_metric else 'positive'
            else:
                direction = 'down'
                status = 'positive' if is_risk_metric else 'neutral'

            deltas[key] = {
                'curr_value': curr_val,
                'prev_value': prev_val,
                'diff': diff,
                'pct': round(pct, 1),
                'direction': direction,
                'status': status
            }

        return deltas

    def get_annual_data(self, client_id, year):
        """Consolida os dados de todos os meses disponíveis de um ano para o Relatório Anual."""
        history = self.load_client_history(client_id)
        year_int = int(year)
        records = [r for r in history if r.get('year') == year_int]

        if not records:
            return None

        # Ordenar meses 1 a 12
        records.sort(key=lambda x: x.get('month', 0))

        # KPIs Acumulados & Médias
        total_annual_events = sum(r.get('metrics', {}).get('total_events', 0) for r in records)
        total_annual_actions = sum(r.get('metrics', {}).get('total_actions', 0) for r in records)
        total_annual_violations = sum(r.get('metrics', {}).get('total_violations', 0) for r in records)
        total_annual_playbook = sum(r.get('metrics', {}).get('total_playbook_events', 0) for r in records)

        num_months = len(records)
        avg_monthly_events = int(total_annual_events / num_months) if num_months > 0 else 0
        avg_monthly_violations = int(total_annual_violations / num_months) if num_months > 0 else 0

        # Computadores únicos acumulados no ano e frequência
        computer_frequency = {}
        for r in records:
            for comp in r.get('top_computers', []):
                name = comp.get('name')
                if name:
                    if name not in computer_frequency:
                        computer_frequency[name] = {'name': name, 'months_count': 0, 'total_events': 0}
                    computer_frequency[name]['months_count'] += 1
                    computer_frequency[name]['total_events'] += comp.get('events', 0)

        top_recurrent_computers = sorted(
            computer_frequency.values(),
            key=lambda x: (x['months_count'], x['total_events']),
            reverse=True
        )[:10]

        # Regras mais recorrentes no ano
        rule_frequency = {}
        for r in records:
            for rule in r.get('top_rules', []):
                name = rule.get('name')
                if name:
                    if name not in rule_frequency:
                        rule_frequency[name] = {'name': name, 'months_count': 0, 'total_events': 0}
                    rule_frequency[name]['months_count'] += 1
                    rule_frequency[name]['total_events'] += rule.get('events', 0)

        top_recurrent_rules = sorted(
            rule_frequency.values(),
            key=lambda x: (x['months_count'], x['total_events']),
            reverse=True
        )[:10]

        # Linha do tempo dos 12 meses (preenchendo meses não cadastrados com 0 ou None para gráficos)
        timeline = []
        for m in range(1, 13):
            month_name = self.MONTHS_PT[m - 1]
            match = next((r for r in records if r.get('month') == m), None)
            if match:
                m_data = match.get('metrics', {})
                timeline.append({
                    'month_num': m,
                    'month_name': month_name,
                    'period': match.get('period'),
                    'has_data': True,
                    'total_events': m_data.get('total_events', 0),
                    'total_actions': m_data.get('total_actions', 0),
                    'total_computers': m_data.get('total_computers', 0),
                    'total_users': m_data.get('total_users', 0),
                    'total_violations': m_data.get('total_violations', 0),
                    'total_playbook_events': m_data.get('total_playbook_events', 0)
                })
            else:
                timeline.append({
                    'month_num': m,
                    'month_name': month_name,
                    'period': f"{month_name}/{year_int}",
                    'has_data': False,
                    'total_events': 0,
                    'total_actions': 0,
                    'total_computers': 0,
                    'total_users': 0,
                    'total_violations': 0,
                    'total_playbook_events': 0
                })

        return {
            'year': year_int,
            'client_id': client_id,
            'num_months_registered': num_months,
            'total_annual_events': total_annual_events,
            'total_annual_actions': total_annual_actions,
            'total_annual_violations': total_annual_violations,
            'total_annual_playbook': total_annual_playbook,
            'avg_monthly_events': avg_monthly_events,
            'avg_monthly_violations': avg_monthly_violations,
            'unique_computers_count': len(computer_frequency),
            'timeline': timeline,
            'top_recurrent_computers': top_recurrent_computers,
            'top_recurrent_rules': top_recurrent_rules,
            'monthly_records': records
        }

    def delete_month_record(self, client_id, period_str):
        """Remove o registro de um mês específico do histórico."""
        m_num, y_num = self.parse_period(period_str)
        history = self.load_client_history(client_id)
        filtered = [r for r in history if not (r.get('year') == y_num and r.get('month') == m_num)]
        if len(filtered) != len(history):
            self.save_client_history(client_id, filtered)
            return True
        return False
