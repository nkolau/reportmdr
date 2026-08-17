# reportmdr
# 🛡️ Cyber Report Generator

Gerador automatizado de relatórios de cibersegurança a partir de arquivos CSV.

## 📋 Sobre o Projeto

Aplicação web desenvolvida em Python/Streamlit para gerar relatórios executivos de cibersegurança a partir de arquivos CSV exportados de ferramentas de segurança (Trellix ENS, ATP, etc.).

## ✨ Funcionalidades

- **Gestão de Clientes** - Cadastro de múltiplos clientes com logo e cores personalizadas
- **Upload de CSVs** - Aceita múltiplos arquivos CSV com identificação automática
- **Configuração Dinâmica** - Interface para adicionar novos tipos de arquivos sem editar código
- **Processamento Automático** - Validação, mapeamento de colunas e cálculo de métricas
- **Análise Visual** - Gráficos de pizza, tabelas e indicadores (KPIs)
- **Investigação de Computadores** - Campo editável para notas de investigação por máquina
- **Exportação HTML** - Relatório profissional com design responsivo
- **Exportação PDF** - Relatório para impressão e compartilhamento
- **Histórico** - Armazenamento de relatórios anteriores por cliente

## 🗂️ Arquivos CSV Suportados

| Arquivo | Descrição |
|---------|-----------|
| `Action_Cyber_Threats.csv` | Ações tomadas pelo antivírus |
| `Top_10_Users.csv` | Usuários com mais detecções |
| `Top_10_Computers.csv` | Computadores com mais detecções |
| `Top_10_regras_de_Prevencao_de_Exploracao_violadas.csv` | Regras violadas |
| `Regras_exploit_prevention_-_Playbook_Trellix_Insights.csv` | Regras do playbook |

## 📦 Instalação

### Pré-requisitos

- Python 3.9+
- pip

### Passos

```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd relatorio

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
streamlit run app.py
